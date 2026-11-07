"""reindex.py — data/sisa 의 _index.json 들을 다시 만듦 (편집장 예약 작업이 판을 고친 뒤 실행).

다시 만들기 전에 판(editions/*.json)을 점검해 고침:
  1) 이슈 id 가 겹치면(편집장이 새 이슈를 이미 있는 g번호로 만든 경우) 뒤엣것을 비어 있는 g번호로 바꿈
     → 겹치면 화면에서 이슈를 누를 때 다른 이슈가 열리고, 해설이 엉뚱한 이슈에 붙음
  2) 똑같은 해설(key)이 두 이슈에 붙어 있으면, 제목과 낱말이 더 겹치는 쪽만 남기고 나머지 이슈의 key 는 비움
     (비우면 화면은 그 이슈의 요약 sum 을 씀)
"""
import sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sisa_run import reindex

ED = Path(__file__).resolve().parent.parent / "data/sisa/editions"


def words(t): return set(re.findall(r"[가-힣A-Za-z0-9]{2,}", t or ""))


def check_edition(p):
    try: E = json.loads(p.read_text())
    except Exception: return 0
    st = E.get("stories") or []; fixed = 0
    used = {s.get("id") for s in st}
    nxt = max([int(m.group(1)) for i in used if i and (m := re.fullmatch(r"g(\d+)", i))] + [0]) + 1
    seen = set()
    for s in st:
        if s.get("id") in seen:
            while f"g{nxt}" in used: nxt += 1
            s["id"] = f"g{nxt}"; used.add(s["id"]); nxt += 1; fixed += 1
        seen.add(s["id"])
    by = {}
    for s in st:
        if s.get("key"): by.setdefault(s["key"], []).append(s)
    for k, lst in by.items():
        if len(lst) < 2: continue
        kw = words(k); best = max(lst, key=lambda s: len(kw & words(s.get("title"))))
        for s in lst:
            if s is not best: s["key"] = ""; fixed += 1
    if fixed:
        p.write_text(json.dumps(E, ensure_ascii=False, separators=(",", ":")) if "\n" not in p.read_text()[:3000] else json.dumps(E, ensure_ascii=False, indent=1))
        print(f"  {p.name}: 겹친 id·해설 {fixed}곳 고침")
    return fixed


if __name__ == "__main__":
    for p in sorted(ED.glob("20*.json"))[-12:]: check_edition(p)
    reindex(); print("reindex ok")
