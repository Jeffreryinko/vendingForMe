// 플래너의 규칙: 할 일·시간 블록·하루 기록을 다루는 동작과 통계, 내보내기
import * as db from './db.js';
import { today, ymd, addDays, toMin, toHm, nowMin, newId, isWeekend, dow, WD, parseQuick, fmtMD, fmtFull, csvCell, mondayOf, diffDays } from './util.js';

// ── 분류 (업무의 성격) ────────────────────────────────────────────────
const BASE_CATS = [
  { id: 0, name: '분류 전', hint: '나중에 성격을 정할 일', dur: 30 },
  { id: 1, name: '119 긴급한 일', hint: '오늘 반드시 처리', dur: 60, g: '11' },
  { id: 2, name: '금방 할 수 있는 일', hint: '30분 안에 끝낼 일', dur: 30, g: '10' },
  { id: 3, name: '오래 고민해야 하는 일', hint: '집중 시간 확보', dur: 90, g: '3' },
  { id: 4, name: '협업이 필요한 일', hint: '요청하고 함께 진행', dur: 60, g: '9' },
  { id: 5, name: '빠르게 시켜야 할 일', hint: '아침에 먼저 넘기기', dur: 30, g: '6' },
  { id: 6, name: '중요하게 해야 할 일', hint: '긴급하진 않지만 핵심', dur: 60, g: '7' },
];
export const cat = id => { const b = BASE_CATS[id] || BASE_CATS[0]; return { ...b, ...(db.settings().cats?.[b.id] || {}) }; };
export const cats = () => [1, 2, 3, 4, 5, 6].map(cat);

export const TAG_COLORS = ['#5B6CFF', '#0E9488', '#E08A1E', '#C2410C', '#B4358B', '#2F9E5B', '#64748B', '#7A55C7'];
export function tags() { return db.settings().tags || []; }
export function tagColor(name) {
  const t = tags().find(t => t.name === name);
  if (t?.color) return t.color;
  let x = 0; for (const ch of name) x = (x * 31 + ch.codePointAt(0)) >>> 0;
  return TAG_COLORS[x % TAG_COLORS.length];
}
export function ensureTags(names) {
  const cur = tags();
  const add = names.filter(n => n && !cur.some(t => t.name === n));
  if (add.length) db.setSettings({ tags: [...cur, ...add.map((name, i) => ({ name, color: TAG_COLORS[(cur.length + i) % TAG_COLORS.length] }))] });
}
export function renameTag(from, to) {
  to = to.trim().replace(/[\s#@!]/g, '');
  if (!to || to === from) return;
  for (const kind of ['task', 'block']) for (const it of [...db.list(kind)]) {
    if (it.tags?.includes(from)) db.patch(it.id, { tags: [...new Set(it.tags.map(t => t === from ? to : t))] });
  }
  db.setSettings({ tags: tags().filter(t => t.name !== to).map(t => t.name === from ? { ...t, name: to } : t) });
}
export function removeTag(name) {
  for (const kind of ['task', 'block']) for (const it of [...db.list(kind)]) {
    if (it.tags?.includes(name)) db.patch(it.id, { tags: it.tags.filter(t => t !== name) });
  }
  db.setSettings({ tags: tags().filter(t => t.name !== name) });
}

// ── 할 일 ────────────────────────────────────────────────────────────
export const tasks = () => db.list('task');
export const isOpen = t => (t.st || 'open') === 'open';

export function addTask(f) {
  ensureTags(f.tags || []);
  return db.put({ id: newId(), kind: 'task', title: f.title.trim().slice(0, 300), cat: f.cat ?? 0, tags: f.tags || [], who: f.who || '', due: f.due || '', note: f.note || '', st: 'open', at: Date.now(), doneAt: null });
}
export function updateTask(id, f) {
  if (f.tags) ensureTags(f.tags);
  const t = db.patch(id, f);
  if (t && ('title' in f || 'cat' in f || 'tags' in f)) {
    for (const b of [...db.list('block')]) if (b.taskId === id && !b.done) db.patch(b.id, { title: t.title, cat: t.cat, tags: t.tags });
  }
  return t;
}
export function setTaskDone(t, done) {
  db.patch(t.id, { st: done ? 'done' : 'open', doneAt: done ? Date.now() : null });
  const td = today();
  for (const b of [...db.list('block')]) {
    if (b.taskId !== t.id) continue;
    if (done && !b.done && b.date <= td) db.patch(b.id, { done: true });
    if (!done && b.done && b.date === td) db.patch(b.id, { done: false });
  }
}
export const setTaskWait = (t, wait) => db.patch(t.id, { st: wait ? 'wait' : 'open', waitAt: wait ? Date.now() : null, doneAt: null });

export function removeTask(id) {
  const t = db.get(id);
  if (!t) return () => {};
  const td = today();
  const gone = db.list('block').filter(b => b.taskId === id && !b.done && b.date >= td);
  gone.forEach(b => db.del(b.id));
  db.del(id);
  return () => { db.put(t); gone.forEach(b => db.put(b)); };
}

// 이 할 일에 붙어 있는 다음 시간 블록
export function nextBlockOf(taskId) {
  const td = today();
  let best = null;
  for (const b of db.list('block')) {
    if (b.taskId !== taskId || b.done || b.date < td) continue;
    if (!best || (b.date + b.start) < (best.date + best.start)) best = b;
  }
  return best;
}

// ── 시간 블록 ─────────────────────────────────────────────────────────
export const blocksOn = date => db.list('block').filter(b => b.date === date).sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end));

