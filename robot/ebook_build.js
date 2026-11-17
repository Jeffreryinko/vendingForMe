#!/usr/bin/env node
/* 종이 자판기 — 이북리더기(전자잉크)용 정적 사이트를 만들어요.  node robot/ebook_build.js
   data/ 의 로봇 자료와 교실 글(sisa/learn · deal/learn · ai/learn · gicho)을 읽어 ebook/ 에 HTML만 써요.
   기존 자판기 파일은 읽기만 하고 고치지 않아요. 자바스크립트·애니메이션·웹폰트·사진 없음 (토큰 0).
   움직이는 것(라디오·univ.·퀘스트·보관함·점수판·랜덤 카드·플래너)은 뺐고,
   퀴즈는 '정답 보기'(접었다 펴기)로, 만화는 대화 글로, 그림(SVG)은 흑백으로 바꿨어요. */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm"), crypto = require("crypto");
const ver = s => crypto.createHash("md5").update(s).digest("hex").slice(0, 8);   // 모양·스크립트가 바뀌면 주소도 바뀌어 옛 저장본을 안 써요
const ROOT = path.resolve(__dirname, ".."), OUT = process.env.EBOOK_OUT ? path.resolve(process.env.EBOOK_OUT) : path.join(ROOT, "ebook");
const SITE = process.env.EBOOK_SITE || "종이 자판기";   // 맨 위 경로·제목에 붙는 이름
const abs = p => path.isAbsolute(p) ? p : path.join(ROOT, p);
const rd = p => { try { return JSON.parse(fs.readFileSync(abs(p), "utf8")); } catch (e) { return null; } };
const ls = p => { try { return fs.readdirSync(abs(p)).sort(); } catch (e) { return []; } };

/* ── 글자 도구 ── */
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const inl = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
const md = s => s ? String(s).split(/\n+/).filter(x => x.trim()).map(x => "<p>" + inl(x) + "</p>").join("") : "";
const sec = (h, body, cls) => body ? `<section${cls ? ` class="${cls}"` : ""}><h3>${h}</h3>${body}</section>` : "";
const ul = (arr, f) => arr && arr.length ? "<ul>" + arr.map(x => "<li>" + f(x) + "</li>").join("") + "</ul>" : "";
const ext = (u, t) => u ? `<a href="${esc(u)}">${esc(t || "원문")}</a>` : esc(t);
const host = u => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return ""; } };
const KST = d => new Date(d.getTime() + 9 * 3600e3);
const now = KST(new Date());
const stamp = `${now.getUTCMonth() + 1}월 ${now.getUTCDate()}일 ${String(now.getUTCHours()).padStart(2, "0")}:${String(now.getUTCMinutes()).padStart(2, "0")}`;
const W = ["일", "월", "화", "수", "목", "금", "토"];
const when = iso => { if (!iso) return ""; const d = KST(new Date(iso)); if (isNaN(d)) return ""; return `${d.getUTCMonth() + 1}월 ${d.getUTCDate()}일 ${d.getUTCHours()}시`; };
const krw = a => { if (!a) return ""; if (a >= 1e12) return "약 " + (a / 1e12).toFixed(a >= 1e13 ? 0 : 1) + "조 원"; if (a >= 1e8) return "약 " + Math.round(a / 1e8).toLocaleString("en") + "억 원"; return "약 " + Math.round(a / 1e4).toLocaleString("en") + "만 원"; };
const num = n => n == null ? "" : Number(n).toLocaleString("en");

const CC = { KR: "한국", US: "미국", CN: "중국", JP: "일본", GB: "영국", FR: "프랑스", DE: "독일", RU: "러시아", UA: "우크라이나", IN: "인도", ID: "인도네시아", BR: "브라질", MX: "멕시코", AR: "아르헨티나", CA: "캐나다", AU: "호주", IT: "이탈리아", ES: "스페인", PT: "포르투갈", NL: "네덜란드", PL: "폴란드", TR: "튀르키예", SA: "사우디", AE: "아랍에미리트", QA: "카타르", EG: "이집트", IL: "이스라엘", IR: "이란", PK: "파키스탄", BD: "방글라데시", TH: "태국", VN: "베트남", PH: "필리핀", MY: "말레이시아", SG: "싱가포르", TW: "대만", HK: "홍콩", KE: "케냐", NG: "나이지리아", ZA: "남아공", GH: "가나", MA: "모로코", CL: "칠레", CO: "콜롬비아", PE: "페루", LV: "라트비아", CH: "스위스", SE: "스웨덴", BE: "벨기에", AT: "오스트리아", IE: "아일랜드", KP: "북한", WW: "세계" };
const cc = c => CC[c] || c || "";
const CAT = { pol: "정치", eco: "경제", tech: "기술", soc: "사회", cul: "문화", war: "분쟁", dis: "재난", spo: "스포츠", sci: "과학" };
const AIK = { feat: "새 기능", model: "새 모델", rule: "규칙·정책", biz: "회사·돈", paper: "논문", tool: "도구" };
const DK = { ma: "인수합병", vc: "투자 유치", ipo: "상장", pe: "사모", fund: "펀드" };
const DST = { done: "성사", rumor: "소문", fail: "무산", plan: "계획", talk: "협상 중", news: "소식" };

/* ── 페이지 쓰기 ── */
let pages = 0;
function page(file, o) {
  if (o.up) { if (o.prev && o.prev[0] === o.up[0]) o.prev = null; if (o.next && o.next[0] === o.up[0]) o.next = null; }
  const depth = file.split("/").length - 1, R = "../".repeat(depth);
  const h = x => /^(https?:|#|mailto:)/.test(x) ? x : R + x;
  const nav = (o.prev || o.next || o.up) ? `<nav class="pn">${o.prev ? `<a data-r="prev" href="${h(o.prev[0])}">‹ ${esc(o.prev[1] || "앞")}</a>` : "<span></span>"}${o.up ? `<a href="${h(o.up[0])}">${esc(o.up[1] || "목차")}</a>` : "<span></span>"}${o.next ? `<a data-r="next" href="${h(o.next[0])}">${esc(o.next[1] || "뒤")} ›</a>` : "<span></span>"}</nav>` : "";
  const crumbs = [["index.html", SITE]].concat(o.crumbs || []);
  const body = String(o.body).replace(/href="@([^"]*)"/g, (m, p) => `href="${R}${p}"`);
  const html = `<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(o.title)}${o.title === SITE ? "" : " · " + esc(SITE)}</title>${o.noindex ? '\n<meta name="robots" content="noindex,nofollow">' : ""}
<link rel="stylesheet" href="${R}e.css?v=${ver(CSS)}">${process.env.EBOOK_ONLY ? "" : `\n<link rel="manifest" href="${R}manifest.webmanifest">`}
</head><body>
<header class="top"><span class="cr">${crumbs.map(c => `<a href="${h(c[0])}">${esc(c[1])}</a>`).join(" › ")}</span><span class="md" hidden><a href="#" data-m="scroll">스크롤</a><a href="#" data-m="page">넘김</a><a href="#" data-f="1" class="fs" hidden>전체화면</a></span></header>
${nav.replace('class="pn"', 'class="pn pt"')}
<main id="m">
${o.h1 === false ? "" : `<h1>${esc(o.title)}</h1>`}
${o.sub ? `<p class="sub">${o.sub}</p>` : ""}
${body}
</main>
<div id="pi" hidden></div>
${nav.replace('class="pn"', 'class="pn pb"')}
<footer>${esc(SITE)}${file.startsWith("learn/") ? "" : ` · ${stamp} 만듦`}</footer>
<script src="${R}e.js?v=${ver(JS)}"></script>
</body></html>`;
  const fp = path.join(OUT, file); fs.mkdirSync(path.dirname(fp), { recursive: true }); fs.writeFileSync(fp, html); pages++;
}
/* 긴 목록을 여러 장으로 */
function paged(base, title, crumbs, items, per, render, intro) {
  const n = Math.max(1, Math.ceil(items.length / per)), name = i => i === 0 ? base + ".html" : `${base}-${i + 1}.html`;
  for (let i = 0; i < n; i++) {
    const part = items.slice(i * per, (i + 1) * per);
    page(name(i), { title: title + (n > 1 ? ` (${i + 1}/${n})` : ""), crumbs, body: (i === 0 && intro ? intro : "") + `<ol class="list" start="${i * per + 1}">${part.map(x => "<li>" + render(x) + "</li>").join("")}</ol>`,
      prev: i > 0 ? [name(i - 1), "앞 장"] : null, next: i < n - 1 ? [name(i + 1), "다음 장"] : null, up: crumbs.length ? [crumbs[crumbs.length - 1][0], "위로"] : ["index.html", "처음"] });
  }
  return name(0);
}

