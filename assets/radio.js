/* radio.js — 홈의 "▶ 라디오". 로봇(robot/radio_run.py)이 무료 음성 MeloTTS 로 만든 소리 파일(data/radio/)을 차례로 틀어 줌.
 *  · 화면을 꺼도 계속(소리 파일이라서), 잠금 화면·이어폰 단추로 재생·멈춤·다음·이전 (Media Session)
 *  · 어디까지 들었는지 폰에 기억 → 다시 누르면 이어서
 *  · 지금 듣는 조각의 '카드 보기'로 그 카드를 열 수 있음
 */
(function () {
  "use strict";
  var BASE = "data/radio/", KEY = "vfm:radio";
  var R = null, i = 0, au = new Audio(); au.preload = "auto";
  var st = (function () { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; } })();
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var toast = function (m) { if (window.vfm && vfm.toast) vfm.toast(m); };
  function save() { try { localStorage.setItem(KEY, JSON.stringify({ slot: R && R.slot, i: i, t: Math.floor(au.currentTime || 0) })); } catch (e) { } }
  function load() {
    return fetch(BASE + "_index.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (x) { R = x && x.items && x.items.length ? x : null; return R; }, function () { return null; });
  }
  var KIND = { intro: "자판기 라디오", sisa: "시사", trend: "트렌드", ai: "AI 소식" };
  function bar() {
    var b = document.getElementById("rdBar");
    if (!b) { b = document.createElement("div"); b.id = "rdBar"; b.className = "rd-bar"; document.body.appendChild(b); }
    if (!R) { b.hidden = true; document.body.classList.remove("rd-on"); return; }
    var it = R.items[i] || {}, playing = !au.paused;
    b.hidden = false; document.body.classList.add("rd-on");
    b.innerHTML = '<div class="rd-info"><span class="rd-k">' + esc(KIND[it.kind] || "") + " · " + (i + 1) + "/" + R.items.length + " · " + esc(R.label || "") + '</span><b class="rd-t">' + esc(it.title || "") + "</b></div>" +
      '<div class="rd-btns"><button type="button" data-rd="prev" aria-label="이전">⏮</button><button type="button" data-rd="toggle" class="rd-play" aria-label="' + (playing ? "멈춤" : "재생") + '">' + (playing ? "⏸" : "▶") + '</button><button type="button" data-rd="next" aria-label="다음">⏭</button>' +
      (it.link ? '<button type="button" data-rd="card" aria-label="카드 보기">카드</button>' : "") + '<button type="button" data-rd="close" aria-label="라디오 닫기">✕</button></div>';
    var btn = document.getElementById("rdBtn"); if (btn) btn.textContent = playing ? "⏸ 라디오" : "▶ 라디오";
  }
  function media() {
    if (!("mediaSession" in navigator) || !R) return;
    var it = R.items[i] || {};
    try {
      navigator.mediaSession.metadata = new MediaMetadata({ title: it.title || "자판기 라디오", artist: "자판기 라디오 · " + (KIND[it.kind] || ""), album: R.label || "",
        artwork: [{ src: "assets/icon-192.png", sizes: "192x192", type: "image/png" }, { src: "assets/icon-512.png", sizes: "512x512", type: "image/png" }] });
    } catch (e) { }
  }
  function playAt(k, from) {
    if (!R) return;
    i = Math.max(0, Math.min(R.items.length - 1, k));
    au.src = BASE + R.items[i].file; au.currentTime = 0;
    if (from) au.addEventListener("loadedmetadata", function f() { au.currentTime = from; au.removeEventListener("loadedmetadata", f); });
    au.play().catch(function () { toast("재생을 시작하지 못했어요. 한 번 더 눌러 주세요"); });
    media(); bar(); save();
  }
  au.addEventListener("ended", function () { if (R && i < R.items.length - 1) playAt(i + 1); else { i = 0; save(); bar(); toast("오늘 라디오를 다 들었어요"); } });
  au.addEventListener("play", bar); au.addEventListener("pause", function () { bar(); save(); });
  setInterval(function () { if (!au.paused) save(); }, 5000);
  if ("mediaSession" in navigator) {
    var h = { play: function () { au.play(); }, pause: function () { au.pause(); }, nexttrack: function () { playAt(i + 1); }, previoustrack: function () { playAt(i - 1); } };
    Object.keys(h).forEach(function (k) { try { navigator.mediaSession.setActionHandler(k, h[k]); } catch (e) { } });
  }
  function start() {
    if (R && au.src) { if (au.paused) au.play(); else au.pause(); return; }
    load().then(function (x) {
      if (!x) return toast("라디오가 아직 없어요. 아침 8시·저녁 8시쯤 로봇이 만들어요");
      var resume = st.slot === x.slot && st.i < x.items.length;
      playAt(resume ? st.i : 0, resume ? st.t : 0);
      toast(resume ? "듣던 곳부터 이어서 틀어요" : x.label + " · 약 " + Math.max(1, Math.round((x.sec || 0) / 60)) + "분");
    });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("#rdBtn,[data-rd]"); if (!b) return;
    if (b.id === "rdBtn") return start();
    var a = b.getAttribute("data-rd");
    if (a === "toggle") { if (au.paused) au.play(); else au.pause(); }
    else if (a === "next") playAt(i + 1);
    else if (a === "prev") playAt(au.currentTime > 4 ? i : i - 1);
    else if (a === "close") { au.pause(); save(); document.getElementById("rdBar").hidden = true; document.body.classList.remove("rd-on"); }
    else if (a === "card") { var it = R.items[i]; if (it && it.link) { try { sessionStorage.setItem("vfm:fromHome", "1"); sessionStorage.setItem("vfm:fromCard", "#" + (it.link.split("#")[1] || "")); } catch (x) { } location.href = it.link; } }
  });
  // 홈 위쪽(찾기 줄)에 단추 넣기
  function addBtn() {
    var top = document.querySelector(".mx-top"); if (!top) return setTimeout(addBtn, 300);
    if (document.getElementById("rdBtn")) return;
    var b = document.createElement("button"); b.type = "button"; b.id = "rdBtn"; b.textContent = "▶ 라디오"; b.setAttribute("aria-label", "라디오로 듣기");
    top.insertBefore(b, top.firstChild);
  }
  addBtn();
  var css = document.createElement("style");
  css.textContent = "#rdBtn{flex:none;border:0;border-radius:12px;padding:0 12px;font:inherit;font-weight:700;background:var(--ap-blue);color:#fff;white-space:nowrap}" +
    ".rd-bar{position:fixed;left:8px;right:8px;bottom:calc(env(safe-area-inset-bottom,0px) + 8px);z-index:9500;display:flex;align-items:center;gap:8px;padding:10px 10px 10px 14px;border-radius:16px;" +
    "background:var(--ap-bar,rgba(249,249,249,.92));-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);box-shadow:0 6px 24px rgba(0,0,0,.18);max-width:560px;margin:0 auto}" +
    ".rd-info{flex:1;min-width:0;display:flex;flex-direction:column}.rd-k{font-size:11.5px;color:var(--ap-label2)}.rd-t{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".rd-btns{display:flex;gap:4px;flex:none}.rd-btns button{border:0;border-radius:10px;min-width:36px;height:36px;background:var(--ap-fill);color:var(--ap-label);font:inherit;font-size:15px}" +
    ".rd-btns .rd-play{background:var(--ap-blue);color:#fff}body.rd-on{padding-bottom:calc(env(safe-area-inset-bottom,0px) + 96px)!important}";
  document.head.appendChild(css);
})();
