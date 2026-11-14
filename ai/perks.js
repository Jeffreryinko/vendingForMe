/* ai/perks.js — AI 탭 '오늘' 맨 위 'AI 혜택 소식' (Supabase 표 ai_perks, 매일 08:47 Claude 예약 작업이 씀)
 *  행: { report_date, headline, must:[항목], items:[항목], sources:[[제목, 주소]] }
 *  항목: { grp:"claude"|"global"|"china", svc, kind:"perk"|"price"|"model"|"feat"|"biz", t, one, how, until, warn, url }
 *  최근 14개를 한 번에 받아, 가장 새 판을 펼쳐 보이고 지난 판은 날짜 칩으로 바꿔 봄.
 */
(function () {
  "use strict";
  const CFG = window.VFM_SYNC || { url: "https://mirbslsgmwfahwitpgsl.supabase.co", key: "sb_publishable_bwp_34f04zXo3x-Pfcl5Wg_UwCJV5Pj" };
  const css = document.createElement("style");
  css.textContent = `.aip{background:var(--surface);border-radius:18px;padding:16px 16px 8px;margin:6px 0 14px}
.aip-k{font-size:12.5px;font-weight:700;color:var(--coin);margin:0 0 4px;display:flex;justify-content:space-between;gap:8px}.aip-k small{color:var(--muted);font-weight:500}
.aip-h{font-size:calc(16px*var(--fs,1));line-height:1.6;font-weight:600;margin:0 0 10px}
.aip-must{background:var(--coin-soft);border-radius:12px;padding:10px 12px;margin:0 0 10px}.aip-must b.l{display:block;font-size:12.5px;color:var(--coin);margin:0 0 4px}
.aip-it{padding:8px 0;border-top:1px solid var(--line)}.aip-must .aip-it{border-top-color:color-mix(in srgb,var(--coin) 25%,transparent)}.aip-must .aip-it:first-of-type{border-top:0}
.aip-it .t{font-weight:650;font-size:calc(15px*var(--fs,1));line-height:1.45;margin:0}.aip-it .t i{font-style:normal;font-size:11px;font-weight:700;color:var(--accent);background:var(--accent-soft);border-radius:6px;padding:1px 6px;margin-right:6px;vertical-align:1px}
.aip-it p{margin:3px 0 0;font-size:calc(14px*var(--fs,1));line-height:1.55}.aip-it .how{color:var(--ink)}.aip-it .how::before{content:"받는 법 · ";color:var(--muted)}
.aip-it .warn{color:var(--bad);font-weight:600}.aip-it .until{display:inline-block;margin-top:4px;font-size:12px;font-weight:700;color:var(--coin)}.aip-it a{font-size:13px;margin-left:8px}
.aip details{border-top:1px solid var(--line)}.aip summary{list-style:none;cursor:pointer;padding:10px 0;font-weight:700;display:flex;justify-content:space-between}.aip summary::-webkit-details-marker{display:none}.aip summary small{color:var(--muted);font-weight:500}
.aip-days{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:8px 0 4px}.aip-days::-webkit-scrollbar{display:none}
.aip-days button{flex:0 0 auto;padding:5px 11px;border-radius:999px;border:0;background:var(--ap-fill);font-size:13px;color:var(--ap-label)}.aip-days button[aria-current="true"]{background:var(--coin);color:#fff;font-weight:600}
.aip-src{font-size:12px;color:var(--muted);margin:6px 0 4px}.aip-src a{color:var(--muted);margin-right:8px}`;
  document.head.appendChild(css);
  const K = { perk: "혜택", price: "요금", model: "새 모델", feat: "새 기능", biz: "회사" };
  const G = [["claude", "Claude"], ["global", "해외 서비스"], ["china", "중국 서비스"]];
  const e = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const md = d => { const [, m, dd] = d.split("-"); return `${+m}월 ${+dd}일`; };
  let R, cur = 0;
  async function load() {
    if (R !== undefined) return R;
    try {
      const r = await fetch(CFG.url + "/rest/v1/ai_perks?select=*&order=report_date.desc&limit=14", { headers: { apikey: CFG.key, Authorization: "Bearer " + CFG.key } });
      R = r.ok ? await r.json() : [];
    } catch (x) { R = []; }
    return R;
  }
  const item = it => `<div class="aip-it"><p class="t">${it.kind ? `<i>${K[it.kind] || "소식"}</i>` : ""}${it.svc ? e(it.svc) + " · " : ""}${e(it.t)}</p>` +
    (it.one ? `<p>${e(it.one)}</p>` : "") + (it.how ? `<p class="how">${e(it.how)}</p>` : "") + (it.warn ? `<p class="warn">⚠ ${e(it.warn)}</p>` : "") +
    `<p>${it.until ? `<span class="until">기한 ${e(it.until)}</span>` : ""}${it.url ? `<a href="${e(it.url)}" target="_blank" rel="noopener">원문 ↗</a>` : ""}</p></div>`;
  function html() {
    if (!R || !R.length) return "";
    const x = R[cur], items = x.items || [];
    return `<section class="aip" id="aip"><p class="aip-k">AI 혜택 소식<small>${md(x.report_date)} 아침 보고</small></p>` +
      (x.headline ? `<p class="aip-h">${e(x.headline)}</p>` : "") +
      ((x.must || []).length ? `<div class="aip-must"><b class="l">꼭 챙길 것</b>${x.must.map(item).join("")}</div>` : "") +
      G.map(([g, name]) => { const l = items.filter(it => it.grp === g); return l.length ? `<details${g === "claude" ? " open" : ""}><summary>${name}<small>${l.length}건</small></summary>${l.map(item).join("")}</details>` : ""; }).join("") +
      ((x.sources || []).length ? `<details><summary>출처<small>${x.sources.length}곳</small></summary><p class="aip-src">${x.sources.map(s => `<a href="${e(s[1])}" target="_blank" rel="noopener">${e(s[0])}</a>`).join("")}</p></details>` : "") +
      (R.length > 1 ? `<div class="aip-days">${R.map((r, i) => `<button data-aip="${i}" aria-current="${i === cur}">${md(r.report_date)}</button>`).join("")}</div>` : "") + `</section>`;
  }
  document.addEventListener("click", ev => {
    const b = ev.target.closest("[data-aip]"); if (!b) return;
    ev.stopPropagation(); cur = +b.dataset.aip; const s = document.getElementById("aip"); if (s) s.outerHTML = html();
  }, true);
  window.aiPerks = async function () { await load(); return html(); };
})();
