// 화면 공통 부품: 상태, 알림 띠, 시트(대화창), 색종이, 분류·태그 고르기
import { h, icon, today, mondayOf } from './util.js';
import * as M from './model.js';

export const ui = {
  date: today(), tab: 'day', tag: null, showDone: false, showWait: false,
  week: mondayOf(today()), justClosed: false,
  render: () => {},          // main.js 가 채움
  go: () => {},              // 날짜 이동
};
export const $ = s => document.querySelector(s);
export const isPhone = () => matchMedia('(max-width: 619px)').matches;      // 한 칸씩 보는 좁은 화면 (폰 · 접은 폴드)

// ── 알림 띠 ──
export function toast(msg, opt = {}) {
  const box = $('#toasts');
  const el = h('div', { class: 'toast' }, h('span', {}, msg),
    (opt.actions || []).map(a => h('button', { type: 'button', onclick: () => { a.fn(); el.remove(); } }, a.label)));
  box.replaceChildren(el);
  setTimeout(() => el.remove(), opt.ms || (opt.actions ? 6000 : 2600));
}

// ── 시트 ──
export function sheet({ title, body, foot, cls = '', onClose }) {
  const dlg = h('dialog', { class: 'sheet ' + cls },
    title ? h('div', { class: 'sheet-head' }, h('h3', {}, title), h('button', { class: 'icon-btn', type: 'button', 'aria-label': '닫기', onclick: () => dlg.close() }, icon('x'))) : null,
    body, foot || null);
  document.body.append(dlg);
  dlg.addEventListener('close', () => { dlg.remove(); onClose?.(); });
  dlg.addEventListener('mousedown', e => { if (e.target === dlg) dlg.close(); });
  dlg.tabIndex = -1;
  dlg.showModal();
  dlg.focus();
  return dlg;
}
export const field = (label, control) => h('label', { class: 'field' }, h('span', {}, label), control);

// ── 분류 고르기 / 태그 고르기 ──
export function catPick(value, onChange, withNone = true) {
  const wrap = h('div', { class: 'catpick' });
  const draw = () => wrap.replaceChildren(...[...M.cats(), ...(withNone ? [M.cat(0)] : [])].map(c =>
    h('button', { type: 'button', 'data-c': c.id, class: c.id === value ? 'on' : '', onclick: () => { value = c.id; onChange(value); draw(); } },
      h('i', {}, c.id ? String(c.id) : '·'), h('span', {}, c.id ? c.name : '아직 정하지 않음 (분류 전)'))));
  draw();
  return wrap;
}
export function tagPick(selected, onChange) {
  const sel = new Set(selected);
  const wrap = h('div', { class: 'chips' });
  const draw = () => {
    const names = [...new Set([...M.tags().map(t => t.name), ...sel])];
    const input = h('input', { class: 'input', placeholder: '새 태그', style: 'width:96px;height:24px;padding:0 9px;font-size:12.5px;border-radius:999px', enterkeyhint: 'done',
      onkeydown: e => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); add(); } }, onblur: () => add() });
    const add = () => { const v = input.value.trim().replace(/[\s#@!]/g, ''); if (!v) return; sel.add(v); onChange([...sel]); draw(); };
    wrap.replaceChildren(...names.map(n => h('button', { type: 'button', class: 'chip tag' + (sel.has(n) ? ' on' : ''), style: `--dot:${M.tagColor(n)}`,
      onclick: () => { sel.has(n) ? sel.delete(n) : sel.add(n); onChange([...sel]); draw(); } }, n)), input);
  };
  draw();
  return wrap;
}

// ── 색종이 (핵심 3 달성 · 하루 마감) ──
export function confetti() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const cv = $('#confetti'), ctx = cv.getContext('2d');
  const W = cv.width = innerWidth, H = cv.height = innerHeight;
  cv.style.display = 'block';
  const css = getComputedStyle(document.documentElement);
  const colors = ['--c1', '--c2', '--c3', '--c4', '--c5', '--c6', '--seal'].map(v => css.getPropertyValue(v).trim());
  const ps = Array.from({ length: 90 }, () => ({ x: W / 2 + (Math.random() - .5) * 120, y: H * .38, vx: (Math.random() - .5) * 13, vy: -Math.random() * 12 - 4, r: Math.random() * 5 + 3, c: colors[Math.random() * colors.length | 0], a: Math.random() * 6, va: (Math.random() - .5) * .4 }));
  let t = 0;
  (function frame() {
    ctx.clearRect(0, 0, W, H);
    for (const p of ps) {
      p.vy += .32; p.x += p.vx; p.y += p.vy; p.vx *= .99; p.a += p.va;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.a); ctx.globalAlpha = Math.max(0, 1 - t / 95);
      ctx.fillStyle = p.c; ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); ctx.restore();
    }
    if (++t < 95) requestAnimationFrame(frame); else cv.style.display = 'none';
  })();
}

export async function copyText(text, okMsg = '복사했어요.') {
  try { await navigator.clipboard.writeText(text); toast(okMsg); }
  catch { const ta = h('textarea', { style: 'position:fixed;opacity:0' }); ta.value = text; document.body.append(ta); ta.select(); document.execCommand('copy'); ta.remove(); toast(okMsg); }
}
export async function shareText(text, title) {
  if (navigator.share) { try { await navigator.share({ text, title }); return; } catch (e) { if (e.name === 'AbortError') return; } }
  copyText(text);
}
