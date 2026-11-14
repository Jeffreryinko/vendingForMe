"""brain_cases.py — 뇌 탭 '유명한 실험·사례' 카드를 Claude(API)가 목록(brain_topics.py)에서 차례로 써요.

· 주제마다 영어 위키백과 본문을 먼저 가져와 근거로 줘요(없으면 Claude가 아는 것만, 불확실하면 쓰지 않게).
· 한 번에 주제 5개씩, 한 실행에 BRAIN_N(기본 40)개. 이미 쓴 것은 건너뜀 → 목록이 끝날 때까지 날마다 채움.
· 결과: data/brain/exp_ai.json  { v, at, items:[{id,title,book,ch,who,field,rs,ref,story,insight,wiki,by}] }
  → vfm-story 뇌 탭이 손으로 쓴 44장 뒤에 붙여 보여 줘요.
· 돈: briefing.claude() 의 주기 한도·하루 몫을 그대로 따라요. 하루 몫이 차면 그날은 멈춤(무료 AI 로는 쓰지 않음 — 품질 때문).

  python robot/brain_cases.py            # 보통
  python robot/brain_cases.py --dry      # 보낼 글만 보기
"""
from __future__ import annotations

import json, os, re, sys, time, urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR
from brain_topics import T

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/brain/exp_ai.json"
N = int(os.environ.get("BRAIN_N") or 40)
PER = 5
RS = "frontal parietal temporal occipital hippocampus amygdala thalamus hypothalamus cerebellum midbrain pons medulla cortex limbic basal brainstem prefrontal dlpfc vmpfc ofc motor sma broca somato spl ipl angular precuneus auditory wernicke fusiform parahipp temporalpole v1 insula acc pcc caudate putamen pallidus accumbens sn vta lc raphe pituitary pineal cc fornix ventricle whitematter".split()

PROMPT = """너는 한국 독자를 위한 뇌과학·심리학 잡지의 수석 기자예요. 아래 주제마다 카드 한 장씩을 써요.
읽는 사람은 전공자가 아니고 집중이 쉽게 흩어져요. 첫 문장부터 장면이 그려지게, 쉬운 해요체로, 짧은 문장으로 써요.

규칙
- 사실(사람 이름·연도·숫자·결과)은 주어진 위키백과 글과 네가 확실히 아는 것만 써요. 불확실한 숫자는 빼거나 '약'을 붙여요. 지어내지 마요.
- story: 문단 4~6개를 빈 줄(\\n\\n)로 나눠요. 장면/배경 → 무엇을 했나(방법) → 무엇이 나왔나(결과, 숫자 하나 이상) → 왜 중요한가.
  마지막 문단은 반드시 '요즘 평가: '로 시작해, 재현 여부·반론·윤리 문제·과장된 부분을 솔직히 적어요(없으면 지금 어디에 쓰이는지).
- 전체 story 는 700~1,200자.
- title: 호기심이 생기는 한 줄(40자 안쪽). 예: '쥐가 스스로 버튼을 7천 번 누른 이유'
- book: 실험이면 '유명한 실험', 특정 환자·사람·사건이면 '유명한 사례'
- who: 연구자/주인공과 연도·장소 (예: '월터 미셸 (1972, 스탠퍼드 대학교)')
- field: 분야 한 낱말 (인지심리학, 신경과학, 사회심리학 …)
- rs: 관련 뇌 부위 0~3개, 반드시 이 목록에서만: {rs}
- ref: 대표 논문 '저자 (연도), 학술지 권' — 확실할 때만. 모르면 빈 문자열.
- insight: 한두 문장. 일상에 가져갈 한 줄.

JSON 하나만:
{{"items":[{{"id":"...","title":"...","book":"...","who":"...","field":"...","rs":[],"ref":"","story":"...","insight":"..."}}]}}

주제:
{items}"""


def wiki(title):
    if not title: return ""
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": title, "format": "json", "formatversion": 2})
    try:
        r = BR.http_json("https://en.wikipedia.org/w/api.php?" + q, timeout=30)
        pg = (r.get("query") or {}).get("pages") or []
        txt = (pg[0].get("extract") or "") if pg else ""
        txt = re.split(r"\n== (See also|References|Notes|Further reading|External links) ==", txt)[0]
        return re.sub(r"\n{3,}", "\n\n", txt).strip()[:5000]
    except Exception as e:
        BR.log(f"  위키 실패 {title}: {e}"); return ""


def main():
    dry = "--dry" in sys.argv
    doc = BR.rj(OUT, None) or {"v": 1, "items": []}
    have = {x["id"] for x in doc["items"]}
    todo = [(f"a{i + 1:03d}", ch, name, wt) for i, (ch, name, wt) in enumerate(T) if f"a{i + 1:03d}" not in have][:N]
    BR.log(f"목록 {len(T)}개 중 쓴 것 {len(have)}개 · 이번에 {len(todo)}개")
    if not todo: return 0
    if not dry and not os.environ.get("ANTHROPIC_API_KEY"): BR.log("Claude 열쇠가 없어요 → 멈춤"); return 0
    def one(batch):
        blocks = []
        for id_, ch, name, wt in batch:
            w = wiki(wt)
            blocks.append(f"■ id={id_} · 갈래: {ch} · 주제: {name}" + (f"\n[위키백과 '{wt}' 발췌]\n{w}" if w else "\n[위키백과 없음 — 확실히 아는 것만]"))
        prompt = PROMPT.format(rs=", ".join(RS), items="\n\n".join(blocks))
        if dry: return prompt, None, batch
        res, err = BR.claude(prompt, os.environ.get("BRAIN_MODEL") or "claude-sonnet-5-5", 16000)
        return res, err, batch

    batches = [todo[b:b + PER] for b in range(0, len(todo), PER)]
    if dry:
        p, _, _ = one(batches[0]); BR.log(p[:3000]); BR.log(f"… {len(p):,}자"); return 0
    got, stop = 0, False
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(int(os.environ.get("BRAIN_PAR") or 4)) as ex:
        futs = [ex.submit(one, b) for b in batches]
        for f in as_completed(futs):
            res, err, batch = f.result()
            if not res:
                BR.log(f"Claude: {err}")
                if "한도" in str(err) or "몫" in str(err): stop = True
                continue
            try:
                meta = {x[0]: x for x in batch}
                for it in BR.parse_json(res[0]).get("items") or []:
                    m = meta.get(it.get("id"))
                    st = str(it.get("story") or "").strip()
                    if not m or not it.get("title") or len(st) < 300 or any(x["id"] == m[0] for x in doc["items"]): continue
                    doc["items"].append({"id": m[0], "title": str(it["title"])[:80], "book": it.get("book") if it.get("book") in ("유명한 실험", "유명한 사례") else "유명한 실험",
                                         "ch": m[1], "who": str(it.get("who") or "")[:120], "field": str(it.get("field") or "")[:30],
                                         "rs": [r for r in (it.get("rs") or []) if r in RS][:3], "ref": str(it.get("ref") or "")[:200],
                                         "story": st[:2400], "insight": str(it.get("insight") or "")[:300], "wiki": m[3], "by": res[1].split(":")[-1]})
                    got += 1
            except Exception as e:
                BR.log(f"답을 못 읽음 ({e}) → 건너뜀")
            doc["at"] = datetime.now(BR.KST).isoformat(timespec="minutes")
            doc["items"].sort(key=lambda x: x["id"])
            BR.wj(OUT, doc)                               # 묶음마다 저장
            if stop: [x.cancel() for x in futs]
    BR.log(f"새로 {got}장 · 모두 {len(doc['items'])}장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
