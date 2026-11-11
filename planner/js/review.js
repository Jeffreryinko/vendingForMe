// 돌아보기: 레벨·연속 기록·잔디·주간 시간 배분·회고
import * as db from './db.js';
import * as M from './model.js';
import { h, icon, today, addDays, mondayOf, fmtShort, fmtMD, WD, dow, hoursText, diffDays } from './util.js';
import { ui, isPhone } from './ui.js';

export function renderReview(el) {
  const st = M.stats(), td = today();
  const span = st.next - st.floor, into = st.xp - st.floor;

  const level = h('div', { class: 'level' },
    h('div', {}, h('div', { class: 'lv-title' }, st.title), h('div', { class: 'lv-sub' }, `레벨 ${st.level} · 다음 레벨까지 ${st.next - st.xp}점`)),
    h('div', { class: 'facts' },
      h('div', { class: 'fact' }, h('b', {}, `${st.streak}일`), h('span', {}, '연속 기록')),
      h('div', { class: 'fact' }, h('b', {}, String(st.doneTasks)), h('span', {}, '끝낸 일')),
      h('div', { class: 'fact' }, h('b', {}, String(st.closed.size)), h('span', {}, '마감 도장'))),
    h('div', { class: 'xpbar' }, h('i', { style: `width:${Math.round(into / span * 100)}%` })),
    h('div', { class: 'xp-cap' }, h('span', {}, `${st.xp}점`), h('span', {}, '할 일 완료 10 · 핵심 달성 +20 · 하루 마감 15')));

  // 잔디: 한 칸 = 하루, 진할수록 많이 끝낸 날, 빨간 점 = 마감 도장
  const weeks = Math.max(12, Math.min(52, Math.floor((Math.min(el.clientWidth || innerWidth, 928) - 50) / 16)));   // 칸 너비에 맞는 만큼
  const start = addDays(mondayOf(td), -(weeks - 1) * 7);
  const cells = [];
  for (let i = 0; i < weeks * 7; i++) {
    const d = addDays(start, i), n = st.activity.get(d) || 0;
    const l = n === 0 ? 0 : n <= 2 ? 1 : n <= 4 ? 2 : n <= 7 ? 3 : 4;
    cells.push(h('i', { 'data-l': l, class: (d > td ? 'future ' : '') + (st.closed.has(d) ? 'closed ' : '') + (d === td ? 'today' : ''), title: `${fmtMD(d)}(${WD[dow(d)]}) · ${n}개 완료${st.closed.has(d) ? ' · 마감' : ''}` }));
  }
  const heat = h('section', { class: 'r-sec' },
    h('h3', {}, '쌓인 날들'),
    h('p', { class: 'sub' }, `최근 ${weeks}주. 한 칸이 하루이고, 많이 끝낸 날일수록 진해요.`),
    h('div', { class: 'heat' }, cells),
    h('div', { class: 'heat-legend' }, '적음', [0, 1, 2, 3, 4].map(l => h('i', { 'data-l': l, class: 'lg', style: l ? `background:color-mix(in srgb, var(--heat) ${[0, 24, 48, 74, 100][l]}%, var(--surface))` : '' })), '많음', h('i', { class: 'dot' }), '동그란 칸은 마감 도장을 찍은 날'));

  // 주간
  const w = M.weekStats(ui.week);
  const thisWeek = mondayOf(td);
  const nav = h('div', { class: 'week-nav' },
    h('button', { class: 'icon-btn', type: 'button', 'aria-label': '지난주', onclick: () => { ui.week = addDays(ui.week, -7); ui.render(); } }, icon('left', 16)),
    h('b', {}, ui.week === thisWeek ? '이번 주' : diffDays(thisWeek, ui.week) === 7 ? '지난주' : `${fmtShort(w.monday)} – ${fmtShort(w.end)}`),
    h('button', { class: 'icon-btn', type: 'button', 'aria-label': '다음 주', disabled: ui.week >= thisWeek, onclick: () => { ui.week = addDays(ui.week, 7); ui.render(); } }, icon('right', 16)));
  const catRows = M.cats().map(c => ({ c, m: w.byCat[c.id] || 0 }));
  const maxCat = Math.max(1, ...catRows.map(r => r.m));
  const urgent = w.byCat[1] || 0, deep = (w.byCat[6] || 0) + (w.byCat[3] || 0);
  let insight = '';
  if (w.doneMin === 0) insight = '아직 이 주에 완료한 시간 블록이 없어요. 블록을 체크하면 어디에 시간을 썼는지 여기에 쌓입니다.';
  else if (urgent > deep) insight = `급한 불을 끄는 데 ${hoursText(urgent)}, 중요한 일·깊이 고민할 일에 ${hoursText(deep)}을 썼어요. 다음 주에는 중요한 일의 블록을 오전에 먼저 잡아 두면 균형이 맞습니다.`;
  else if (deep > 0) insight = `중요한 일·깊이 고민할 일에 ${hoursText(deep)}, 급한 일에 ${hoursText(urgent)}을 썼어요. 급한 일에 끌려다니지 않은 한 주예요.`;
  else insight = `완료한 시간은 ${hoursText(w.doneMin)}인데 '중요하게 해야 할 일'에 쓴 시간이 아직 없어요. 하루 한 블록만 잡아 보세요.`;
  const tagRows = Object.entries(w.byTag).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxTag = Math.max(1, ...tagRows.map(r => r[1]));

  const week = h('section', { class: 'r-sec' },
    h('div', { class: 'pane-head', style: 'margin-bottom:12px' }, h('h3', { style: 'margin:0' }, '한 주 돌아보기'), h('div', { class: 'right' }, nav)),
    h('div', { class: 'kpis' },
      h('div', {}, h('b', {}, String(w.tasksDone)), h('span', {}, '끝낸 일')),
      h('div', {}, h('b', {}, hoursText(w.doneMin)), h('span', {}, '완료한 시간')),
      h('div', {}, h('b', {}, w.blocks ? Math.round(w.blocksDone / w.blocks * 100) + '%' : '–'), h('span', {}, `계획 달성 ${w.blocksDone}/${w.blocks}`)),
      h('div', {}, h('b', {}, w.topSet ? `${w.topHit}/${w.topSet}` : '–'), h('span', {}, '핵심 달성'))),
    h('div', { class: 'bars' }, catRows.map(r => h('div', { class: 'bar-row', 'data-c': r.c.id },
      h('span', { class: 'lbl' }, r.c.name), h('span', { class: 'track' }, r.m ? h('i', { style: `width:${r.m / maxCat * 100}%` }) : null), h('span', { class: 'val' }, r.m ? hoursText(r.m) : '–')))),
    h('p', { class: 'insight' }, insight),
    tagRows.length ? h('div', { style: 'margin-top:20px' }, h('p', { class: 'sub', style: 'margin-bottom:10px' }, '태그별 시간'),
      h('div', { class: 'bars' }, tagRows.map(([name, m]) => h('div', { class: 'bar-row', style: `--dot:${M.tagColor(name)}` },
        h('span', { class: 'lbl' }, '#' + name), h('span', { class: 'track' }, h('i', { style: `width:${m / maxTag * 100}%` })), h('span', { class: 'val' }, hoursText(m)))))) : null);

  const notes = h('section', { class: 'r-sec' },
    h('h3', {}, '한 줄 회고'),
    h('p', { class: 'sub' }, '하루를 마감할 때 남긴 말이 여기에 모입니다.'),
    w.notes.length ? h('ul', { class: 'notes' }, w.notes.map(n => h('li', {}, h('time', {}, `${fmtShort(n.date)} (${WD[dow(n.date)]})`), h('span', {}, n.note))))
      : h('p', { class: 'empty' }, '이 주에 남긴 회고가 없어요.'));

  el.replaceChildren(h('div', { class: 'review-wrap' }, level, heat, week, notes));
  const hm = el.querySelector('.heat'); if (hm) hm.scrollLeft = hm.scrollWidth;
}
