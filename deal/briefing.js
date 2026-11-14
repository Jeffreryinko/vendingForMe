/* deal/briefing.js — 딜 첫 화면 '브리핑'
 *  자료: data/deal/briefing/latest.json  (로봇 robot/deal_briefing.py 가 무료 AI 로 씀. 열쇠를 넣기 전에는 Claude 가 쓴 예시)
 *   { label, at, by, note, lead,
 *     items:[{ ids:[딜 번호…], kind:"ma|vc|pe|ipo|fund|tie", st:"done|talk|plan|fail", cc, t 제목, one 한두 줄,
 *              buyer 사는 쪽·투자자, target 팔리는 쪽·투자받는 회사, amt 원, amtNote,
 *              why 왜 했나, co:[[이름, 한 줄 소개]…], mean 이 딜의 뜻, src 출처 }] }
 *  금액은 '원화 + 견주기' — 나라 예산·롯데월드타워 같은 익숙한 크기에 견줌.
 *  이 파일은 deal/index.html 의 함수(esc, won, flag, S, paint …)를 이름으로 바로 씀.
 */
(function () {
  "use strict";
  const css = `
.dbf{display:flex;flex-direction:column;gap:10px;margin:8px 0 6px}
.dbf-hero{background:var(--surface);border-radius:18px;padding:18px 18px 16px}
.dbf-k{font-size:12.5px;font-weight:700;color:var(--accent);margin:0 0 4px}
.dbf-h{font:800 24px/1.25 var(--ap-display,inherit);letter-spacing:-.02em;margin:0 0 4px}
.dbf-meta{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:12.5px;color:var(--muted);margin:0 0 12px}
.dbf-tts{border:0;background:var(--ap-fill,var(--sunk));border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:600}
.dbf-tts[aria-pressed=true]{background:var(--accent);color:var(--accent-ink,#fff)}
.dbf-lead{font-size:calc(17px*var(--fs,1));line-height:1.72;margin:0}
.dbf-it{background:var(--surface);border-radius:16px;overflow:hidden}
.dbf-top{display:block;width:100%;text-align:left;border:0;background:none;padding:14px 16px 12px}
.dbf-c{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:11.5px;font-weight:700;color:var(--muted);margin-bottom:4px}
.dbf-c b{background:var(--accent-soft);color:var(--accent);border-radius:6px;padding:1px 7px}
.dbf-c i{font-style:normal;border:1px solid var(--line);border-radius:6px;padding:0 6px}
.dbf-amt{display:block;font:800 21px/1.2 var(--ap-display,inherit);letter-spacing:-.02em;color:var(--accent);font-variant-numeric:tabular-nums}
.dbf-cmp{display:block;font-size:12.5px;color:var(--muted);margin:1px 0 6px}
.dbf-t{display:block;font-size:calc(17px*var(--fs,1));line-height:1.36;font-weight:700;letter-spacing:-.01em}
.dbf-one{display:block;font-size:calc(15px*var(--fs,1));line-height:1.62;color:color-mix(in srgb,var(--ink) 84%,transparent);margin-top:5px}
.dbf-full{padding:0 16px 14px}
.dbf-full h4{font-size:13px;font-weight:800;color:var(--accent);margin:12px 0 5px}
.dbf-full p{font-size:calc(15.5px*var(--fs,1));line-height:1.7;margin:0 0 6px}
.dbf-who{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;background:var(--sunk);border-radius:12px;padding:10px 12px;font-size:14.5px;margin:0}
.dbf-who dt{color:var(--muted);font-size:12.5px;font-weight:700;padding-top:2px}.dbf-who dd{margin:0;font-weight:600}
.dbf-co{margin:0;padding:0;list-style:none}.dbf-co li{font-size:14.5px;line-height:1.6;padding:6px 0;border-top:1px solid var(--line)}.dbf-co li:first-child{border-top:0}
.dbf-src{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.dbf-src button{border:0;background:var(--ap-fill,var(--sunk));border-radius:999px;padding:6px 13px;font-size:13px;font-weight:600}
.dbf-more{width:100%;border:0;background:var(--surface);border-radius:14px;padding:13px;font-size:15px;font-weight:700;color:var(--accent)}
.dbf-foot{font-size:12.5px;line-height:1.6;color:var(--muted);margin:0 4px}
.dbf-list{display:flex;flex-direction:column;gap:10px}
@media (min-width:700px){.dbf-list{display:grid;grid-template-columns:1fr 1fr;align-items:start}}
`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const KIND = { ma: "인수·합병", vc: "스타트업 투자", pe: "대형 투자", ipo: "상장", fund: "펀드", tie: "제휴·계약" };
  const ST = { talk: "협상 중", plan: "추진 중", fail: "무산", rumor: "소문" };
  const BY = { "claude-sample": "Claude가 쓴 예시 브리핑이에요", gemini: "AI(Gemini)가 딜 기사 제목을 바탕으로 썼어요", groq: "AI(Groq)가 딜 기사 제목을 바탕으로 썼어요" };
  let full = false, speaking = false;
  /* 원화 금액을 익숙한 크기에 견줌 (2026년 한국 예산 727.9조 원 · 롯데월드타워 사업비 약 4조 원) */
  function cmp(v) {
    v = +v || 0; if (!v) return "";
    const B = 727.9e12, T = 4e12, f = x => x >= 10 ? Math.round(x) : x.toFixed(1).replace(/\.0$/, "");
    if (v >= B * 0.01) return `한국 한 해 나라 예산의 ${f(v / B * 100)}%쯤`;
    if (v >= T * 1.5) return `롯데월드타워를 ${f(v / T)}채 지을 돈`;
    if (v >= T * 0.75) return "롯데월드타워를 한 채 지을 돈";
    if (v >= T * 0.1) return `롯데월드타워 짓는 돈의 ${f(v / T * 100)}%쯤`;
    return "";
  }
  const B = window.DBRF = {
    data: null,
    load() { return fetch("../data/deal/briefing/latest.json", { cache: "no-cache" }).then(r => r.ok ? r.json() : null).then(d => { B.data = d && Array.isArray(d.items) && d.items.length ? d : null; return B.data; }).catch(() => null); },
    deal(it) { for (const i of it.ids || []) if (S.byId[i]) return S.byId[i]; return null; },
    of(id) { return B.data ? B.data.items.find(it => (it.ids || []).includes(id)) : null; },
    body(it) {
      const d = B.deal(it);
      return `<dl class="dbf-who">${it.buyer ? `<dt>${it.kind === "ma" ? "사는 쪽" : "돈 넣는 쪽"}</dt><dd>${esc(it.buyer)}</dd>` : ""}${it.target ? `<dt>${it.kind === "ma" ? "팔리는 쪽" : it.kind === "ipo" ? "상장하는 회사" : "받는 쪽"}</dt><dd>${esc(it.target)}</dd>` : ""}${it.amt ? `<dt>얼마</dt><dd>약 ${won(it.amt)}${it.amtNote ? ` <small style="font-weight:400;color:var(--muted)">(${esc(it.amtNote)})</small>` : ""}</dd>` : ""}</dl>
        ${it.why ? `<h4>왜 했나</h4><p>${esc(it.why)}</p>` : ""}
        ${it.co && it.co.length ? `<h4>어떤 회사인가요</h4><ul class="dbf-co">${it.co.map(c => `<li><b>${esc(c[0])}</b> — ${esc(c[1])}</li>`).join("")}</ul>` : ""}
        ${it.mean ? `<h4>이 딜의 뜻</h4><p>${esc(it.mean)}</p>` : ""}
        <div class="dbf-src">${d ? `<button type="button" data-open="${esc(d.id)}">기사·관련 딜 보기 ›</button>` : ""}${it.src ? `<span class="note" style="margin:0;align-self:center">출처: ${esc(it.src)}</span>` : ""}</div>`;
    },
    view() {
      const d = B.data, when = d.at ? new Date(d.at) : null;
      const rows = d.items.map((it, k) => {
        const c = cmp(it.amt);
        return `<article class="dbf-it"><button type="button" class="dbf-top" data-dbfone="${k}">
          <span class="dbf-c"><b>${esc(KIND[it.kind] || "딜")}</b>${ST[it.st] ? `<i>${ST[it.st]}</i>` : ""}<span>${it.cc ? flag(it.cc) : ""}</span></span>
          ${it.amt ? `<span class="dbf-amt">약 ${won(it.amt)}</span>${c ? `<span class="dbf-cmp">${c}</span>` : ""}` : ""}
          <span class="dbf-t">${esc(it.t)}</span><span class="dbf-one">${esc(it.one || "")}</span></button>
          ${full || B.open === k ? `<div class="dbf-full">${B.body(it)}</div>` : ""}</article>`;
      }).join("");
      return `<div class="dbf">
        <section class="dbf-hero"><p class="dbf-k">딜 브리핑</p><h2 class="dbf-h">${esc(d.label || "오늘의 딜")}</h2>
          <p class="dbf-meta"><span>딜 ${d.items.length}건${when ? " · " + when.getHours() + "시에 씀" : ""}</span>${"speechSynthesis" in window ? `<button type="button" class="dbf-tts" data-dbftts aria-pressed="${speaking}">${speaking ? "■ 멈추기" : "▶ 듣기"}</button>` : ""}</p>
          <p class="dbf-lead">${esc(d.lead || "")}</p></section>
        <div class="dbf-list">${rows}</div>
        <button type="button" class="dbf-more" data-dbffull>${full ? "짧은 판으로 접기" : "자세한 판 보기 — 누가·얼마에 · 왜 했나 · 어떤 회사 · 이 딜의 뜻"}</button>
        <p class="dbf-foot">${esc(BY[d.by] || "")}${d.note ? " · " + esc(d.note) : ""}</p></div>`;
    },
    stop() { try { speechSynthesis.cancel(); } catch (e) { } speaking = false; },
    speak() {
      if (speaking) { B.stop(); return paint(); }
      const d = B.data, parts = [d.label, d.lead].concat(d.items.map((it, k) => `${k + 1}번. ${it.t}. ${it.one || ""}`)).filter(Boolean); let i = 0; speaking = true;
      const next = () => { if (!speaking || i >= parts.length) { speaking = false; if ((location.hash || "#today") === "#today") paint(); return; } const u = new SpeechSynthesisUtterance(parts[i++]); u.lang = "ko-KR"; u.rate = 1.05; u.onend = next; u.onerror = () => { speaking = false; }; speechSynthesis.speak(u); };
      try { speechSynthesis.cancel(); } catch (e) { } next(); paint();
    },
  };
  document.addEventListener("click", e => {
    const t = e.target.closest("[data-dbfone],[data-dbffull],[data-dbftts]"); if (!t) return;
    const y = scrollY;
    if (t.dataset.dbfone != null) { const k = +t.dataset.dbfone; B.open = B.open === k ? -1 : k; }
    else if (t.hasAttribute("data-dbffull")) { full = !full; B.open = -1; }
    else return B.speak();
    Promise.resolve(paint()).then(() => scrollTo(0, y));
  });
  addEventListener("pagehide", () => { if (speaking) B.stop(); });
})();