/* ── 교실 글 읽기 (브라우저 없이 node 안에서 그대로 돌려요) ── */
function loadLearn(dir) {
  const html = fs.readFileSync(path.join(ROOT, dir, "index.html"), "utf8");
  const srcs = [...html.matchAll(/<script[^>]*src="([^"]+)"/g)].map(m => m[1].split("?")[0]).filter(s => !/assets\//.test(s));
  const el = () => ({ style: {}, appendChild() {}, setAttribute() {}, classList: { add() {} } });
  const win = { console: { warn() {}, log() {}, error() {} }, document: { createElement: el, head: el(), body: el(), addEventListener() {}, querySelector() { return null; } }, addEventListener() {}, location: { href: "" }, localStorage: { getItem() { return null; }, setItem() {} } };
  win.window = win;
  const line = p => { const [cap, ...r] = p.split("|"); return [cap, r.filter(Boolean).map(x => { const i = x.indexOf(":"), j = x.indexOf(":", i + 1); return [x.slice(0, i), x.slice(i + 1, j), x.slice(j + 1)]; })]; };
  win.VFM_ART = { cms: o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v.map(line)])) };
  const ctx = vm.createContext(win);
  for (const s of srcs) { try { vm.runInContext(fs.readFileSync(path.join(ROOT, dir, s), "utf8"), ctx, { filename: s }); } catch (e) { console.warn("[ebook] 읽기 실패", dir, s, e.message); } }
  return win;
}
/* 그림: 화면 테마 색(var) → 흑백 */
const figCache = {};
function fig(win, name) {
  const f = win.VFM_FIGS && win.VFM_FIGS[name]; if (!f) return "";
  try { const s = typeof f === "function" ? f() : f; return typeof s === "string" && s.startsWith("<svg") ? `<div class="fig">${s}</div>` : ""; } catch (e) { return ""; }
}
const comic = cm => cm && cm.length ? `<div class="cm">${cm.map(([cap, lines]) => `<div class="cmp"><h4>${esc(cap)}</h4>${(lines || []).filter(l => l[2]).map(([who, face, t]) => `<p class="${who === "me" ? "me" : "you"}${face === "t" ? " th" : ""}"><b>${who === "me" ? "나" : "너"}</b> ${inl(t)}</p>`).join("")}</div>`).join("")}</div>` : "";
const toon = t => t && t.length ? `<div class="cm">${t.map(x => Array.isArray(x) ? `<p><b>${esc(x[0])}</b> ${inl(x[1])}</p>` : `<p>${inl(x)}</p>`).join("")}</div>` : "";
const longRead = long => long && long.length ? `<section class="long"><h3>깊이 읽기 <small>${Math.max(1, Math.round(long.reduce((n, x) => n + String(x[1]).length, 0) / 500))}분</small></h3>${long.map(x => `<h4>${esc(x[0])}</h4>${md(x[1])}`).join("")}</section>` : "";
const quizHtml = (qs, chLink) => qs.map((q, i) => `<div class="q"><p class="qq"><b>${i + 1}.</b> ${inl(q.q)}</p><ol class="opt">${(q.o || []).map(o => `<li>${inl(o)}</li>`).join("")}</ol><details><summary>정답 보기</summary><p><b>${(q.a | 0) + 1}번</b> ${inl((q.o || [])[q.a] || "")}</p>${q.why ? md(q.why) : ""}${chLink && q.ch ? chLink(q.ch) : ""}</details></div>`).join("");

const LEARN = [
  ["sisa", "sisa/learn", "세상 읽기 교실", "뉴스 뒤 배경 — 정치·경제·역사·나라별"],
  ["deal", "deal/learn", "투자 교실", "돈이 움직이는 말과 역사"],
  ["ai", "ai/learn", "AI 교실", "AI 낱말·쓰는 법·역사"],
  ["gicho", "gicho", "기초 교실", "과학·심리학·철학을 이야기 순서로"],
];
const learnInfo = {};   // 앱 → { terms:Set, chapters:Set }

