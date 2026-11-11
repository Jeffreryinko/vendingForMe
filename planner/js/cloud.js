// 서버와 이어지는 부분: 구글 로그인 · 기록 맞추기 · 구글 캘린더 · 폰 알림 · 공유 링크
import * as db from './db.js';
import { today, addDays, toMin } from './util.js';
import { cat } from './model.js';

const CFG = window.PLANNER_CONFIG || {};
const LS = { gtok: 'planner:gtok', gcal: 'planner:gcal', gpending: 'planner:gpending' };
const ls = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* 저장 불가 */ } },
  del: k => { try { localStorage.removeItem(k); } catch { /* 무시 */ } },
};

export const cloud = { available: false, user: null, booted: false, gstate: 'off', gdetail: '' };
// gstate: off(연결 안 함) | ok | expired(다시 연결 필요) | api_off(구글 콘솔에서 캘린더 API 꺼짐) | error
let sb = null;
const listeners = new Set();
export const onCloud = fn => listeners.add(fn);
const emit = () => listeners.forEach(fn => { try { fn(); } catch (e) { console.error(e); } });

function loadLib() {
  if (window.supabase) return Promise.resolve();
  return new Promise((ok, no) => {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js';
    s.crossOrigin = 'anonymous';
    s.onload = ok; s.onerror = () => no(new Error('로그인 도구를 불러오지 못했어요'));
    document.head.append(s);
  });
}

export async function init() {
  const test = window.__PLANNER_TEST__;           // 자동 검사용 가짜 서버
  if (test) { cloud.available = true; cloud.user = test.user; db.setRemote(test.remote); cloud.booted = true; emit(); db.sync(); return; }
  if (!CFG.url || !CFG.key) { cloud.booted = true; emit(); return; }
  try {
    await loadLib();
    sb = window.supabase.createClient(CFG.url, CFG.key, { auth: { persistSession: true, detectSessionInUrl: true, flowType: 'pkce' } });
    cloud.available = true;
    sb.auth.onAuthStateChange((event, session) => setTimeout(() => applySession(session), 0));
    const { data } = await sb.auth.getSession();
    await applySession(data.session);
  } catch (e) {
    console.warn(e);
  }
  cloud.booted = true; emit();
}

let lastUid;
async function applySession(session) {
  const user = session?.user || null;
  // 구글 캘린더 연결 직후: 구글이 준 토큰을 받아 둠 (이 순간에만 받을 수 있음)
  if (session?.provider_token && ls.get(LS.gpending)) {
    ls.del(LS.gpending);
    ls.set(LS.gtok, JSON.stringify({ t: session.provider_token, exp: Date.now() + 50 * 60e3 }));
    ls.set(LS.gcal, '1');
    cloud.gstate = 'ok';
    if (session.provider_refresh_token) { try { await sb.rpc('planner_google_set', { p_token: session.provider_refresh_token }); } catch (e) { console.warn(e); } }
  }
  if (lastUid !== undefined && (user?.id || null) === lastUid) return;
  lastUid = user?.id || null;
  cloud.user = user ? { id: user.id, email: user.email, name: user.user_metadata?.full_name || user.user_metadata?.name || '' } : null;
  if (!user) { db.setRemote(null); emit(); return; }
  if (db.meta.uid && db.meta.uid !== user.id) await db.wipe();     // 다른 계정의 기록이 이 기기에 남아 있으면 비움
  db.setRemote({
    uid: user.id,
    pull: async cursor => {
      const { data, error } = await sb.from('planner_items').select('id,kind,data,updated_at,deleted,rev').gt('rev', cursor).order('rev').limit(1000);
      if (error) throw error;
      return data;
    },
    push: async rows => {
      const { error } = await sb.from('planner_items').upsert(rows.map(r => ({ ...r, user_id: user.id })), { onConflict: 'user_id,id' });
      if (error) throw error;
    },
  });
  emit();
  db.sync();
}

