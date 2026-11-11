// 매일 업무 플래너 — 시작점: 화면 틀, 할 일 목록, 하루 타임라인
import * as db from './db.js';
import * as M from './model.js';
import * as C from './cloud.js';
import { h, icon, svg, today, ymd, addDays, toMin, toHm, nowMin, fmtMD, fmtShort, fmtFull, relDay, WD, dow, dueInfo, durText, clamp, debounce, diffDays } from './util.js';
import { ui, $, toast, isPhone, confetti } from './ui.js';
import { openQuick, openTask, openBlock, openTopPicker, openCloseDay, openShare, openSettings, placePreset, shareName } from './sheets.js';
import { renderReview } from './review.js';

const lsGet = k => { try { return localStorage.getItem(k); } catch { return null; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch { /* 무시 */ } };

// ═══ 상단·탭 ═════════════════════════════════════════════════════════
function renderShell() {
  $('#main').dataset.tab = ui.tab;
  document.querySelectorAll('.views button').forEach(b => b.classList.toggle('on', (b.dataset.go === 'review') === (ui.tab === 'review')));
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === ui.tab));
  const s = db.status.state, btn = $('#syncBtn');
  btn.dataset.s = s;
  btn.querySelector('span').textContent = { local: '이 기기에만 저장', idle: '저장됨', syncing: '맞추는 중', error: '연결 안 됨', offline: '오프라인' }[s];
  const open = M.tasks().filter(M.isOpen).length;
  const tabs = document.querySelectorAll('.tabs button');
  tabs[0].querySelector('b').textContent = open || '';
  tabs[1].querySelector('span:nth-child(2)').textContent = ui.date === today() ? '오늘' : fmtShort(ui.date);
  tabs[1].querySelector('b').textContent = M.blocksOn(ui.date).filter(b => !b.done).length || '';
}
function setTab(tab) {
  ui.tab = tab; lsSet('planner:tab', tab);
  render();
  if (isPhone()) scrollTo(0, 0);
}

