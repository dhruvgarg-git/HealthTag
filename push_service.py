"""Minimal, privacy-preserving Web Push delivery for HealthTag.

Only generic notification text is sent to browsers. Never pass medical details,
OTP values, approval tokens, or user-provided message bodies to this module.
"""
import json
import os

from pywebpush import WebPushException, webpush


def send_generic_push(subscription_info):
    """Submit a generic notification to one browser subscription.

    Returns one of: "accepted", "unavailable", or "failed".
    "accepted" means the push service accepted the request, not that a device
    displayed or a person read the notification.
    """
    public_key = os.environ.get("HEALTHTAG_VAPID_PUBLIC_KEY", "").strip()
    private_key = os.environ.get("HEALTHTAG_VAPID_PRIVATE_KEY", "").strip()
    subject = os.environ.get("HEALTHTAG_VAPID_SUBJECT", "").strip()

    if not (public_key and private_key and subject):
        return "unavailable"

    payload = {
        "title": "HealthTag notification",
        "body": "You have a new account update. Open HealthTag to view it.",
        "path": "/notifications",
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
        return "accepted"
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code in (404, 410):
            return "unavailable"
        return "failed"
    except Exception:
        # Do not log subscription data, credentials, or provider response bodies.
        return "failed"