function buildLearn([app, dir, label, desc]) {
  const win = loadLearn(dir), L = win.VFM_LEARN || {}, B = `learn/${app}/`;
  const terms = win.VFM_TERMS || [], cats = win.VFM_TERM_CATS || [], CM = win.VFM_CARDCM || {}, chs = L.chapters || [], HS = L.history || [];
  const termById = new Map(terms.map(t => [t.id, t]));
  learnInfo[app] = { terms: termById, chapters: new Map(chs.map(c => [c.id, c])), label };
  const crumb = [[B + "index.html", label]];
  const tlink = id => { const t = termById.get(id); return t ? `<a href="@${B}t/${encodeURIComponent(id)}.html">${esc(t.t)}</a>` : ""; };
  const tchips = ids => { const s = (ids || []).map(tlink).filter(Boolean); return s.length ? `<p class="chips">${s.join(" · ")}</p>` : ""; };

  /* 코스: 장마다 카드 한 장씩 */
  chs.forEach((ch, ci) => {
    const nch = chs[ci + 1], after = nch ? [`${B}ch/${nch.id}.html`, "다음 장"] : [`${B}index.html`, "교실 목차"];
    const cards = ch.cards || [], base = `${B}ch/${ch.id}`, hasQ = (ch.quiz || []).length;
    page(`${base}.html`, { title: `${ch.flag ? ch.flag + " " : ""}${ch.t}`, crumbs: crumb, sub: inl(ch.sub || ""),
      body: `<ol class="list">${cards.map((k, i) => `<li><a href="@${base}-${i + 1}.html">${esc(k.h)}</a></li>`).join("")}${hasQ ? `<li><a href="@${base}-q.html">확인 문제 ${ch.quiz.length}개</a></li>` : ""}</ol>`,
      up: [B + "index.html", "교실 목차"], next: cards.length ? [`${base}-1.html`, "첫 카드"] : null });
    cards.forEach((k, i) => {
      const deep = sec(L.txt && L.txt.x || "예를 들면", md(k.ex), "box") + sec("기억할 것", ul(k.pt, inl)) + longRead(k.long);
      page(`${base}-${i + 1}.html`, { title: k.h, crumbs: crumb.concat([[`${base}.html`, ch.t]]), sub: `${esc(ch.t)} · ${i + 1}/${cards.length}`,
        body: comic(CM[`${ch.id}:${i}`]) + md(k.b) + (k.fig ? fig(win, k.fig) : "") + deep + (k.tm && k.tm.length ? sec("이 카드의 낱말", tchips(k.tm)) : ""),
        prev: i > 0 ? [`${base}-${i}.html`, "앞 카드"] : [`${base}.html`, "장 목차"],
        next: i < cards.length - 1 ? [`${base}-${i + 2}.html`, "다음 카드"] : hasQ ? [`${base}-q.html`, "확인 문제"] : after,
        up: [`${base}.html`, "장 목차"] });
    });
    if (hasQ) page(`${base}-q.html`, { title: `확인 문제 — ${ch.t}`, crumbs: crumb.concat([[`${base}.html`, ch.t]]), sub: "답을 골라 본 뒤 '정답 보기'를 누르세요.",
      body: quizHtml(ch.quiz), prev: cards.length ? [`${base}-${cards.length}.html`, "마지막 카드"] : null, next: after, up: [`${base}.html`, "장 목차"] });
  });
  /* 수준 확인 */
  if ((L.diag || []).length) page(`${B}diag.html`, { title: "수준 확인", crumbs: crumb, sub: "모르는 문제가 나온 장부터 읽으면 돼요.",
    body: quizHtml(L.diag, id => learnInfo[app].chapters.get(id) ? `<p>→ <a href="@${B}ch/${id}.html">${esc(learnInfo[app].chapters.get(id).t)}</a></p>` : ""), up: [B + "index.html", "교실 목차"] });

  /* 역사: 사건마다 한 장 (같은 사건이 여러 묶음에 나오면 한 장을 함께 가리켜요) */
  const evNo = new Map(); let en = 0; const evHome = new Map();
  for (const h of HS) for (const e of h.items) { if (!evNo.has(e)) { evNo.set(e, ++en); evHome.set(e, h); } }
  for (const h of HS) {
    page(`${B}h/${h.id}.html`, { title: `${h.flag ? h.flag + " " : ""}${h.name}`, crumbs: crumb, sub: inl(h.intro || ""),
      body: `<ol class="list tl">${h.items.map(e => `<li><span class="y">${esc(e.y)}</span> <a href="@${B}e/${evNo.get(e)}.html">${esc(e.t)}</a></li>`).join("")}</ol>`, up: [B + "index.html", "교실 목차"] });
  }
  for (const [e, no] of evNo) {
    const h = evHome.get(e), i = h.items.indexOf(e), pv = h.items[i - 1], nx = h.items[i + 1];
    const body = md(e.b) + sec(L.txt && L.txt.w ? L.txt.w + " 이어지는 점" : "지금과 이어지는 점", md(e.w), "box") + sec("왜 일어났나", md(e.why)) +
      sec("어떻게 흘러갔나", e.flow && e.flow.length ? `<ol class="list tl">${e.flow.map(f => `<li><span class="y">${esc(f[0])}</span> ${inl(f[1])}</li>`).join("")}</ol>` : "") +
      sec("나오는 사람·나라", ul(e.who, w => `<b>${esc(w[0])}</b> — ${inl(w[1])}`)) + sec("숫자로 보면", ul(e.num, n => `<b>${esc(n[0])}</b> — ${inl(n[1])}`)) +
      sec("그 뒤", md(e.aft)) + sec("헷갈리기 쉬운 점", md(e.mis), "mis") + toon(e.toon) + longRead(e.long) + (e.tm && e.tm.length ? sec("함께 볼 낱말", tchips(e.tm)) : "") +
      (e.co && e.co.length ? sec("나오는 이름", `<p>${e.co.map(esc).join(" · ")}</p>`) : "");
    page(`${B}e/${no}.html`, { title: e.t, crumbs: crumb.concat([[`${B}h/${h.id}.html`, h.name]]), sub: esc(e.y), body,
      prev: pv ? [`${B}e/${evNo.get(pv)}.html`, "앞 사건"] : null, next: nx ? [`${B}e/${evNo.get(nx)}.html`, "다음 사건"] : null, up: [`${B}h/${h.id}.html`, "연표"] });
  }

  /* 낱말 */
  const catName = new Map(cats.map(c => [c[0], c[1]])), byCat = new Map();
  for (const t of terms) { const c = catName.has(t.c) ? t.c : "_etc"; if (!byCat.has(c)) byCat.set(c, []); byCat.get(c).push(t); }
  const catOrder = cats.map(c => c[0]).filter(c => byCat.has(c)).concat(byCat.has("_etc") ? ["_etc"] : []);
  const LV = { 1: "꼭", 2: "보통", 3: "깊이" };
  for (const c of catOrder) {
    const list = byCat.get(c), cn = catName.get(c) || "그 밖의 낱말";
    page(`${B}t/c-${c}.html`, { title: cn, crumbs: crumb, sub: `낱말 ${list.length}개`,
      body: `<ul class="list terms">${list.map(t => `<li><a href="@${B}t/${encodeURIComponent(t.id)}.html">${esc(t.t)}</a> — ${inl(t.s)}</li>`).join("")}</ul>`, up: [B + "index.html", "교실 목차"] });
    list.forEach((t, i) => {
      const tf = L.termFig && L.termFig[t.id];
      page(`${B}t/${encodeURIComponent(t.id)}.html`, { title: t.t, crumbs: crumb.concat([[`${B}t/c-${c}.html`, cn]]),
        sub: [t.en ? esc(t.en) : "", LV[t.lv] ? `${LV[t.lv]} 알아 둘 말` : ""].filter(Boolean).join(" · "),
        body: `<p class="lead">${inl(t.s)}</p>` + sec("비유하면", md(t.a), "box") + sec("이렇게 나와요", md(t.x)) + (tf ? fig(win, tf) : "") +
          sec("조금 더 자세히", md(t.d)) + sec("실제 예", md(t.ex), "box") + sec("헷갈리기 쉬운 점", md(t.mis), "mis") + sec("어디서 온 말", md(t.hs)) + longRead(t.long) +
          (t.r && t.r.length ? sec("이어지는 말", tchips(t.r)) : ""),
        prev: i > 0 ? [`${B}t/${encodeURIComponent(list[i - 1].id)}.html`, list[i - 1].t] : null,
        next: i < list.length - 1 ? [`${B}t/${encodeURIComponent(list[i + 1].id)}.html`, list[i + 1].t] : null, up: [`${B}t/c-${c}.html`, cn] });
    });
  }

  /* 교실 목차 */
  const chGroups = L.chGroups, histGroups = L.histGroups;
  const chList = list => `<ol class="list">${list.map(c => `<li><a href="@${B}ch/${c.id}.html">${c.flag ? c.flag + " " : ""}${esc(c.t)}</a>${c.sub ? `<br><small>${inl(c.sub)}</small>` : ""}</li>`).join("")}</ol>`;
  let body = md(L.intro);
  body += `<h2>코스 <small>${chs.length}장 · 카드 ${chs.reduce((n, c) => n + c.cards.length, 0)}장</small></h2>`;
  if ((L.diag || []).length) body += `<p><a class="btn" href="@${B}diag.html">수준 확인 ${L.diag.length}문제</a></p>`;
  if (chGroups) for (const g in chGroups) { const l = chs.filter(c => c.g === g); if (l.length) body += `<h3>${esc(chGroups[g][0])}</h3><p class="sub">${esc(chGroups[g][1])}</p>` + chList(l); }
  else body += chList(chs);
  if (HS.length) {
    body += `<h2>역사 <small>${en}편</small></h2>`;
    const hl = l => `<ul class="list">${l.map(h => `<li><a href="@${B}h/${h.id}.html">${h.flag ? h.flag + " " : ""}${esc(h.name)}</a> <small>${h.items.length}편</small></li>`).join("")}</ul>`;
    if (histGroups) for (const g in histGroups) { const l = HS.filter(h => h.g === g); if (l.length) body += `<h3>${esc(histGroups[g][0])}</h3>` + hl(l); }
    else body += hl(HS);
  }
  if (terms.length) body += `<h2>낱말 <small>${terms.length}개</small></h2><ul class="list">${catOrder.map(c => `<li><a href="@${B}t/c-${c}.html">${esc(catName.get(c) || "그 밖의 낱말")}</a> <small>${byCat.get(c).length}개</small></li>`).join("")}</ul>`;
  page(`${B}index.html`, { title: label, crumbs: [], sub: esc(desc), body, up: ["index.html", "처음"] });
  return { app, label, desc, n: `코스 ${chs.length}장 · 역사 ${en}편 · 낱말 ${terms.length}개` };
}

/* ── 브리핑(시사·AI·딜 공통 틀) ── */
function bgLinks(bg, app) {
  const I = learnInfo[app]; if (!bg || !bg.length || !I) return "";
  const s = bg.map(b => {
    if (b.k === "term" && I.terms.has(b.id)) return `<a href="@learn/${app}/t/${encodeURIComponent(b.id)}.html">${esc(b.t || I.terms.get(b.id).t)}</a>`;
    if (b.k === "ch" && I.chapters.has(b.id)) return `<a href="@learn/${app}/ch/${b.id}.html">${esc(b.t || I.chapters.get(b.id).t)}</a>`;
    return b.t ? esc(b.t) : "";
  }).filter(Boolean);
  return s.length ? sec("배경 지식", `<p class="chips">${s.join(" · ")}</p>`) : "";
}
function briefings(app, dataDir, home, label, itemBody, extra) {
  const idx = (rd(`${dataDir}/_index.json`) || ls(dataDir).filter(f => /^\d{4}-.*\.json$/.test(f)).map(f => ({ id: f.slice(0, -5) }))).slice(-7).reverse();
  const out = [];
  for (const { id } of idx) {
    const b = rd(`${dataDir}/${id}.json`); if (!b || !(b.items || []).length) continue;
    const base = `${home}/br/${id}`, crumb = [[`${home}/index.html`, label]];
    b.items.forEach((it, i) => page(`${base}/${i + 1}.html`, { title: it.t, crumbs: crumb.concat([[`${base}/index.html`, b.label]]), sub: `${i + 1}/${b.items.length}` + (it.tag ? " · " + esc(it.tag) : ""),
      body: itemBody(it), prev: i > 0 ? [`${base}/${i}.html`, "앞 소식"] : [`${base}/index.html`, "목차"],
      next: i < b.items.length - 1 ? [`${base}/${i + 2}.html`, "다음 소식"] : [`${base}/index.html`, "목차"], up: [`${base}/index.html`, "목차"] }));
    const list = `<ol class="list">${b.items.map((it, i) => `<li><a href="@${base}/${i + 1}.html">${esc(it.t)}</a><br><small>${inl(it.one || "")}</small></li>`).join("")}</ol>`;
    const bodyB = (b.lead ? `<p class="lead">${inl(b.lead)}</p>` : "") + `<p><a class="btn" href="@${base}/1.html">첫 소식부터 읽기 ›</a></p>` + list + (extra ? extra(b, base) : "") + (b.note ? `<p class="note">${inl(b.note)}</p>` : "");
    page(`${base}/index.html`, { title: b.label, crumbs: crumb, sub: when(b.at) + " 정리", body: bodyB, up: [`${home}/index.html`, label] });
    out.push({ id, label: b.label, at: b.at, lead: b.lead, base, n: b.items.length });
  }
  return out;
}

