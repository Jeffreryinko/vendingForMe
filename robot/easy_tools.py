"""easy_tools.py — "쉬운 풀이"(AI 논문)와 사용자 요청함을 다루는 도구. 루틴(편집장·작가)이 씀. 토큰 0.

  python robot/easy_tools.py todo [N]          오늘 풀이할 논문 N편(기본 3): 요청 먼저, 그다음 HF 추천 ▲ 많은 순 (아직 풀이 없는 것)
  python robot/easy_tools.py add <파일.json>   풀이(1편 또는 배열)를 검사해 data/ai/easy/<id>.json 으로 저장, 목록 갱신, 요청 완료 표시
  python robot/easy_tools.py requests [앱]      요청함 보기 (ai / iyagi)
  python robot/easy_tools.py done <앱> <id>     요청 하나를 완료로 표시 (이야기 작가가 쓴 뒤)

풀이 한 편의 모양 (초등학생도 알 수 있게):
  {"id":"2611.00859", "title":"<쉬운 한국어 제목>", "one":"<한 문장 요약>",
   "analogy":"<쉬운 비유 2~4문장>",
   "must":["<꼭 알아야 할 것 1>", "<2>", "<3>"],
   "terms":[{"t":"<용어>", "en":"<영어>", "d":"<초등학생용 한 줄 뜻>"}],      # 3~5개
   "why":"<왜 중요한지 2~3문장>", "limit":"<논문에서 확인 안 되는 점/조심할 점 한 줄 또는 빈칸>"}
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EASY = ROOT / "data/ai/easy"
REQ = ROOT / "data/requests.json"
KST = timezone(timedelta(hours=9))
REQUIRED = ["id", "title", "one", "analogy", "must", "terms", "why"]


def rj(p, d):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d


def wj(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")


def requests_(app=None):
    r = rj(REQ, {"items": []})
    return [x for x in r.get("items", []) if not x.get("done") and (not app or x.get("app") == app)]


def mark_done(app, id_):
    r = rj(REQ, {"items": []}); n = 0
    for x in r.get("items", []):
        if x.get("app") == app and str(x.get("id")) == str(id_) and not x.get("done"):
            x["done"] = datetime.now(KST).isoformat(timespec="seconds"); n += 1
    if n: wj(REQ, r)
    return n


def have():
    return set(rj(EASY / "_index.json", []))


def papers_today():
    idx = rj(ROOT / "data/ai/_index.json", {})
    out = []
    for d in reversed(idx.get("days", [])[-3:]):
        out += rj(ROOT / f"data/ai/days/{d}.json", {}).get("papers", [])
    return out


def cmd_todo(n=3):
    got = have(); ps = {p["id"]: p for p in papers_today()}
    picks = []
    for r in requests_("ai"):
        if r["id"] not in got: picks.append({"id": r["id"], "why": "사용자 요청", **({"title": ps[r["id"]]["title"], "abs": ps[r["id"]].get("abs", "")} if r["id"] in ps else {"title": r.get("title", "")})})
    hf = sorted([p for p in ps.values() if p.get("src") == "hf" and p["id"] not in got], key=lambda p: -(p.get("up") or 0))
    for p in hf:
        if len(picks) >= n: break
        if any(x["id"] == p["id"] for x in picks): continue
        picks.append({"id": p["id"], "why": f"HF 추천 ▲{p.get('up', 0)}", "title": p["title"], "abs": p.get("abs", ""), "ksum": p.get("ksum", "")})
    print(json.dumps(picks, ensure_ascii=False, indent=1))


def validate(e):
    miss = [k for k in REQUIRED if not e.get(k)]
    assert not miss, f"빠진 항목: {miss}"
    assert isinstance(e["must"], list) and 2 <= len(e["must"]) <= 5, "must 는 2~5개"
    assert isinstance(e["terms"], list) and 1 <= len(e["terms"]) <= 6 and all(t.get("t") and t.get("d") for t in e["terms"]), "terms 는 1~6개, 각각 t·d"


def cmd_add(path):
    new = rj(path, None)
    if isinstance(new, dict): new = [new]
    got = have(); n = 0
    for e in new:
        validate(e)
        e.setdefault("at", datetime.now(KST).isoformat(timespec="seconds")); e.setdefault("by", "Claude 루틴 · 초록 기준")
        wj(EASY / f"{e['id']}.json", e); got.add(e["id"]); n += 1
        mark_done("ai", e["id"])
    wj(EASY / "_index.json", sorted(got))
    print(f"쉬운 풀이 {n}편 저장 · 전체 {len(got)}편")


if __name__ == "__main__":
    a = sys.argv[1:] or ["todo"]
    if a[0] == "todo": cmd_todo(int(a[1]) if len(a) > 1 else 3)
    elif a[0] == "add": cmd_add(a[1])
    elif a[0] == "requests": print(json.dumps(requests_(a[1] if len(a) > 1 else None), ensure_ascii=False, indent=1))
    elif a[0] == "done": print("완료 표시", mark_done(a[1], a[2]))
    else: print(__doc__)