// ═══ 할 일 ═══════════════════════════════════════════════════════════
function checkBtn(on, c, onToggle, label = '완료') {
  const b = h('button', { class: 'check' + (on ? ' on' : ''), type: 'button', 'aria-label': label, 'aria-pressed': on ? 'true' : 'false', 'data-c': c ?? 0,
    onclick: e => { e.stopPropagation(); if (!on) { b.classList.add('pop'); setTimeout(onToggle, 170); } else onToggle(); } }, icon('check'));
  return b;
}
function completeTask(t) {
  const before = M.stats(), top = M.topTasks(today());
  M.setTaskDone(t, true);
  const isTop = top.some(x => x.id === t.id);
  if (isTop && top.every(x => x.id === t.id || x.st === 'done') && top.length >= 3) { confetti(); toast('오늘의 핵심 3가지를 모두 끝냈어요. +30점'); }
  else {
    const acts = [{ label: '되돌리기', fn: () => M.setTaskDone(db.get(t.id) || t, false) }];
    if (t.who || t.cat === 5) acts.unshift({ label: '답을 기다리는 중', fn: () => M.setTaskWait(db.get(t.id) || t, true) });
    toast(isTop ? '핵심 하나 완료. +30점' : '완료. +10점', { actions: acts });
  }
  const after = M.stats();
  if (after.level > before.level) setTimeout(() => { confetti(); toast(`승진했어요. 이제 ${after.title}입니다.`, { ms: 5000 }); }, 900);
}
function taskRow(t, sorter) {
  const blk = M.nextBlockOf(t.id);
  const inTop = (M.dayOf(ui.date).top || []).includes(t.id);
  const meta = h('div', { class: 't-meta' },
    t.due && t.st !== 'done' ? h('span', { class: 'chip ' + dueInfo(t.due).cls }, dueInfo(t.due).text) : null,
    blk ? h('span', { class: 'chip when' }, `${relDay(blk.date)} ${blk.start}`) : null,
    t.who ? h('span', { class: 'chip' }, '@' + t.who) : null,
    (t.tags || []).map(n => h('span', { class: 'chip tag', style: `--dot:${M.tagColor(n)}` }, n)),
    t.st === 'wait' && t.waitAt ? h('span', { class: 'chip' }, `${Math.max(0, diffDays(today(), ymd(new Date(t.waitAt))))}일째`) : null);
  const done = t.st === 'done';
  return h('li', { class: 'task' + (done ? ' done' : '') + (sorter ? ' unsorted' : ''), 'data-c': t.cat, 'data-id': t.id, draggable: !done && !isPhone() ? 'true' : null,
    ondragstart: e => { e.dataTransfer.setData('text/plain', 'task:' + t.id); e.dataTransfer.effectAllowed = 'copy'; dragTask = t; },
    ondragend: () => { dragTask = null; } },
    checkBtn(done, t.cat, () => done ? M.setTaskDone(t, false) : completeTask(t)),
    h('div', { class: 't-body', onclick: () => openTask(t) }, h('div', { class: 't-title' }, t.title), meta),
    sorter || (done ? null : h('div', { class: 't-acts' },
      h('button', { class: 'icon-btn' + (inTop ? ' on' : ''), type: 'button', title: inTop ? '핵심에서 빼기' : `${relDay(ui.date)}의 핵심으로`, 'aria-label': '핵심 지정', onclick: () => { if (!M.toggleTop(ui.date, t.id)) toast('핵심은 3개까지예요. 하나를 빼고 넣어 주세요.'); } }, icon(inTop ? 'starfill' : 'star', 17)),
      h('button', { class: 'icon-btn', type: 'button', title: `${relDay(ui.date)}에 시간 붙이기`, 'aria-label': '시간 붙이기', onclick: () => openBlock(null, placePreset(t)) }, icon('clock', 17)))));
}
function addRow(catId, placeholder) {
  const input = h('input', { placeholder, 'data-add': catId, enterkeyhint: 'done', autocomplete: 'off', 'aria-label': placeholder });
  input.addEventListener('keydown', e => {
    if (e.key !== 'Enter' || e.isComposing || !input.value.trim()) return;
    e.preventDefault();
    const r = M.quickAdd(input.value, { cat: catId, tags: ui.tag ? [ui.tag] : [], date: ui.date });
    input.value = '';
    if (r?.block) toast(`${relDay(r.block.date)} ${r.block.start}에 시간도 붙였어요.`);
  });
  return h('div', { class: 'add' }, input);
}
function renderTasks() {
  const el = $('#tasks');
  const drafts = {}; el.querySelectorAll('input[data-add]').forEach(i => { drafts[i.dataset.add] = i.value; });
  const focused = document.activeElement?.dataset?.add, scroll = el.scrollTop;
  const all = M.tasks();
  const match = t => !ui.tag || (t.tags || []).includes(ui.tag);
  const byDue = (a, b) => (a.due || '9999').localeCompare(b.due || '9999') || (a.at || 0) - (b.at || 0);
  const open = all.filter(t => M.isOpen(t) && match(t));
  const inbox = open.filter(t => !t.cat).sort(byDue);
  const waiting = all.filter(t => t.st === 'wait' && match(t)).sort((a, b) => (a.waitAt || 0) - (b.waitAt || 0));
  const done = all.filter(t => t.st === 'done' && match(t)).sort((a, b) => (b.doneAt || 0) - (a.doneAt || 0));
  const tagList = M.tags();

  const kids = [
    h('div', { class: 'pane-head' }, h('h2', {}, '할 일'), h('span', { class: 'count' }, `${open.length}개 남음`)),
    tagList.length ? h('div', { class: 'chips tagbar' },
      h('button', { type: 'button', class: 'chip' + (!ui.tag ? ' on' : ''), onclick: () => { ui.tag = null; render(); } }, '전체'),
      tagList.map(t => h('button', { type: 'button', class: 'chip tag' + (ui.tag === t.name ? ' on' : ''), style: `--dot:${t.color}`, onclick: () => { ui.tag = ui.tag === t.name ? null : t.name; render(); } }, t.name))) : null,
    !all.length && !lsGet('planner:guide') ? h('div', { class: 'guide' },
      h('b', {}, '하루에 세 번만 열면 됩니다'),
      h('ol', {}, h('li', {}, h('b', {}, '적기'), ' — 떠오르는 일을 전부 적고, 성격에 맞는 칸에 넣습니다.'), h('li', {}, h('b', {}, '고르기'), ' — 오늘의 핵심 3가지를 고르고 시간을 붙입니다.'), h('li', {}, h('b', {}, '닫기'), ' — 저녁에 도장을 찍어 하루를 마감합니다.')),
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': '안내 닫기', onclick: () => { lsSet('planner:guide', '1'); render(); } }, icon('x', 16))) : null,
    inbox.length ? h('div', { class: 'sec', 'data-c': 0 },
      h('div', { class: 'sec-head' }, h('span', { class: 'sec-no' }, '·'), h('span', { class: 'sec-name' }, '분류 전'), h('span', { class: 'sec-count' }, inbox.length), h('span', { class: 'sec-hint' }, '번호를 눌러 성격 정하기')),
      h('ul', {}, inbox.map(t => taskRow(t, h('div', { class: 'sorter' }, M.cats().map(c => h('button', { type: 'button', 'data-c': c.id, title: c.name, 'aria-label': c.name, onclick: () => M.updateTask(t.id, { cat: c.id }) }, String(c.id)))))))) : null,
    ...M.cats().map(c => {
      const list = open.filter(t => t.cat === c.id).sort(byDue);
      return h('div', { class: 'sec', 'data-c': c.id },
        h('div', { class: 'sec-head' }, h('span', { class: 'sec-no' }, String(c.id)), h('span', { class: 'sec-name' }, c.name), h('span', { class: 'sec-count' }, list.length || ''), h('span', { class: 'sec-hint' }, c.hint)),
        list.length ? h('ul', {}, list.map(t => taskRow(t))) : null,
        addRow(c.id, '할 일 추가'));
    }),
    waiting.length ? h('div', { class: 'sec', 'data-c': 5 },
      h('button', { class: 'sec-toggle', type: 'button', 'aria-expanded': String(ui.showWait), onclick: () => { ui.showWait = !ui.showWait; render(); } }, icon('wait', 16), `기다리는 중 ${waiting.length}`, h('span', { class: 'caret' }, '›')),
      ui.showWait ? h('ul', {}, waiting.map(t => taskRow(t))) : null) : null,
    done.length ? h('div', { class: 'sec' },
      h('button', { class: 'sec-toggle', type: 'button', 'aria-expanded': String(ui.showDone), onclick: () => { ui.showDone = !ui.showDone; render(); } }, icon('check', 16), `끝낸 일 ${done.length}`, h('span', { class: 'caret' }, '›')),
      ui.showDone ? h('ul', {}, done.slice(0, 50).map(t => taskRow(t))) : null) : null,
  ];
  el.replaceChildren(...kids.filter(Boolean));
  el.querySelectorAll('input[data-add]').forEach(i => { if (drafts[i.dataset.add]) i.value = drafts[i.dataset.add]; });
  if (focused != null) el.querySelector(`input[data-add="${focused}"]`)?.focus();
  el.scrollTop = scroll;
}

// ═══ 하루 ════════════════════════════════════════════════════════════
let dragTask = null;
const ppm = () => (parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hour')) || 66) / 60;

function ring(p) {
  const r = 22, c = 2 * Math.PI * r;
  return h('div', { class: 'ring', title: `블록 ${p.done}/${p.total} 완료` },
    svg('svg', { width: 52, height: 52, viewBox: '0 0 52 52' }, svg('circle', { class: 'bg', cx: 26, cy: 26, r }), svg('circle', { class: 'fg', cx: 26, cy: 26, r, 'stroke-dasharray': c, 'stroke-dashoffset': c * (1 - p.pct / 100) })),
    h('span', { class: 'num' }, p.total ? `${p.done}/${p.total}` : '–'));
}

function layout(items) {       // 겹치는 블록을 옆으로 나란히
  items.sort((a, b) => a.s - b.s || b.e - a.e);
  let group = [], end = -1;
  const flush = () => { const n = Math.max(...group.map(x => x.col)) + 1; group.forEach(x => { x.cols = n; }); group = []; };
  for (const it of items) {
    if (group.length && it.s >= end) { flush(); end = -1; }
    const used = new Set(group.filter(x => x.ve > it.s).map(x => x.col));
    let c = 0; while (used.has(c)) c++;
    it.col = c; group.push(it); end = Math.max(end, it.ve);
  }
  if (group.length) flush();
  return items;
}

function renderTimeline(date, gev) {
  const P = ppm(), isToday = date === today(), nm = nowMin();
  const blocks = M.blocksOn(date);
  const items = layout([
    ...blocks.map(b => ({ b, s: toMin(b.start), e: toMin(b.end) })),
    ...gev.map(g => ({ g, s: toMin(g.start), e: toMin(g.end) })),
  ].map(x => ({ ...x, ve: Math.max(x.e, x.s + 20) })));
  let h0 = isToday ? clamp(Math.floor(nm / 60) - 1, 6, 9) : 8, h1 = 19;
  if (items.length) { h0 = Math.min(h0, Math.floor(Math.min(...items.map(x => x.s)) / 60)); h1 = Math.max(h1, Math.ceil(Math.max(...items.map(x => x.e)) / 60)); }
  if (isToday) h1 = Math.max(h1, Math.min(24, Math.floor(nm / 60) + 2));
  const t0 = h0 * 60, t1 = h1 * 60;
  const top = (date ? M.dayOf(date).top : []) || [];

  const area = h('div', { class: 'tl-area' });
  const tl = h('div', { class: 'tl', style: `height:${(t1 - t0) * P + 1}px` },
    h('div', { class: 'tl-ruler' }, Array.from({ length: h1 - h0 + 1 }, (_, i) => h('span', { style: `top:${i * 60 * P}px` }, String(h0 + i)))), area);

  for (const it of items) {
    const height = Math.max((it.e - it.s) * P - 2, 22);
    const style = `top:${(it.s - t0) * P + 1}px;height:${height}px;left:calc(${it.col / it.cols * 100}% + 3px);width:calc(${100 / it.cols}% - 6px)`;
    if (it.g) {
      area.append(h('a', { class: 'blk gev' + (height < 40 ? ' short' : ''), style, href: it.g.link, target: '_blank', rel: 'noopener', title: 'Google 캘린더에서 열기' },
        h('span', { class: 'g' }, 'G'), h('div', { class: 'blk-main' }, h('div', { class: 'blk-title' }, it.g.title), h('div', { class: 'blk-time' }, `${it.g.start}–${it.g.end}`))));
      continue;
    }
    const b = it.b;
    const time = h('div', { class: 'blk-time' }, `${b.start}–${b.end}`, height >= 40 && b.tags?.length ? '  ' + b.tags.map(t => '#' + t).join(' ') : '');
    const el = h('div', { class: `blk${b.done ? ' done' : ''}${height < 40 ? ' short' : ''}${b.routine ? ' routine' : ''}`, 'data-c': b.routine ? 0 : (b.cat || 0), 'data-id': b.id, style, tabindex: 0, role: 'button',
      onkeydown: e => { if (e.key === 'Enter') openBlock(b); } },
      checkBtn(b.done, b.routine ? 0 : (b.cat || 0), () => {
        if (b.done) return M.setBlockDone(b, false);
        const t = b.taskId && db.get(b.taskId);
        if (t && t.st !== 'done') { db.patch(b.id, { done: true, doneAt: Date.now() }); completeTask(t); } else M.setBlockDone(b, true);
      }),
      h('div', { class: 'blk-main' }, h('div', { class: 'blk-title' }, b.taskId && top.includes(b.taskId) ? icon('starfill', 13) : null, b.title), time),
      h('div', { class: 'blk-grip', 'data-grip': '1' }));
    bindDrag(el, b, time, t0, t1);
    area.append(el);
  }
  if (isToday && nm >= t0 && nm <= t1) area.append(h('div', { class: 'now', style: `top:${(nm - t0) * P}px` }));

  // 빈 곳을 누르면 그 시간에 블록 추가
  area.addEventListener('click', e => {
    if (e.target !== area || suppressClick) return;
    const m = clamp(Math.floor((t0 + e.offsetY / P) / 30) * 30, 0, 1410);
    openBlock(null, { start: toHm(m), end: toHm(Math.min(m + 60, 1439)), date });
  });
  // 할 일을 끌어다 놓기 (PC)
  const marker = h('div', { class: 'tl-drop' });
  const at = e => clamp(Math.round((t0 + (e.clientY - area.getBoundingClientRect().top) / P) / 15) * 15, 0, 1425);
  area.addEventListener('dragover', e => { if (!dragTask) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; const m = at(e); marker.style.top = (m - t0) * P + 'px'; marker.dataset.t = toHm(m); if (!marker.isConnected) area.append(marker); area.classList.add('drop'); });
  area.addEventListener('dragleave', () => { marker.remove(); area.classList.remove('drop'); });
  area.addEventListener('drop', e => {
    e.preventDefault(); marker.remove(); area.classList.remove('drop');
    const t = dragTask; dragTask = null;
    if (!t) return;
    const m = at(e), dur = M.cat(t.cat).dur;
    M.placeTask(t, date, toHm(m), toHm(Math.min(m + dur, 1439)));
  });
  return h('div', { class: 'tl-wrap' }, tl);
}

// 블록 끌기: 몸통 = 옮기기, 아래 가장자리 = 길이 조절. 폰에서는 길게 눌러서 끕니다.
let drag = null, suppressClick = false;
function bindDrag(el, b, timeEl, t0, t1) {
  el.addEventListener('click', e => { if (suppressClick || e.target.closest('.check')) return; openBlock(b); });
  el.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.target.closest('.check')) return;
    const mode = e.target.dataset.grip ? 'resize' : 'move';
    const d = drag = { el, b, mode, y: e.clientY, x: e.clientX, s: toMin(b.start), e: toMin(b.end), ns: toMin(b.start), ne: toMin(b.end), active: false, id: e.pointerId, t0, t1, timeEl, touch: e.pointerType !== 'mouse' };
    if (d.touch) d.timer = setTimeout(() => { if (drag === d) { activate(d); navigator.vibrate?.(12); } }, 380);
  });
}
function activate(d) { d.active = true; d.el.classList.add('dragging'); try { d.el.setPointerCapture(d.id); } catch { /* 무시 */ } }
function endDrag(commit) {
  const d = drag; drag = null;
  if (!d) return;
  clearTimeout(d.timer);
  if (!d.active) return;
  d.el.classList.remove('dragging');
  suppressClick = true; setTimeout(() => { suppressClick = false; }, 60);
  if (commit && (d.ns !== d.s || d.ne !== d.e)) db.patch(d.b.id, { start: toHm(d.ns), end: toHm(d.ne) });
  else renderDay();
}
addEventListener('pointermove', e => {
  const d = drag;
  if (!d || e.pointerId !== d.id) return;
  const dy = e.clientY - d.y;
  if (!d.active) {
    if (d.touch) { if (Math.abs(dy) > 8 || Math.abs(e.clientX - d.x) > 8) { clearTimeout(d.timer); drag = null; } return; }
    if (Math.abs(dy) < 4) return;
    activate(d);
  }
  const P = ppm(), dm = Math.round(dy / P / 15) * 15, len = d.e - d.s;
  if (d.mode === 'move') { d.ns = clamp(d.s + dm, d.t0, Math.min(d.t1, 1439) - len); d.ne = d.ns + len; }
  else d.ne = clamp(d.e + dm, d.s + 15, Math.min(d.t1, 1439));
  d.el.style.top = (d.ns - d.t0) * P + 1 + 'px';
  d.el.style.height = Math.max((d.ne - d.ns) * P - 2, 22) + 'px';
  d.timeEl.textContent = `${toHm(d.ns)}–${toHm(d.ne)}`;
});
addEventListener('pointerup', () => endDrag(true));
addEventListener('pointercancel', () => endDrag(false));
addEventListener('touchmove', e => { if (drag?.active) e.preventDefault(); }, { passive: false });
addEventListener('contextmenu', e => { if (drag) e.preventDefault(); });