export function addBlock(f) {
  ensureTags(f.tags || []);
  let end = f.end;
  if (!end || toMin(end) <= toMin(f.start)) end = toHm(Math.min(toMin(f.start) + (f.dur || 30), 1439));
  return db.put({ id: newId(), kind: 'block', date: f.date, start: f.start, end, title: (f.title || '새 블록').trim().slice(0, 300), cat: f.cat ?? 0, tags: f.tags || [], taskId: f.taskId || null, done: false });
}
export function setBlockDone(b, done) {
  db.patch(b.id, { done, doneAt: done ? Date.now() : null });
  const t = b.taskId && db.get(b.taskId);
  if (t && (t.st === 'done') !== done) db.patch(t.id, { st: done ? 'done' : 'open', doneAt: done ? Date.now() : null });
}
export function removeBlock(id) {
  const b = db.get(id);
  if (!b) return () => {};
  db.del(id);
  return () => db.put(b);
}

export function freeSlot(date, dur, extraBusy = []) {
  const busy = [...blocksOn(date), ...extraBusy].map(x => [toMin(x.start), toMin(x.end)]);
  let s = 9 * 60;
  if (date === today()) s = Math.max(s, Math.ceil((nowMin() + 1) / 30) * 30);
  for (; s + dur <= 1439; s += 30) if (!busy.some(([a, b]) => s < b && a < s + dur)) return [toHm(s), toHm(s + dur)];
  return ['09:00', toHm(9 * 60 + dur)];
}
export function placeTask(t, date, start, end) {
  if (!start) [start, end] = freeSlot(date, cat(t.cat).dur);
  return addBlock({ date, start, end, dur: cat(t.cat).dur, title: t.title, cat: t.cat, tags: t.tags, taskId: t.id });
}

// 루틴(매일 깔리는 블록): 오늘~2주 뒤까지, 그 날짜를 처음 볼 때 한 번만 만듭니다.
export function seedDay(date) {
  const td = today();
  if (date < td || diffDays(date, td) > 14) return;
  const s = db.settings();
  for (const r of s.routines || []) {
    if (r.days !== 'all' && isWeekend(date)) continue;
    const id = 'r' + date.replaceAll('-', '') + r.id;
    if (db.has(id)) continue;
    db.putDefault({ id, kind: 'block', date, start: r.start, end: r.end, title: r.title, cat: 0, tags: [], taskId: null, done: false, routine: r.id });
  }
}

// ── 하루 기록 (핵심 3 · 한 줄 회고 · 마감 도장) ─────────────────────────
export const dayOf = date => db.get('day:' + date) || { id: 'day:' + date, kind: 'day', date, top: [], note: '', closedAt: null };
export const setDay = (date, f) => db.put({ ...dayOf(date), ...f });
export function topTasks(date) { return (dayOf(date).top || []).map(id => db.get(id)).filter(Boolean); }
export function toggleTop(date, taskId) {
  const d = dayOf(date);
  const top = (d.top || []).filter(id => db.get(id));
  if (top.includes(taskId)) { setDay(date, { top: top.filter(x => x !== taskId) }); return true; }
  if (top.length >= 3) return false;
  setDay(date, { top: [...top, taskId] });
  return true;
}

