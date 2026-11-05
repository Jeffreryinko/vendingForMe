/* trendcard.js — 트렌드 카드 한 장 그리기 (시사 트렌드 탭과 자판기 홈 랜덤이 같이 씀). 토큰 0.
 *   VfmTrend.card({cc, cname, src, srcName, it, rank, country, extra})  → 카드 안쪽 HTML
 *   VfmTrend.wikiFor(url) → 위키백과 첫 문단 (카드가 보일 때만 받음, 한국어판이 있으면 한국어)
 *   VfmTrend.items(countryData) → 한 나라 자료를 카드 목록 재료로 [{src, srcName, it, rank}]
 */
(function () {
  "use strict";
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var flag = function (cc) { return !cc || cc.length !== 2 ? "🌐" : String.fromCodePoint.apply(null, cc.toUpperCase().split("").map(function (c) { return 0x1F1E6 + c.charCodeAt(0) - 65; })); };
  var ku = function (u, l) { return window.VfmDeck ? VfmDeck.koUrl(u, l) : u; };
  var ADULT = /(porn|sex|xxx|nude|hentai|onlyfans|야동|섹스|포르노|성인|エロ|성관계|rape|강간|gore|nsfl)/i;
  var LANG = { ko: "한국어", en: "영어", ja: "일본어", zh: "중국어", de: "독일어", fr: "프랑스어", pt: "포르투갈어", id: "인도네시아어", ru: "러시아어", vi: "베트남어", es: "스페인어", ar: "아랍어" };
  var LANG_WHO = { en: "미국·영국·인도·캐나다 등", es: "스페인·멕시코·아르헨티나 등", pt: "브라질·포르투갈 등", ar: "이집트·사우디 등 아랍권", zh: "중국·대만 등", fr: "프랑스·캐나다 퀘벡 등", de: "독일·오스트리아 등" };
  var ORDER = ["google", "reddit", "yt", "ytfun", "signal", "yahoojp", "baidu", "weibo", "x", "wiki"];
  var WK = {};
  function wikiFor(u) {
    if (WK[u] !== undefined) return Promise.resolve(WK[u]);
    WK[u] = null;
    var m = String(u).match(/^https:\/\/([a-z-]+)\.wikipedia\.org\/wiki\/(.+)$/); if (!m) return Promise.resolve(null);
    var lang = m[1], title = decodeURIComponent(m[2].replace(/\+/g, " "));
    var q = function (l, t, extra) { return fetch("https://" + l + ".wikipedia.org/w/api.php?action=query&format=json&origin=*&redirects=1&prop=extracts" + (extra || "") + "&exintro=1&explaintext=1&exsentences=4&titles=" + encodeURIComponent(t)).then(function (r) { return r.json(); }).then(function (j) { var p = (j.query || {}).pages || {}; return p[Object.keys(p)[0]] || {}; }); };
    return q(lang, title, lang === "ko" ? "" : "|langlinks&lllang=ko").then(function (pg) {
      var out = { lang: lang, title: pg.title || title, text: pg.extract || "" }, ko = (pg.langlinks || [])[0];
      if (ko && ko["*"]) return q("ko", ko["*"]).then(function (k) { if (k.extract) out = { lang: "ko", title: k.title, text: k.extract }; return out; });
      return out;
    }).then(function (o) { WK[u] = o.text ? o : null; return WK[u]; }, function () { WK[u] = null; return null; });
  }
  function items(d) {
    var out = [];
    Object.keys((d && d.src) || {}).sort(function (a, b) { return ORDER.indexOf(a) - ORDER.indexOf(b); }).forEach(function (src) {
      var b = d.src[src]; (b.items || []).slice(0, 20).forEach(function (it, i) { if (!ADULT.test(it.kw + " " + (it.ko || ""))) out.push({ src: src, srcName: b.name, it: it, rank: i }); });
    });
    return out;
  }
  // 유튜브 썸네일: 영상 번호(vid)만 있으면 주소가 정해져 있음 (API·토큰 0)
  function ytId(it) { return it.vid || (String(it.url || "").match(/(?:v=|youtu\.be\/|shorts\/)([\w-]{11})/) || [])[1] || ""; }
  function thumb(it) { var v = ytId(it); return v ? '<a class="vdk-yt" href="' + esc(it.url) + '" target="_blank" rel="noopener" aria-label="유튜브에서 보기"><img src="https://i.ytimg.com/vi/' + v + '/hqdefault.jpg" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.closest(\'a\').remove()"><span>▶</span></a>' : ""; }
  function video(it) {
    var desc = it.dko || it.desc, cap = it.capko || it.cap;
    return thumb(it) + '<p class="vdk-h">영상 정보</p><p class="vdk-p">' + esc(it.sub || "") + " 채널" + (it.n ? " · 조회 " + esc(it.n) : "") + "</p>" +
      (desc ? '<p class="vdk-h">설명란' + (it.dko ? " (기계번역)" : "") + '</p><p class="vdk-p">' + esc(desc) + "</p>" : '<p class="vdk-note">설명란이 비어 있거나 아직 못 가져왔어요.</p>') +
      (cap ? '<p class="vdk-h">자막 앞부분' + (it.capko ? " (기계번역)" : "") + '</p><p class="vdk-p">' + esc(cap.slice(0, 700)) + (cap.length > 700 ? "…" : "") + "</p>" : "") +
      '<a class="vdk-more" href="' + esc(it.url) + '" target="_blank" rel="noopener">유튜브에서 영상 보기 ↗</a>';
  }
  function card(o) {
    var it = o.it, src = o.src, cc = o.cc;
    var isNew = it.since && (Date.now() - Date.parse(it.since)) < 6 * 3600e3;
    var h = '<div class="vdk-k"><span>' + flag(cc) + " " + esc(o.cname || cc) + "</span><span>" + esc(o.srcName || src) + (o.rank != null ? " " + (o.rank + 1) + "위" : "") + "</span>" +
      (it.n && src !== "wiki" ? "<span>" + esc(it.n) + "</span>" : "") + (it.tag === "NEW" || isNew ? '<b class="new">NEW</b>' : it.tag ? "<span>" + esc(it.tag) + "</span>" : "") + "</div>" +
      '<h2 class="vdk-t">' + esc(it.ko || it.kw) + "</h2>" + (it.ko && it.ko !== it.kw ? '<p class="vdk-note" style="margin:-6px 0 10px">' + esc(it.kw) + "</p>" : "");
    var b = "";
    if (src === "google") {
      var ns = it.news || [];
      b = '<p class="vdk-h">왜 떴나 · 구글이 함께 보여 준 뉴스</p>' + (ns.length ? '<div class="vdk-links">' + ns.map(function (n) {
        return '<a href="' + esc(ku(n.u, cc === "KR" ? "ko" : undefined)) + '" target="_blank" rel="noopener">' + esc(n.ko || n.t) + (n.sn ? "<small>" + esc(n.sn) + "</small>" : "") + "<small>" + esc(n.s || "") + (n.ko ? " · 제목 기계번역" : "") + " · " + "기사" + " ↗</small></a>";
      }).join("") + "</div>" : '<p class="vdk-note">이번에는 관련 뉴스가 같이 오지 않았어요.</p>');
    } else if (src === "yt" || src === "ytfun") {
      b = video(it);
    } else if (src === "reddit" || src === "memes") {
      b = (it.img ? '<a href="' + esc(it.url) + '" target="_blank" rel="noopener" class="vdk-img"><img src="' + esc(it.img) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.closest(\'a\').remove()"></a>' : "") +
        (it.desc ? '<p class="vdk-p">' + esc(it.desc) + "</p>" : "") +
        '<p class="vdk-note">' + esc(it.sub || "레딧") + " · " + esc(it.n || "") + (it.ko ? " · 제목 기계번역" : "") + " · 그 나라 사람들이 많이 모이는 게시판의 하루 인기 글이에요(나라 전체 여론은 아니에요).</p>" +
        '<a class="vdk-more" href="' + esc(it.url) + '" target="_blank" rel="noopener">레딧에서 글·댓글 보기 ↗</a>';
    } else if (src === "wiki") {
      var w = WK[it.url], lm = String(it.url).match(/^https:\/\/([a-z-]+)\./), lg = lm ? lm[1] : "";
      b = '<p class="vdk-h">얼마나 봤나</p><p class="vdk-p">어제 <b>' + esc(LANG[lg] || lg) + " 위키백과</b>에서 <b>" + esc(it.n || "") + "</b> 읽혔어요" + (it.sub ? " (" + esc(it.sub) + ")" : "") + ".</p>" +
        '<p class="vdk-note">위키백과는 나라가 아니라 언어별로 세요. ' + (LANG_WHO[lg] ? esc(LANG_WHO[lg]) + "에서 본 수를 모두 합친 숫자예요." : "그 언어를 쓰는 사람들이 본 수예요.") + " 한 문서를 하루 수천 번 보면 그 언어권에서 꽤 큰 관심이에요.</p>" +
        '<p class="vdk-h">어떤 문서인가 · 위키백과 첫 문단</p>' + (w ? '<p class="vdk-p">' + esc(w.text) + '</p><p class="vdk-note">위키백과(' + esc(LANG[w.lang] || w.lang) + ") ‘" + esc(w.title) + "’</p>" : w === null ? '<p class="vdk-note">설명을 불러오지 못했어요.</p>' : '<p class="vdk-note">설명을 불러오는 중…</p>') +
        '<a class="vdk-more" href="' + esc(ku(it.url, w && w.lang === "ko" ? "ko" : undefined)) + '" target="_blank" rel="noopener">문서 열기 ↗</a>';
    } else {
      var g = ((((o.country || {}).src || {}).google || {}).items) || [];
      var k = (it.ko || it.kw).toLowerCase(), hit = g.filter(function (x) { var t = (x.ko || x.kw).toLowerCase(); return t.indexOf(k) >= 0 || k.indexOf(t) >= 0; })[0];
      b = (it.sub ? '<p class="vdk-p">' + esc(it.sub) + "</p>" : "") + (hit && (hit.news || []).length ? '<p class="vdk-h">관련 뉴스 (구글 급상승)</p><div class="vdk-links">' + hit.news.map(function (n) { return '<a href="' + esc(ku(n.u)) + '" target="_blank" rel="noopener">' + esc(n.ko || n.t) + "<small>" + esc(n.s || "") + "</small></a>"; }).join("") + "</div>" : '<p class="vdk-note">이 출처는 검색어만 알려 줘요. 이유는 검색 결과에서 확인해요.</p>') +
        '<a class="vdk-more" href="' + esc(it.url) + '" target="_blank" rel="noopener">그 사이트 검색 결과 보기 ↗</a>';
    }
    // 모든 트렌드 카드에 구글 검색 단추 (검색어 원문 그대로)
    var gq = src === "wiki" ? String(it.kw || "").replace(/_/g, " ") : (it.kw || "");
    var gs = '<a class="vdk-more vdk-gsearch" href="https://www.google.com/search?q=' + encodeURIComponent(gq) + '" target="_blank" rel="noopener">🔍 구글에서 검색 ↗</a>';
    return '<div class="vdk-body dk">' + h + (o.extra || "") + b + gs + "</div>";
  }
  var css = document.createElement("style");
  css.textContent = ".vdk-yt{position:relative;display:block;margin:2px 0 12px;border-radius:12px;overflow:hidden;aspect-ratio:16/9;background:rgba(118,118,128,.12)}.vdk-yt img{display:block;width:100%;height:100%;object-fit:cover}" +
    ".vdk-yt span{position:absolute;left:50%;top:50%;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;display:grid;place-items:center;font-size:17px;padding-left:3px;box-sizing:border-box}" +
    ".vdk-img{display:block;margin:4px 0 10px;border-radius:12px;overflow:hidden;background:rgba(118,118,128,.12)}.vdk-img img{display:block;width:100%;max-height:60vh;object-fit:contain}";
  document.head.appendChild(css);
  window.VfmTrend = { thumb: thumb, ytId: ytId, card: card, items: items, wikiFor: wikiFor, WK: WK, flag: flag, esc: esc, ADULT: ADULT };
})();
