// 공통 도우미: 날짜·시간 계산, 화면 조각 만들기, "빠르게 적기" 문장 해석
export const WD = ['일', '월', '화', '수', '목', '금', '토'];
const p2 = n => String(n).padStart(2, '0');

export const ymd = (d = new Date()) => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`;
export const today = () => ymd();
export const toDate = s => new Date(s + 'T12:00:00');
export const addDays = (date, n) => { const d = toDate(date); d.setDate(d.getDate() + n); return ymd(d); };
export const dow = date => toDate(date).getDay();
export const isWeekend = date => [0, 6].includes(dow(date));
export const diffDays = (a, b) => Math.round((toDate(a) - toDate(b)) / 864e5);
export const mondayOf = date => addDays(date, -((dow(date) + 6) % 7));
export const nextWorkday = (date, weekdaysOnly = true) => { let d = addDays(date, 1); while (weekdaysOnly && isWeekend(d)) d = addDays(d, 1); return d; };

export const toMin = hm => { const [h, m] = hm.split(':').map(Number); return h * 60 + m; };
export const toHm = m => { m = Math.max(0, Math.min(1439, Math.round(m))); return `${p2(Math.floor(m / 60))}:${p2(m % 60)}`; };
export const nowMin = () => { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); };
export const durText = min => min < 60 ? `${min}분` : (min % 60 ? `${Math.floor(min / 60)}시간 ${min % 60}분` : `${min / 60}시간`);
export const hoursText = min => (Math.round(min / 6) / 10) + '시간';

export const fmtMD = date => { const d = toDate(date); return `${d.getMonth() + 1}월 ${d.getDate()}일`; };
export const fmtShort = date => { const d = toDate(date); return `${d.getMonth() + 1}/${d.getDate()}`; };
export const fmtFull = date => { const d = toDate(date); return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 ${WD[d.getDay()]}요일`; };
export const relDay = date => { const n = diffDays(date, today()); return n === 0 ? '오늘' : n === 1 ? '내일' : n === -1 ? '어제' : n === 2 ? '모레' : `${fmtShort(date)}(${WD[dow(date)]})`; };
export function dueInfo(due) {
  const n = diffDays(due, today());
  if (n < 0) return { text: `${-n}일 지남`, cls: 'late' };
  if (n === 0) return { text: '오늘까지', cls: 'soon' };
  if (n === 1) return { text: '내일까지', cls: 'soon' };
  return { text: n <= 14 ? `D-${n}` : `${fmtShort(due)}까지`, cls: '' };
}

// 구글 캘린더 일정 id 로도 쓸 수 있는 글자(0-9, a-v)만 사용
const ID_CHARS = '0123456789abcdefghijklmnopqrstuv';
export const newId = (len = 16) => Array.from(crypto.getRandomValues(new Uint8Array(len)), b => ID_CHARS[b & 31]).join('');

