/* briefing.js — 시사 첫 화면 '브리핑' (아침 7시 · 저녁 7시)
 *  자료: data/sisa/briefing/latest.json  (로봇 robot/briefing.py 가 무료 AI 로 씀. 열쇠를 넣기 전에는 Claude 가 쓴 예시)
 *   { id, slot:"am|pm", label, at, ed, by, note, lead,
 *     items:[{ sids:[이슈 번호…], cat, t 제목, one 한두 줄, sum 요약, why 왜 중요, chg 어제와 달라진 점,
 *              views:[{cc 나라, src 매체, t}], bg:[{k:"term|hist|ch", id, t}] }],
 *     kr:[{sid,t,one}]  한국 언론엔 잘 안 나온 일,  buzz:[{t,one,cc}] 요즘 화제 }
 *  화면: 짧은 판(제목 + 한두 줄) → '자세한 판' 단추로 요약·왜 중요·나라별 시각·배경까지. 이슈를 누르면 이슈 화면.
 *  이 파일은 sisa/index.html 의 함수(esc, flag, cname, findStory, CAT, S, render …)를 부를 때 이름으로 바로 씀.
 */
(function () {
  "use strict";
  const css = `
.brf-sw{display:flex;gap:4px;background:var(--sunk);border-radius:12px;padding:3px;margin:0 0 14px}
.brf-sw button{flex:1;border:0;background:none;border-radius:9px;padding:8px 4px;font-size:13.5px;font-weight:500;color:var(--muted)}
.brf-sw button[aria-pressed=true]{background:var(--surface);color:var(--ink);font-weight:700;box-shadow:0 1px 4px rgba(0,0,0,.10)}
.brf{display:flex;flex-direction:column;gap:12px}
.brf-hero{background:var(--surface);border:.5px solid var(--line);box-shadow:0 1px 2px rgba(0,0,0,.04),0 10px 30px -12px rgba(0,0,0,.10);border-radius:20px;padding:18px 18px 16px}
.brf-k{display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:700;color:var(--accent);margin:0 0 6px}
.brf-k i{width:8px;height:8px;border-radius:50%;background:var(--accent)}
.brf-h{font-size:24px;line-height:1.25;font-weight:800;letter-spacing:-.02em;margin:0 0 4px}
.brf-meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;font-size:12.5px;color:var(--muted);margin:0 0 12px}
.brf-tts{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:600;color:var(--ink)}
.brf-tts[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.brf-lead{font-size:17px;line-height:1.72;margin:0;word-break:keep-all}
.brf-list{display:flex;flex-direction:column;gap:10px;margin:0;padding:0;list-style:none}
.brf-it{background:var(--surface);border:.5px solid var(--line);box-shadow:0 1px 2px rgba(0,0,0,.03);border-radius:18px;overflow:hidden}
.brf-it.rd .brf-t{color:var(--muted)}
.brf-top{display:flex;gap:12px;align-items:flex-start;width:100%;text-align:left;border:0;background:none;padding:14px 16px;color:inherit;font:inherit}
.brf-n{flex:none;width:26px;height:26px;border-radius:50%;background:var(--accent-soft);color:var(--accent);font-size:13px;font-weight:800;display:grid;place-items:center;margin-top:1px}
.brf-it.rd .brf-n{background:var(--sunk);color:var(--muted)}
.brf-tx{flex:1;min-width:0}
.brf-c{display:block;font-size:11.5px;font-weight:700;color:var(--muted);margin:0 0 2px}
.brf-t{display:block;font-size:17px;line-height:1.36;font-weight:700;letter-spacing:-.01em;word-break:keep-all}
.brf-one{display:block;font-size:15px;line-height:1.62;color:color-mix(in srgb,var(--ink) 84%,transparent);margin-top:5px;word-break:keep-all}
.brf-sub{display:block;font-size:12px;color:var(--muted);margin-top:6px}
.brf-th{flex:none;width:64px;height:64px;border-radius:12px;object-fit:cover;background:var(--sunk) center/cover no-repeat}
.brf-full{padding:0 16px 14px 54px}
.brf-full p{font-size:15.5px;line-height:1.72;margin:0 0 10px;word-break:keep-all}
.brf-full h4,.brf-ib h4{font-size:13px;font-weight:800;color:var(--accent);margin:14px 0 6px;letter-spacing:-.01em}
.brf-vw{display:flex;flex-direction:column;gap:8px;margin:0;padding:0;list-style:none}
.brf-vw li{background:var(--sunk);border-radius:12px;padding:9px 12px;font-size:14.5px;line-height:1.6;word-break:keep-all}
.brf-vw b{display:block;font-size:12.5px;margin-bottom:2px}
.brf-vw small{font-weight:500;color:var(--muted)}
.brf-bg{display:flex;flex-wrap:wrap;gap:6px}
.brf-bg a{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:13px;color:var(--ink);text-decoration:none;background:var(--surface)}
.brf-bg a i{font-style:normal;font-size:11px;color:var(--accent);font-weight:700}
.brf-chg{background:var(--coin-soft);border-radius:12px;padding:9px 12px;font-size:14.5px;line-height:1.6;margin:0 0 10px}
.brf-chg b{display:block;font-size:12.5px;color:var(--coin);margin-bottom:2px}
.brf-more{width:100%;border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:13px;font-size:15px;font-weight:700;color:var(--accent)}
.brf-box{background:var(--surface);border:.5px solid var(--line);border-radius:18px;padding:14px 16px}
.brf-box h3{font-size:15px;font-weight:800;margin:0 0 2px}
.brf-box .note{margin-bottom:8px}
.brf-box button{display:block;width:100%;text-align:left;border:0;border-top:1px solid var(--line);background:none;padding:10px 0;color:inherit;font:inherit}
.brf-box button b{display:block;font-size:15px;line-height:1.4}
.brf-box button span{display:block;font-size:13.5px;color:var(--muted);margin-top:2px}
.brf-foot{font-size:12.5px;line-height:1.6;color:var(--muted);margin:2px 4px 0}
.brf-ib{margin:8px 0 12px}
.brf-it>.vfm-ask{margin:0 0 14px 54px}.brf-hero>.vfm-ask{margin-top:12px}
.brf-ib p{font-size:16px;line-height:1.74;margin:0 0 8px;word-break:keep-all}
.brf-ib .brf-by{font-size:12px;color:var(--muted);margin:10px 0 0}
.brf-tm{border:0;background:none;padding:0;font:inherit;color:inherit;border-bottom:1.5px dotted var(--accent);cursor:pointer}
.brf-vw.op li{background:none;border:1px dashed var(--line)}
.brf-full h4 small,.brf-ib h4 small{font-weight:500;color:var(--muted)}
.brf-lk{border:0;background:none;padding:0;font:inherit;color:var(--accent);font-weight:600}
.brf-pop{position:fixed;inset:0;z-index:90;background:rgba(0,0,0,.28);display:flex;align-items:flex-end;justify-content:center}
.brf-pop-in{width:min(560px,100%);background:var(--surface);border-radius:20px 20px 0 0;padding:20px 20px calc(20px + env(safe-area-inset-bottom,0px));box-shadow:0 -8px 30px rgba(0,0,0,.18)}
.brf-pop-in b{font-size:18px}
.brf-pop-in p{font-size:16px;line-height:1.7;margin:8px 0 14px}
.brf-pop-in div{display:flex;justify-content:space-between;align-items:center}
.brf-pop-in a{font-size:14.5px;font-weight:600}
.brf-pop-in button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:7px 16px;font-size:14px}
@media (min-width:700px){ .brf-list{display:grid;grid-template-columns:1fr 1fr;align-items:start} .brf-h{font-size:28px} }
`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  const LS = { g(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, s(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } } };
  const BY = { "claude-sample": "Claude가 쓴 예시 브리핑이에요", gemini: "AI(Gemini)가 기사 제목·요약을 바탕으로 썼어요", groq: "AI(Groq)가 기사 제목·요약을 바탕으로 썼어요", rule: "로봇이 규칙으로 엮었어요" };
  const KBG = { term: ["낱말", "learn/#term="], hist: ["역사", "learn/#hist="], ch: ["나라·코스", "learn/#ch="] };
  let full = false, speaking = false;
  // sisa/index.html 의 함수는 window.SISA 다리로 받아 씀 (본문 스크립트가 함수 안에 싸여 있어서)
  const X = n => (...a) => window.SISA[n](...a);
  const esc = X("esc"), flag = X("flag"), cname = X("cname"), findStory = X("findStory"), storyPhoto = X("storyPhoto"), issueCountries = X("issueCountries"), sm = X("sm"), issueOpened = X("issueOpened"), render = X("render");
  const CAT = new Proxy({}, { get: (_, k) => window.SISA.CAT[k] }), S = new Proxy({}, { get: (_, k) => window.SISA.S[k], set: (_, k, v) => { window.SISA.S[k] = v; return true; } });

  const B = window.BRF = {
    data: null,
    load() {
      const base = window.VFM_DATA_BASE || "../data/sisa/";
      const get = (f, o) => fetch(base + f, o).then(r => r.ok ? r.json() : null).catch(() => null);
      get("lean.json").then(d => { B.leans = d || {}; });                       // 매체 성향표
      get("learn_index.json").then(d => { if (d && d.term) { B.terms = Object.keys(d.def || {}).map(id => [d.term[id], id, d.def[id]]).filter(x => x[0] && x[0].length >= 2 && !/[·\/(]/.test(x[0])).sort((a, b) => b[0].length - a[0].length); if (B.data && B.mode() === "brief" && !S.sheetOpen) render(); } });
      return get("briefing/latest.json", { cache: "no-cache" }).then(d => { B.data = d && Array.isArray(d.items) && d.items.length ? d : null; return B.data; });
    },
    leans: {}, terms: [],
    lean(id) { return B.leans[id] || ""; },
    /* 글 안의 어려운 낱말(배움 사전에 있는 것)을 누를 수 있게 — 한 문단에 낱말마다 한 번만 */
    tx(t) {
      let h = esc(t || ""); if (!B.terms.length) return h;
      const used = [];
      for (const [name, id] of B.terms) {
        if (used.length >= 4) break;
        const i = h.indexOf(esc(name)); if (i < 0) continue;
        if (/<[^>]*$/.test(h.slice(0, i)) || used.some(([a, b]) => i < b && i + name.length > a)) continue;      // 이미 단추 안이면 건너뜀
        const btn = `<button type="button" class="brf-tm" data-brfterm="${esc(id)}">${esc(name)}</button>`;
        h = h.slice(0, i) + btn + h.slice(i + esc(name).length); used.push([i, i + btn.length]);
      }
      return h;
    },
    termPop(id) {
      const t = B.terms.find(x => x[1] === id); if (!t) return;
      let el = document.getElementById("brfPop"); if (el) el.remove();
      el = document.createElement("div"); el.id = "brfPop"; el.className = "brf-pop";
      el.innerHTML = `<div class="brf-pop-in" role="dialog" aria-label="낱말 풀이"><b>${esc(t[0])}</b><p>${esc(t[2])}</p><div><a href="learn/#term=${encodeURIComponent(id)}">배움에서 더 보기 ›</a><button type="button" data-brfpopx>닫기</button></div></div>`;
      document.body.appendChild(el);
    },
    mode() { return LS.g("vfm:sisa:home", "brief"); },
    setMode(m) { LS.s("vfm:sisa:home", m); if (m !== "brief") LS.s("vfm:mode:sisa-today", m); },
    sw() {
      const m = B.mode();
      return `<div class="brf-sw" role="group" aria-label="보기 방식">${[["brief", "브리핑"], ["deck", "넘겨보기"], ["list", "목록"]].map(([k, l]) => `<button type="button" data-hm="${k}" aria-pressed="${m === k}">${l}</button>`).join("")}</div>`;
    },
    story(it) { for (const k of it.sids || (it.sid ? [it.sid] : [])) { const s = findStory(k); if (s) return s; } return null; },
    stories(it) { return (it.sids || []).map(k => findStory(k)).filter(Boolean); },
    of(s) { const d = B.data; if (!d || !s) return null; return d.items.find(it => (it.sids || []).includes(s.sid) || (it.sids || []).includes(s.id)) || null; },
    bgHtml(bg) {
      if (!bg || !bg.length) return "";
      return `<h4>배경 더 알기</h4><div class="brf-bg">${bg.map(b => { const k = KBG[b.k]; return k ? `<a href="${k[1]}${encodeURIComponent(b.id)}"><i>${k[0]}</i>${esc(b.t)}</a>` : ""; }).join("")}</div>`;
    },
    viewsHtml(v) {
      if (!v || !v.length) return "";
      return `<h4>나라마다 이렇게 전해요</h4><ul class="brf-vw">${v.map(x => `<li><b>${flag(x.cc)} ${esc(cname(x.cc))} <small>· ${esc(x.src || "")}</small></b>${esc(x.t)}</li>`).join("")}</ul>`;
    },
    body(it) {
      return `${it.chg ? `<div class="brf-chg"><b>어제와 달라진 점</b>${esc(it.chg)}</div>` : ""}
        ${it.sum ? `<p>${B.tx(it.sum)}</p>` : ""}
        ${it.why ? `<h4>왜 중요한가요</h4><p>${B.tx(it.why)}</p>` : ""}
        ${B.viewsHtml(it.views)}
        ${it.op && it.op.length ? `<h4>이렇게 보는 사람도 있어요 <small>사설·칼럼</small></h4><ul class="brf-vw op">${it.op.map(x => `<li><b>${flag(x.cc)} ${esc(x.src || "")}</b>${esc(x.t)}</li>`).join("")}</ul>` : ""}
        ${B.bgHtml(it.bg)}`;
    },
    /* 이슈 화면 맨 위에 넣는 칸: 요약 → 왜 중요 → 나라별 시각 → 배경 */
    issueBlock(s) {
      const it = B.of(s); if (!it) return "";
      return `<div class="brf-ib">${B.body(it)}<p class="brf-by">${esc(BY[B.data.by] || "")} · ${esc(B.data.label || "")}</p></div>`;
    },
    view() {
      const d = B.data, when = d.at ? new Date(d.at) : null;
      const hm = when ? `${when.getHours()}시${when.getMinutes() ? " " + when.getMinutes() + "분" : ""}에 씀` : "";
      const rows = d.items.map((it, k) => {
        const ss = B.stories(it), s = ss[0];
        const n = new Set(ss.flatMap(x => x.items || [])).size, cs = new Set(ss.flatMap(x => issueCountries(x))).size;
        const ph = k < 3 && s ? storyPhoto(s) : null;
        const rd = s && issueOpened(s);
        const top = `<span class="brf-n">${k + 1}</span><span class="brf-tx">${CAT[it.cat] ? `<span class="brf-c">${esc(CAT[it.cat])}</span>` : ""}<span class="brf-t">${esc(it.t)}</span><span class="brf-one">${esc(it.one || "")}</span>${n ? `<span class="brf-sub">${cs > 1 ? cs + "개 나라 · " : ""}기사 ${n}개${s ? " · 누르면 자세히" : ""}</span>` : ""}</span>${ph ? `<img class="brf-th" src="${esc(sm(ph.u, 168, 168))}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer"${ph.b ? ` style="background-image:url(data:image/webp;base64,${ph.b})"` : ""}>` : ""}`;
        return `<li class="brf-it${rd ? " rd" : ""}">${s ? `<button type="button" class="brf-top" data-issue="${esc(s.id)}">${top}</button>` : `<div class="brf-top">${top}</div>`}${full ? `<div class="brf-full">${B.body(it)}</div>` : ""}</li>`;
      }).join("");
      const kr = (d.kr || []).map(x => { const s = findStory(x.sid); return `<button type="button"${s ? ` data-issue="${esc(s.id)}"` : ""}><b>${esc(x.t)}</b><span>${esc(x.one || "")}</span></button>`; }).join("");
      const buzz = (d.buzz || []).map(x => `<button type="button"${x.q ? ` data-q="${esc(x.q)}"` : ""}><b>${x.cc ? flag(x.cc) + " " : ""}${esc(x.t)}</b><span>${esc(x.one || "")}</span></button>`).join("");
      S.issueOrder = d.items.map(it => { const s = B.story(it); return s && s.id; }).filter(Boolean);
      return `${S.newEd ? `<button type="button" class="newed" data-ed="${S.newEd.id}">새 판이 도착했어요 · ${esc(S.newEd.label)} 보기</button>` : ""}${B.sw()}
      <div class="brf">
        <section class="brf-hero">
          <p class="brf-k"><i></i>${d.slot === "am" ? "아침 브리핑" : "저녁 브리핑"}</p>
          <h1 class="brf-h">${esc(d.label || "오늘의 브리핑")}</h1>
          <p class="brf-meta"><span>이슈 ${d.items.length}개 · 짧은 판 1분${hm ? " · " + hm : ""}</span>${"speechSynthesis" in window ? `<button type="button" class="brf-tts" data-brftts aria-pressed="${speaking}">${speaking ? "■ 멈추기" : "▶ 듣기"}</button>` : ""}</p>
          <p class="brf-lead">${esc(d.lead || "")}</p>
        </section>
        <ol class="brf-list">${rows}</ol>
        <button type="button" class="brf-more" data-brffull>${full ? "짧은 판으로 접기" : "자세한 판 보기 — 요약 · 왜 중요한지 · 나라별 시각"}</button>
        ${kr ? `<section class="brf-box"><h3>한국 언론엔 잘 안 나온 일</h3><p class="note">해외에서는 여러 나라가 다뤘어요</p>${kr}</section>` : ""}
        ${buzz ? `<section class="brf-box"><h3>요즘 화제</h3><p class="note">나라별 검색어·게시판에서 뜨는 것</p>${buzz}</section>` : ""}
        <p class="brf-foot">${esc(BY[d.by] || "")}${d.note ? " · " + esc(d.note) : ""}<br>이 판의 모든 이슈는 위의 '목록'에서 볼 수 있어요. <button type="button" class="brf-lk" data-v="hot">나라별 검색어 보기 ›</button></p>
      </div>`;
    },
    speakText() {
      const d = B.data; if (!d) return "";
      return [d.label, d.lead].concat(d.items.map((it, k) => `${k + 1}번. ${it.t}. ${full ? [it.sum, it.why].filter(Boolean).join(" ") : it.one || ""}`)).filter(Boolean).join("\n");
    },
    stop() { try { speechSynthesis.cancel(); } catch (e) { } speaking = false; },
    speak() {
      if (speaking) { B.stop(); return render(); }
      const parts = B.speakText().split("\n").filter(Boolean); let i = 0; speaking = true;
      const next = () => {
        if (!speaking || i >= parts.length) { speaking = false; if (B.mode() === "brief" && !S.sheetOpen) render(); return; }
        const u = new SpeechSynthesisUtterance(parts[i++]); u.lang = "ko-KR"; u.rate = 1.05; u.onend = next; u.onerror = () => { speaking = false; };
        speechSynthesis.speak(u);
      };
      try { speechSynthesis.cancel(); } catch (e) { }
      next(); render();
    },
  };

  document.addEventListener("click", e => {
    const pop = document.getElementById("brfPop");
    if (pop && (e.target.closest("[data-brfpopx]") || !e.target.closest(".brf-pop-in"))) { pop.remove(); if (!e.target.closest("[data-brfterm]")) return; }
    const tm = e.target.closest("[data-brfterm]"); if (tm) { e.preventDefault(); e.stopPropagation(); return B.termPop(tm.dataset.brfterm); }
    const t = e.target.closest("[data-hm],[data-brffull],[data-brftts]"); if (!t) return;
    if (t.dataset.hm) { B.setMode(t.dataset.hm); if (speaking) B.stop(); render(); scrollTo(0, 0); }
    else if (t.hasAttribute("data-brffull")) { const y = scrollY; full = !full; render(); if (!full) scrollTo(0, 0); else scrollTo(0, y); }
    else if (t.hasAttribute("data-brftts")) B.speak();
  });
  addEventListener("pagehide", () => { if (speaking) B.stop(); });
})();
