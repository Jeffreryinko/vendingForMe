/* assets/today.js — 홈 맨 위 "오늘의 한 페이지"
 *  ① 전체 검색  ② 오늘 할 일(체크)  ③ 시사 브리핑 요약  ④ 딜 한 줄  ⑤ 오늘 배울 낱말  ⑥ 오늘의 이야기
 *  자료: data/sisa/briefing/latest.json · data/deal/briefing/latest.json · data/sisa/learn_index.json
 *        /vfm-story/data/iyagi/stories/_index.json (이야기 자판기)
 *  할 일 체크는 이 기기 localStorage(vfm:home:done) — 배움·복습은 배움 기록(vfm:learn:sisa:*)을 그대로 읽음.
 */
(function () {
  "use strict";
  var box = document.getElementById("tp"); if (!box) return;
  var STORY = "/vfm-story/";
  var kst = function (o) { return new Date(Date.now() + 9 * 3600e3 + (o || 0) * 864e5).toISOString().slice(0, 10); };
  var today = kst();
  var e = function (x) { return String(x == null ? "" : x).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var j = function (p) { return fetch(p, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); };
  var g = function (k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (x) { return d; } };
  var hash = function (s) { var h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); };

  var css = document.createElement("style");
  /* 조용한 잡지 지면처럼: 상자 대신 가는 줄과 여백, 강조색은 하나, 숫자는 고정 폭 */
  css.textContent =
    ".tp{display:flex;flex-direction:column;gap:0;margin:0 0 22px;font-variant-numeric:tabular-nums}" +
    ".tp-q{position:relative;margin:0 0 14px}.tp-q input{width:100%;border:0;border-radius:14px;padding:12px 14px 12px 40px;background:var(--ap-fill,rgba(120,120,128,.12));color:var(--ap-label);font:inherit;font-size:16px;outline:0;transition:box-shadow .2s,background .2s}" +
    ".tp-q input:focus{background:var(--ap-surface);box-shadow:0 0 0 1.5px var(--ap-label)}.tp-q svg{position:absolute;left:13px;top:50%;width:18px;height:18px;transform:translateY(-50%);color:var(--ap-label2)}" +
    ".tp-res{background:var(--ap-surface);border-radius:16px;overflow:hidden;margin:-4px 0 14px}.tp-res:empty{display:none}" +
    ".tp-res h5{margin:0;padding:12px 18px 2px;font-size:11.5px;letter-spacing:.06em;color:var(--ap-label2);font-weight:600}" +
    ".tp-res a{display:block;padding:9px 18px;color:var(--ap-label);text-decoration:none;font-size:15px;line-height:1.4}.tp-res a small{display:block;color:var(--ap-label2);font-size:13px;margin-top:1px}" +
    ".tp-hero{background:var(--ap-surface);border-radius:24px;padding:20px 20px 18px;margin:0 0 12px}" +
    ".tp-top{display:flex;align-items:center;gap:16px}.tp-ring{flex:none;position:relative;width:68px;height:68px}.tp-ring svg{width:68px;height:68px;transform:rotate(-90deg)}" +
    ".tp-ring circle{fill:none;stroke-width:6;stroke:var(--ap-fill,rgba(120,120,128,.14))}.tp-ring .p{stroke:var(--ap-label);stroke-linecap:round;transition:stroke-dashoffset .7s cubic-bezier(.2,.9,.3,1)}.tp-ring.all .p{stroke:var(--ap-green,#34C759)}" +
    ".tp-ring b{position:absolute;inset:0;display:flex;align-items:baseline;justify-content:center;padding-top:23px;font:700 19px/1 var(--ap-display,inherit);letter-spacing:-.02em}.tp-ring b small{font-size:12px;font-weight:500;color:var(--ap-label2);margin-left:1px}" +
    ".tp-say{min-width:0}.tp-say p{margin:0}.tp-say .h{font:700 20px/1.25 var(--ap-display,inherit);letter-spacing:-.025em}.tp-say .s{margin-top:5px;font-size:13px;color:var(--ap-label2);display:flex;flex-wrap:wrap;gap:4px 10px}" +
    ".tp-say .s b{color:var(--ap-label);font-weight:600}" +
    ".tp-go{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:16px 0 4px;padding:15px 18px;border-radius:16px;background:var(--ap-label);color:var(--ap-surface);text-decoration:none;font-size:16.5px;font-weight:650;letter-spacing:-.01em;transition:transform .15s}" +
    ".tp-go:active{transform:scale(.98)}.tp-go small{display:block;font-size:12px;font-weight:500;opacity:.62;margin-bottom:2px;letter-spacing:.02em}.tp-go i{font-style:normal;font-size:20px;opacity:.8}" +
    ".tp-go.fin{background:var(--ap-green,#34C759);color:#fff}" +
    ".tp-todo{margin-top:8px}.tp-todo a{display:flex;align-items:center;gap:12px;padding:11px 2px;color:var(--ap-label);text-decoration:none;font-size:15.5px;border-top:.5px solid var(--ap-sep,rgba(60,60,67,.18))}" +
    ".tp-todo i{flex:none;width:22px;height:22px;border-radius:50%;box-shadow:inset 0 0 0 1.5px var(--ap-label3,rgba(60,60,67,.3));display:grid;place-items:center;font-style:normal;font-size:12px;color:var(--ap-surface);transition:background .25s,box-shadow .25s,transform .35s cubic-bezier(.2,1.6,.4,1)}" +
    ".tp-todo a.ok i{background:var(--ap-label);box-shadow:none;transform:scale(1.06)}.tp-todo a.ok span{color:var(--ap-label2)}" +
    ".tp-todo small{margin-left:auto;color:var(--ap-label2);font-size:12.5px}" +
    ".tp-sec{padding:20px 4px 6px}.tp-k{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin:0 0 10px;font-size:11.5px;font-weight:600;letter-spacing:.08em;color:var(--ap-label2);text-transform:uppercase}" +
    ".tp-k a{color:var(--ap-label2);text-decoration:none;letter-spacing:0;text-transform:none;font-weight:500;font-size:13px}" +
    ".tp-lead{margin:0 0 12px;font:500 17.5px/1.6 var(--ap-display,inherit);letter-spacing:-.015em}" +
    ".tp-li{display:grid;grid-template-columns:26px 1fr;gap:4px;padding:11px 0;color:var(--ap-label);text-decoration:none;font-size:15.5px;line-height:1.42;border-top:.5px solid var(--ap-sep,rgba(60,60,67,.18))}" +
    ".tp-li em{font-style:normal;font-size:12px;font-weight:600;color:var(--ap-label2);padding-top:2px}.tp-li b{font-weight:600}" +
    ".tp-one{display:block;color:var(--ap-label);text-decoration:none;font-size:15px;line-height:1.6}.tp-one b{display:block;font:650 18px/1.35 var(--ap-display,inherit);letter-spacing:-.02em;margin-bottom:4px}.tp-one span{color:var(--ap-label2)}" +
    ".tp-rule{height:.5px;background:var(--ap-sep,rgba(60,60,67,.18));margin:14px 4px 0}";
  document.head.appendChild(css);

  var IC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>';
  box.className = "tp";
  box.innerHTML = '<div class="tp-q">' + IC + '<input id="tpq" type="search" placeholder="전체 검색 — 뉴스·딜·AI·낱말·이야기" autocomplete="off"></div><div class="tp-res" id="tpr"></div><div id="tpb"></div>';

  var D = { sb: null, db: null, li: null, dli: null, st: null };
  var done = g("vfm:home:done", {}); if (done.d !== today) done = { d: today };
  var learnDay = g("vfm:learn:sisa:day", {})[today], learnRd = g("vfm:learn:sisa:rd", {})[today];

  var first = true;
  function paint() {
    var h = "";
    var todo = [
      ["brief", "sisa/", "시사 브리핑 읽기", D.sb && D.sb.label ? D.sb.label.replace(/^\d+월 \d+일 /, "") : "", false, "5분"],
      ["deal", "deal/", "딜 브리핑 훑기", D.db && D.db.items ? D.db.items.length + "건" : "", false, "3분"],
      ["learn", "sisa/learn/", "오늘 배울 것", "", !!(learnDay && learnDay.ch + (learnDay.tm || 0) + learnDay.ep > 0), "5분"],
      ["rd", "sisa/learn/#yday", "어제 복습", "", !!learnRd, "2분"],
      ["story", D.st ? STORY + "iyagi/#read-" + encodeURIComponent(D.st.id) : STORY + "iyagi/", "오늘의 이야기 한 편", "", false, "5분"]
    ];
    var isOk = function (t) { return t[4] || done[t[0]]; };
    var nOk = todo.filter(isOk).length, nx = todo.filter(function (t) { return !isOk(t); })[0], N = todo.length;
    var C = 2 * Math.PI * 28, jt = (window.vfm && vfm.joyToday && vfm.joyToday()) || {}, stk = (window.vfm && vfm.joyStreak && vfm.joyStreak()) || 0;
    var say = nOk === 0 ? "하나만 먼저 해 볼까요" : nOk < N ? "좋아요, " + (N - nOk) + "개 남았어요" : "오늘 몫을 다 했어요";
    h += '<div class="tp-hero"><div class="tp-top"><div class="tp-ring' + (nOk === N ? " all" : "") + '"><svg viewBox="0 0 68 68"><circle cx="34" cy="34" r="28"/><circle class="p" cx="34" cy="34" r="28" stroke-dasharray="' + C.toFixed(1) + '" stroke-dashoffset="' + (first ? C : C * (1 - nOk / N)).toFixed(1) + '" data-off="' + (C * (1 - nOk / N)).toFixed(1) + '"/></svg><b>' + nOk + "<small>/" + N + "</small></b></div>" +
      '<div class="tp-say"><p class="h">' + say + '</p><p class="s">' + (stk ? "<span><b>" + stk + "일</b> 연속</span>" : "") + (jt.card ? "<span>카드 <b>" + jt.card + "</b></span>" : "") + (jt.quiz ? "<span>문제 <b>" + jt.quiz + "</b></span>" : "") + (!stk && !jt.card && !jt.quiz ? "<span>오늘 첫 걸음을 기다려요</span>" : "") + "</p></div></div>" +
      (nx ? '<a class="tp-go" href="' + e(nx[1]) + '" data-td="' + nx[0] + '"><span><small>지금 할 것 · ' + nx[5] + "</small>" + e(nx[2]) + "</span><i>→</i></a>" : '<a class="tp-go fin" href="#mixcap"><span><small>다 했어요</small>랜덤 카드로 놀기</span><i>↓</i></a>') +
      '<div class="tp-todo">' + todo.map(function (t) {
        var ok = isOk(t);
        return '<a href="' + e(t[1]) + '" data-td="' + t[0] + '" class="' + (ok ? "ok" : "") + '"><i>' + (ok ? "✓" : "") + "</i><span>" + e(t[2]) + "</span>" + (t[3] ? "<small>" + e(t[3]) + "</small>" : "") + "</a>";
      }).join("") + "</div></div>";
    if (D.sb && D.sb.items) {
      h += '<div class="tp-sec"><p class="tp-k"><span>' + e(D.sb.label || "시사 브리핑") + '</span><a href="sisa/">전체 ›</a></p>' +
        (D.sb.lead ? '<p class="tp-lead">' + e(D.sb.lead.split(/(?<=[.요다])\s/).slice(0, 2).join(" ")) + "</p>" : "") +
        D.sb.items.slice(0, 3).map(function (it, i) { var s = (it.sids || [])[0]; return '<a class="tp-li" href="sisa/' + (s ? "#issue-" + encodeURIComponent(s) : "") + '"><em>0' + (i + 1) + "</em><b>" + e(it.t) + "</b></a>"; }).join("") + "</div>";
    }
    if (D.db && D.db.items && D.db.items[0]) {
      var dt = D.db.items[0];
      h += '<div class="tp-rule"></div><div class="tp-sec"><p class="tp-k"><span>딜 한 줄</span><a href="deal/">전체 ›</a></p><a class="tp-one" href="deal/"><b>' + e(dt.t) + "</b><span>" + e(dt.one) + "</span></a></div>";
    }
    if (D.li && D.li.def) {
      var ids = Object.keys(D.li.def); if (ids.length) {
        var id = ids[hash(today) % ids.length];
        h += '<div class="tp-rule"></div><div class="tp-sec"><p class="tp-k"><span>오늘의 낱말</span><a href="sisa/learn/#terms">사전 ›</a></p><a class="tp-one" href="sisa/learn/#term=' + encodeURIComponent(id) + '"><b>' + e(D.li.term[id] || id) + "</b><span>" + e(D.li.def[id]) + "</span></a></div>";
      }
    }
    if (D.st) h += '<div class="tp-rule"></div><div class="tp-sec"><p class="tp-k"><span>오늘의 이야기</span><span>' + e([D.st.kind, D.st.region].filter(Boolean).join(" · ")) + '</span></p><a class="tp-one" href="' + STORY + "iyagi/#read-" + encodeURIComponent(D.st.id) + '"><b>' + e(D.st.title) + "</b><span>" + e(String(D.st.hook || "").slice(0, 120)) + "…</span></a></div>";
    document.getElementById("tpb").innerHTML = '<div class="tp" style="margin:0">' + h + "</div>";
    var ring = box.querySelector(".tp-ring .p"); if (ring && first) requestAnimationFrame(function () { requestAnimationFrame(function () { ring.style.strokeDashoffset = ring.getAttribute("data-off"); }); });
    first = false;
  }

  Promise.all([j("data/sisa/briefing/latest.json"), j("data/deal/briefing/latest.json"), j("data/sisa/learn_index.json")]).then(function (r) {
    D.sb = r[0]; D.db = r[1]; D.li = r[2]; paint();
    j(STORY + "data/iyagi/stories/_index.json").then(function (l) { if (Array.isArray(l) && l.length) { D.st = l[hash("s" + today) % l.length]; D.stAll = l; paint(); } });
  });
  paint();

  box.addEventListener("click", function (ev) {
    var a = ev.target.closest("[data-td]"); if (!a) return;
    var k = a.getAttribute("data-td"); if (done[k]) return;
    done[k] = 1; try { localStorage.setItem("vfm:home:done", JSON.stringify(done)); } catch (x) { }
    try { vfm.tick("done", true); } catch (x) { }
  });
  window.addEventListener("pageshow", function () { paint(); });   // 다른 화면에서 돌아오면 체크·숫자 새로

  /* ① 전체 검색 — 들고 있는 자료(브리핑 두 개·배움 목록 두 개·이야기 목록)에서 찾고, 딜·시사는 그 앱으로 넘김 */
  var q = document.getElementById("tpq"), res = document.getElementById("tpr"), t0;
  q.addEventListener("focus", function () { if (!D.dli) j("data/deal/learn_index.json").then(function (x) { D.dli = x || {}; }); if (!D.ali) j("data/ai/learn_index.json").then(function (x) { D.ali = x || {}; }); }, { once: true });
  q.addEventListener("input", function () { clearTimeout(t0); t0 = setTimeout(search, 160); });
  function hit(s, w) { s = String(s || "").toLowerCase(); return w.every(function (x) { return s.indexOf(x) >= 0; }); }
  function search() {
    var v = q.value.trim(); if (!v) { res.innerHTML = ""; return; }
    var w = v.toLowerCase().split(/\s+/).filter(Boolean), G = [];
    var add = function (name, list) { if (list.length) G.push("<h5>" + name + "</h5>" + list.slice(0, 5).join("")); };
    var row = function (href, t, s) { return '<a href="' + e(href) + '">' + e(t) + (s ? "<small>" + e(String(s).slice(0, 90)) + "</small>" : "") + "</a>"; };
    add("시사 브리핑", ((D.sb && D.sb.items) || []).filter(function (it) { return hit([it.t, it.one, it.sum, it.why].join(" "), w); })
      .map(function (it) { var s = (it.sids || [])[0]; return row("sisa/" + (s ? "#issue-" + encodeURIComponent(s) : ""), it.t, it.one); }));
    add("딜 브리핑", ((D.db && D.db.items) || []).filter(function (it) { return hit([it.t, it.one, it.buyer, it.target, it.why].join(" "), w); })
      .map(function (it) { return row("deal/", it.t, it.one); }));
    var learn = function (li, base, label) {
      var out = []; if (!li) return out;
      var K = { term: ["낱말", "#term="], hist: ["역사", "#hist="], ch: ["코스", "#ch="] };
      Object.keys(K).forEach(function (k) { var m = li[k] || {}; Object.keys(m).forEach(function (id) { if (hit(m[id] + " " + ((k === "term" && li.def && li.def[id]) || ""), w)) out.push(row(base + K[k][1] + encodeURIComponent(id), K[k][0] + " · " + m[id], k === "term" && li.def ? li.def[id] : label)); }); });
      return out;
    };
    add("시사 배움", learn(D.li, "sisa/learn/", "시사 배움"));
    add("딜 배움", learn(D.dli, "deal/learn/", "투자 교실"));
    add("AI 배움", learn(D.ali, "ai/learn/", "AI 교실"));
    add("이야기", (D.stAll || []).filter(function (s) { return hit([s.title, s.orig, s.hook, (s.tags || []).join(" "), s.region].join(" "), w); })
      .map(function (s) { return row(STORY + "iyagi/#read-" + encodeURIComponent(s.id), s.title, s.hook); }));
    G.push("<h5>다른 곳에서 더 찾기</h5>" + row("deal/#name=" + encodeURIComponent(v), "딜에서 '" + v + "' 거래 모아 보기", "최근 90일 투자·인수합병") +
      row("https://news.google.com/search?q=" + encodeURIComponent(v) + "&hl=ko&gl=KR&ceid=KR:ko", "구글 뉴스에서 '" + v + "' ↗", ""));
    res.innerHTML = G.join("");
  }
})();
