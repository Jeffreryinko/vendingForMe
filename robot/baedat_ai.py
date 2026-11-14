"""baedat_ai.py — 배댓 고르기·맥락 한 줄 (매일, baedat_daily.py 다음에)

창고(raw-YYYY-MM.json 웃긴 배댓 · talk-YYYY-MM.json 댓글 맛집)에 새로 들어온 영상을 AI 에게 보여 주고
  · 영상마다 '맥락 한 줄' (무슨 영상이고 댓글이 왜 웃긴지/무슨 이야기인지, 해요체 50자 안쪽)
  · 영상 재미 점수 s (1~5) — 화면이 '오늘의 배댓' 순서를 정할 때 씀
  · 댓글마다 점수 s (0~5, 0 = 비하·혐오라 숨김) + 필요한 것만 '드립 풀이' why
를 받아 data/baedat/ai.json 에 적어요. 창고 파일은 건드리지 않아요(로봇이 14일째 다시 받을 때 지워지지 않게 따로 둠).

AI: Claude(Sonnet, 한 주기 한도 안에서) → 안 되면 무료 Gemini → Groq.  한 번에 영상 40개씩, 하루 최대 MAXB 묶음.
  python robot/baedat_ai.py            # 보통
  python robot/baedat_ai.py --dry      # 보낼 글만 보기
"""
from __future__ import annotations

import glob, json, re, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/baedat"
AIF = OUT / "ai.json"
PER, MAXB = 40, 3

PROMPT = """너는 한국 유튜브 댓글 문화를 잘 아는 편집자예요. 아래는 영상마다 인기 댓글을 모은 거예요.
영상마다 답을 주세요.

1) line: '맥락 한 줄'. 이 영상이 무슨 내용이고 댓글들이 무엇에 반응하는지, 처음 보는 사람이 바로 이해하게 해요체 한 문장(50자 안쪽).
   제목·댓글에 있는 것만 써요. 모르면 지어내지 말고 제목을 쉽게 풀어 써요.
2) s: 이 영상 댓글 묶음의 재미 (1~5). 5 = 기발한 드립·찰떡 비유·모두 공감할 상황, 3 = 무난, 1 = 응원·홍보·뻔함.
   댓글 맛집(kind=talk)은 '이야기가 재밌고 알찬지'로 매겨요.
3) c: 댓글마다 {{"id", "s", "why"}}.
   s: 0~5. 비하·혐오·특정인 조롱·선정적이면 0(숨김). 웃기거나 알차면 높게.
   why: 드립·말장난·밈·배경을 몰라서 이해 못 할 만한 댓글만 짧게 풀어 줘요(40자 안쪽). 바로 이해되면 빈 문자열.

JSON 하나만:
{{"v":[{{"id":"영상id","line":"...","s":4,"c":[{{"id":"댓글id","s":5,"why":""}}]}}]}}

영상 목록:
{items}"""


def S(v, n): return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def months():
    now = datetime.now(BR.KST)
    m0 = now.strftime("%Y-%m")
    y, m = now.year, now.month - 1 or 12
    if now.month == 1: y -= 1
    return [m0, f"{y}-{m:02d}"]


def todo(ai):
    out = []
    for M in months():
        for kind in ("raw", "talk"):
            d = BR.rj(OUT / f"{kind}-{M}.json", None)
            if not d: continue
            by = {}
            for c in d.get("comments") or []: by.setdefault(c[0], []).append(c)
            for vid, v in (d.get("videos") or {}).items():
                if vid in ai["v"] or vid not in by: continue
                out.append({"id": vid, "kind": kind, "pub": v[2], "v": v, "cs": by[vid][:5]})
    out.sort(key=lambda x: x["pub"], reverse=True)          # 새 영상 먼저
    return out


def block(x):
    v = x["v"]
    lines = [f"■ id={x['id']} kind={x['kind']} | 제목: {S(v[0], 90)} | 채널: {S(v[1], 30)} | 분야: {v[4]}"]
    for c in x["cs"]:
        rep = (c[6][0][0] if len(c) > 6 and c[6] else "")
        lines.append(f"  - {c[1]} (좋아요 {c[3]}): {S(c[2], 220)}" + (f"  ↳ {S(rep, 80)}" if rep else ""))
    return "\n".join(lines)


def main():
    dry = "--dry" in sys.argv
    ai = BR.rj(AIF, None) or {"v": {}, "c": {}}
    ai.setdefault("v", {}); ai.setdefault("c", {})
    q = todo(ai)
    BR.log(f"AI 를 기다리는 영상 {len(q)}개")
    if not q: return 0
    if not dry and not BR.any_key(): BR.log("AI 열쇠가 없어요 → 그대로 둬요"); return 0
    chain = (("Claude", lambda p: BR.claude(p, "claude-sonnet-5-5", 12000)), ("Gemini", BR.gemini), ("Groq", BR.groq))
    done = 0
    for b in range(MAXB):
        batch = q[b * PER:(b + 1) * PER]
        if not batch: break
        prompt = PROMPT.format(items="\n\n".join(block(x) for x in batch))
        if dry: BR.log(prompt[:3000]); BR.log(f"… {len(prompt):,}자"); return 0
        ids = {x["id"]: x for x in batch}
        got = 0
        for name, fn in chain:
            res, err = fn(prompt)
            if not res: BR.log(f"{name}: {err}"); continue
            try:
                for it in BR.parse_json(res[0]).get("v") or []:
                    x = ids.get(it.get("id"))
                    if not x or not it.get("line"): continue
                    try: s = max(1, min(5, int(it.get("s") or 3)))
                    except Exception: s = 3
                    ai["v"][x["id"]] = {"l": S(it["line"], 80), "s": s, "by": res[1].split(":")[0]}
                    cids = {c[1] for c in x["cs"]}
                    for c in it.get("c") or []:
                        if c.get("id") not in cids: continue
                        try: cs = max(0, min(5, int(c.get("s"))))
                        except Exception: continue
                        ai["c"][c["id"]] = {"s": cs, **({"w": S(c.get("why"), 60)} if S(c.get("why"), 60) else {})}
                    got += 1
                if got: BR.log(f"{name}: 영상 {got}개 맥락·점수"); break
            except Exception as e:
                BR.log(f"{name}: 답을 못 읽음 ({e})")
        done += got
        if not got: break
    # 창고에서 빠진 지 오래된 영상은 정리 (두 달 전 것까지만 남김 — 파일이 커지지 않게)
    keep = set()
    for p in glob.glob(str(OUT / "raw-*.json")) + glob.glob(str(OUT / "talk-*.json")):
        d = BR.rj(Path(p), {}) or {}
        keep |= set((d.get("videos") or {}).keys()); keep |= {c[1] for c in d.get("comments") or []}
    ai["v"] = {k: v for k, v in ai["v"].items() if k in keep}
    ai["c"] = {k: v for k, v in ai["c"].items() if k in keep}
    ai["at"] = datetime.now(BR.KST).isoformat(timespec="minutes")
    AIF.write_text(json.dumps(ai, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    BR.log(f"저장: 영상 {done}개 새로 · 모두 영상 {len(ai['v'])} · 댓글 {len(ai['c'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