/* ── 시사 ── */
function buildSisa() {
  const meta = rd("data/sisa/_meta.json") || {}, edId = meta.edition;
  const ed = edId ? rd(`data/sisa/editions/${edId}.json`) : null;
  const srcName = new Map(((ed && ed.sources) || []).map(s => [s.id, s.n]));
  const feed = new Map();
  for (const f of ls("data/sisa/feed")) if (edId && f.startsWith(edId + "__")) { const d = rd("data/sisa/feed/" + f); for (const it of (d && d.items) || []) feed.set(it.id, it); }
  const stories = (ed && ed.stories) || [], bySid = new Map(stories.map(s => [s.sid, s]));
  const artLinks = ids => ul((ids || []).map(i => feed.get(i)).filter(Boolean).slice(0, 6), it => `${ext(it.u, it.ko || it.t)} <small>${esc(srcName.get(it.s) || host(it.u))} · ${cc(it.c)}</small>`);
  const storyHome = new Map(); const issueBase = "sisa/i";

  const br = briefings("sisa", "data/sisa/briefing", "sisa", "시사", it => {
    const st = (it.sids || []).map(s => bySid.get(s)).filter(Boolean)[0];
    return `<p class="tag">${esc(CAT[it.cat] || it.cat || "")}</p><p class="lead">${inl(it.one)}</p>` + md(it.sum) + sec("왜 중요해요", md(it.why), "box") + sec("지난번과 달라진 점", md(it.chg)) +
      sec("나라마다 이렇게 봐요", ul(it.views, v => `<b>${esc(cc(v.cc))} · ${esc(v.src)}</b> — ${inl(v.t)}`)) + bgLinks(it.bg, "sisa") +
      (st ? sec("기사 원문", artLinks(st.first && st.first.length ? st.first : st.items)) + `<p><a href="@${issueBase}/${st.sid}.html">이 이슈 자세히 ›</a></p>` : "");
  }, b => (b.kr && b.kr.length ? `<h2>한국 소식</h2>` + ul(b.kr, k => `<b>${esc(k.t)}</b> — ${inl(k.one)}`) : "") + (b.buzz && b.buzz.length ? `<h2>나라별 화제</h2>` + ul(b.buzz, k => `<b>${esc(cc(k.cc))} · ${esc(k.t)}</b> — ${inl(k.one)}`) : ""));

  /* 이슈: 이번 판에서 기사가 많은 순 */
  const top = stories.filter(s => (s.title || s.label)).sort((a, b) => (b.top | 0) - (a.top | 0) || (b.items || []).length - (a.items || []).length).slice(0, 60);
  top.forEach((s, i) => {
    page(`${issueBase}/${s.sid}.html`, { title: s.title || s.label, crumbs: [["sisa/index.html", "시사"], ["sisa/issues.html", "이슈"]],
      sub: [CAT[s.cat], (s.countries || []).map(cc).slice(0, 6).join("·"), `기사 ${(s.items || []).length}개`].filter(Boolean).join(" · "),
      body: md(s.sum) + sec("나라마다 이렇게 썼어요", ul(s.angles, a => `<b>${esc(cc(a.c))} · ${esc(a.f)}</b> — ${inl(a.t)}`)) +
        sec("기사 속 문장", ul((s.lines || []).slice(0, 6), l => `${inl(l.t)} <small>${esc(srcName.get(l.s) || l.s)}${l.mt ? " · 기계번역" : ""}</small>`)) +
        sec("기사 원문", artLinks((s.first || []).concat(s.items || []).filter((v, k, a) => a.indexOf(v) === k))),
      prev: i > 0 ? [`${issueBase}/${top[i - 1].sid}.html`, "앞 이슈"] : null, next: i < top.length - 1 ? [`${issueBase}/${top[i + 1].sid}.html`, "다음 이슈"] : null, up: ["sisa/issues.html", "이슈 목록"] });
  });
  paged("sisa/issues", "지금의 이슈", [["sisa/index.html", "시사"]], top, 12, s => `<a href="@${issueBase}/${s.sid}.html">${esc(s.title || s.label)}</a><br><small>${esc(CAT[s.cat] || "")} · 기사 ${(s.items || []).length}개${s.life === "new" ? " · 새로 생김" : ""}</small>`,
    `<p class="sub">${esc(meta.label || "")} 기준 · 여러 나라 기사를 로봇이 같은 사건끼리 묶었어요.</p>`);
  /* 나라별 */
  const cd = (ed && ed.countryDigest) || {}, cds = Object.keys(cd).sort((a, b) => (a === "KR" ? -1 : b === "KR" ? 1 : cc(a).localeCompare(cc(b), "ko")));
  paged("sisa/nation", "나라별 두 줄", [["sisa/index.html", "시사"]], cds, 12, c => `<b>${esc(cc(c))}</b><br>${inl(cd[c])}`, `<p class="sub">${esc(meta.label || "")} 기준</p>`);

  const L0 = br[0];
  const body = (L0 ? `<h2>${esc(L0.label)}</h2><p class="sub">${when(L0.at)} 정리 · 소식 ${L0.n}개</p>${L0.lead ? `<p class="lead">${inl(L0.lead)}</p>` : ""}<p><a class="btn" href="@${L0.base}/index.html">브리핑 읽기 ›</a></p>` : "<p>브리핑이 아직 없어요.</p>") +
    `<h2>더 보기</h2><ul class="list"><li><a href="@sisa/issues.html">지금의 이슈 ${top.length}개</a> <small>${esc(meta.label || "")}</small></li><li><a href="@sisa/nation.html">나라별 두 줄</a> <small>${cds.length}개 나라</small></li><li><a href="@learn/sisa/index.html">세상 읽기 교실</a></li></ul>` +
    (br.length > 1 ? `<h2>지난 브리핑</h2><ul class="list">${br.slice(1).map(b => `<li><a href="@${b.base}/index.html">${esc(b.label)}</a></li>`).join("")}</ul>` : "");
  page("sisa/index.html", { title: "시사", crumbs: [], sub: "세계 뉴스를 한국어로", body, up: ["index.html", "처음"] });
  return { label: L0 ? L0.label : "", at: meta.updatedAt };
}

/* ── AI ── */
function buildAi() {
  const br = briefings("ai", "data/ai/briefing", "ai", "AI", it => `<p class="tag">${esc([AIK[it.kind] || it.kind, it.who].filter(Boolean).join(" · "))}</p><p class="lead">${inl(it.one)}</p>` +
    sec("왜 중요해요", md(it.why), "box") + sec("써 보려면", md(it.how)) + bgLinks(it.bg, "ai") + sec("원문", ul(it.links, l => ext(l[1], l[0]))));
  const days = ls("data/ai/days").filter(f => /^\d{4}-\d\d-\d\d\.json$/.test(f)), day = days.length ? rd("data/ai/days/" + days[days.length - 1]) : null;
  const C = [["ai/index.html", "AI"]], more = [];
  if (day) {
    const sets = [
      ["posts", "회사 발표", x => `${ext(x.url, x.ko || x.title)} <small>${esc(x.name)} · ${esc(x.date || "")}</small>${x.ksum || x.sum ? `<br>${inl(x.ksum || x.sum)}` : ""}`],
      ["news", "AI 뉴스", x => `${ext(x.url, x.title)} <small>${esc(x.name)}</small>${x.sum ? `<br>${inl(String(x.sum).slice(0, 220))}${String(x.sum).length > 220 ? "…" : ""}` : ""}`],
      ["papers", "인기 논문", x => `${ext(x.url, x.ko || x.title)} <small>추천 ${num(x.up)}</small><br>${inl(x.one || x.ksum || x.sum || "")}`],
      ["repos", "새 코드 저장소", x => `${ext(x.url, x.name)} <small>별 ${num(x.stars)}</small><br>${inl(x.ksum || x.sum || "")}`],
      ["vids", "AI 영상", x => `${ext(x.url, x.title)} <small>${esc(x.ch)}</small>`],
    ];
    for (const [k, name, f] of sets) { const arr = (day[k] || []).slice(0, k === "papers" ? 40 : 60); if (!arr.length) continue; more.push([paged(`ai/${k}`, name, C, arr, 10, f), name, arr.length]); }
  }
  const L0 = br[0];
  page("ai/index.html", { title: "AI", crumbs: [], sub: "AI 서비스 새 기능·인기 논문", up: ["index.html", "처음"],
    body: (L0 ? `<h2>${esc(L0.label)}</h2><p class="sub">${when(L0.at)} 정리 · 소식 ${L0.n}개</p>${L0.lead ? `<p class="lead">${inl(L0.lead)}</p>` : ""}<p><a class="btn" href="@${L0.base}/index.html">브리핑 읽기 ›</a></p>` : "") +
      (more.length ? `<h2>오늘 모은 것 <small>${esc(day.day)}</small></h2><ul class="list">${more.map(m => `<li><a href="@${m[0]}">${esc(m[1])}</a> <small>${m[2]}개</small></li>`).join("")}</ul>` : "") +
      `<p><a href="@learn/ai/index.html">AI 교실 ›</a></p>` + (br.length > 1 ? `<h2>지난 브리핑</h2><ul class="list">${br.slice(1).map(b => `<li><a href="@${b.base}/index.html">${esc(b.label)}</a></li>`).join("")}</ul>` : "") });
  return { label: L0 ? L0.label : "" };
}

