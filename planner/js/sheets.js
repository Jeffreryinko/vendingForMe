// 시트(대화창) 모음: 빠르게 적기 · 할 일 · 시간 블록 · 핵심 3 고르기 · 하루 마감 · 공유 · 설정
import * as db from './db.js';
import * as M from './model.js';
import * as C from './cloud.js';
import { h, icon, today, addDays, toMin, toHm, fmtMD, fmtShort, fmtFull, relDay, WD, dow, newId, parseQuick, durText, nextWorkday, download, ymd, dueInfo, mondayOf } from './util.js';
import { ui, toast, sheet, field, catPick, tagPick, confetti, copyText, shareText } from './ui.js';

const foot = (...kids) => h('div', { class: 'sheet-foot' }, kids);
const grow = () => h('span', { class: 'grow' });
const btn = (label, onclick, cls = '') => h('button', { type: 'button', class: 'btn ' + cls, onclick }, label);

// ── 빠르게 적기 ───────────────────────────────────────────────────────
export function openQuick(preset = {}) {
  let catSel = preset.cat ?? null, tagSel = ui.tag ? [ui.tag] : [];
  const input = h('input', { class: 'cmd-input', placeholder: '무엇을 해야 하나요?', enterkeyhint: 'done', autocomplete: 'off' });
  const preview = h('div', { class: 'cmd-preview chips' });
  const log = h('div', { class: 'cmd-log' });
  const draw = () => {
    const p = parseQuick(input.value, ui.date);
    const chips = [];
    if (!input.value.trim()) { preview.replaceChildren(h('span', { class: 'hint' }, '예: 내일 3시 견적서 보내기 #영업 @김대리 30분')); return; }
    const c = p.cat ?? catSel;
    if (c != null) chips.push(h('span', { class: 'chip tag', style: `--dot:var(--c${c})` }, M.cat(c).name));
    [...new Set([...tagSel, ...p.tags])].forEach(t => chips.push(h('span', { class: 'chip tag', style: `--dot:${M.tagColor(t)}` }, t)));
    if (p.who) chips.push(h('span', { class: 'chip' }, '@' + p.who));
    if (p.due) chips.push(h('span', { class: 'chip soon' }, relDay(p.due) + '까지'));
    if (p.start) { const end = p.end || toHm(toMin(p.start) + (p.dur || M.cat(c ?? 0).dur)); chips.push(h('span', { class: 'chip when' }, `${relDay(p.date)} ${p.start}–${end}`)); }
    preview.replaceChildren(...chips);
  };
  const submit = () => {
    if (!input.value.trim()) return;
    const r = M.quickAdd(input.value, { cat: catSel ?? 0, tags: tagSel, date: ui.date });
    if (!r) return;
    log.prepend(h('div', {}, r.task.title + (r.block ? ` — ${relDay(r.block.date)} ${r.block.start}` : '')));
    while (log.children.length > 3) log.lastChild.remove();
    input.value = ''; draw(); input.focus();
  };
  input.addEventListener('input', draw);
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); submit(); } });
  const body = h('div', { style: 'display:flex;flex-direction:column;gap:12px;overflow-y:auto' },
    input, preview,
    h('div', { style: 'padding:0 20px' }, catPick(catSel, v => { catSel = v; draw(); input.focus(); })),
    M.tags().length ? h('div', { style: 'padding:0 20px' }, tagPick(tagSel, v => { tagSel = v; draw(); })) : null,
    log,
    h('div', { class: 'cmd-help' }, h('span', {}, '#태그  @담당  내일 3시  30분  금요일까지'), grow(), btn('추가', submit, 'primary sm')));
  const dlg = sheet({ body, cls: 'cmd' });
  draw(); input.focus();
  return dlg;
}

