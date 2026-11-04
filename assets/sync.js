/* sync.js — 구글 로그인으로 폰·PC 기록 이어 보기 (Supabase 무료, 토큰 0).
 *  · 로그인하지 않으면 아무것도 하지 않음 (지금처럼 이 폰 안에만 저장)
 *  · 로그인하면: 이 기기의 기록(vfm:* · 담아둔 이야기)을 내 계정 칸에 올리고, 다른 기기에서 바뀐 것을 받아 합침
 *  · 표: public.kv (user_id, k, v, ts) — 행 보안(RLS)으로 각자 자기 것만 읽고 씀
 *  · 설정: assets/sync-config.js 의 window.VFM_SYNC = { url, key } (공개용 키라 저장소에 있어도 됨)
 */
(function () {
  "use strict";
  var CFG = window.VFM_SYNC || {};
  var META = "vfm-sync-meta";                                     // vfm: 로 시작하지 않게 (자기 자신은 올리지 않음)
  var SKIP = /^vfm:(mode:|deck:|tab$|trc|mix:si$)/;               // 화면 상태·임시 값은 올리지 않음
  var EXTRA = ["iyagi-library-v1", "iyagi-extra-v1"];
  var client = null, user = null, busy = false, timer = null;
  var api = window.vfmSync = { ready: !!(CFG.url && CFG.key && CFG.google), user: function () { return user; }, login: login, logout: logout, now: function () { return run(true); }, status: "" };

  function syncKeys() {
    var out = [];
    for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if ((k.indexOf("vfm:") === 0 && !SKIP.test(k)) || EXTRA.indexOf(k) >= 0) out.push(k); }
    return out;
  }
  function h(s) { var x = 5381; for (var i = 0; i < s.length; i++) x = ((x << 5) + x + s.charCodeAt(i)) | 0; return s.length + ":" + (x >>> 0).toString(36); }
  function meta() { try { return JSON.parse(localStorage.getItem(META)) || { h: {}, pulled: 0 }; } catch (e) { return { h: {}, pulled: 0 }; } }
  function setMeta(m) { try { localStorage.setItem(META, JSON.stringify(m)); } catch (e) { } }
  var stamp = function (o) { return o && typeof o === "object" ? (o.ed || o.at || (o.updatedAt ? Date.parse(o.updatedAt) : 0) || 0) : 0; };
  // 두 기기에서 모두 바뀐 값 합치기: 목록은 id 기준, 사전은 칸마다 최신 것, 나머지는 받은 것
  function merge(a, b) {
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.concat(b).every(function (x) { return x && typeof x === "object" && x.id; })) {
        var m = {}; a.concat(b).forEach(function (x) { if (!m[x.id] || stamp(x) >= stamp(m[x.id])) m[x.id] = x; });
        return Object.keys(m).map(function (k) { return m[k]; }).sort(function (x, y) { return stamp(y) - stamp(x); });
      }
      return a.concat(b.filter(function (x) { return a.indexOf(x) < 0; }));
    }
    if (a && b && typeof a === "object" && typeof b === "object") {
      var o = {}; Object.keys(a).forEach(function (k) { o[k] = a[k]; });
      Object.keys(b).forEach(function (k) {
        if (!(k in o)) o[k] = b[k];
        else if (typeof o[k] === "number" && typeof b[k] === "number") o[k] = Math.max(o[k], b[k]);
        else if (stamp(b[k]) > stamp(o[k])) o[k] = b[k];
        else if (o[k] && b[k] && typeof o[k] === "object" && typeof b[k] === "object" && !stamp(o[k]) && !stamp(b[k])) o[k] = merge(o[k], b[k]);
      });
      return o;
    }
    return b;
  }
  function load() {
    if (client) return Promise.resolve(client);
    return new Promise(function (ok, no) {
      var s = document.createElement("script"); s.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js";
      s.onload = function () { client = window.supabase.createClient(CFG.url, CFG.key, { auth: { persistSession: true, detectSessionInUrl: true, flowType: "pkce" } }); ok(client); };
      s.onerror = function () { no(new Error("로그인 도구를 못 받았어요")); }; document.head.appendChild(s);
    });
  }
  function login() {
    if (!api.ready) return Promise.reject(new Error("아직 준비 중이에요"));
    return load().then(function (c) { return c.auth.signInWithOAuth({ provider: "google", options: { redirectTo: location.origin + location.pathname } }); });
  }
  function logout() { return load().then(function (c) { return c.auth.signOut(); }).then(function () { user = null; localStorage.removeItem(META); paint(); }); }

  function run(manual) {
    if (!user || busy) return Promise.resolve();
    busy = true; api.status = "맞추는 중…"; paint();
    var m = meta(), changed = 0;
    return client.from("kv").select("k,v,ts").gt("ts", m.pulled || 0).then(function (r) {
      if (r.error) throw r.error;
      (r.data || []).forEach(function (row) {
        var raw = localStorage.getItem(row.k), local = null;
        try { local = raw == null ? null : JSON.parse(raw); } catch (e) { local = raw; }
        var mine = raw != null && m.h[row.k] !== h(raw);            // 이 기기에서도 지난번 맞춘 뒤 바뀜 → 합침
        var v = mine ? merge(local, row.v) : row.v, s = typeof v === "string" ? v : JSON.stringify(v);
        if (s !== raw) { try { localStorage.setItem(row.k, s); changed++; } catch (e) { } }
        m.h[row.k] = mine ? "" : h(s);
        if (row.ts > m.pulled) m.pulled = row.ts;
      });
      var up = syncKeys().filter(function (k) { return m.h[k] !== h(localStorage.getItem(k) || ""); }).map(function (k) {
        var raw = localStorage.getItem(k), v; try { v = JSON.parse(raw); } catch (e) { v = raw; }
        return { k: k, v: v, ts: Date.now() };
      });
      if (!up.length) return null;
      return client.from("kv").upsert(up.map(function (x) { return { user_id: user.id, k: x.k, v: x.v, ts: x.ts }; }), { onConflict: "user_id,k" }).then(function (w) {
        if (w.error) throw w.error;
        up.forEach(function (x) { m.h[x.k] = h(localStorage.getItem(x.k) || ""); if (x.ts > m.pulled) m.pulled = x.ts; });
      });
    }).then(function () {
      setMeta(m); busy = false; api.status = "맞춤 " + new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }); paint();
      if (changed && !sessionStorage.getItem("vfm:syncReload")) { sessionStorage.setItem("vfm:syncReload", "1"); location.reload(); }   // 다른 기기 기록을 받았으면 화면을 한 번 새로
      else if (manual && window.vfm && window.vfm.toast) window.vfm.toast(changed ? "다른 기기 기록을 받았어요" : "기록을 맞췄어요");
    }).catch(function (e) { busy = false; api.status = "맞추기 실패 — 다음에 다시"; paint(); if (manual && window.vfm && window.vfm.toast) window.vfm.toast("맞추기 실패: " + (e.message || "오류")); });
  }
  function paint() { var el = document.getElementById("vfmSync"); if (el && api.render) el.innerHTML = api.render(); }

  // 로그인한 적이 있을 때만 도구를 받음 (처음 방문은 가볍게)
  var hasSession = false; for (var i = 0; i < localStorage.length; i++) if (/^sb-.*-auth-token/.test(localStorage.key(i))) hasSession = true;
  if (api.ready && (hasSession || /[?&#](code|access_token)=/.test(location.href))) {
    load().then(function (c) {
      c.auth.onAuthStateChange(function (ev, s) { user = s && s.user || null; paint(); if (user && ev === "SIGNED_IN") run(); });
      return c.auth.getSession();
    }).then(function (r) {
      user = (r && r.data && r.data.session && r.data.session.user) || null; paint();
      if (!user) return;
      run();
      timer = setInterval(run, 120000);
      document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") run(); });
    }).catch(function () { });
  }
})();
