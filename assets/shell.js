/* shell.js — 두 앱(시사·이야기)에 공통으로 붙는 껍데기.
 *   · 오른쪽 아래 작은 알약 버튼: 다른 탭으로 전환 / 길게 누르면 설정
 *   · 설정: 마지막 갱신 시각, 기록 내보내기·불러오기, 저장 용량
 *   · PWA(홈화면 앱) 등록
 */
(function () {
  "use strict";
  var APP = (window.vfm && window.vfm.app) || "sisa";
  var OTHER = APP === "sisa" ? "iyagi" : "sisa";
  var NAME = { sisa: "시사", iyagi: "이야기" };
  try { localStorage.setItem("vfm:tab", APP); } catch (e) { }

  /* ── 스타일 ── */
  var css = document.createElement("style");
  css.textContent =
    ".vfm-pill{position:fixed;right:max(12px,env(safe-area-inset-right,0px));bottom:calc(env(safe-area-inset-bottom,0px) + 74px);z-index:9000;" +
    "display:flex;align-items:center;gap:6px;padding:7px 12px;border-radius:999px;border:1px solid rgba(127,127,127,.35);" +
    "background:rgba(250,250,250,.92);color:#222;font:600 13px/1 -apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;" +
    "box-shadow:0 4px 16px rgba(0,0,0,.18);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);cursor:pointer;user-select:none;-webkit-user-select:none;-webkit-tap-highlight-color:transparent}" +
    "@media (prefers-color-scheme:dark){.vfm-pill{background:rgba(32,38,42,.92);color:#eee;border-color:rgba(255,255,255,.18)}}" +
    ".vfm-pill i{width:7px;height:7px;border-radius:50%;background:#2F7D4F;display:inline-block}.vfm-pill i.old{background:#E3A35C}.vfm-pill i.none{background:#999}" +
    ".vfm-back{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9001;display:flex;align-items:flex-end;justify-content:center}" +
    ".vfm-sheet{width:100%;max-width:560px;background:#fff;color:#222;border-radius:18px 18px 0 0;padding:16px 18px calc(env(safe-area-inset-bottom,0px) + 18px);" +
    "font:15px/1.55 -apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif}" +
    "@media (prefers-color-scheme:dark){.vfm-sheet{background:#1b262b;color:#eaf1f2}}" +
    ".vfm-sheet h3{margin:0 0 8px;font-size:17px}.vfm-sheet p{margin:4px 0;font-size:13.5px;opacity:.8}" +
    ".vfm-sheet .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}" +
    ".vfm-sheet button{font:inherit;font-size:14px;font-weight:600;padding:9px 14px;border-radius:10px;border:1px solid rgba(127,127,127,.4);background:transparent;color:inherit;cursor:pointer}" +
    ".vfm-sheet button.pri{background:#0C6E77;color:#fff;border-color:#0C6E77}" +
    ".vfm-toast{position:fixed;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 130px);transform:translateX(-50%);background:#222;color:#fff;padding:8px 14px;border-radius:10px;font-size:13px;z-index:9002}";
  document.head.appendChild(css);

  /* ── 마지막 갱신 ── */
  var meta = null;
  function ago(iso) {
    if (!iso) return "기록 없음";
    var m = Math.round((Date.now() - Date.parse(iso)) / 60000);
    if (m < 1) return "방금";
    if (m < 60) return m + "분 전";
    var h = Math.floor(m / 60); if (h < 48) return h + "시간 " + (m % 60) + "분 전";
    return Math.floor(h / 24) + "일 전";
  }
  function loadMeta() {
    return fetch("../data/" + APP + "/_meta.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { meta = m; paintDot(); return m; }).catch(function () { meta = null; paintDot(); });
  }
  function paintDot() {
    var dot = document.querySelector(".vfm-pill i"); if (!dot) return;
    dot.className = !meta || !meta.updatedAt ? "none" : (Date.now() - Date.parse(meta.updatedAt) > 6 * 3600e3 ? "old" : "");
    pill.title = meta && meta.updatedAt ? "마지막 갱신 " + ago(meta.updatedAt) : "갱신 기록 없음";
  }

  /* ── 알약 버튼 ── */
  var pill = document.createElement("button");
  pill.className = "vfm-pill"; pill.type = "button";
  pill.innerHTML = "<i></i><span>" + NAME[OTHER] + "로 →</span>";
  var pressTimer = null, longPressed = false;
  function go() { location.href = "../" + OTHER + "/"; }
  pill.addEventListener("click", function () { if (longPressed) { longPressed = false; return; } go(); });
  pill.addEventListener("touchstart", function () { pressTimer = setTimeout(function () { longPressed = true; openSheet(); }, 550); }, { passive: true });
  pill.addEventListener("touchend", function () { clearTimeout(pressTimer); }, { passive: true });
  pill.addEventListener("touchmove", function () { clearTimeout(pressTimer); }, { passive: true });
  pill.addEventListener("contextmenu", function (e) { e.preventDefault(); longPressed = true; openSheet(); });
  document.body.appendChild(pill);

  /* ── 설정 시트 ── */
  function toast(msg) { var t = document.createElement("div"); t.className = "vfm-toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(function () { t.remove(); }, 2200); }
  function openSheet() {
    var back = document.createElement("div"); back.className = "vfm-back";
    var kb = window.vfm && window.vfm.storageBytes ? Math.round(window.vfm.storageBytes() / 1024) : 0;
    back.innerHTML =
      '<div class="vfm-sheet" role="dialog">' +
      "<h3>자판기 설정</h3>" +
      "<p>지금 보는 탭: <b>" + NAME[APP] + "</b> · 마지막 갱신: <b>" + (meta && meta.updatedAt ? ago(meta.updatedAt) : "기록 없음") + "</b>" + (meta && meta.label ? " (" + meta.label + ")" : "") + "</p>" +
      "<p>읽은 기록은 이 폰 브라우저 안에만 저장돼요 (" + kb + "KB 사용 / 약 5,000KB). 폰을 바꾸거나 PC로 옮길 땐 아래 버튼으로 파일 하나로 내보내세요.</p>" +
      '<div class="row"><button class="pri" data-act="export">기록 내보내기</button><button data-act="import">기록 불러오기</button>' +
      '<button data-act="other">' + NAME[OTHER] + ' 탭으로</button><button data-act="reload">새로고침</button><button data-act="close">닫기</button></div>' +
      '<p class="vfm-broken"></p>' +
      '<input type="file" accept="application/json" hidden></div>';
    document.body.appendChild(back);
    if (APP === "sisa") fetch("../data/trends/_index.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      var el = back.querySelector(".vfm-broken"); if (!el || !j) return;
      var ks = Object.keys(j.broken || {});
      el.textContent = ks.length ? "트렌드 고장 난 출처 (3일 넘게 실패): " + ks.join(", ") + " — 클로드에게 '트렌드 출처 고쳐줘'라고 하면 돼요." : "트렌드 출처: 모두 정상";
    }).catch(function () {});
    var input = back.querySelector("input");
    back.addEventListener("click", function (e) {
      if (e.target === back) return back.remove();
      var act = e.target.getAttribute && e.target.getAttribute("data-act"); if (!act) return;
      if (act === "close") back.remove();
      else if (act === "other") go();
      else if (act === "reload") location.reload();
      else if (act === "export") {
        var data = JSON.stringify(window.vfm.exportAll());
        var blob = new Blob([data], { type: "application/json" });
        var a = document.createElement("a"); a.href = URL.createObjectURL(blob);
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

  /* ── PWA ── */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("../sw.js", { scope: "../" }).catch(function () { }); });
  }
  if (!document.querySelector('link[rel="manifest"]')) {
    var l = document.createElement("link"); l.rel = "manifest"; l.href = "../manifest.webmanifest"; document.head.appendChild(l);
  }
  loadMeta();
  setInterval(loadMeta, 15 * 60 * 1000);
})();
