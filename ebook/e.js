/* 종이 자판기 보기 설정 — 스크롤 또는 넘김. 이 기기에만 기억해요 */
(function () {
  var K = "ebook:mode", d = document, R = d.documentElement, m = d.getElementById("m"), pi = d.getElementById("pi");
  function get() { try { return localStorage.getItem(K) || "page"; } catch (e) { return "page"; } }
  function set(v) { try { localStorage.setItem(K, v); } catch (e) {} }
  var mode = get(), n = 0, N = 1, W = 0, G = 40;
  var sw = d.querySelector(".md"); if (sw) sw.hidden = false;
  function marks() { var a = d.querySelectorAll(".md a"); for (var i = 0; i < a.length; i++) a[i].className = a[i].getAttribute("data-m") === mode ? "on" : ""; }
  function link(r) { var a = d.querySelector("nav.pt a[data-r=" + r + "]"); return a ? a.href : ""; }
  function show() { m.scrollLeft = n * (W + G); pi.textContent = (n + 1) + " / " + N + "  ·  화면 왼쪽·오른쪽을 눌러 넘겨요"; }
  function layout(keep) {
    if (mode !== "page") return;
    m.style.columnWidth = m.style.webkitColumnWidth = "auto"; m.scrollLeft = 0;
    W = m.clientWidth; m.style.columnGap = m.style.webkitColumnGap = G + "px";
    m.style.columnWidth = m.style.webkitColumnWidth = W + "px";
    N = Math.max(1, Math.round(m.scrollWidth / (W + G)));
    var end = !keep && location.hash === "#end";
    if (end) n = N - 1; if (n > N - 1) n = N - 1; show();
  }
  function go(dir) {
    if (dir > 0 && n < N - 1) { n++; show(); return; }
    if (dir < 0 && n > 0) { n--; show(); return; }
    var u = link(dir > 0 ? "next" : "prev"); if (u) location.href = u + (dir < 0 ? "#end" : "");
  }
  function apply() {
    marks();
    if (mode === "page") { R.className += " pm"; pi.hidden = false; n = 0; layout(); }
    else { R.className = R.className.replace(/ ?pm/g, ""); pi.hidden = true; m.style.height = ""; m.style.columnWidth = m.style.webkitColumnWidth = ""; m.scrollLeft = 0; }
  }
  d.addEventListener("click", function (e) {
    var t = e.target;
    while (t && t !== d) { if (t.getAttribute && t.getAttribute("data-m")) { e.preventDefault(); mode = t.getAttribute("data-m"); set(mode); apply(); return; } t = t.parentNode; }
    if (mode !== "page") return;
    t = e.target;
    while (t && t !== m) { if (/^(A|SUMMARY|DETAILS|BUTTON)$/.test(t.tagName)) return; t = t.parentNode; }
    if (!t) return;
    var x = e.clientX / window.innerWidth; if (x < 0.35) go(-1); else go(1);
  });
  d.addEventListener("keydown", function (e) {
    if (mode !== "page") return; var k = e.key || e.keyCode;
    if (k === "ArrowRight" || k === "ArrowDown" || k === "PageDown" || k === "AudioVolumeDown" || k === " " || k === 39 || k === 34 || k === 32) { e.preventDefault(); go(1); }
    else if (k === "ArrowLeft" || k === "ArrowUp" || k === "PageUp" || k === "AudioVolumeUp" || k === 37 || k === 33) { e.preventDefault(); go(-1); }
  });
  d.addEventListener("toggle", function () { layout(true); }, true);
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { layout(true); }, 200); });
  apply();
})();
