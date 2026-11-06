/* history-player.js — 역사 탭 공통 에피소드 플레이어 (토큰 0, 서버 0)
 *  · 편집 에피소드: data/history/editorial/index.json + episodes/{id}.json (사람이 출처를 확인해 쓴 것만)
 *  · 읽는 장면은 그냥 스크롤, 판단이 필요한 장면(선택)에서만 멈춤. ‘전체 글’로 바꾸면 멈춤 없이 다 보임
 *  · 진행 저장: vfm:history:ep → { id: { ch:{장면:선택}, last, cue, done, at } }  (메모는 vfm:history:memo 의 "ep:id")
 *  · 표시: 기록(번호 = 출처) · 해석 · 재구성 · 가정 · 전승 — 장면마다
 *  역사 탭(history/index.html)의 esc·toast·LS·S·save·nav·idOf 등을 부를 때 씀 (그 스크립트보다 먼저 읽히지만, 부르는 건 나중이라 괜찮음)
 */
window.HP = (function () {
  "use strict";
  var BASE = "../data/history/editorial/";
  var IDX = null, EPS = {};
  var MARK = { recon: ["재구성 장면", "실제 기록이 아니라 이해를 돕기 위해 꾸민 장면이에요"], interp: ["해석", "기록을 바탕으로 한 풀이예요"], hypo: ["가정", "실제로 일어나지 않은 경우를 따져 본 거예요"], lore: ["전승", "후대에 전해진 이야기예요"] };
  var EMPTY = { episodes: [], programs: {}, moods: {}, featured: [] };

  function index() {
    if (IDX) return Promise.resolve(IDX);
    return fetch(BASE + "index.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : EMPTY; }).catch(function () { return EMPTY; }).then(function (j) { IDX = j; return j; });
  }
  function ep(id) {
    if (EPS[id]) return Promise.resolve(EPS[id]);
    return fetch(BASE + "episodes/" + encodeURIComponent(id) + ".json", { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error("없음"); return r.json(); }).then(function (j) { EPS[id] = j; return j; });
  }
  function st(id) { return S.ep[id] || (S.ep[id] = { ch: {}, at: 0 }); }
  function meta(id) { return ((IDX || EMPTY).episodes || []).find(function (e) { return e.id === id; }); }
  function progName(p) { return (((IDX || EMPTY).programs || {})[p] || {}).name || ""; }
  function stateLabel(id) { var s = S.ep[id]; if (!s) return ""; if (s.done) return "다 봄"; if (s.last) return "이어서 보기"; return ""; }

  /* ── 글 꾸미기: [1] → 출처 단추, 빈 줄 → 문단, “로 시작하면 인용 ── */
  function fmt(t, sid) {
    return String(t || "").split(/\n\n+/).map(function (p) {
      var h = esc(p).replace(/\[(\d+)\]/g, '<button type="button" class="ep-cite" data-ep-src="$1" aria-label="출처 $1">$1</button>');
      return /^[“"]/.test(p) ? '<p class="ep-quote">' + h + "</p>" : "<p>" + h + "</p>";
    }).join("");
  }
  function fill(t, e, s) {                                          // {c1} → 그 장면에서 고른 것
    return String(t || "").replace(/\{(\w+)\}/g, function (_, sid) {
      var sc = e.scenes.find(function (x) { return x.id === sid; }), o = sc && s.ch[sid];
      if (!sc || !o) return "고르지 않음";
      if (o === "_skip") return "고르지 않음";
      var op = (sc.opts || []).find(function (x) { return x.id === o; }); return op ? op.label : "고르지 않음";
    });
  }

  /* ── 장면 하나 ── */
  function scene(sc, e, s, full) {
    var m = MARK[sc.mark];
    var out = '<section class="ep-s ep-' + sc.type + '" id="es-' + esc(sc.id) + '">';
    if (m) out += '<span class="ep-mark ep-mark-' + sc.mark + '" title="' + esc(m[1]) + '">' + m[0] + "</span>";
    if (sc.h) out += '<h2 class="ep-sh">' + esc(sc.h) + "</h2>";
    if (sc.note) out += '<p class="ep-note">' + esc(sc.note) + "</p>";
    if (sc.text) out += '<div class="ep-txt">' + fmt(sc.text) + "</div>";
    if (sc.rel) out += '<div class="ep-rel" role="list">' + sc.rel.map(function (r) {   // 관계: 처음엔 몇 개만, 선에 관계 종류를 적음
      return '<div class="ep-rl" role="listitem"><span class="ep-node">' + esc(r[0]) + '</span><span class="ep-edge">' + esc(r[1]) + '</span><span class="ep-node">' + esc(r[2]) + "</span></div>";
    }).join("") + "</div>";
    if (sc.items) out += '<div class="ep-doc">' + sc.items.map(function (it, i) {
      return '<details' + (full ? " open" : "") + '><summary><span class="ep-dn">' + (i + 1) + "</span>" + esc(it.label) + '</summary><div class="ep-txt">' + fmt(it.text) + "</div></details>";
    }).join("") + "</div>";
    if (sc.tabs) {
      var on = s.tab && s.tab[sc.id] != null ? s.tab[sc.id] : 0;
      out += '<div class="ep-tabs" role="tablist">' + sc.tabs.map(function (t, i) { return '<button type="button" role="tab" aria-selected="' + (i === on) + '" data-ep-tab="' + esc(sc.id) + '" data-i="' + i + '">' + esc(t.label) + "</button>"; }).join("") + "</div>" +
        sc.tabs.map(function (t, i) { return '<div class="ep-panel" role="tabpanel"' + (i === on || full ? "" : " hidden") + ">" + (full ? '<h3 class="ep-ph">' + esc(t.label) + "</h3>" : "") + '<div class="ep-txt">' + fmt(t.text) + "</div></div>"; }).join("");
    }
    if (sc.type === "choice") {
      var pick = s.ch[sc.id];
      out += '<p class="ep-q">' + esc(sc.q) + "</p>";
      if (!pick && full) {                                          // 전체 글: 고르지 않았으면 모든 갈래를 글로
        out += '<div class="ep-all">' + sc.opts.map(function (o) { return '<div class="ep-reply"><b>‘' + esc(o.label) + "’을 고르면</b>" + fmt(fill(o.reply, e, s)) + "</div>"; }).join("") + "</div>";
      } else {
        out += '<div class="ep-opts">' + sc.opts.map(function (o) {
          var cls = pick ? (pick === o.id ? " on" : " dim") : "";
          return '<button type="button" class="ep-opt' + cls + '" data-ep-c="' + esc(sc.id) + '" data-o="' + esc(o.id) + '"' + (pick ? " disabled" : "") + ">" + esc(o.label) + "</button>";
        }).join("") + "</div>";
        if (!pick) out += '<button type="button" class="ep-skip" data-ep-c="' + esc(sc.id) + '" data-o="_skip">' + esc(sc.skip || "고르지 않고 계속") + " ›</button>";
        else if (pick !== "_skip") { var op = sc.opts.find(function (x) { return x.id === pick; }); if (op) out += '<div class="ep-reply">' + fmt(fill(op.reply, e, s)) + "</div>"; }
      }
    }
    return out + "</section>";
  }

  /* ── 에피소드 화면 ── */
  var CUR = null;
  function render(id, keepScroll) {
    var app = document.getElementById("app");
    return Promise.all([index(), ep(id)]).then(function (r) {
      var e = r[1], s = st(id), full = !!(S.cfg && S.cfg.epFull);
      CUR = e;
      var vis = [], stopped = false;
      for (var i = 0; i < e.scenes.length; i++) {
        var sc = e.scenes[i]; vis.push(sc);
        if (!full && sc.type === "choice" && !s.ch[sc.id]) { stopped = true; break; }
      }
      var last = vis[vis.length - 1];
      if (!full) { s.last = last.id; s.cue = last.cue || last.h || ""; }
      if (vis.some(function (x) { return x.type === "result"; }) && !s.done) { s.done = Date.now(); }
      s.at = Date.now(); save("ep");
      var m = meta(id) || e, pg = progName(e.program), nSrc = (e.sources || []).length;
      var end = !stopped;
      app.innerHTML = '<div class="read-top"><button class="ib" data-act="back" aria-label="뒤로">‹</button><span class="ep-tt">' + esc(pg) + '</span><span class="sp"></span>' +
        '<button class="btn sm" data-ep="full" aria-pressed="' + full + '">' + (full ? "멈추며 읽기" : "전체 글") + "</button></div>" +
        '<article class="ep" data-mood="' + esc(e.mood) + '">' +
        '<header class="ep-h"><p class="ep-prog">' + esc(pg) + " · 약 " + e.mins + "분</p><h1>" + esc(e.title) + '</h1><p class="ep-hook">' + esc(e.hook) + "</p>" +
        '<p class="ep-meta">' + esc([e.place, e.when].filter(Boolean).join(" · ")) + ' · <button type="button" class="lnk" data-ep="srcs">출처 ' + nSrc + "개</button></p>" +
        '<p class="ep-legend">작은 번호는 출처예요. 꾸민 장면은 <span class="ep-mark ep-mark-recon">재구성 장면</span>, 풀이는 <span class="ep-mark ep-mark-interp">해석</span>으로 따로 표시해요.</p></header>' +
        vis.map(function (sc) { return scene(sc, e, s, full); }).join("") +
        (end ? endHtml(e, s) : '<p class="ep-wait">고르면 다음 장면이 이어져요 · 위의 ‘전체 글’로 한 번에 읽어도 돼요</p>') +
        "</article>";
      if (end) resolveNext(e);
      if (!keepScroll) scrollTo(0, 0);
      return e;
    }).catch(function () {
      app.innerHTML = '<div class="read-top"><button class="ib" data-act="back" aria-label="뒤로">‹</button></div><p class="empty">이 이야기를 불러오지 못했어요.<br><button class="btn sm" data-ep-retry="' + esc(id) + '" style="margin-top:12px">다시 시도</button> <button class="btn sm" data-v="explore">자료 탐색으로</button></p>';
    });
  }
  function endHtml(e, s) {
    var k = "ep:" + e.id;
    var ser = ((IDX || EMPTY).series || []).filter(function (x) { return x.eps.indexOf(e.id) >= 0; }).map(function (x) {
      var rest = x.eps.slice(x.eps.indexOf(e.id) + 1).concat(x.eps.slice(0, x.eps.indexOf(e.id))).filter(function (id) { return !(S.ep[id] || {}).done && id !== e.id; });
      return rest.length && meta(rest[0]) ? '<p class="srcl">시리즈 「' + esc(x.name) + "」의 다음 편</p>" + card(meta(rest[0])) : "";
    }).filter(Boolean).slice(0, 1).join("");
    return '<section class="ep-end">' + ser + '<h2 class="sec">다음 질문</h2><div class="ep-next" id="epNext">' + (e.next || []).map(function (n, i) {
      return '<div class="ep-nx" data-nx="' + i + '"><small>' + esc(n.dir) + "</small><b>" + esc(n.q) + '</b><span class="sub">찾는 중…</span></div>';
    }).join("") + "</div>" +
      '<div class="ep-acts"><button class="btn sm" data-ep="star">' + (S.star[k] ? "★ 저장됨" : "☆ 저장") + '</button><button class="btn sm" data-ep="share">공유</button><button class="btn sm" data-ep="think">생각 남기기</button><button class="btn sm" data-ep="restart">처음부터</button></div>' +
      '<p class="lbl">메모</p><textarea class="memo" data-ep-memo="' + esc(e.id) + '" placeholder="이 이야기에 대한 메모 (이 폰에만 저장)">' + esc(S.memo[k] || "") + "</textarea>" +
      '<section class="ep-src" id="epSrc"><h2 class="sec">출처와 표시</h2><ol>' + (e.sources || []).map(function (x) {
        return '<li id="src-' + x.n + '"><a href="' + esc(x.url) + '" target="_blank" rel="noopener">' + esc(x.title) + " ↗</a><small>뒷받침: " + esc(x.supports) + "</small></li>";
      }).join("") + "</ol>" + (e.extra ? '<p class="sub">' + esc(e.extra) + "</p>" : "") +
      ((e.log || []).length ? '<p class="sub">수정 이력: ' + e.log.map(function (l) { return esc(l.v + " " + l.what); }).join(" · ") + "</p>" : "") +
      '<p class="sub">확인한 날 ' + esc(e.ver || "") + ". 틀린 곳을 발견하면 ‘생각 남기기’에 적어 주세요. 고칠 때 이 주소는 그대로 둡니다.</p></section></section>";
  }
  function resolveNext(e) {
    (e.next || []).forEach(function (n, i) {
      var box = document.querySelector('.ep-nx[data-nx="' + i + '"]'); if (!box) return;
      var done = function (attrs, sub) {
        if (!attrs) { box.querySelector(".sub").textContent = sub; box.classList.add("off"); return; }
        var b = document.createElement("button"); b.type = "button"; b.className = "ep-nx"; b.innerHTML = box.innerHTML; b.querySelector(".sub").textContent = sub;
        Object.keys(attrs).forEach(function (k) { b.setAttribute(k, attrs[k]); }); box.replaceWith(b);
      };
      if (n.ep) { var m = meta(n.ep); return done(m ? { "data-ep-open": n.ep } : null, m ? "편집 이야기 · " + m.title + " · 약 " + m.mins + "분" : "아직 없음"); }
      if (n.xm) return done({ "data-ep-xm": n.xm, "data-se": n.se != null ? n.se : "", "data-from": n.from != null ? n.from : "" }, n.xm === "sync" ? "탐색 · 나란히 보기" : "탐색 · 나라의 일생");
      if (n.page) idOf(n.page).then(function (pid) { done(pid ? { "data-open": pid } : null, pid ? "원문 자료 · " + n.page : "원문 자료가 아직 없어요"); }).catch(function () { done(null, "원문 자료가 아직 없어요"); });
    });
  }

  /* ── 카드 (첫 화면·시리즈에서 씀) ── */
  function card(m, big) {
    if (!m) return "";
    var c = m.cover || {}, sl = stateLabel(m.id), s = S.ep[m.id] || {};
    return '<button type="button" class="epc epc-' + esc(c.kind || "scene") + (big ? " big" : "") + '" data-ep-open="' + esc(m.id) + '" data-mood="' + esc(m.mood) + '">' +
      '<span class="epc-top"><span class="epc-stamp">' + esc(c.stamp || "") + '</span><span class="epc-line">' + esc(c.line || "") + "</span></span>" +
      '<b class="epc-t">' + esc(m.title) + '</b><span class="epc-hook">' + esc(m.hook) + "</span>" +
      '<span class="epc-m">' + esc(progName(m.program)) + " · 약 " + m.mins + "분" + (sl ? ' · <em>' + sl + "</em>" : "") + "</span>" +
      (big ? '<span class="epc-go">' + (s.done ? "다시 보기" : s.last ? "이어서 보기" : "읽기 시작") + " ›</span>" : "") + "</button>";
  }

  /* ── 누르기 ── */
  document.addEventListener("click", function (ev) {
    var t = ev.target.closest && ev.target.closest("[data-ep],[data-ep-c],[data-ep-src],[data-ep-tab],[data-ep-open],[data-ep-xm],[data-ep-retry]"); if (!t) return;
    var d = t.dataset;
    if (d.epOpen) { nav("#ep=" + d.epOpen); return; }
    if (d.epRetry) { delete EPS[d.epRetry]; IDX = null; render(d.epRetry); return; }
    if (d.epXm) { if (d.epXm === "sync") { F.mode = "sync"; if (d.se !== "") F.se = +d.se; F.sfrom = d.from !== "" ? +d.from : null; } else { F.mode = "life"; } nav("#explore"); return; }
    var e = CUR; if (!e) return; var s = st(e.id), k = "ep:" + e.id;
    if (d.epC) {
      s.ch[d.epC] = d.o; save("ep");
      render(e.id, true).then(function () {
        var el = document.querySelector("#es-" + d.epC + " .ep-reply") || document.querySelector("#es-" + d.epC)?.nextElementSibling;
        var rm = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (el) el.scrollIntoView({ block: "start", behavior: rm ? "auto" : "smooth" });
      });
      return;
    }
    if (d.epTab) { s.tab = s.tab || {}; s.tab[d.epTab] = +d.i; save("ep"); var y = scrollY; render(e.id, true).then(function () { scrollTo(0, y); }); return; }
    if (d.epSrc) { srcSheet(e, +d.epSrc); return; }
    if (d.ep === "srcs") { var box = document.getElementById("epSrc"); if (box) box.scrollIntoView({ block: "start" }); else srcSheet(e, 0); return; }
    if (d.ep === "full") { S.cfg.epFull = !S.cfg.epFull; save("cfg"); var y2 = scrollY; render(e.id, true).then(function () { scrollTo(0, y2); }); return; }
    if (d.ep === "restart") { S.ep[e.id] = { ch: {}, at: Date.now(), done: s.done }; save("ep"); toast("처음부터 · 메모는 그대로예요"); render(e.id); return; }
    if (d.ep === "star") {
      if (S.star[k]) { delete S.star[k]; toast("저장 해제"); }
      else { S.star[k] = { at: Date.now(), item: { i: k, t: e.title, o: e.hook, y: null, c: [], g: "", h: -1, e: -1, k: "", r: "xx", n: 0 } }; toast("저장했어요 · 내 기록에서 봐요"); }
      save("star"); var y3 = scrollY; render(e.id, true).then(function () { scrollTo(0, y3); }); return;
    }
    if (d.ep === "share") {
      var url = location.origin + location.pathname + "#ep=" + e.id;      // 진행·메모는 주소에 넣지 않음
      var text = e.title + "\n" + e.hook + " (약 " + e.mins + "분)";
      if (navigator.share) navigator.share({ title: e.title, text: text, url: url }).catch(function () { });
      else if (navigator.clipboard) navigator.clipboard.writeText(text + "\n" + url).then(function () { toast("복사했어요"); });
      return;
    }
    if (d.ep === "think") { if (window.vfm && window.vfm.think) window.vfm.think({ app: "history", key: k, title: e.title, url: "history/#ep=" + e.id }); return; }
  });
  var memoT = null;
  document.addEventListener("input", function (ev) {
    var t = ev.target; if (!t.dataset || !t.dataset.epMemo) return;
    clearTimeout(memoT); memoT = setTimeout(function () { var k = "ep:" + t.dataset.epMemo; if (t.value.trim()) S.memo[k] = t.value; else delete S.memo[k]; save("memo"); }, 400);
  });
  function srcSheet(e, n) {
    var list = (e.sources || []).filter(function (x) { return !n || x.n === n; });
    var back = document.createElement("div"); back.className = "back";
    back.innerHTML = '<div class="sheet" role="dialog" aria-label="출처"><h3>' + (n ? "출처 " + n : "출처") + "</h3>" + list.map(function (x) {
      return '<div class="wiki"><a href="' + esc(x.url) + '" target="_blank" rel="noopener"><b>' + esc(x.title) + ' ↗</b></a><p class="sub" style="margin:6px 0 0">이 출처가 뒷받침하는 것: ' + esc(x.supports) + "</p></div>";
    }).join("") + '<button class="btn" style="width:100%;margin-top:8px" data-x="1">닫기</button></div>';
    back.addEventListener("click", function (ev) { if (ev.target === back || ev.target.dataset.x) back.remove(); });
    document.body.appendChild(back);
  }

  var FROM = "vfm:history:from";
  document.addEventListener("click", function (ev) {
    var t = ev.target.closest && ev.target.closest("article.ep [data-open], article.ep [data-ep-xm], article.ep [data-ep-open]");
    if (t && CUR && !t.closest(".ep-end > .epc")) try { sessionStorage.setItem(FROM, JSON.stringify({ id: CUR.id, t: CUR.title, at: Date.now() })); } catch (x) { }
  }, true);
  function pill() {
    var old = document.getElementById("epBackPill"); if (old) old.remove();
    var f = null; try { f = JSON.parse(sessionStorage.getItem(FROM) || "null"); } catch (x) { }
    if (!f || Date.now() - f.at > 3600e3) return;
    if (location.hash === "#ep=" + f.id) { try { sessionStorage.removeItem(FROM); } catch (x) { } return; }
    var b = document.createElement("div"); b.id = "epBackPill"; b.className = "ep-pill";
    b.innerHTML = '<button type="button" data-ep-open="' + esc(f.id) + '">‹ 「' + esc(f.t) + '」로 돌아가기</button><button type="button" class="x" aria-label="닫기">×</button>';
    b.querySelector(".x").addEventListener("click", function () { try { sessionStorage.removeItem(FROM); } catch (x) { } b.remove(); });
    document.body.appendChild(b);
  }
  window.addEventListener("hashchange", function () { setTimeout(pill, 60); });
  setTimeout(pill, 400);

  return { pill: pill, index: index, ep: ep, render: render, card: card, meta: meta, progName: progName };
})();
