/* univ.js — 'univ.': 내가 만든 자판기·띵크폴미·타이쿤을 4학기 과정으로 끝까지 익히는 일정표의 계산 부분.
   진도는 각 앱이 이 기기에 이미 남기는 기록을 읽어서 저절로 세요(로봇·토큰 0). 타이쿤만 주소가 달라 판 수를 직접 눌러요.
     세 교실   vfm:learn:<sisa|deal|gicho>:ch(끝낸 장) · box(외우기 상자에 든 용어) · ep(읽은 역사) · diag(수준 확인 {c,n})
     뇌        vfm:brain:srs  {부위: {b}}  — b 3 이상 = 외움 (뇌 화면의 '외운 부위'와 같은 기준)
     이야기    iyagi-library-v1 .levels {이야기: 읽은 깊이} — 1 이상 = 읽음
     맨탈      vfm:mental:school .done {수업: …}
     이 화면   vfm:univ = { set:{pace,speed,at}, ty:타이쿤 판 수, log:{날짜: 끝낸 분} }
   구글로 로그인하면 sync.js 가 vfm:* 와 iyagi-library-v1 을 기기끼리 맞춰요(그래서 폰·PC 진도가 같음).
   쓰는 곳: univ/index.html(전체 화면), 자판기 첫 화면·띵크폴미 홈의 '오늘 수업' 카드(VFM_UNIV.card). */