// ── 할 일 ────────────────────────────────────────────────────────────
export function openTask(t) {
  const f = { cat: t.cat, tags: [...(t.tags || [])] };
  const title = h('input', { value: t.title, maxlength: 300, autocomplete: 'off' });
  const due = h('input', { type: 'date', value: t.due || '' });
  const who = h('input', { value: t.who || '', placeholder: '예: 김대리', autocomplete: 'off' });
  const note = h('textarea', { placeholder: '배경, 링크, 다음 행동' }); note.value = t.note || '';
  const save = () => M.updateTask(t.id, { title: title.value.trim() || t.title, cat: f.cat, tags: f.tags, due: due.value, who: who.value.trim(), note: note.value.trim() });
  const inTop = (M.dayOf(ui.date).top || []).includes(t.id);
  const fri = addDays(mondayOf(today()), 4);
  const dlg = sheet({
    title: '할 일',
    body: h('div', { class: 'sheet-body' },
      field('무엇을', title),
      field('업무의 성격', catPick(f.cat, v => { f.cat = v; })),
      field('태그', tagPick(f.tags, v => { f.tags = v; })),
      h('div', { class: 'row2' }, field('마감', due), field('담당 (시킬 사람)', who)),
      h('div', { class: 'chips' }, [['오늘', today()], ['내일', addDays(today(), 1)], ['이번 주 금요일', fri], ['마감 없음', '']].map(([l, v]) => h('button', { type: 'button', class: 'chip', onclick: () => { due.value = v; } }, l))),
      field('메모', note),
      h('div', { class: 'acts' },
        t.st !== 'done' ? btn('시간 붙이기', () => { const nt = save(); dlg.close(); openBlock(null, placePreset(nt || t)); }, 'sm') : null,
        t.st !== 'done' ? btn(inTop ? '핵심에서 빼기' : `${relDay(ui.date)} 핵심에 넣기`, () => { save(); if (!M.toggleTop(ui.date, t.id)) toast('핵심은 3개까지예요. 하나를 빼고 넣어 주세요.'); dlg.close(); }, 'sm') : null,
        t.st === 'open' ? btn('넘겼어요 · 기다리는 중으로', () => { save(); M.setTaskWait(t, true); dlg.close(); toast('기다리는 중으로 옮겼어요.'); }, 'sm') : null,
        t.st === 'wait' ? btn('다시 할 일로', () => { save(); M.setTaskWait(t, false); dlg.close(); }, 'sm') : null,
        t.st === 'done' ? btn('다시 할 일로', () => { save(); M.setTaskDone(t, false); dlg.close(); }, 'sm') : null,
        btn('요청 문구 공유', () => { const nt = save(); shareText(M.requestText(nt || t)); }, 'sm'))),
    foot: foot(
      btn('삭제', () => { const undo = M.removeTask(t.id); dlg.close(); toast('할 일을 지웠어요.', { actions: [{ label: '되돌리기', fn: undo }] }); }, 'danger'),
      grow(), btn('취소', () => dlg.close()), btn('저장', () => { save(); dlg.close(); }, 'primary')),
  });
  return dlg;
}
export function placePreset(t) {
  const [start, end] = M.freeSlot(ui.date, M.cat(t.cat).dur, C.gEventsCached(ui.date).filter(e => !e.allDay));
  return { title: t.title, start, end, cat: t.cat, tags: t.tags || [], taskId: t.id, date: ui.date };
}

