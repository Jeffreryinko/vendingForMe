/* 종이 자판기 보기 설정 — 스크롤/넘김, 전체화면. 이 기기에만 기억해요.
   쪽을 옮길 때 새로 불러오지 않고 글만 바꿔 끼워서(같은 문서 유지) 전체화면이 쭉 이어져요.
   글을 못 받아 오면 예전처럼 그냥 그 쪽으로 이동해요. */
(function () {
  var K = "ebook:mode", KF = "ebook:fs", d = document, R = d.documentElement, m, pi;
  function get(k, v) { try { return localStorage.getItem(k) || v; } catch (e) { return v; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var mode = get(K, "page"), n = 0, N = 1, W = 0, G = 40, busy = 0;
  /* 이 사이트의 맨 위 주소 (e.js 가 있는 곳) — 이 안의 .html 쪽만 바꿔 끼워요 */
  var me = d.querySelector('script[src*="e.js"]'), ROOT = me ? new URL(".", me.src).href : "";
  var canSwap = !!(window.fetch && window.DOMParser && ROOT);
  /* 전체화면 */
  var fsOn = function () { return !!(d.fullscreenElement || d.webkitFullscreenElement); };
  var canFs = !!(R.requestFullscreen || R.webkitRequestFullscreen) && (d.fullscreenEnabled !== false || d.webkitFullscreenEnabled);
  var fsPref = get(KF, "0") === "1";
  function fsEnter() { if (!canFs || fsOn()) return; try { var r = (R.requestFullscreen || R.webkitRequestFullscreen).call(R); if (r && r.catch) r.catch(function () {}); } catch (e) {} }
  function fsExit() { if (!fsOn()) return; try { var r = (d.exitFullscreen || d.webkitExitFullscreen).call(d); if (r && r.catch) r.catch(function () {}); } catch (e) {} }
  function fsToggle() { fsPref = !fsPref; set(KF, fsPref ? "1" : "0"); head(); if (fsPref) fsEnter(); else fsExit(); }
  function fsAuto() { if (fsPref) fsEnter(); }   /* 처음 열었을 때: 첫 누르기에 켜요 */
  d.addEventListener("touchend", fsAuto, true); d.addEventListener("keydown", fsAuto, true);
  function relay() { setTimeout(function () { layout(true); }, 150); }
  d.addEventListener("fullscreenchange", relay); d.addEventListener("webkitfullscreenchange", relay);
  /* 맨 위 버튼 표시 */
  function head() {
    var sw = d.querySelector(".md"); if (sw) sw.hidden = false;
    var a = d.querySelectorAll(".md a[data-m]"); for (var i = 0; i < a.length; i++) a[i].className = a[i].getAttribute("data-m") === mode ? "on" : "";
    var f = d.querySelector(".md a.fs"); if (f && canFs) { f.hidden = false; f.textContent = fsPref ? "전체화면 끄기" : "전체화면"; f.className = "fs" + (fsPref ? " on" : ""); }
  }
  function link(r) { var a = d.querySelector("nav.pt a[data-r=" + r + "]"); return a ? a.href : ""; }
  function show() { m.scrollLeft = n * (W + G); pi.textContent = (n + 1) + " / " + N + "  ·  누르거나 밀어서 넘겨요"; }
  function layout(keep, hash) {
    if (mode !== "page" || !m) return;
    m.style.columnWidth = m.style.webkitColumnWidth = "auto"; m.scrollLeft = 0;
    W = m.clientWidth; m.style.columnGap = m.style.webkitColumnGap = G + "px";
    m.style.columnWidth = m.style.webkitColumnWidth = W + "px";
    N = Math.max(1, Math.round(m.scrollWidth / (W + G)));
    if (!keep) { n = 0; hash = hash == null ? location.hash : hash;
      if (hash === "#end") n = N - 1;
      else if (hash && hash.length > 1) { var el = d.getElementById(hash.slice(1)); if (el) n = Math.floor((el.offsetLeft - m.offsetLeft) / (W + G)); } }
    if (n > N - 1) n = N - 1; if (n < 0) n = 0; show();
  }
  function apply(hash) {
    m = d.getElementById("m"); pi = d.getElementById("pi"); head();
    if (!m || !pi) return;
    if (mode === "page") { if (!/(^| )pm( |$)/.test(R.className)) R.className += " pm"; pi.hidden = false; layout(false, hash); }
    else { R.className = R.className.replace(/ ?pm/g, ""); pi.hidden = true; m.style.columnWidth = m.style.webkitColumnWidth = ""; m.scrollLeft = 0;
      var el = hash && hash.length > 1 && hash !== "#end" ? d.getElementById(hash.slice(1)) : null; if (el && el.scrollIntoView) el.scrollIntoView(); else window.scrollTo(0, 0); }
  }
  /* 쪽 바꿔 끼우기 */
  function inside(u) { return !!(canSwap && u.indexOf(ROOT) === 0 && /\.html($|[#?])/.test(u)); }
  function swap(u, push) {
    if (busy) return; var hash = u.indexOf("#") >= 0 ? u.slice(u.indexOf("#")) : "", url = u.split("#")[0];
    busy = 1;
    fetch(url, { credentials: "same-origin" }).then(function (r) { if (!r.ok) throw 0; return r.text(); }).then(function (t) {
      var nd = new DOMParser().parseFromString(t, "text/html"); if (!nd.getElementById("m")) throw 0;
      var b = d.querySelector("base"); if (!b) { b = d.createElement("base"); d.head.insertBefore(b, d.head.firstChild); } b.href = url;  /* 새 쪽 기준으로 링크 풀기 */
      var sc = nd.body.querySelectorAll("script"); for (var i = 0; i < sc.length; i++) sc[i].parentNode.removeChild(sc[i]);
      d.body.innerHTML = nd.body.innerHTML; d.title = nd.title;
      if (push) { try { history.pushState({ u: u }, "", u); } catch (e) {} }
      busy = 0; apply(hash);
    }).catch(function () { busy = 0; location.href = u; });
  }
  function nav(u) { if (inside(u)) swap(u, true); else location.href = u; }
  window.addEventListener("popstate", function () { if (inside(location.href)) swap(location.href, false); });
  try { history.replaceState({ u: location.href }, "", location.href); } catch (e) {}
  function go(dir) {
    if (dir > 0 && n < N - 1) { n++; show(); return; }
    if (dir < 0 && n > 0) { n--; show(); return; }
    var u = link(dir > 0 ? "next" : "prev"); if (u) nav(u + (dir < 0 ? "#end" : ""));
  }
  /* 밀기(스와이프): 왼쪽·위로 밀면 다음, 오른쪽·아래로 밀면 앞 */
  var sx = 0, sy = 0, st = 0, swiped = 0;
  d.addEventListener("touchstart", function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
  d.addEventListener("touchend", function (e) {
    if (mode !== "page") return; var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy, ax = Math.abs(dx), ay = Math.abs(dy);
    if (Date.now() - st > 800 || Math.max(ax, ay) < 40) return;
    swiped = Date.now(); if (ax > ay) go(dx < 0 ? 1 : -1); else go(dy < 0 ? 1 : -1);
  }, { passive: true });
  d.addEventListener("click", function (e) {
    if (Date.now() - swiped < 600) { e.preventDefault(); return; }
    var t = e.target, isF = false, x;
    for (x = t; x && x !== d; x = x.parentNode) if (x.getAttribute && x.getAttribute("data-f")) isF = true;
    if (!isF) fsAuto();
    while (t && t !== d) {
      if (t.getAttribute && t.getAttribute("data-f")) { e.preventDefault(); fsToggle(); return; }
      if (t.getAttribute && t.getAttribute("data-m")) { e.preventDefault(); mode = t.getAttribute("data-m"); set(K, mode); apply(""); return; }
      if (t.tagName === "A" && t.href && !e.ctrlKey && !e.metaKey) { if (inside(t.href)) { e.preventDefault(); swap(t.href, true); } return; }
      t = t.parentNode;
    }
    if (mode !== "page" || !m) return;
    for (t = e.target; t && t !== m; t = t.parentNode) if (/^(A|SUMMARY|DETAILS|BUTTON)$/.test(t.tagName)) return;
    if (!t) return;
    if (e.clientX / window.innerWidth < 0.35) go(-1); else go(1);
  });
  d.addEventListener("keydown", function (e) {
    if (mode !== "page") return; var k = e.key || e.keyCode;
    if (k === "ArrowRight" || k === "ArrowDown" || k === "PageDown" || k === "AudioVolumeDown" || k === " " || k === 39 || k === 34 || k === 32) { e.preventDefault(); go(1); }
    else if (k === "ArrowLeft" || k === "ArrowUp" || k === "PageUp" || k === "AudioVolumeUp" || k === 37 || k === 33) { e.preventDefault(); go(-1); }
  });
  d.addEventListener("toggle", function () { layout(true); }, true);
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { layout(true); }, 200); });
  apply(location.hash);
})();
