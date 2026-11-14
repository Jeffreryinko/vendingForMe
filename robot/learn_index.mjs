// 배움 글 목록 만들기 — 브리핑 로봇이 '배경'으로 연결할 수 있는 낱말·역사·코스 번호표
//   node robot/learn_index.mjs [sisa|deal]  →  data/<앱>/learn_index.json  (배움 글을 더하거나 고친 뒤 한 번 돌림)
import fs from "node:fs"; import vm from "node:vm"; import path from "node:path";
const APP = process.argv[2] || "sisa", dir = APP + "/learn", html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
const files = [...html.matchAll(/<script src="([^"?]+\.js)(?:\?[^"]*)?"/g)].map(m => m[1]).filter(f => !f.includes("/") && !/^(learn|art|figs)/.test(f));
const window = {}, ctx = { window, console: { log() {}, warn() {}, error() {} }, document: { createElement: () => ({}), head: { appendChild() {} } } };
ctx.globalThis = ctx; vm.createContext(ctx);
for (const f of files) { try { vm.runInContext("with(window){" + fs.readFileSync(path.join(dir, f), "utf8") + "\n}", ctx, { filename: f }); } catch (e) { console.error("건너뜀", f, e.message); } }
const L = window.VFM_LEARN || {}, T = window.VFM_TERMS || [];
const out = { term: {}, hist: {}, ch: {}, def: {} };
for (const t of T) { out.term[t.id] = t.t || t.id; if (t.s) out.def[t.id] = t.s; }
for (const h of L.history || []) if (!h.virt) out.hist[h.id] = h.name;
for (const c of L.chapters || []) out.ch[c.id] = c.t;
fs.writeFileSync("data/" + APP + "/learn_index.json", JSON.stringify(out));
console.log("낱말", Object.keys(out.term).length, "역사", Object.keys(out.hist).length, "코스", Object.keys(out.ch).length);