/* ── 딜 ── */
/* 기업 이름은 늘 구글 검색 버튼으로 */
const gq = name => name ? `<a class="gq" href="https://www.google.com/search?q=${encodeURIComponent(String(name).replace(/\s*\(.*?\)\s*/g, " ").trim())}">${esc(name)}</a>` : "";
function buildDeal() {
  const br = briefings("deal", "data/deal/briefing", "deal", "딜", it => `<p class="tag">${esc([DK[it.kind] || it.kind, DST[it.st] || it.st, cc(it.cc)].filter(Boolean).join(" · "))}</p><p class="lead">${inl(it.one)}</p>` +
    ((it.buyer || it.target || it.amt) ? `<table class="kv">${it.buyer ? `<tr><th>사는 쪽</th><td>${gq(it.buyer)}</td></tr>` : ""}${it.target ? `<tr><th>대상</th><td>${gq(it.target)}</td></tr>` : ""}${it.amt ? `<tr><th>금액</th><td>${krw(it.amt)}${it.amtNote ? ` <small>(${esc(it.amtNote)})</small>` : ""}</td></tr>` : ""}</table>` : "") +
    sec("왜 했을까", md(it.why), "box") + sec("나오는 회사", ul(it.co, c => `${gq(c[0])} — ${inl(c[1])}`)) + sec("무슨 뜻이에요", md(it.mean)) + bgLinks(it.bg, "deal") +
    (it.src ? `<p class="note">출처: ${esc(it.src)}</p>` : ""));
  const now = rd("data/deal/now.json") || {}, deals = now.deals || [], byId = new Map(deals.map(d => [d.id, d]));
  const C = [["deal/index.html", "딜"]];
  const cos = d => { const l = [d.co, d.tgt].concat(d.inv || []).filter(x => x && typeof x === "string" && x.length < 40); return l.length ? `<br>${[...new Set(l)].map(gq).join(" ")}` : ""; };
  const line = d => `${ext(d.url, d.ko || d.title)}${cos(d)}<br><small>${[DK[d.kind] || d.kind, DST[d.st] || d.st, cc(d.cc), d.amtS ? `${d.amtS}${d.amt ? " (" + krw(d.amt) + ")" : ""}` : "", d.src, d.date].filter(Boolean).map(esc).join(" · ")}</small>${d.ksum ? `<br>${inl(String(d.ksum).slice(0, 200))}` : ""}`;
  const daily = ((now.daily && now.daily.items) || []).map(x => byId.get(Array.isArray(x) ? x[0] : x)).filter(Boolean);
  const links = [];
  if (daily.length) links.push([paged("deal/daily", now.daily.label ? `오늘의 딜 — ${now.daily.label}` : "오늘의 딜", C, daily, 12, line), "오늘의 딜", daily.length]);
  for (const st of ["done", "rumor", "fail"]) { const l = deals.filter(d => d.st === st).sort((a, b) => (b.amt || 0) - (a.amt || 0)); if (l.length) links.push([paged(`deal/${st}`, `${DST[st]} 거래 (큰 순)`, C, l, 12, line), `${DST[st]} 거래`, l.length]); }
  const L0 = br[0];
  page("deal/index.html", { title: "딜", crumbs: [], sub: "세계 투자 유치·인수합병·상장·펀드", up: ["index.html", "처음"],
    body: (L0 ? `<h2>${esc(L0.label)}</h2><p class="sub">${when(L0.at)} 정리 · 소식 ${L0.n}개</p>${L0.lead ? `<p class="lead">${inl(L0.lead)}</p>` : ""}<p><a class="btn" href="@${L0.base}/index.html">브리핑 읽기 ›</a></p>` : "") +
      (links.length ? `<h2>거래 목록 <small>${when(now.at)}</small></h2><ul class="list">${links.map(m => `<li><a href="@${m[0]}">${esc(m[1])}</a> <small>${m[2]}건</small></li>`).join("")}</ul>` : "") +
      `<p><a href="@learn/deal/index.html">투자 교실 ›</a></p>` + (br.length > 1 ? `<h2>지난 브리핑</h2><ul class="list">${br.slice(1).map(b => `<li><a href="@${b.base}/index.html">${esc(b.label)}</a></li>`).join("")}</ul>` : "") });
  return { label: L0 ? L0.label : "" };
}

/* ── 도구 ── */
function buildTools() {
  const n = rd("data/tools/now.json"); if (!n) return null;
  const S = n.sec || {}, all = new Map(); for (const k in S) for (const x of S[k]) all.set(x.id, x);
  const C = [["tools/index.html", "도구"]];
  const f = x => `${ext(x.url, x.ko || x.title)}${x.owner ? ` <small>${esc(x.owner)}</small>` : ""}${x.ch ? ` <small>${esc(x.ch)}</small>` : ""}<br><small>${[x.kind, x.stars ? "별 " + num(x.stars) + (x.gain ? ` (+${num(x.gain)})` : "") : "", x.pts ? num(x.pts) + "점" : "", x.likes ? "좋아요 " + num(x.likes) : "", x.views ? "조회 " + num(x.views) : "", x.lang, x.date].filter(Boolean).map(esc).join(" · ")}</small>${x.ksum || x.sum ? `<br>${inl(String(x.ksum || x.sum).slice(0, 240))}` : ""}${x.disc ? ` <small>${ext(x.disc, "토론")}</small>` : ""}`;
  const NAMES = [["hot", "지금 뜨는 것"], ["gh", "깃허브 급상승"], ["gn", "긱뉴스"], ["hn", "해커뉴스"], ["hf", "허깅페이스 AI 앱"], ["ye", "유튜브 해설 영상"], ["list", "모음 목록에 새로 들어온 것"]];
  const links = [];
  for (const [k, name] of NAMES) {
    const arr = k === "hot" ? (n.hot || []).map(id => all.get(id)).filter(Boolean) : (S[k] || []);
    if (arr.length) links.push([paged(`tools/${k}`, name, C, arr, 10, f), name, arr.length]);
  }
  page("tools/index.html", { title: "도구", crumbs: [], sub: `요즘 뜨는 AI 도구·오픈소스 · ${when(n.at)} 모음`, up: ["index.html", "처음"],
    body: `<ul class="list">${links.map(m => `<li><a href="@${m[0]}">${esc(m[1])}</a> <small>${m[2]}개</small></li>`).join("")}</ul>` });
  return { at: n.at };
}

/* ── 트렌드 ── */
function buildTrends() {
  const fs_ = ls("data/trends").filter(f => /^[A-Z]{2}\.json$/.test(f)), list = [];
  for (const f of fs_) { const t = rd("data/trends/" + f); if (t && t.src) list.push(t); }
  list.sort((a, b) => a.cc === "KR" ? -1 : b.cc === "KR" ? 1 : String(a.name).localeCompare(String(b.name), "ko"));
  const C = [["trends/index.html", "트렌드"]];
  list.forEach((t, i) => {
    let body = "";
    for (const k of ["google", "x", "wiki", "yt", "ytfun", "reddit"]) {
      const s = t.src[k]; if (!s || !s.ok || !(s.items || []).length) continue;
      body += `<h2>${esc(s.name)} <small>${when(s.at)}</small></h2><ol class="list">${s.items.slice(0, 15).map(x => `<li>${ext(x.url, x.ko || x.kw)}${x.ko && x.ko !== x.kw ? ` <small>${esc(x.kw)}</small>` : ""}${x.n ? ` <small>${esc(x.n)}</small>` : ""}${x.sub ? ` <small>${esc(x.sub)}</small>` : ""}${(x.news || []).length ? `<br><small>${x.news.slice(0, 2).map(nw => ext(nw.u, nw.t) + " · " + esc(nw.s)).join("<br>")}</small>` : ""}</li>`).join("")}</ol>`;
    }
    page(`trends/${t.cc}.html`, { title: `${t.name} 트렌드`, crumbs: C, sub: when(t.at) + " 기준", body: body || "<p>이번에는 모은 게 없어요.</p>",
      prev: i > 0 ? [`trends/${list[i - 1].cc}.html`, list[i - 1].name] : null, next: i < list.length - 1 ? [`trends/${list[i + 1].cc}.html`, list[i + 1].name] : null, up: ["trends/index.html", "나라 목록"] });
  });
  page("trends/index.html", { title: "트렌드", crumbs: [], sub: `${list.length}개 나라 검색어·영상·위키 순위`, up: ["index.html", "처음"],
    body: `<ul class="list cols">${list.map(t => `<li><a href="@trends/${t.cc}.html">${esc(t.name)}</a></li>`).join("")}</ul>` });
  return { n: list.length };
}

