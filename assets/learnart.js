/* 배움 그림 도구 — 딜 '투자 교실', 시사 '세상 읽기 교실'이 같이 써요. 모두 화면에서 바로 그려요(사진 파일·로봇·토큰 0).
   · face / comic : 표정 7가지 얼굴과 말풍선으로 만드는 만화 (n보통 s웃음 o놀람 t생각 a화남 d시무룩 w윙크)
   · termComic    : 사전 낱말의 뜻·비유·기사 속 모습을 만화 세 칸으로
   · relMap       : 낱말과 '이어지는 말'을 잇는 지도
   · strip        : 역사 한 지역의 연표 띠 (읽은 편은 색이 참)
   · pic          : 위키백과 대표 사진 (assets/wikithumb.js 가 채움, 없으면 자리 없이 숨김)
   각 앱의 learn/art.js 가 사진 이름(VFM_PICS)과 코스 카드 만화(VFM_CARDCM)를 줘요. */
(function () {
  "use strict";
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  function face(who, mood) {
    const me = who === "me", skin = me ? "#FFD9A8" : "#F6C9A0", hair = me ? "#3F51B5" : "#5D4037";
    const eye = { n: `<circle cx="17" cy="23" r="2.2"/><circle cx="31" cy="23" r="2.2"/>`, s: `<path d="M14 24q3-4 6 0M28 24q3-4 6 0" fill="none" stroke="#222" stroke-width="2" stroke-linecap="round"/>`,
      o: `<circle cx="17" cy="23" r="3.4" fill="#fff" stroke="#222" stroke-width="1.6"/><circle cx="31" cy="23" r="3.4" fill="#fff" stroke="#222" stroke-width="1.6"/><circle cx="17" cy="23" r="1.3"/><circle cx="31" cy="23" r="1.3"/>`,
      t: `<circle cx="18" cy="22" r="2.2"/><circle cx="32" cy="22" r="2.2"/><path d="M13 17l8-2M27 15l8 2" stroke="#222" stroke-width="1.8" stroke-linecap="round"/>`,
      a: `<circle cx="17" cy="24" r="2.2"/><circle cx="31" cy="24" r="2.2"/><path d="M12 17l9 3M36 17l-9 3" stroke="#222" stroke-width="2.2" stroke-linecap="round"/>`,
      d: `<circle cx="17" cy="24" r="2.2"/><circle cx="31" cy="24" r="2.2"/><path d="M12 20l8-3M36 20l-8-3" stroke="#222" stroke-width="1.8" stroke-linecap="round"/>`,
      w: `<circle cx="17" cy="23" r="2.2"/><path d="M28 23h6" stroke="#222" stroke-width="2.2" stroke-linecap="round"/>` }[mood] || "";
    const mouth = { n: `<path d="M19 33h10"/>`, s: `<path d="M17 31q7 7 14 0"/>`, o: `<ellipse cx="24" cy="34" rx="3" ry="4" fill="#7a3b2e" stroke="none"/>`, t: `<path d="M20 34q4-2 8 0"/>`, a: `<path d="M18 35q6-5 12 0"/>`, d: `<path d="M18 35q6-4 12 0"/>`, w: `<path d="M17 31q8 6 14-1"/>` }[mood] || "";
    const top = me ? `<path d="M6 21C5 8 15 2 24 2s19 6 18 19c-3-6-8-9-11-9-4 3-12 4-18 3-3 1-5 3-7 6z" fill="${hair}"/>` : `<path d="M5 30C2 12 12 2 24 2s22 10 19 28c-1-9-4-14-8-16-6 2-16 2-22 0-4 2-7 7-8 16z" fill="${hair}"/>`;
    return `<svg class="fc" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="25" r="19" fill="${skin}"/>${top}<g fill="#222">${eye}</g><g fill="none" stroke="#222" stroke-width="2" stroke-linecap="round">${mouth}</g></svg>`;
  }
  /* cm = [[칸 제목, [[누구, 표정, 대사], …]], …] */
  function comic(cm) {
    if (!cm || !cm.length) return "";
    return `<div class="cmx" role="img" aria-label="만화">${cm.map(([cap, who], i) => `<div class="pn"><div class="cap"><b>${i + 1}</b>${esc(cap)}</div>${who.map(([w, mood, tx]) => `<div class="ln ${w}">${face(w, mood)}${tx ? `<span class="bb${/^\(.*\)$/.test(tx) ? " th" : ""}">${esc(tx)}</span>` : ""}</div>`).join("")}</div>`).join("")}</div>`;
  }
  const hash = s => { let h = 0; for (const c of String(s)) h = (h * 31 + c.charCodeAt(0)) >>> 0; return h; };
  const ASK = [t => `'${t}'가 뭐예요?`, t => `${((window.VFM_LEARN || {}).txt || {}).seen || "기사에"} '${t}'라는 말이 나왔어요.`, t => `'${t}', 들어는 봤는데…`, t => `'${t}'를 한 줄로 말하면요?`];
  const AHA = [["s", "아하!"], ["o", "그런 거였군요!"], ["s", "이제 알겠어요."], ["w", "기억하기 쉽네요."], ["s", "그림이 그려져요."]];
  function termComic(t) {
    const h = hash(t.id), cm = [["뜻", [["you", "t", ASK[h % ASK.length](t.t)], ["me", "s", t.s]]]];
    if (t.a) { const r = AHA[h % AHA.length]; cm.push(["비유", [["me", "w", t.a], ["you", r[0], r[1]]]]); }
    if (t.x) cm.push([((window.VFM_LEARN || {}).txt || {}).x || "기사에서는", [["me", "n", t.x]]]);
    return comic(cm);
  }
  /* 낱말 지도: 가운데 낱말 + 이어지는 말(많아야 6개) */
  function relMap(t, TB) {
    const rs = (t.r || []).filter(i => TB[i]).slice(0, 6); if (rs.length < 2) return "";
    const W = 320, H = rs.length > 4 ? 190 : 160, cx = W / 2, cy = H / 2, cut = (s, n) => s.length > n ? s.slice(0, n - 1) + "…" : s;
    const pos = rs.map((_, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / rs.length + (rs.length % 2 ? 0 : Math.PI / rs.length); return [cx + Math.cos(a) * 112, cy + Math.sin(a) * (H / 2 - 24)]; });
    return `<svg class="fg rm" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t.t)}와 이어지는 말">` +
      pos.map(([x, y]) => `<path d="M${cx} ${cy}L${x} ${y}" stroke="var(--line)" stroke-width="1.5"/>`).join("") +
      pos.map(([x, y], i) => { const s = cut(TB[rs[i]].t, 9), w = Math.max(44, s.length * 12 + 16); return `<rect x="${x - w / 2}" y="${y - 13}" width="${w}" height="26" rx="13" fill="var(--sunk)"/><text x="${x}" y="${y + 4}" text-anchor="middle" font-size="11.5" fill="var(--ink)">${esc(s)}</text>`; }).join("") +
      (() => { const s = cut(t.t, 10), w = Math.max(60, s.length * 14 + 22); return `<rect x="${cx - w / 2}" y="${cy - 17}" width="${w}" height="34" rx="17" fill="var(--accent)"/><text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="13.5" font-weight="800" fill="var(--accent-ink)">${esc(s)}</text>`; })() + `</svg>`;
  }
  /* 연표 띠: items = [{y, t}], read(i) → 읽었나, cur = 지금 펼친 편 */
  function strip(items, read, cur) {
    const n = items.length, W = 320, x = i => 14 + i * (W - 28) / Math.max(1, n - 1);
    return `<svg class="fg st" viewBox="0 0 ${W} 46" role="img" aria-label="연표">` + `<path d="M14 18H${W - 14}" stroke="var(--line)" stroke-width="3" stroke-linecap="round"/>` +
      items.map((e, i) => `<circle cx="${x(i)}" cy="18" r="${i === cur ? 7 : 5}" fill="${read(i) ? "var(--accent)" : "var(--surface)"}" stroke="var(--accent)" stroke-width="2"/>`).join("") +
      `<text x="14" y="40" font-size="10.5" fill="var(--muted)">${esc(items[0].y)}</text><text x="${W - 14}" y="40" text-anchor="end" font-size="10.5" fill="var(--muted)">${esc(items[n - 1].y)}</text>` +
      (cur >= 0 && cur < n && cur > 0 && cur < n - 1 ? `<text x="${Math.min(W - 40, Math.max(40, x(cur)))}" y="40" text-anchor="middle" font-size="10.5" font-weight="700" fill="var(--accent)">${esc(items[cur].y)}</text>` : "") + `</svg>`;
  }
  const pic = (key, cls) => { const k = (window.VFM_PICS || {})[key]; return k ? `<img class="${cls}" data-wt="${esc(k)}" alt="" loading="lazy">` : ""; };
  const css = `
.cmx{display:grid;gap:8px;margin:4px 0 10px}
.cmx .pn{border:1.5px solid var(--ink);border-radius:12px;padding:8px 9px 9px;background:var(--surface);display:grid;gap:6px}
.cmx .cap{font-size:12px;font-weight:700;color:var(--muted);display:flex;gap:6px;align-items:center;min-height:18px}
.cmx .cap b{flex:none;width:18px;height:18px;border-radius:50%;background:var(--accent);color:var(--accent-ink) !important;font-size:11px;display:inline-flex;align-items:center;justify-content:center}
.cmx .ln{display:flex;gap:8px;align-items:flex-end}.cmx .ln.you{flex-direction:row-reverse}
.cmx .fc{flex:none;width:38px;height:38px}
.cmx .bb{background:var(--sunk);border-radius:14px 14px 14px 4px;padding:7px 11px;font-size:calc(14.5px*var(--fs,1));line-height:1.5;max-width:80%;overflow-wrap:anywhere}
.cmx .you .bb{border-radius:14px 14px 4px 14px;background:var(--accent-soft)}
.cmx .bb.th{background:none;border:1.5px dashed var(--line);color:var(--muted)}
.why .fc{width:30px;height:30px;vertical-align:-9px;margin-right:6px}
img[data-wt]{display:none}
.hp{width:100%;height:150px;object-fit:cover;border-radius:10px;margin:8px 0 2px;background:var(--sunk)}
.hpt{width:46px;height:46px;object-fit:cover;border-radius:8px;float:right;margin-left:8px;background:var(--sunk)}
.fg.st{margin:2px 0 10px}.fg.rm{margin:6px 0 0}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  /* 만화 대본 줄임말: "칸 제목|me:s:대사|you:o:대사" → comic() 이 읽는 꼴 */
  const line = p => { const [cap, ...r] = p.split("|"); return [cap, r.filter(Boolean).map(x => { const i = x.indexOf(":"), j = x.indexOf(":", i + 1); return [x.slice(0, i), x.slice(i + 1, j), x.slice(j + 1)]; })]; };
  const cms = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v.map(line)]));
  window.VFM_ART = { face, comic, termComic, relMap, strip, pic, cms };
})();
