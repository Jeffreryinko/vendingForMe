/* hot.js — 시사 자판기 '트렌드' 코너. data/trends/*.json 을 읽어 나라별 검색어·영상·문서 순위를 보여줍니다.
   화면 본체(sisa/index.html)의 S·render·esc·ago·toast 를 그대로 씁니다. 보관·본 기록은 폰 저장소(vfm:sisa:hot). */
(() => {
  const KEY = "vfm:sisa:hot", BASE = "../data/trends/";
  const { S, render, esc, ago, toast } = window.SISA;
  const H = { idx: null, cc: null, data: {}, tab: "now", day: null, open: null, more: {}, reveal: {}, loading: false, err: null };
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } };
  const P = Object.assign({ cc: "KR", stars: [], seenAt: "", views: {} }, load());
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(P)); } catch {} };
  const flag = cc => String.fromCodePoint(...[...cc].map(c => 0x1F1E6 + c.charCodeAt(0) - 65));
  const dayOf = iso => new Date(new Date(iso).getTime() + 9 * 3600e3).toISOString().slice(0, 10);
  const today = () => dayOf(new Date().toISOString());
  const SRC_ORDER = ["google", "signal", "yahoojp", "baidu", "weibo", "reddit", "x", "yt", "ytfun", "wiki"];
  const ADULT = /(porn|sex|xxx|nude|hentai|onlyfans|야동|섹스|포르노|성인|エロ|성관계|rape|강간)/i;
  const css = `
  .hot-flags{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0 4px}.hot-flags::-webkit-scrollbar{display:none}
  .hot-flags .chip{display:inline-flex;align-items:center;gap:5px}
  .hot-world{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding-bottom:2px}.hot-world::-webkit-scrollbar{display:none}
  .hot-world .wchip{flex:none;text-decoration:none;border:1px solid var(--line);background:var(--accent-soft);color:var(--accent);border-radius:999px;padding:5px 11px;font-size:13px;font-weight:600;white-space:nowrap}
  .hot-world .wchip small{font-weight:400;opacity:.8;margin-left:4px}
  .hot-src{padding:0}.hot-h{display:flex;align-items:center;gap:8px;padding:10px 14px 6px}.hot-h b{font-size:14px}.hot-h .note{margin-left:auto}
  .hot-row{display:flex;gap:10px;align-items:flex-start;width:100%;text-align:left;background:none;border:0;padding:9px 14px;border-top:1px solid var(--line)}
  .hot-row .rank{width:18px;flex:none;padding-top:3px}.hot-row .hb{flex:1;min-width:0}.hot-row .ht{font-size:15px;font-weight:600;line-height:1.35;overflow-wrap:anywhere}
  .hot-row .ho{font-size:12px;color:var(--muted);display:block;overflow-wrap:anywhere}.hot-row .hm{font-size:11.5px;color:var(--muted);display:flex;gap:6px;flex-wrap:wrap;margin-top:2px}
  .hot-row.has-th .ht{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.hot-row.has-th .ho{display:none}
  .hot-row .hot-th{flex:none;width:88px;aspect-ratio:16/9;object-fit:cover;border-radius:8px;background:var(--line)}
  .hot-row .hn{flex:none;font-family:var(--f-mono);font-size:11px;color:var(--muted);padding-top:4px}
  .hot-x{padding:4px 14px 12px 42px;display:flex;flex-direction:column;gap:6px;border-top:1px dashed var(--line)}
  .hot-x a{font-size:13px;color:var(--ink);text-decoration:none;line-height:1.4}.hot-x a small{color:var(--muted)}
  .hot-x .btnrow{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}.hot-x .btn{padding:7px 10px;font-size:13px}
  .hot-blur{filter:blur(5px)}.hot-more{width:100%;background:none;border:0;border-top:1px solid var(--line);padding:9px;font-size:13px;color:var(--muted)}
  nav.tabs button[data-v="hot"].hasnew span{position:relative}nav.tabs button[data-v="hot"].hasnew span::after{content:"";position:absolute;top:-2px;right:-8px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
  .hot-star{display:flex;gap:10px;align-items:center;padding:10px 14px;border-top:1px solid var(--line)}.hot-star:first-child{border-top:0}.hot-star .hb{flex:1;min-width:0}
  .hot-star .ht{font-size:14.5px;font-weight:600}.hot-star button{background:none;border:0;color:var(--muted);font-size:13px}`;
  document.head.appendChild(Object.assign(document.createElement("style"), { textContent: css }));

  async function fetchJ(p) { const r = await fetch(BASE + p + "?t=" + Math.floor(Date.now() / 6e5)); if (!r.ok) throw new Error(r.status); return r.json(); }
  async function ensure() {
    if (H.loading) return; H.loading = true; H.err = null;
    try {
      if (!H.idx) { H.idx = await fetchJ("_index.json"); H.cc = H.cc || P.cc || "KR"; }
      const k = H.tab === "past" && H.day ? `hist/${H.cc}_${H.day}.json` : `${H.cc}.json`;
      if (!H.data[k]) { H.data[k] = await fetchJ(k); if (D) D.stale("sisa"); }
    } catch (e) { H.err = e.message; }
    H.loading = false;
    if (S.view === "hot") render();
    navDot();
  }
  function navDot() {
    const b = document.querySelector('nav.tabs button[data-v="hot"]'); if (!b || !H.idx) return;
    b.classList.toggle("hasnew", S.view !== "hot" && P.seenAt !== H.idx.at);
  }
  const cur = () => H.data[H.tab === "past" && H.day ? `hist/${H.cc}_${H.day}.json` : `${H.cc}.json`];
  const isStar = (cc, src, kw) => P.stars.some(s => s.cc === cc && s.src === src && s.kw === kw);
  function issueOf(it) {
    const st = (window.S && S.ed && S.ed.stories) || []; const keys = [it.ko, it.kw].filter(x => x && x.length >= 2).map(x => x.toLowerCase());
    return st.find(s => { const t = (s.title || "").toLowerCase(); return keys.some(k => t.includes(k) || (k.length >= 4 && k.includes(t.slice(0, 8).toLowerCase()) && t.length >= 8)); });
  }
  function logView(it, cc) { const d = today(); const v = P.views[d] = P.views[d] || []; const t = it.ko || it.kw; if (!v.includes(t)) { v.push(t); if (v.length > 60) v.shift(); } for (const k of Object.keys(P.views)) if (k < dayOf(new Date(Date.now() - 30 * 864e5).toISOString())) delete P.views[k]; save(); }

  function rowHtml(cc, src, it, i) {
    const id = `${src}|${i}`, open = H.open === id, hide = ADULT.test(it.kw + " " + (it.ko || "")) && !H.reveal[id];
    const isNew = it.since && (Date.now() - Date.parse(it.since)) < 6 * 3600e3, days = it.since ? Math.floor((Date.now() - Date.parse(it.since)) / 864e5) : 0;
    const tag = it.tag === "NEW" || isNew ? '<span class="pill acc">NEW</span>' : it.tag ? `<span class="pill">${esc(it.tag)}</span>` : days >= 1 ? `<span class="pill">${days}일째</span>` : "";
    const iss = issueOf(it);
    const main = hide ? `<span class="ht hot-blur">${esc(it.ko || it.kw)}</span><span class="ho">가려진 검색어 · 누르면 보여요</span>`
      : `<span class="ht">${esc(it.ko || it.kw)}</span>${it.ko && it.ko !== it.kw ? `<span class="ho">${esc(it.kw)}</span>` : ""}`;
    const meta = [it.sub ? esc(it.sub) : "", tag, iss ? `<button type="button" class="pill coin" data-hotiss="${esc(iss.id)}">이슈 보기</button>` : ""].filter(Boolean).join("");
    const yv = (src === "yt" || src === "ytfun") && !hide && window.VfmTrend && window.VfmTrend.ytId ? window.VfmTrend.ytId(it) : "";
    const x = open && !hide ? `<div class="hot-x">
        ${(it.news || []).map(n => `<a href="${esc(ku(n.u))}" target="_blank" rel="noopener">${esc(n.ko || n.t)} <small>· ${esc(n.s || "")}</small>${n.sn ? `<small style="display:block">${esc(n.sn)}</small>` : ""}</a>`).join("")}
        ${yv && window.VfmTrend.thumb ? window.VfmTrend.thumb(it) : ""}
        ${src === "yt" && (it.dko || it.desc) ? `<p class="note" style="color:var(--ink);margin:0">${esc(it.dko || it.desc)}</p>` : ""}
        ${src === "yt" && (it.capko || it.cap) ? `<p class="note" style="margin:0"><b>자막</b> ${esc((it.capko || it.cap).slice(0, 300))}…</p>` : ""}
        <div class="btnrow"><a class="btn" href="${esc(it.url)}" target="_blank" rel="noopener">${src === "yt" ? "유튜브에서 보기" : src === "wiki" ? "문서 열기" : "검색 결과"}</a>
          <button type="button" class="btn ${isStar(cc, src, it.kw) ? "on" : ""}" data-hotstar="${id}">${isStar(cc, src, it.kw) ? "★ 보관됨" : "☆ 보관"}</button>
          <button type="button" class="btn" data-hotshare="${id}">공유</button></div></div>` : "";
    return `<button type="button" class="hot-row${yv ? " has-th" : ""}" data-hotrow="${id}" ${hide ? `data-hotreveal="${id}"` : ""}><span class="rank">${i + 1}</span>${yv ? `<img class="hot-th" src="https://i.ytimg.com/vi/${yv}/mqdefault.jpg" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">` : ""}<span class="hb">${main}<span class="hm">${meta}</span></span>${it.n ? `<span class="hn">${esc(it.n)}</span>` : ""}</button>${x}`;
  }
  function srcCard(cc, src, b) {
    const items = b.items || [], n = H.more[src] ? 20 : 5, more = items.length > 5;
    const st = !b.ok && b.stale ? `<span class="pill warn">${ago(b.at)} 자료</span>` : !b.ok ? `<span class="pill bad">${esc(b.err === "키 필요" ? "유튜브 키 필요" : "지금 못 가져옴")}</span>` : "";
    return `<div class="card hot-src stack"><div class="hot-h"><b>${esc(b.name)}</b>${st}<a class="note" href="${esc(b.home)}" target="_blank" rel="noopener">출처 ↗</a></div>
      ${items.length ? items.slice(0, n).map((it, i) => rowHtml(cc, src, it, i)).join("") : `<p class="note" style="padding:0 14px 12px">${b.err === "키 필요" ? "유튜브 API 키를 넣으면 나라별 인기 영상이 나와요 (무료)." : "자료가 없어요."}</p>`}
      ${more ? `<button type="button" class="hot-more" data-hotmore="${src}">${H.more[src] ? "접기" : `더 보기 (${Math.min(20, items.length)}개)`}</button>` : ""}</div>`;
  }
  function view() {
    if (!H.idx || !cur()) { ensure(); return `<p class="lead">트렌드</p><p class="note">${H.err ? "트렌드 자료를 아직 못 불러왔어요 · " + esc(H.err) : "불러오는 중…"}</p>`; }
    if (S.view === "hot" && P.seenAt !== H.idx.at) { P.seenAt = H.idx.at; save(); navDot(); }
    const d = cur(), idx = H.idx;
    const seg = `<div class="chips" role="tablist">${[["now", "지금"], ["past", "지난 날"], ["star", `내 보관함${P.stars.length ? " " + P.stars.length : ""}`]].map(([k, l]) => `<button type="button" class="chip" data-hottab="${k}" aria-pressed="${H.tab === k}">${l}</button>`).join("")}</div>`;
    if (H.tab === "star") return `<p class="lead">트렌드</p>${seg}${P.stars.length ? `<div class="list">${P.stars.slice().reverse().map((s, i) => `<div class="hot-star"><span>${flag(s.cc)}</span><span class="hb"><span class="ht">${esc(s.ko || s.kw)}</span><span class="note">${esc(s.srcName)} · ${esc(s.at.slice(0, 10))}${s.ko && s.ko !== s.kw ? " · " + esc(s.kw) : ""}</span></span><a class="note" href="${esc(s.url)}" target="_blank" rel="noopener">열기</a><button type="button" data-hotunstar="${P.stars.length - 1 - i}">지우기</button></div>`).join("")}</div>` : '<p class="note">검색어를 펼쳐 ☆ 보관을 누르면 여기 영구 보관돼요. 설정 → 내보내기로 백업할 수 있어요.</p>'}`;
    const world = idx.world && idx.world.length && H.tab === "now" ? `<div class="stack"><h2 class="sec">세계가 같이 찾는 것</h2><div class="hot-world">${idx.world.map(w => `<a class="wchip" href="https://www.google.com/search?q=${encodeURIComponent(w.kw)}" target="_blank" rel="noopener">${esc(w.ko)}<small>${w.cc.map(flag).join("")}</small></a>`).join("")}</div></div>` : "";
    const flags = `<div class="hot-flags">${idx.countries.map(([cc, nm]) => `<button type="button" class="chip" data-hotcc="${cc}" aria-pressed="${cc === H.cc}">${flag(cc)} ${esc(nm)}</button>`).join("")}</div>`;
    const days = H.tab === "past" ? `<div class="chips">${(idx.days || []).slice().reverse().filter(x => x !== today()).map(x => `<button type="button" class="chip" data-hotday="${x}" aria-pressed="${x === H.day}">${x.slice(5).replace("-", "/")}</button>`).join("") || '<span class="note">아직 지난 날 자료가 없어요 (내일부터 쌓여요)</span>'}</div>` : "";
    const msw = D && H.tab === "now" ? D.modeSwitch("sisa-hot", () => render()) : "";
    if (D && H.tab === "now" && D.mode("sisa-hot") === "deck") {
      const dc = P.deckCc || "ALL";
      if (dc === "ALL") ensureAll();
      const dflags = `<div class="hot-flags"><button type="button" class="chip" data-hotdeck="ALL" aria-pressed="${dc === "ALL"}">🌐 모든 나라 랜덤</button>${idx.countries.map(([cc, nm]) => `<button type="button" class="chip" data-hotdeck="${cc}" aria-pressed="${cc === dc}">${flag(cc)} ${esc(nm)}</button>`).join("")}</div>`;
      if (dc !== "ALL" && !H.data[`${dc}.json`]) { fetchJ(`${dc}.json`).then(x => { H.data[`${dc}.json`] = x; render(); }).catch(() => {}); return `<p class="lead">트렌드</p>${seg}${msw}${dflags}<p class="note">불러오는 중…</p>`; }
      const dk = deckOf(dc); const k0 = dk.curKey(), x0 = k0 && dk.map[k0];
      if (x0 && x0.src === "wiki" && T.WK[x0.it.url] === undefined) T.wikiFor(x0.it.url).then(() => { if (dk.curKey() === k0) dk.paint(); });
      return `<p class="lead">트렌드</p>${seg}${msw}${dflags}<p class="note">${dc === "ALL" ? "22개국 검색어·영상·레딧·밈을 모두 섞어서" : esc((H.data[`${dc}.json`] || {}).name || dc) + "의 검색어·영상·레딧을"} 한 장씩 · ${ago(idx.at)} 갱신 · 본 것은 다시 안 나와요</p>${dk.html()}`;
    }
    const srcs = Object.entries(d.src || {}).sort((a, b) => SRC_ORDER.indexOf(a[0]) - SRC_ORDER.indexOf(b[0]));
    const broken = Object.keys(idx.broken || {}).length ? `<p class="note">3일 넘게 못 가져오는 출처 ${Object.keys(idx.broken).length}곳 — 설정 시트에서 볼 수 있어요.</p>` : "";
    return `<p class="lead">트렌드</p><p class="note">${d.name} · ${ago(d.at)} 갱신 · 3시간마다 로봇이 모아요 · 순위를 누르면 펼쳐져요</p>${seg}${msw}${world}${flags}${days}
      ${srcs.map(([k, b]) => srcCard(d.cc, k, b)).join("")}${broken}
      <p class="note">구글·위키백과·유튜브는 공식 자료, 나머지는 민간 집계 사이트(출처 ↗)에서 가져와요. 틱톡·페이스북·인스타그램은 순위를 공개하지 않아 없어요.</p>`;
  }
  /* ── 넘겨보기: 한 나라의 검색어·영상·문서를 한 장씩 (안 본 것만) ── */
  const D = window.VfmDeck || null;
  const tKey = (cc, src, it) => `t:${cc}:${src}:${it.kw}`;
  const ku = (u, l) => D ? D.koUrl(u, l) : u;
  const T = window.VfmTrend;
  // 22개국을 한꺼번에 받아 둠 (모든 나라 랜덤 넘겨보기)
  let allP = null;
  function ensureAll() {
    if (!allP) allP = Promise.all((H.idx.countries || []).map(([cc]) => H.data[`${cc}.json`] ? null : fetchJ(`${cc}.json`).then(d => { H.data[`${cc}.json`] = d; }).catch(() => {})))
      .then(() => { if (D) D.stale("sisa"); if (S.view === "hot") render(); });
    return allP;
  }
  const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  function cardOf(cc, x) {
    const d = H.data[`${cc}.json`] || {}, iss = issueOf(x.it);
    return { key: tKey(cc, x.src, x.it), title: x.it.ko || x.it.kw, url: ["yt", "ytfun", "wiki", "reddit"].includes(x.src) ? x.it.url : location.href.split("#")[0] + "#hot",
      shareText: `${flag(cc)} ${d.name || cc} ${x.srcName} ${x.rank + 1}위 · ${x.it.ko || x.it.kw}`, src: x.src, it: x.it, cc,
      html: () => T.card({ cc, cname: d.name || cc, src: x.src, srcName: x.srcName, it: x.it, rank: x.rank, country: d, extra: iss ? `<button type="button" class="vdk-more" data-hotiss="${esc(iss.id)}">관련 이야기: ${esc(iss.title || "")} ›</button>` : "" }) };
  }
  function deckOf(cc) {
    return D.create({ id: "sisa-hot-" + cc, app: "sisa", emptyTitle: "트렌드 자료가 없어요",
      items: () => {
        if (cc === "ALL") {                                          // 모든 나라·모든 출처를 완전히 섞어서
          const out = [];
          (H.idx.countries || []).forEach(([c]) => { const d = H.data[`${c}.json`]; if (d) T.items(d).forEach(x => out.push(cardOf(c, x))); });
          (H.idx.memes || []).forEach((it, r) => out.push({ key: `t:WW:memes:${it.kw}`, title: it.ko || it.kw, url: it.url, shareText: it.ko || it.kw, src: "memes", it, cc: "WW",
            html: () => T.card({ cc: "WW", cname: "세계 밈", src: "memes", srcName: "레딧 밈", it, rank: r }) }));
          return shuffle(out);
        }
        const d = H.data[`${cc}.json`]; if (!d) return [];
        const by = {}; T.items(d).forEach(x => (by[x.rank] = by[x.rank] || []).push(x));   // 출처마다 1위끼리, 2위끼리… 번갈아
        return Object.keys(by).sort((a, b) => a - b).flatMap(r => by[r]).map(x => cardOf(cc, x));
      },
      onShow(x) { if (x.src === "wiki" && T.WK[x.it.url] === undefined) T.wikiFor(x.it.url).then(() => { const dk = D.get("sisa-hot-" + cc); if (dk && dk.curKey() === x.key) dk.paint(); }); if (x.it) logView(x.it, x.cc); },
      onList() { try { localStorage.setItem("vfm:mode:sisa-hot", '"list"'); } catch (e) { } render(); } });
  }
  function itemOf(id) { const [src, i] = id.split("|"); const d = cur(); const b = d && d.src[src]; return b && { it: b.items[+i], src, b, cc: d.cc }; }
  document.addEventListener("click", e => {
    const t = e.target.closest("[data-hotdeck],[data-hotcc],[data-hottab],[data-hotday],[data-hotrow],[data-hotmore],[data-hotstar],[data-hotunstar],[data-hotshare],[data-hotiss],[data-hotreveal]"); if (!t) return;
    const d = t.dataset;
    if (d.hotiss) { e.stopPropagation(); (window.SISA && SISA.replaceTo ? SISA.replaceTo("#issue-" + d.hotiss) : location.replace("#issue-" + d.hotiss)); return; }
    if (d.hotdeck) { P.deckCc = d.hotdeck; save(); render(); const on = document.querySelector(`[data-hotdeck="${d.hotdeck}"]`); if (on) on.scrollIntoView({ block: "nearest", inline: "center" }); return; }
    if (d.hotcc) { H.cc = d.hotcc; P.cc = d.hotcc; save(); H.open = null; H.more = {}; render(); ensure(); return; }
    if (d.hottab) { H.tab = d.hottab; H.open = null; if (H.tab === "past" && !H.day) H.day = ((H.idx && H.idx.days) || []).filter(x => x !== today()).slice(-1)[0] || null; render(); ensure(); return; }
    if (d.hotday) { H.day = d.hotday; H.open = null; render(); ensure(); return; }
    if (d.hotmore) { H.more[d.hotmore] = !H.more[d.hotmore]; render(); return; }
    if (d.hotreveal) { H.reveal[d.hotreveal] = true; render(); return; }
    if (d.hotrow) { H.open = H.open === d.hotrow ? null : d.hotrow; const o = itemOf(d.hotrow); if (H.open && o) { logView(o.it, o.cc); if (D) D.Seen.add("sisa", tKey(o.cc, o.src, o.it)); } render(); return; }
    if (d.hotstar) { const o = itemOf(d.hotstar); if (!o) return; const i = P.stars.findIndex(s => s.cc === o.cc && s.src === o.src && s.kw === o.it.kw);
      if (i >= 0) { P.stars.splice(i, 1); toast("보관함에서 뺐어요"); } else { P.stars.push({ cc: o.cc, src: o.src, srcName: o.b.name, kw: o.it.kw, ko: o.it.ko || "", url: o.it.url, at: new Date().toISOString() }); toast("영구 보관했어요 · 내 보관함"); }
      save(); render(); return; }
    if (d.hotunstar !== undefined) { P.stars.splice(+d.hotunstar, 1); save(); render(); return; }
    if (d.hotshare) { const o = itemOf(d.hotshare); if (!o) return; const top = o.b.items.slice(0, 5).map((x, i) => `${i + 1}. ${x.ko || x.kw}${x.ko && x.ko !== x.kw ? ` (${x.kw})` : ""}`).join("\n");
      const text = `${flag(o.cc)} ${cur().name} · ${o.b.name} TOP5\n${top}\n— ${new Date(o.b.at).toLocaleString("ko-KR", { timeZone: "Asia/Seoul", month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit" })} 기준 · 자판기\n${location.href.split("#")[0]}#hot`;
      if (navigator.share) navigator.share({ text }).catch(() => {}); else navigator.clipboard?.writeText(text).then(() => toast("복사했어요 — 카톡 등에 붙여넣기")); return; }
  });
  window.HOT = { view, ensure, dayLine(day) { const v = P.views[day] || []; return v.length ? `<p class="note" style="color:var(--ink)">본 트렌드: ${v.map(esc).join(" / ")}</p>` : ""; } };
  setTimeout(() => { ensure(); }, 1500);                       // 첫 화면 뒤에 조용히 받아서 '새 트렌드' 점 표시
  setInterval(() => { H.idx = null; H.data = {}; ensure(); }, 30 * 60e3);
})();
