"""Minimal, privacy-preserving Web Push delivery for HealthTag.

Only generic notification text is sent to browsers. Never pass medical details,
OTP values, approval tokens, or user-provided message bodies to this module.
"""
import json
import logging
import os

from pywebpush import WebPushException, webpush

logger = logging.getLogger(__name__)


def send_generic_push(subscription_info, notification_path="/notifications"):
    """Submit a generic notification to one browser subscription.

    Returns one of: "accepted", "unavailable", or "failed".
    "accepted" means the push service accepted the request, not that a device
    displayed or a person read the notification.
    """
    public_key = os.environ.get("HEALTHTAG_VAPID_PUBLIC_KEY", "").strip()
    private_key = os.environ.get("HEALTHTAG_VAPID_PRIVATE_KEY", "").strip()
    subject = os.environ.get("HEALTHTAG_VAPID_SUBJECT", "").strip()

    if not (public_key and private_key and subject):
        logger.warning(
            "Web Push unavailable: VAPID configuration incomplete "
            "(public_key=%s, private_key=%s, subject=%s)",
            bool(public_key), bool(private_key), bool(subject),
        )
        return "unavailable"

    payload = {
        "title": "HealthTag notification",
        "body": "You have a new account update. Open HealthTag to view it.",
        "path": notification_path if isinstance(notification_path, str) and notification_path.startswith("/notifications") and not notification_path.startswith("//") else "/notifications",
        "tag": "healthtag-account-update",
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload, separators=(",", ":")),
            vapid_private_key=private_key,
            vapid_claims={"sub": subject},
            ttl=60,
        )
        logger.info("Web Push accepted by push service")
        return "accepted"
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code in (404, 410):
            logger.warning("Web Push subscription expired or revoked (HTTP %s)", status_code)
            return "unavailable"
        logger.error("Web Push rejected by push service (HTTP %s)", status_code)
        return "failed"
    except Exception as exc:
        # Log only the exception class; never log subscription data, credentials,
        # payloads, or provider response bodies.
        logger.error("Web Push failed before acceptance (%s)", type(exc).__name__)
        return "failed"
