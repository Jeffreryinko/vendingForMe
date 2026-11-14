"""book_deep.py — 이야기 자판기 '책' 탭: 많이 추천된 책 순서로 '깊이 소개'를 Claude(API)가 써요 (결정: 책 깊이 소개).
목록: vfm-story 저장소 data/book/top.json (raw 로 읽음) · 근거: 한국어 위키백과(없으면 영어) 문서
결과: data/book/deep_ai.json { at, byId: { 책id: {one, body[], start, q[], wiki} } } → vfm-story book 화면이 불러 붙임
  python robot/book_deep.py [--dry]    환경: BOOK_N(기본 100) · BOOK_FAST=1
"""
from __future__ import annotations

import json, os, re, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/book/deep_ai.json"
TOP = "https://raw.githubusercontent.com/Jeffreryinko/vfm-story/main/data/book/top.json"
HAND = {"be81940dae", "bb7a303277", "bcb018ff61", "bf3bc70eab", "b3ac832bc4", "b7c387f3c7", "b89b2ebf9d", "b74b979ba8", "bcb434bf8c", "b848f24dbf", "b7bf3f39a0", "b897ad573f"}   # 손으로 쓴 12권 (book/deep.js)
PER = 4

PROMPT = """너는 한국 독자에게 고전과 좋은 책을 소개하는 서평가예요. 아래 책마다 '깊이 소개'를 써요.
독자는 바쁘고 집중이 쉽게 흩어지는 직장인이에요. 쉬운 해요체, 짧은 문장, 구체적인 장면.
- one: 이 책을 한 문장으로(45자 안쪽, 인상적으로).
- body: 문단 4개, 각 180~280자. ① 누가 언제 왜 썼나(시대 배경) ② 핵심 내용·줄거리 ③ 이 책만의 읽는 맛·유명한 장면 ④ 그 뒤의 영향과 비판(공정하게).
- start: 어디서부터 읽으면 좋은지 한두 문장(장 이름은 확실할 때만).
- q: 읽고 나서 생각해 볼 질문 2개.
- 사실(연도·이름·장 제목)은 주어진 위키백과와 확실히 아는 것만. 원문을 길게 인용하지 마요(한 문장 이하). 큰따옴표 대신 ‘ ’.
JSON 하나만: {{"books":[{{"id":"...","one":"","body":["","","",""],"start":"","q":["",""]}}]}}

책:
{items}"""


def wiki(title, author):
    for lang in ("ko", "en"):
        try:
            q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": f"{title} {author}".strip(), "srlimit": 1, "format": "json"})
            hit = (BR.http_json(f"https://{lang}.wikipedia.org/w/api.php?" + q, timeout=20).get("query") or {}).get("search") or []
            if not hit: continue
            t = hit[0]["title"]; time.sleep(0.6)
            q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": t, "format": "json", "formatversion": 2})
            pg = (BR.http_json(f"https://{lang}.wikipedia.org/w/api.php?" + q, timeout=20).get("query") or {}).get("pages") or []
            txt = (pg[0].get("extract") or "") if pg else ""
            if len(txt) > 300: return f"{lang}:{t}", txt[:4000]
        except Exception:
            time.sleep(1.5)
    return "", ""


def main():
    dry = "--dry" in sys.argv
    doc = BR.rj(OUT, None) or {"byId": {}}
    top = BR.http_json(TOP, timeout=30); cols = top["cols"]
    rows = [dict(zip(cols, r)) for r in top["rows"]]
    todo = [b for b in rows if b["id"] not in HAND and b["id"] not in doc["byId"]][:int(os.environ.get("BOOK_N") or 100)]
    BR.log(f"추천 많은 책 {len(rows)}권 · 이번에 {len(todo)}권")
    if not todo: return 0
    if os.environ.get("BOOK_FAST"): os.environ["CLAUDE_NO_DAILY"] = "1"
    W = {}

    def prompt_of(batch):
        bl = []
        for b in batch:
            wt, w = wiki(b["t"], b.get("a", "")); W[b["id"]] = wt
            bl.append(f"■ id={b['id']} · 『{b['t']}』 · {b.get('a', '')} · 분야 {b.get('f', '')}" + (f"\n[위키백과 {wt}]\n{w}" if w else "\n[위키백과 없음 — 확실히 아는 것만]"))
        return PROMPT.format(items="\n\n".join(bl))
    batches = [todo[i:i + PER] for i in range(0, len(todo), PER)]
    if dry: p = prompt_of(batches[0]); BR.log(p[:2500]); BR.log(f"… {len(p):,}자"); return 0
    if not os.environ.get("ANTHROPIC_API_KEY"): BR.log("Claude 열쇠 없음"); return 0

    def one(b): return BR.claude(prompt_of(b), "claude-sonnet-5-5", 16000), b
    got = 0
    with ThreadPoolExecutor(3) as ex:
        for f in as_completed([ex.submit(one, b) for b in batches]):
            (res, err), b = f.result()
            if not res: BR.log(f"Claude: {err}"); continue
            ids = {x["id"] for x in b}
            try:
                for it in BR.parse_json(res[0]).get("books") or []:
                    body = [str(x)[:700] for x in it.get("body") or [] if len(str(x)) > 60]
                    if it.get("id") in ids and it.get("one") and len(body) >= 3:
                        doc["byId"][it["id"]] = {"one": str(it["one"])[:120], "body": body, "start": str(it.get("start") or "")[:300],
                                                 "q": [str(x)[:160] for x in it.get("q") or []][:3], "wiki": W.get(it["id"], ""), "api": 1}
                        got += 1
            except Exception as e:
                BR.log(f"답을 못 읽음 ({e})")
            doc["at"] = datetime.now(BR.KST).isoformat(timespec="minutes")
            OUT.parent.mkdir(parents=True, exist_ok=True); BR.wj(OUT, doc)
    BR.log(f"새로 {got}권 · 모두 {len(doc['byId'])}권")
    return 0


if __name__ == "__main__":
    sys.exit(main())
