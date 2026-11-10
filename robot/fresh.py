"""fresh.py — 시사 '새로움' 규칙 (토큰 0). 이슈가 태어나고·자라고·식고·내려가게 하는 계산을 한곳에 모음.

왜: 11월 10일 판을 재 보니 ① 발행 시각 없는 글이 영원히 '새 글' 취급돼 일주일 된 이슈가 안 내려가고
    ② 한 이슈가 글이 붙을 때마다 핵심어를 늘려 전체 글의 84%를 빨아들이고 ③ 순위에 시간이 없어 같은 이슈가 28판 연속 1위였음.
    (기획서: 프로젝트 문서 '자판기-시사-개편-기획서')

쓰는 곳
  robot/pipeline/hourly.py   carry()      이전 판 이슈 이어받기 (수명·블랙홀 막기)
  robot/sisa_edit.py         heat() · pick_top()   순위(시간 감쇠) · 꼭 알아야 할 5개(자격·다양성)
  robot/builder/build_edition.py  too_old()   72시간 넘은 글은 판에 안 실음

규칙 (숫자를 바꾸려면 아래 상수만)
  글의 나이   = 발행 시각 기준. 발행 시각이 없으면 '로봇이 처음 본 판'의 시각
  LIVE_H 48   이 시간 안의 글만 이슈의 근거가 됨 → 근거가 모자라면 이슈는 내려감(끝난 이슈)
  CARRY_H 30  피드에서 밀려난 글을 이슈에 남겨 두는 시간
  COOL_H 24   이 시간 동안 새 글이 없으면 '식는 중' → 꼭 알아야 할 5개 자격 없음
  NEW_H 12    태어난 지 이 시간 안이면 '새 이슈'
  FEED_H 72   이보다 오래된(발행 시각 기준) 글은 판에 안 실음
  이슈의 핵심어(core)는 처음 정해지면 고정 — 글이 붙어도 늘리지 않음 (블랙홀 막기)
  새 글이 붙으려면: 핵심어와 2개 이상 겹치고 + (이름 사전의 고유명사가 끼어 있거나, 겹친 낱말이 충분히 드물어야)
  한 이슈는 전체 글의 CAP_RATE(8%)·최소 CAP_MIN(60)개까지 — 넘으면 최신 글만
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
LIVE_H, CARRY_H, COOL_H, NEW_H, FEED_H = 48, 30, 24, 12, 72
CAP_MIN, CAP_RATE = 60, 0.08
RARE = 0.03          # 겹친 낱말이 평균적으로 전체 글의 3% 아래에만 나와야 '드물다'
ONE_RARE = 0.01      # 낱말 하나만 겹칠 때는 그 낱말이 고유명사이고 전체 글의 1% 아래에만 나와야 함
TOP_MIN = 10         # 꼭 알아야 할 것에 오르려면: 최근 24시간 나라 수×3 + 출처 수×2 가 이 값 이상 (예: 2개국·2곳)
CORE_MAX = 14
ROOT = Path(__file__).resolve().parent.parent


def ed_time(ed):
    """판 이름 '2026-11-10_h15' → 그 시각(한국 시간)"""
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)_h(\d\d)", ed or "")
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), tzinfo=KST) if m else None


def now_of(ed):
    """그 판을 만드는 '지금' — 판 시각 + 1시간 (수집이 그 시각에 시작해 한 시간 안에 끝남)"""
    t = ed_time(ed)
    return (t + timedelta(hours=1)) if t else datetime.now(KST)


def item_time(it):
    """글의 시각: 발행 시각(p), 없으면 로봇이 처음 본 판(first)의 시각"""
    p = it.get("p") or it.get("published_at")
    if p:
        try:
            d = datetime.fromisoformat(str(p).replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return ed_time(it.get("first") or it.get("_first"))


def age_h(it, now):
    t = item_time(it)
    return 9999.0 if t is None else max(0.0, (now - t).total_seconds() / 3600)


def too_old(published_at, now, hours=FEED_H):
    """발행 시각이 있고 hours 보다 오래됐으면 True (발행 시각이 없으면 False — 처음 본 시각으로 따로 셈)"""
    if not published_at: return False
    try:
        d = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return (now - d).total_seconds() / 3600 > hours
    except Exception:
        return False


_PROPER = None


def proper_names():
    """이름 사전(사람·장소·기관·사건)의 한국어 이름 — 묶을 때 '확실한 근거'로 침"""
    global _PROPER
    if _PROPER is None:
        try:
            m = json.loads((ROOT / "data/sisa/brief/ents.json").read_text(encoding="utf-8")).get("map", {})
            _PROPER = frozenset(k for k in m if len(k) >= 2)
        except Exception:
            _PROPER = frozenset()
    return _PROPER


# 어느 사건에나 나오는 말 — 핵심어로 안 씀 (이것만 겹쳐서 '스페인 폭발'이 '튀르키예 폭발'에 붙던 것 막기)
WEAK = set("발생 발생한 발생해 수가 증가 감소 이후 관련 위해 대한 통해 지난 오늘 현지 당국 사건 소식 결과 상황 문제 가능성 예정 계획 최근 이번 처음 다시 이상 이하 사람들 사람 지역 국가 정부".split())
_NUM = re.compile(r"\d")


def core_ok(t, GENERIC):
    return t not in GENERIC and t not in WEAK and not _NUM.search(t)


def core_of(s, tokens, GENERIC):
    """이슈의 핵심어: 제목 + 묶음 이름 낱말에서 흔한 말·숫자 낱말을 뺀 것. 한 번 정하면 s['core'] 에 적어 두고 그대로 씀"""
    if s.get("core"): return {t for t in s["core"] if core_ok(t, GENERIC)}
    c = [t for t in tokens(s.get("title") or "") if core_ok(t, GENERIC)]
    for k in (s.get("kw") or []):
        for t in tokens(str(k)):
            if core_ok(t, GENERIC) and t not in c: c.append(t)
    return set(c[:CORE_MAX])


def carry(prev_stories, items, prev_items, ed, tokens, GENERIC, title_of, ctry, proper=None):
    """이전 판 이슈를 새 판으로 이어받음.
    돌려주는 것: (이어받은 이슈 목록, 피드에서 밀려났지만 남겨 둘 글 {언어: [글]}, 끝난 이슈 목록, 쓴 글 id 모음)"""
    now = now_of(ed); proper = proper_names() if proper is None else proper
    tk = {}
    def toks(it):
        i = it["id"]
        if i not in tk: tk[i] = tokens(title_of(it))
        return tk[i]
    pool = [it for it in items.values() if it.get("k") != "trend"]
    n = max(len(pool), 2); df = Counter(t for it in pool for t in toks(it))
    idf = lambda t: math.log(n / max(df.get(t, 1), 1))
    thr = 2 * math.log(1 / RARE)
    cap = max(CAP_MIN, int(n * CAP_RATE))

    one = math.log(1 / ONE_RARE)
    def fit(it, core, need=2):
        ov = toks(it) & core
        if len(ov) == 1 and need <= 2:                       # 낱말 하나만 겹쳐도: 이름 사전의 고유명사이고 아주 드물면(전체 글의 1% 아래) 같은 사건으로 봄 (예: 아이젠코트)
            t = next(iter(ov)); return t in proper and idf(t) >= one
        if len(ov) < need: return False
        if ov & proper: return True
        return len(ov) >= need + 1 and sum(idf(t) for t in ov) >= thr      # 고유명사 없이 붙으려면 한 낱말 더 (예: 공장·폭발·사고)

    used = set(); out = []; carried = {}; ended = []
    order = sorted([x for x in prev_stories if x.get("method") in ("ai-v1", "auto-v1")], key=lambda s: len(s.get("items") or []))   # 작은 이슈부터 (큰 이슈가 다 가져가지 않게)
    for s in order:
        brief = s.get("kind") == "brief"
        first_time = not s.get("core")                       # 새 규칙을 처음 적용받는 이슈 → 지금 있는 글도 전부 다시 검사 (블랙홀 청소)
        core = core_of(s, tokens, GENERIC)
        keep = []
        for i in s.get("items") or []:
            it = items.get(i); back = False
            if not it:
                it = prev_items.get(i)
                if not it or it.get("k") == "trend" or age_h(it, now) > CARRY_H: continue
                back = True
            if i in used or age_h(it, now) > LIVE_H: continue
            t = toks(it)
            if t and core and not brief:                     # 번역이 없는 글(낱말 없음)은 판단할 수 없어 그대로 둠
                if first_time and not fit(it, core): continue
                if not first_time and not (t & core): continue
            if back:
                carried.setdefault(it.get("_lang", ""), []).append({k: v for k, v in it.items() if k != "_lang"}); items[i] = it
            keep.append(i)
        added = []
        if core:
            for i, it in items.items():
                if i in used or i in keep or it.get("k") == "trend" or it.get("first") != ed or age_h(it, now) > LIVE_H: continue
                if fit(it, core, 3 if brief else 2): added.append(i)
        ids = keep + added
        if len(ids) > cap: ids = sorted(ids, key=lambda i: age_h(items[i], now))[:cap]; added = [i for i in added if i in ids]
        if len(ids) < (1 if brief else 2):
            ended.append({"title": s.get("title") or s.get("label") or "", "born": s.get("born") or "", "cat": s.get("cat") or "", "kind": s.get("kind") or ""})
            continue
        used |= set(ids)
        s2 = dict(s); s2["items"] = ids; s2["core"] = sorted(core)
        s2["countries"] = sorted({ctry(items[i]) for i in ids}); s2["langs"] = sorted({items[i].get("_lang", "") for i in ids})
        if brief and len(ids) >= 2:
            s2["kind"] = "global" if len(s2["countries"]) >= 2 else "local"
        elif not s2.get("kind"):
            s2["kind"] = "global" if len(s2["countries"]) >= 2 else "local"
        s2["grow"] = len(added); s2["_added"] = added
        stamp(s2, items, ed, added=bool(added))
        out.append(s2)
    return out, carried, ended, used


def stamp(s, items, ed, added=False):
    """이슈에 수명 표시를 붙임: born(태어난 판) · last(가장 새 글 시각) · life(new·hot·on·cool) · delta(화면이 쓰는 값)"""
    now = now_of(ed)
    its = [items[i] for i in s.get("items") or [] if i in items]
    if not s.get("born"):
        fs = sorted(x.get("first") for x in its if x.get("first"))
        s["born"] = fs[0] if fs else ed
    ages = [age_h(x, now) for x in its] or [9999.0]
    newest = min(ages)
    ts = [t for t in (item_time(x) for x in its) if t]
    if ts: s["last"] = max(ts).astimezone(KST).strftime("%Y-%m-%dT%H:%M")
    src12 = {x["s"] for x in its if age_h(x, now) <= NEW_H}
    born_t = ed_time(s["born"])
    young = born_t is not None and (now - born_t).total_seconds() / 3600 <= NEW_H + 1
    s["life"] = "new" if young else "hot" if (len(src12) >= 2 or added) and newest <= NEW_H else "cool" if newest > COOL_H else "on"
    s["delta"] = {"new": "new", "hot": "grown"}.get(s["life"], "same")
    return s


def give_sid(stories, ed):
    """이슈마다 판이 바뀌어도 그대로인 번호(sid)를 붙임. 이미 있으면 그대로 둠 — 폰이 '읽은 이슈'를 판을 넘어 기억하는 열쇠.
    번호는 태어난 판 + 대표 글(없으면 첫 글)로 한 번만 만들고, 다음 판부터는 이어받은 이슈 그대로 따라감."""
    import hashlib
    have = {s["sid"] for s in stories if s.get("sid")}
    for s in stories:
        if s.get("sid"): continue
        base = f'{s.get("born") or ed}|{s.get("rep_id") or (s.get("items") or [""])[0]}|{s.get("kind") or ""}'
        k = 0
        while True:
            sid = "s" + hashlib.md5(f"{base}|{k}".encode()).hexdigest()[:7]
            if sid not in have: break
            k += 1
        s["sid"] = sid; have.add(sid)
    return stories


def breadth(s, items, ed, ctry):
    """최근 24시간에 이 이슈를 다룬 폭: 나라 수×3 + 출처 수×2"""
    now = now_of(ed)
    live = [items[i] for i in s.get("items") or [] if i in items and age_h(items[i], now) <= COOL_H]
    return len({ctry(x) for x in live}) * 3 + len({x["s"] for x in live}) * 2


def heat(s, items, ed, ctry):
    """순위 점수: 최근 24시간에 불어난 폭(나라·출처) ÷ (가장 새 글의 나이 + 2시간)^1.2  — 새 글이 끊기면 빠르게 내려감"""
    now = now_of(ed)
    its = [items[i] for i in s.get("items") or [] if i in items]
    if not its: return 0.0
    live = [x for x in its if age_h(x, now) <= COOL_H]
    cs = {ctry(x) for x in live}; ns = {x["s"] for x in live}
    newest = min(age_h(x, now) for x in its)
    base = len(cs) * 3 + len(ns) * 2 + (3 if s.get("life") == "new" else 0) + (2 if "KR" in cs else 0)
    return base / (newest + 2) ** 1.2


def pick_top(ranked, tokens, GENERIC, n=5, wide=None, proper=None):
    """꼭 알아야 할 것: 새 이슈·커지는 이슈만, 같은 분야 2개·같은 나라 2개까지, 같은 얘기(제목 낱말 2개 겹침)는 하나만.
    자격 있는 이슈가 모자라면 억지로 채우지 않되, 최소 3개는 '식지 않은' 이슈로 채움"""
    picked = []; cat = Counter(); cc = Counter(); seen = []
    proper = proper_names() if proper is None else proper
    def ok(s):
        if wide is not None and wide(s) < TOP_MIN: return None           # 한두 곳만 다룬 작은 이슈는 5대 이슈에 안 올림
        tk = {t for t in tokens(s.get("title") or "") if t not in GENERIC} | core_of(s, tokens, GENERIC)     # 제목 + 묶음 낱말 (제목 표기가 달라도 — Nvidia·엔비디아)
        if any(len(tk & o) >= 2 or (tk & o & proper) for o in seen): return None   # 같은 사건이 두 칸을 차지하지 않게
        c = s.get("cat") or "-"; w = (s.get("where") or s.get("countries") or ["-"])[0]
        if cat[c] >= 2 or cc[w] >= 2: return None
        return tk, c, w
    for want in (("new", "hot"), ("on",)):
        for s in ranked:
            if len(picked) >= (n if want[0] == "new" else 3): break
            if any(s is p for p in picked) or s.get("life") not in want: continue
            r = ok(s)
            if not r: continue
            picked.append(s); seen.append(r[0]); cat[r[1]] += 1; cc[r[2]] += 1
    return picked
