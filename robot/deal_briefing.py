#!/usr/bin/env python3
"""딜 브리핑 로봇 — 그날 모인 딜(data/deal/now.json)을 보고 무료 AI 가 '딜 브리핑'을 씀.

 딜마다: 누가·누구를·얼마에 / 왜 했나 / 어떤 회사인가 / 이 딜의 뜻.
 금액·당사자는 기사 제목에 있는 것만. 회사 소개와 풀이는 AI 가 아는 내용이라 화면에 '틀릴 수 있어요'라고 적음.
 딜이 아닌 글(사기 사건, 무기 구매, 모금 행사, 실적 기사)은 AI 가 빼게 함.
 AI 부르는 방법은 robot/briefing.py 와 같음 (Gemini → Groq, 열쇠 없으면 아무것도 안 바꿈).
   시험:  python robot/deal_briefing.py --dry
"""
from __future__ import annotations
import os, re, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR  # noqa: E402

D = BR.ROOT / "data" / "deal"
OUT = D / "briefing"
KINDS = {"ma", "vc", "pe", "ipo", "fund", "tie"}
STS = {"done", "talk", "plan", "fail", "rumor"}

PROMPT = """너는 한국어 '딜 브리핑' 편집자야. 아래 [딜 목록]은 오늘 모인 투자·인수합병·상장 기사 제목이야 (기계번역이라 어색하고, 금액 칸은 자주 틀려).
이걸로 "{label}"을 써 줘. 읽는 사람은 투자 전문가가 아니고, 딜이 어떻게 이뤄지는지 배우는 중이야.

꼭 지킬 것
1. **진짜 거래만** 골라: 회사를 사고파는 것, 투자 유치, 상장, 큰 제휴·공급 계약. 사기 사건, 정부의 무기 구매, 모금 행사, 실적 발표, 칼럼, 소문만 있는 글은 빼.
2. 같은 거래를 다룬 기사가 여러 개면 하나로 합쳐 (ids 에 번호를 모두).
3. 금액·당사자는 **제목에 적힌 것만**. 금액 칸(usd)이 제목과 다르면 제목을 믿어. 제목에 금액이 없으면 amt_usd 는 0.
4. 큰 거래, 한국과 관련된 거래, AI·반도체 거래를 먼저. 여러 나라를 고루. {lo}~{hi}건.
5. 말투는 쉬운 해요체. 전문 용어(시리즈A, 프리IPO, 주식 교환 등)는 풀어 써.
6. 회사 소개(co)와 '왜 했나', '이 딜의 뜻'은 네가 아는 일반 지식으로 써도 돼. 단, 잘 모르는 회사면 "~하는 회사로 알려져 있어요" 정도로만 쓰고 지어내지 마.

딜마다
- ids: 딜 번호들
- kind: ma(인수·합병) | vc(스타트업 투자) | pe(대형 투자·사모) | ipo(상장) | fund(펀드) | tie(제휴·계약)
- st: done(확정) | talk(협상 중) | plan(추진·신청) | fail(무산)
- cc: 받는 회사의 나라 두 글자
- t: 제목 28자 안팎, 해요체
- one: 한두 문장. 누가 누구를 얼마에.
- buyer: 사는 쪽·투자자 (없으면 빈 글자) / target: 팔리는 쪽·투자받는 회사
- amt_usd: 달러 금액 숫자 (원화·엔화 등은 달러로 어림), 모르면 0 / amtNote: 금액에 붙일 짧은 설명 (없으면 빈 글자)
- why: 2문장. 왜 이 거래를 했나.
- co: [["회사 이름","한 줄 소개"], …] 1~2개
- mean: 1~2문장. 이 딜에서 배울 점이나 업계에 주는 뜻.
- src: 매체 이름

그리고 lead: 오늘 딜의 줄기를 3문장으로.
답은 JSON 하나만: {{"lead":"…","items":[…]}}

[딜 목록]  (번호 | 종류 | 나라 | 금액 칸 | 제목 | 매체)
{deals}
"""


