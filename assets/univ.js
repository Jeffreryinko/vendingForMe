/* univ.js — 'univ.': 내가 만든 자판기·띵크폴미·타이쿤을 4학기 과정으로 끝까지 익히는 일정표의 계산 부분.
   진도는 각 앱이 이 기기에 이미 남기는 기록을 읽어서 저절로 세요(로봇·토큰 0). 타이쿤만 주소가 달라 판 수를 직접 눌러요.
     세 교실   vfm:learn:<sisa|deal|gicho>:ch(끝낸 장 {day,q}) · box(외우기 상자 {b,due}) · ep(읽은 역사 → 날짜) · day(날마다 {ch,tm,ep}) · diag(수준 확인 {c,n,day})
     뇌        vfm:brain:srs  {부위: {b,ok,ng}}  — b 3 이상 = 외움 (뇌 화면의 '외운 부위'와 같은 기준)
     이야기    iyagi-library-v1 .levels {이야기: 읽은 깊이} — 1 이상 = 읽음
     맨탈      vfm:mental:school .done {수업: 날짜}
     띵크폴미  tfm:cache (생각·연 날·회고 — 분석 화면의 숫자에만 씀)
     이 화면   vfm:univ = { set:{pace,speed}, plays:[타이쿤 끝낸 날…], base:{첫날 개수}, snap:{날짜:{과목:개수}}, log:{날짜: 끝낸 분} }
   전체 개수(TOT)는 robot/univ_catalog.py 가 세 교실의 글 파일을 실제로 읽어 세고 이 파일의 TOT 줄과 univ/catalog.json 을 고쳐 써요.
   구글로 로그인하면 sync.js 가 vfm:* 와 iyagi-library-v1 을 기기끼리 맞춰요(그래서 폰·PC 진도가 같음).
   쓰는 곳: univ/index.html(전체 화면·분석), 자판기 첫 화면·띵크폴미 홈의 '오늘 수업' 카드(VFM_UNIV.card·html). */
