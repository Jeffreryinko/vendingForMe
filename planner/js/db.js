// 기록 저장소: 이 기기(IndexedDB)에 먼저 저장하고, 로그인돼 있으면 서버와 맞춥니다.
// 한 항목 = { id, kind, ...내용, u: 고친 시각(ms), d: 지워짐 표시 }.  kind: task | block | day | settings | share
const DB_NAME = 'daily-planner';
let idb = null;
let memoryOnly = false;

export const items = new Map();
export const meta = { cursor: 0, uid: null, lastFull: 0, lastSync: 0 };
export const status = { state: 'local', error: '' };   // local(로그인 안 함) | idle | syncing | error | offline

const listeners = new Set();
const byKind = new Map();
let emitQueued = false;
export const on = fn => { listeners.add(fn); return () => listeners.delete(fn); };
function emit() {
  if (emitQueued) return;
  emitQueued = true;
  queueMicrotask(() => { emitQueued = false; listeners.forEach(fn => { try { fn(); } catch (e) { console.error(e); } }); });
}
export const notify = emit;

function req(r) { return new Promise((ok, no) => { r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); }); }
function store(name, mode = 'readonly') { return idb.transaction(name, mode).objectStore(name); }

export async function open() {
  try {
    idb = await new Promise((ok, no) => {
      const r = indexedDB.open(DB_NAME, 1);
      r.onupgradeneeded = () => { r.result.createObjectStore('items', { keyPath: 'id' }); r.result.createObjectStore('meta'); };
      r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error);
    });
    for (const it of await req(store('items').getAll())) items.set(it.id, it);
    Object.assign(meta, (await req(store('meta').get('sync'))) || {});
  } catch (e) {
    console.warn('이 브라우저에서는 기기 저장을 쓸 수 없어 임시로만 기억합니다.', e);
    memoryOnly = true;
  }
}
function persist(it) { if (!memoryOnly) try { store('items', 'readwrite').put(it); } catch (e) { console.error(e); } }
function saveMeta() { if (!memoryOnly) try { store('meta', 'readwrite').put({ ...meta }, 'sync'); } catch (e) { console.error(e); } }

// ── 읽기 ─────────────────────────────────────────────────────────────
export const get = id => { const it = items.get(id); return it && !it.d ? it : null; };
export const has = id => items.has(id);            // 지워진 것도 포함 (같은 id 를 다시 만들지 않기 위해)
export function list(kind) {
  let arr = byKind.get(kind);
  if (!arr) { arr = []; for (const it of items.values()) if (it.kind === kind && !it.d) arr.push(it); byKind.set(kind, arr); }
  return arr;
}

// ── 쓰기 (항상 이 기기에 먼저) ─────────────────────────────────────────
function commit(it, dirty = true) {
  if (dirty) it._dirty = 1; else delete it._dirty;
  items.set(it.id, it);
  byKind.delete(it.kind);
  persist(it);
}
export function put(obj) {
  const it = { ...obj, u: Date.now() };
  delete it.d;
  commit(it);
  emit(); scheduleSync();
  return it;
}
// 기본값으로 깔아 두는 항목(루틴 블록): 고친 시각을 가장 옛날로 두어, 어디서든 사람이 고친 내용이 항상 이기게 함
export function putDefault(obj) { commit({ ...obj, u: 1 }); emit(); scheduleSync(); }
export function patch(id, fields) {
  const cur = items.get(id);
  if (!cur || cur.d) return null;
  return put({ ...cur, ...fields });
}
// 지워진 항목(흔적)까지 포함해 일부 값만 고침 — 구글 캘린더 반영 기록용
export function patchRaw(id, fields) {
  const cur = items.get(id);
  if (!cur) return;
  commit({ ...cur, ...fields, u: Date.now() });
  scheduleSync();
}
export function del(id) {
  const cur = items.get(id);
  if (!cur || cur.d) return;
  commit({ id: cur.id, kind: cur.kind, gs: cur.gs, date: cur.date, u: Date.now(), d: 1 });
  emit(); scheduleSync();
}
// 가져오기: 더 최신인 것만 받아들임
export function importItems(arr) {
  let n = 0;
  for (const raw of arr) {
    if (!raw || typeof raw.id !== 'string' || typeof raw.kind !== 'string') continue;
    const it = { ...raw, u: Number(raw.u) || Date.now() };
    delete it._dirty;
    const cur = items.get(it.id);
    if (cur && cur.u >= it.u) continue;
    commit(it); n++;
  }
  emit(); scheduleSync();
  return n;
}
export async function wipe() {
  items.clear(); byKind.clear();
  Object.assign(meta, { cursor: 0, uid: null, lastFull: 0, lastSync: 0 });
  if (!memoryOnly) { await req(store('items', 'readwrite').clear()); saveMeta(); }
  emit();
}

