/* 세상 읽기 교실 — 깊이 더하기. 사람이 써 둔 글(로봇·토큰 0).
   history.js · terms.js · course.js 는 그대로 두고, 이 폴더의 deep-*.js 가
     ① 이미 있는 역사 사건·낱말·코스 카드에 '자세히'를 덧붙이고  ② 새 사건·새 지역·새 낱말·새 장을 더해요.
   화면(assets/learn.js)은 window.VFM_DEEP.hist / term / card 가 돌려주는 HTML 을 원래 글 아래에 붙여요.

   역사 사건에 덧붙는 칸:  why 왜 일어났나 · flow [[때, 일]] 어떻게 흘러갔나 · who [[이름, 누구]] · num [[숫자, 뜻]] · aft 그 뒤 · mis 헷갈리기 쉬운 점 · tm [낱말 id]
   낱말에 덧붙는 칸:      d 조금 더 자세히 · ex 실제 예 · mis 헷갈리기 쉬운 점 · hs 어디서 온 말
   코스 카드에 덧붙는 칸:  ex 예를 들면 · pt [기억할 것]                                                                                         */
(function () {
  const L = window.VFM_LEARN = window.VFM_LEARN || {};
  const css = `
.dp{margin:10px 0 0;display:grid;gap:10px}
.dp h5{margin:0 0 3px;font:700 12.5px var(--ap-display,inherit);color:var(--accent);letter-spacing:.01em}
.dp p{margin:0;font-size:14px;line-height:1.62}
.dp .bx2{background:var(--sunk);border-radius:12px;padding:10px 12px}
.dp ol.fl{list-style:none;margin:0;padding:0;display:grid;gap:7px;border-left:2px solid var(--line);margin-left:4px}
.dp ol.fl li{position:relative;padding-left:12px;font-size:14px;line-height:1.55}
.dp ol.fl li::before{content:"";position:absolute;left:-5px;top:8px;width:8px;height:8px;border-radius:50%;background:var(--accent)}
.dp ol.fl b{display:block;font:700 12px var(--ap-display,inherit);color:var(--muted);font-variant-numeric:tabular-nums}
.dp .who{display:grid;gap:5px}
.dp .who div{font-size:13.5px;line-height:1.5}.dp .who b{font-weight:700}
.dp .nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:6px}
.dp .nums div{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:8px 10px;min-width:0}
.dp .nums b{display:block;font:800 17px var(--ap-display,inherit);font-variant-numeric:tabular-nums;line-height:1.2}
.dp .nums span{font-size:12px;color:var(--muted);line-height:1.4;display:block}
.dp .mis{border-left:3px solid #E0A12A;padding:2px 0 2px 10px}
.dp ul.pt{margin:0;padding-left:18px;display:grid;gap:3px;font-size:14px;line-height:1.55}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  const para = (s, H) => String(s).split("\n").map(x => "<p>" + H.esc(x).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>") + "</p>").join("");
  const sec = (title, body, cls = "") => body ? `<div class="${cls}"><h5>${title}</h5>${body}</div>` : "";

  window.VFM_DEEP = {
    hist(e, H) {
      if (!e || !(e.why || e.flow || e.who || e.num || e.aft || e.mis)) return "";
      return `<div class="dp">` +
        sec("왜 일어났나", e.why ? para(e.why, H) : "") +
        sec("어떻게 흘러갔나", (e.flow || []).length ? `<ol class="fl">${e.flow.map(f => `<li><b>${H.esc(f[0])}</b>${H.esc(f[1])}</li>`).join("")}</ol>` : "") +
        sec("나오는 사람·나라", (e.who || []).length ? `<div class="who">${e.who.map(w => `<div><b>${H.esc(w[0])}</b> — ${H.esc(w[1])}</div>`).join("")}</div>` : "", "bx2") +
        sec("숫자로 보면", (e.num || []).length ? `<div class="nums">${e.num.map(n => `<div><b>${H.esc(n[0])}</b><span>${H.esc(n[1])}</span></div>`).join("")}</div>` : "") +
        sec("그 뒤", e.aft ? para(e.aft, H) : "") +
        sec("헷갈리기 쉬운 점", e.mis ? para(e.mis, H) : "", "mis") +
        ((e.tm || []).length && H.chips(e.tm) ? `<div><h5>함께 볼 낱말</h5><div>${H.chips(e.tm)}</div></div>` : "") + `</div>`;
    },
    term(t, H) {
      if (!t || !(t.d || t.ex || t.mis || t.hs)) return "";
      return `<div class="dp">` + sec("조금 더 자세히", t.d ? para(t.d, H) : "") + sec("실제 예", t.ex ? para(t.ex, H) : "", "bx2") +
        sec("헷갈리기 쉬운 점", t.mis ? para(t.mis, H) : "", "mis") + sec("어디서 온 말", t.hs ? para(t.hs, H) : "") + `</div>`;
    },
    card(k, H) {
      if (!k || !(k.ex || k.pt)) return "";
      return `<div class="dp">` + sec("예를 들면", k.ex ? para(k.ex, H) : "", "bx2") +
        sec("기억할 것", (k.pt || []).length ? `<ul class="pt">${k.pt.map(x => `<li>${H.esc(x)}</li>`).join("")}</ul>` : "") + `</div>`;
    },
  };

  /* ── 덧붙이기 도구: deep-*.js 가 불러 씀 ── */
  const yr = e => { const m = String(e.y || "").match(/\d{3,4}/); return m ? +m[0] : 9999; };
  window.VFM_DEEP_ADD = {
    /* 역사: patch = { "지역id|사건 제목": {why, flow, …} },  add = { 지역id: [새 사건…] },  regions = [새 지역…] */
    hist({ patch = {}, add = {}, regions = [] }) {
      const HS = L.history = L.history || [];
      for (const k in patch) { const [r, t] = k.split("|"); const reg = HS.find(h => h.id === r), e = reg && reg.items.find(x => x.t === t); if (e) Object.assign(e, patch[k]); else console.warn("[deep] 역사 사건 없음:", k); }
      for (const r in add) { const reg = HS.find(h => h.id === r); if (!reg) { console.warn("[deep] 지역 없음:", r); continue; }
        for (const e of add[r]) if (!reg.items.some(x => x.t === e.t)) reg.items.push(e);
        reg.items = reg.items.map((e, i) => [e, i]).sort((a, b) => yr(a[0]) - yr(b[0]) || a[1] - b[1]).map(x => x[0]); }
      for (const g of regions) if (!HS.some(h => h.id === g.id)) HS.push(g);
    },
    /* 낱말: patch = { id: {d, ex, mis, hs} },  add = [새 낱말…],  cats = [[id, 이름]…] */
    terms({ patch = {}, add = [], cats = [] }) {
      const T = window.VFM_TERMS = window.VFM_TERMS || [], C = window.VFM_TERM_CATS = window.VFM_TERM_CATS || [];
      for (const c of cats) if (!C.some(x => x[0] === c[0])) C.push(c);
      for (const id in patch) { const t = T.find(x => x.id === id); if (t) Object.assign(t, patch[id]); else console.warn("[deep] 낱말 없음:", id); }
      for (const t of add) if (!T.some(x => x.id === t.id)) T.push(t);
    },
    /* 코스: patch = { "장id|카드 제목": {ex, pt, b?} },  cards = { 장id: [새 카드…] },  quiz = { 장id: [새 문제…] },  chapters = [새 장…] */
    course({ patch = {}, cards = {}, quiz = {}, chapters = [] }) {
      const CH = L.chapters = L.chapters || [];
      for (const k in patch) { const [c, h] = k.split("|"); const ch = CH.find(x => x.id === c), cd = ch && ch.cards.find(x => x.h === h); if (cd) Object.assign(cd, patch[k]); else console.warn("[deep] 카드 없음:", k); }
      for (const c in cards) { const ch = CH.find(x => x.id === c); if (ch) for (const k of cards[c]) if (!ch.cards.some(x => x.h === k.h)) ch.cards.push(k); }
      for (const c in quiz) { const ch = CH.find(x => x.id === c); if (ch) for (const q of quiz[c]) if (!(ch.quiz = ch.quiz || []).some(x => x.q === q.q)) ch.quiz.push(q); }
      for (const ch of chapters) if (!CH.some(x => x.id === ch.id)) CH.push(ch);
    },
  };
})();