/* ── 모양 (전자잉크: 흰 바탕·검은 글자·굵은 선·움직임 없음) ── */
const CSS = `/* 종이 자판기 — 전자잉크 화면용. 회색은 아주 조금만, 그림자·애니메이션·웹폰트 없음 */
:root{--accent:#000;--accent-soft:#ddd;--accent-ink:#fff;--up:#000;--up-soft:#e6e6e6;--muted:#444;--ink:#000;--sunk:#eee;--surface:#fff;--line:#000;--ap-label:#000;--ap-label2:#333;--ap-label3:#666;--ap-surface:#fff;--ap-sep:#000;--fs:1}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{background:#fff;color:#000;-webkit-text-size-adjust:100%}
body{margin:0 auto;max-width:42em;padding:12px 20px 28px;font-family:"Noto Serif KR","Noto Serif CJK KR","Source Han Serif K","Nanum Myeongjo","NanumMyeongjo","Batang","AppleMyungjo",serif;font-size:20px;line-height:1.75;
  word-break:keep-all;overflow-wrap:break-word;line-break:strict;text-rendering:optimizeLegibility}
*{transition:none!important;animation:none!important}
a{color:#000;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}
h1{font-size:1.45em;line-height:1.35;margin:.5em 0 .3em;font-weight:800}
h2{font-size:1.15em;margin:1.6em 0 .4em;padding-top:.5em;border-top:2px solid #000}
h3{font-size:1em;margin:1.2em 0 .2em}
h4{font-size:1em;margin:1em 0 .1em}
h2 small,h3 small{font-weight:400;font-size:.75em}
p{margin:.45em 0}
small,.sub,.note,footer,.top{font-size:.8em;color:#222}
.sub{margin:0 0 .8em}
.lead{font-size:1.06em;font-weight:600}
.tag{font-size:.8em;font-weight:700;display:inline-block;border:1.5px solid #000;padding:0 .5em;margin:0}
.top{padding:6px 0 8px;border-bottom:2px solid #000}
.top a{text-decoration:none}
nav.pn{display:flex;gap:8px;margin:10px 0}
nav.pn>*{flex:1;text-align:center}
nav.pn a{display:block;border:2px solid #000;padding:12px 6px;text-decoration:none;font-weight:700;font-size:.85em;min-height:52px;line-height:1.4}
nav.pn a:active{background:#000;color:#fff}
.btn{display:inline-block;border:2px solid #000;padding:10px 16px;text-decoration:none;font-weight:700}
.btn:active{background:#000;color:#fff}
ul,ol{padding-left:1.3em;margin:.4em 0}
.list>li{padding:.55em 0;border-bottom:1px solid #000}
h1.art{margin-top:1.4em;padding-top:.6em;border-top:3px double #000}
.list>li:last-child{border-bottom:0}
.list>li>a:first-child{font-weight:700}
.list.cols{columns:2;column-gap:2em}.list.cols>li{break-inside:avoid}
.tl .y{font-weight:700;font-variant-numeric:tabular-nums;margin-right:.3em}
.chips a{white-space:nowrap}
.box{border:2px solid #000;padding:.3em .9em .5em;margin:1em 0}
.box h3{margin-top:.4em}
.mis{border-left:6px solid #000;padding:.1em 0 .1em .9em;margin:1em 0}
.long{border-top:3px double #000;margin-top:1.6em}
.long h4{font-size:1.02em}
.cm{border:2px solid #000;margin:1em 0;padding:.2em .9em .5em}
.cmp h4{margin:.6em 0 .2em;font-size:.85em}
.cm p{margin:.25em 0}.cm p.you{padding-left:1.6em}.cm p.th{font-style:italic}
.cm b{display:inline-block;min-width:1.6em}
.fig{margin:1em 0;text-align:center}
.fig svg{max-width:100%;height:auto;filter:grayscale(1) contrast(1.4)}
.q{border-bottom:1px solid #000;padding:.6em 0 .9em}
.q .opt{margin:.3em 0}
details{margin-top:.4em}
summary{display:inline-block;border:2px solid #000;padding:6px 14px;font-weight:700;cursor:pointer;list-style:none}
summary::-webkit-details-marker{display:none}
details[open] summary{background:#000;color:#fff}
table.kv{border-collapse:collapse;margin:.8em 0;width:100%}
table.kv th,table.kv td{border:1px solid #000;padding:.3em .6em;text-align:left;vertical-align:top}
table.kv th{width:5em;white-space:nowrap}
footer{margin-top:1.4em;padding-top:8px;border-top:2px solid #000}
.home li{padding:.7em 0}
a.gq{display:inline-block;border:1.5px solid #000;padding:0 .45em;margin:.1em .15em .1em 0;text-decoration:none;font-weight:700;font-size:.9em;white-space:nowrap}
a.gq::after{content:" ↗";font-weight:400;font-size:.8em}
.top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.md{white-space:nowrap;display:flex}
.md a{border:2px solid #000;padding:3px 9px;text-decoration:none;font-weight:700;font-size:.95em}
.md a+a{border-left:0}
.md a.fs{margin-left:6px;border-left:2px solid #000}
.md a.on{background:#000;color:#fff}
/* 넘김 보기: 한 화면씩 끊어 옆으로 넘겨요 (e.js 가 켜요) */
html.pm,html.pm body{height:100%;overflow:hidden}
html.pm body{display:flex;flex-direction:column;padding-bottom:6px}
html.pm main{flex:1;min-height:0;overflow:hidden;column-fill:auto}
html.pm nav.pb,html.pm footer{display:none}
html.pm .fig svg{max-height:55vh}
html.pm .fig,html.pm .list>li,html.pm .q p,html.pm .cm p{break-inside:avoid}
html.pm h2,html.pm h3,html.pm h4{break-after:avoid}
#pi{text-align:center;font-size:.8em;padding:6px 0 0;border-top:2px solid #000}
/* 7인치 이북리더기(북스 Go 7·Page 등, 화면 폭 약 600px) 기준 */
/* 영업 허브에서 옮겨 온 화면 */
.v table{border-collapse:collapse;width:100%;font-size:.82em;margin:.6em 0}
.v th,.v td{border:1px solid #000;padding:.25em .4em;vertical-align:top;text-align:left}
.v dl{display:grid;grid-template-columns:auto 1fr;gap:.2em .8em}.v dt{font-weight:700}.v dd{margin:0}
.v>div>div,.v div div div{margin:.3em 0}
.bar{display:grid;grid-template-columns:6.5em 1fr auto;gap:.5em;align-items:center;margin:.3em 0;font-size:.9em}
.bar i{display:block;height:.9em;background:#000}
.big{font-size:2.2em;font-weight:800;line-height:1.1;margin:.4em 0 0}
.sms{border:1.5px solid #000;padding:.5em .7em;font-size:.92em}
blockquote{margin:1em 0;padding:.2em 0 .2em 1em;border-left:6px solid #000;font-size:1.08em;font-weight:600}
@media (max-width:760px){body{font-size:19.5px;line-height:1.7;padding:8px 16px 20px}
  h1{font-size:1.35em}.top{font-size:.75em;padding:4px 0 6px}.top .cr{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;min-width:0}
  nav.pn{margin:8px 0}nav.pn a{padding:9px 4px;min-height:44px;font-size:.8em}
  .box,.cm{padding-left:.7em;padding-right:.7em}}
@media (max-width:420px){body{font-size:18px}.list.cols{columns:1}}
@media (min-width:900px){body{font-size:22px}}
`;

