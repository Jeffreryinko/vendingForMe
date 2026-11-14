"""sisa_titles.py — 시사 이슈 제목 다듬기. 대표 기사의 기계번역 제목 대신, 이슈 전체를 담은 짧고 자연스러운 한국어 제목.
sisa_run.py 가 판을 만든 뒤 실행(3시간마다). 새 이슈(sid)만 AI 에게 보내고, 결과는 data/sisa/titles.json {sid: {t, at}} 에 쌓음.
화면(sisa/index.html)이 판을 불러올 때 이 표로 제목을 바꿔 보여 줘요(원래 제목은 이슈 화면에 그대로 남음).
AI: Claude Haiku(아주 쌈) → 무료 Gemini → Groq.
"""
from __future__ import annotations

import json, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/sisa"
OUT = D / "titles.json"
PER = 40

PROMPT = """너는 한국 신문의 편집기자야. 아래 이슈는 여러 나라 기사를 같은 사건끼리 묶은 것이고, 제목·요약은 기계번역이라 어색해.
이슈마다 '무슨 일이 일어났는지' 한눈에 알 수 있는 한국어 제목을 새로 써.
- 28자 안쪽, 신문 제목체(~해, ~했다 대신 명사형·간결체. 예: '미 전역 항공 관제 마비…4시간 만에 재개')
- 주어진 제목·요약에 있는 사실만. 숫자·이름을 지어내지 마. 확신이 없으면 원래 제목을 짧게 다듬기만.
- 따옴표는 ‘ ’만.
JSON 하나만: {{"titles":[{{"sid":"...","t":"..."}}]}}

이슈:
{items}"""


def main():
    ix = BR.rj(D / "editions/_index.json", [])
    if not ix: return 0
    eid = ix[-1].get("id") or ""
    ed = BR.rj(D / f"editions/{eid}.json", None) if eid else None
    if not ed or not ed.get("stories"):                       # _index 맨 끝이 판 전체를 담은 경우
        ed = ix[-1]
    T = BR.rj(OUT, {}) or {}
    todo = [s for s in ed.get("stories", []) if s.get("kind") != "brief" and s.get("sid") and s["sid"] not in T and s.get("title")]
    todo.sort(key=lambda s: (0 if s.get("top") else 1, -len(s.get("countries") or [])))
    todo = todo[:120]
    BR.log(f"판 {eid} · 새 이슈 {len(todo)}개")
    if not todo or not BR.any_key(): return 0
    for i in range(0, len(todo), PER):
        b = todo[i:i + PER]
        items = "\n".join(f"- sid={s['sid']} | 제목: {s['title'][:120]} | 요약: {str(s.get('sum') or '')[:160]} | 다른 나라 제목: {' / '.join(a.get('t', '')[:60] for a in (s.get('angles') or [])[:2])}" for s in b)
        for name, fn in BR.ai_chain(True):
            res, err = fn(PROMPT.format(items=items))
            if not res: BR.log(f"{name}: {err}"); continue
            try:
                n = 0
                ok = {s["sid"] for s in b}
                for x in BR.parse_json(res[0]).get("titles") or []:
                    t = str(x.get("t") or "").strip().strip('"')
                    if x.get("sid") in ok and 4 <= len(t) <= 40: T[x["sid"]] = {"t": t, "at": datetime.now(BR.KST).strftime("%m%d%H"), "by": res[1].split(":")[0]}; n += 1
                BR.log(f"{name}: {n}개"); break
            except Exception as e:
                BR.log(f"{name}: 답을 못 읽음 ({e})")
    if len(T) > 4000:                                          # 오래된 것부터 정리
        for k in sorted(T, key=lambda k: T[k].get("at", ""))[:len(T) - 4000]: T.pop(k)
    OUT.write_text(json.dumps(T, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
