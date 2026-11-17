/* 종이 넘김 — 아무 웹 글이나 이북리더기용 넘김 화면으로 바꾸는 책갈피(북마클릿) 원본.
   robot/ebook_build.js 가 줄여서 ebook/web.html 에 'javascript:' 주소로 넣어요.
   본문만 골라(광고·메뉴 빼기) 흰 바탕·검은 글자로 다시 깔고, 한 화면씩 넘겨요.
   누르기(왼쪽 35% 앞 / 나머지 뒤)·밀기·음량/쪽 넘김 키, 글자 크기, 전체화면, 원래대로. */
(function () {
  var d = document, W = window;
  if (W.__jpaper) { location.reload(); return; }
  W.__jpaper = 1;
  var BAD = /(^|[\s_-])(ad|ads|advert|banner|promo|sponsor|share|social|related|recommend|comment|footer|header|nav|menu|sidebar|subscribe|newsletter|popup|modal|cookie|breadcrumb|tag|rank|byline-share)([\s_-]|$)/i;
  var KEEP = { H1: 1, H2: 1, H3: 1, H4: 1, P: 1, BLOCKQUOTE: 1, UL: 1, OL: 1, LI: 1, PRE: 1, TABLE: 1, THEAD: 1, TBODY: 1, TR: 1, TD: 1, TH: 1, FIGURE: 1, FIGCAPTION: 1, IMG: 1, A: 1, B: 1, STRONG: 1, EM: 1, I: 1, BR: 1, SUP: 1, SUB: 1, CODE: 1, DL: 1, DT: 1, DD: 1, HR: 1 };
  function txt(e) { return (e.textContent || "").replace(/\s+/g, " ").trim(); }
  function score(e) { var s = 0, ps = e.querySelectorAll("p"); for (var i = 0; i < ps.length; i++) { var l = txt(ps[i]).length; if (l > 40) s += l; } return s; }
  /* 본문 고르기: <article> 중 글이 가장 많은 것 → 없으면 문단 글자 수가 가장 많은 상자 */
  var best = null, bs = 0, c = d.querySelectorAll("article, main, [role=main], [itemprop=articleBody], .article, .post, .entry-content, #content, #articleBody, #article-view-content-div, #dic_area, #newsct_article, .article_body, .news_end, div, section");
  for (var i = 0; i < c.length; i++) { var s = score(c[i]); if (/^(ARTICLE|MAIN)$/.test(c[i].tagName) || c[i].getAttribute("itemprop") === "articleBody") s *= 1.25; if (s > bs) { bs = s; best = c[i]; } }
  /* 너무 바깥 상자(사이트 전체)를 고르지 않게: 글의 80% 넘게 가진 자식이 있으면 내려가기 */
  while (best) { var kids = best.children, down = null; for (var k = 0; k < kids.length; k++) if (score(kids[k]) > bs * 0.8) down = kids[k]; if (!down) break; best = down; bs = score(down); }
  var title = (d.querySelector("h1") && txt(d.querySelector("h1"))) || d.title;
  function clean(n) {
    if (n.nodeType === 3) return d.createTextNode(n.nodeValue);
    if (n.nodeType !== 1) return null;
    var t = n.tagName, cls = (n.className && n.className.baseVal == null ? n.className : "") + " " + (n.id || "");
    if (/^(SCRIPT|STYLE|NOSCRIPT|IFRAME|FORM|BUTTON|INPUT|SELECT|TEXTAREA|SVG|CANVAS|VIDEO|AUDIO|NAV|ASIDE|FOOTER|HEADER|OBJECT|EMBED)$/.test(t)) return null;
    if (BAD.test(cls) && txt(n).length < 600) return null;
    try { var cs = W.getComputedStyle(n); if (cs && (cs.display === "none" || cs.visibility === "hidden")) return null; } catch (e) {}
    var out;
    if (t === "IMG") {
      var src = n.currentSrc || n.src || n.getAttribute("data-src") || n.getAttribute("data-original") || n.getAttribute("data-lazy-src");
      if (!src || (n.naturalWidth && n.naturalWidth < 80)) return null;
      out = d.createElement("img"); out.src = src; out.alt = n.alt || ""; return out;
    }
    out = d.createElement(KEEP[t] ? t.toLowerCase() : (/^(DIV|SECTION|ARTICLE|MAIN|SPAN|FONT|LABEL|TIME|SMALL|MARK|U|S)$/.test(t) ? (t === "SPAN" || t === "FONT" || t === "SMALL" || t === "MARK" || t === "U" || t === "TIME" || t === "LABEL" || t === "S" ? "span" : "div") : "span"));
    if (t === "A" && n.href) out.href = n.href;
    if ((t === "TD" || t === "TH") && n.colSpan > 1) out.colSpan = n.colSpan;
    for (var ch = n.firstChild; ch; ch = ch.nextSibling) { var x = clean(ch); if (x) out.appendChild(x); }
    if (out.tagName === "DIV" && !txt(out) && !out.querySelector("img")) return null;
    return out;
  }
  var body = best && bs > 300 ? clean(best) : null;
  var host = location.hostname.replace(/^www\./, ""), href = location.href;
  /* 화면 다시 깔기 */
  var css = "html,body{margin:0;background:#fff!important;color:#000!important}" +
    "*{animation:none!important;transition:none!important}" +
    "#jp{position:fixed;inset:0;display:flex;flex-direction:column;font-family:'Noto Serif KR','Noto Serif CJK KR','Nanum Myeongjo',serif;word-break:keep-all;overflow-wrap:break-word;line-break:strict}" +
    "#jp-bar{display:flex;gap:6px;align-items:center;padding:6px 12px;border-bottom:2px solid #000;font:700 14px/1.2 sans-serif}" +
    "#jp-bar span{flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-weight:400}" +
    "#jp-bar b{border:2px solid #000;padding:6px 10px;cursor:pointer;user-select:none;white-space:nowrap}" +
    "#jp-bar b.on{background:#000;color:#fff}" +
    "#jp-m{flex:1;min-height:0;overflow:hidden;padding:0 18px;column-fill:auto;line-height:1.75}" +
    "#jp-m h1{font-size:1.4em;line-height:1.35;margin:.6em 0 .3em}#jp-m h2,#jp-m h3,#jp-m h4{font-size:1.1em;margin:1.2em 0 .3em;break-after:avoid}" +
    "#jp-m p{margin:.5em 0}#jp-m a{color:#000}#jp-m img{max-width:100%;max-height:60vh;height:auto;display:block;margin:.6em auto;filter:grayscale(1);break-inside:avoid}" +
    "#jp-m blockquote{margin:1em 0;padding-left:1em;border-left:5px solid #000}#jp-m table{border-collapse:collapse;font-size:.85em}#jp-m td,#jp-m th{border:1px solid #000;padding:.2em .4em}" +
    "#jp-m pre{white-space:pre-wrap;font-size:.85em}#jp-m figcaption,#jp-m .src{font-size:.8em}" +
    "#jp-pi{text-align:center;font:13px/1.2 sans-serif;padding:6px 0;border-top:2px solid #000}";
  var fs = 20;
  try { fs = +localStorage.getItem("jpaper:fs") || 20; } catch (e) {}
  var wrap = d.createElement("div"); wrap.id = "jp";
  wrap.innerHTML = '<div id="jp-bar"><b data-a="x">✕</b><span></span><b data-a="-">가−</b><b data-a="+">가+</b><b data-a="f">전체화면</b></div><div id="jp-m"></div><div id="jp-pi"></div>';
  wrap.querySelector("#jp-bar span").textContent = host;
  var m = wrap.querySelector("#jp-m"), pi = wrap.querySelector("#jp-pi");
  var h = d.createElement("h1"); h.textContent = title; m.appendChild(h);
  if (body) m.appendChild(body);
  else { var p = d.createElement("p"); p.textContent = "이 쪽에서는 본문을 찾지 못했어요. ✕를 눌러 원래 화면으로 돌아가세요."; m.appendChild(p); }
  var src = d.createElement("p"); src.className = "src"; src.textContent = "원문: " + href; m.appendChild(src);
  /* 원래 문서 비우고 새로 깔기 (스타일시트도 끔) */
  var ss = d.querySelectorAll("link[rel=stylesheet],style"); for (i = 0; i < ss.length; i++) ss[i].disabled = true, ss[i].parentNode && ss[i].parentNode.removeChild(ss[i]);
  d.body.innerHTML = ""; d.body.removeAttribute("class"); d.body.removeAttribute("style");
  var st = d.createElement("style"); st.textContent = css; (d.head || d.documentElement).appendChild(st);
  d.body.appendChild(wrap);
  var n = 0, N = 1, Wd = 0, G = 36;
  function lay(keep) {
    m.style.fontSize = fs + "px";
    m.style.columnWidth = "auto"; m.scrollLeft = 0;
    Wd = m.clientWidth - 36; m.style.columnGap = G + "px"; m.style.columnWidth = Wd + "px";
    N = Math.max(1, Math.round((m.scrollWidth - 36 + G) / (Wd + G)));
    if (!keep) n = 0; if (n > N - 1) n = N - 1; show();
  }
  function show() { m.scrollLeft = n * (Wd + G); pi.textContent = (n + 1) + " / " + N + "  ·  누르거나 밀어서 넘겨요"; }
  function go(k) { n = Math.max(0, Math.min(N - 1, n + k)); show(); }
  var R = d.documentElement, fsOn = function () { return !!(d.fullscreenElement || d.webkitFullscreenElement); };
  function fsT() { try { if (fsOn()) (d.exitFullscreen || d.webkitExitFullscreen).call(d); else { var r = (R.requestFullscreen || R.webkitRequestFullscreen).call(R); if (r && r.catch) r.catch(function () {}); } } catch (e) {} }
  var sx = 0, sy = 0, t0 = 0, sw = 0;
  wrap.addEventListener("touchstart", function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; t0 = Date.now(); }, { passive: true });
  wrap.addEventListener("touchend", function (e) { var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy, ax = Math.abs(dx), ay = Math.abs(dy);
    if (Date.now() - t0 > 800 || Math.max(ax, ay) < 40) return; sw = Date.now(); if (ax > ay) go(dx < 0 ? 1 : -1); else go(dy < 0 ? 1 : -1); }, { passive: true });
  wrap.addEventListener("click", function (e) {
    if (Date.now() - sw < 600) { e.preventDefault(); return; }
    var a = e.target.getAttribute && e.target.getAttribute("data-a");
    if (a === "x") { location.reload(); return; }
    if (a === "+" || a === "-") { fs = Math.max(14, Math.min(34, fs + (a === "+" ? 2 : -2))); try { localStorage.setItem("jpaper:fs", fs); } catch (x) {} lay(); return; }
    if (a === "f") { fsT(); return; }
    for (var t = e.target; t && t !== m; t = t.parentNode) if (t.tagName === "A") return;
    if (!t) return;
    go(e.clientX / W.innerWidth < 0.35 ? -1 : 1);
  });
  d.addEventListener("keydown", function (e) { var k = e.key;
    if (/^(ArrowRight|ArrowDown|PageDown| |AudioVolumeDown)$/.test(k)) { e.preventDefault(); e.stopPropagation(); go(1); }
    else if (/^(ArrowLeft|ArrowUp|PageUp|AudioVolumeUp)$/.test(k)) { e.preventDefault(); e.stopPropagation(); go(-1); } }, true);
  var rt; W.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { lay(true); }, 200); });
  d.addEventListener("fullscreenchange", function () { setTimeout(function () { lay(true); }, 150); });
  var imgs = m.querySelectorAll("img"); for (i = 0; i < imgs.length; i++) imgs[i].addEventListener("load", function () { lay(true); });
  W.scrollTo(0, 0); lay();
})();