(function () {
  "use strict";
  var START = "2026-11-16";
  var PACES = [{ n: "가볍게", wd: 20, we: 40 }, { n: "기본", wd: 30, we: 60 }, { n: "집중", wd: 45, we: 90 }];
  var O = location.origin, VS = O + "/vendingForMe/", ST = O + "/vfm-story/", MD = O + "/vfm-mind/";
  var LINK = { tycoon: "https://tycoon-prototype.vercel.app/", think: O + "/thinkingForMe/", univ: VS + "univ/" };
  var TERMS = [
    { n: "1학기", t: "세상 읽는 눈", goal: "뉴스를 용어 찾지 않고 읽고, 타이쿤으로 가게 하나가 굴러가는 원리를 몸에 붙여요." },
    { n: "2학기", t: "돈과 사업", goal: "투자·인수 기사를 읽고, 운동시설 업종마다 돈 버는 구조가 어떻게 다른지 말할 수 있어요." },
    { n: "3학기", t: "교양의 뼈대", goal: "과학·심리학·철학의 큰 줄기를 이야기 순서로 꿰어요." },
    { n: "4학기", t: "사람과 이야기", goal: "사람을 읽는 기술과, 대화에서 비유로 통하는 이야기 100편을 갖춰요." }
  ];
  var BIG = ["frontal", "parietal", "temporal", "occipital", "hippocampus", "amygdala", "thalamus", "hypothalamus", "cerebellum", "midbrain", "pons", "medulla"];
  /* id, 학기, 종류, 이름, 단위, 전체, 하나에 드는 분(추정), 주소, 읽는 법, 시작 번호(이야기·뇌처럼 이어지는 것) */
  var U = [
    ["s_course", 0, "course", "세상 읽기 교실 · 코스", "장", 8, 15, VS + "sisa/learn/", ["learn", "sisa", "ch"]],
    ["s_terms", 0, "terms", "세상 읽기 교실 · 용어", "개", 129, 2.5, VS + "sisa/learn/", ["learn", "sisa", "box"]],
    ["s_hist", 0, "hist", "세상 읽기 교실 · 역사", "편", 77, 4, VS + "sisa/learn/", ["learn", "sisa", "ep"]],
    ["ty1", 0, "play", "타이쿤 · 헬스장 첫 판, 같은 운 다시, 다른 상권", "판", 3, 45, LINK.tycoon, ["ty", 0]],
    ["br1", 0, "brain", "뇌 · 큰 부위", "개", 12, 5, ST + "brain/", ["brain", 1]],
    ["iy1", 0, "story", "이야기 1~20편", "편", 20, 6, ST + "iyagi/", ["iyagi", 0]],
    ["d_course", 1, "course", "투자 교실 · 코스", "장", 8, 15, VS + "deal/learn/", ["learn", "deal", "ch"]],
    ["d_terms", 1, "terms", "투자 교실 · 용어", "개", 130, 2.5, VS + "deal/learn/", ["learn", "deal", "box"]],
    ["d_hist", 1, "hist", "투자 교실 · 역사", "편", 111, 4, VS + "deal/learn/", ["learn", "deal", "ep"]],
    ["ty2", 1, "play", "타이쿤 · 나머지 업종 한 판씩 + 다시 하기", "판", 9, 45, LINK.tycoon, ["ty", 3]],
    ["iy2", 1, "story", "이야기 21~30편", "편", 10, 6, ST + "iyagi/", ["iyagi", 20]],
    ["g_course", 2, "course", "기초 교실 · 코스 (과학 14 · 심리 8 · 철학 9)", "장", 31, 15, VS + "gicho/", ["learn", "gicho", "ch"]],
    ["g_terms", 2, "terms", "기초 교실 · 용어", "개", 174, 2.5, VS + "gicho/", ["learn", "gicho", "box"]],
    ["g_hist", 2, "hist", "기초 교실 · 역사", "편", 98, 4, VS + "gicho/", ["learn", "gicho", "ep"]],
    ["br2", 2, "brain", "뇌 · 세부 부위", "개", 40, 5, ST + "brain/", ["brain", 2]],
    ["iy3", 2, "story", "이야기 31~50편", "편", 20, 6, ST + "iyagi/", ["iyagi", 30]],
    ["mental", 3, "play", "맨탈 · 수업 (고수 13명)", "개", 75, 10, MD + "mental/", ["mental"]],
    ["iy4", 3, "story", "이야기 51~100편", "편", 50, 6, ST + "iyagi/", ["iyagi", 50]],
    ["final", 3, "final", "졸업 시험 · 세 교실 수준 확인 다시 풀기", "곳", 3, 20, VS + "sisa/learn/", ["final"]]
  ].map(function (a) { return { id: a[0], term: a[1], kind: a[2], name: a[3], unit: a[4], total: a[5], min: a[6], url: a[7], src: a[8] }; });
  /* 통과 기준: 수준 확인은 12문제 중 10개(83%) 이상 */
  var EXIT = [
    [["diag", "sisa", "세상 읽기 수준 확인 10/12 이상"], ["full", "ty1", "타이쿤 3판 (같은 운으로 선택 하나만 바꿔 비교)"], ["full", "br1", "뇌 큰 부위 12개 외움"]],
    [["diag", "deal", "투자 교실 수준 확인 10/12 이상"], ["full", "ty2", "타이쿤 업종 전부 한 판씩"]],
    [["diag", "gicho", "기초 교실 수준 확인 10/12 이상"], ["full", "br2", "뇌 부위 52개 전부 외움"]],
    [["full", "mental", "맨탈 수업 75개"], ["full", "iy4", "이야기 100편"], ["full", "final", "세 교실 다시 풀어 모두 통과"]]
  ];
  var SLOT = { 1: ["course", "terms"], 2: ["play", "brain"], 3: ["terms", "course"], 4: ["play", "brain"], 5: ["hist", "terms"], 6: ["story", "hist"], 0: ["story", "hist"] };
  var DAYN = ["일", "월", "화", "수", "목", "금", "토"];

  function g(k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } }
  function n(o) { return o && typeof o === "object" ? Object.keys(o).filter(function (k) { return k.charAt(0) !== "_"; }).length : 0; }
  function pd(s) { var p = s.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function addDays(d, k) { var x = new Date(d.getTime()); x.setDate(x.getDate() + Math.round(k)); return x; }
  function iso(d) { return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function dd(a, b) { return Math.round((b.getTime() - a.getTime()) / 864e5); }
  function today() { var x = new Date(); return new Date(x.getFullYear(), x.getMonth(), x.getDate()); }
  function md(d) { return (d.getMonth() + 1) + "월 " + d.getDate() + "일"; }
  function fmt(d, y) { return (y ? d.getFullYear() + "년 " : "") + md(d) + "(" + DAYN[d.getDay()] + ")"; }
  function hrs(m) { var h = m / 60; return (h >= 10 ? Math.round(h) : Math.round(h * 10) / 10) + "시간"; }

  function state() { var s = g("vfm:univ", {}) || {}; s.set = s.set || {}; if (s.set.pace == null) s.set.pace = 1; if (!s.set.speed) s.set.speed = 100; s.ty = s.ty || 0; s.log = s.log || {}; return s; }
  function saveState(s) { try { localStorage.setItem("vfm:univ", JSON.stringify(s)); } catch (e) { } }
  function setOpt(k, v) { var s = state(); s.set[k] = v; s.set.at = Date.now(); saveState(s); }
  function addTy(d) { var s = state(); s.ty = Math.max(0, Math.min(12, s.ty + d)); saveState(s); }

  /* 기기 기록 읽기 → { 단위id: 끝낸 개수 }, 수준 확인 */
  function read() {
    var s = state(), raw = {}, diag = {};
    ["sisa", "deal", "gicho"].forEach(function (a) {
      raw[a + ":ch"] = n(g("vfm:learn:" + a + ":ch", {})); raw[a + ":box"] = n(g("vfm:learn:" + a + ":box", {})); raw[a + ":ep"] = n(g("vfm:learn:" + a + ":ep", {}));
      diag[a] = g("vfm:learn:" + a + ":diag", null);
    });
    var srs = g("vfm:brain:srs", {}) || {}, big = 0, small = 0;
    Object.keys(srs).forEach(function (k) { if ((srs[k] || {}).b >= 3) { if (BIG.indexOf(k) >= 0) big++; else small++; } });
    var lv = (g("iyagi-library-v1", {}) || {}).levels || {}, story = Object.keys(lv).filter(function (k) { return lv[k] > 0; }).length;
    var mental = n((g("vfm:mental:school", {}) || {}).done);
    var t4 = calcTerms(s)[3].from, pass = 0;
    ["sisa", "deal", "gicho"].forEach(function (a) { var x = diag[a]; if (x && x.n && x.c / x.n >= 0.83 && x.day && pd(x.day) >= t4) pass++; });
    var got = {};
    U.forEach(function (u) {
      var r = u.src, v = 0;
      if (r[0] === "learn") v = raw[r[1] + ":" + r[2]];
      else if (r[0] === "ty") v = s.ty - r[1];
      else if (r[0] === "brain") v = r[1] === 1 ? big : small;
      else if (r[0] === "iyagi") v = story - r[1];
      else if (r[0] === "mental") v = mental;
      else if (r[0] === "final") v = pass;
      got[u.id] = Math.max(0, Math.min(u.total, v || 0));
    });
    return { got: got, diag: diag, story: story, s: s };
  }
  function calcTerms(s) {
    var p = PACES[s.set.pace] || PACES[1], weekly = 5 * p.wd + 2 * p.we, sp = s.set.speed / 100, s0 = pd(START), cum = 0;
    return TERMS.map(function (t, i) {
      var min = U.filter(function (u) { return u.term === i; }).reduce(function (a, u) { return a + u.total * u.min * sp; }, 0);
      var from = addDays(s0, Math.ceil(cum / weekly) * 7); cum += min;
      var endW = Math.ceil(cum / weekly);
      return { min: min, from: from, to: addDays(s0, endW * 7 - 1), weeks: endW - Math.round(dd(s0, from) / 7), weekly: weekly, sp: sp, p: p };
    });
  }
  function calc() {
    var R = read(), s = R.s, T = calcTerms(s), now = today(), s0 = pd(START), sp = T[0].sp, tot = 0, done = 0;
    T.forEach(function (t) { t.done = 0; });
    U.forEach(function (u) { var m = u.total * u.min * sp, d = R.got[u.id] * u.min * sp; tot += m; done += d; T[u.term].done += d; });
    var end = T[3].to, days = dd(s0, end) + 1, el = dd(s0, now), planned = el < 0 ? 0 : Math.min(tot, (el + 1) / days * tot);
    var cur = 0; while (cur < 3 && T[cur].done >= T[cur].min - 1e-6) cur++;
    var fc = el >= 6 && done > 0 ? addDays(now, (tot - done) / (done / (el + 1))) : null;
    var weekly = T[0].weekly, gapD = Math.round((done - planned) / weekly * 7);
    var term = 0; T.forEach(function (t, i) { if (now >= t.from) term = i; });
    var week = el < 0 ? 0 : Math.floor(dd(T[term].from, now) / 7) + 1;
    // 그래프용 기록: 오늘 끝낸 분을 남김(합칠 때 큰 값이 이김)
    if (el >= 0) { var k = iso(now), r = Math.round(done); if ((s.log[k] || 0) !== r && r >= (s.log[k] || 0)) { s.log[k] = r; saveState(s); } }
    return { R: R, s: s, T: T, tot: tot, done: done, end: end, days: days, el: el, planned: planned, cur: cur, fc: fc, gapD: gapD, now: now, term: term, week: week, sp: sp, p: T[0].p, weekly: weekly };
  }
  /* 오늘 할 것: 요일마다 다른 종류(월·수 새 개념, 화·목 손으로, 금 역사, 주말 길게 읽기), 지금 학기에서 남은 것만 */
  function pick(C, day) {
    day = day || (C.el < 0 ? pd(START) : C.now);
    var wd = day.getDay(), budget = (wd === 0 || wd === 6) ? C.p.we : C.p.wd, kinds = SLOT[wd];
    var pool = U.filter(function (u) { return u.term === C.cur && C.R.got[u.id] < u.total; });
    if (!pool.length) return null;
    var u = null; kinds.forEach(function (k) { if (!u) u = pool.filter(function (x) { return x.kind === k; })[0]; }); if (!u) u = pool[0];
    var left = u.total - C.R.got[u.id], k = Math.max(1, Math.min(left, Math.floor(budget / (u.min * C.sp))));
    return { u: u, n: k, min: Math.round(k * u.min * C.sp), day: day };
  }
  function status(C) {
    if (C.el < 0) return ["wait", dd(C.now, pd(START)) + "일 뒤 시작"];
    if (C.gapD >= 0) return ["good", C.gapD > 0 ? C.gapD + "일 앞섬" : "계획대로"];
    return [C.gapD > -7 ? "warn" : "bad", -C.gapD + "일 밀림"];
  }
  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* 다른 화면에 붙이는 '오늘 수업' 카드. el 안을 채움 */
  var CARD_CSS = ".uv{display:block;background:var(--ap-surface,var(--card,#fff));color:var(--ap-label,var(--ink,inherit));border-radius:22px;padding:16px 18px;margin:0 0 14px;text-decoration:none;-webkit-tap-highlight-color:transparent}" +
    ".uv .k{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:13px;color:var(--ap-label2,var(--dim,#666));font-weight:600}" +
    ".uv .k b{color:var(--ap-label,var(--ink,inherit));font-variant-numeric:tabular-nums}" +
    ".uv .t{font:700 19px/1.35 var(--ap-display,inherit);letter-spacing:-.02em;margin:6px 0 2px;word-break:keep-all}" +
    ".uv .d{font-size:14px;color:var(--ap-label2,var(--dim,#666));margin:0;word-break:keep-all}" +
    ".uv .bar{height:6px;border-radius:99px;background:var(--ap-fill,var(--fill,rgba(120,120,128,.16)));overflow:hidden;margin:12px 0 0}.uv .bar i{display:block;height:100%;background:var(--ap-blue,var(--blue,#0a6cff));border-radius:99px}" +
    ".uv .pl{display:inline-block;font-size:12px;font-weight:700;padding:1px 8px;border-radius:99px;margin-left:6px}.uv .pl.good{background:rgba(52,199,89,.16);color:var(--ap-green-t,#1e8e3e)}.uv .pl.warn{background:rgba(255,149,0,.16);color:var(--ap-orange-t,#c26a00)}.uv .pl.bad{background:rgba(255,59,48,.14);color:var(--ap-red-t,#c4271c)}.uv .pl.wait{background:var(--ap-fill,#eee);color:var(--ap-label2,var(--dim,#666))}";
  function html() { var d = document.createElement("div"); try { card(d); } catch (e) { return ""; } return d.innerHTML; }
  function card(el) {
    if (!el) return;
    if (!document.getElementById("uv-css")) { var st = document.createElement("style"); st.id = "uv-css"; st.textContent = CARD_CSS; document.head.appendChild(st); }
    var C = calc(), t = pick(C), s = status(C), pc = Math.round(C.done / C.tot * 100);
    var head = C.el < 0 ? "univ. · " + fmt(pd(START)) + " 첫 수업" : "univ. · " + TERMS[C.term].n + " " + C.week + "주차";
    el.innerHTML = '<a class="uv" href="' + LINK.univ + '"><div class="k"><span>' + esc(head) + '<span class="pl ' + s[0] + '">' + s[1] + '</span></span><b>' + pc + "% · 졸업 " + (C.end.getMonth() + 1) + "/" + C.end.getDate() + "</b></div>" +
      (t ? '<p class="t">' + esc(t.u.name) + " " + t.n + t.u.unit + " · 약 " + t.min + "분</p>" : '<p class="t">전 과정을 끝냈어요</p>') +
      '<p class="d">누르면 오늘 할 것과 학기 진도가 열려요</p><div class="bar"><i style="width:' + Math.max(2, pc) + '%"></i></div></a>';
  }

  window.VFM_UNIV = { START: START, PACES: PACES, TERMS: TERMS, U: U, EXIT: EXIT, LINK: LINK, DAYN: DAYN, calc: calc, pick: pick, status: status, card: card, html: html, setOpt: setOpt, addTy: addTy,
    util: { pd: pd, iso: iso, dd: dd, md: md, fmt: fmt, hrs: hrs, addDays: addDays, esc: esc } };
})();
