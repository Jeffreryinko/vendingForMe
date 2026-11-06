/* radio.js — 자판기 라디오. 로봇(robot/radio_run.py)이 무료 음성 MeloTTS 로 만든 소리 파일(data/radio/)을 차례로 틀어 줌.
 *  · 홈의 "▶ 라디오"로 시작. 모든 화면(시사·이야기·AI·역사·도구)에 이 부품이 들어 있어서,
 *    다른 화면·앱으로 옮겨도 듣던 곳부터 바로 이어서 재생 (껍데기 assets/shell.js 가 불러 줌)
 *  · 제목만 듣기 / 자세히 듣기(제목 + 내용) 고르기, 배속, 화면 꺼도 계속, 잠금 화면 재생·멈춤·다음·이전
 *  · 어디까지 들었는지 폰에 기억
 */
(function () {
  "use strict";
  if (window.__vfmRadio) return; window.__vfmRadio = true;
  var HOME = window.VFM_APP === "home", ROOT = HOME ? "" : "../";
  var BASE = ROOT + "data/radio/", KEY = "vfm:radio";
  var R = null, steps = [], s = 0, au = new Audio(); au.preload = "auto";
  var LS = { g: function (k, d) { try { var v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, s: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } } };
  var SPEEDS = [1, 1.25, 1.5, 1.75, 2, 0.75], speed = +LS.g("vfm:radio:speed", 1) || 1;
  var mode = LS.g("vfm:radio:mode", "full");                          // "title" = 제목만, "full" = 제목 + 내용
  function applySpeed() { au.defaultPlaybackRate = speed; au.playbackRate = speed; try { au.preservesPitch = true; } catch (e) { } }
  applySpeed();
  var st = LS.g(KEY, {});
  var esc = function (x) { return String(x == null ? "" : x).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var toast = function (m) { if (window.vfm && vfm.toast) vfm.toast(m); };
  var KIND = { intro: "자판기 라디오", sisa: "시사", trend: "트렌드", ai: "AI 소식" };

  // 들을 순서: 제목만이면 조각마다 제목 소리, 자세히면 제목 → 내용
  function build() {
    steps = [];
    (R.items || []).forEach(function (it, i) {
      if (it.file) { steps.push({ i: i, f: it.file }); return; }               // 예전 모양(조각 하나 = 파일 하나)
      if (it.t) steps.push({ i: i, f: it.t });
      if (it.b && (mode === "full" || !it.t)) steps.push({ i: i, f: it.b });
    });
  }
  function save(playing) { LS.s(KEY, { slot: R && R.slot, s: s, f: steps[s] && steps[s].f, t: Math.floor(au.currentTime || 0), playing: playing === undefined ? !au.paused : playing, at: Date.now() }); }
  function load() {
    return fetch(BASE + "_index.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (x) { R = x && x.items && x.items.length ? x : null; if (R) build(); return R; }, function () { return null; });
  }
  function cur() { return R && steps[s] ? R.items[steps[s].i] : {}; }
  function bar() {
    var b = document.getElementById("rdBar");
    if (!b) { b = document.createElement("div"); b.id = "rdBar"; b.className = "rd-bar"; document.body.appendChild(b); }
    if (!R) { b.hidden = true; document.body.classList.remove("rd-on"); return; }
    var it = cur(), playing = !au.paused, n = R.items.length, part = steps[s] && /b\.mp3$/.test(steps[s].f) ? " · 내용" : "";
    b.hidden = false; document.body.classList.add("rd-on");
    b.innerHTML = '<div class="rd-info"><span class="rd-k">' + esc(KIND[it.kind] || "") + " · " + ((steps[s] ? steps[s].i : 0) + 1) + "/" + n + part + " · " + esc(R.label || "") + '</span><b class="rd-t">' + esc(it.title || "") + "</b></div>" +
      '<div class="rd-btns"><button type="button" data-rd="prev" aria-label="이전 소식">⏮</button><button type="button" data-rd="toggle" class="rd-play" aria-label="' + (playing ? "멈춤" : "재생") + '">' + (playing ? "⏸" : "▶") + '</button><button type="button" data-rd="next" aria-label="다음 소식">⏭</button>' +
      '<button type="button" data-rd="mode" class="rd-mode" aria-label="듣는 방식">' + (mode === "title" ? "제목만" : "자세히") + "</button>" +
      '<button type="button" data-rd="speed" class="rd-speed" aria-label="재생 속도">' + speed + "×</button>" +
      (it.link ? '<button type="button" data-rd="card" aria-label="카드 보기">카드</button>' : "") + '<button type="button" data-rd="close" aria-label="라디오 닫기">✕</button></div>';
    var btn = document.getElementById("rdBtn"); if (btn) btn.textContent = playing ? "⏸ 라디오" : "▶ 라디오";
  }
  function media() {
    if (!("mediaSession" in navigator) || !R) return;
    var it = cur();
    try {
      navigator.mediaSession.metadata = new MediaMetadata({ title: it.title || "자판기 라디오", artist: "자판기 라디오 · " + (KIND[it.kind] || ""), album: R.label || "",
        artwork: [{ src: ROOT + "assets/icon-192.png", sizes: "192x192", type: "image/png" }, { src: ROOT + "assets/icon-512.png", sizes: "512x512", type: "image/png" }] });
    } catch (e) { }
  }
  function playStep(k, from, quiet) {
    if (!R || !steps.length) return;
    s = Math.max(0, Math.min(steps.length - 1, k));
    au.src = BASE + steps[s].f; applySpeed();
    if (from) au.addEventListener("loadedmetadata", function f() { au.currentTime = from; au.removeEventListener("loadedmetadata", f); });
    var p = au.play();
    if (p && p.catch) p.catch(function () { save(true); bar(); toast(quiet ? "라디오: ▶를 누르면 이어서 들어요" : "재생을 시작하지 못했어요. ▶를 눌러 주세요"); });
    media(); bar(); save(true);
  }
  // 소식 단위로 앞뒤 (자세히 모드에서도 다음 '소식'의 처음부터)
  function firstOf(k) { while (k > 0 && steps[k - 1].i === steps[k].i) k--; return k; }
  function jump(dir) {
    if (!R || !steps.length) return;
    var ci = steps[s].i, k;
    if (dir > 0) { k = s; while (k < steps.length && steps[k].i === ci) k++; if (k >= steps.length) return toast("마지막 소식이에요"); }
    else { k = firstOf(s); if (!(k === s && au.currentTime > 4)) k = k > 0 ? firstOf(k - 1) : 0; }
    playStep(k);
  }
  au.addEventListener("ended", function () { if (R && s < steps.length - 1) playStep(s + 1); else { s = 0; save(false); bar(); toast("오늘 라디오를 다 들었어요"); } });
  au.addEventListener("play", bar); au.addEventListener("pause", bar);
  setInterval(function () { if (!au.paused) save(true); }, 4000);
  window.addEventListener("pagehide", function () { if (R) save(!au.paused); });
  if ("mediaSession" in navigator) {
    var h = { play: function () { au.play(); }, pause: function () { au.pause(); save(false); }, nexttrack: function () { jump(1); }, previoustrack: function () { jump(-1); } };
    Object.keys(h).forEach(function (k) { try { navigator.mediaSession.setActionHandler(k, h[k]); } catch (e) { } });
  }
  function resumeIndex(x) { return st.slot === x.slot ? steps.map(function (y) { return y.f; }).indexOf(st.f) : -1; }
  function start() {
    if (R && au.src) { if (au.paused) au.play(); else { au.pause(); save(false); } return; }
    load().then(function (x) {
      if (!x) return toast("라디오가 아직 없어요. 아침 8시·저녁 8시쯤 로봇이 만들어요");
      var k = resumeIndex(x);
      playStep(k >= 0 ? k : 0, k >= 0 ? st.t : 0);
      toast(k >= 0 ? "듣던 곳부터 이어서 틀어요" : x.label + " · " + (mode === "title" ? "제목만 약 " + Math.max(1, Math.round((x.secT || x.sec || 0) / 60)) : "자세히 약 " + Math.max(1, Math.round((x.sec || 0) / 60))) + "분");
    });
  }
  // 다른 화면으로 옮겨 왔을 때: 듣던 중이었으면(3분 안) 바로 이어서
  if (st.playing && st.at && Date.now() - st.at < 3 * 60e3) {
    load().then(function (x) { if (!x || st.slot !== x.slot) return; var k = resumeIndex(x); playStep(k >= 0 ? k : 0, k >= 0 ? st.t : 0, true); });
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("#rdBtn,[data-rd]"); if (!b) return;
    if (b.id === "rdBtn") return start();
    var a = b.getAttribute("data-rd");
    if (a === "speed") { speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]; LS.s("vfm:radio:speed", speed); applySpeed(); bar(); toast(speed + "배속"); return; }
    if (a === "mode") {
      mode = mode === "title" ? "full" : "title"; LS.s("vfm:radio:mode", mode);
      var ci = steps[s] ? steps[s].i : 0, wasPlaying = !au.paused; build();
      var k = 0; for (var q = 0; q < steps.length; q++) if (steps[q].i === ci) { k = q; break; }
      if (wasPlaying) playStep(k); else { s = k; bar(); save(false); }
      toast(mode === "title" ? "제목만 들어요" : "제목과 내용을 자세히 들어요"); return;
    }
    if (a === "toggle") { if (au.paused) { if (!au.src && steps.length) playStep(s, st.t); else au.play(); } else { au.pause(); save(false); } }
    else if (a === "next") jump(1);
    else if (a === "prev") jump(-1);
    else if (a === "close") { au.pause(); save(false); document.getElementById("rdBar").hidden = true; document.body.classList.remove("rd-on"); }
    else if (a === "card") {
      var it = cur(); if (!it.link) return;
      save(!au.paused);                                                       // 카드를 열어도 다음 화면에서 이어서
      try { sessionStorage.setItem("vfm:fromHome", "1"); sessionStorage.setItem("vfm:fromCard", "#" + (it.link.split("#")[1] || "")); } catch (x) { }
      location.href = ROOT + it.link;
    }
  });
  // 홈 위쪽(찾기 줄)에 단추
  function addBtn() {
    if (!HOME) return;
    var top = document.querySelector(".mx-top"); if (!top) return setTimeout(addBtn, 300);
    if (document.getElementById("rdBtn")) return;
    var b = document.createElement("button"); b.type = "button"; b.id = "rdBtn"; b.textContent = "▶ 라디오"; b.setAttribute("aria-label", "라디오로 듣기");
    top.insertBefore(b, top.firstChild);
  }
  addBtn();
  var css = document.createElement("style");
  css.textContent = "#rdBtn{flex:none;border:0;border-radius:12px;padding:0 12px;font:inherit;font-weight:700;background:var(--ap-blue,#0A84FF);color:#fff;white-space:nowrap}" +
    ".rd-bar{position:fixed;left:8px;right:8px;bottom:calc(env(safe-area-inset-bottom,0px) + 8px);z-index:9500;display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:10px;border-radius:16px;" +
    "background:var(--ap-bar,rgba(249,249,249,.92));color:var(--ap-label,#000);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);box-shadow:0 6px 24px rgba(0,0,0,.18);max-width:560px;margin:0 auto}" +
    ".rd-info{flex:1 1 100%;min-width:0;display:flex;flex-direction:column;padding:0 4px}.rd-k{font-size:11.5px;color:var(--ap-label2,#666)}.rd-t{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}" +
    ".rd-btns{display:flex;gap:4px;width:100%}.rd-btns button{flex:1;border:0;border-radius:10px;min-width:0;height:38px;background:var(--ap-fill,rgba(118,118,128,.12));color:var(--ap-label,#000);font:inherit;font-size:15px;padding:0}" +
    ".rd-btns .rd-speed,.rd-btns .rd-mode{font-size:12.5px;font-weight:700}.rd-btns .rd-play{background:var(--ap-blue,#0A84FF);color:#fff}" +
    "body.rd-on{padding-bottom:calc(env(safe-area-inset-bottom,0px) + 130px)!important}body.rd-on nav.tabs,body.rd-on .tabbar{bottom:118px!important}";
  document.head.appendChild(css);
})();