// ── 시간 블록 ─────────────────────────────────────────────────────────
export function openBlock(b, preset = {}) {
  const src = b || preset;
  const f = { cat: src.cat ?? 0, tags: [...(src.tags || [])] };
  const title = h('input', { value: src.title || '', maxlength: 300, placeholder: '예: 주간 회의', autocomplete: 'off' });
  const date = h('input', { type: 'date', value: src.date || ui.date });
  const start = h('input', { type: 'time', step: 300, value: src.start || '09:00' });
  const end = h('input', { type: 'time', step: 300, value: src.end || '10:00' });
  const durs = h('div', { class: 'chips' }, [15, 30, 45, 60, 90, 120].map(m => h('button', { type: 'button', class: 'chip', onclick: () => { end.value = toHm(Math.min(toMin(start.value) + m, 1439)); } }, durText(m))));
  let lastLen = toMin(end.value) - toMin(start.value);
  start.addEventListener('change', () => { if (start.value) end.value = toHm(Math.min(toMin(start.value) + lastLen, 1439)); });
  end.addEventListener('change', () => { if (start.value && end.value && toMin(end.value) > toMin(start.value)) lastLen = toMin(end.value) - toMin(start.value); });
  const linked = src.taskId && db.get(src.taskId);
  const save = () => {
    if (!start.value || !end.value || !date.value) return toast('날짜와 시간을 채워 주세요.');
    if (toMin(end.value) <= toMin(start.value)) return toast('끝나는 시간이 시작보다 늦어야 해요.');
    const data = { title: title.value.trim() || src.title || '새 블록', date: date.value, start: start.value, end: end.value, cat: f.cat, tags: f.tags };
    if (b) { db.patch(b.id, data); if (linked && (f.cat !== linked.cat || data.title !== linked.title)) M.updateTask(linked.id, { cat: f.cat, title: data.title, tags: f.tags }); }
    else M.addBlock({ ...data, taskId: src.taskId });
    dlg.close();
    if (data.date !== ui.date) toast(`${relDay(data.date)}(${fmtShort(data.date)})에 넣었어요.`, { actions: [{ label: '보러 가기', fn: () => ui.go(data.date) }] });
  };
  const dlg = sheet({
    title: b ? '시간 블록' : '시간 붙이기',
    body: h('div', { class: 'sheet-body' },
      field('무엇을', title),
      h('div', { class: 'row3' }, field('날짜', date), field('시작', start), field('끝', end)),
      durs,
      b?.routine || (!b && linked) ? null : field('업무의 성격', catPick(f.cat, v => { f.cat = v; })),
      b?.routine || (!b && linked) ? null : field('태그', tagPick(f.tags, v => { f.tags = v; })),
      linked ? h('p', { class: 'hint' }, b ? '할 일과 이어진 블록이에요. 블록을 완료하면 할 일도 완료됩니다.' : '비어 있는 시간을 찾아 넣어 두었어요. 시간만 확인하고 저장하세요.') : null,
      b?.routine ? h('p', { class: 'hint' }, '루틴으로 깔린 블록이에요. 이 날짜만 바뀌고, 매일의 기본 시간은 설정 → 루틴에서 바꿉니다.') : null),
    foot: foot(
      b ? btn('삭제', () => { const undo = M.removeBlock(b.id); dlg.close(); toast('블록을 지웠어요.', { actions: [{ label: '되돌리기', fn: undo }] }); }, 'danger') : null,
      grow(), btn('취소', () => dlg.close()), btn('저장', save, 'primary')),
  });
  if (!b && !src.title) title.focus();
  return dlg;
}

