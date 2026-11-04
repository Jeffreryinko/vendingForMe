/* mix.js — 자판기 홈의 "랜덤 넘겨보기" + 한 번에 찾기 + 섞는 비율. 토큰 0.
 *  재료: 시사 이야기·단신 / 나라별 오늘 / 트렌드(22개국 검색어·영상) / 레딧·밈 / AI 새 기능 / 이야기·역사(가끔)
 *  · 새 것 위주로 섞음(최근 것이 앞쪽에 몰리게 섞은 뒤, 종류는 비율대로 뽑음)
 *  · 본 카드는 그 앱의 본 기록에도 남음 → 앱에 들어가도 다시 안 나옴
 *  · 비율은 종류마다 많이·보통·적게·끄기 (폰에 저장)
 */
(function () {
  "use strict";
  var D = window.VfmDeck, T = window.VfmTrend, esc = D.esc, flag = T.flag;
  var KINDS = [["sisa", "시사 이야기·단신"], ["trend", "트렌드 (검색어·영상)"], ["meme", "레딧·밈"], ["ai", "AI 새 기능"], ["nation", "나라별 오늘"], ["story", "이야기·역사"]];
  var DEF = { sisa: 3, trend: 3, meme: 2, ai: 2, nation: 2, story: 1 };
  var WNAME = ["끄기", "적게", "보통", "많이"];
  var W = Object.assign({}, DEF, (function () { try { return JSON.parse(localStorage.getItem("vfm:mix:w") || "{}"); } catch (e) { return {}; } })());
  var POOL = { sisa: [], trend: [], meme: [], ai: [], nation: [], story: [] };
  var CAT = { war: "전쟁·안보", pol: "정치·외교", eco: "경제·시장", tech: "기술·과학", dis: "재난·사고", soc: "사회", spo: "스포츠", cul: "문화" };
  var RK = null; try { RK = new Intl.DisplayNames(["ko"], { type: "region" }); } catch (e) { }
  var cname = function (c) { if (c === "WW") return "세계"; try { return RK ? RK.of(c) : c; } catch (e) { return c; } };
  var go = function (h) { return ' data-mixgo="' + esc(h) + '"'; };
  function j(p) { return fetch(p, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  // 새 것 위주 섞기: 앞쪽(새 것) 절반을 섞고, 뒤쪽을 섞어 이어 붙임
  function freshShuffle(a) {
    var sh = function (x) { for (var i = x.length - 1; i > 0; i--) { var k = Math.floor(Math.random() * (i + 1)); var t = x[i]; x[i] = x[k]; x[k] = t; } return x; };
    var n = Math.max(1, Math.ceil(a.length * 0.4));
    return sh(a.slice(0, n)).concat(sh(a.slice(n)));
  }
  function add(kind, list) {
    if (kind === "trend" || kind === "meme") {                     // 여러 나라가 따로 도착하니, 순위대(1~3위, 4~6위…)끼리 나라를 섞어서
      list.forEach(function (x) { x._b = Math.floor((x.rank || 0) / 3); x._r = Math.random(); });
      POOL[kind] = POOL[kind].concat(list).sort(function (a, b) { return a._b - b._b || a._r - b._r; });
    } else POOL[kind] = POOL[kind].concat(freshShuffle(list));
    D.stale("mix");
    var d = D.get("mix-home"); var el = d && d.el(); if (el && !document.getElementById("mxq").value.trim() && el.querySelector(".vdk-end")) d.paint();   // 읽던 카드는 건드리지 않음 (빈 화면일 때만 다시 그림)
  }

  /* ── 재료 받기 ── */
  // 시사: 최신 판 하나만 (이야기·단신·나라별 오늘)
  j("data/sisa/_meta.json").then(function (m) {
    if (!m || !m.edition) return;
    return j("data/sisa/editions/" + m.edition + ".json").then(function (ed) {
      if (!ed) return;
      var st = (ed.stories || []).filter(function (s) { return s.title && (s.key || s.sum); });
      var rank = function (s) { return (s.top ? 0 : 2) + (s.delta === "new" ? 0 : 1) + (s.kind === "brief" ? 2 : 0); };
      st.sort(function (a, b) { return rank(a) - rank(b); });
      add("sisa", st.map(function (s) {
        var brief = s.kind === "brief", key = brief ? "b:" + (s.items[0] || s.id) : "i:" + s.title, cs = s.countries || [];
        return { key: key, sa: "sisa", kind: "sisa", title: s.title, url: location.origin + location.pathname + "sisa/#issue-" + s.id, shareText: s.title + (s.key ? "\n" + s.key : ""),
          q: s.title + " " + (s.key || ""), html: function () {
            return '<div class="vdk-body"><div class="vdk-k"><span class="mx-tag sisa">시사</span>' + (CAT[s.cat] ? "<span>" + CAT[s.cat] + "</span>" : "") + "<span>" + cs.slice(0, 6).map(flag).join("") + "</span><span>" + (brief ? "단신" : cs.length + "개국") + "</span>" + (s.delta === "new" ? '<b class="new">새 소식</b>' : "") + "</div>" +
              '<h2 class="vdk-t">' + esc(s.title) + '</h2><p class="vdk-p">' + esc(s.key || s.sum) + "</p>" +
              (s.why3 ? '<p class="vdk-h">왜 중요한가</p><p class="vdk-p">' + esc(s.why3.now || s.why3.link || "") + "</p>" : "") +
              ((s.bg || []).length ? '<p class="vdk-h">알아 둘 배경</p><ol class="vdk-ol">' + s.bg.map(function (b) { return "<li>" + esc(b) + "</li>"; }).join("") + "</ol>" : "") +
              '<button type="button" class="vdk-more"' + go("sisa/#issue-" + s.id) + ">" + (brief ? "시사에서 기사 보기 ›" : "시사에서 해설·기사 전체 보기 ›") + "</button></div>";
          } };
      }));
      var dg = ed.countryDigest || {};
      add("nation", Object.keys(dg).map(function (c) {
        return { key: "n:" + c + ":" + dg[c].slice(0, 24), sa: "sisa", kind: "nation", title: cname(c) + "의 오늘", url: location.origin + location.pathname + "sisa/#nation", shareText: cname(c) + "의 오늘\n" + dg[c], q: cname(c) + " " + dg[c],
          html: function () { return '<div class="vdk-body"><div class="vdk-k"><span class="mx-tag nation">나라별 오늘</span><span>' + esc(ed.label || "") + '</span></div><h2 class="vdk-t">' + flag(c) + " " + esc(cname(c)) + '의 오늘</h2><p class="vdk-p">' + esc(dg[c]) + '</p><button type="button" class="vdk-more"' + go("sisa/#nation") + ">이 나라 뉴스 넘겨 보기 ›</button></div>"; } };
      }));
    });
  });
  // 트렌드·레딧·밈: 22개국
  j("data/trends/_index.json").then(function (idx) {
    if (!idx) return;
    var memes = (idx.memes || []).map(function (it, r) {
      return { key: "t:WW:memes:" + it.kw, sa: "sisa", kind: "meme", rank: r, title: it.ko || it.kw, url: it.url, shareText: it.ko || it.kw, q: (it.ko || "") + " " + it.kw,
        html: function () { return T.card({ cc: "WW", cname: "세계 밈", src: "memes", srcName: "레딧 밈", it: it, rank: r }); } };
    });
    if (memes.length) add("meme", memes);
    (idx.countries || []).forEach(function (cn) {
      var cc = cn[0];
      j("data/trends/" + cc + ".json").then(function (d) {
        if (!d) return;
        var tr = [], mm = [];
        T.items(d).forEach(function (x) {
          var item = { key: "t:" + cc + ":" + x.src + ":" + x.it.kw, sa: "sisa", kind: x.src === "reddit" || x.src === "ytfun" ? "meme" : "trend", title: x.it.ko || x.it.kw,
            url: x.it.url, rank: x.rank, shareText: flag(cc) + " " + d.name + " " + x.srcName + " " + (x.rank + 1) + "위 · " + (x.it.ko || x.it.kw), q: (x.it.ko || "") + " " + x.it.kw + " " + d.name, src: x.src, it: x.it,
            html: function () { return T.card({ cc: cc, cname: d.name, src: x.src, srcName: x.srcName, it: x.it, rank: x.rank, country: d }); } };
          (item.kind === "meme" ? mm : tr).push(item);
        });
        add("trend", tr); if (mm.length) add("meme", mm);
      });
    });
  });
  // AI 새 기능 (+ 정리된 '어떻게 써 보나')
  Promise.all([j("data/ai/feed.json"), j("data/ai/feat.json")]).then(function (r) {
    var F = r[0] || {}, FE = r[1] || {};
    var list = (F.posts || []).concat(F.news || [], F.vids || []).sort(function (a, b) { return (FE[b.id] ? 1 : 0) - (FE[a.id] ? 1 : 0) || String(b.date || "").localeCompare(String(a.date || "")); });
    add("ai", list.map(function (p) {
      var f = FE[p.id], vid = !!p.vid, one = (f && f.one) || p.ksum || p.sum || ""; if (one.length > 220) one = one.slice(0, 210).replace(/\s\S*$/, "") + "…";
      return { key: p.id, sa: "ai", kind: "ai", title: p.ko || p.title, url: p.url, shareText: (p.ko || p.title) + "\n" + p.url, q: (p.ko || "") + " " + p.title + " " + (p.name || ""),
        html: function () {
          return '<div class="vdk-body"><div class="vdk-k"><span class="mx-tag ai">AI</span><span>' + esc(p.name || p.ch || "") + "</span><span>" + esc(p.date || "") + "</span></div>" +
            '<h2 class="vdk-t">' + esc(p.ko || p.title) + "</h2>" + (p.ko ? '<p class="vdk-note" style="margin:-6px 0 10px">' + esc(p.title) + "</p>" : "") +
            (one ? '<p class="vdk-h">뭐가 생겼나</p><p class="vdk-p">' + esc(one) + "</p>" : "") + (f && f.how ? '<p class="vdk-h">나는 어떻게 써 보나</p><p class="vdk-p">' + esc(f.how) + "</p>" : "") +
            '<a class="vdk-more" href="' + esc(vid ? p.url : D.koUrl(p.url)) + '" target="_blank" rel="noopener">' + (vid ? "유튜브에서 보기 ↗" : "원문 보기 (한국어 번역) ↗") + "</a>" +
            '<button type="button" class="vdk-more"' + go("ai/#today") + ">AI 탭에서 더 보기 ›</button></div>";
        } };
    }));
  });
  // 이야기·역사 (가끔): 첫 카드가 뜬 다음에 받음
  setTimeout(function () {
    j("data/iyagi/stories/_index.json").then(function (a) {
      if (!Array.isArray(a)) return;
      add("story", a.map(function (s) {
        var d1 = ((s.depths || {}).d1 || {}).body || [];
        return { key: s.id, sa: "iyagi", kind: "story", title: s.title, url: location.origin + location.pathname + "iyagi/#read-" + s.id, shareText: s.title + (s.hook ? "\n" + s.hook : ""), q: s.title + " " + (s.orig || "") + " " + (s.hook || ""),
          html: function () {
            return '<div class="vdk-body"><div class="vdk-k"><span class="mx-tag story">이야기</span><span>' + esc(s.kind || "") + "</span><span>" + esc(s.region || "") + '</span></div><h2 class="vdk-t">' + esc(s.title) + '</h2><p class="vdk-note">' + esc(s.orig || "") + "</p>" +
              d1.filter(function (x) { return typeof x === "string"; }).slice(0, 3).map(function (x) { return '<p class="vdk-p">' + esc(x) + "</p>"; }).join("") +
              '<button type="button" class="vdk-more"' + go("iyagi/#read-" + s.id) + ">이야기 끝까지 읽기 ›</button></div>";
          } };
      }));
    });
    j("data/history/top.json").then(function (h) {
      if (!h || !h.all) return;
      add("story", h.all.slice(0, 400).map(function (r) {
        var id = r[0], title = r[1], y = r[2], sum = r[14] || "";
        return { key: "h:" + id, sa: "history", kind: "story", title: title, url: location.origin + location.pathname + "history/#p=" + id, shareText: title, q: title + " " + sum,
          html: function () {
            return '<div class="vdk-body"><div class="vdk-k"><span class="mx-tag story">역사</span>' + (y != null ? "<span>" + (y < 0 ? "기원전 " + (-y) : y) + "년</span>" : "") + "<span>" + (r[6] || []).slice(0, 4).map(flag).join("") + '</span></div><h2 class="vdk-t">' + esc(title) + '</h2><p class="vdk-p">' + esc(sum) + "…</p>" +
              '<button type="button" class="vdk-more"' + go("history/#p=" + id) + ">역사에서 이어 읽기 ›</button></div>";
          } };
      }));
    });
  }, 2500);

  /* ── 비율대로 섞기 ── */
  function mixed() {
    var ptr = {}, out = [], used = {};
    KINDS.forEach(function (k) { ptr[k[0]] = 0; });
    for (;;) {
      var live = KINDS.map(function (k) { return k[0]; }).filter(function (k) { return W[k] > 0 && ptr[k] < POOL[k].length; });
      if (!live.length) break;
      var tot = live.reduce(function (a, k) { return a + W[k] * W[k]; }, 0), r = Math.random() * tot, pick = live[0];   // 많이(3)=9, 보통(2)=4, 적게(1)=1 배
      for (var i = 0; i < live.length; i++) { r -= W[live[i]] * W[live[i]]; if (r <= 0) { pick = live[i]; break; } }
      var it = POOL[pick][ptr[pick]++];
      if (!used[it.key]) { used[it.key] = 1; out.push(it); }
    }
    return out;
  }
  var deck = D.create({ id: "mix-home", app: "mix", emptyTitle: "불러오는 중이에요", emptyNote: "잠시만요. 시사·트렌드·AI를 모으고 있어요.", items: mixed,
    onShow: function (x) { if (x.src === "wiki" && T.WK[x.it.url] === undefined) T.wikiFor(x.it.url).then(function () { if (deck.curKey() === x.key) deck.paint(); }); } });
  var sdeck = null;

  /* ── 화면 ── */
  var host = document.getElementById("mix");
  function ratioHtml() {
    return '<div class="mx-ratio" id="mxRatio" hidden><p class="mx-rh">섞는 비율 <small>종류마다 고르세요 · 바꾸면 바로 다시 섞어요</small></p>' + KINDS.map(function (k) {
      return '<div class="mx-row"><span>' + k[1] + '</span><div class="mx-seg">' + [3, 2, 1, 0].map(function (v) { return '<button type="button" data-mxw="' + k[0] + "|" + v + '" aria-pressed="' + (W[k[0]] === v) + '">' + WNAME[v] + "</button>"; }).join("") + "</div></div>";
    }).join("") + '<button type="button" class="mx-reset" data-mxw="reset">처음 비율로</button></div>';
  }
  host.innerHTML = '<div class="mx-top"><input id="mxq" type="search" placeholder="전부에서 찾기 (예: 트럼프, 아이폰)" aria-label="한 번에 찾기"><button type="button" id="mxRatioBtn" aria-label="섞는 비율">비율</button></div>' +
    ratioHtml() + '<p class="mx-note" id="mxNote">시사·트렌드·밈·AI를 섞어서 한 장씩 · 옆으로 밀면 다음 · 본 것은 다시 안 나와요</p><div id="mxDeck">' + deck.html() + "</div>";
  var q = document.getElementById("mxq"), qT = null;
  q.addEventListener("input", function () {
    clearTimeout(qT); qT = setTimeout(function () {
      var v = q.value.trim().toLowerCase(), box = document.getElementById("mxDeck"), note = document.getElementById("mxNote");
      if (v.length < 2) { note.textContent = "시사·트렌드·밈·AI를 섞어서 한 장씩 · 옆으로 밀면 다음 · 본 것은 다시 안 나와요"; box.innerHTML = deck.html(); return; }
      var all = [];
      KINDS.forEach(function (k) { all = all.concat(POOL[k[0]]); });
      var seen = {}, hits = all.filter(function (x) { if (seen[x.key] || String(x.q || x.title).toLowerCase().indexOf(v) < 0) return false; seen[x.key] = 1; return true; });
      note.textContent = "‘" + q.value.trim() + "’ 찾은 것 " + hits.length + "장 · 본 것도 나와요";
      sdeck = D.create({ id: "mix-search", app: "mix", noSeen: true, emptyTitle: "찾은 게 없어요", emptyNote: "다른 낱말로 찾아보세요. 지금 불러온 자료 안에서 찾아요.", items: function () { return hits; } });
      sdeck.queue = null; sdeck.hist = []; sdeck.pos = -1;
      box.innerHTML = sdeck.html();
    }, 250);
  });
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-mxw],#mxRatioBtn,[data-mixgo]"); if (!t) return;
    if (t.id === "mxRatioBtn") { var r = document.getElementById("mxRatio"); r.hidden = !r.hidden; return; }
    if (t.hasAttribute("data-mixgo")) { try { sessionStorage.setItem("vfm:fromHome", "1"); } catch (x) { } location.href = t.getAttribute("data-mixgo"); return; }
    var v = t.getAttribute("data-mxw");
    if (v === "reset") W = Object.assign({}, DEF);
    else { var p = v.split("|"); W[p[0]] = +p[1]; }
    try { localStorage.setItem("vfm:mix:w", JSON.stringify(W)); } catch (x) { }
    document.getElementById("mxRatio").outerHTML = ratioHtml().replace(" hidden", "");
    deck.refresh();
    if (window.vfm && window.vfm.toast) window.vfm.toast("비율을 바꿨어요");
  });
  var css = document.createElement("style");
  css.textContent = ".mx-top{display:flex;gap:8px;margin:0 0 8px}.mx-top input{flex:1;min-width:0;border:0;border-radius:12px;padding:11px 14px;font:inherit;font-size:16px;background:var(--ap-fill);color:var(--ap-label)}" +
    ".mx-top button{flex:none;border:0;border-radius:12px;padding:0 14px;font:inherit;font-weight:600;background:var(--ap-fill);color:var(--ap-label)}" +
    ".mx-note{margin:0 4px 4px;font-size:12.5px;color:var(--ap-label2)}" +
    ".mx-ratio{background:var(--ap-surface);border-radius:14px;padding:12px;margin:0 0 10px}.mx-rh{margin:0 0 8px;font-weight:700}.mx-rh small{font-weight:400;color:var(--ap-label2);font-size:12px;display:block}" +
    ".mx-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 0;border-top:.5px solid var(--ap-sep);font-size:14px}.mx-row:first-of-type{border-top:0}" +
    ".mx-seg{display:flex;gap:2px;background:var(--ap-fill);border-radius:9px;padding:2px;flex:none}.mx-seg button{border:0;border-radius:7px;padding:6px 8px;font:inherit;font-size:12.5px;background:none;color:var(--ap-label)}.mx-seg button[aria-pressed=true]{background:var(--ap-seg-on);font-weight:700;box-shadow:0 1px 4px rgba(0,0,0,.12)}" +
    ".mx-reset{margin-top:8px;border:0;background:none;color:var(--ap-blue);font:inherit;font-size:14px;padding:4px 0}" +
    ".mx-tag{font-weight:700;padding:2px 8px;border-radius:999px;font-size:12px}.mx-tag.sisa{background:color-mix(in srgb,var(--ap-blue) 15%,transparent);color:var(--ap-blue-t)}" +
    ".mx-tag.nation{background:color-mix(in srgb,var(--ap-teal) 18%,transparent);color:var(--ap-teal)}.mx-tag.ai{background:color-mix(in srgb,var(--ap-purple) 15%,transparent);color:var(--ap-purple-t)}" +
    ".mx-tag.story{background:color-mix(in srgb,var(--ap-orange) 16%,transparent);color:var(--ap-orange-t)}.vdk .new{color:var(--ap-blue-t)}";
  document.head.appendChild(css);
})();