// ── 빠르게 적기 ───────────────────────────────────────────────────────
export function quickAdd(text, opt = {}) {
  const p = parseQuick(text, opt.date || today());
  if (!p.title) return null;
  const c = p.cat ?? opt.cat ?? 0;
  const task = addTask({ title: p.title, cat: c, tags: [...new Set([...(opt.tags || []), ...p.tags])], who: p.who, due: p.due || '' });
  let block = null;
  if (p.start) block = addBlock({ date: p.date, start: p.start, end: p.end, dur: p.dur || cat(c).dur, title: task.title, cat: c, tags: task.tags, taskId: task.id });
  return { task, block, parsed: p };
}

// ── 통계·레벨 ─────────────────────────────────────────────────────────
const TITLES = ['인턴', '애널리스트', '어소시에이트', '매니저', '시니어 매니저', '디렉터', '파트너', '시니어 파트너', '매니징 파트너', '레전드'];
const levelFloor = n => 200 * n * (n - 1);      // 레벨 10 ≈ 반년, 레벨 20 ≈ 2년, 레벨 28(레전드) ≈ 4년 꾸준히 썼을 때
let statCache = null;
db.on(() => { statCache = null; });

export function stats() {
  if (statCache) return statCache;
  const activity = new Map(), closed = new Set();
  const bump = (d, n = 1) => activity.set(d, (activity.get(d) || 0) + n);
  let xp = 0, doneTasks = 0;
  const doneDay = new Map();
  for (const t of db.list('task')) if (t.st === 'done' && t.doneAt) { const d = ymd(new Date(t.doneAt)); bump(d); doneDay.set(t.id, d); xp += 10; doneTasks++; }
  for (const b of db.list('block')) if (b.done && !b.taskId && !b.routine) { bump(b.date); xp += 5; }
  let topHit = 0, topSet = 0;
  for (const d of db.list('day')) {
    if (d.closedAt) { closed.add(d.date); xp += 15; }
    const top = (d.top || []).filter(id => db.get(id));
    const hit = top.filter(id => doneDay.get(id) === d.date).length;
    topSet += top.length; topHit += hit;
    xp += hit * 20 + (top.length >= 3 && hit === top.length ? 30 : 0);
  }
  const level = Math.floor((1 + Math.sqrt(1 + xp / 50)) / 2);
  const s = db.settings();
  let streak = 0, d = today();
  const active = x => (activity.get(x) || 0) > 0 || closed.has(x);
  if (!active(d)) d = addDays(d, -1);
  for (let i = 0; i < 4000; i++, d = addDays(d, -1)) {
    if (active(d)) streak++;
    else if (s.weekdaysOnly && isWeekend(d)) continue;
    else break;
  }
  statCache = { xp, level, title: TITLES[Math.min(Math.floor((level - 1) / 3), TITLES.length - 1)], floor: levelFloor(level), next: levelFloor(level + 1), streak, activity, closed, doneTasks, topHit, topSet };
  return statCache;
}

export function dayProgress(date) {
  const bl = blocksOn(date);
  const done = bl.filter(b => b.done).length;
  const top = topTasks(date);
  return { total: bl.length, done, pct: bl.length ? Math.round(done / bl.length * 100) : 0, top: top.length, topDone: top.filter(t => t.st === 'done').length,
    planned: bl.filter(b => !b.routine).reduce((n, b) => n + toMin(b.end) - toMin(b.start), 0) };
}

export function weekStats(monday) {
  const end = addDays(monday, 6);
  const byCat = {}, byTag = {};
  let planned = 0, doneMin = 0, blocks = 0, blocksDone = 0;
  for (const b of db.list('block')) {
    if (b.date < monday || b.date > end || b.routine) continue;
    const m = toMin(b.end) - toMin(b.start);
    blocks++; planned += m;
    if (!b.done) continue;
    blocksDone++; doneMin += m;
    byCat[b.cat || 0] = (byCat[b.cat || 0] || 0) + m;
    for (const t of b.tags || []) byTag[t] = (byTag[t] || 0) + m;
  }
  let tasksDone = 0;
  for (const t of db.list('task')) if (t.st === 'done' && t.doneAt) { const d = ymd(new Date(t.doneAt)); if (d >= monday && d <= end) tasksDone++; }
  let topSet = 0, topHit = 0, closedDays = 0;
  const notes = [];
  for (const d of db.list('day')) {
    if (d.date < monday || d.date > end) continue;
    if (d.closedAt) closedDays++;
    if (d.note) notes.push({ date: d.date, note: d.note });
    const top = (d.top || []).map(id => db.get(id)).filter(Boolean);
    topSet += top.length;
    topHit += top.filter(t => t.st === 'done' && t.doneAt && ymd(new Date(t.doneAt)) === d.date).length;
  }
  notes.sort((a, b) => b.date.localeCompare(a.date));
  return { monday, end, byCat, byTag, planned, doneMin, blocks, blocksDone, tasksDone, topSet, topHit, closedDays, notes };
}

