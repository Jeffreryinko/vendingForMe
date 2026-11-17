/* 종이 자판기 — 다른 자판기 세 곳도 이북리더기판으로 (ebook_build.js 가 불러요, 토큰 0)
   · 이야기 자판기(vfm-story): 이야기 · 역사 · 뇌 · 책
   · 사람 자판기(vfm-mind): 맨탈 · (배댓은 이 저장소 data/baedat)
   · 뷰티·폰게임 자판기(vfm-consumer): 뷰티 · 게임
   저장소들은 VFM_EXT 폴더(기본 /tmp/ext) 아래 vfm-story · vfm-mind · vfm-consumer 로 받아 둬요 (ebook.yml 이 받음).
   읽기만 하고 그 저장소는 고치지 않아요. 움직이는 것(3D 뇌 지도·선택 놀이·진도 기록)은 글로 바꿨어요. */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");

module.exports = function (H) {
  const { rd, ls, esc, inl, md, sec, ul, ext, when, num, page, paged, comic, quizHtml, briefings, bgLinks, learnInfo, now } = H;
  const EXT = process.env.VFM_EXT || "/tmp/ext";
  const X = (repo, p) => path.join(EXT, repo, p);
  const has = repo => fs.existsSync(path.join(EXT, repo));
  const runJs = (files, pre) => {
    const w = Object.assign({ console: { warn() {}, log() {}, error() {} }, document: { createElement: () => ({ style: {} }), head: { appendChild() {} } }, addEventListener() {} }, pre || {});
    w.window = w; const c = vm.createContext(w);
    for (const f of files) { try { vm.runInContext(fs.readFileSync(f, "utf8"), c, { filename: f }); } catch (e) { console.warn("[ebook+] 읽기 실패", f, e.message); } }
    return w;
  };
  /* 문단 목록. {e:1,t} 는 결말 문단 → 접어 두고 '결말 펼치기' */
  const paras = a => { let h = "", end = ""; for (const x of (Array.isArray(a) ? a : a ? [a] : [])) { if (x && typeof x === "object") { if (x.e) end += md(x.t); else h += md(x.t || x.text || ""); } else h += md(x); }
    return h + (end ? `<details class="end"><summary>결말 펼치기</summary>${end}</details>` : ""); };
  const slug = s => String(s).replace(/[^\w-]/g, c => "_" + c.charCodeAt(0).toString(16));
  const groups = [];
  const today = `${String(now.getUTCMonth() + 1).padStart(2, "0")}-${String(now.getUTCDate()).padStart(2, "0")}`;

  /* ═════════ 이야기 자판기 ═════════ */
  if (has("vfm-story")) {
    const items = [];
    try { items.push(buildIyagi()); } catch (e) { console.warn("[ebook+] 이야기", e.message); }
    try { items.push(buildHist()); } catch (e) { console.warn("[ebook+] 역사", e.message); }
    try { items.push(buildBrain()); } catch (e) { console.warn("[ebook+] 뇌", e.message); }
    try { items.push(buildBook()); } catch (e) { console.warn("[ebook+] 책", e.message); }
    groups.push({ h: "이야기 자판기", items: items.filter(Boolean) });
  }
  /* ═════════ 사람 자판기 ═════════ */
  {
    const items = [];
    if (has("vfm-mind")) try { items.push(buildMental()); } catch (e) { console.warn("[ebook+] 맨탈", e.message); }
    try { items.push(buildBaedat()); } catch (e) { console.warn("[ebook+] 배댓", e.message); }
    if (items.filter(Boolean).length) groups.push({ h: "사람 자판기", items: items.filter(Boolean) });
  }
  /* ═════════ 뷰티·게임 ═════════ */
  if (has("vfm-consumer")) {
    const items = [];
    for (const [ind, label] of [["beauty", "뷰티"], ["game", "게임"]]) try { items.push(buildConsumer(ind, label)); } catch (e) { console.warn("[ebook+]", label, e.message); }
    groups.push({ h: "뷰티·폰게임 자판기", items: items.filter(Boolean) });
  }
  /* ═════════ 브로제이 영업 허브 (data/hub/hub.json, 원가 뺀 판) ═════════ */
  try { const hub = require("./ebook_hub.js")(H, { data: rd("data/hub/hub.json"), B: "hub/", label: "영업 허브", at: "2026년 11월 17일" }); if (hub) groups.push({ h: "브로제이", items: [hub] }); }
  catch (e) { console.warn("[ebook+] 영업 허브", e.message); }
  return groups;

  /* ── 이야기: 다시 쓴 이야기(깊이별) + 위키 서가 ── */
  function buildIyagi() {
    const all = new Map(), add = o => { if (o && o.id && o.title && !all.has(o.id)) all.set(o.id, o); };
    const html = fs.readFileSync(X("vfm-story", "iyagi/index.html"), "utf8"), i0 = html.indexOf("const SEED=");
    if (i0 >= 0) { const i1 = html.indexOf("\n];", i0); const w = runJs([]); vm.runInContext("window.SEED=" + html.slice(i0 + 11, i1 + 2), vm.createContext(w)); (w.SEED || []).forEach(add); }
    const cl = ls(X("vfm-story", "iyagi")).filter(f => /^claude-\d+\.js$/.test(f)).map(f => X("vfm-story", "iyagi/" + f));
    (runJs(cl).IYAGI_ADD || []).forEach(add);
    (rd("data/iyagi/claude_stories.json") || {}).items?.forEach(add);
    (rd(X("vfm-story", "data/iyagi/stories/_index.json")) || []).forEach(add);
    const list = [...all.values()], B = "story/", C = [[B + "index.html", "이야기"]];
    const DN = { d1: "짧게", d2: "보통", d3: "길게", d4: "아주 길게" };
    list.forEach((o, i) => {
      const ds = Object.keys(o.depths || {}).sort(), base = `${B}s/${slug(o.id)}`, nextStory = list[i + 1] ? [`${B}s/${slug(list[i + 1].id)}.html`, "다음 이야기"] : null;
      const meta = [o.kind, o.region, o.era].filter(Boolean).map(esc).join(" · ");
      page(`${base}.html`, { title: o.title, crumbs: C, sub: `${esc(o.orig || "")}${meta ? " · " + meta : ""}`,
        body: `<p class="lead">${inl(o.hook || "")}</p>${o.warn ? `<p class="note">주의: ${inl(o.warn)}</p>` : ""}<h2>얼마나 읽을까요</h2><ul class="list">${ds.map(d => `<li><a href="@${base}-${d}.html">${DN[d] || d} 읽기</a> <small>약 ${esc(o.depths[d].min)}분</small></li>`).join("")}</ul>` +
          (o.tags && o.tags.length ? `<p class="sub">${o.tags.map(esc).join(" · ")}</p>` : "") + (o.form ? `<p class="note">${esc(o.form)}${o.basis ? " · " + esc(o.basis) : ""}</p>` : ""),
        prev: i > 0 ? [`${B}s/${slug(list[i - 1].id)}.html`, "앞 이야기"] : null, next: ds.length ? [`${base}-${ds[0]}.html`, `${DN[ds[0]]} 읽기`] : nextStory, up: [B + "index.html", "이야기 목록"] });
      ds.forEach((d, k) => {
        const dp = o.depths[d], last = k === ds.length - 1;
        const tail = sec("함께 알면 좋은 것", ul(o.parts, p => `<b>${esc(p.t)}</b> — ${inl(p.b)}`)) + sec("더 생각해 볼 것", ul(o.beyond, p => `<b>${esc(p.t)}</b> — ${inl(p.b)}`), "box") +
          (o.limit ? `<p class="note">${inl(o.limit)}</p>` : "") + sec("출처", ul(o.sources, s => ext(s.u, s.t)));
        page(`${base}-${d}.html`, { title: o.title, crumbs: C.concat([[`${base}.html`, o.title]]), sub: `${DN[d] || d} · 약 ${esc(dp.min)}분`,
          body: paras(dp.body) + (dp.end ? md(dp.end) : "") + tail,
          prev: k > 0 ? [`${base}-${ds[k - 1]}.html`, DN[ds[k - 1]] + " 판"] : [`${base}.html`, "처음"], next: !last ? [`${base}-${ds[k + 1]}.html`, `더 길게 (${DN[ds[k + 1]]})`] : nextStory, up: [`${base}.html`, "이야기 처음"] });
      });
    });
    /* 위키 서가 */
    const wi = rd(X("vfm-story", "data/iyagi/wiki/_index.json")) || [], wl = [];
    for (const x of wi) { const d = rd(X("vfm-story", `data/iyagi/wiki/${x.id}.json`)); if (d && ((d.lead || []).length || (d.secs || []).length)) wl.push(d); }
    const WG = new Map(); for (const d of wl) { const g = d.g || "그 밖"; if (!WG.has(g)) WG.set(g, []); WG.get(g).push(d); }
    const order = [...WG.values()].flat();
    order.forEach((d, i) => page(`${B}w/${d.id}.html`, { title: d.t || d.o, crumbs: C.concat([[`${B}wiki.html`, "위키 서가"]]), sub: [d.g, d.r, d.e].filter(Boolean).map(esc).join(" · "),
      body: paras(d.lead) + (d.secs || []).map(s => `<h2>${esc(s.h)}</h2>${paras(s.p)}`).join("") + `<p class="note">글: ${ext(d.u, "위키백과")} (CC BY-SA 4.0)${d.l && d.l !== "ko" ? " · 기계번역" : ""}</p>`,
      prev: order[i - 1] ? [`${B}w/${order[i - 1].id}.html`, "앞 글"] : null, next: order[i + 1] ? [`${B}w/${order[i + 1].id}.html`, "다음 글"] : null, up: [`${B}wiki.html`, "서가"] }));
    page(`${B}wiki.html`, { title: "위키 서가", crumbs: C, sub: `위키백과 이야기 문서 ${wl.length}편`,
      body: [...WG].map(([g, l]) => `<h2>${esc(g)} <small>${l.length}편</small></h2><ul class="list">${l.map(d => `<li><a href="@${B}w/${d.id}.html">${esc(d.t || d.o)}</a>${d.r ? ` <small>${esc(d.r)}</small>` : ""}</li>`).join("")}</ul>`).join(""), up: [B + "index.html", "이야기"] });
    const G = new Map(); for (const o of list) { const g = o.group || "그 밖"; if (!G.has(g)) G.set(g, []); G.get(g).push(o); }
    page(`${B}index.html`, { title: "이야기", crumbs: [], sub: `다시 쓴 이야기 ${list.length}편 · 짧게부터 길게까지 골라 읽어요`, up: ["index.html", "처음"],
      body: `<p><a class="btn" href="@${B}wiki.html">위키 서가 ${wl.length}편 ›</a></p>` + [...G].map(([g, l]) => `<h2>${esc(g)} <small>${l.length}편</small></h2><ul class="list">${l.map(o => `<li><a href="@${B}s/${slug(o.id)}.html">${esc(o.title)}</a><br><small>${esc(o.orig || "")}${o.region ? " · " + esc(o.region) : ""}</small></li>`).join("")}</ul>`).join("") });
    return [B + "index.html", "이야기", `다시 쓴 이야기 ${list.length}편 · 위키 서가 ${wl.length}편`];
  }

  /* ── 역사: 세계사 한 줄로 · 사건 이야기 · 역사 속 오늘 · 많이 읽는 문서 ── */
  function buildHist() {
    const B = "hist/", C = [[B + "index.html", "역사"]], out = [];
    /* 세계사 한 줄로 */
    const ts = []; runJs(ls(X("vfm-story", "history")).filter(f => /^tongsa-\d+\.js$/.test(f)).map(f => X("vfm-story", "history/" + f)), { VFM_TS_ADD: l => ts.push(...l) });
    ts.sort((a, b) => a.n - b.n);
    ts.forEach((c, i) => page(`${B}ts/${c.id}.html`, { title: `${c.n}. ${c.t}`, crumbs: C.concat([[`${B}ts.html`, "세계사 한 줄로"]]), sub: esc(c.yrs || ""),
      body: `<p class="lead">${inl(c.sum || "")}</p>` + (c.secs || []).map(s => `<h2>${esc(s[0])}</h2>${md(s[1])}`).join("") + sec("나오는 사람", ul(c.people, p => `<b>${esc(p[0])}</b> — ${inl(p[1])}`)) + (c.q ? sec("생각해 볼 질문", md(c.q), "box") : ""),
      prev: ts[i - 1] ? [`${B}ts/${ts[i - 1].id}.html`, "앞 장"] : null, next: ts[i + 1] ? [`${B}ts/${ts[i + 1].id}.html`, "다음 장"] : null, up: [`${B}ts.html`, "차례"] }));
    if (ts.length) page(`${B}ts.html`, { title: "세계사 한 줄로", crumbs: C, sub: `고대 문명부터 오늘까지 ${ts.length}장`, body: `<ol class="list">${ts.map(c => `<li><a href="@${B}ts/${c.id}.html">${esc(c.t)}</a><br><small>${esc(c.yrs || "")}</small></li>`).join("")}</ol>`, up: [B + "index.html", "역사"] });
    /* 사건 이야기 (선택 놀이 → 고른 답은 '답 보기'로) */
    const ei = rd(X("vfm-story", "data/history/editorial/index.json")) || {}, P = ei.programs || {};
    const eps = ls(X("vfm-story", "data/history/editorial/episodes")).map(f => rd(X("vfm-story", "data/history/editorial/episodes/" + f))).filter(e => e && e.scenes);
    const scene = s => {
      let h = s.h ? `<h2>${esc(s.h)}</h2>` : (s.cue ? `<h3>${esc(s.cue)}</h3>` : "");
      if (s.note) h += `<p class="note">${inl(s.note)}</p>`;
      if (s.text) h += md(s.text);
      if (s.items) h += ul(s.items, it => typeof it === "string" ? inl(it) : `<b>${esc(it.label || it.t || it.h || "")}</b> ${inl(it.text || it.b || "")}`);
      if (s.tabs) h += s.tabs.map(t => `<h4>${esc(t.label || t.t || t.h || "")}</h4>${md(t.text || t.b || "")}${t.items ? ul(t.items, it => typeof it === "string" ? inl(it) : `<b>${esc(it.label || it.t || "")}</b> ${inl(it.text || it.b || "")}`) : ""}`).join("");
      if (s.type === "choice") h += `<div class="box"><p><b>${inl(s.q || "")}</b></p>${ul(s.opts, o => `${esc(o.label)}`)}<details><summary>생각해 보고 펼치기</summary>${ul(s.opts, o => `<b>${esc(o.label)}</b> — ${inl(o.reply || "")}`)}</details></div>`;
      return h;
    };
    eps.forEach((e, i) => page(`${B}ep/${e.id}.html`, { title: e.title, crumbs: C.concat([[`${B}ep.html`, "사건 이야기"]]), sub: [P[e.program] && P[e.program].name, e.place, e.when, e.mins ? `${e.mins}분` : ""].filter(Boolean).map(esc).join(" · "),
      body: `<p class="lead">${inl(e.hook || "")}</p>` + e.scenes.map(scene).join("") + sec("출처", ul(e.sources, s => typeof s === "string" ? inl(s) : ext(s.u || s.url, s.t || s.title))),
      prev: eps[i - 1] ? [`${B}ep/${eps[i - 1].id}.html`, "앞 이야기"] : null, next: eps[i + 1] ? [`${B}ep/${eps[i + 1].id}.html`, "다음 이야기"] : null, up: [`${B}ep.html`, "목록"] }));
    if (eps.length) page(`${B}ep.html`, { title: "사건 이야기", crumbs: C, sub: "고르는 장면은 생각해 본 뒤 펼쳐 보세요", body: `<ul class="list">${eps.map(e => `<li><a href="@${B}ep/${e.id}.html">${esc(e.title)}</a><br><small>${esc((P[e.program] || {}).name || "")} · ${inl(e.hook || "")}</small></li>`).join("")}</ul>`, up: [B + "index.html", "역사"] });
    /* 많이 읽는 문서 — 한국어 위키백과 역사 글 (첫 화면 목록에 나온 것만) */
    const top = rd(X("vfm-story", "data/history/top.json")) || {}, want = new Map();
    for (const k of ["all", "korea", "recent", "back", "pron"]) for (const r of top[k] || []) if (!want.has(r[0])) want.set(r[0], r);
    const where = new Map(), pd = X("vfm-story", "data/history/pages");
    for (const dd of ls(pd)) for (const f of ls(path.join(pd, dd))) { const id = f.slice(0, -5); if (want.has(id)) where.set(id, path.join(pd, dd, f)); }
    const arts = []; for (const [id] of want) { const p = where.get(id); if (!p) continue; const a = rd(p); if (a) arts.push(a); }
    const yr = y => y == null || y === "None" ? "" : (+y < 0 ? `기원전 ${-y}년` : `${y}년`);
    const artSet = new Set(arts.map(a => a.id));
    arts.forEach((a, i) => page(`${B}a/${a.id}.html`, { title: a.title, crumbs: C.concat([[`${B}a.html`, "많이 읽는 문서"]]), sub: [a.desc, yr(a.y)].filter(Boolean).map(esc).join(" · "),
      body: md(a.lead || a.one || "") + (a.secs || []).map(s => `${(s.l || 2) <= 2 ? "<h2>" : "<h3>"}${esc(s.h)}${(s.l || 2) <= 2 ? "</h2>" : "</h3>"}${md(s.t)}`).join("") + `<p class="note">글: ${ext(a.src && a.src.url, "한국어 위키백과")} (CC BY-SA 4.0)${a.full === false ? " · 앞부분만 받아 둔 글" : ""}</p>`,
      prev: arts[i - 1] ? [`${B}a/${arts[i - 1].id}.html`, "앞 문서"] : null, next: arts[i + 1] ? [`${B}a/${arts[i + 1].id}.html`, "다음 문서"] : null, up: [`${B}a.html`, "목록"] }));
    if (arts.length) paged(`${B}a`, "많이 읽는 문서", C, arts, 25, a => `<a href="@${B}a/${a.id}.html">${esc(a.title)}</a> <small>${esc([a.desc, yr(a.y)].filter(Boolean).join(" · "))}</small>`);
    /* 역사 속 오늘 — 365일 다 만들고, 첫 화면은 오늘 날짜로 */
    const days = ls(X("vfm-story", "data/history/days")).filter(f => /^\d\d-\d\d\.json$/.test(f)).map(f => f.slice(0, 5));
    days.forEach((d, i) => { const l = rd(X("vfm-story", `data/history/days/${d}.json`)) || [];
      page(`${B}d/${d}.html`, { title: `역사 속 ${+d.slice(0, 2)}월 ${+d.slice(3)}일`, crumbs: C, sub: `${l.length}가지 일`,
        body: `<ol class="list tl">${l.map(x => `<li><span class="y">${esc(yr(x.y))}</span> ${x.id && artSet.has(x.id) ? `<a href="@${B}a/${x.id}.html">${esc(x.t)}</a>` : esc(x.t)}</li>`).join("")}</ol>`,
        prev: days[i - 1] ? [`${B}d/${days[i - 1]}.html`, "어제"] : null, next: days[i + 1] ? [`${B}d/${days[i + 1]}.html`, "내일"] : null, up: [B + "index.html", "역사"] }); });
    page(`${B}index.html`, { title: "역사", crumbs: [], sub: "세계사 통사 · 사건 이야기 · 역사 속 오늘", up: ["index.html", "처음"],
      body: `<ul class="list home">${days.includes(today) ? `<li><a href="@${B}d/${today}.html">역사 속 오늘</a><br><small>${+today.slice(0, 2)}월 ${+today.slice(3)}일에 있었던 일</small></li>` : ""}` +
        (ts.length ? `<li><a href="@${B}ts.html">세계사 한 줄로</a><br><small>고대 문명부터 오늘까지 ${ts.length}장</small></li>` : "") +
        (eps.length ? `<li><a href="@${B}ep.html">사건 이야기</a><br><small>${eps.length}편 · 그때 당신이라면, 수상한 문서함 …</small></li>` : "") +
        (arts.length ? `<li><a href="@${B}a.html">많이 읽는 문서</a><br><small>한국어 위키백과 역사 글 ${arts.length}편</small></li>` : "") + `</ul>` });
    return [B + "index.html", "역사", `세계사 ${ts.length}장 · 사건 이야기 ${eps.length}편 · 문서 ${arts.length}편 · 역사 속 오늘`];
  }

  /* ── 뇌: 부위 52곳 · 유명한 실험·사례 · 소식 ── */
  function buildBrain() {
    const B = "brain/", C = [[B + "index.html", "뇌"]];
    const R = rd(X("vfm-story", "data/brain/regions.json")) || {}, regs = R.regions || [], byId = new Map(regs.map(r => [r.id, r]));
    const rlink = id => byId.has(id) ? `<a href="@${B}r/${id}.html">${esc(byId.get(id).ko)}</a>` : esc(id);
    regs.forEach((r, i) => page(`${B}r/${r.id}.html`, { title: r.ko, crumbs: C, sub: [r.en, (r.alt || []).join("·")].filter(Boolean).map(esc).join(" · "),
      body: `<p class="lead">${inl(r.one || "")}</p>` + sec("하는 일", ul(r.role, inl)) + sec("비유하면", md(r.like), "box") + sec("어디쯤", md(r.where)) + sec("다치면", md(r.hurt), "mis") + sec("이름의 뜻", md(r.origin)) +
        ((r.pair || []).length ? sec("함께 보면 좋은 곳", `<p class="chips">${r.pair.map(rlink).join(" · ")}</p>`) : ""),
      prev: regs[i - 1] ? [`${B}r/${regs[i - 1].id}.html`, regs[i - 1].ko] : null, next: regs[i + 1] ? [`${B}r/${regs[i + 1].id}.html`, regs[i + 1].ko] : null, up: [B + "index.html", "뇌"] }));
    const st = (rd(X("vfm-story", "data/brain/stories.json")) || {}).items || [];
    const exp = runJs(ls(X("vfm-story", "brain")).filter(f => /^exp(-\d+)?\.js$/.test(f)).map(f => X("vfm-story", "brain/" + f))).BRAIN_EXP || [];
    const cases = exp.concat(st);
    cases.forEach((c, i) => page(`${B}c/${slug(c.id)}.html`, { title: c.title, crumbs: C.concat([[`${B}cases.html`, "실험·사례"]]), sub: [c.book, c.ch, c.field].filter(Boolean).map(esc).join(" · "),
      body: (c.who ? `<p class="tag">${esc(c.who)}</p>` : "") + md(c.story) + sec("이 이야기가 알려 주는 것", md(c.insight), "box") + ((c.rs || []).length ? sec("관련 부위", `<p class="chips">${c.rs.map(rlink).join(" · ")}</p>`) : ""),
      prev: cases[i - 1] ? [`${B}c/${slug(cases[i - 1].id)}.html`, "앞 이야기"] : null, next: cases[i + 1] ? [`${B}c/${slug(cases[i + 1].id)}.html`, "다음 이야기"] : null, up: [`${B}cases.html`, "목록"] }));
    if (cases.length) page(`${B}cases.html`, { title: "유명한 실험·사례", crumbs: C, sub: `${cases.length}편`, body: `<ol class="list">${cases.map(c => `<li><a href="@${B}c/${slug(c.id)}.html">${esc(c.title)}</a><br><small>${esc(c.book || "")}</small></li>`).join("")}</ol>`, up: [B + "index.html", "뇌"] });
    const nw = ((rd(X("vfm-story", "data/brain/news.json")) || {}).items || []).filter(x => !x.dup).slice(0, 120);
    const newsLink = nw.length ? paged(`${B}news`, "뇌과학 소식", C, nw, 10, x => `${ext(x.url, x.ko || x.title)}<br><small>${esc(x.pub)} · ${esc(String(x.date || "").slice(0, 10))}</small>${x.ksum || x.sum ? `<br>${inl(String(x.ksum || x.sum).slice(0, 220))}` : ""}${(x.rs || []).length ? `<br><small>${x.rs.map(rlink).join(" · ")}</small>` : ""}`) : "";
    const L1 = regs.filter(r => r.lv === 1), L2 = regs.filter(r => r.lv !== 1);
    page(`${B}index.html`, { title: "뇌", crumbs: [], sub: "부위·실험·소식 (3D 지도는 원래 자판기에서)", up: ["index.html", "처음"],
      body: `<ul class="list home">${cases.length ? `<li><a href="@${B}cases.html">유명한 실험·사례</a> <small>${cases.length}편</small></li>` : ""}${newsLink ? `<li><a href="@${newsLink}">뇌과학 소식</a> <small>${nw.length}개</small></li>` : ""}</ul>` +
        `<h2>먼저 알 곳 <small>${L1.length}곳</small></h2><ul class="list cols">${L1.map(r => `<li>${rlink(r.id)}</li>`).join("")}</ul><h2>더 깊이 <small>${L2.length}곳</small></h2><ul class="list cols">${L2.map(r => `<li>${rlink(r.id)}</li>`).join("")}</ul>` });
    return [B + "index.html", "뇌", `부위 ${regs.length}곳 · 실험·사례 ${cases.length}편 · 소식`];
  }

  /* ── 책: 깊이 소개 · 주제별 · 많이 권하는 책 ── */
  function buildBook() {
    const B = "book/", C = [[B + "index.html", "책"]];
    const T = rd(X("vfm-story", "data/book/top.json")) || {}, cols = T.cols || [], rows = (T.rows || []).map(r => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
    const byId = new Map(rows.map(r => [r.id, r])), BD = runJs([X("vfm-story", "book/deep.js")]).BOOK_DEEP || { byId: {}, themes: [] };
    const deepIds = Object.keys(BD.byId || {}).filter(id => byId.has(id));
    const info = r => [r.a, r.f, r.y ? r.y + "년판" : "", r.pg ? r.pg + "쪽" : "", r.r ? `대학·기관 ${r.r}곳 추천` : ""].filter(Boolean).map(esc).join(" · ");
    const blink = id => byId.has(id) ? (BD.byId[id] ? `<a href="@${B}b/${id}.html">${esc(byId.get(id).t)}</a>` : esc(byId.get(id).t)) + ` <small>${esc(byId.get(id).a || "")}</small>` : "";
    deepIds.forEach((id, i) => { const r = byId.get(id), d = BD.byId[id];
      page(`${B}b/${id}.html`, { title: r.t, crumbs: C, sub: info(r), body: `<p class="lead">${inl(d.one || "")}</p>` + paras(d.body) + sec("어디서부터 읽을까", md(d.start), "box") + sec("생각할 질문", ul(d.q, inl)),
        prev: deepIds[i - 1] ? [`${B}b/${deepIds[i - 1]}.html`, "앞 책"] : null, next: deepIds[i + 1] ? [`${B}b/${deepIds[i + 1]}.html`, "다음 책"] : null, up: [B + "index.html", "책"] }); });
    const allLink = rows.length ? paged(`${B}all`, "많이 권하는 책", C, rows.slice(0, 300), 20, r => `${BD.byId[r.id] ? `<a href="@${B}b/${r.id}.html">${esc(r.t)}</a>` : `<b>${esc(r.t)}</b>`}<br><small>${info(r)}</small>`) : "";
    page(`${B}index.html`, { title: "책", crumbs: [], sub: "대학·기관이 권하는 책", up: ["index.html", "처음"],
      body: (allLink ? `<p><a class="btn" href="@${allLink}">많이 권하는 책 ${Math.min(rows.length, 300)}권 ›</a></p>` : "") + (deepIds.length ? `<h2>깊이 소개 <small>${deepIds.length}권</small></h2>${ul(deepIds, blink)}` : "") +
        (BD.themes || []).map(t => `<h2>${esc(t.t)}</h2><p class="sub">${inl(t.d || "")}</p>${ul((t.ids || []).filter(id => byId.has(id)), blink)}`).join("") });
    return [B + "index.html", "책", `깊이 소개 ${deepIds.length}권 · 권장도서 ${rows.length}권`];
  }

  /* ── 맨탈: 고수의 수업 · 기술 깊이 · 상황별 코스 · 회차별 장면 · 실험실 ── */
  function buildMental() {
    const B = "mental/", C = [[B + "index.html", "맨탈"]], D = p => rd(X("vfm-mind", "data/mental/" + p));
    const school = D("school.json") || {}, GR = school.grades || {}, masters = school.masters || [];
    const meta = (D("meta/_index.json") || [])[0] || {}, techName = new Map((meta.techs || []).map(t => [t.k, t])), stages = meta.stages || [];
    const MD = runJs([X("vfm-mind", "mental/deep.js")]).MDEEP || { techs: {}, courses: [] };
    const ev = g => GR[g] ? `<p class="tag">근거 ${esc(g)} · ${esc(GR[g][0])}</p>` : "";
    const lessons = new Map(); for (const m of masters) for (const l of m.lessons || []) lessons.set(l.k, Object.assign({ m }, l));
    const tlink = k => techName.has(k) ? `<a href="@${B}t/${k}.html">${esc(techName.get(k).n)}</a>` : esc(k);
    const llink = k => lessons.has(k) ? `<a href="@${B}l/${k}.html">${esc(lessons.get(k).n)}</a> <small>${esc(lessons.get(k).m.name)}</small>` : esc(k);
    const lk = [...lessons.keys()];
    lk.forEach((k, i) => { const l = lessons.get(k);
      page(`${B}l/${k}.html`, { title: l.n, crumbs: C.concat([[`${B}m/${l.m.k}.html`, l.m.name]]), sub: esc(l.m.name), body: ev(l.ev) + comic(l.cm) + md(l.what) + sec("이렇게 말해요", ul(l.say, inl), "box") + sec("연습", md(l.drill)) +
        sec("근거", md(l.evn) + (l.src ? `<p class="note">${esc(l.src)}</p>` : "")) + ((l.techs || []).length ? sec("이어지는 기술", `<p class="chips">${l.techs.map(tlink).join(" · ")}</p>`) : ""),
        prev: lk[i - 1] ? [`${B}l/${lk[i - 1]}.html`, "앞 수업"] : null, next: lk[i + 1] ? [`${B}l/${lk[i + 1]}.html`, "다음 수업"] : null, up: [`${B}m/${l.m.k}.html`, l.m.name] }); });
    masters.forEach(m => page(`${B}m/${m.k}.html`, { title: m.name, crumbs: C, sub: esc([m.en, m.years, m.role].filter(Boolean).join(" · ")),
      body: `<p class="lead">${inl(m.one || "")}</p>` + md(m.story) + sec("제인에게서 보이는 모습", md(m.jane), "box") + sec("어디까지 사실일까", md(m.truth), "mis") + sec("읽을거리", ul(m.books, esc)) +
        `<h2>수업 ${(m.lessons || []).length}개</h2><ol class="list">${(m.lessons || []).map(l => `<li><a href="@${B}l/${l.k}.html">${esc(l.n)}</a> <small>근거 ${esc(l.ev || "")}</small></li>`).join("")}</ol>`, up: [B + "index.html", "맨탈"] }));
    const tk = Object.keys(MD.techs || {});
    tk.forEach((k, i) => { const t = MD.techs[k], tn = techName.get(k) || {};
      page(`${B}t/${k}.html`, { title: tn.n || k, crumbs: C, sub: esc(tn.d || ""), body: ev(t.ev) + `<p class="lead">${inl(t.one || "")}</p>` + sec("왜 되나", md(t.why)) + sec("단계", `<ol>${(t.steps || []).map(x => `<li>${inl(x)}</li>`).join("")}</ol>`) +
        sec("생활 속 예", ul(t.life, x => `<b>${esc(x[0])}</b> — ${inl(x[1])}`), "box") + sec("흔한 착각", ul(t.mis, inl), "mis") + sec("연습 3단계", ul(t.drill, x => `<b>${esc(x[0])}</b> ${inl(x[1])}`)) + sec("지킬 선", md(t.line)),
        prev: tk[i - 1] ? [`${B}t/${tk[i - 1]}.html`, "앞 기술"] : null, next: tk[i + 1] ? [`${B}t/${tk[i + 1]}.html`, "다음 기술"] : null, up: [B + "index.html", "맨탈"] }); });
    (MD.courses || []).forEach(c => page(`${B}co/${c.k}.html`, { title: c.n, crumbs: C, sub: esc(c.who || ""), body: md(c.intro) + `<ol class="list">${(c.lessons || []).map(k => `<li>${llink(k)}</li>`).join("")}</ol>` + sec("한 줄 팁", md(c.tip), "box"), up: [B + "index.html", "맨탈"] }));
    /* 회차별 장면 */
    const eps = D("eps/_index.json") || [], uses = D("uses/_index.json") || [], ana = D("analysis/_index.json") || [], con = meta.concepts || {};
    const anaBy = new Map(); for (const a of ana) { const k = a.id.split("__")[0]; if (!anaBy.has(k)) anaBy.set(k, []); anaBy.get(k).push(a); }
    const useBy = new Map(); for (const u of uses) { const k = u.id.split("-")[0]; if (!useBy.has(k)) useBy.set(k, []); useBy.get(k).push(u); }
    const LENS = { psy: "심리학", phi: "철학", sci: "과학" };
    eps.forEach((e, i) => { const us = useBy.get(e.id) || [];
      page(`${B}e/${e.id}.html`, { title: `${e.season}×${String(e.ep).padStart(2, "0")} ${e.titleKo || e.title}`, crumbs: C.concat([[`${B}eps.html`, "회차별 장면"]]), sub: esc([e.title, e.aired].filter(Boolean).join(" · ")),
        body: md(e.summary) + (e.people ? `<p class="note">${esc(e.people)}</p>` : "") + us.map(u => `<h2>${esc(u.name)}</h2>${u.tech ? `<p class="tag">${esc((techName.get(u.tech) || {}).n || u.tech)}</p>` : ""}${sec("장면", md(u.scene))}${sec("단서", md(u.clue))}${sec("원리", md(u.principle), "box")}${sec("결과", md(u.result))}${sec("연습", md(u.drill))}${sec("조심할 점", md(u.risk), "mis")}` +
          ((anaBy.get(u.id) || []).length ? sec("세 가지 눈", ul(anaBy.get(u.id), a => `<b>${esc(LENS[a.id.split("__")[1]] || "")} · ${esc(a.title)}</b>${a.s ? " — " + inl(a.s) : ""}${con[a.c] ? `<br><small>${inl(con[a.c].b)}</small>` : ""}`)) : "")).join(""),
        prev: eps[i - 1] ? [`${B}e/${eps[i - 1].id}.html`, "앞 회차"] : null, next: eps[i + 1] ? [`${B}e/${eps[i + 1].id}.html`, "다음 회차"] : null, up: [`${B}eps.html`, "회차 목록"] }); });
    if (eps.length) page(`${B}eps.html`, { title: "회차별 장면", crumbs: C, sub: `「멘탈리스트」 ${eps.length}회 · 장면 카드 ${uses.length}장`,
      body: [...new Set(eps.map(e => e.season))].map(s => `<h2>시즌 ${s}</h2><ol class="list">${eps.filter(e => e.season === s).map(e => `<li><a href="@${B}e/${e.id}.html">${esc(e.titleKo || e.title)}</a> <small>장면 ${(useBy.get(e.id) || []).length}개</small></li>`).join("")}</ol>`).join(""), up: [B + "index.html", "맨탈"] });
    /* 실험실 */
    const lab = (D("lab.json") || {}).items || [];
    const labLink = lab.length ? paged(`${B}lab`, "실험실 — 정말 그럴까", C, lab, 4, x => `<b>${esc(x.t)}</b> <small>${esc(x.by || "")}</small>${ev(x.ev)}<ol>${(x.how || []).map(h => `<li>${inl(h[1])}</li>`).join("")}</ol><p><b>결과</b> ${inl(x.so || "")}</p>${x.note ? `<p class="note">${inl(x.note)}</p>` : ""}${(x.tk || []).length ? `<p class="chips">${x.tk.map(tlink).join(" · ")}</p>` : ""}`) : "";
    /* 목차 */
    const gl = meta.glossary || [];
    page(`${B}index.html`, { title: "맨탈", crumbs: [], sub: "「멘탈리스트」 기술을 근거와 함께", up: ["index.html", "처음"],
      body: `<p class="sub">근거 등급: ${Object.keys(GR).map(g => `<b>${esc(g)}</b> ${esc(GR[g][0])}`).join(" · ")}</p>` +
        `<h2>고수의 수업 <small>${masters.length}명 · ${lessons.size}개</small></h2>${ul(masters, m => `<a href="@${B}m/${m.k}.html">${esc(m.name)}</a><br><small>${esc(m.role || "")}</small>`)}` +
        ((school.course || []).length ? `<h2>4주 코스</h2>` + school.course.map(w => `<h3>${esc(w[0])}</h3><ol class="list">${w[1].map(k => `<li>${llink(k)}</li>`).join("")}</ol>`).join("") : "") +
        ((MD.courses || []).length ? `<h2>상황별 코스</h2>${ul(MD.courses, c => `<a href="@${B}co/${c.k}.html">${esc(c.n)}</a><br><small>${esc(c.who || "")}</small>`)}` : "") +
        (tk.length ? `<h2>기술 깊이 배우기 <small>${tk.length}갈래</small></h2>` + stages.map(s => { const l = (meta.techs || []).filter(t => t.stage === s.k && MD.techs[t.k]); return l.length ? `<h3>${esc(s.n)}</h3><ul class="list">${l.map(t => `<li>${tlink(t.k)}<br><small>${esc(t.d)}</small></li>`).join("")}</ul>` : ""; }).join("") : "") +
        `<h2>더 보기</h2><ul class="list">${eps.length ? `<li><a href="@${B}eps.html">회차별 장면</a> <small>${eps.length}회</small></li>` : ""}${labLink ? `<li><a href="@${labLink}">실험실</a> <small>${lab.length}개</small></li>` : ""}</ul>` +
        (gl.length ? `<h2>낱말</h2>${ul(gl, g => `<b>${esc(g[0])}</b> — ${inl(g[1])}`)}` : "") });
    return [B + "index.html", "맨탈", `고수 ${masters.length}명 · 수업 ${lessons.size}개 · 회차 ${eps.length}회`];
  }

  /* ── 배댓: 달마다 한국 유튜브 인기 영상과 베스트 댓글 (이 저장소 data/baedat) ── */
  function buildBaedat() {
    const months = ls("data/baedat").filter(f => /^\d{4}-\d\d\.json$/.test(f)).map(f => f.slice(0, 7)).reverse();
    if (!months.length) return null;
    const B = "baedat/", C = [[B + "index.html", "배댓"]];
    months.forEach((m, i) => { const d = rd(`data/baedat/${m}.json`) || {}, vids = d.videos || [];
      const intro = (d.report ? md(d.report) : "") + (d.summary && d.summary.types ? `<p class="note">댓글 유형: ${d.summary.types.slice(0, 6).map(t => `${esc(t[0])} ${t[1]}`).join(" · ")}</p>` : "");
      paged(`${B}${m}`, `${+m.slice(5)}월의 배댓`, C, vids, 3, v => `${ext("https://www.youtube.com/watch?v=" + v.id, v.title)}<br><small>${esc(v.channel)} · ${esc(v.category || "")} · 조회 ${num(v.views)}</small><ol>${(v.best || []).map(c => `<li>${inl(c.ko || c.text)} <small>좋아요 ${num(c.likes)}</small></li>`).join("")}</ol>`, intro);
    });
    page(`${B}index.html`, { title: "배댓", crumbs: [], sub: "달마다 한국 유튜브 인기 영상 50개와 베스트 댓글", up: ["index.html", "처음"],
      body: `<ul class="list">${months.map(m => `<li><a href="@${B}${m}.html">${m.slice(0, 4)}년 ${+m.slice(5)}월</a></li>`).join("")}</ul>` });
    return [B + "index.html", "배댓", `${months.length}달치 · 영상마다 베스트 댓글`];
  }

  /* ── 뷰티·게임: 브리핑 · 교실(이야기·낱말) · 뉴스 · 순위 ── */
  function buildConsumer(ind, label) {
    const R = "vfm-consumer", D = p => rd(X(R, "data/" + p)), B = ind + "/", C = [[B + "index.html", label]], LB = `learn/${ind}/`;
    /* 낱말 (브리핑 '배경 지식'이 이어 붙어요) */
    const terms = (D(`learn/terms_${ind}.json`) || {}).terms || [], tById = new Map(terms.map(t => [t.id, t])), tByW = new Map(terms.map(t => [t.w, t]));
    learnInfo[ind] = { terms: new Map(terms.map(t => [t.id, { t: t.w }])), chapters: new Map(), label };
    const tl = w => { const t = tByW.get(w) || tById.get(w); return t ? `<a href="@${LB}t/${t.id}.html">${esc(t.w)}</a>` : esc(w); };
    const cats = [...new Set(terms.map(t => t.k || "그 밖"))];
    cats.forEach(k => { const l = terms.filter(t => (t.k || "그 밖") === k);
      l.forEach((t, i) => page(`${LB}t/${t.id}.html`, { title: t.w, crumbs: C.concat([[`${LB}terms.html`, "낱말"]]), sub: esc([t.en, k].filter(Boolean).join(" · ")),
        body: `<p class="lead">${inl(t.s || "")}</p>` + md(t.d) + sec("예", md(t.ex), "box") + ((t.rel || []).length ? sec("이어지는 말", `<p class="chips">${t.rel.map(tl).join(" · ")}</p>`) : "") + (t.q ? sec("확인 문제", quizHtml([{ q: t.q.q, o: t.q.a, a: t.q.c, why: t.q.ex }])) : ""),
        prev: l[i - 1] ? [`${LB}t/${l[i - 1].id}.html`, l[i - 1].w] : null, next: l[i + 1] ? [`${LB}t/${l[i + 1].id}.html`, l[i + 1].w] : null, up: [`${LB}terms.html`, "낱말"] })); });
    if (terms.length) page(`${LB}terms.html`, { title: `${label} 낱말`, crumbs: C, sub: `${terms.length}개`, body: cats.map(k => `<h2>${esc(k)}</h2><ul class="list terms">${terms.filter(t => (t.k || "그 밖") === k).map(t => `<li><a href="@${LB}t/${t.id}.html">${esc(t.w)}</a> — ${inl(t.s || "")}</li>`).join("")}</ul>`).join(""), up: [B + "index.html", label] });
    /* 이야기 단원 */
    const hist = D(`learn/hist_${ind}.json`) || {}, ids = (hist.units || []).map(u => u.id), units = new Map();
    for (const id of ids) { const u = D(`learn/u/${id}.json`); if (u) units.set(id, u); }
    const ul2 = [...units.values()];
    ul2.forEach((u, i) => page(`${LB}u/${u.id}.html`, { title: u.t, crumbs: C.concat([[`${LB}index.html`, "교실"]]), sub: esc([u.sub, (u.y || []).join("~"), u.theme].filter(Boolean).join(" · ")),
      body: `<p class="lead">${inl(u.short || "")}</p>` + paras(u.mid) + (u.long || []).map(s => `<h2>${esc(s.h)}</h2>${paras(s.p)}`).join("") +
        sec("연표", (u.events || []).length ? `<ol class="list tl">${u.events.map(e => `<li><span class="y">${esc(e.y)}${e.m ? "." + e.m : ""}</span> ${inl(e.t)}</li>`).join("")}</ol>` : "") +
        sec("그때 세상은", typeof u.ctx === "string" ? md(u.ctx) : "") + sec("지금은", typeof u.now === "string" ? md(u.now) : (Array.isArray(u.now) ? paras(u.now) : "")) +
        ((u.terms || []).length ? sec("나온 낱말", `<p class="chips">${u.terms.map(tl).join(" · ")}</p>`) : "") +
        ((u.quiz || []).length ? sec("확인 문제", quizHtml(u.quiz.map(q => ({ q: q.q, o: q.a, a: q.c, why: q.ex })))) : "") + sec("출처", ul(u.src, s => typeof s === "string" ? inl(s) : ext(s.u, s.t))),
      prev: ul2[i - 1] ? [`${LB}u/${ul2[i - 1].id}.html`, "앞 이야기"] : null, next: ul2[i + 1] ? [`${LB}u/${ul2[i + 1].id}.html`, "다음 이야기"] : null, up: [`${LB}index.html`, "교실"] }));
    page(`${LB}index.html`, { title: `${label} 교실`, crumbs: C, sub: `이야기 ${ul2.length}편 · 낱말 ${terms.length}개`, up: [B + "index.html", label],
      body: `<p><a class="btn" href="@${LB}terms.html">낱말 ${terms.length}개 ›</a></p>` + (hist.courses || []).map(c => `<h2>${esc(c.t)}</h2><p class="sub">${esc(c.one || "")}</p><ol class="list">${(c.units || []).filter(id => units.has(id)).map(id => `<li><a href="@${LB}u/${id}.html">${esc(units.get(id).t)}</a></li>`).join("")}</ol>`).join("") });
    /* 브리핑 */
    const br = briefings(ind, X(R, `data/brief/${ind}`), ind, label, it => `${it.tag ? `<p class="tag">${esc(it.tag)}</p>` : ""}<p class="lead">${inl(it.one || "")}</p>` + md(it.sum) + sec("왜 중요해요", md(it.why), "box") + sec("돈으로 보면", md(it.money)) + sec("지난번과 달라진 점", md(it.chg)) +
      (it.cc && typeof it.cc === "object" ? sec("나라마다", ul(Object.entries(it.cc), e => `<b>${esc(H.cc(String(e[0]).toUpperCase()))}</b> — ${inl(e[1])}`)) : "") + bgLinks(it.bg, ind) + sec("기사", ul(it.src, s => ext(s.u || s.url, s.t || s.src) + (s.src ? ` <small>${esc(s.src)}</small>` : ""))));
    /* 뉴스·순위 */
    const nw = ((D(`news/${ind}.json`) || {}).items || []).slice(0, 150);
    const newsLink = nw.length ? paged(`${B}news`, `${label} 뉴스`, C, nw, 12, x => `${ext(x.url, x.ko || x.t)}<br><small>${esc(x.src || "")} · ${esc(H.cc(String(x.cc || "").toUpperCase()))} · ${esc(String(x.at || "").slice(0, 10))}</small>`) : "";
    const boards = Object.entries((D("rank/latest.json") || {}).boards || {}).filter(([, b]) => b.ind === ind);
    boards.forEach(([k, b]) => page(`${B}rank/${slug(k)}.html`, { title: b.t, crumbs: C, sub: esc(b.day || ""), body: `<ol class="list">${(b.rows || []).slice(0, 50).map(r => `<li><b>${esc(r.n)}</b> <small>${esc(r.by || "")}${r.d ? ` · ${r.d > 0 ? "▲" : "▼"}${Math.abs(r.d)}` : ""}</small></li>`).join("")}</ol>`, up: [B + "index.html", label] }));
    const L0 = br[0];
    page(`${B}index.html`, { title: label, crumbs: [], sub: `${label} 산업 소식과 이야기`, up: ["index.html", "처음"],
      body: (L0 ? `<h2>${esc(L0.label)}</h2><p class="sub">${when(L0.at)} 정리 · 소식 ${L0.n}개</p>${L0.lead ? `<p class="lead">${inl(L0.lead)}</p>` : ""}<p><a class="btn" href="@${L0.base}/index.html">브리핑 읽기 ›</a></p>` : "") +
        `<h2>더 보기</h2><ul class="list"><li><a href="@${LB}index.html">${label} 교실</a> <small>이야기 ${ul2.length}편 · 낱말 ${terms.length}개</small></li>${newsLink ? `<li><a href="@${newsLink}">${label} 뉴스</a> <small>${nw.length}개</small></li>` : ""}${boards.map(([k, b]) => `<li><a href="@${B}rank/${slug(k)}.html">${esc(b.t)}</a></li>`).join("")}</ul>` +
        (br.length > 1 ? `<h2>지난 브리핑</h2><ul class="list">${br.slice(1).map(b => `<li><a href="@${b.base}/index.html">${esc(b.label)}</a></li>`).join("")}</ul>` : "") });
    return [B + "index.html", label, L0 ? L0.label : `이야기 ${ul2.length}편 · 낱말 ${terms.length}개`];
  }
};