const redirectTo = () => location.origin + location.pathname;
export function login() {
  if (!sb) throw new Error('지금은 로그인할 수 없어요. 인터넷 연결을 확인해 주세요.');
  return sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: redirectTo() } });
}
export async function logout() {
  await db.sync();
  if (db.dirtyCount() && !confirm('아직 서버에 올리지 못한 기록이 있어요. 그래도 로그아웃하면 이 기기에서 지워집니다. 계속할까요?')) return false;
  try { await pushDisable(); } catch { /* 무시 */ }
  [LS.gtok, LS.gcal, LS.gpending].forEach(ls.del);
  await sb.auth.signOut();
  await db.wipe();
  cloud.gstate = 'off';
  return true;
}

// ── 구글 캘린더 ───────────────────────────────────────────────────────
const GCAL = 'https://www.googleapis.com/calendar/v3/calendars/primary/events';
export function gcalConnect() {
  if (!sb) throw new Error('지금은 연결할 수 없어요.');
  ls.set(LS.gpending, '1');
  return sb.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: redirectTo(), scopes: 'https://www.googleapis.com/auth/calendar.events', queryParams: { access_type: 'offline', prompt: 'consent' } },
  });
}
export async function gcalDisconnect() {
  [LS.gtok, LS.gcal].forEach(ls.del);
  cloud.gstate = 'off';
  try { await sb.rpc('planner_google_clear'); } catch { /* 무시 */ }
  emit();
}
export const gcalWanted = () => ls.get(LS.gcal) === '1';

