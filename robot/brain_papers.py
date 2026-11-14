"""brain_papers.py — 뇌 탭 '논문으로 읽기': 유명한·화제가 된 논문을 Claude(API)가 쉬운 카드로.
근거: OpenAlex(무료 논문 DB)에서 제목으로 찾은 초록·학술지·연도·인용 수·DOI.  목록: brain_papers_list.py
결과: data/brain/papers_ai.json { at, items:[{id,title,book:'논문으로 읽기',ch,who,field,rs,ref,doi,cites,story,insight}] }
  python robot/brain_papers.py [--dry]     환경: PAPER_N(기본 40) · PAPER_FAST=1 (하루 몫 무시, 주기 한도는 지킴)
"""
from __future__ import annotations

import json, os, re, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR
from brain_cases import RS
from brain_papers_list import P

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/brain/papers_ai.json"
PER = 4

PROMPT = """너는 논문을 일반 독자에게 풀어 주는 과학 기자예요. 아래 논문마다 카드 한 장을 써요.
독자는 전공자가 아니고 집중이 쉽게 흩어져요. 쉬운 해요체, 짧은 문장. 전문 용어는 처음 나올 때 괄호로 풀어요.

규칙
- 사실은 주어진 초록·서지 정보와 네가 확실히 아는 것만. 숫자(표본 수·효과 크기·%)는 초록에 있거나 확실할 때만. 지어내지 마요.
- story: 문단 5개를 빈 줄(\\n\\n)로. ① 무엇을 물었나(일상 장면으로 시작) ② 어떻게 했나(실험 방법) ③ 무엇을 찾았나(숫자 하나 이상) ④ 왜 중요한가(뒤의 연구·생활에 준 영향) ⑤ '요즘 평가: '로 시작 — 재현 여부·반론·한계를 솔직히.
- 전체 700~1,100자. 문장 안 큰따옴표 대신 ‘ ’.
- title: 호기심이 생기는 한 줄(40자 안쪽). who: '저자 (연도, 학술지)'. field: 분야 한 낱말.
- rs: 관련 뇌 부위 0~3개, 이 목록에서만: {rs}
- insight: 한두 문장, 생활에 가져갈 한 줄.

JSON 하나만: {{"items":[{{"id":"...","title":"","who":"","field":"","rs":[],"story":"","insight":""}}]}}

논문:
{items}"""


def openalex(title):
    q = urllib.parse.urlencode({"search": title, "per-page": 1, "mailto": "robot@users.noreply.github.com"})
    for _ in range(2):
        try:
            r = BR.http_json("https://api.openalex.org/works?" + q, timeout=30)
            w = (r.get("results") or [None])[0]
            if not w: return {}
            inv = w.get("abstract_inverted_index") or {}
            pos = sorted((p, word) for word, ps in inv.items() for p in ps)
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            au = [a["author"]["display_name"] for a in (w.get("authorships") or [])[:4] if a.get("author")]
            return {"t": w.get("title") or "", "y": w.get("publication_year"), "j": src, "au": au, "doi": w.get("doi") or "",
                    "cites": w.get("cited_by_count") or 0, "abs": " ".join(x for _, x in pos)[:3500]}
        except Exception as e:
            BR.log(f"  OpenAlex 실패 {title[:40]}: {e}"); time.sleep(2)
    return {}


def main():
    dry = "--dry" in sys.argv
    doc = BR.rj(OUT, None) or {"items": []}
    have = {x["id"] for x in doc["items"]}
    todo = [(f"p{i + 1:03d}", ch, t, hint) for i, (ch, t, hint) in enumerate(P) if f"p{i + 1:03d}" not in have][:int(os.environ.get("PAPER_N") or 40)]
    BR.log(f"논문 {len(P)}편 · 쓴 것 {len(have)} · 이번에 {len(todo)}")
    if not todo: return 0
    if os.environ.get("PAPER_FAST"): os.environ["CLAUDE_NO_DAILY"] = "1"
    META = {}

    def prompt_of(batch):
        blocks = []
        for id_, ch, t, hint in batch:
            m = openalex(t); time.sleep(0.5); META[id_] = m
            ok = m and m.get("t") and (t.lower()[:25] in m["t"].lower() or m["t"].lower()[:25] in t.lower())
            blocks.append(f"■ id={id_} · 갈래: {ch}\n제목: {t}\n알려진 서지: {hint}" + (
                f"\n[OpenAlex] {m['t']} · {', '.join(m['au'])} · {m['y']} · {m['j']} · 인용 {m['cites']}회\n초록: {m['abs'] or '(초록 없음)'}" if ok else "\n[OpenAlex에서 못 찾음 — 확실히 아는 것만]"))
            if not ok: META[id_] = {}
        return PROMPT.format(rs=", ".join(RS), items="\n\n".join(blocks))
    batches = [todo[i:i + PER] for i in range(0, len(todo), PER)]
    if dry: p = prompt_of(batches[0]); BR.log(p[:3000]); BR.log(f"… {len(p):,}자"); return 0
    if not os.environ.get("ANTHROPIC_API_KEY"): BR.log("Claude 열쇠 없음"); return 0

    def one(b):
        p = prompt_of(b)
        return BR.claude(p, os.environ.get("PAPER_MODEL") or "claude-sonnet-5-5", 16000), b
    got = 0
    with ThreadPoolExecutor(3) as ex:
        for f in as_completed([ex.submit(one, b) for b in batches]):
            (res, err), b = f.result()
            if not res: BR.log(f"Claude: {err}"); continue
            meta = {x[0]: x for x in b}
            try:
                for it in BR.parse_json(res[0]).get("items") or []:
                    m = meta.get(it.get("id")); st = str(it.get("story") or "").strip()
                    if not m or not it.get("title") or len(st) < 300 or any(x["id"] == m[0] for x in doc["items"]): continue
                    om = META.get(m[0]) or {}
                    ref = (", ".join(om.get("au", [])[:3]) + (" 외" if len(om.get("au", [])) > 3 else "") + f" ({om.get('y')}), {om.get('j')}") if om.get("t") else m[3]
                    doc["items"].append({"id": m[0], "title": str(it["title"])[:80], "book": "논문으로 읽기", "ch": m[1], "who": str(it.get("who") or m[3])[:140],
                                         "field": str(it.get("field") or "")[:30], "rs": [r for r in it.get("rs") or [] if r in RS][:3], "ref": ref[:220], "paper": m[2],
                                         "doi": om.get("doi", ""), "cites": om.get("cites", 0), "story": st[:2400], "insight": str(it.get("insight") or "")[:300], "api": 1})
                    got += 1
            except Exception as e:
                BR.log(f"답을 못 읽음 ({e})")
            doc["at"] = datetime.now(BR.KST).isoformat(timespec="minutes"); doc["items"].sort(key=lambda x: x["id"])
            BR.wj(OUT, doc)
    BR.log(f"새로 {got}편 · 모두 {len(doc['items'])}편")
    return 0


if __name__ == "__main__":
    sys.exit(main())