def main():
    dry = "--dry" in sys.argv
    now = BR.rj(D / "now.json", {}) or {}
    deals = now.get("deals") or []
    if not deals: BR.log("딜이 없어요"); return 0
    fx = float(((BR.rj(D / "_index.json", {}) or {}).get("fx") or {}).get("USD") or 1350)
    day = now.get("day", "")
    fresh = [d for d in deals if d.get("date", "") >= day[:8] + f"{max(1, int(day[8:10] or 1) - 1):02d}"] or deals
    fresh.sort(key=lambda d: -(d.get("usd") or 0))
    rows = [f"{d['id']} | {d.get('kind', '')} | {d.get('cc', '')} | {d.get('amtS') or ''} | {(d.get('ko') or d.get('title') or '')[:130]} | {d.get('src', '')}" for d in fresh[:90]]
    t = datetime.now(BR.KST)
    label = f"{t.month}월 {t.day}일 딜 브리핑"
    prompt = PROMPT.format(label=label, lo=8, hi=14, deals="\n".join(rows))
    BR.log(f"딜 {len(rows)}건 · AI 에게 보낼 글 {len(prompt):,}자")
    if dry: BR.log(prompt[:2500]); return 0
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        BR.log("무료 AI 열쇠가 없어요 → 딜 브리핑을 바꾸지 않아요"); return 0
    ids = {d["id"] for d in deals}
    S = lambda v, n: re.sub(r"\s+", " ", str(v or "")).strip()[:n]
    out = None
    for name, fn in (("Gemini", BR.gemini), ("Groq", BR.groq)):
        res, err = fn(prompt)
        if not res: BR.log(f"{name}: {err}"); continue
        try:
            o = BR.parse_json(res[0]); items, used = [], set()
            for it in o.get("items") or []:
                ii = [i for i in (it.get("ids") or []) if i in ids and i not in used]
                if not ii or not it.get("t") or not it.get("one"): continue
                used.update(ii)
                try: usd = float(it.get("amt_usd") or 0)
                except Exception: usd = 0
                items.append({"ids": ii, "kind": it.get("kind") if it.get("kind") in KINDS else "ma", "st": it.get("st") if it.get("st") in STS else "done",
                              "cc": S(it.get("cc"), 2).upper(), "t": S(it.get("t"), 60), "one": S(it.get("one"), 240), "buyer": S(it.get("buyer"), 60), "target": S(it.get("target"), 60),
                              "amt": round(usd * fx) if 1e5 < usd < 5e12 else 0, **({"amtNote": S(it.get("amtNote"), 60)} if it.get("amtNote") else {}),
                              "why": S(it.get("why"), 320), "co": [[S(c[0], 40), S(c[1], 140)] for c in (it.get("co") or [])[:2] if isinstance(c, list) and len(c) >= 2],
                              "mean": S(it.get("mean"), 260), "src": S(it.get("src"), 60)})
            if len(items) >= 5 and o.get("lead"):
                out = ({"lead": S(o["lead"], 420), "items": items[:14]}, res[1]); break
            BR.log(f"{name}: 쓸 만한 딜이 {len(items)}건뿐")
        except Exception as e:
            BR.log(f"{name}: 답을 못 읽음 ({e})")
    if not out: BR.log("AI 가 딜 브리핑을 쓰지 못했어요 → 그대로 둬요"); return 0
    o, who = out
    doc = {"id": f"{t:%Y-%m-%d}", "label": label, "at": t.isoformat(timespec="minutes"), "by": who.split(":")[0], "model": who,
           "note": f"금액과 당사자는 기사 제목에서, 회사 소개와 풀이는 AI가 아는 내용이라 틀릴 수 있어요. 원화는 1달러 {round(fx):,}원으로 어림했어요.", **o}
    BR.wj(OUT / "latest.json", doc); BR.wj(OUT / f"{doc['id']}.json", doc)
    for p in sorted(OUT.glob("20*.json"))[:-30]: p.unlink()
    BR.log(f"딜 브리핑 저장 · {len(o['items'])}건 · {who}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