function renderDay() {
  const el = $('#day'), date = ui.date, isToday = date === today(), scroll = el.scrollTop;
  const d = M.dayOf(date), p = M.dayProgress(date), st = M.stats();
  const gAll = C.gEventsCached(date), gev = gAll.filter(e => !e.allDay), allDay = gAll.filter(e => e.allDay);
  const top = M.topTasks(date);

  const head = h('div', { class: 'day-head' },
    h('div', { class: 'date-nav' },
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': '이전 날', onclick: () => ui.go(addDays(date, -1)) }, icon('left')),
      h('label', { class: 'date-pick' },
        h('span', { class: 'd-big' }, fmtMD(date)),
        h('span', { class: 'd-sub' }, `${WD[dow(date)]}요일 · `, isToday ? h('b', {}, '오늘') : relDay(date), p.planned ? ` · 계획 ${durText(p.planned)}` : ''),
        h('input', { type: 'date', value: date, 'aria-label': '날짜 선택', onchange: e => e.target.value && ui.go(e.target.value) })),
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': '다음 날', onclick: () => ui.go(addDays(date, 1)) }, icon('right')),
      isToday ? null : h('button', { class: 'btn sm', type: 'button', onclick: () => ui.go(today()) }, '오늘')),
    h('div', { class: 'day-side' },
      st.streak > 1 ? h('div', { class: 'streak' }, h('b', {}, `${st.streak}일`), '연속') : null,
      d.closedAt ? h('button', { class: 'stamp' + (ui.justClosed ? ' thunk' : ''), type: 'button', title: '마감한 날 — 눌러서 회고 보기', onclick: () => openCloseDay(date) }, '마감') : ring(p)));
  ui.justClosed = false;

  const slots = [0, 1, 2].map(i => {
    const t = top[i];
    if (!t) return h('button', { class: 'slot empty', type: 'button', onclick: () => openTopPicker(date) }, h('span', { class: 'no' }, String(i + 1)), i === top.length ? '가장 중요한 일 고르기' : '');
    const done = t.st === 'done';
    return h('div', { class: 'slot filled' + (done ? ' done' : ''), 'data-c': t.cat },
      h('span', { class: 'no' }, String(i + 1)),
      checkBtn(done, t.cat, () => done ? M.setTaskDone(t, false) : completeTask(t)),
      h('span', { class: 's-title', onclick: () => openTask(t) }, t.title));
  });
  const top3 = h('div', { class: 'top3' },
    h('div', { class: 'top3-title' }, '핵심 3', h('span', {}, top.length ? `${p.topDone}/${top.length} 완료` : '이것만 끝내면 성공인 일'),
      top.length ? h('button', { class: 'link', type: 'button', style: 'margin-left:auto;font-size:13px', onclick: () => openTopPicker(date) }, '바꾸기') : null),
    slots);

  const dueSoon = isToday ? M.tasks().filter(t => M.isOpen(t) && t.due && t.due <= date && !M.blocksOn(date).some(b => b.taskId === t.id)).slice(0, 6) : [];
  const strips = [
    dueSoon.length ? h('div', { class: 'strip' }, h('b', {}, '마감 임박'), dueSoon.map(t => h('button', { type: 'button', class: 'chip ' + dueInfo(t.due).cls, title: '눌러서 시간 붙이기', onclick: () => openBlock(null, placePreset(t)) }, t.title))) : null,
    allDay.length ? h('div', { class: 'strip' }, h('b', {}, '종일'), allDay.map(e => h('a', { class: 'chip', href: e.link, target: '_blank', rel: 'noopener' }, e.title))) : null,
    C.cloud.user && C.gcalWanted() && ['expired', 'api_off'].includes(C.cloud.gstate) ? h('div', { class: 'banner' }, h('span', { class: 'grow' }, C.cloud.gstate === 'api_off' ? 'Google 캘린더 설정이 필요해요.' : 'Google 캘린더 연결이 끊겼어요.'), h('button', { class: 'btn sm', type: 'button', onclick: () => openSettings('gcal') }, '확인')) : null,
  ];

  const acts = h('div', { class: 'day-acts' },
    h('button', { class: 'btn', type: 'button', onclick: () => { const [s, e] = M.freeSlot(date, 60, gev); openBlock(null, { start: s, end: e, date }); } }, icon('plus', 16), '시간 블록'),
    h('button', { class: 'btn', type: 'button', onclick: () => openShare(date) }, icon('share', 16), '공유'),
    h('span', { class: 'grow' }),
    d.closedAt ? null : h('button', { class: 'btn seal', type: 'button', onclick: () => openCloseDay(date) }, '하루 마감'));

  el.replaceChildren(...[head, top3, ...strips, d.note && d.closedAt ? h('p', { class: 'note-view' }, d.note) : null, acts, renderTimeline(date, gev)].filter(Boolean));
  el.scrollTop = scroll;
}