let fnTried = 0;
async function gToken(force) {
  if (!cloud.user) return null;
  let cached = null;
  try { cached = JSON.parse(ls.get(LS.gtok) || 'null'); } catch { /* 없음 */ }
  if (!force && cached && cached.exp > Date.now() + 30e3) { cloud.gstate = 'ok'; return cached.t; }
  if (!sb) return null;
  if (!gcalWanted() && fnTried) return null;                 // 이 기기에서 연결한 적이 없으면 한 번만 확인
  if (Date.now() - fnTried < 60e3 && !force) return null;
  fnTried = Date.now();
  let r;
  try {
    const { data } = await sb.auth.getSession();
    const res = await fetch(CFG.fn, { method: 'POST', headers: { 'Content-Type': 'application/json', apikey: CFG.key, Authorization: 'Bearer ' + data.session.access_token }, body: JSON.stringify({ op: 'gtoken' }) });
    r = await res.json();
  } catch { r = { error: 'net' }; }
  if (r.access_token) {
    ls.set(LS.gtok, JSON.stringify({ t: r.access_token, exp: Date.now() + (Number(r.expires_in || 3600) - 120) * 1000 }));
    ls.set(LS.gcal, '1');
    cloud.gstate = 'ok'; emit();
    return r.access_token;
  }
  const was = cloud.gstate;
  if (r.error === 'not_connected' && !gcalWanted()) cloud.gstate = 'off';
  else if (r.error === 'net') cloud.gstate = gcalWanted() ? 'error' : 'off';
  else cloud.gstate = gcalWanted() ? 'expired' : 'off';
  cloud.gdetail = r.error || '';
  if (was !== cloud.gstate) emit();
  return null;
}
async function gfetch(url, opt = {}, retry = true) {
  const t = await gToken();
  if (!t) { const e = new Error('no token'); e.code = 'notoken'; throw e; }
  const res = await fetch(url, { ...opt, headers: { Authorization: 'Bearer ' + t, 'Content-Type': 'application/json' } });
  if (res.status === 401 && retry) { ls.del(LS.gtok); fnTried = 0; return gfetch(url, opt, false); }
  if (res.status === 403) {
    const j = await res.clone().json().catch(() => ({}));
    const reason = j.error?.errors?.[0]?.reason || j.error?.status || '';
    if (/accessNotConfigured|SERVICE_DISABLED|PERMISSION_DENIED/i.test(reason + ' ' + (j.error?.message || ''))) { cloud.gstate = 'api_off'; cloud.gdetail = j.error?.message || ''; emit(); }
    else if (/insufficient/i.test(reason + (j.error?.message || ''))) { cloud.gstate = 'expired'; emit(); }
  }
  return res;
}
const hm = d => `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
const eventCache = new Map();
export const gEventsCached = date => eventCache.get(date) || [];
export async function gEvents(date) {
  if (!cloud.user || (!gcalWanted() && cloud.gstate === 'off' && fnTried)) return [];
  const from = new Date(date + 'T00:00:00'), to = new Date(date + 'T23:59:59');
  const q = new URLSearchParams({ timeMin: from.toISOString(), timeMax: to.toISOString(), singleEvents: 'true', orderBy: 'startTime', maxResults: '50' });
  let res;
  try { res = await gfetch(`${GCAL}?${q}`); } catch { return gEventsCached(date); }
  if (!res.ok) return gEventsCached(date);
  const json = await res.json();
  const list = (json.items || [])
    .filter(ev => ev.status !== 'cancelled' && ev.extendedProperties?.private?.planner !== '1')
    .map(ev => {
      if (ev.start?.date) return { id: ev.id, title: ev.summary || '(제목 없음)', allDay: true, link: ev.htmlLink };
      const s = new Date(ev.start.dateTime), e = new Date(ev.end.dateTime);
      return { id: ev.id, title: ev.summary || '(제목 없음)', allDay: false, link: ev.htmlLink, start: s < from ? '00:00' : hm(s), end: e > to ? '23:59' : hm(e) };
    })
    .filter(ev => ev.allDay || toMin(ev.end) > toMin(ev.start));
  eventCache.set(date, list);
  return list;
}

const gHash = b => [b.date, b.start, b.end, b.title, b.done ? 1 : 0, b.cat || 0].join('|');
function gBody(b) {
  let tz = 'Asia/Seoul';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || tz; } catch { /* 기본값 */ }
  const c = b.routine ? null : cat(b.cat);
  return {
    summary: (b.done ? '✓ ' : '') + b.title,
    description: ['매일 업무 플래너', c && c.id ? c.name : null, ...(b.tags || []).map(t => '#' + t)].filter(Boolean).join(' · '),
    start: { dateTime: `${b.date}T${b.start}:00`, timeZone: tz },
    end: { dateTime: `${b.date}T${b.end}:00`, timeZone: tz },
    colorId: c?.g,
    reminders: { useDefault: false, overrides: [] },     // 알림은 플래너가 보내므로 구글 알림은 끔 (두 번 울리지 않게)
    extendedProperties: { private: { planner: '1' } },
  };
}
let gBusy = false, gTimer = null;
export function gPushSoon(ms = 7000) { clearTimeout(gTimer); gTimer = setTimeout(gPush, ms); }
// 바뀐 블록만 구글 캘린더에 반영. 일정 id 를 블록 id 에서 만들기 때문에 기기가 여러 대여도 중복이 생기지 않음
export async function gPush() {
  if (gBusy || !cloud.user || !gcalWanted() || cloud.gstate === 'api_off' || cloud.gstate === 'expired') return;
  const s = db.settings(), since = addDays(today(), -1);
  const todo = [];
  for (const b of db.items.values()) {
    if (b.kind !== 'block') continue;
    if (b.d) { if (b.gs) todo.push(b); continue; }
    if (b.routine && !s.gcalRoutines) { if (b.gs) todo.push({ ...b, d: 1, _keep: 1 }); continue; }
    if (b.gs ? b.gs !== gHash(b) : b.date >= since) todo.push(b);
  }
  if (!todo.length) return;
  gBusy = true;
  try {
    for (const b of todo.slice(0, 60)) {
      const url = `${GCAL}/pl${b.id}`;
      if (b.d) {
        const res = await gfetch(url, { method: 'DELETE' });
        if (res.ok || res.status === 404 || res.status === 410) {
          db.patchRaw(b.id, { gs: '' });
        } else break;
        continue;
      }
      const body = JSON.stringify(gBody(b));
      let res = await gfetch(url, { method: 'PATCH', body });
      if (res.status === 404) res = await gfetch(GCAL, { method: 'POST', body: JSON.stringify({ ...gBody(b), id: 'pl' + b.id }) });
      if (res.status === 409) res = await gfetch(url, { method: 'PATCH', body: JSON.stringify({ ...gBody(b), status: 'confirmed' }) });
      if (res.ok || res.status === 409 || res.status === 410) { const cur = db.get(b.id); if (cur) db.patch(b.id, { gs: gHash(cur) }); }
      else break;
    }
  } catch (e) { if (e.code !== 'notoken') console.warn('gcal', e); }
  gBusy = false;
}

// ── 폰 알림 (웹 푸시) ─────────────────────────────────────────────────
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
const b64ToU8 = b64 => { const p = '='.repeat((4 - b64.length % 4) % 4); return Uint8Array.from(atob((b64 + p).replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0)); };

export async function pushStatus() {
  if (!cloud.user) return { on: false, can: false, text: '알림은 로그인한 뒤에 켤 수 있어요.' };
  if (!('serviceWorker' in navigator) || !('PushManager' in window))
    return { on: false, can: false, text: isIOS && !standalone() ? '아이폰은 Safari 공유 버튼 → "홈 화면에 추가"를 한 뒤, 홈 화면 아이콘으로 열어야 알림을 켤 수 있어요.' : '이 브라우저는 알림을 지원하지 않아요.' };
  if (Notification.permission === 'denied') return { on: false, can: false, text: '알림이 차단돼 있어요. 휴대폰(브라우저) 설정에서 이 사이트의 알림을 허용해 주세요.' };
  const reg = await navigator.serviceWorker.getRegistration();
  const sub = reg && await reg.pushManager.getSubscription();
  return sub ? { on: true, can: true, text: '이 기기에서 알림을 받고 있어요.' } : { on: false, can: true, text: '이 기기는 아직 알림이 꺼져 있어요.' };
}
export async function pushEnable() {
  if (await Notification.requestPermission() !== 'granted') throw new Error('알림 권한이 허용되지 않았어요.');
  const { data: key, error } = await sb.rpc('planner_vapid_public');
  if (error || !key) throw new Error('알림 서버가 아직 준비되지 않았어요. (서버 설정 필요)');
  const reg = await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (sub && sub.options?.applicationServerKey && btoa(String.fromCharCode(...new Uint8Array(sub.options.applicationServerKey))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') !== key) { await sub.unsubscribe(); sub = null; }
  if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToU8(key) });
  const j = sub.toJSON();
  const { error: e2 } = await sb.from('planner_push_subs').upsert({ endpoint: j.endpoint, p256dh: j.keys.p256dh, auth: j.keys.auth, ua: navigator.userAgent.slice(0, 200), user_id: cloud.user.id });
  if (e2) throw new Error('기기를 등록하지 못했어요: ' + e2.message);
  db.setSettings({});          // 시간대(tz)를 서버에 알려 둠
}
export async function pushDisable() {
  const reg = 'serviceWorker' in navigator && await navigator.serviceWorker.getRegistration();
  const sub = reg && await reg.pushManager.getSubscription();
  if (!sub) return;
  if (sb && cloud.user) await sb.from('planner_push_subs').delete().eq('endpoint', sub.endpoint);
  await sub.unsubscribe();
}
export async function pushTest() {
  const { data, error } = await sb.rpc('planner_push_test');
  if (error) throw new Error(error.message);
  return data;
}

// ── 공유 링크 ─────────────────────────────────────────────────────────
export const shareUrl = id => `${location.origin}${location.pathname}?s=${id}`;
export async function shareSave(id, payload) {
  const { error } = await sb.from('planner_shares').upsert({ id, payload, user_id: cloud.user.id, updated_at: new Date().toISOString() });
  if (error) throw new Error(error.message);
}
export async function shareDelete(id) {
  const { error } = await sb.from('planner_shares').delete().eq('id', id);
  if (error) throw new Error(error.message);
}
export async function shareGet(id) {            // 로그인 없이 읽기 (주소를 아는 사람만)
  const res = await fetch(`${CFG.url}/rest/v1/rpc/planner_share_get`, { method: 'POST', headers: { apikey: CFG.key, Authorization: 'Bearer ' + CFG.key, 'Content-Type': 'application/json' }, body: JSON.stringify({ p_id: id }) });
  if (!res.ok) throw new Error('공유된 일정을 불러오지 못했어요.');
  return res.json();
}