// ── 내보내기 (다른 도구로 옮기기 쉽게, 열어서 읽을 수 있는 형식만) ─────────
export function exportJson() {
  const all = [...db.items.values()].filter(it => !it.d).map(({ _dirty, ...it }) => it);
  return JSON.stringify({ app: '매일 업무 플래너', format: 'planner-backup', version: 1, exportedAt: new Date().toISOString(), items: all }, null, 1);
}
const ST = { open: '할 일', wait: '기다리는 중', done: '완료' };
const dt = ms => ms ? ymd(new Date(ms)) : '';
export function exportTasksCsv() {
  const rows = [['제목', '분류', '태그', '담당', '마감', '상태', '만든 날', '완료한 날', '메모']];
  for (const t of [...tasks()].sort((a, b) => (a.at || 0) - (b.at || 0)))
    rows.push([t.title, cat(t.cat).name, (t.tags || []).join(' '), t.who, t.due, ST[t.st || 'open'], dt(t.at), dt(t.doneAt), t.note]);
  return '﻿' + rows.map(r => r.map(csvCell).join(',')).join('\r\n');
}
export function exportBlocksCsv() {
  const rows = [['날짜', '요일', '시작', '끝', '길이(분)', '제목', '분류', '태그', '완료', '루틴']];
  for (const b of [...db.list('block')].sort((a, b) => (a.date + a.start).localeCompare(b.date + b.start)))
    rows.push([b.date, WD[dow(b.date)], b.start, b.end, toMin(b.end) - toMin(b.start), b.title, b.routine ? '' : cat(b.cat).name, (b.tags || []).join(' '), b.done ? 'O' : '', b.routine ? 'O' : '']);
  return '﻿' + rows.map(r => r.map(csvCell).join(',')).join('\r\n');
}
export function exportMarkdown() {
  const dates = new Set([...db.list('block').map(b => b.date), ...db.list('day').map(d => d.date)]);
  const out = ['# 업무 일지', ''];
  for (const date of [...dates].sort().reverse()) {
    const d = dayOf(date), bl = blocksOn(date);
    out.push(`## ${fmtFull(date)}${d.closedAt ? ' · 마감' : ''}`, '');
    const top = topTasks(date);
    if (top.length) out.push('**핵심** ' + top.map(t => (t.st === 'done' ? '✔ ' : '') + t.title).join(' / '), '');
    for (const b of bl) out.push(`- [${b.done ? 'x' : ' '}] ${b.start}–${b.end} ${b.title}${b.tags?.length ? ' ' + b.tags.map(t => '#' + t).join(' ') : ''}`);
    if (d.note) out.push('', '> ' + d.note.replace(/\n/g, '\n> '));
    out.push('');
  }
  return out.join('\n');
}

// ── 공유 ─────────────────────────────────────────────────────────────
export function dayText(date) {
  const lines = [`${fmtFull(date)} 일정`];
  const top = topTasks(date);
  if (top.length) lines.push('핵심: ' + top.map((t, i) => `${'①②③'[i]} ${t.title}`).join('  '));
  for (const b of blocksOn(date)) lines.push(`${b.start}–${b.end}  ${b.done ? '✔ ' : ''}${b.title}`);
  return lines.join('\n');
}
export function sharePayload(date, name) {
  return {
    v: 1, date, name: name || '', at: Date.now(),
    top: topTasks(date).map(t => ({ t: t.title, done: t.st === 'done' })),
    blocks: blocksOn(date).map(b => ({ s: b.start, e: b.end, t: b.title, c: b.routine ? 0 : (b.cat || 0), done: !!b.done })),
  };
}
export function requestText(t) {
  const parts = [`[요청] ${t.title}`];
  if (t.due) parts.push(`기한: ${fmtMD(t.due)}(${WD[dow(t.due)]})`);
  if (t.note) parts.push(t.note);
  return parts.join('\n');
}
