"""brain_briefing.py — 뇌 탭 '새 연구 브리핑' (결정: 뇌 = 생활 심리 + 새 연구 브리핑 + 실험·사례).
vfm-story 의 뇌과학 소식(data/brain/news.json, 하루 2번 모음)에서 최근 사흘 기사를 골라 Claude(API)가 쉬운 브리핑을 써요.
기사 제목·요약에 있는 것만 씀(본문을 읽지 않으므로). 결과: data/brain/briefing.json → vfm-story 뇌 첫 화면.
AI: Claude Sonnet → 무료 Gemini → Groq.
"""
from __future__ import annotations

import json, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/brain/briefing.json"
NEWS = "https://raw.githubusercontent.com/Jeffreryinko/vfm-story/main/data/brain/news.json"

PROMPT = """너는 뇌과학·심리학 소식을 일반 독자에게 전하는 한국어 기자예요. 아래 [기사]는 최근 사흘 동안 나온 뇌·마음 관련 기사 제목이에요(외국어는 번역 전).
1. 같은 연구를 다룬 기사는 하나로 묶고, 일반인에게 흥미롭고 의미 있는 순서로 6~8개를 골라요. 광고·건강식품 홍보·연예 기사는 빼요.
2. 제목·요약에 있는 사실만 써요. 연구 결과를 부풀리지 마요('쥐 실험', '작은 연구'면 그렇게 밝혀요).
3. 쉬운 해요체.

JSON 하나만:
{{"lead":"오늘의 흐름 2문장","items":[{{"ids":["기사 id"],"t":"한국어 제목 30자 안쪽","one":"무엇을 발견했나 1~2문장","why":"생활에서 무슨 뜻인지 1문장","care":"조심해서 읽을 점 1문장(동물 실험·표본 작음·아직 초기 등, 없으면 빈 글자)"}}]}}

[기사]
{rows}"""


def main():
    d = BR.http_json(NEWS, timeout=30)
    cut = (datetime.now(BR.KST) - timedelta(days=3)).strftime("%Y-%m-%d")
    items = [x for x in d.get("items") or [] if (x.get("first") or x.get("date") or "")[:10] >= cut][:120]
    BR.log(f"뇌과학 소식 {len(d.get('items') or [])}개 중 최근 {len(items)}개")
    if len(items) < 5 or not BR.any_key(): return 0
    by = {x["id"]: x for x in items}
    rows = "\n".join(f"- id={x['id']} | {x.get('pub', '')} | {x['title'][:160]}" for x in items)
    for name, fn in BR.ai_chain():
        res, err = fn(PROMPT.format(rows=rows))
        if not res: BR.log(f"{name}: {err}"); continue
        try:
            o = BR.parse_json(res[0]); out = []
            for it in o.get("items") or []:
                ids = [i for i in it.get("ids") or [] if i in by]
                if not ids or not it.get("t"): continue
                out.append({"t": str(it["t"])[:60], "one": str(it.get("one") or "")[:300], "why": str(it.get("why") or "")[:200], "care": str(it.get("care") or "")[:200],
                            "links": [[by[i].get("pub", ""), by[i]["url"]] for i in ids][:3]})
            if len(out) >= 3 and o.get("lead"):
                BR.wj(OUT, {"at": datetime.now(BR.KST).isoformat(timespec="minutes"), "by": res[1], "lead": str(o["lead"])[:400], "items": out[:8]})
                BR.log(f"뇌 브리핑 저장 · {len(out)}건 · {res[1]}"); return 0
            BR.log(f"{name}: 쓸 만한 것이 {len(out)}건뿐")
        except Exception as e:
            BR.log(f"{name}: 답을 못 읽음 ({e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
