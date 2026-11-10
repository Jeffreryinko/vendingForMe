"""사용: 저장소 맨 위에서  python robot/tests/sisa_replay.py <시작판> [-v]   (예: 2026-11-08_h21)
지난 판들을 새 규칙으로 다시 돌려 보기 (저장소 자료만 씀, 아무것도 안 바꿈)"""
import json, glob, sys, copy, statistics
sys.path.insert(0, 'robot'); sys.path.insert(0, 'robot/crawler')
import fresh as F
from cluster import tokens, GENERIC, build_stories
SC = {"reddit-worldnews": "WW"}
ctry = lambda it: SC.get(it["s"], it["c"])
title = lambda it: it.get("ko") or (it["t"] if it["_lang"] == "ko" else "")
def feed(ed):
    out = {}
    for f in glob.glob(f'data/sisa/feed/{ed}__*.json'):
        lang = f.split('__')[1][:-5]
        for it in json.load(open(f))['items']:
            it["_lang"] = lang; out[it["id"]] = it
    return out
eds = [p.split('/')[-1][:-5] for p in sorted(glob.glob('data/sisa/editions/20*.json'))]
start = sys.argv[1]; k0 = eds.index(start)
P = json.load(open(f'data/sisa/editions/{start}.json'))['stories']; TOPS = []
prev = start
for ed in eds[k0 + 1:]:
    items = feed(ed); prev_items = feed(prev); now = F.now_of(ed)
    for i in [i for i, it in items.items() if it.get("carried")]: prev_items.setdefault(i, items.pop(i))     # 옛 규칙이 붙여 둔 글은 '피드에서 밀려난 글'로
    out, carried, ended, used = F.carry(P, items, prev_items, ed, tokens, GENERIC, title, ctry)
    # 새 이슈 후보: 그 판의 낱말 묶음 중 아직 안 쓴 글
    raw = [{"id": it["id"], "kind": it["k"], "title_ko": title(it), "published_at": it.get("p"), "first_seen_at": it.get("p") or "", "source_id": it["s"], "lang": it["_lang"], "country": it["c"]}
           for it in items.values() if F.age_h(it, now) <= F.FEED_H]
    cand = []
    for s in build_stories(raw, ed[:10]):
        rest = [i for i in s["item_ids"] if i not in used and i in items and F.age_h(items[i], now) <= F.LIVE_H]
        if len(rest) >= 2 and len({items[i]["s"] for i in rest}) >= 2:
            its = [items[i] for i in rest]; tk = {x["id"]: tokens(title(x)) for x in its}
            rep = max(its, key=lambda it: sum(len(tk[it["id"]] & tk[o["id"]]) for o in its if o is not it))
            rt = tokens(title(rep)) - GENERIC; PR = F.proper_names()
            rest = [x["id"] for x in its if x is rep or len((tk[x["id"]] - GENERIC) & rt) >= 2 or ((tk[x["id"]] - GENERIC) & rt & PR)]     # sisa_edit.tighten 과 같은 규칙
            if len(rest) < 2 or len({items[i]["s"] for i in rest}) < 2: continue
            its = [items[i] for i in rest]
            c = {"items": rest, "title": title(rep), "kw": s["keywords"], "method": "auto-v1", "born": ed, "kind": "global" if len({ctry(x) for x in its}) >= 2 else "local",
                 "countries": sorted({ctry(x) for x in its}), "where": [ctry(rep)], "cat": ""}
            F.stamp(c, items, ed); used |= set(rest); cand.append(c)
    st = out + cand
    main = [s for s in st if s.get("kind") != "brief"]
    main.sort(key=lambda s: F.heat(s, items, ed, ctry), reverse=True)
    top = F.pick_top(main, tokens, GENERIC, wide=lambda s: F.breadth(s, items, ed, ctry))
    TOPS.append([s["title"] for s in top])
    big = max((len(s["items"]) for s in st), default=0); n_news = sum(1 for it in items.values() if it["k"] != "trend")
    life = {}
    for s in main: life[s["life"]] = life.get(s["life"], 0) + 1
    newest = lambda s: round(min(F.age_h(items[i], now) for i in s["items"]))
    print(f"== {ed}  이어받음 {len(out)} (끝남 {len(ended)}) + 새 후보 {len(cand)} · 큰 이슈 {len(main)} {life} · 가장 큰 이슈 {big}개({big * 100 // max(n_news,1)}%)")
    for s in top: print(f"   TOP [{s['life']:4}] 열기 {F.heat(s, items, ed, ctry):5.1f} · 글 {len(s['items']):3} · 새 글 {newest(s):2}시간 전 · 태어남 {s['born'][5:]} | {s['title'][:46]}")
    if '-v' in sys.argv:
        for e in ended[:8]: print('      끝남:', e['title'][:50])
    P = st; prev = ed

import collections
c = collections.Counter(t for tt in TOPS for t in tt)
print("\n판", len(TOPS), "· 5대 이슈 칸", sum(len(t) for t in TOPS), "· 서로 다른 제목", len(c), "· 가장 오래 머문 것", c.most_common(3)[0][1], "판")