export const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// 화면 조각 만들기: h('div', {class:'x', onclick: fn}, 자식...)
export function h(tag, attrs, ...kids) {
  const n = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (k === 'class') n.className = v;
    else if (k === 'style') n.style.cssText = v;
    else if (k === 'value') n.value = v;
    else if (k === 'checked') n.checked = !!v;
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat(Infinity)) if (k != null && k !== false && k !== '') n.append(k);
  return n;
}
const SVG_NS = 'http://www.w3.org/2000/svg';
export function svg(tag, attrs, ...kids) {
  const n = document.createElementNS(SVG_NS, tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) if (v != null && v !== false) n.setAttribute(k, v);
  for (const k of kids.flat()) if (k != null) n.append(k);
  return n;
}
const ICONS = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  plus: 'M12 5v14M5 12h14',
  left: 'M15 5l-7 7 7 7',
  right: 'M9 5l7 7-7 7',
  clock: 'M12 7v5l3 2M12 3a9 9 0 100 18 9 9 0 000-18z',
  star: 'M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z',
  gear: 'M12 15.2a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4zM19 12a7 7 0 00-.1-1.3l2-1.5-2-3.4-2.3.9a7 7 0 00-2.2-1.3L14 3h-4l-.4 2.4a7 7 0 00-2.2 1.3l-2.3-.9-2 3.4 2 1.5a7 7 0 000 2.6l-2 1.5 2 3.4 2.3-.9a7 7 0 002.2 1.3L10 21h4l.4-2.4a7 7 0 002.2-1.3l2.3.9 2-3.4-2-1.5c.1-.4.1-.9.1-1.3z',
  share: 'M12 15V4m0 0L8 8m4-4l4 4M5 13v5a2 2 0 002 2h10a2 2 0 002-2v-5',
  x: 'M6 6l12 12M18 6L6 18',
  list: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
  day: 'M4 9h16M8 3v3M16 3v3M5 5h14a1 1 0 011 1v13a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1z',
  chart: 'M5 20V10M12 20V4M19 20v-7',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  search: 'M11 18a7 7 0 100-14 7 7 0 000 14zM20 20l-4-4',
  wait: 'M7 3h10M7 21h10M8 3c0 5 8 5 8 9s-8 4-8 9M16 3c0 5-8 5-8 9s8 4 8 9',
  cal: 'M4 9h16M8 3v3M16 3v3M5 5h14a1 1 0 011 1v13a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1zM9 14l2 2 4-4',
};
export function icon(name, size = 18) {
  return svg('svg', { viewBox: '0 0 24 24', width: size, height: size, fill: name === 'starfill' ? 'currentColor' : 'none', stroke: 'currentColor', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', class: 'ic' },
    svg('path', { d: ICONS[name === 'starfill' ? 'star' : name] }));
}

/* ── "빠르게 적기" 해석 ──────────────────────────────────────────────
   예) "내일 3시 견적서 보내기 #영업 @김대리 30분"
   → 제목 "견적서 보내기", 날짜 내일, 15:00–15:30, 태그 영업, 담당 김대리
   규칙: #태그  @담당  !1~!6 분류  오늘/내일/모레/월요일/11월 15일/11/15  3시·오후 3시 반·15:30  30분·1시간  "…까지"=마감 */
export function parseQuick(raw, base = today()) {
  const out = { title: '', tags: [], who: '', cat: null, date: null, due: null, start: null, end: null, dur: null };
  let s = ' ' + String(raw).replace(/\s+/g, ' ').trim() + ' ';
  if (!s.trim()) return out;
  s = s.replace(/(\d{1,2}:\d{2})\s?[-~]\s?(\d{1,2}:\d{2})/, '$1 ~ $2').replace(/\s?~\s?/g, ' ~ ');

  s = s.replace(/ #([^\s#@!]+)/g, (m, t) => { if (!out.tags.includes(t)) out.tags.push(t); return ' '; });
  s = s.replace(/ @([^\s#@!]+)/, (m, w) => { out.who = w; return ' '; });
  s = s.replace(/ !([0-6])(?= )/, (m, c) => { out.cat = Number(c); return ' '; });

  let dueOnly = false;
  const setDate = (d, until) => { if (!out.date) { out.date = d; dueOnly = !!until; } return ' '; };
  s = s.replace(/ (오늘|내일|모레|글피)(까지)?(?= )/, (m, w, u) => setDate(addDays(today(), { 오늘: 0, 내일: 1, 모레: 2, 글피: 3 }[w]), u));
  s = s.replace(/ (?:(이번 ?주|다음 ?주) ?)?([월화수목금토일])요일(까지|에)?(?= )/, (m, wk, d, u) => {
    const target = WD.indexOf(d), t = today();
    let date;
    if (wk) date = addDays(mondayOf(t), (wk.startsWith('다음') ? 7 : 0) + ((target + 6) % 7));
    else date = addDays(t, (target - dow(t) + 7) % 7);
    return setDate(date, u === '까지');
  });
  const md = (mo, da, u) => {
    mo = Number(mo); da = Number(da);
    if (mo < 1 || mo > 12 || da < 1 || da > 31) return null;
    const t = toDate(today());
    let date = `${t.getFullYear()}-${p2(mo)}-${p2(da)}`;
    if (diffDays(date, today()) < -180) date = `${t.getFullYear() + 1}-${p2(mo)}-${p2(da)}`;
    return setDate(date, u === '까지');
  };
  s = s.replace(/ (\d{1,2})월 ?(\d{1,2})일(까지|에)?(?= )/, (m, a, b, u) => md(a, b, u) ?? m);
  s = s.replace(/ (\d{1,2})\/(\d{1,2})(까지)?(?= )/, (m, a, b, u) => md(a, b, u) ?? m);

  const times = [];
  const pushTime = (hh, mm, ap) => {
    hh = Number(hh); mm = Number(mm || 0);
    if (hh > 24 || mm > 59) return false;
    if (/오후|저녁|밤/.test(ap || '')) { if (hh < 12) hh += 12; }
    else if (/오전|아침|새벽/.test(ap || '')) { if (hh === 12) hh = 0; }
    else if (ap !== 'x' && hh >= 1 && hh <= 6) hh += 12;          // "3시" → 오후 3시 (업무 시간 기준)
    times.push(Math.min(hh * 60 + mm, 1439));
    return true;
  };
  s = s.replace(/ (\d{1,2}):(\d{2})(?= )/g, (m, a, b) => (times.length < 2 && pushTime(a, b, 'x')) ? ' ' : m);
  s = s.replace(/ (?:(오전|오후|아침|저녁|밤|새벽) ?)?(\d{1,2})시 ?(반|(\d{1,2})분)?(에|부터|까지)?(?= )/g,
    (m, ap, hh, half, mm) => (times.length < 2 && pushTime(hh, half === '반' ? 30 : mm, ap)) ? ' ' : m);
  s = s.replace(/ ~ /g, ' ');

  s = s.replace(/ (\d{1,2})시간(?: ?(\d{1,2})분)?(?: ?동안)?(?= )/, (m, a, b) => { out.dur = Number(a) * 60 + Number(b || 0); return ' '; });
  if (out.dur == null) s = s.replace(/ (\d{1,3})분(?: ?동안)?(?= )/, (m, a) => { out.dur = Number(a); return ' '; });

  if (times.length) {
    out.start = toHm(times[0]);
    if (times[1] != null) { let e = times[1]; if (e <= times[0] && e + 720 <= 1439) e += 720; if (e > times[0]) out.end = toHm(e); }
  }
  if (out.date && (dueOnly || !out.start)) { out.due = out.date; out.date = null; }
  if (out.start && !out.date) out.date = base;
  out.title = s.replace(/\s+/g, ' ').trim() || String(raw).trim();
  return out;
}

export function download(name, text, type = 'text/plain') {
  const a = h('a', { href: URL.createObjectURL(new Blob([text], { type: type + ';charset=utf-8' })), download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
export const csvCell = v => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
