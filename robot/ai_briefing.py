#!/usr/bin/env python3
"""AI 브리핑 로봇 — 그날 모인 AI 소식(data/ai/feed.json)을 보고 무료 AI 가 'AI 브리핑'을 씀.

 소식마다: 무엇이 나왔나 / 왜 중요한가 / 나는 어떻게 써 보나(어디서·누가·값).
 사실은 제목·요약에 있는 것만. 모르는 건 "발표문에 안 나와요"라고 적게 함.
 AI 부르는 방법은 robot/briefing.py 와 같음 (Gemini → Groq, 열쇠 없으면 아무것도 안 바꿈).
   시험:  python robot/ai_briefing.py --dry
"""
from __future__ import annotations
import os, re, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR  # noqa: E402

D = BR.ROOT / "data" / "ai"
OUT = D / "briefing"
KINDS = {"model", "feat", "biz", "rule", "paper", "etc"}

PROMPT = """너는 한국어 'AI 브리핑' 편집자야. 아래 [소식 목록]은 오늘 모인 AI 회사 발표·AI 뉴스·인기 논문이야 (요약은 기계번역이라 어색할 수 있어).
이걸로 "{label}"을 써 줘. 읽는 사람은 개발자가 아니고, AI를 일과 생활에 잘 쓰고 싶은 직장인이야.

꼭 지킬 것
1. 같은 일을 다룬 소식은 하나로 합쳐 (ids 에 번호를 모두).
2. 실제로 써 볼 수 있는 새 기능·새 모델을 먼저, 그다음 업계 큰 소식(투자·규제·장애), 논문은 1개까지. {lo}~{hi}건.
3. 사실(이름·숫자·날짜)은 목록에 적힌 것만. 값·지역·출시일을 모르면 "발표문에 안 나와요"라고 써. 지어내지 마.
4. 말투는 쉬운 해요체. 영어 용어는 풀어 써 (예: 에이전트 → 대신 일을 해 주는 AI).

소식마다
- ids: 소식 번호들
- kind: model(새 모델) | feat(새 기능) | biz(회사·투자) | rule(규제·사건) | paper(논문) | etc
- who: 회사·기관 이름
- t: 제목 26자 안팎, 해요체
- one: 한두 문장. 무엇이 나왔나.
- why: 1~2문장. 왜 중요한가.
- how: 1~2문장. 나는 어떻게 써 보나 (어디서 켜나, 누가 쓸 수 있나, 값). 써 볼 게 없으면 빈 글자.

그리고 lead: 오늘 AI 소식의 줄기를 2~3문장으로 (lead 도 꼭 해요체, "~했습니다" 쓰지 마).
답은 JSON 하나만: {{"lead":"…","items":[…]}}

[소식 목록]  (번호 | 출처 | 제목 | 요약)
{rows}
"""


def main():
    dry = "--dry" in sys.argv
    f = BR.rj(D / "feed.json", {}) or {}
    pool = []
    for k in ("posts", "news", "papers"):
        for x in f.get(k) or []:
            pool.append({"id": x["id"], "src": x.get("name") or x.get("sid") or ("논문" if k == "papers" else ""), "t": x.get("ko") or x.get("title") or "",
                         "s": x.get("ksum") or x.get("one") or x.get("sum") or "", "url": x.get("url", ""), "date": x.get("date", ""), "k": k})
    if not pool: BR.log("AI 소식이 없어요"); return 0
    pool.sort(key=lambda x: x["date"], reverse=True)
    pool = pool[:80]
    S = lambda v, n: re.sub(r"\s+", " ", str(v or "")).strip()[:n]
    rows = [f"{x['id']} | {x['src']} | {S(x['t'], 120)} | {S(x['s'], 220)}" for x in pool]
    t = datetime.now(BR.KST)
    label = f"{t.month}월 {t.day}일 AI 브리핑"
    prompt = PROMPT.format(label=label, lo=6, hi=10, rows="\n".join(rows))
    BR.log(f"AI 소식 {len(rows)}건 · AI 에게 보낼 글 {len(prompt):,}자")
    if dry: BR.log(prompt[:2500]); return 0
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        BR.log("무료 AI 열쇠가 없어요 → AI 브리핑을 바꾸지 않아요"); return 0
    by = {x["id"]: x for x in pool}
    out = None
    for name, fn in (("Gemini", BR.gemini), ("Groq", BR.groq)):
        res, err = fn(prompt)
        if not res: BR.log(f"{name}: {err}"); continue
        try:
            o = BR.parse_json(res[0]); items, used = [], set()
            for it in o.get("items") or []:
                ii = [i for i in (it.get("ids") or []) if i in by and i not in used]
                if not ii or not it.get("t") or not it.get("one"): continue
                used.update(ii)
                items.append({"ids": ii, "kind": it.get("kind") if it.get("kind") in KINDS else "etc", "who": S(it.get("who"), 40),
                              "t": S(it.get("t"), 60), "one": S(it.get("one"), 260), "why": S(it.get("why"), 260), "how": S(it.get("how"), 260),
                              "links": [[by[i]["src"], by[i]["url"]] for i in ii if by[i]["url"]][:3]})
            if len(items) >= 4 and o.get("lead"):
                out = ({"lead": S(o["lead"], 420), "items": items[:10]}, res[1]); break
            BR.log(f"{name}: 쓸 만한 소식이 {len(items)}건뿐")
        except Exception as e:
            BR.log(f"{name}: 답을 못 읽음 ({e})")
    if not out: BR.log("AI 가 브리핑을 쓰지 못했어요 → 그대로 둬요"); return 0
    o, who = out
    doc = {"id": f"{t:%Y-%m-%d}", "label": label, "at": t.isoformat(timespec="minutes"), "by": who.split(":")[0], "model": who,
           "note": "발표문·기사 제목과 요약만 보고 AI가 썼어요. 값·지역 같은 세부는 원문을 확인하세요.", **o}
    BR.wj(OUT / "latest.json", doc); BR.wj(OUT / f"{doc['id']}.json", doc)
    for p in sorted(OUT.glob("20*.json"))[:-30]: p.unlink()
    BR.log(f"AI 브리핑 저장 · {len(o['items'])}건 · {who}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
