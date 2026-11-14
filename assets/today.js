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
  css.textContent =
    ".tp{display:flex;flex-direction:column;gap:12px;margin:0 0 18px}" +
    ".tp-q{position:relative}.tp-q input{width:100%;border:0;border-radius:12px;padding:11px 14px 11px 38px;background:var(--ap-fill,rgba(120,120,128,.16));color:var(--ap-label);font:inherit;font-size:16px}" +
    ".tp-q svg{position:absolute;left:12px;top:50%;width:18px;height:18px;transform:translateY(-50%);color:var(--ap-label2)}" +
    ".tp-res{background:var(--ap-surface);border-radius:14px;overflow:hidden}.tp-res:empty{display:none}" +
    ".tp-res h5{margin:0;padding:10px 16px 4px;font-size:12px;color:var(--ap-label2);font-weight:600}" +
    ".tp-res a{display:block;padding:9px 16px;color:var(--ap-label);text-decoration:none;font-size:15px;line-height:1.4}.tp-res a small{display:block;color:var(--ap-label2);font-size:13px;margin-top:1px}" +
    ".tp-res .none{padding:12px 16px;color:var(--ap-label2);font-size:14px}" +
    ".tp-card{background:var(--ap-surface);border-radius:18px;padding:14px 16px}" +
    ".tp-k{font-size:12.5px;font-weight:700;color:var(--ap-blue);margin:0 0 6px;display:flex;justify-content:space-between;gap:8px}.tp-k small{color:var(--ap-label2);font-weight:500}" +
    ".tp-todo a{display:flex;align-items:center;gap:10px;padding:8px 0;color:var(--ap-label);text-decoration:none;font-size:16px}.tp-todo a+a{border-top:.5px solid var(--ap-sep)}" +
    ".tp-todo i{flex:none;width:22px;height:22px;border-radius:50%;box-shadow:inset 0 0 0 1.5px var(--ap-label3);display:grid;place-items:center;font-style:normal;font-size:13px;color:#fff}" +
    ".tp-todo a.ok i{background:var(--ap-green);box-shadow:none}.tp-todo a.ok span{color:var(--ap-label2);text-decoration:line-through}" +
    ".tp-todo small{margin-left:auto;color:var(--ap-label2);font-size:13px}" +
    ".tp-lead{margin:0 0 8px;font-size:15.5px;line-height:1.62}" +
    ".tp-li{display:block;padding:7px 0;color:var(--ap-label);text-decoration:none;font-size:15px;line-height:1.4;border-top:.5px solid var(--ap-sep)}.tp-li b{font-weight:600}" +
    ".tp-one{display:block;color:var(--ap-label);text-decoration:none;font-size:15.5px;line-height:1.55}.tp-one b{display:block;font-size:16.5px;margin-bottom:2px}";
  document.head.appendChild(css);

  var IC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>';
  box.className = "tp";
  box.innerHTML = '<div class="tp-q">' + IC + '<input id="tpq" type="search" placeholder="전체 검색 — 뉴스·딜·AI·낱말·이야기" autocomplete="off"></div><div class="tp-res" id="tpr"></div><div id="tpb"></div>';

  var D = { sb: null, db: null, li: null, dli: null, st: null };
  var done = g("vfm:home:done", {}); if (done.d !== today) done = { d: today };
  var learnDay = g("vfm:learn:sisa:day", {})[today], learnRd = g("vfm:learn:sisa:rd", {})[today];

  function paint() {
    var h = "";
    // ② 오늘 할 일
    var todo = [
      ["brief", "sisa/", "시사 브리핑 읽기", D.sb && D.sb.label ? D.sb.label.replace(/^\d+월 \d+일 /, "") : ""],
      ["deal", "deal/", "딜 브리핑 훑기", D.db && D.db.items ? D.db.items.length + "건" : ""],
      ["learn", "sisa/learn/", "오늘 배울 것", "", !!(learnDay && learnDay.ch + (learnDay.tm || 0) + learnDay.ep > 0)],
      ["rd", "sisa/learn/#yday", "어제 복습", "", !!learnRd],
      ["story", D.st ? STORY + "iyagi/#read-" + encodeURIComponent(D.st.id) : STORY + "iyagi/", "오늘의 이야기 한 편", ""]
    ];
    var nOk = todo.filter(function (t) { return t[4] || done[t[0]]; }).length;
    h += '<div class="tp-card tp-todo"><p class="tp-k">오늘 할 일<small>' + nOk + " / " + todo.length + "</small></p>" + todo.map(function (t) {
      var ok = t[4] || done[t[0]];
      return '<a href="' + e(t[1]) + '" data-td="' + t[0] + '" class="' + (ok ? "ok" : "") + '"><i>' + (ok ? "✓" : "") + "</i><span>" + e(t[2]) + "</span>" + (t[3] ? "<small>" + e(t[3]) + "</small>" : "") + "</a>";
    }).join("") + "</div>";
    // ③ 시사 브리핑
    if (D.sb && D.sb.items) {
      h += '<div class="tp-card"><p class="tp-k">' + e(D.sb.label || "시사 브리핑") + '<small><a href="sisa/" style="color:inherit">전체 ›</a></small></p>' +
        (D.sb.lead ? '<p class="tp-lead">' + e(D.sb.lead.split(/(?<=[.요다])\s/).slice(0, 2).join(" ")) + "</p>" : "") +
        D.sb.items.slice(0, 3).map(function (it) { var s = (it.sids || [])[0]; return '<a class="tp-li" href="sisa/' + (s ? "#issue-" + encodeURIComponent(s) : "") + '"><b>' + e(it.t) + "</b></a>"; }).join("") + "</div>";
    }
    // ④ 딜 한 줄
    if (D.db && D.db.items && D.db.items[0]) {
      var dt = D.db.items[0];
      h += '<div class="tp-card"><p class="tp-k">딜 한 줄<small>' + e(D.db.label || "") + '</small></p><a class="tp-one" href="deal/"><b>' + e(dt.t) + "</b>" + e(dt.one) + "</a></div>";
    }
    // ⑤ 오늘 배울 낱말 (날마다 바뀜)
    if (D.li && D.li.def) {
      var ids = Object.keys(D.li.def); if (ids.length) {
        var id = ids[hash(today) % ids.length];
        h += '<div class="tp-card"><p class="tp-k">오늘 배울 낱말<small>시사 배움</small></p><a class="tp-one" href="sisa/learn/#term=' + encodeURIComponent(id) + '"><b>' + e(D.li.term[id] || id) + "</b>" + e(D.li.def[id]) + "</a></div>";
      }
    }
    // ⑥ 오늘의 이야기
    if (D.st) h += '<div class="tp-card"><p class="tp-k">오늘의 이야기<small>' + e([D.st.kind, D.st.region].filter(Boolean).join(" · ")) + '</small></p><a class="tp-one" href="' + STORY + "iyagi/#read-" + encodeURIComponent(D.st.id) + '"><b>' + e(D.st.title) + "</b>" + e(String(D.st.hook || "").slice(0, 120)) + "…</a></div>";
    document.getElementById("tpb").innerHTML = '<div class="tp" style="margin:0">' + h + "</div>";
  }

  Promise.all([j("data/sisa/briefing/latest.json"), j("data/deal/briefing/latest.json"), j("data/sisa/learn_index.json")]).then(function (r) {
    D.sb = r[0]; D.db = r[1]; D.li = r[2]; paint();
    j(STORY + "data/iyagi/stories/_index.json").then(function (l) { if (Array.isArray(l) && l.length) { D.st = l[hash("s" + today) % l.length]; D.stAll = l; paint(); } });
  });
  paint();

  box.addEventListener("click", function (ev) {
    var a = ev.target.closest("[data-td]"); if (!a) return;
    done[a.getAttribute("data-td")] = 1; try { localStorage.setItem("vfm:home:done", JSON.stringify(done)); } catch (x) { }
  });

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
