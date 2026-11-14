#!/usr/bin/env python3
"""도구 자세한 설명 로봇 — 설명이 짧은 GitHub 저장소·HN·HF 항목에 '무엇인가·누구에게·써 보는 법·조심할 점'을 붙임.

 GitHub 은 README 앞부분(약 2,500자)을 읽어서 AI 에게 함께 줌 → 지어내지 않게.
 결과: data/tools/explain.json  { id: {what, who, how, care, at, by} }  (30일 지난 것은 정리)
 한 번에 최대 20개. 이미 설명한 것은 건너뜀. 무료 AI(Gemini → Groq), 열쇠 없으면 아무것도 안 함.
   시험:  python robot/tools_explain.py --dry
"""
from __future__ import annotations
import json, os, re, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR  # noqa: E402

D = BR.ROOT / "data" / "tools"
OUT = D / "explain.json"
MAX = 12

PROMPT = """너는 개발자가 아닌 직장인에게 새 AI 도구·오픈소스를 소개하는 한국어 편집자야.
아래 [항목]마다 쉬운 해요체로 설명을 써 줘. 사실은 주어진 설명·README 에 있는 것만 쓰고, 모르면 "README 에 안 나와요"라고 써. 지어내지 마.

항목마다
- id: 그대로
- what: 2~3문장. 이게 무엇이고 무엇을 해 주나. 영어 용어는 풀어 써.
- who: 1문장. 누구에게 쓸모 있나 (예: 회의록을 자주 쓰는 사람).
- how: 1~2문장. 어떻게 써 보나 (웹에서 바로 / 앱 설치 / 개발 도구가 필요함 등). 설치가 어려우면 그렇다고 솔직히.
- care: 1문장. 조심할 점 (아직 시험판, 영어만, 개인정보 등). 없으면 빈 글자.

답은 JSON 하나만: {{"items":[…]}}

[항목]
{rows}
"""


def readme(owner, repo):
    for br in ("main", "master"):
        for fn in ("README.md", "readme.md", "README.MD"):
            try:
                req = urllib.request.Request(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{fn}", headers={"User-Agent": "vfm-tools"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    t = r.read(60000).decode("utf-8", "ignore")
                t = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)|```.*?```", " ", t, flags=re.S)
                t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
                return re.sub(r"\s+", " ", t).strip()[:1500]
            except Exception:
                continue
    return ""


def main():
    dry = "--dry" in sys.argv
    old = BR.rj(OUT, {}) or {}
    cut = (datetime.now(BR.KST) - timedelta(days=30)).isoformat()
    old = {k: v for k, v in old.items() if v.get("at", "") >= cut}
    days = sorted(p for p in (D / "days").glob("20*.json") if "_more" not in p.name)[-2:]
    pool = []
    for p in reversed(days):
        for x in (BR.rj(p, {}) or {}).get("items") or []:
            s = x.get("ksum") or x.get("sum") or ""
            if x["id"] in old or x.get("sec") not in ("gh", "hn", "hf", "ph") or len(s) >= 90: continue
            if any(y["id"] == x["id"] for y in pool): continue
            pool.append(x)
    pool.sort(key=lambda x: -(x.get("gain") or x.get("stars") or x.get("score") or 0))
    pool = pool[:MAX]
    if not pool: BR.log("설명할 새 항목이 없어요"); return 0
    rd = {}
    for x in pool:
        m = re.match(r"https://github\.com/([^/]+)/([^/#?]+)", x.get("url", ""))
        rd[x["id"]] = readme(m.group(1), m.group(2)) if m else ""

    def make(items, rl):   # Gemini 는 넉넉히, Groq 는 분당 8천 토큰 한도라 작게
        return PROMPT.format(rows="\n".join(
            f"id={x['id']} | 이름={x.get('owner', '') + '/' if x.get('owner') else ''}{x.get('title', '')} | 설명={x.get('sum', '')} | 언어={x.get('lang', '')} | 주소={x.get('url', '')}"
            + (f"\n  README: {rd[x['id']][:rl]}" if rd[x["id"]] else "") for x in items))
    prompt = make(pool, 1500)
    BR.log(f"설명할 항목 {len(pool)}개 · AI 에게 보낼 글 {len(prompt):,}자")
    if dry: BR.log(prompt[:3000]); return 0
    if not BR.any_key():
        BR.log("무료 AI 열쇠가 없어요 → 그대로 둬요"); return 0
    ids = {x["id"] for x in pool}
    S = lambda v, n: re.sub(r"\s+", " ", str(v or "")).strip()[:n]
    now = datetime.now(BR.KST).isoformat(timespec="minutes")
    for name, fn, pr in (("Claude", BR.ai_chain(True)[0][1], prompt), ("Gemini", BR.gemini, prompt), ("Groq", BR.groq, make(pool[:4], 500))):
        res, err = fn(pr)
        if not res: BR.log(f"{name}: {err}"); continue
        try:
            n = 0
            for it in BR.parse_json(res[0]).get("items") or []:
                if it.get("id") in ids and it.get("what"):
                    old[it["id"]] = {"what": S(it["what"], 360), "who": S(it.get("who"), 180), "how": S(it.get("how"), 260), "care": S(it.get("care"), 180), "at": now, "by": res[1].split(":")[0]}
                    n += 1
            if n: BR.log(f"{name}: {n}개 설명"); break
        except Exception as e:
            BR.log(f"{name}: 답을 못 읽음 ({e})")
    OUT.write_text(json.dumps(old, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