/* ── 보기 바꾸기: 스크롤 / 넘김 (기기에 기억). 옛 브라우저도 돌게 ES5로 ── */
const JS = `/* 종이 자판기 보기 설정 — 스크롤/넘김, 전체화면. 이 기기에만 기억해요.
   쪽을 옮길 때 새로 불러오지 않고 글만 바꿔 끼워서(같은 문서 유지) 전체화면이 쭉 이어져요.
   글을 못 받아 오면 예전처럼 그냥 그 쪽으로 이동해요. */
(function () {
  var K = "ebook:mode", KF = "ebook:fs", d = document, R = d.documentElement, m, pi;
  function get(k, v) { try { return localStorage.getItem(k) || v; } catch (e) { return v; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var mode = get(K, "page"), n = 0, N = 1, W = 0, G = 40, busy = 0;
  /* 이 사이트의 맨 위 주소 (e.js 가 있는 곳) — 이 안의 .html 쪽만 바꿔 끼워요 */
  var me = d.querySelector('script[src*="e.js"]'), ROOT = me ? new URL(".", me.src).href : "";
  var canSwap = !!(window.fetch && window.DOMParser && ROOT);
  /* 전체화면 */
  var fsOn = function () { return !!(d.fullscreenElement || d.webkitFullscreenElement); };
  var canFs = !!(R.requestFullscreen || R.webkitRequestFullscreen) && (d.fullscreenEnabled !== false || d.webkitFullscreenEnabled);
  var fsPref = get(KF, "0") === "1";
  function fsEnter() { if (!canFs || fsOn()) return; try { var r = (R.requestFullscreen || R.webkitRequestFullscreen).call(R); if (r && r.catch) r.catch(function () {}); } catch (e) {} }
  function fsExit() { if (!fsOn()) return; try { var r = (d.exitFullscreen || d.webkitExitFullscreen).call(d); if (r && r.catch) r.catch(function () {}); } catch (e) {} }
  function fsToggle() { fsPref = !fsPref; set(KF, fsPref ? "1" : "0"); head(); if (fsPref) fsEnter(); else fsExit(); }
  function fsAuto() { if (fsPref) fsEnter(); }   /* 처음 열었을 때: 첫 누르기에 켜요 */
  d.addEventListener("touchend", fsAuto, true); d.addEventListener("keydown", fsAuto, true);
  function relay() { setTimeout(function () { layout(true); }, 150); }
  d.addEventListener("fullscreenchange", relay); d.addEventListener("webkitfullscreenchange", relay);
  /* 맨 위 버튼 표시 */
  function head() {
    var sw = d.querySelector(".md"); if (sw) sw.hidden = false;
    var a = d.querySelectorAll(".md a[data-m]"); for (var i = 0; i < a.length; i++) a[i].className = a[i].getAttribute("data-m") === mode ? "on" : "";
    var f = d.querySelector(".md a.fs"); if (f && canFs) { f.hidden = false; f.textContent = fsPref ? "전체화면 끄기" : "전체화면"; f.className = "fs" + (fsPref ? " on" : ""); }
  }
  function link(r) { var a = d.querySelector("nav.pt a[data-r=" + r + "]"); return a ? a.href : ""; }
  function show() { m.scrollLeft = n * (W + G); pi.textContent = (n + 1) + " / " + N + "  ·  누르거나 밀어서 넘겨요"; }
  function layout(keep, hash) {
    if (mode !== "page" || !m) return;
    m.style.columnWidth = m.style.webkitColumnWidth = "auto"; m.scrollLeft = 0;
    W = m.clientWidth; m.style.columnGap = m.style.webkitColumnGap = G + "px";
    m.style.columnWidth = m.style.webkitColumnWidth = W + "px";
    N = Math.max(1, Math.round(m.scrollWidth / (W + G)));
    if (!keep) { n = 0; hash = hash == null ? location.hash : hash;
      if (hash === "#end") n = N - 1;
      else if (hash && hash.length > 1) { var el = d.getElementById(hash.slice(1)); if (el) n = Math.floor((el.offsetLeft - m.offsetLeft) / (W + G)); } }
    if (n > N - 1) n = N - 1; if (n < 0) n = 0; show();
  }
  function apply(hash) {
    m = d.getElementById("m"); pi = d.getElementById("pi"); head();
    if (!m || !pi) return;
    if (mode === "page") { if (!/(^| )pm( |$)/.test(R.className)) R.className += " pm"; pi.hidden = false; layout(false, hash); }
    else { R.className = R.className.replace(/ ?pm/g, ""); pi.hidden = true; m.style.columnWidth = m.style.webkitColumnWidth = ""; m.scrollLeft = 0;
      var el = hash && hash.length > 1 && hash !== "#end" ? d.getElementById(hash.slice(1)) : null; if (el && el.scrollIntoView) el.scrollIntoView(); else window.scrollTo(0, 0); }
  }
  /* 쪽 바꿔 끼우기 */
  function inside(u) { return !!(canSwap && u.indexOf(ROOT) === 0 && /\\.html($|[#?])/.test(u)); }
  function swap(u, push) {
    if (busy) return; var hash = u.indexOf("#") >= 0 ? u.slice(u.indexOf("#")) : "", url = u.split("#")[0];
    busy = 1;
    fetch(url, { credentials: "same-origin" }).then(function (r) { if (!r.ok) throw 0; return r.text(); }).then(function (t) {
      var nd = new DOMParser().parseFromString(t, "text/html"); if (!nd.getElementById("m")) throw 0;
      var b = d.querySelector("base"); if (!b) { b = d.createElement("base"); d.head.insertBefore(b, d.head.firstChild); } b.href = url;  /* 새 쪽 기준으로 링크 풀기 */
      var sc = nd.body.querySelectorAll("script"); for (var i = 0; i < sc.length; i++) sc[i].parentNode.removeChild(sc[i]);
      d.body.innerHTML = nd.body.innerHTML; d.title = nd.title;
      if (push) { try { history.pushState({ u: u }, "", u); } catch (e) {} }
      busy = 0; apply(hash);
    }).catch(function () { busy = 0; location.href = u; });
  }
  function nav(u) { if (inside(u)) swap(u, true); else location.href = u; }
  window.addEventListener("popstate", function () { if (inside(location.href)) swap(location.href, false); });
  try { history.replaceState({ u: location.href }, "", location.href); } catch (e) {}
  function go(dir) {
    if (dir > 0 && n < N - 1) { n++; show(); return; }
    if (dir < 0 && n > 0) { n--; show(); return; }
    var u = link(dir > 0 ? "next" : "prev"); if (u) nav(u + (dir < 0 ? "#end" : ""));
  }
  /* 밀기(스와이프): 왼쪽·위로 밀면 다음, 오른쪽·아래로 밀면 앞 */
  var sx = 0, sy = 0, st = 0, swiped = 0;
  d.addEventListener("touchstart", function (e) { var t = e.touches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
  d.addEventListener("touchend", function (e) {
    if (mode !== "page") return; var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy, ax = Math.abs(dx), ay = Math.abs(dy);
    if (Date.now() - st > 800 || Math.max(ax, ay) < 40) return;
    swiped = Date.now(); if (ax > ay) go(dx < 0 ? 1 : -1); else go(dy < 0 ? 1 : -1);
  }, { passive: true });
  d.addEventListener("click", function (e) {
    if (Date.now() - swiped < 600) { e.preventDefault(); return; }
    var t = e.target, isF = false, x;
    for (x = t; x && x !== d; x = x.parentNode) if (x.getAttribute && x.getAttribute("data-f")) isF = true;
    if (!isF) fsAuto();
    while (t && t !== d) {
      if (t.getAttribute && t.getAttribute("data-f")) { e.preventDefault(); fsToggle(); return; }
      if (t.getAttribute && t.getAttribute("data-m")) { e.preventDefault(); mode = t.getAttribute("data-m"); set(K, mode); apply(""); return; }
      if (t.tagName === "A" && t.href && !e.ctrlKey && !e.metaKey) { if (inside(t.href)) { e.preventDefault(); swap(t.href, true); } return; }
      t = t.parentNode;
    }
    if (mode !== "page" || !m) return;
    for (t = e.target; t && t !== m; t = t.parentNode) if (/^(A|SUMMARY|DETAILS|BUTTON)$/.test(t.tagName)) return;
    if (!t) return;
    if (e.clientX / window.innerWidth < 0.35) go(-1); else go(1);
  });
  d.addEventListener("keydown", function (e) {
    if (mode !== "page") return; var k = e.key || e.keyCode;
    if (k === "ArrowRight" || k === "ArrowDown" || k === "PageDown" || k === "AudioVolumeDown" || k === " " || k === 39 || k === 34 || k === 32) { e.preventDefault(); go(1); }
    else if (k === "ArrowLeft" || k === "ArrowUp" || k === "PageUp" || k === "AudioVolumeUp" || k === 37 || k === 33) { e.preventDefault(); go(-1); }
  });
  d.addEventListener("toggle", function () { layout(true); }, true);
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { layout(true); }, 200); });
  apply(location.hash);
})();
`;