// ═══ 전체 그리기 ══════════════════════════════════════════════════════
let queued = false;
function render() {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => {
    queued = false;
    if (drag?.active) return;
    renderShell();
    if (ui.tab === 'review') renderReview($('#review'));
    else { renderTasks(); renderDay(); }
  });
}
ui.render = render;
ui.go = date => {
  ui.date = date;
  M.seedDay(date);
  if (ui.tab === 'review' || (isPhone() && ui.tab !== 'day')) ui.tab = 'day';
  render();
  loadCalendar();
};
async function loadCalendar() {
  const date = ui.date;
  if (!C.cloud.user) return;
  await C.gEvents(date);
  if (date === ui.date) render();
}

// 공유 중인 날짜의 일정이 바뀌면 링크 내용도 따라 고침
const sharedHash = new Map();
const syncShares = debounce(async () => {
  if (!C.cloud.user) return;
  for (const sh of db.list('share')) {
    const payload = M.sharePayload(sh.date, shareName());
    const sig = JSON.stringify({ ...payload, at: 0 });
    if (!sharedHash.has(sh.id)) { sharedHash.set(sh.id, sig); continue; }
    if (sharedHash.get(sh.id) === sig) continue;
    try { await C.shareSave(sh.sid, payload); sharedHash.set(sh.id, sig); } catch (e) { console.warn(e); }
  }
}, 2500);