(function () {
  "use strict";
  var TOT = {"sisa":{"ch":36,"chMin":10.4,"tm":214,"ep":250},"deal":{"ch":18,"chMin":8.7,"tm":287,"ep":133},"gicho":{"ch":31,"chMin":12.8,"tm":174,"ep":98}}; /*@totals*/
  var START = "2026-11-16";
  var PACES = [{ n: "가볍게", wd: 20, we: 40 }, { n: "기본", wd: 30, we: 60 }, { n: "집중", wd: 45, we: 90 }, { n: "몰입", wd: 60, we: 120 }];
  var O = location.origin, VS = O + "/vendingForMe/", ST = O + "/vfm-story/", MD = O + "/vfm-mind/";
  var LINK = { tycoon: "https://tycoon-prototype.vercel.app/", think: O + "/thinkingForMe/", univ: VS + "univ/", story: ST, mind: MD, vs: VS };
  var ROOM = { sisa: ["세상 읽기 교실", VS + "sisa/learn/"], deal: ["투자 교실", VS + "deal/learn/"], gicho: ["기초 교실", VS + "gicho/"] };
  var TERMS = [
    { n: "1학기", t: "세상 읽는 눈", goal: "뉴스를 용어 찾지 않고 읽고, 타이쿤으로 가게 하나가 굴러가는 원리를 몸에 붙여요." },
    { n: "2학기", t: "돈과 사업", goal: "투자·인수 기사를 읽고, 운동시설 업종마다 돈 버는 구조가 어떻게 다른지 말할 수 있어요." },
    { n: "3학기", t: "교양의 뼈대", goal: "과학·심리학·철학의 큰 줄기를 이야기 순서로 꿰어요." },
    { n: "4학기", t: "사람과 이야기", goal: "사람을 읽는 기술과, 대화에서 비유로 통하는 이야기 100편을 갖춰요." }
  ];
  var BIG = ["frontal", "parietal", "temporal", "occipital", "hippocampus", "amygdala", "thalamus", "hypothalamus", "cerebellum", "midbrain", "pons", "medulla"];
  function room(a, term) {
    var t = TOT[a], nm = ROOM[a][0], url = ROOM[a][1];
    return [[a.charAt(0) + "_course", term, "course", nm + " · 코스", "장", t.ch, t.chMin, url, ["learn", a, "ch"]],
      [a.charAt(0) + "_terms", term, "terms", nm + " · 용어", "개", t.tm, 2.5, url, ["learn", a, "box"]],
      [a.charAt(0) + "_hist", term, "hist", nm + " · 역사", "편", t.ep, 4, url, ["learn", a, "ep"]]];
  }
  /* id, 학기, 종류, 이름, 단위, 전체, 하나에 드는 분(추정), 주소, 읽는 법 */
  var U = [].concat(
    room("sisa", 0), [["ty1", 0, "play", "타이쿤 · 헬스장 첫 판, 같은 운 다시, 다른 상권", "판", 3, 45, LINK.tycoon, ["ty", 0]],
      ["br1", 0, "brain", "뇌 · 큰 부위", "개", 12, 5, ST + "brain/", ["brain", 1]], ["iy1", 0, "story", "이야기 1~20편", "편", 20, 6, ST + "iyagi/", ["iyagi", 0]]],
    room("deal", 1), [["ty2", 1, "play", "타이쿤 · 나머지 업종 한 판씩 + 다시 하기", "판", 9, 45, LINK.tycoon, ["ty", 3]], ["iy2", 1, "story", "이야기 21~30편", "편", 10, 6, ST + "iyagi/", ["iyagi", 20]]],
    room("gicho", 2), [["br2", 2, "brain", "뇌 · 세부 부위", "개", 40, 5, ST + "brain/", ["brain", 2]], ["iy3", 2, "story", "이야기 31~50편", "편", 20, 6, ST + "iyagi/", ["iyagi", 30]]],
    [["mental", 3, "play", "맨탈 · 수업 (고수 13명)", "개", 75, 10, MD + "mental/", ["mental"]], ["iy4", 3, "story", "이야기 51~100편", "편", 50, 6, ST + "iyagi/", ["iyagi", 50]],
      ["final", 3, "final", "졸업 시험 · 세 교실 수준 확인 다시 풀기", "곳", 3, 20, VS + "sisa/learn/", ["final"]]]
  ).map(function (a) { return { id: a[0], term: a[1], kind: a[2], name: a[3], unit: a[4], total: a[5], min: a[6], url: a[7], src: a[8] }; });
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
  function keys(o) { return o && typeof o === "object" ? Object.keys(o).filter(function (k) { return k.charAt(0) !== "_"; }) : []; }
  function pd(s) { var p = String(s).split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function addDays(d, k) { var x = new Date(d.getTime()); x.setDate(x.getDate() + Math.round(k)); return x; }
  function iso(d) { return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
  function dd(a, b) { return Math.round((b.getTime() - a.getTime()) / 864e5); }
  function today() { var x = new Date(); return new Date(x.getFullYear(), x.getMonth(), x.getDate()); }
  function md(d) { return (d.getMonth() + 1) + "월 " + d.getDate() + "일"; }
  function fmt(d, y) { return (y ? d.getFullYear() + "년 " : "") + md(d) + "(" + DAYN[d.getDay()] + ")"; }
  function hrs(m) { var h = m / 60; return (h >= 10 ? Math.round(h) : Math.round(h * 10) / 10) + "시간"; }
  function dayStr(v) { return typeof v === "number" ? new Date(v * 864e5).toISOString().slice(0, 10) : (typeof v === "string" ? v.slice(0, 10) : ""); }   // 날짜가 숫자(날 번호)로 적힌 기록도 읽음

  function state() {
    var s = g("vfm:univ", {}) || {}; s.set = s.set || {}; if (s.set.pace == null) s.set.pace = 1; if (!s.set.speed) s.set.speed = 100;
    s.log = s.log || {}; s.snap = s.snap || {};
    if (!s.plays) { s.plays = []; for (var i = 0; i < (s.ty || 0); i++) s.plays.push(iso(today())); }   // 예전 기록(판 수만)에서 옮김
    return s;
  }
  function saveState(s) { s.ty = s.plays.length; try { localStorage.setItem("vfm:univ", JSON.stringify(s)); } catch (e) { } }
  function setOpt(k, v) { var s = state(); s.set[k] = v; s.set.at = Date.now(); saveState(s); }
  function addTy(d) { var s = state(); if (d > 0) { if (s.plays.length < 12) s.plays.push(iso(today())); } else s.plays.pop(); saveState(s); }

  /* 기기 기록 읽기 → { 단위id: 끝낸 개수 } + 분석용 원본 */
  function read() {
    var s = state(), rec = { learn: {} }, diag = {};
    ["sisa", "deal", "gicho"].forEach(function (a) {
      var r = rec.learn[a] = {}; ["ch", "box", "ep", "day", "rd"].forEach(function (k) { r[k] = g("vfm:learn:" + a + ":" + k, {}) || {}; });
      diag[a] = r.diag = g("vfm:learn:" + a + ":diag", null);
    });
    var srs = rec.srs = g("vfm:brain:srs", {}) || {}, big = 0, small = 0;
    Object.keys(srs).forEach(function (k) { if ((srs[k] || {}).b >= 3) { if (BIG.indexOf(k) >= 0) big++; else small++; } });
    var lv = rec.levels = (g("iyagi-library-v1", {}) || {}).levels || {}, story = Object.keys(lv).filter(function (k) { return lv[k] > 0; }).length;
    var mdone = rec.mental = (g("vfm:mental:school", {}) || {}).done || {}, mental = keys(mdone).length;
    var t4 = calcTerms(s)[3].from, pass = 0;
    ["sisa", "deal", "gicho"].forEach(function (a) { var x = diag[a]; if (x && x.n && x.c / x.n >= 0.83 && x.day && pd(x.day) >= t4) pass++; });
    var got = {};
    U.forEach(function (u) {
      var r = u.src, v = 0;
      if (r[0] === "learn") v = keys(rec.learn[r[1]][r[2]]).length;
      else if (r[0] === "ty") v = s.plays.length - r[1];
      else if (r[0] === "brain") v = r[1] === 1 ? big : small;
      else if (r[0] === "iyagi") v = story - r[1];
      else if (r[0] === "mental") v = mental;
      else if (r[0] === "final") v = pass;
      got[u.id] = Math.max(0, Math.min(u.total, v || 0));
    });
    return { got: got, diag: diag, story: story, s: s, rec: rec };
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
    var R = read(), s = R.s, T = calcTerms(s), now = today(), s0 = pd(START), sp = T[0].sp, tot = 0, done = 0, nU = 0, nD = 0;
    T.forEach(function (t) { t.done = 0; });
    U.forEach(function (u) { var m = u.total * u.min * sp, d = R.got[u.id] * u.min * sp; tot += m; done += d; T[u.term].done += d; nU += u.total; nD += R.got[u.id]; });
    var end = T[3].to, days = dd(s0, end) + 1, el = dd(s0, now), planned = el < 0 ? 0 : Math.min(tot, (el + 1) / days * tot);
    var cur = 0; while (cur < 3 && T[cur].done >= T[cur].min - 1e-6) cur++;
    var fc = el >= 6 && done > 0 ? addDays(now, (tot - done) / (done / (el + 1))) : null;
    var weekly = T[0].weekly, gapD = Math.round((done - planned) / weekly * 7);
    var term = 0; T.forEach(function (t, i) { if (now >= t.from) term = i; });
    var week = el < 0 ? 0 : Math.floor(dd(T[term].from, now) / 7) + 1;
    // 날마다 개수를 한 장씩 찍어 둠(분석의 '하루에 얼마나'가 여기서 나옴). 첫날 개수는 base 로 따로.
    var k = iso(now), cg = JSON.stringify(R.got), ch = false;
    if (!s.base) { s.base = R.got; ch = true; }
    if (JSON.stringify(s.snap[k] || null) !== cg) { s.snap[k] = R.got; ch = true; }
    var r = Math.round(done); if (el >= 0 && (s.log[k] || 0) < r) { s.log[k] = r; ch = true; }
    var sk = Object.keys(s.snap).sort(); if (sk.length > 120) { sk.slice(0, sk.length - 120).forEach(function (x) { delete s.snap[x]; }); ch = true; }
    if (ch) saveState(s);
    return { R: R, s: s, T: T, tot: tot, done: done, nU: nU, nD: nD, end: end, days: days, el: el, planned: planned, cur: cur, fc: fc, gapD: gapD, now: now, term: term, week: week, sp: sp, p: T[0].p, weekly: weekly };
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
  /* 날짜별로 과목마다 몇 개 했는지. 날짜가 적힌 기록(끝낸 장·읽은 역사·맨탈 수업·타이쿤)은 그대로, 나머지(용어·뇌·이야기)는 날마다 찍어 둔 개수의 차이로 */
  function daily(C) {
    var out = {}, rec = C.R.rec, s = C.s;
    function add(d, id, n) { if (!d || !n) return; (out[d] = out[d] || {})[id] = ((out[d] || {})[id] || 0) + n; }
    U.forEach(function (u) {
      var r = u.src;
      if (r[0] === "learn" && r[2] === "ch") keys(rec.learn[r[1]].ch).forEach(function (k) { add(dayStr((rec.learn[r[1]].ch[k] || {}).day), u.id, 1); });
      else if (r[0] === "learn" && r[2] === "ep") keys(rec.learn[r[1]].ep).forEach(function (k) { add(dayStr(rec.learn[r[1]].ep[k]), u.id, 1); });
      else if (r[0] === "mental") keys(rec.mental).forEach(function (k) { add(dayStr(rec.mental[k]), u.id, 1); });
      else if (r[0] === "ty") s.plays.forEach(function (d, i) { if (i >= r[1] && i < r[1] + u.total) add(d, u.id, 1); });
      else { var prev = (s.base || {})[u.id] || 0; Object.keys(s.snap).sort().forEach(function (d) { var v = (s.snap[d] || {})[u.id] || 0; if (v > prev) { add(d, u.id, v - prev); prev = v; } }); }
    });
    return out;
  }
  function dayMin(D, d, sp) { var o = D[d] || {}, m = 0; U.forEach(function (u) { if (o[u.id]) m += o[u.id] * u.min * sp; }); return m; }
  function stats(C) {
    var D = daily(C), now = C.now, s0 = pd(START), ser = [], i, d, m;
    for (i = 13; i >= 0; i--) { d = addDays(now, -i); m = dayMin(D, iso(d), C.sp); ser.push({ d: d, min: m, pre: d < s0 }); }
    var m7 = 0, act7 = 0; ser.slice(7).forEach(function (x) { m7 += x.min; if (x.min > 0) act7++; });
    var streak = 0; for (i = 0; i < 400; i++) { m = dayMin(D, iso(addDays(now, -i)), C.sp); if (m > 0) streak++; else if (i) break; }
    var el = Math.max(0, C.el + 1), act = 0, byDow = [0, 0, 0, 0, 0, 0, 0], nDow = [0, 0, 0, 0, 0, 0, 0], best = null;
    for (i = 0; i < el; i++) { d = addDays(s0, i); m = dayMin(D, iso(d), C.sp); if (m > 0) act++; byDow[d.getDay()] += m; nDow[d.getDay()]++; if (m > 0 && (!best || m > best.min)) best = { d: d, min: m }; }
    var left = C.tot - C.done, daysLeft = Math.max(1, dd(now, C.end) + 1), u7 = {};
    U.forEach(function (u) { var c = 0; for (var j = 0; j < 7; j++) c += ((D[iso(addDays(now, -j))] || {})[u.id] || 0); u7[u.id] = c; });
    var span = Math.max(1, Math.min(7, el));
    return { D: D, ser: ser, m7: m7, avg7: m7 / span, act7: act7, streak: streak, act: act, el: el, byDow: byDow.map(function (v, k) { return nDow[k] ? v / nDow[k] : 0; }), best: best, left: left, daysLeft: daysLeft, need: left / daysLeft, u7: u7, span: span };
  }
  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* 다른 화면에 붙이는 '오늘 수업' 카드. el 안을 채움 */
  var CARD_CSS = ".uv{display:block;background:var(--ap-surface,var(--card,#fff));color:var(--ap-label,var(--ink,inherit));border-radius:22px;padding:16px 18px;margin:0 0 14px;text-decoration:none;-webkit-tap-highlight-color:transparent}" +
    ".uv .k{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:13px;color:var(--ap-label2,var(--dim,#666));font-weight:600}" +
    ".uv .k b{color:var(--ap-label,var(--ink,inherit));font-variant-numeric:tabular-nums;white-space:nowrap}" +
    ".uv .t{font:700 19px/1.35 var(--ap-display,inherit);letter-spacing:-.02em;margin:6px 0 2px;word-break:keep-all}" +
    ".uv .d{font-size:14px;color:var(--ap-label2,var(--dim,#666));margin:0;word-break:keep-all;font-variant-numeric:tabular-nums}" +
    ".uv .bar{height:6px;border-radius:99px;background:var(--ap-fill,var(--fill,rgba(120,120,128,.16)));overflow:hidden;margin:12px 0 0}.uv .bar i{display:block;height:100%;background:var(--ap-blue,var(--blue,#0a6cff));border-radius:99px}" +
    ".uv .pl{display:inline-block;font-size:12px;font-weight:700;padding:1px 8px;border-radius:99px;margin-left:6px}.uv .pl.good{background:rgba(52,199,89,.16);color:var(--ap-green-t,#1e8e3e)}.uv .pl.warn{background:rgba(255,149,0,.16);color:var(--ap-orange-t,#c26a00)}.uv .pl.bad{background:rgba(255,59,48,.14);color:var(--ap-red-t,#c4271c)}.uv .pl.wait{background:var(--ap-fill,#eee);color:var(--ap-label2,#666)}";
  function html() { var d = document.createElement("div"); try { card(d); } catch (e) { return ""; } return d.innerHTML; }
  function card(el) {
    if (!el) return;
    if (!document.getElementById("uv-css")) { var st = document.createElement("style"); st.id = "uv-css"; st.textContent = CARD_CSS; document.head.appendChild(st); }
    var C = calc(), t = pick(C), s = status(C), pc = Math.round(C.done / C.tot * 1000) / 10, S = stats(C);
    var head = C.el < 0 ? "univ. · " + fmt(pd(START)) + " 첫 수업" : "univ. · " + TERMS[C.term].n + " " + C.week + "주차";
    el.innerHTML = '<a class="uv" href="' + LINK.univ + '"><div class="k"><span>' + esc(head) + '<span class="pl ' + s[0] + '">' + s[1] + '</span></span><b>' + pc + "% · 졸업 " + (C.end.getMonth() + 1) + "/" + C.end.getDate() + "</b></div>" +
      (t ? '<p class="t">' + esc(t.u.name) + " " + t.n + t.u.unit + " · 약 " + t.min + "분</p>" : '<p class="t">전 과정을 끝냈어요</p>') +
      '<p class="d">' + C.nD.toLocaleString() + " / " + C.nU.toLocaleString() + "개 · 남은 " + hrs(C.tot - C.done) + " · 최근 7일 하루 " + Math.round(S.avg7) + "분 (필요 " + Math.round(S.need) + '분)</p><div class="bar"><i style="width:' + Math.max(2, pc) + '%"></i></div></a>';
  }

  window.VFM_UNIV = { START: START, PACES: PACES, TERMS: TERMS, U: U, EXIT: EXIT, LINK: LINK, ROOM: ROOM, DAYN: DAYN, BIG: BIG, TOT: TOT, calc: calc, pick: pick, status: status, stats: stats, card: card, html: html, setOpt: setOpt, addTy: addTy,
    util: { pd: pd, iso: iso, dd: dd, md: md, fmt: fmt, hrs: hrs, addDays: addDays, esc: esc, keys: keys, dayStr: dayStr, g: g } };
})();