/* ── 웹 글도 넘김으로: 책갈피(북마클릿) 안내 쪽 ── */
function buildWeb() {
  let min = ""; try { min = fs.readFileSync(path.join(__dirname, "ebook_webreader.min.js"), "utf8").trim(); } catch (e) { return null; }
  const bm = "javascript:" + encodeURIComponent(min).replace(/'/g, "%27");
  page("web.html", { title: "웹 글도 넘김으로", crumbs: [], up: ["index.html", "처음"],
    sub: "종이 자판기에서 기사 원문으로 넘어가도 한 화면씩 넘겨 읽는 법",
    body: `<p class="lead">책갈피 하나를 만들어 두면, 아무 웹 글에서나 그 책갈피를 누를 때 광고·메뉴를 빼고 본문만 흰 바탕·검은 글자로 다시 깔아 <b>넘김 방식</b>으로 보여 줘요.</p>
<p>화면 오른쪽을 누르거나 왼쪽으로 밀면 다음, 왼쪽을 누르면 앞이에요. 음량·쪽 넘김 키도 되고, 위에 <b>가− 가+</b>(글자 크기), <b>전체화면</b>, <b>✕</b>(원래 화면)이 있어요.</p>
<h2>1. 책갈피 주소 복사</h2>
<p><a class="btn" href="#" id="cp">책갈피 주소 복사</a> <span id="cpok"></span></p>
<details><summary>주소 직접 보기</summary><textarea id="bm" readonly rows="6" style="width:100%;font-size:12px">${esc(bm)}</textarea></details>
<p class="note">지금 이 쪽에서 시험해 보려면: <a href="${esc(bm)}">넘김 보기 해 보기</a> (일부 브라우저는 여기서 바로 안 돼요. 책갈피로 만들면 돼요.)</p>
<h2>2. 폰에서 책갈피 만들기</h2>
<h3>크롬 모바일 (가장 잘 돼요)</h3>
<ol><li>아무 쪽에서나 ☆(책갈피) 눌러 저장 → 책갈피 목록에서 그 책갈피 <b>수정</b></li>
<li>이름을 <b>넘김</b>으로, 주소(URL) 칸을 지우고 복사한 주소 붙여넣기 → 저장</li>
<li>크롬 설정 → 동기화에서 <b>북마크</b> 켜기 (이북리더기 크롬도 같은 구글 계정)</li></ol>
<h3>파이어폭스</h3>
<ol><li>아무 쪽에서 ⋮ → ☆ 책갈피 → <b>수정</b>, 이름 <b>넘김</b>, URL에 복사한 주소 붙여넣기 → 저장</li>
<li>⋮ → 설정 → <b>동기화</b>(Firefox 계정)에서 북마크 켜기. 이북리더기 파이어폭스도 같은 계정으로 로그인하면 책갈피가 넘어와요.</li></ol>
<h2>3. 이북리더기에서 쓰기</h2>
<ol><li>읽을 글(종이 자판기의 '원문' 링크 등)을 연다</li>
<li><b>주소창을 누르고 넘김 이라고 친다</b> → 아래 추천 목록에 뜬 ☆ <b>넘김</b> 책갈피를 누른다</li>
<li>본문이 넘김 화면으로 바뀌어요. 다 읽고 ✕ 누르면 원래 화면</li></ol>
<p class="note">책갈피 목록에서 바로 누르면 안 되는 브라우저가 많아요. 꼭 <b>주소창에 이름을 쳐서</b> 고르세요. 파이어폭스(안드로이드)는 버전에 따라 책갈피 실행이 막혀 있을 때가 있어요. 그러면 크롬이나 아래 EinkBro를 쓰세요.</p>
<h2>더 편한 방법: EinkBro 브라우저</h2>
<p>이북리더기 전용 무료 브라우저예요. 화면 가장자리 누르기나 음량(쪽 넘김) 키로 <b>모든 웹 쪽을 넘김</b>으로 보고, 읽기 모드·글자 크기·전체화면도 있어요. 책갈피 없이 늘 넘김이라 이북에서는 이게 가장 편해요.</p>
<ul><li>받는 곳: ${ext("https://f-droid.org/packages/info.plateaukao.einkbro/", "F-Droid의 EinkBro")} 또는 ${ext("https://plateaukao.github.io/einkbro/download.html", "EinkBro 내려받기 쪽")}(arm64-v8a 고르기)</li>
<li>북스는 설정에서 앱별로 쪽 넘김 버튼이 '한 화면만큼 스크롤'하게 바꿀 수도 있어요. 그러면 크롬·파이어폭스에서도 버튼으로 넘길 수 있어요.</li></ul>
<script>(function(){var b=document.getElementById("cp"),t=document.getElementById("bm"),o=document.getElementById("cpok");if(!b)return;b.addEventListener("click",function(e){e.preventDefault();e.stopPropagation();var v=t.value;function ok(){o.textContent=" 복사했어요";}function sel(){t.parentNode.open=true;t.focus();t.select();try{document.execCommand("copy");ok();}catch(x){o.textContent=" 위 칸을 길게 눌러 복사하세요";}}try{navigator.clipboard.writeText(v).then(ok,sel);}catch(x){sel();}},true);})();</script>` });
  return "web.html";
}

/* ── 처음 화면 ── */
function main() {
  if (process.env.EBOOK_ONLY === "hub") {   // 영업 허브 아티팩트에 넣을 종이판만 따로
    fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(path.join(OUT, "e.css"), CSS); fs.writeFileSync(path.join(OUT, "e.js"), JS);
    const d = JSON.parse(fs.readFileSync(process.env.EBOOK_HUB_DATA, "utf8"));
    require("./ebook_hub.js")({ esc, inl, md, sec, ul, ext, page, paged, quizHtml }, { data: d, B: "", label: SITE, home: true, compact: true, at: process.env.EBOOK_HUB_AT || "" });
    console.log(`[ebook] 영업 허브 종이판 ${pages}장 → ${OUT}`); return;
  }
  fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, "e.css"), CSS);
  fs.writeFileSync(path.join(OUT, "e.js"), JS);
  /* 홈 화면에 추가하면 처음부터 전체화면으로 열려요 */
  fs.writeFileSync(path.join(OUT, "manifest.webmanifest"), JSON.stringify({ name: "종이 자판기", short_name: "종이 자판기", start_url: "./index.html", scope: "./", display: "fullscreen", background_color: "#ffffff", theme_color: "#ffffff", icons: [{ src: "../assets/icon-192.png", sizes: "192x192", type: "image/png" }] }));
  const learned = LEARN.map(buildLearn);   // 교실 먼저 (브리핑이 낱말에 이어 붙어요)
  const s = buildSisa(), a = buildAi(), d = buildDeal(), t = buildTools(), tr = buildTrends(), web = buildWeb();
  /* 다른 자판기(이야기·사람·뷰티게임) — robot/ebook_more.js. 저장소가 없으면 그 부분만 건너뛰어요 */
  let more = [];
  try { more = require("./ebook_more.js")({ ROOT, rd, ls, esc, inl, md, sec, ul, ext, host, when, krw, num, cc, page, paged, comic, toon, longRead, quizHtml, briefings, bgLinks, learnInfo, now }); }
  catch (e) { console.warn("[ebook] 다른 자판기 건너뜀:", e.stack || e.message); }
  const d0 = now;
  const li = (href, name, desc) => `<li><a href="@${href}">${esc(name)}</a><br><small>${esc(desc)}</small></li>`;
  const body = `<p class="sub">${d0.getUTCMonth() + 1}월 ${d0.getUTCDate()}일 ${W[d0.getUTCDay()]}요일 · ${String(d0.getUTCHours()).padStart(2, "0")}:${String(d0.getUTCMinutes()).padStart(2, "0")}에 새로 만듦</p>
<p>자판기를 이북리더기로 읽기 좋게 옮긴 판이에요. 움직이는 것 없이 글만 있고, 한 장씩 넘겨 읽어요.</p>
<h2>오늘 읽기</h2><ul class="list home">
${li("sisa/index.html", "시사", s.label || "세계 뉴스를 한국어로")}
${li("ai/index.html", "AI", a.label || "AI 서비스 새 기능·인기 논문")}
${li("deal/index.html", "딜", d.label || "세계 투자 유치·인수합병·상장·펀드")}
${t ? li("tools/index.html", "도구", "요즘 뜨는 AI 도구·오픈소스 · " + when(t.at)) : ""}
${li("trends/index.html", "트렌드", `${tr.n}개 나라 검색어·영상 순위`)}
</ul>
<h2>교실</h2><ul class="list home">
${learned.map(l => li(`learn/${l.app}/index.html`, l.label, `${l.desc} · ${l.n}`)).join("\n")}
</ul>
${more.map(g => `<h2>${esc(g.h)}</h2><ul class="list home">${g.items.map(x => li(x[0], x[1], x[2])).join("\n")}</ul>`).join("\n")}
${web ? `<h2>웹 글도 넘김으로</h2><ul class="list home">${li(web, "웹 글도 넘김으로 보기", "원문 기사로 넘어가도 넘김 방식으로 — 책갈피 하나로 크롬·파이어폭스, 또는 EinkBro")}</ul>` : ""}
<h2>보기 방식</h2>
<p><b>전체화면</b>: 맨 위 오른쪽 '전체화면'을 누르면 켜지고, '전체화면 끄기'를 누르면 일반 화면으로 돌아와요. 고른 것은 이 기기에 기억해요. 쪽을 넘기거나 링크를 눌러도 전체화면이 쭉 이어져요. 사이트를 처음 열었을 때만 브라우저 규칙상 한 번 눌러야 다시 켜져요(넘기기 한 번이면 돼요). 브라우저 메뉴 → <b>홈 화면에 추가</b>로 열면 처음부터 전체화면이에요.</p>
<p>맨 위 오른쪽 <b>스크롤 · 넘김</b>으로 바꿔요. 넘김은 책처럼 한 화면씩 끊어서, 화면 오른쪽을 누르거나 왼쪽으로 밀면 다음, 왼쪽을 누르거나 오른쪽으로 밀면 앞으로 가요(북스 옆 버튼을 '쪽 넘김 키'로 맞춰 두면 버튼으로도 넘어가요). 글 끝에서 더 넘기면 다음 글로 이어져요. 고른 방식은 이 기기에 기억해요.</p>
<h2>이 판에 대해</h2>
<p>뉴스는 로봇이 자료를 모을 때마다 다시 만들어져요. 퀴즈는 '정답 보기'를 눌러 확인하고, 만화는 대화 글로 바꿨어요.</p>
<p>라디오·univ.·한 달 퀘스트·보관함·점수판·랜덤 카드처럼 움직이거나 이 기기 기록이 필요한 것은 뺐어요. 그런 건 <a href="../">원래 자판기</a>에서 보면 돼요.</p>`;
  page("index.html", { title: "종이 자판기", crumbs: [], body, h1: true });
  console.log(`[ebook] ${pages}장 만듦 → ebook/`);
}
main();