// ═══ 공유받은 화면 (읽기 전용) ═════════════════════════════════════════
async function renderViewer(id) {
  const box = $('#viewer'); box.hidden = false;
  box.replaceChildren(h('div', { class: 'viewer' }, h('p', { class: 'empty' }, '일정을 불러오는 중…')));
  let p = null;
  try { p = await C.shareGet(id); } catch { /* 아래에서 안내 */ }
  if (!p) { box.replaceChildren(h('div', { class: 'viewer' }, h('div', { class: 'v-card' }, h('h1', {}, '볼 수 없는 일정이에요'), h('p', { class: 'v-sub' }, '공유가 중지됐거나 주소가 잘못됐어요. 보낸 분께 새 링크를 부탁해 보세요.')))); return; }
  document.title = `${fmtMD(p.date)} 일정`;
  box.replaceChildren(h('div', { class: 'viewer' },
    h('div', { class: 'v-card' },
      h('h1', {}, fmtFull(p.date)),
      h('p', { class: 'v-sub' }, `${p.name ? p.name + '님의 일정 · ' : ''}${new Date(p.at).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })} 기준`),
      p.top?.length ? h('div', { class: 'v-top' }, h('p', { class: 'v-label' }, '오늘의 핵심'), p.top.map((t, i) => h('div', {}, h('span', { class: 'no' }, String(i + 1)), h('span', { class: t.done ? 'done' : '' }, t.t)))) : null,
      p.blocks?.length ? h('ul', { class: 'v-list' }, p.blocks.map(b => h('li', { 'data-c': b.c || 0 }, h('time', {}, `${b.s}–${b.e}`), h('span', { class: b.done ? 'done' : '' }, b.t))))
        : h('p', { class: 'empty' }, '이 날은 잡힌 일정이 없어요.')),
    h('p', { class: 'v-foot' }, '보기 전용 화면입니다 · 매일 업무 플래너')));
}

