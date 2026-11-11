/* 배움 엔진 — 딜 '투자 교실', 시사 '배경지식'이 같이 써요. 글·그림은 각 앱의 learn/ 폴더(terms.js · course.js · history.js · figs.js).
   하루 몫(코스 1장 + 용어 + 역사)을 정해 주고 '이어서 하기' 한 버튼으로 끌고 가요. 기록은 이 기기에만(localStorage). 로봇·토큰 0. */
(function () {
  "use strict";
  const L = window.VFM_LEARN || {}, TERMS = window.VFM_TERMS || [], CATS = window.VFM_TERM_CATS || [], FIG = window.VFM_FIGS || {};
  const ART = window.VFM_ART || { face: () => "", comic: () => "", termComic: null, relMap: () => "", strip: () => "", pic: () => "" };
  const APP = L.app || "deal", app = document.getElementById("app"), tabs = document.getElementById("tabs");
  const TB = Object.fromEntries(TERMS.map(t => [t.id, t])), CH = L.chapters || [], HS = L.history || [], DG = L.diag || [];
  const LS = { g(k, d) { try { const v = localStorage.getItem("vfm:learn:" + APP + ":" + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, s(k, v) { try { localStorage.setItem("vfm:learn:" + APP + ":" + k, JSON.stringify(v)); } catch (e) { } } };
  const S = { diag: LS.g("diag", null), ch: LS.g("ch", {}), box: LS.g("box", {}), ep: LS.g("ep", {}), day: LS.g("day", {}), size: LS.g("size", "normal") };
  const save = k => LS.s(k, S[k]);
  /* 역사 읽음 표시는 자리 번호가 아니라 '지역|제목'으로 기억해요 (사건이 늘어도 안 밀림). 묶음 보기(virt)는 같은 사건을 가리켜요 */
  HS.forEach(h => { if (!h.virt) h.items.forEach(e => { if (!e._k) { e._k = h.id + "|" + e.t; e._f = h.flag; } }); });
  if (!S.ep._v) { const o = S.ep, n = { _v: 2 }; for (const k in o) { const m = k.match(/^(.+):(\d+)$/), h = m && HS.find(x => x.id === m[1]), e = h && h.items[+m[2]]; if (e) n[e._k] = o[k]; } S.ep = n; LS.s("ep", n); }
  const epKey = k => { const [r, i] = String(k).split(":"), h = HS.find(x => x.id === r), e = h && h.items[+i]; return e ? e._k : k; };
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const fmt = s => "<p>" + esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "</p><p>") + "</p>";
  const kst = (off = 0) => new Date(Date.now() + 9 * 3600e3 + off * 864e5).toISOString().slice(0, 10);
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const toast = m => { const t = document.createElement("div"); t.className = "toast"; t.textContent = m; document.body.appendChild(t); setTimeout(() => t.remove(), 1800); };

  const css = `
.fg{width:100%;height:auto;display:block;font-family:inherit;margin:10px 0 2px}
.lc{background:var(--surface);border-radius:var(--r);padding:16px 16px 14px;margin:0 0 10px}.lc h3{margin:0 0 8px;font:700 19px/1.35 var(--ap-display);letter-spacing:-.02em}.lc p{margin:0 0 9px;font-size:calc(15px*var(--fs))}.lc p:last-child{margin-bottom:0}.lc b{color:var(--accent)}
.ring{display:flex;gap:16px;align-items:center;background:var(--surface);border-radius:var(--r);padding:16px;margin:8px 0}.ring svg{flex:none}.ring .tx{flex:1;min-width:0}.ring .tx b{font:800 20px var(--ap-display);display:block;letter-spacing:-.02em}.ring .tx small{color:var(--muted);font-size:13px}
.step{display:flex;gap:10px;align-items:center;width:100%;text-align:left;border:0;background:none;padding:11px 0;border-bottom:.5px solid var(--ap-sep);color:inherit}.step:last-child{border-bottom:0}
.step i{flex:none;width:24px;height:24px;border-radius:50%;border:2px solid var(--ap-label3);display:grid;place-items:center;font-style:normal;font-size:13px;color:#fff}.step.ok i{background:var(--up);border-color:var(--up)}.step.now i{border-color:var(--accent)}
.step .bx{flex:1;min-width:0}.step .t{font-weight:650;margin:0}.step .s{font-size:12.5px;color:var(--muted);margin:0}.step .v{color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}
.go{width:100%;font-size:17px;padding:14px;margin:4px 0 6px}
.dots{display:flex;gap:4px;margin:2px 2px 10px}.dots i{flex:1;height:4px;border-radius:2px;background:var(--ap-fill)}.dots i.on{background:var(--accent)}
.opt{display:block;width:100%;text-align:left;border:0;background:var(--surface);border-radius:12px;padding:13px 14px;margin:0 0 8px;font-size:15px}.opt.ok{background:var(--up-soft);box-shadow:inset 0 0 0 1.5px var(--up)}.opt.no{background:#FBE3E1;box-shadow:inset 0 0 0 1.5px #D9534F}.opt.dim{opacity:.55}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .opt.no{background:#3A1A18}}
.why{background:var(--accent-soft);border-radius:12px;padding:11px 14px;margin:2px 0 10px;font-size:14px}
.tchip{display:inline-block;border:0;background:var(--accent-soft);color:var(--accent);border-radius:999px;padding:4px 11px;margin:3px 5px 3px 0;font-size:13px;font-weight:600}
.lv{display:inline-block;font-size:11px;font-weight:700;border-radius:5px;padding:1px 6px;background:var(--ap-fill);color:var(--muted);margin-left:6px;vertical-align:2px}.lv.l1{background:var(--accent);color:var(--accent-ink)}
.bxs{display:inline-flex;gap:2px;vertical-align:middle}.bxs i{width:7px;height:7px;border-radius:2px;background:var(--ap-fill)}.bxs i.on{background:var(--up)}
.tlv{position:relative;margin:6px 0 0;padding-left:0}.ev{display:grid;grid-template-columns:5.6em 1fr;gap:8px;background:var(--surface);border-radius:12px;padding:12px 14px;margin:0 0 8px;width:100%;text-align:left;border:0;color:inherit}
.ev .y{font:700 12.5px var(--ap-display);color:var(--accent);font-variant-numeric:tabular-nums;padding-top:2px}.ev .t{font-weight:700;margin:0 0 2px;font-size:15px}.ev .b{font-size:14px;margin:6px 0 0;color:var(--ink)}.ev .w{font-size:13px;margin:8px 0 0;color:var(--up);font-weight:500}.ev.rd .t::after{content:" ✓";color:var(--up)}
.ev .hint{font-size:12px;color:var(--muted);margin:0}
.ev>div,.ev .evb{min-width:0}.ev.op{display:block;padding:0;overflow:hidden}.ev .evh{display:grid;grid-template-columns:5.6em 1fr;gap:8px;width:100%;text-align:left;border:0;background:none;color:inherit;padding:12px 14px 4px}.ev .evb{padding:0 14px 14px}
.ev .b p{margin:0 0 9px;font-size:calc(15px*var(--fs));line-height:1.65;overflow-wrap:anywhere}.ev .b b{color:var(--accent)}.ev .hint{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.toon{display:grid;gap:8px;margin:6px 0 12px;padding:10px;border-radius:12px;background:var(--sunk)}.toon .tp{display:flex;gap:8px;align-items:flex-start}.toon .tp.r{flex-direction:row-reverse}
.toon .tf{flex:none;width:38px;height:38px;border-radius:50%;background:var(--surface);display:grid;place-items:center;font-size:21px}.toon .tb{background:var(--surface);border-radius:14px;padding:8px 11px;font-size:14px;line-height:1.45;max-width:82%;overflow-wrap:anywhere}.toon .tp.r .tb{background:var(--accent-soft)}
.colab{font-size:12px;color:var(--muted);margin:10px 0 4px}.cos{display:flex;flex-wrap:wrap;gap:5px}.cos span{font-size:12.5px;font-weight:600;background:var(--ap-fill);border-radius:999px;padding:3px 10px}
.wgal{max-width:100%;overflow:hidden}
.pg{display:flex;gap:8px;margin:10px 0}.pg .btn{flex:1}
.sizeb{display:flex;gap:6px;margin:6px 0 2px}.sizeb button{flex:1;border:0;background:var(--ap-fill);border-radius:10px;padding:8px 4px;font-size:13px}.sizeb button.on{background:var(--accent);color:var(--accent-ink);font-weight:700}
.hero{background:var(--accent-soft);border-radius:var(--r);padding:14px 16px;margin:8px 0;font-size:14px}.hero b{display:block;font:700 17px var(--ap-display);margin-bottom:3px}
.back{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:9500;display:flex;align-items:flex-end;justify-content:center}
.sheet{width:100%;max-width:560px;max-height:84vh;overflow:auto;background:var(--bg);border-radius:14px 14px 0 0;padding:10px 16px calc(18px + env(safe-area-inset-bottom,0px))}.sheet .grab{width:36px;height:5px;border-radius:3px;background:var(--ap-label3);margin:0 auto 10px}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  /* ───── 하루 몫 ───── */
  const SIZE = { light: { ch: 1, tm: 5, ep: 1, n: "가볍게 · 5분" }, normal: { ch: 1, tm: 8, ep: 2, n: "보통 · 10분" }, more: { ch: 2, tm: 15, ep: 3, n: "많이 · 20분" } };
  const Q = () => SIZE[S.size] || SIZE.normal;
  const today = () => (S.day[kst()] = S.day[kst()] || { ch: 0, tm: 0, ep: 0 });
  const bump = (k, n = 1) => { today()[k] += n; save("day"); };
  const chLeft = () => CH.filter(c => !S.ch[c.id]);
  const epAll = () => { const seen = new Set(); return HS.filter(h => !h.virt).flatMap(h => h.items.map((e, i) => [h, i, e._k])).filter(x => !seen.has(x[2]) && seen.add(x[2])); };
  const epLeft = () => epAll().filter(x => !S.ep[x[2]]);
  const due = () => TERMS.filter(t => S.box[t.id] && S.box[t.id].due <= kst());
  const fresh = () => { const seen = new Set(Object.keys(S.box)); const pri = new Set(CH.filter(c => S.ch[c.id]).flatMap(c => c.cards.flatMap(k => k.tm || []))); return TERMS.filter(t => !seen.has(t.id)).sort((a, b) => (pri.has(b.id) - pri.has(a.id)) || a.lv - b.lv); };
  function quota() {                                                             // [열쇠, 이름, 한 것, 할 것, 남은 게 있나]
    const q = Q(), d = today();
    const tmNeed = Math.min(q.tm, d.tm + due().length + fresh().length), chNeed = Math.min(q.ch, d.ch + chLeft().length), epNeed = Math.min(q.ep, d.ep + epLeft().length);
    return [["ch", "코스 한 장", d.ch, chNeed, "카드 5~6장 + 문제 3개"], ["tm", "용어", d.tm, tmNeed, "복습 먼저, 그다음 새 말"], ["ep", "역사 이야기", d.ep, epNeed, "큰 사건 한 편씩"]].filter(x => x[3] > 0);
  }
  function streak() { let n = 0; for (let i = 0; i < 400; i++) { const d = S.day[kst(-i)]; if (d && d.ch + d.tm + d.ep > 0) n++; else if (i) break; } return n; }
  function nextHash() {
    if (!S.diag && DG.length) return "#diag";
    const q = quota().find(x => x[2] < x[3]); if (!q) return "";
    if (q[0] === "ch") return "#ch=" + (startCh() || chLeft()[0]).id;
    if (q[0] === "tm") return "#review";
    const e = epLeft()[0]; return "#hist=" + e[0].id;
  }
  const startCh = () => { const sk = new Set((S.diag || {}).know || []); return chLeft().find(c => !sk.has(c.id)) || chLeft()[0]; };

  /* ───── 공통 ───── */
  const head = (t, sub, right = "") => `<div class="top"><h1 class="lt">${t}</h1><div class="row">${right}</div></div>${sub ? `<p class="sub">${sub}</p>` : ""}`;
  const backTop = (r = "") => `<div class="top"><button class="ib" data-act="back" aria-label="뒤로">‹</button><div class="row">${r}</div></div>`;
  const DEEP = window.VFM_DEEP || {}, DH = { esc, fmt, chips: ids => chips(ids) };   // 앱이 덧붙이는 '자세히' (예: sisa/learn/deep.js)
  const chips = ids => (ids || []).filter(i => TB[i]).map(i => `<button class="tchip" data-term="${i}">${esc(TB[i].t)}</button>`).join("");
  const boxes = id => { const b = (S.box[id] || {}).b || 0; return `<span class="bxs" title="익힘 ${b}/5">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= b ? "on" : ""}"></i>`).join("")}</span>`; };
  const ringSvg = (p, txt) => { const r = 30, c = 2 * Math.PI * r; return `<svg width="76" height="76" viewBox="0 0 76 76"><circle cx="38" cy="38" r="${r}" fill="none" stroke="var(--ap-fill)" stroke-width="8"/><circle cx="38" cy="38" r="${r}" fill="none" stroke="${p >= 1 ? "var(--up)" : "var(--accent)"}" stroke-width="8" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - Math.min(1, p))}" transform="rotate(-90 38 38)"/><text x="38" y="43" text-anchor="middle" font-size="15" font-weight="800" fill="var(--ink)">${txt}</text></svg>`; };

  /* ───── 오늘 ───── */
  function renderHome() {
    const q = quota(), done = q.reduce((a, x) => a + Math.min(x[2], x[3]), 0), tot = q.reduce((a, x) => a + x[3], 0), nx = nextHash(), sk = streak();
    let h = head(esc(L.name || "배움"), esc(L.intro || ""), L.back ? `<a class="btn sm" href="${L.back[0]}">‹ ${esc(L.back[1])}</a>` : "");
    if (!S.diag && DG.length) h += `<div class="hero"><b>먼저 3분, 지금 어디까지 아는지 볼게요</b>${DG.length}문제예요. 모르면 '모르겠어요'를 누르세요. 아는 장은 건너뛰고 필요한 곳부터 시작하게 해 드려요.<button class="btn pri go" data-go="#diag" style="margin-top:10px">수준 확인 시작</button></div>`;
    h += `<div class="ring">${ringSvg(tot ? done / tot : 1, tot ? `${done}/${tot}` : "✓")}<div class="tx"><b>${!tot ? "다 배웠어요" : done >= tot ? "오늘 몫 끝 ✓" : "오늘의 몫"}</b><small>${sk ? `연속 ${sk}일째 · ` : ""}${Q().n}</small><div class="sizeb">${Object.entries(SIZE).map(([k, v]) => `<button data-size="${k}" class="${S.size === k ? "on" : ""}">${v.n.split(" · ")[0]}</button>`).join("")}</div></div></div>`;
    h += `<div class="lc" style="padding:4px 16px">${q.map(x => { const ok = x[2] >= x[3], now = !ok && q.find(y => y[2] < y[3]) === x; return `<button class="step${ok ? " ok" : now ? " now" : ""}" data-step="${x[0]}"><i>${ok ? "✓" : ""}</i><div class="bx"><p class="t">${x[1]}</p><p class="s">${x[4]}</p></div><span class="v">${Math.min(x[2], x[3])}/${x[3]}</span></button>`; }).join("") || '<p class="note" style="margin:10px 0">준비된 것을 다 마쳤어요. 사전과 역사는 언제든 다시 볼 수 있어요.</p>'}</div>`;
    if (S.diag || !DG.length) h += nx ? `<button class="btn pri go" data-go="${nx}">이어서 하기 ›</button>` : `<p class="endnote">오늘은 여기까지 ✓ 내일 또 만나요. 더 하고 싶으면 아래에서 골라요.</p>`;
    const kn = TERMS.filter(t => (S.box[t.id] || {}).b >= 2).length, chd = CH.filter(c => S.ch[c.id]).length, ept = epAll().length, epd = ept - epLeft().length;
    h += `<h2 class="sec">내 진도</h2><div class="grid"><button class="tile" data-go="#course"><b>코스 ${chd}/${CH.length}장</b><small>${chd >= CH.length ? "다 마쳤어요" : "다음: " + esc((startCh() || {}).t || "")}</small></button><button class="tile" data-go="#terms"><b>용어 ${kn}/${TERMS.length}</b><small>익힌 말 · 복습 대기 ${due().length}개</small></button><button class="tile" data-go="#hist"><b>역사 ${epd}/${ept}편</b><small>${HS.filter(x => !x.virt).slice(0, 9).map(x => x.flag).join(" ")}</small></button>${L.practice ? `<button class="tile" data-go="#practice"><b>오늘 기사로 연습</b><small>${esc(L.practice.sub)}</small></button>` : ""}</div>`;
    if (S.diag) h += `<p class="note" style="margin-top:10px">수준 확인: ${S.diag.c}/${S.diag.n}개 맞음 (${esc(S.diag.day)}) · <a href="#diag">다시 하기</a></p>`;
    h += `<p class="note">기록은 이 기기에만 남아요. 여기 글은 공부용 설명이고 투자 권유가 아니에요.</p>`;
    return h;
  }

  /* ───── 수준 확인 ───── */
  let dg = null;
  function renderDiag() {
    if (!dg) dg = { i: 0, ok: [], miss: {} };
    if (dg.i >= DG.length) {
      const c = dg.ok.length, n = DG.length, per = {};
      DG.forEach((q, i) => { (per[q.ch] = per[q.ch] || [0, 0])[1]++; if (dg.ok.includes(i)) per[q.ch][0]++; });
      const know = Object.keys(per).filter(k => per[k][0] === per[k][1]);
      S.diag = { c, n, day: kst(), know }; save("diag"); const first = startCh(); dg = null;
      const lv = c <= n * .34 ? ["새싹", "처음이어도 괜찮아요. 1장부터 차근차근 가요."] : c <= n * .67 ? ["걸음마", "뼈대는 알고 있어요. 빈 곳부터 채워요."] : c < n ? ["기사 읽는 사람", "거의 알아요. 헷갈린 장만 짚고 역사와 용어로 넓혀요."] : ["탄탄", "기본은 다 알아요. 용어 깊이와 역사로 넓혀 가요."];
      return backTop() + head("결과: " + lv[0], `${n}문제 중 ${c}개 맞음 — ${lv[1]}`) + `<div class="lc" style="padding:4px 16px">${CH.map(ch => { const p = per[ch.id]; if (!p) return ""; const ok = p[0] === p[1]; return `<div class="step${ok ? " ok" : ""}"><i>${ok ? "✓" : ""}</i><div class="bx"><p class="t">${esc(ch.t)}</p><p class="s">${ok ? "알고 있어요 — 뒤로 미뤄도 돼요" : "여기부터 보면 좋아요"}</p></div><span class="v">${p[0]}/${p[1]}</span></div>`; }).join("")}</div>${first ? `<button class="btn pri go" data-go="#ch=${first.id}">'${esc(first.t)}'부터 시작 ›</button>` : ""}<button class="btn go" data-go="#home">오늘 화면으로</button>`;
    }
    const q = DG[dg.i];
    return backTop() + `<div class="dots">${DG.map((_, i) => `<i class="${i <= dg.i ? "on" : ""}"></i>`).join("")}</div><p class="note">수준 확인 ${dg.i + 1}/${DG.length} · 찍지 말고 모르면 '모르겠어요'</p><div class="lc"><h3>${esc(q.q)}</h3></div>${q.o.map((o, i) => `<button class="opt" data-dg="${i}">${esc(o)}</button>`).join("")}<button class="opt dim" data-dg="-1">모르겠어요</button>`;
  }

  /* ───── 코스 ───── */
  function renderCourse() {
    const sk = new Set((S.diag || {}).know || []), nx = startCh();
    const G = L.chGroups || {}; let pg = null;
    return head("코스", `${CH.length}장 · 한 장에 5분쯤. 순서대로 가면 기사가 읽혀요.`) + CH.map((c, i) => { const d = S.ch[c.id], gh = c.g && c.g !== pg && G[c.g] ? `<h2 class="sec">${esc(G[c.g][0])}<small>${esc(G[c.g][1] || "")}</small></h2>` : ""; pg = c.g || pg; return gh + `<button class="card" data-go="#ch=${c.id}"><span class="fl" style="font:800 15px var(--ap-display)">${d ? "✓" : c.flag || i + 1}</span><div class="bx"><p class="t">${esc(c.t)}${nx === c ? '<span class="lv l1">다음</span>' : ""}${!d && sk.has(c.id) ? '<span class="lv">아는 장</span>' : ""}</p><p class="s">${esc(c.sub)}</p><div class="meta"><span>카드 ${c.cards.length}장 · 문제 ${c.quiz.length}개</span>${d ? `<span>${esc(d.day)} 마침 · ${d.q}/${c.quiz.length}</span>` : ""}</div></div></button>`; }).join("") + (DG.length ? `<button class="btn more" data-go="#diag">수준 확인 ${S.diag ? "다시 " : ""}하기</button>` : "");
  }
  let cv = null;
  function renderCh(id) {
    const c = CH.find(x => x.id === id); if (!c) return renderCourse();
    if (!cv || cv.id !== id) cv = { id, i: 0, qi: -1, ok: 0, ans: null };
    const tot = c.cards.length + c.quiz.length, pos = cv.qi < 0 ? cv.i : c.cards.length + cv.qi;
    let h = backTop(`<span class="note" style="margin:0">${esc(c.t)}</span>`) + `<div class="dots">${Array.from({ length: tot }, (_, i) => `<i class="${i <= pos ? "on" : ""}"></i>`).join("")}</div>`;
    if (cv.qi < 0) {
      const k = c.cards[cv.i];
      h += `<div class="lc" id="swipe"><h3>${esc(k.h)}</h3>${fmt(k.b)}${DEEP.card ? DEEP.card(k, DH) : ""}${k.fig && FIG[k.fig] ? FIG[k.fig]() : ""}${ART.comic((window.VFM_CARDCM || {})[c.id + ":" + cv.i])}</div>${k.tm ? `<p class="note" style="margin:8px 2px 2px">이 카드의 말 (누르면 뜻)</p><div>${chips(k.tm)}</div>` : ""}<div class="pg">${cv.i ? '<button class="btn" data-cv="-1">‹ 이전</button>' : ""}<button class="btn pri" data-cv="1">${cv.i === c.cards.length - 1 ? "확인 문제 ›" : "다음 ›"}</button></div>`;
    } else if (cv.qi < c.quiz.length) {
      const q = c.quiz[cv.qi];
      h += `<p class="note">확인 문제 ${cv.qi + 1}/${c.quiz.length}</p><div class="lc"><h3>${esc(q.q)}</h3></div>${q.o.map((o, i) => `<button class="opt${cv.ans == null ? "" : i === q.a ? " ok" : i === cv.ans ? " no" : " dim"}" data-cq="${i}" ${cv.ans == null ? "" : "disabled"}>${esc(o)}</button>`).join("")}${cv.ans != null ? `<div class="why">${ART.face("me", cv.ans === q.a ? "s" : "t")}<b>${cv.ans === q.a ? "맞았어요." : "아쉬워요."}</b> ${esc(q.why)}</div><button class="btn pri go" data-cv="2">${cv.qi === c.quiz.length - 1 ? "마치기" : "다음 문제 ›"}</button>` : ""}`;
    } else {
      const first = !S.ch[id]; S.ch[id] = { day: kst(), q: cv.ok }; save("ch"); if (first) bump("ch");
      for (const t of new Set(c.cards.flatMap(k => k.tm || []))) if (TB[t] && !S.box[t]) S.box[t] = { b: 1, due: kst(1) }; save("box");
      const nx = nextHash(); cv = null;
      h = backTop() + head("한 장 끝 ✓", `'${esc(c.t)}' — 문제 ${S.ch[id].q}/${c.quiz.length}개 맞음. 이 장의 말들은 내일부터 복습에 나와요.`) + `<div>${chips([...new Set(c.cards.flatMap(k => k.tm || []))])}</div>` + (nx ? `<button class="btn pri go" data-go="${nx}" style="margin-top:14px">이어서 하기 ›</button>` : `<p class="endnote">오늘 몫을 다 했어요 ✓</p>`) + `<button class="btn go" data-go="#home">오늘 화면으로</button>`;
    }
    return h;
  }

  /* ───── 용어 복습 (라이트너 상자: 맞히면 다음 상자로, 틀리면 처음으로. 상자마다 1·3·7·16·35일 뒤 다시) ───── */
  const GAP = [0, 1, 3, 7, 16, 35];
  let rv = null;
  function buildReview(n) { const d = shuffle(due()).slice(0, n), f = fresh().slice(0, Math.max(0, n - d.length)); return { q: d.map(t => [t, "q"]).concat(f.map(t => [t, "n"])), i: 0, ans: null, opts: null, ok: 0 }; }
  function renderReview() {
    const q = Q(), left = Math.max(0, q.tm - today().tm);
    if (!rv) rv = buildReview(left || 6);
    if (rv.i >= rv.q.length) { const n = rv.q.length, ok = rv.ok; rv = null; const nx = nextHash(); return backTop() + head(n ? "용어 끝 ✓" : "지금은 볼 말이 없어요", n ? `${n}개를 봤어요${ok ? ` · 복습 ${ok}개 맞음` : ""}. 맞힌 말은 며칠 뒤에, 틀린 말은 내일 다시 나와요.` : "복습할 말도 새 말도 다 봤어요. 내일 다시 와요.") + (nx && nx !== "#review" ? `<button class="btn pri go" data-go="${nx}">이어서 하기 ›</button>` : "") + `<button class="btn go" data-go="#review" data-more="1">몇 개 더 하기</button><button class="btn go" data-go="#home">오늘 화면으로</button>`; }
    const [t, kind] = rv.q[rv.i];
    let h = backTop(`<span class="note" style="margin:0">용어 ${rv.i + 1}/${rv.q.length}</span>`) + `<div class="dots">${rv.q.map((_, i) => `<i class="${i <= rv.i ? "on" : ""}"></i>`).join("")}</div>`;
    if (kind === "n") return h + `<p class="note">새 말</p>` + termCard(t) + `<button class="btn pri go" data-rv="learn">알겠어요 ›</button>`;
    if (!rv.opts) { const pool = TERMS.filter(x => x.id !== t.id && x.c === t.c).concat(TERMS.filter(x => x.id !== t.id && x.c !== t.c)); rv.opts = shuffle([t].concat(shuffle(pool.slice(0, 8)).slice(0, 3))); }
    h += `<p class="note">복습 — 이 뜻의 말은?</p><div class="lc"><h3 style="font-size:17px;font-weight:600">${esc(t.s)}</h3></div>${rv.opts.map(o => `<button class="opt${rv.ans == null ? "" : o.id === t.id ? " ok" : o.id === rv.ans ? " no" : " dim"}" data-rv="${o.id}" ${rv.ans == null ? "" : "disabled"}>${esc(o.t)}</button>`).join("")}`;
    if (rv.ans != null) h += `<div class="why">${ART.face("me", rv.ans === t.id ? "s" : "t")}<b>${rv.ans === t.id ? "맞았어요." : "정답은 '" + esc(t.t) + "'."}</b> ${esc(t.a || "")}</div><button class="btn pri go" data-rv="next">다음 ›</button>`;
    else h += `<button class="opt dim" data-rv="?">모르겠어요</button>`;
    return h;
  }
  function termCard(t) {
    const cn = (CATS.find(c => c[0] === t.c) || [])[1] || "";
    return `<div class="lc"><p class="note" style="margin:0 0 4px">${esc(cn)}${t.en ? " · " + esc(t.en) : ""} ${boxes(t.id)}</p><h3>${esc(t.t)}</h3>${ART.termComic ? ART.termComic(t) : `<p>${esc(t.s)}</p>${t.a ? `<p><b>비유</b> ${esc(t.a)}</p>` : ""}${t.x ? `<p><b>기사에서는</b> ${esc(t.x)}</p>` : ""}`}${(L.termFig || {})[t.id] && FIG[L.termFig[t.id]] ? FIG[L.termFig[t.id]]() : ""}${DEEP.term ? DEEP.term(t, DH) : ""}${ART.relMap(t, TB)}${(t.r || []).length ? `<p class="note" style="margin:10px 0 2px">이어지는 말</p><div>${chips(t.r)}</div>` : ""}</div>`;
  }

  /* ───── 사전 ───── */
  let tf = { q: "", c: "" };
  function renderTerms() {
    const q = tf.q.trim().toLowerCase(), lst = TERMS.filter(t => (!tf.c || t.c === tf.c) && (!q || (t.t + " " + (t.en || "") + " " + t.s).toLowerCase().includes(q)));
    return head("사전", `${TERMS.length}개 · 뜻 한 줄, 비유, 기사에서 쓰이는 모습`) + `<input class="search" id="tq" type="search" placeholder="낱말 찾기 (예: 희석, series a)" value="${esc(tf.q)}"><div class="chips"><button data-tc="" class="${tf.c ? "" : "on"}">전체</button>${CATS.map(c => `<button data-tc="${c[0]}" class="${tf.c === c[0] ? "on" : ""}">${esc(c[1])}</button>`).join("")}</div><div class="list" id="tl">${termRows(lst)}</div>`;
  }
  const termRows = lst => lst.map(t => `<button class="li" data-term="${t.id}"><div class="bx"><p class="t">${esc(t.t)}${t.lv === 1 ? '<span class="lv l1">꼭</span>' : ""}</p><p class="s">${esc(t.s)}</p></div>${boxes(t.id)}</button>`).join("") || '<p class="note" style="padding:14px 0">찾는 말이 없어요</p>';
  function openTerm(id) {
    const t = TB[id]; if (!t) return; closeSheet();
    const b = document.createElement("div"); b.className = "back"; b.innerHTML = `<div class="sheet"><div class="grab"></div>${termCard(t)}<div class="pg">${S.box[id] ? "" : `<button class="btn" data-addbox="${id}">복습에 넣기</button>`}<button class="btn pri" data-act="close">닫기</button></div></div>`;
    b.addEventListener("click", e => { if (e.target === b) closeSheet(); }); document.body.appendChild(b);
  }
  const closeSheet = () => { const b = document.querySelector(".back"); if (b) b.remove(); };

  /* ───── 역사 ───── */
  function renderHist() {
    return head("역사", "큰 이야기만 골랐어요. 사건마다 '오늘 뉴스와 이어지는 점'이 붙어 있어요.") + (() => { const G = L.histGroups || {}; let pg = null; return HS.map(x => { const n = x.items.filter(e => S.ep[e._k]).length, gh = x.g && x.g !== pg && G[x.g] ? `<h2 class="sec">${esc(G[x.g][0])}<small>${esc(G[x.g][1] || "")}</small></h2>` : ""; pg = x.g || pg; if (!x.items.length) return gh; return gh + `<button class="card" data-go="#hist=${x.id}"><span class="fl">${x.flag}</span><div class="bx"><p class="t">${esc(x.name)}</p><p class="s">${esc(x.intro)}</p><div class="meta"><span>${n}/${x.items.length}편 읽음</span><span>${esc(x.items[0].y)} → ${esc(x.items[x.items.length - 1].y)}</span></div></div></button>`; }).join(""); })();
  }
  let openEp = null;
  function renderReg(id) {
    const x = HS.find(h => h.id === id); if (!x) return renderHist();
    if (openEp == null || !String(openEp).startsWith(id + ":")) { const i = x.items.findIndex(e => !S.ep[e._k]); openEp = id + ":" + (i < 0 ? 0 : i); markEp(openEp); }
    const pk = e => e.wk ? "en:" + String(e.wk).replace(/_/g, " ") : "";
    const pic = (e, cls) => pk(e) ? `<img class="${cls}" data-wt="${esc(pk(e))}" alt="" loading="lazy">` : "";
    const toon = e => (e.toon || []).length ? `<div class="toon">${e.toon.map((p, i) => `<div class="tp${i % 2 ? " r" : ""}"><span class="tf">${esc(p[0])}</span><span class="tb">${esc(p[1])}</span></div>`).join("")}</div>` : "";
    return backTop() + head(`${x.flag} ${esc(x.name)}`, esc(x.intro)) + (window.VFM_ART ? ART.strip(x.items, i => !!S.ep[x.items[i]._k], +String(openEp).split(":")[1]) : "") + `<div class="tlv">${x.items.map((e, i) => { const k = id + ":" + i, op = openEp === k;
      if (!op) return `<button class="ev${S.ep[e._k] ? " rd" : ""}" data-ep="${k}" id="ep-${i}"><span class="y">${esc(e.y)}</span><div>${pic(e, "hpt")}<p class="t">${esc(e.t)}</p><p class="hint">${x.virt ? esc(e._f || "") + " " : ""}${(e.co || []).length ? esc(e.co.slice(0, 4).join(" · ")) : "눌러서 읽기"}</p></div></button>`;
      return `<div class="ev op${S.ep[e._k] ? " rd" : ""}" id="ep-${i}"><button class="evh" data-ep="${k}"><span class="y">${esc(e.y)}</span><p class="t">${esc(e.t)}</p></button><div class="evb">${toon(e)}<div class="b">${fmt(e.b)}</div>${(e.co || []).length ? `<p class="colab">나오는 이름</p><div class="cos">${e.co.map(c => `<span>${esc(c)}</span>`).join("")}</div>` : ""}${pk(e) ? `<div data-gal="${esc(pk(e))}"></div>` : ""}${DEEP.hist ? DEEP.hist(e, DH) : ""}${e.w ? `<p class="w">→ ${APP === "sisa" ? "오늘 뉴스와" : "오늘 기사와"}: ${esc(e.w)}</p>` : ""}</div></div>`; }).join("")}</div>` + (() => { const nx = nextHash(); return nx && !nx.startsWith("#hist") ? `<button class="btn pri go" data-go="${nx}">이어서 하기 ›</button>` : ""; })();
  }
  function markEp(k) { k = epKey(k); if (!S.ep[k]) { S.ep[k] = kst(); save("ep"); bump("ep"); } }

  /* ───── 오늘 기사로 연습 (앱마다 다름: L.practice.load() → [{q, o, a, why}]) ───── */
  let pr = null;
  async function renderPractice() {
    if (!L.practice) return renderHome();
    if (!pr) { let qs = []; try { qs = await L.practice.load(); } catch (e) { } pr = { qs, i: 0, ans: null, ok: 0 }; }
    if (!pr.qs.length) { pr = null; return backTop() + head("오늘 기사로 연습", "지금은 문제로 낼 기사가 없어요. 조금 뒤에 다시 와요."); }
    if (pr.i >= pr.qs.length) { const r = `${pr.ok}/${pr.qs.length}`; pr = null; return backTop() + head("연습 끝 ✓", `${r}개 맞음. 실제 오늘 기사였어요.`) + `<button class="btn pri go" data-go="#practice">다른 기사로 한 번 더</button><button class="btn go" data-go="#home">오늘 화면으로</button>`; }
    const q = pr.qs[pr.i];
    return backTop(`<span class="note" style="margin:0">${pr.i + 1}/${pr.qs.length}</span>`) + `<p class="note">${esc(q.lab || "")}</p><div class="lc"><h3 style="font-size:17px">${esc(q.q)}</h3>${q.sub ? `<p class="note" style="margin:0">${esc(q.sub)}</p>` : ""}</div>${q.o.map((o, i) => `<button class="opt${pr.ans == null ? "" : i === q.a ? " ok" : i === pr.ans ? " no" : " dim"}" data-pq="${i}" ${pr.ans == null ? "" : "disabled"}>${esc(o)}</button>`).join("")}${pr.ans != null ? `<div class="why">${ART.face("me", pr.ans === q.a ? "s" : "t")}<b>${pr.ans === q.a ? "맞았어요." : "아쉬워요."}</b> ${esc(q.why || "")}</div>${chips(q.tm)}<button class="btn pri go" data-pq="next">다음 ›</button>` : ""}`;
  }

  /* ───── 그리기·누르기 ───── */
  const TABS = ["#home", "#course", "#terms", "#hist"];
  async function paint(keep) {
    let h = location.hash || "#home"; const y = keep ? scrollY : 0;
    const tab = h.startsWith("#ch") || h === "#diag" ? "course" : h === "#review" || h.startsWith("#term") ? "terms" : h.startsWith("#hist") ? "hist" : h === "#course" ? "course" : h === "#terms" ? "terms" : "home";
    tabs.querySelectorAll("button").forEach(b => b.dataset.v === tab ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"));
    if (h === "#diag") app.innerHTML = renderDiag();
    else if (h === "#course") app.innerHTML = renderCourse();
    else if (h.startsWith("#ch=")) app.innerHTML = renderCh(h.slice(4));
    else if (h === "#review") app.innerHTML = renderReview();
    else if (h === "#terms") { app.innerHTML = renderTerms(); const i = document.getElementById("tq"); i.addEventListener("input", () => { tf.q = i.value; const q = tf.q.trim().toLowerCase(); document.getElementById("tl").innerHTML = termRows(TERMS.filter(t => (!tf.c || t.c === tf.c) && (!q || (t.t + " " + (t.en || "") + " " + t.s).toLowerCase().includes(q)))); }); }
    else if (h.startsWith("#term=")) { app.innerHTML = renderTerms(); openTerm(decodeURIComponent(h.slice(6))); }
    else if (h === "#hist") app.innerHTML = renderHist();
    else if (h.startsWith("#hist=")) app.innerHTML = renderReg(h.slice(6));
    else if (h === "#practice") app.innerHTML = await renderPractice();
    else app.innerHTML = renderHome();
    scrollTo(0, y);
  }
  const nav = h => { if (location.hash === h) paint(); else location.hash = h; };
  addEventListener("hashchange", () => { cv = location.hash.startsWith("#ch=") ? cv : null; if (location.hash !== "#review") rv = null; if (location.hash !== "#diag") dg = null; if (location.hash !== "#practice") pr = null; closeSheet(); paint(); });
  tabs.addEventListener("click", e => { const b = e.target.closest("button[data-v]"); if (b) nav("#" + b.dataset.v); });
  document.addEventListener("click", e => {
    const el = e.target.closest("[data-go],[data-act],[data-term],[data-size],[data-step],[data-dg],[data-cv],[data-cq],[data-rv],[data-tc],[data-ep],[data-pq],[data-addbox]"); if (!el) return; const d = el.dataset;
    if (d.go) { if (d.more) rv = buildReview(6); return nav(d.go); }
    if (d.act === "back") { if (history.length > 1) history.back(); else nav("#home"); return; }
    if (d.act === "close") return closeSheet();
    if (d.term) return openTerm(d.term);
    if (d.addbox) { S.box[d.addbox] = { b: 1, due: kst(1) }; save("box"); toast("내일부터 복습에 나와요"); closeSheet(); return paint(true); }
    if (d.size) { S.size = d.size; save("size"); return paint(true); }
    if (d.step) return nav(d.step === "ch" ? (chLeft().length ? "#ch=" + startCh().id : "#course") : d.step === "tm" ? "#review" : (epLeft()[0] ? "#hist=" + epLeft()[0][0].id : "#hist"));
    if (d.dg != null) { const q = DG[dg.i]; if (+d.dg === q.a) dg.ok.push(dg.i); dg.i++; return paint(); }
    if (d.cv) { const c = CH.find(x => x.id === cv.id), n = +d.cv; if (n === 2) { cv.qi++; cv.ans = null; } else if (n === 1 && cv.i === c.cards.length - 1) cv.qi = 0; else cv.i = Math.max(0, cv.i + n); return paint(); }
    if (d.cq != null) { const q = CH.find(x => x.id === cv.id).quiz[cv.qi]; cv.ans = +d.cq; if (cv.ans === q.a) cv.ok++; return paint(true); }
    if (d.rv) { const [t, kind] = rv.q[rv.i];
      if (d.rv === "learn") { S.box[t.id] = { b: 1, due: kst(1) }; save("box"); bump("tm"); rv.i++; rv.opts = null; return paint(); }
      if (d.rv === "next") { rv.i++; rv.ans = null; rv.opts = null; return paint(); }
      rv.ans = d.rv; const ok = d.rv === t.id, b = ok ? Math.min(5, (S.box[t.id].b || 1) + 1) : 1; S.box[t.id] = { b, due: kst(GAP[b]) }; save("box"); bump("tm"); if (ok) rv.ok++; return paint(true); }
    if (d.tc != null) { tf.c = d.tc; return paint(true); }
    if (d.ep) { const shut = openEp === d.ep; openEp = shut ? d.ep.split(":")[0] + ":-" : d.ep; if (!shut) markEp(openEp); return paint(true); }
    if (d.pq != null) { if (d.pq === "next") { pr.i++; pr.ans = null; return paint(); } pr.ans = +d.pq; if (pr.ans === pr.qs[pr.i].a) pr.ok++; return paint(true); }
  });
  // 코스 카드: 옆으로 밀어 넘기기
  let sx = null; document.addEventListener("touchstart", e => { sx = e.target.closest("#swipe") ? e.touches[0].clientX : null; }, { passive: true });
  document.addEventListener("touchend", e => { if (sx == null || !cv) return; const dx = e.changedTouches[0].clientX - sx; sx = null; if (Math.abs(dx) < 60) return; const c = CH.find(x => x.id === cv.id); if (dx < 0) { if (cv.i === c.cards.length - 1) cv.qi = 0; else cv.i++; } else cv.i = Math.max(0, cv.i - 1); paint(); }, { passive: true });
  paint();
})();
