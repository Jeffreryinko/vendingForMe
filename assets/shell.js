/* shell.js — 자판기 공통 껍데기 (시사·이야기·AI·역사·첫 화면).
 *
 *  1) 앱 전환 막대: 화면 맨 위에 [홈] [시사 | 이야기 | AI | 역사] [⋯] — 크게, 애플식 분할 버튼
 *  2) 뒤로가기 한 가지 규칙 (모든 앱 공통)
 *       · 앱 안에서 화면을 옮겨도 브라우저 기록은 쌓지 않는다 (각 앱이 replaceState 로 이동)
 *       · 휴대폰 뒤로가기 = "한 단계 위로": 열린 창 닫기 → 앞 화면 → 그 앱의 첫 화면 → 자판기 첫 화면(홈)
 *       · 앱끼리 옮겨 다닐 때도 기록을 쌓지 않음 → 뒤로가기가 다른 앱으로 튀지 않음
 *       · 홈에서 뒤로가기 = 자판기를 나감
 *     각 앱은 window.vfmApp = { back(): 처리했으면 true, go(hash): 그 화면으로 } 를 내놓는다.
 *  3) 설정 시트: 마지막 갱신, 기록 내보내기·불러오기, 출처 상태
 *  4) PWA 등록
 */
(function () {
  "use strict";
  var APP = (window.vfm && window.vfm.app) || window.VFM_APP || "sisa";
  var HOME = APP === "home";
  var ROOT = HOME ? "./" : "../";
  var APPS = [["sisa", "시사"], ["iyagi", "이야기"], ["ai", "AI"], ["history", "역사"]];
  var NAME = { home: "홈", sisa: "시사", iyagi: "이야기", ai: "AI", history: "역사" };
  try { if (!HOME) localStorage.setItem("vfm:tab", APP); } catch (e) { }

  /* ── 모양 (애플식, apple.css 의 색 변수를 씀) ── */
  var css = document.createElement("style");
  css.textContent =
    ".vfm-bar{position:relative;z-index:30;display:flex;align-items:center;gap:8px;max-width:720px;margin:0 auto;" +
    "padding:10px 0 6px;" +
    "font:600 15px/1 var(--ap-font);-webkit-user-select:none;user-select:none}" +
    ".vfm-bar .h{flex:none;width:40px;height:40px;border-radius:12px;border:0;background:var(--ap-fill);display:grid;place-items:center;color:var(--ap-label);cursor:pointer}" +
    ".vfm-bar .h svg{width:20px;height:20px}" +
    ".vfm-seg{flex:1;display:grid;grid-template-columns:repeat(4,1fr);gap:2px;padding:3px;border-radius:12px;background:var(--ap-fill);height:40px}" +
    ".vfm-seg button{border:0;border-radius:9px;background:transparent;color:var(--ap-label);font:inherit;font-size:14.5px;letter-spacing:-.02em;white-space:nowrap;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;-webkit-tap-highlight-color:transparent}" +
    ".vfm-seg button i{width:8px;height:8px;border-radius:50%;display:inline-block}" +
    ".vfm-seg button[aria-current=page]{background:var(--ap-seg-on);box-shadow:0 3px 8px rgba(0,0,0,.12),0 1px 1px rgba(0,0,0,.04);font-weight:700}" +
    ".vfm-dot{width:7px;height:7px;border-radius:50%;background:var(--ap-green);display:inline-block}.vfm-dot.old{background:var(--ap-orange)}.vfm-dot.none{background:var(--ap-label3)}" +
    ".vfm-back{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:9700;display:flex;align-items:flex-end;justify-content:center;animation:vfmFade .18s ease}" +
    ".vfm-sheet{width:100%;max-width:560px;max-height:88vh;overflow:auto;background:var(--ap-bg);color:var(--ap-label);border-radius:14px 14px 0 0;" +
    "padding:8px 16px calc(env(safe-area-inset-bottom,0px) + 20px);font:15px/1.45 var(--ap-font);animation:vfmUp .26s cubic-bezier(.2,.8,.2,1)}" +
    ".vfm-sheet .grab{width:36px;height:5px;border-radius:3px;background:var(--ap-label3);margin:0 auto 10px}" +
    ".vfm-sheet h3{margin:4px 4px 14px;font-size:22px;font-weight:700;letter-spacing:-.02em}" +
    ".vfm-sheet .cap{margin:18px 16px 6px;font-size:13px;color:var(--ap-label2);text-transform:none}" +
    ".vfm-sheet .grp{background:var(--ap-surface);border-radius:12px;overflow:hidden}" +
    ".vfm-sheet .grp>*{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;min-height:46px;padding:11px 16px;border:0;background:none;color:inherit;font:inherit;text-align:left;position:relative;cursor:pointer}" +
    ".vfm-sheet .grp>*+*::before{content:'';position:absolute;left:16px;right:0;top:0;height:.5px;background:var(--ap-sep)}" +
    ".vfm-sheet .grp .v{color:var(--ap-label2)}.vfm-sheet .grp .tint{color:var(--ap-tint)}" +
    ".vfm-sheet .foot{margin:6px 16px 0;font-size:12.5px;color:var(--ap-label2)}" +
    ".vfm-toast{position:fixed;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 96px);transform:translateX(-50%);background:rgba(30,30,30,.92);color:#fff;" +
    "padding:10px 16px;border-radius:14px;font:500 14px/1.3 var(--ap-font);z-index:9800;-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px)}" +
    "@keyframes vfmUp{from{transform:translateY(40px);opacity:.4}to{transform:none;opacity:1}}@keyframes vfmFade{from{opacity:0}to{opacity:1}}" +
    ".vfm-pill{display:none!important}";
  document.head.appendChild(css);

  function toast(msg) { var t = document.createElement("div"); t.className = "vfm-toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(function () { t.remove(); }, 2200); }
  function ago(iso) {
    if (!iso) return "기록 없음";
    var m = Math.round((Date.now() - Date.parse(iso)) / 60000);
    if (m < 1) return "방금"; if (m < 60) return m + "분 전";
    var h = Math.floor(m / 60); if (h < 48) return h + "시간 전";
    return Math.floor(h / 24) + "일 전";
  }
  function getJ(p) { return fetch(ROOT + p, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }

  /* ── 앱 사이 이동: 기록을 쌓지 않음 ── */
  function openApp(a) {
    if (a === APP) { if (window.vfmApp && window.vfmApp.top) window.vfmApp.top(); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
    if (a === "home") return goHome();
    var to = ROOT + a + "/";
    // 이 앱이 깔아 둔 뒤로가기 칸(top)을 먼저 걷고 바꿔 끼움 → 뒤로가기가 옛 앱으로 튀지 않음
    if (!HOME && history.state && history.state.vfm === "top") { switching = to; leaving = true; history.back(); setTimeout(function () { if (switching) location.replace(switching); }, 600); }
    else location.replace(to);
  }
  var switching = null;
  var homeTimer = null;
  function goHome() {
    // 홈에서 들어왔으면 진짜 뒤로(홈 화면이 그대로 남아 있음), 아니면 홈으로 바꿔 끼움
    var fromHome = false; try { fromHome = sessionStorage.getItem("vfm:fromHome") === "1"; } catch (e) { }
    if (fromHome && history.length > 1) {
      var st = history.state && history.state.vfm;
      leaving = true;
      history.go(st === "top" ? -2 : -1);
      homeTimer = setTimeout(function () { location.replace(ROOT); }, 800);   // 혹시 안 넘어가면
    } else location.replace(ROOT);
  }
  var leaving = false;
  window.addEventListener("pagehide", function () { clearTimeout(homeTimer); leaving = false; });
  // 홈이 아닌 바깥에서 바로 들어왔으면 '홈에서 왔음' 표시를 지움
  if (!HOME) {
    try {
      var ref = document.referrer || "", base = new URL(ROOT, location.href).href;
      if (!ref || ref.indexOf(base) !== 0) sessionStorage.removeItem("vfm:fromHome");
    } catch (e) { }
  }

  /* ── 위쪽 앱 전환 막대 ── */
  var meta = null, bar = null;
  if (!HOME) {
    bar = document.createElement("div"); bar.className = "vfm-bar"; bar.setAttribute("role", "navigation"); bar.setAttribute("aria-label", "자판기 앱");
    bar.innerHTML =
      '<button class="h" type="button" data-vfm="home" aria-label="자판기 홈"><svg viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="7.5" height="7.5" rx="2.2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="2.2"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="2.2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2.2"/></svg></button>' +
      '<div class="vfm-seg">' + APPS.map(function (a) {
        return '<button type="button" data-vfm="' + a[0] + '"' + (a[0] === APP ? ' aria-current="page"' : "") + ">" + (a[0] === APP ? '<span class="vfm-dot none"></span>' : "") + a[1] + "</button>";
      }).join("") + "</div>" +
      '<button class="h" type="button" data-vfm="settings" aria-label="설정"><svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg></button>';
    document.body.insertBefore(bar, document.body.firstChild);
    bar.addEventListener("click", function (e) {
      var b = e.target.closest("[data-vfm]"); if (!b) return;
      var a = b.getAttribute("data-vfm");
      if (a === "settings") return openSheet();
      openApp(a);
    });
  }
  function paintDot() {
    var dot = document.querySelector(".vfm-seg .vfm-dot"); if (!dot) return;
    dot.className = "vfm-dot " + (!meta || !meta.updatedAt ? "none" : (Date.now() - Date.parse(meta.updatedAt) > (APP === "sisa" ? 6 : 30) * 3600e3 ? "old" : ""));
    dot.title = meta && meta.updatedAt ? "마지막 갱신 " + ago(meta.updatedAt) : "갱신 기록 없음";
  }
  function loadMeta() { if (HOME) return; return getJ("data/" + APP + "/_meta.json").then(function (m) { meta = m; paintDot(); }); }

  /* ── 뒤로가기 (한 단계 위로) ── */
  var touched = false;
  function arm() {
    try { if (!(history.state && history.state.vfm === "top")) history.pushState({ vfm: "top" }, "", location.href); } catch (e) { }
  }
  // 지금 보이는 화면 주소를 늘 기억 (뒤로가기 때 브라우저가 옛 주소로 되돌려 놓는 것을 바로잡으려고)
  var curUrl = location.href;
  ["pushState", "replaceState"].forEach(function (k) {
    var orig = history[k];
    history[k] = function () { var r = orig.apply(history, arguments); curUrl = location.href; return r; };
  });
  window.addEventListener("hashchange", function () { curUrl = location.href; });
  if (!HOME) {
    try { if (!(history.state && (history.state.vfm === "top" || history.state.vfm === "base"))) history.replaceState({ vfm: "base" }, "", location.href); } catch (e) { }
    // 브라우저는 사람이 화면을 누른 뒤에 만든 기록만 뒤로가기에서 인정함 → 첫 터치 때 한 칸 깔아 둠
    var onTouch = function () { touched = true; if (!(history.state && history.state.vfm === "top")) arm(); };
    document.addEventListener("click", onTouch, true);
    document.addEventListener("touchend", onTouch, { capture: true, passive: true });
    window.addEventListener("popstate", function (e) {
      var st = e.state && e.state.vfm;
      if (switching) { var to = switching; switching = null; location.replace(to); return; }
      if (leaving) return;                              // 홈으로 가는 중
      if (st === "top") return;
      if (st !== "base") { if (window.vfmApp && window.vfmApp.route) window.vfmApp.route(); return; }
      if (location.href !== curUrl) { var shown = curUrl; try { history.replaceState({ vfm: "base" }, "", shown); } catch (x) { } }
      var done = false;
      var sh = document.querySelector(".vfm-back"); if (sh) { sh.remove(); done = true; }
      if (!done && window.vfmApp && window.vfmApp.back) { try { done = !!window.vfmApp.back(); } catch (x) { done = false; } }
      if (done) { if (touched) arm(); return; }
      goHome();                                         // 앱 첫 화면에서 뒤로 → 자판기 홈
    });
  }

  /* ── 바깥 링크 갔다 오면 그 자리로 (앱이 go 를 내놓으면 기록 없이 이동) ── */
  window.vfm = window.vfm || {};
  window.vfm.goHash = function (h) {
    if (window.vfmApp && window.vfmApp.go) return window.vfmApp.go(h);
    try { history.replaceState(history.state, "", location.pathname + location.search + h); } catch (e) { }
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  };

  /* ── 설정 시트 ── */
  function openSheet() {
    var back = document.createElement("div"); back.className = "vfm-back";
    var kb = window.vfm && window.vfm.storageBytes ? Math.round(window.vfm.storageBytes() / 1024) : 0;
    back.innerHTML =
      '<div class="vfm-sheet" role="dialog" aria-label="자판기 설정"><div class="grab"></div><h3>설정</h3>' +
      '<div class="cap">마지막 갱신</div><div class="grp" id="vfmUpd">' + APPS.map(function (a) { return '<div data-u="' + a[0] + '"><span>' + a[1] + '</span><span class="v">…</span></div>'; }).join("") + "</div>" +
      '<div class="cap">내 기록</div><div class="grp">' +
      '<button type="button" data-act="export"><span class="tint">기록 내보내기</span><span class="v">파일 하나로</span></button>' +
      '<button type="button" data-act="import"><span class="tint">기록 불러오기</span><span class="v">›</span></button>' +
      "<div><span>이 폰에 저장된 양</span><span class=\"v\">" + kb.toLocaleString() + " KB / 약 5,000 KB</span></div></div>" +
      '<p class="foot">읽은 기록·별표·메모는 이 폰 브라우저 안에만 있어요. 폰을 바꾸거나 PC로 옮길 땐 내보내기 → 새 기기에서 불러오기.</p>' +
      '<div class="cap">출처 상태</div><div class="grp" id="vfmHealth"><div><span>확인 중…</span></div></div>' +
      '<div class="cap"></div><div class="grp"><button type="button" data-act="reload"><span class="tint">새로고침</span></button>' +
      (HOME ? "" : '<button type="button" data-act="home"><span class="tint">자판기 홈으로</span></button>') + "</div>" +
      '<input type="file" accept="application/json" hidden></div>';
    document.body.appendChild(back);
    APPS.forEach(function (a) {
      getJ("data/" + a[0] + "/_meta.json").then(function (m) { var el = back.querySelector('[data-u="' + a[0] + '"] .v'); if (el) el.textContent = m && m.updatedAt ? ago(m.updatedAt) + (m.label ? " · " + m.label : "") : "기록 없음"; });
    });
    Promise.all([getJ("data/trends/_index.json"), getJ("data/ai/_index.json"), getJ("data/history/_index.json")]).then(function (r) {
      var el = back.querySelector("#vfmHealth"); if (!el) return;
      var rows = [["트렌드", r[0]], ["AI", r[1]], ["역사", r[2]]].map(function (x) {
        var ks = Object.keys((x[1] && x[1].broken) || {});
        return "<div><span>" + x[0] + '</span><span class="v">' + (x[1] ? (ks.length ? "고장 " + ks.length + "곳: " + ks.slice(0, 3).join(", ") : "모두 정상") : "자료 없음") + "</span></div>";
      });
      el.innerHTML = rows.join("");
    });
    var input = back.querySelector("input");
    back.addEventListener("click", function (e) {
      if (e.target === back) return back.remove();
      var b = e.target.closest("[data-act]"); if (!b) return;
      var act = b.getAttribute("data-act");
      if (act === "reload") location.reload();
      else if (act === "home") { back.remove(); goHome(); }
      else if (act === "export") {
        var data = JSON.stringify(window.vfm.exportAll());
        var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([data], { type: "application/json" }));
        a.download = "vendingForMe-기록-" + new Date().toISOString().slice(0, 10) + ".json"; a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000); toast("내보냈어요");
      } else if (act === "import") input.click();
    });
    input.addEventListener("change", function () {
      var f = input.files[0]; if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        try { var n = window.vfm.importAll(JSON.parse(r.result)); toast(n + "개 항목을 불러왔어요"); setTimeout(function () { location.reload(); }, 900); }
        catch (e) { toast("불러오기 실패: " + e.message); }
      };
      r.readAsText(f);
    });
  }
  window.vfm.openSettings = openSheet;
  window.vfm.openApp = openApp;
  window.vfm.toast = toast;

  /* ── PWA ── */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register(ROOT + "sw.js", { scope: ROOT }).catch(function () { }); });
  }
  if (!document.querySelector('link[rel="manifest"]')) {
    var l = document.createElement("link"); l.rel = "manifest"; l.href = ROOT + "manifest.webmanifest"; document.head.appendChild(l);
  }
  loadMeta();
  setInterval(loadMeta, 15 * 60 * 1000);
})();
