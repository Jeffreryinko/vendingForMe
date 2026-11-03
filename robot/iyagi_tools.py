"""iyagi_tools.py — 이야기 작가 로봇(클로드 예약 작업)이 쓰는 도구.

  python robot/iyagi_tools.py todo [N]        아직 안 쓴 목록(카탈로그) 항목을 N개 골라 JSON으로 출력 (대명사급 우선, 서가 고루)
  python robot/iyagi_tools.py add <파일.json>  새 이야기(1편 또는 배열)를 검사해 data/iyagi/stories/_index.json 에 추가
  python robot/iyagi_tools.py stats           현재 장서 수
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "iyagi/index.html"
INDEX = ROOT / "data/iyagi/stories/_index.json"
META = ROOT / "data/iyagi/_meta.json"
GROUPS = ["신화와 전승", "소설과 창작", "사람의 생애", "창작과 도전", "웃음과 말", "역사와 사건", "생활과 문화"]
REQUIRED = ["id", "title", "orig", "group", "kind", "region", "era", "basis", "form", "mood", "tags", "hook", "depths", "sources"]


def norm(t: str) -> str:
    return re.sub(r"[\s·・,.:;'\"“”‘’()（）\[\]「」『』〈〉《》\-–—]", "", str(t or "")).lower()


def catalog():
    h = HTML.read_text(encoding="utf-8")
    i = h.find("const CAT_RAW=[")
    j = h.find("];", i)
    rows = json.loads("[" + h[i + len("const CAT_RAW=["):j].strip().rstrip(",") + "]")
    out = []
    for n, r in enumerate(rows):
        o, g, rg, era, *sh = (r + "|").split("|")
        out.append({"catId": f"c{n}", "orig": o, "group": GROUPS[int(g)] if g.isdigit() else GROUPS[0], "region": rg, "era": era, "shelf": (sh[0] if sh else "")})
    return out


def stories():
    return json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []


def written_keys(st):
    return {s.get("catId") for s in st if s.get("catId")} | {norm(s.get("orig")) for s in st} | {norm(s.get("title")) for s in st}


def cmd_todo(n=5):
    st = stories(); have = written_keys(st)
    cands = [c for c in catalog() if c["catId"] not in have and norm(c["orig"]) not in have]
    # 앞쪽(더 유명한 것)일수록 가중치, 서가가 겹치지 않게
    random.seed(int(time.time() // 86400))
    picked, used_shelf = [], set()
    pool = sorted(cands, key=lambda c: int(c["catId"][1:]) + random.randint(0, 120))
    for c in pool:
        if c["shelf"] in used_shelf and len(picked) < n - 1:
            continue
        picked.append(c); used_shelf.add(c["shelf"])
        if len(picked) >= n: break
    print(json.dumps(picked, ensure_ascii=False, indent=1))


def validate(s: dict):
    miss = [k for k in REQUIRED if k not in s]
    assert not miss, f"빠진 항목: {miss}"
    assert s["group"] in GROUPS, f"group 은 {GROUPS} 중 하나"
    assert isinstance(s["depths"], dict) and "d1" in s["depths"], "depths.d1 필요"
    for k, d in s["depths"].items():
        assert isinstance(d.get("body"), list) and d["body"], f"depths.{k}.body 는 문단 배열"
    assert isinstance(s["sources"], list) and s["sources"], "sources 필요 (위키백과 등 실제 문서)"
    assert "AI" in (s.get("form") or "") or s.get("robot"), "form 에 재화 주체(AI) 표시 또는 robot=true"


def cmd_add(path: str):
    new = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(new, dict): new = [new]
    st = stories(); have = written_keys(st); ids = {s["id"] for s in st}
    added = 0
    for s in new:
        validate(s)
        if s["id"] in ids or norm(s["orig"]) in have or (s.get("catId") and s["catId"] in have):
            print("이미 있음, 건너뜀:", s["orig"]); continue
        s.setdefault("at", str(int(time.time() * 1000)))
        s.setdefault("robot", True); s.setdefault("web", True); s.setdefault("lane", "web")
        s.setdefault("spoiler", False)
        st.insert(0, s); ids.add(s["id"]); added += 1
    INDEX.write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    META.write_text(json.dumps({"updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S+09:00", time.localtime()), "stories": len(st), "by": "author-robot"}, ensure_ascii=False), encoding="utf-8")
    print(f"추가 {added}편 → 총 {len(st)}편")


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if c == "todo": cmd_todo(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    elif c == "add": cmd_add(sys.argv[2])
    else:
        st = stories(); print(f"장서 {len(st)}편, 목록(카탈로그) {len(catalog())}개, 아직 안 쓴 것 {len(catalog()) - len([s for s in st if s.get('catId')])}개")
