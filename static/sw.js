/* HealthTag browser push service worker.
 * Push payloads must contain generic, non-sensitive text only.
 */
self.addEventListener("push", (event) => {
  let payload = {};
  if (event.data) {
    try {
      payload = event.data.json();
    } catch (_error) {
      payload = { body: event.data.text() };
    }
  }

  const title = typeof payload.title === "string" && payload.title.trim()
    ? payload.title.trim().slice(0, 80)
    : "HealthTag notification";
  const body = typeof payload.body === "string" && payload.body.trim()
    ? payload.body.trim().slice(0, 180)
    : "You have a new notification.";

  // Never put OTPs, approval tokens, medical details, or private URLs in push data.
  const options = {
    body,
    tag: typeof payload.tag === "string" ? payload.tag.slice(0, 100) : "healthtag-update",
    data: { path: typeof payload.path === "string" ? payload.path : "/notifications" },
    renotify: false
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  event.waitUntil((async () => {
    const path = event.notification.data && event.notification.data.path;
    let target;
    try {
      target = new URL(typeof path === "string" ? path : "/notifications", self.location.origin);
    } catch (_error) {
      target = new URL("/notifications", self.location.origin);
    }

    // Only allow same-origin navigation.
    if (target.origin !== self.location.origin) {
      target = new URL("/notifications", self.location.origin);
    }

    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of windows) {
      if (client.url.startsWith(self.location.origin) && "focus" in client) {
        await client.focus();
        if ("navigate" in client && client.url !== target.href) {
          await client.navigate(target.href);
        }
        return;
      }
    }

    if (self.clients.openWindow) {
      await self.clients.openWindow(target.href);
    }
  })());
});