// ── 설정 ─────────────────────────────────────────────────────────────
export const DEFAULT_SETTINGS = {
  remindMin: 5, remindAtStart: true, morningTime: '08:50', weekdaysOnly: true, gcalRoutines: false,
  routines: [
    { id: 'lunch', start: '12:00', end: '13:00', title: '점심 · 휴식', days: 'wd' },
    { id: 'buffer', start: '15:00', end: '15:30', title: '여유 시간 · 돌발 업무', days: 'wd' },
    { id: 'close', start: '16:30', end: '17:00', title: '오늘 점검 · 내일 계획', days: 'wd' },
  ],
  tags: [], cats: {},
};
export function settings() { return { ...DEFAULT_SETTINGS, ...(get('settings') || {}) }; }
export function setSettings(fields) {
  const cur = get('settings') || { id: 'settings', kind: 'settings' };
  let tz = 'Asia/Seoul';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || tz; } catch { /* 기본값 */ }
  return put({ ...cur, ...fields, tz });
}

// ── 서버와 맞추기 ─────────────────────────────────────────────────────
let remote = null;       // { uid, pull(cursor) → rows, push(rows) }
let syncing = false, again = false, timer = null;
const WEEK = 7 * 864e5;

export function setRemote(r) {
  remote = r;
  status.state = r ? 'idle' : 'local';
  emit();
}
export const hasRemote = () => !!remote;
export const dirtyCount = () => { let n = 0; for (const it of items.values()) if (it._dirty) n++; return n; };

function toRow(it) {
  const { id, kind, u, d, _dirty, ...data } = it;
  return { id, kind, data, updated_at: u, deleted: !!d };
}
export function scheduleSync(ms = 1200) {
  if (!remote) return;
  clearTimeout(timer);
  timer = setTimeout(() => sync(), ms);
}
export async function sync(opts = {}) {
  if (!remote) return false;
  if (syncing) { again = true; return false; }
  syncing = true; status.state = 'syncing'; emit();
  try {
    if (meta.uid !== remote.uid) { meta.uid = remote.uid; meta.cursor = 0; }
    if (opts.full || Date.now() - (meta.lastFull || 0) > WEEK) { meta.cursor = 0; meta.lastFull = Date.now(); }   // 가끔은 전부 다시 확인
    // 1) 받기
    for (;;) {
      const rows = await remote.pull(meta.cursor);
      for (const row of rows) {
        const local = items.get(row.id);
        if (!(local && local._dirty && local.u > row.updated_at) && !(local && !local._dirty && local.u === row.updated_at)) {
          const it = { ...row.data, id: row.id, kind: row.kind, u: row.updated_at };
          if (row.deleted) it.d = 1;
          commit(it, false);
        }
        if (row.rev > meta.cursor) meta.cursor = row.rev;
      }
      if (rows.length < 1000) break;
    }
    // 2) 올리기
    const dirty = [...items.values()].filter(it => it._dirty);
    for (let i = 0; i < dirty.length; i += 200) {
      const chunk = dirty.slice(i, i + 200);
      await remote.push(chunk.map(toRow));
      for (const sent of chunk) {
        const cur = items.get(sent.id);
        if (cur && cur.u === sent.u) { delete cur._dirty; persist(cur); }
      }
    }
    meta.lastSync = Date.now(); saveMeta();
    status.state = 'idle'; status.error = '';
  } catch (e) {
    console.warn('sync', e);
    status.state = navigator.onLine === false ? 'offline' : 'error';
    status.error = e?.message || String(e);
  } finally {
    syncing = false; emit();
    if (again) { again = false; scheduleSync(300); }
  }
  return status.state === 'idle';
}