// ── 핵심 3 고르기 ─────────────────────────────────────────────────────
export function openTopPicker(date) {
  const list = h('ul', { class: 'picker' });
  const input = h('input', { class: 'input', placeholder: '새로 적어서 바로 핵심에 넣기', enterkeyhint: 'done', autocomplete: 'off' });
  const count = h('span', { class: 'hint' });
  const draw = () => {
    const top = (M.dayOf(date).top || []).filter(id => db.get(id));
    const rank = t => top.includes(t.id) ? -1 : (t.due && t.due <= date ? 0 : t.cat === 1 ? 1 : t.cat === 6 ? 2 : t.cat === 3 ? 3 : 4);
    const pool = M.tasks().filter(t => M.isOpen(t) || top.includes(t.id)).sort((a, b) => rank(a) - rank(b) || (a.at || 0) - (b.at || 0));
    count.textContent = `${top.length}/3 선택`;
    list.replaceChildren(...pool.map(t => h('li', { class: top.includes(t.id) ? 'on' : '', 'data-c': t.cat, onclick: () => { if (!M.toggleTop(date, t.id)) toast('핵심은 3개까지예요.'); draw(); } },
      h('i', { class: 'no' }, top.includes(t.id) ? String(top.indexOf(t.id) + 1) : ''), h('i', { class: 'dot' }), h('span', {}, t.title),
      t.due ? h('em', { class: 'chip ' + dueInfo(t.due).cls, style: 'font-style:normal' }, dueInfo(t.due).text) : null)));
    if (!pool.length) list.replaceChildren(h('li', { class: 'empty', style: 'cursor:default' }, '아직 할 일이 없어요. 위에 바로 적어 보세요.'));
  };
  input.addEventListener('keydown', e => {
    if (e.key !== 'Enter' || e.isComposing || !input.value.trim()) return;
    e.preventDefault();
    const r = M.quickAdd(input.value, { cat: 6, date });
    if (r && !M.toggleTop(date, r.task.id)) toast('핵심은 3개까지예요. 할 일 목록에만 넣었어요.');
    input.value = ''; draw();
  });
  const dlg = sheet({
    title: `${relDay(date)}의 핵심 3가지`,
    body: h('div', { class: 'sheet-body' }, h('p', { class: 'hint' }, '이것만 끝내면 오늘은 성공이라고 할 수 있는 일을 세 개까지 고릅니다.'), input, list),
    foot: foot(count, grow(), btn('완료', () => dlg.close(), 'primary')),
  });
  draw();
  return dlg;
}

// ── 하루 마감 ─────────────────────────────────────────────────────────
export function openCloseDay(date) {
  const d = M.dayOf(date), p = M.dayProgress(date), s = db.settings();
  const next = nextWorkday(date, s.weekdaysOnly);
  const left = M.blocksOn(date).filter(b => !b.done && !b.routine);
  const doneToday = M.tasks().filter(t => t.st === 'done' && t.doneAt && ymd(new Date(t.doneAt)) === date).length;
  const move = new Set(left.map(b => b.id));
  const note = h('textarea', { placeholder: '오늘 가장 잘한 것 하나, 내일 다르게 할 것 하나' }); note.value = d.note || '';
  const close = () => {
    for (const id of move) db.patch(id, { date: next });
    M.setDay(date, { note: note.value.trim(), closedAt: Date.now() });
    ui.justClosed = true;
    dlg.close(); confetti();
    toast(`${fmtMD(date)} 마감했어요. +15점`, { actions: [{ label: `${relDay(next)} 계획하기`, fn: () => ui.go(next) }], ms: 8000 });
  };
  const dlg = sheet({
    title: d.closedAt ? `${fmtMD(date)} 기록` : `${fmtMD(date)} 마감`,
    body: h('div', { class: 'sheet-body' },
      h('div', { class: 'sum' },
        h('div', {}, h('b', {}, `${p.done}/${p.total}`), h('span', {}, '끝낸 블록')),
        h('div', {}, h('b', {}, `${p.topDone}/${p.top}`), h('span', {}, '핵심 달성')),
        h('div', {}, h('b', {}, String(doneToday)), h('span', {}, '끝낸 일'))),
      !d.closedAt && left.length ? h('div', { class: 'field' }, h('span', {}, `못 끝낸 블록 ${left.length}개 — 체크한 것은 ${relDay(next)}(${fmtShort(next)}) 같은 시간으로 옮깁니다`),
        left.map(b => h('label', { class: 'checkline' }, h('input', { type: 'checkbox', checked: true, onchange: e => { e.target.checked ? move.add(b.id) : move.delete(b.id); } }), `${b.start} ${b.title}`))) : null,
      field('한 줄 회고', note)),
    foot: d.closedAt
      ? foot(btn('마감 취소', () => { M.setDay(date, { closedAt: null }); dlg.close(); }, 'danger'), grow(), btn('닫기', () => dlg.close()), btn('회고 저장', () => { M.setDay(date, { note: note.value.trim() }); dlg.close(); }, 'primary'))
      : foot(grow(), btn('취소', () => dlg.close()), btn('도장 찍고 마감', close, 'primary')),
  });
  return dlg;
}

