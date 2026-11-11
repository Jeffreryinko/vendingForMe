// 서비스 워커: 홈 화면 앱으로 열기(오프라인에서도 화면이 뜸) + 폰 알림 표시
const VER = 'planner-v2';
const SHELL = ['./', './index.html', './app.css', './config.js', './js/main.js', './js/db.js', './js/util.js', './js/model.js', './js/cloud.js', './js/ui.js', './js/sheets.js', './js/review.js', './manifest.webmanifest', './icons/icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('planner-') && k !== VER).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET') return;
  if (url.origin === location.origin) {
    // 화면 파일: 늘 새것을 먼저 확인하고, 안 되면 저장해 둔 것
    e.respondWith(fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VER).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: req.mode === 'navigate' }).then(hit => hit || caches.match('./index.html'))));
  } else if (url.hostname === 'cdn.jsdelivr.net') {
    // 글꼴·로그인 도구: 저장해 둔 것을 먼저 쓰고 뒤에서 새로 받아 둠
    e.respondWith(caches.open(VER).then(c => c.match(req).then(hit => {
      const fresh = fetch(req).then(res => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || fresh;
    })));
  }
});

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data.json(); } catch { d = { title: '업무 플래너', body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || '업무 플래너', {
    body: d.body || '', tag: d.tag, renotify: !!d.tag,
    icon: 'icons/icon-192.png', badge: 'icons/badge-96.png', data: { url: d.url || './?today' },
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL(e.notification.data?.url || './', self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
    for (const c of list) if (c.url.startsWith(self.registration.scope) && 'focus' in c) return c.focus();
    return self.clients.openWindow(url);
  }));
});