// ═══ 시작 ════════════════════════════════════════════════════════════
async function boot() {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
  const q = new URLSearchParams(location.search);
  if (q.get('s')) return renderViewer(q.get('s'));

  $('#settingsBtn').append(icon('gear', 19));
  $('#fab').append(icon('plus', 24));
  const tabIcons = ['list', 'day', 'chart'];
  document.querySelectorAll('.tabs .tab-ic').forEach((n, i) => n.append(icon(tabIcons[i], 21)));
  $('#quickBtn').addEventListener('click', () => openQuick());
  $('#fab').addEventListener('click', () => openQuick());
  $('#settingsBtn').addEventListener('click', () => openSettings());
  $('#syncBtn').addEventListener('click', () => { if (db.hasRemote()) db.sync().then(ok => toast(ok ? '서버와 맞췄어요.' : '지금은 맞추지 못했어요.')); else openSettings('account'); });
  document.querySelectorAll('.views button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.go === 'review' ? 'review' : 'day')));
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));
  addEventListener('keydown', e => {
    if (e.target.closest('input, textarea, select, dialog') || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'n' || e.key === 'N' || e.key === '/' || e.key === 'ㅜ') { e.preventDefault(); openQuick(); }
    else if (e.key === 't' || e.key === 'T' || e.key === 'ㅅ') ui.go(today());
    else if (e.key === 'ArrowLeft' && ui.tab !== 'review') ui.go(addDays(ui.date, -1));
    else if (e.key === 'ArrowRight' && ui.tab !== 'review') ui.go(addDays(ui.date, 1));
  });

  await db.open();
  const saved = lsGet('planner:tab');
  ui.tab = saved === 'review' ? 'day' : (saved || 'day');
  if (!isPhone() && ui.tab === 'tasks') ui.tab = 'day';
  M.seedDay(ui.date);
  $('#app').hidden = false;
  render();
  db.on(() => { render(); syncShares(); if (C.cloud.user && C.gcalWanted()) C.gPushSoon(); });
  C.onCloud(() => { render(); if (C.cloud.user) loadCalendar(); });
  await C.init();
  if (q.has('today')) history.replaceState(null, '', location.pathname);

  // 다른 기기에서 바꾼 내용 받기, 자정 넘기면 오늘로
  let lastDay = today(), lastSync = Date.now();
  const wake = () => {
    if (document.visibilityState !== 'visible') return;
    if (lastDay !== today()) { if (ui.date === lastDay) ui.go(today()); lastDay = today(); }
    if (Date.now() - lastSync > 20e3) { lastSync = Date.now(); db.sync(); loadCalendar(); }
    render();
  };
  document.addEventListener('visibilitychange', wake);
  setInterval(wake, 60e3);
  addEventListener('online', () => db.sync());
  addEventListener('resize', debounce(render, 150));
}
boot();
