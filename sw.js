/* sw.js — 홈화면 앱(PWA)용. 앱 껍데기는 미리 저장, 데이터는 네트워크 우선 + 실패하면 마지막 저장본. */
const VER = "vfm-v145-calm";
const SHELL = ["./", "./index.html", "./sisa/", "./sisa/index.html", "./ai/", "./ai/index.html", "./tools/", "./tools/index.html", "./deal/", "./deal/index.html", "./box/", "./box/index.html", "./deal/learn/", "./deal/learn/index.html", "./ai/learn/", "./ai/learn/index.html", "./ai/learn/terms.js", "./ai/learn/course.js", "./ai/learn/history.js", "./ai/learn/figs.js", "./ai/learn/art.js", "./deal/learn/terms.js", "./deal/learn/figs.js", "./deal/learn/course.js", "./deal/learn/history.js", "./sisa/learn/", "./sisa/learn/index.html", "./sisa/learn/terms.js", "./sisa/learn/figs.js", "./sisa/learn/course.js", "./sisa/learn/history.js", "./gicho/", "./gicho/index.html", "./gicho/terms.js", "./gicho/terms2.js", "./gicho/figs.js", "./gicho/course.js", "./gicho/course1b.js", "./gicho/course2.js", "./gicho/course3.js", "./gicho/history.js", "./gicho/history2.js", "./gicho/history3.js", "./gicho/figs2.js", "./gicho/art.js", "./sisa/learn/deep.js", "./assets/learn.js", "./assets/learn.css", "./assets/learnart.js", "./assets/wikigal.js", "./sisa/learn/art.js", "./deal/learn/art.js",
  "./assets/claude-shim.js", "./assets/deck.js", "./assets/today.js", "./assets/trendcard.js", "./assets/mix.js", "./assets/radio.js", "./assets/shell.js", "./assets/polish.css", "./assets/sync.js", "./assets/sync-config.js", "./assets/apple.css", "./assets/hot.js", "./assets/history-player.js", "./assets/history-player.css", "./assets/wikithumb.js", "./manifest.webmanifest"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VER).then(c => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VER).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // 원문(orig)은 크니까 저장하지 않고 그대로
  if (req.url.includes("/data/iyagi/orig/") || req.url.includes("_more.json") || req.url.includes("/data/history/s/")) return;
  // 라디오 소리 파일은 저장하지 않고 그대로 (이어 듣기·되감기가 되게)
  if (req.url.includes("/data/radio/") && req.url.endsWith(".mp3")) return;
  // 화면(HTML)은 브라우저 저장본(최대 10분)을 건너뛰고 늘 서버에 새로 확인 — 올린 직후에도 바로 바뀌게
  const fresh = req.mode === "navigate" || req.url.endsWith(".html") || req.url.endsWith("/") || req.url.includes("/data/");
  e.respondWith(
    fetch(req, fresh ? { cache: "no-cache" } : undefined).then(res => {
      if (res.ok) caches.open(VER).then(c => c.put(req, res.clone()));
      return res;
    }).catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});

/* 알림(웹 푸시): 수파베이스 → 이 폰. 누르면 해당 화면으로 */
self.addEventListener("push", e => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(d.title || "자판기", {
    body: d.body || "", tag: d.tag || "vfm", data: { url: d.url || "./" },
    icon: "./assets/icon-192.png", badge: "./assets/icon-192.png", renotify: !!d.tag,
  }));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = new URL(e.notification.data && e.notification.data.url || "./", self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
    for (const c of list) if (c.url.split("#")[0] === url.split("#")[0] && "focus" in c) { c.navigate(url).catch(() => {}); return c.focus(); }
    return self.clients.openWindow(url);
  }));
});
