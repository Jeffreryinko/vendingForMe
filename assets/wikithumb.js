/* wikithumb.js — 위키백과 대표 사진을 카드에 붙이기 (토큰 0, 서버 0)
 *  <img data-wt="ko:문서 제목"> 처럼 써 두면, 위키백과에 50개씩 묶어 물어 작은 사진(썸네일)을 채움
 *  · 사진이 없거나 못 받으면 그 img 를 지움 (원래 그림·자리 그대로)
 *  · 한 번 알아낸 결과는 이 폰에 기억 (vfm:wt, 최대 4,000개) → 다시 물어보지 않음
 *  · 빨라지게 (2026-11-12)
 *      1) 화면에 그려지자마자 그 화면의 사진 주소를 한꺼번에 물어 둠 (예전: 사진이 화면 가까이 와야 그제야 물음 → 스크롤할 때마다 0.5초씩 빈칸)
 *         실제 사진 파일은 브라우저가 화면 가까이 올 때 받음(loading=lazy) — 데이터는 그대로
 *      2) 숨겨 둔 사진(display:none)도 빠짐없이 물음 (예전: 배움 역사 목록의 작은 사진이 아예 안 떴음)
 *      3) 칸 크기에 맞는 크기로 받음: 46px 칸이면 250px, 큰 칸이면 500px (예전엔 모두 500px → 작은 칸에서 4배 무거웠음)
 *         위키미디어가 미리 만들어 두는 크기(120·250·330·500)만 씀. 작은 크기가 안 되면 500px 로 다시
 *  · 위키백과 사진은 대부분 위키미디어 공용의 자유 이용 사진
 */