// ── 공유 ─────────────────────────────────────────────────────────────
export function openShare(date) {
  const box = h('div', { class: 'sheet-body' });
  const draw = () => {
    const sh = db.list('share').find(x => x.date === date);
    const linkPart = !C.cloud.user
      ? [h('p', { class: 'hint' }, '링크 공유는 로그인한 뒤에 쓸 수 있어요. 글로 보내기는 지금도 됩니다.')]
      : sh
        ? [h('div', { class: 'linkbox' }, h('input', { class: 'input', readonly: true, value: C.shareUrl(sh.sid), onfocus: e => e.target.select() }), btn('복사', () => copyText(C.shareUrl(sh.sid), '링크를 복사했어요.'), 'primary')),
           h('p', { class: 'hint' }, '이 링크를 가진 사람은 이 날짜의 일정(제목·시간·완료 여부)만 볼 수 있어요. 일정을 고치면 링크 내용도 따라 바뀝니다. 구글 캘린더 일정과 할 일 목록은 보이지 않아요.'),
           btn('공유 중지', async () => { try { await C.shareDelete(sh.sid); db.del(sh.id); toast('공유를 멈췄어요.'); draw(); } catch (e) { toast(e.message); } }, 'danger sm')]
        : [btn('보기 전용 링크 만들기', async e => {
            e.target.disabled = true;
            try { const sid = newId(24); await C.shareSave(sid, M.sharePayload(date, shareName())); db.put({ id: 's' + sid, kind: 'share', sid, date, at: Date.now() }); draw(); }
            catch (err) { toast('링크를 만들지 못했어요: ' + err.message); e.target.disabled = false; }
          }, 'primary block'),
           h('p', { class: 'hint' }, '받는 사람은 로그인 없이 볼 수 있고, 고칠 수는 없어요.')];
    box.replaceChildren(
      h('div', { class: 'field' }, h('span', {}, '링크로 보여 주기'), linkPart),
      h('div', { class: 'field' }, h('span', {}, '글로 보내기 (카카오톡·메일)'),
        h('textarea', { readonly: true, style: 'min-height:120px;font-size:14px' }, M.dayText(date)),
        btn('글 공유·복사', () => shareText(M.dayText(date), `${fmtMD(date)} 일정`), 'block')));
  };
  const dlg = sheet({ title: `${fmtMD(date)} 일정 공유`, body: box });
  draw();
  return dlg;
}
export const shareName = () => db.settings().name || C.cloud.user?.name || '';

