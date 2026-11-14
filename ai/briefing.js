/* ai/briefing.js — AI 탭 '오늘' 맨 위 AI 브리핑 (data/ai/briefing/latest.json, 로봇 robot/ai_briefing.py · 하루 2번)
 *  { label, at, by, note, lead, items:[{ ids, kind, who, t, one, why, how, links:[[출처, 주소]] }] }
 *  접힌 채로 제목 목록 → 누르면 '무엇·왜 중요·써 보는 법' 펼침. 오늘 날짜(S.day가 오늘)일 때만 보임.
 */
(function () {
  "use strict";
  const css = document.createElement("style");
  css.textContent = `.aib{background:var(--surface);border-radius:18px;padding:16px 16px 6px;margin:6px 0 14px}
.aib-k{font-size:12.5px;font-weight:700;color:var(--accent);margin:0 0 4px;display:flex;justify-content:space-between}.aib-k small{color:var(--muted);font-weight:500}
.aib-lead{font-size:calc(16px*var(--fs,1));line-height:1.68;margin:0 0 8px}
.aib details{border-top:1px solid var(--line)}.aib summary{list-style:none;cursor:pointer;padding:11px 0;font-size:calc(16px*var(--fs,1));font-weight:700;line-height:1.4;display:flex;gap:8px}
.aib summary::-webkit-details-marker{display:none}.aib summary i{flex:none;font-style:normal;font-size:11px;font-weight:700;color:var(--accent);background:var(--accent-soft);border-radius:6px;padding:2px 6px;height:fit-content;margin-top:2px}
.aib .bd{padding:0 0 12px;font-size:calc(15px*var(--fs,1));line-height:1.65}.aib .bd h5{margin:8px 0 2px;font-size:12.5px;color:var(--muted)}.aib .bd p{margin:0}
.aib .bd a{color:var(--accent);font-size:13px;margin-right:10px}.aib-note{font-size:12px;color:var(--muted);margin:4px 0 10px}`;
  document.head.appendChild(css);
  const K = { model: "새 모델", feat: "새 기능", biz: "회사", rule: "규제·사건", paper: "논문", etc: "소식" };
  const e = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let B;
  window.aiBriefing = async function () {
    if (B === undefined) { try { const r = await fetch("../data/ai/briefing/latest.json", { cache: "no-cache" }); B = r.ok ? await r.json() : null; } catch (x) { B = null; } }
    if (!B || !B.items || !B.items.length) return "";
    if (Date.now() - Date.parse(B.at) > 40 * 3600e3) return "";   // 오래된 브리핑은 숨김
    return `<section class="aib"><p class="aib-k">${e(B.label)}<small>${e(B.by || "")}</small></p><p class="aib-lead">${e(B.lead)}</p>` +
      B.items.map(it => `<details><summary><i>${K[it.kind] || "소식"}</i><span>${e(it.t)}</span></summary><div class="bd"><p>${e(it.one)}</p>` +
        (it.why ? `<h5>왜 중요한가</h5><p>${e(it.why)}</p>` : "") + (it.how ? `<h5>나는 어떻게 써 보나</h5><p>${e(it.how)}</p>` : "") +
        `<p style="margin-top:6px">${(it.links || []).map(l => `<a href="${e(l[1])}" target="_blank" rel="noopener">${e(l[0])} 원문 ↗</a>`).join("")}</p></div></details>`).join("") +
      `<p class="aib-note">${e(B.note || "")}</p></section>`;
  };
})();