(function () {
  "use strict";
  if (window.WT) return;                              // 두 번 실려도 한 번만
  var KEY = "vfm:wt", MEM = {};
  try { MEM = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { MEM = {}; }
  var saveT = null;
  function save() {
    clearTimeout(saveT); saveT = setTimeout(function () {
      var ks = Object.keys(MEM); if (ks.length > 4000) ks.slice(0, ks.length - 3000).forEach(function (k) { delete MEM[k]; });
      try { localStorage.setItem(KEY, JSON.stringify(MEM)); } catch (e) { }
    }, 500);
  }
  var SIZES = [120, 250, 330, 500], DPR = Math.min(window.devicePixelRatio || 1, 3);
  var THUMB = /(\/thumb\/.+\/)(\d+)px-/;
  function full(v) { return v.replace(THUMB, function (m, a, n) { return a + (+n > 500 ? 500 : n) + "px-"; }); }   // 예전에 기억한 640·960px 은 500px 로
  function fit(img, v) {                               // 칸 너비에 맞는 크기
    if (!THUMB.test(v)) return v;                      // 원본이 작아 썸네일 주소가 아닌 경우 그대로
    var w = 0;
    try { if (img.getClientRects().length) w = img.getBoundingClientRect().width; else { var cw = getComputedStyle(img).width; if (/px$/.test(cw)) w = parseFloat(cw); } } catch (e) { }   // 숨겨진 사진은 CSS 에 적힌 px 너비만 믿음
    if (!w || w > 260) return v;                       // 모르거나 크면 500px
    var need = w * DPR, s = SIZES.filter(function (x) { return x >= need; })[0] || 500;
    return v.replace(THUMB, function (m, a) { return a + s + "px-"; });
  }
  var queue = {}, timer = null;                       // queue[lang] = Set(제목)
  function apply(img) {
    var k = img.getAttribute("data-wt"), v = MEM[k];
    if (v === undefined) return false;
    if (v) {
      v = full(v);
      if (!img.hasAttribute("loading")) img.loading = "lazy";
      img.decoding = "async"; img.setAttribute("data-wt-full", v);
      img.src = fit(img, v); img.removeAttribute("data-wt"); img.classList.add("wt-on");
    }
    else { var p = img.parentElement; img.remove(); if (p) p.classList.add("wt-none"); }
    return true;
  }
  function flush() {
    timer = null;
    Object.keys(queue).forEach(function (lang) {
      var titles = Array.from(queue[lang]); delete queue[lang];
      for (var i = 0; i < titles.length; i += 50) ask(lang, titles.slice(i, i + 50));
    });
  }
  var ASKED = {}, RETRY = 0;
  function ask(lang, titles) {
    titles.forEach(function (t) { ASKED[lang + ":" + t] = 1; });
    var u = "https://" + lang + ".wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail&pithumbsize=500&redirects=1&format=json&formatversion=2&origin=*&titles=" + encodeURIComponent(titles.join("|"));
    fetch(u).then(function (r) { if (!r.ok) throw r.status; return r.json(); }).then(function (j) {
      if (!j || !j.query) throw 0;                     // 막힘·오류 답을 "사진 없음"으로 기억하지 않게
      var q = j.query, map = {};
      (q.normalized || []).forEach(function (n) { map[n.to] = (map[n.to] || []).concat([n.from]); });
      (q.redirects || []).forEach(function (n) { map[n.to] = (map[n.to] || []).concat([n.from], map[n.from] || []); });
      var got = {};
      (q.pages || []).forEach(function (p) {
        var src = p.thumbnail && p.thumbnail.source || "";
        [p.title].concat(map[p.title] || []).forEach(function (t) { got[t] = src; });
      });
      titles.forEach(function (t) { var k = lang + ":" + t; MEM[k] = got[t] || ""; if (WARM[k] && MEM[k]) preload(MEM[k]); });
      save(); paint();
    }).catch(function () {                         // 실패(위키백과가 잠깐 막음 등) → 몇 초 뒤 다시 (최대 3번)
      titles.forEach(function (t) { delete ASKED[lang + ":" + t]; });
      if (RETRY < 3) { RETRY++; setTimeout(paint, 3000 * RETRY); }
    });
  }
  var WARM = {};
  function preload(u) { var p = new Image(); p.decoding = "async"; p.src = full(u); }
  function queueKey(k) {
    if (!k || ASKED[k] || MEM[k] !== undefined) return;
    var i = k.indexOf(":"); if (i < 1) return;
    ASKED[k] = 1;
    (queue[k.slice(0, i)] = queue[k.slice(0, i)] || new Set()).add(k.slice(i + 1));
    if (!timer) timer = setTimeout(flush, 30);
  }
  function warm(k) {                                   // 아직 화면에 없는 카드의 위키 사진을 미리 (다음 카드용)
    if (!k || WARM[k]) return; WARM[k] = 1;
    var v = MEM[k]; if (v) return preload(v); if (v === "") return;
    queueKey(k);
  }
  function paint() {
    var n = 0;
    document.querySelectorAll("img[data-wt]").forEach(function (img) {
      if (apply(img)) return;
      if (n++ < 300) queueKey(img.getAttribute("data-wt"));   // 한 번에 300개까지 미리 물음 (나머지는 다음 그리기 때)
    });
  }
  new MutationObserver(function () { clearTimeout(paint._t); paint._t = setTimeout(paint, 30); }).observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("error", function (e) {
    var t = e.target; if (!t || !t.classList || !t.classList.contains("wt-on")) return;
    var f = t.getAttribute("data-wt-full");
    if (f && t.src !== f) { t.src = f; return; }       // 작은 크기가 안 되면 500px 로 다시
    var p = t.parentElement; t.remove(); if (p) p.classList.add("wt-none");
  }, true);
  window.WT = { paint: paint, warm: warm, wikiOf: function (url) {             // 위키백과 주소 → "ko:제목"
    var m = /^https?:\/\/([a-z\-]+)\.(?:m\.)?wikipedia\.org\/wiki\/([^#?]+)/.exec(url || ""); if (!m) return "";
    try { return m[1] + ":" + decodeURIComponent(m[2]).replace(/_/g, " "); } catch (e) { return ""; }
  } };
  if (document.readyState !== "loading") paint(); else document.addEventListener("DOMContentLoaded", paint);
})();