// ── 설정 ─────────────────────────────────────────────────────────────
export async function openSettings(openKey) {
  const body = h('div', { class: 'sheet-body', style: 'gap:0' });
  const sec = (key, title, small, ...kids) => h('details', { class: 'set', open: key === openKey, 'data-k': key }, h('summary', {}, title, h('small', {}, small || '')), h('div', {}, kids));
  const push = await C.pushStatus().catch(() => ({ on: false, can: false, text: '' }));
  const draw = () => {
    const openNow = body.querySelector('details[open]')?.dataset.k || openKey;
    openKey = openNow;
    const s = db.settings(), u = C.cloud.user, g = C.cloud.gstate;
    const set = f => { db.setSettings(f); };

    const account = !u
      ? [h('p', { class: 'hint' }, C.cloud.available ? '지금은 이 기기에만 저장돼요. 로그인하면 폰·PC 기록이 이어지고, 알림·구글 캘린더·링크 공유를 쓸 수 있어요. 이미 적어 둔 기록은 그대로 올라갑니다.' : '인터넷에 연결되면 로그인할 수 있어요. 지금은 이 기기에만 저장됩니다.'),
         C.cloud.available ? btn('Google 계정으로 로그인', () => C.login().catch(e => toast(e.message)), 'primary') : null]
      : [h('p', {}, u.email),
         h('p', { class: 'hint' }, db.status.state === 'error' ? `서버와 맞추지 못했어요: ${db.status.error}` : db.meta.lastSync ? `마지막으로 맞춘 시각 ${new Date(db.meta.lastSync).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}` : '아직 맞추지 않았어요.'),
         h('div', { class: 'acts' }, btn('지금 맞추기', async () => { const ok = await db.sync({ full: true }); toast(ok ? '서버와 맞췄어요.' : '맞추지 못했어요. 잠시 뒤 다시 해 주세요.'); draw(); }, 'sm'),
           btn('로그아웃', async () => { if (await C.logout()) { dlg.close(); toast('로그아웃했어요.'); } }, 'sm')),
         field('공유 화면에 보일 이름', h('input', { value: s.name || u.name || '', onchange: e => set({ name: e.target.value.trim() }) }))];

    const gText = { ok: '연결됨 — 시간 블록이 구글 캘린더에 올라가고, 캘린더 일정이 타임라인에 함께 보여요.', off: '연결하면 시간 블록이 구글 캘린더에 자동으로 올라가고, 캘린더 일정이 타임라인에 함께 보여요.', expired: '연결이 끊겼어요. 다시 연결해 주세요.', api_off: 'Google Cloud에서 Calendar API가 꺼져 있어요. 안내서(README)의 "구글 캘린더 켜기"를 따라 켠 뒤 다시 연결해 주세요.', error: '지금은 구글 캘린더에 닿지 않아요. 잠시 뒤 다시 시도합니다.' }[g];
    const calendar = !u ? [h('p', { class: 'hint' }, '로그인한 뒤에 연결할 수 있어요.')] : [
      h('p', { class: 'hint' }, gText),
      h('div', { class: 'acts' }, g === 'ok' ? btn('연결 끊기', async () => { await C.gcalDisconnect(); draw(); }, 'sm') : btn(g === 'off' ? 'Google 캘린더 연결' : '다시 연결', () => C.gcalConnect().catch(e => toast(e.message)), 'primary sm')),
      h('label', { class: 'checkline' }, h('input', { type: 'checkbox', checked: s.gcalRoutines, onchange: e => { set({ gcalRoutines: e.target.checked }); C.gPushSoon(1500); } }), '점심·점검 같은 루틴 블록도 캘린더에 올리기')];

    const notif = [
      h('p', { class: 'hint' }, push.text),
      u ? h('div', { class: 'acts' },
        push.on ? btn('이 기기 알림 끄기', async () => { await C.pushDisable(); Object.assign(push, await C.pushStatus()); draw(); }, 'sm')
          : btn('이 기기에서 알림 켜기', async () => { try { await C.pushEnable(); toast('알림을 켰어요.'); } catch (e) { toast(e.message); } Object.assign(push, await C.pushStatus()); draw(); }, 'primary sm', ),
        push.on ? btn('테스트 알림 보내기', async () => { try { const n = await C.pushTest(); toast(n ? `기기 ${n}대로 보냈어요. 곧 도착합니다.` : '알림 받는 기기가 없어요.'); } catch (e) { toast('보내지 못했어요: ' + e.message); } }, 'sm') : null) : null,
      field('시작 전 미리 알림', h('select', { onchange: e => set({ remindMin: Number(e.target.value) }) }, [[0, '끔'], [5, '5분 전'], [10, '10분 전'], [15, '15분 전'], [30, '30분 전']].map(([v, l]) => h('option', { value: v, selected: s.remindMin === v }, l)))),
      h('label', { class: 'checkline' }, h('input', { type: 'checkbox', checked: s.remindAtStart, onchange: e => set({ remindAtStart: e.target.checked }) }), '시작 시각에도 알림'),
      field('아침 요약 알림 (비우면 끔)', h('input', { type: 'time', value: s.morningTime || '', onchange: e => set({ morningTime: e.target.value }) })),
      h('label', { class: 'checkline' }, h('input', { type: 'checkbox', checked: s.weekdaysOnly, onchange: e => set({ weekdaysOnly: e.target.checked }) }), '주말은 쉬는 날 (아침 알림·연속 기록에서 제외)')];

    const rs = s.routines || [];
    const setR = (i, f) => set({ routines: rs.map((r, j) => j === i ? { ...r, ...f } : r) });
    const routines = [
      h('p', { class: 'hint' }, '매일 같은 시간에 깔리는 블록이에요. 바꾼 내용은 아직 열어 보지 않은 날짜부터 적용됩니다.'),
      rs.map((r, i) => h('div', { class: 'rowline routine' },
        h('input', { class: 'input', type: 'time', value: r.start, onchange: e => e.target.value && setR(i, { start: e.target.value, end: toMin(r.end) > toMin(e.target.value) ? r.end : toHm(toMin(e.target.value) + 30) }) }),
        h('input', { class: 'input', type: 'time', value: r.end, onchange: e => e.target.value && toMin(e.target.value) > toMin(r.start) && setR(i, { end: e.target.value }) }),
        h('input', { class: 'input', value: r.title, onchange: e => setR(i, { title: e.target.value.trim() || r.title }) }),
        h('select', { class: 'input', onchange: e => setR(i, { days: e.target.value }) }, h('option', { value: 'wd', selected: r.days !== 'all' }, '평일'), h('option', { value: 'all', selected: r.days === 'all' }, '매일')),
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': '루틴 지우기', onclick: () => { set({ routines: rs.filter((_, j) => j !== i) }); draw(); } }, icon('x', 16)))),
      btn('+ 루틴 추가', () => { set({ routines: [...rs, { id: newId(6), start: '09:00', end: '09:30', title: '새 루틴', days: 'wd' }] }); draw(); }, 'sm')];

    const tagRows = M.tags();
    const tags = [
      tagRows.length ? null : h('p', { class: 'hint' }, '할 일에 #프로젝트이름 처럼 적으면 태그가 자동으로 생겨요.'),
      tagRows.map(t => h('div', { class: 'rowline' },
        h('button', { class: 'swatch', type: 'button', 'aria-label': '색 바꾸기', style: `--dot:${t.color}`, onclick: () => { const i = M.TAG_COLORS.indexOf(t.color); set({ tags: tagRows.map(x => x.name === t.name ? { ...x, color: M.TAG_COLORS[(i + 1) % M.TAG_COLORS.length] } : x) }); draw(); } }),
        h('input', { class: 'input', value: t.name, onchange: e => { M.renameTag(t.name, e.target.value); draw(); } }),
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': '태그 지우기', onclick: () => { if (confirm(`'${t.name}' 태그를 지울까요? 할 일은 그대로 두고 태그만 뗍니다.`)) { M.removeTag(t.name); draw(); } } }, icon('x', 16)))),
      h('div', { class: 'rowline' }, h('input', { class: 'input', placeholder: '새 태그 이름', onkeydown: e => { if (e.key === 'Enter' && !e.isComposing && e.target.value.trim()) { M.ensureTags([e.target.value.trim().replace(/[\s#@!]/g, '')]); draw(); } } }))];

    const catRows = [h('p', { class: 'hint' }, '여섯 가지 성격의 이름을 내 말로 바꿀 수 있어요.'),
      M.cats().map(c => h('div', { class: 'rowline', 'data-c': c.id },
        h('span', { class: 'sec-no' }, String(c.id)),
        h('input', { class: 'input', value: c.name, onchange: e => set({ cats: { ...s.cats, [c.id]: { ...(s.cats?.[c.id] || {}), name: e.target.value.trim() || c.name } } }) }),
        h('input', { class: 'input', value: c.hint, onchange: e => set({ cats: { ...s.cats, [c.id]: { ...(s.cats?.[c.id] || {}), hint: e.target.value.trim() } } }) })))];

    const shares = db.list('share').slice().sort((a, b) => b.date.localeCompare(a.date));
    const shareRows = shares.length ? shares.map(sh => h('div', { class: 'rowline' },
      h('span', { style: 'flex:1' }, fmtFull(sh.date)),
      btn('링크 복사', () => copyText(C.shareUrl(sh.sid), '링크를 복사했어요.'), 'sm'),
      btn('중지', async () => { try { await C.shareDelete(sh.sid); db.del(sh.id); draw(); } catch (e) { toast(e.message); } }, 'sm danger')))
      : [h('p', { class: 'hint' }, '공유 중인 링크가 없어요. 하루 화면의 "공유"에서 만들 수 있어요.')];

    const stamp = today();
    const file = h('input', { type: 'file', accept: '.json,application/json', style: 'display:none', onchange: async e => {
      try { const j = JSON.parse(await e.target.files[0].text()); const n = db.importItems(Array.isArray(j) ? j : j.items || []); toast(`${n}개 항목을 가져왔어요.`); }
      catch { toast('백업 파일을 읽지 못했어요.'); }
    } });
    const paste = h('textarea', { placeholder: '한 줄에 하나씩 붙여 넣으세요.\n예) 내일 3시 견적서 보내기 #영업\n엑셀에서 복사한 칸도 그대로 붙여 넣을 수 있어요.' });
    const data = [
      h('p', { class: 'hint' }, '기록은 언제든 통째로 꺼낼 수 있어요. 모두 메모장·엑셀·노션에서 바로 열리는 형식입니다.'),
      h('div', { class: 'acts' },
        btn('전체 백업 (JSON)', () => download(`planner-backup-${stamp}.json`, M.exportJson(), 'application/json'), 'sm'),
        btn('할 일 (엑셀 CSV)', () => download(`planner-tasks-${stamp}.csv`, M.exportTasksCsv(), 'text/csv'), 'sm'),
        btn('시간 기록 (엑셀 CSV)', () => download(`planner-time-${stamp}.csv`, M.exportBlocksCsv(), 'text/csv'), 'sm'),
        btn('업무 일지 (Markdown)', () => download(`planner-journal-${stamp}.md`, M.exportMarkdown(), 'text/markdown'), 'sm')),
      h('div', { class: 'acts' }, btn('백업 파일 불러오기', () => file.click(), 'sm'), file),
      field('여러 개 한꺼번에 넣기', paste),
      btn('할 일로 추가', () => {
        const lines = paste.value.split(/\r?\n/).map(l => l.split('\t').map(c => c.trim()).filter(Boolean).join(' ')).filter(Boolean);
        lines.forEach(l => M.quickAdd(l, { cat: 0, date: today() }));
        if (lines.length) { paste.value = ''; toast(`${lines.length}개를 넣었어요. "분류 전"에서 성격을 정해 주세요.`); }
      }, 'sm')];

    let theme = 'auto';
    try { theme = localStorage.getItem('planner:theme') || 'auto'; } catch { /* 기본값 */ }
    const look = [h('div', { class: 'chips' }, [['auto', '기기 설정대로'], ['light', '밝게'], ['dark', '어둡게']].map(([v, l]) => h('button', { type: 'button', class: 'chip' + (theme === v ? ' on' : ''), onclick: () => {
      try { v === 'auto' ? localStorage.removeItem('planner:theme') : localStorage.setItem('planner:theme', v); } catch { /* 무시 */ }
      if (v === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = v;
      draw();
    } }, l)))];

    body.replaceChildren(
      sec('account', '계정과 기록 맞추기', u ? '로그인됨' : '이 기기에만 저장 중', account),
      sec('gcal', 'Google 캘린더', { ok: '연결됨', off: '연결 안 됨', expired: '다시 연결 필요', api_off: '설정 필요', error: '확인 중' }[g], calendar),
      sec('notif', '알림', push.on ? '켜짐' : '꺼짐', notif),
      sec('routine', '루틴', `${rs.length}개`, routines),
      sec('tags', '태그', `${tagRows.length}개`, tags),
      sec('cats', '업무의 성격 이름', '', catRows),
      sec('share', '공유 중인 링크', shares.length ? `${shares.length}개` : '', shareRows),
      sec('data', '기록 내보내기·가져오기', '', data),
      sec('look', '화면', '', look));
  };
  const dlg = sheet({ title: '설정', body, cls: 'wide' });
  draw();
  return dlg;
}
