/* sw.js — 홈화면 앱(PWA)용. 앱 껍데기는 미리 저장, 데이터는 네트워크 우선 + 실패하면 마지막 저장본. */
const VER = "vfm-v3";
const SHELL = ["./", "./index.html", "./sisa/", "./sisa/index.html", "./iyagi/", "./iyagi/index.html",
  "./assets/claude-shim.js", "./assets/shell.js", "./manifest.webmanifest"];

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
  if (req.url.includes("/data/iyagi/orig/")) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) caches.open(VER).then(c => c.put(req, res.clone()));
      return res;
    }).catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});
