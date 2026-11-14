"""iyagi_claude.py — 이야기 자판기용 이야기를 Claude(API)가 위키백과를 근거로 세 단계 깊이로 써요.
목록: robot/iyagi_topics.py · 결과: data/iyagi/claude_stories.json { at, items:[이야기…] } → vfm-story iyagi 가 불러 붙임.
  python robot/iyagi_claude.py [--dry]      환경: IYAGI_N(기본 30) · IYAGI_FAST=1 이면 하루 몫 무시(주기 한도는 지킴)
"""
from __future__ import annotations

import json, os, re, sys, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR
from iyagi_topics import T

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/iyagi/claude_stories.json"
PER = 2
MOODS = ["웃긴", "따뜻한", "기묘한", "비극적인", "씁쓸한", "통쾌한", "무서운", "신비로운"]

PROMPT = """너는 한국어로 옛이야기와 고전을 다시 들려주는 이야기꾼이에요. 아래 주제마다 이야기 한 편을 써요.
독자는 어른이지만 집중이 쉽게 흩어져요. 첫 문장부터 장면이 보이게, 쉬운 '-습니다/-했어요' 대신 이야기체 '-했습니다'로, 짧은 문장으로.

규칙
- 줄거리·이름·연도는 주어진 위키백과 글과 확실히 아는 것만. 판본마다 다르면 '판본에 따라'라고 밝혀요. 지어내지 마요.
- 소설·희곡은 줄거리와 '읽는 맛'만. 원문 문장을 길게 옮기지 마요(인용은 한 문장 이하).
- depths.d1: 한눈에 — 문단 3개, 300~450자, 이야기 전체 흐름(결말 포함).
  depths.d2: 조금 자세히 — 문단 5~6개, 900~1,300자, 장면과 대사 느낌을 살려서.
  depths.d3: 깊이 읽기 — 문단 5~6개, 1,300~1,900자, 기원·판본 차이·시대 배경·뒤에 남긴 영향(작품, 말, 문화).
- min: 읽는 데 걸리는 분(d1 1, d2 3~4, d3 6~8).
- hook: 궁금해지는 두 문장. title: 원래 이름 대신 호기심이 생기는 한 줄 제목(25자 안쪽). orig: 원래 이름.
- group: {groups} 중 하나. kind: 신화·전설·민담·소설·단편소설·희곡·인물 일화·역사적 사건 등. region, era(시대·출전), basis(전승·기록·소설 등).
- mood: {moods} 중 1~2개. tags: 낱말 3~5개.
- parts: 이야기에서 나온 말·상징 2개 [{{"t","b"}}]. beyond: 생각해 볼 질문 2개 [{{"t","b"}}].
- warn: 죽음·폭력 등 주의할 장면이 있으면 한 줄, 없으면 빈 문자열.

JSON 하나만:
{{"items":[{{"id":"...","title":"","orig":"","group":"","kind":"","region":"","era":"","basis":"","mood":[],"tags":[],"hook":"",
"depths":{{"d1":{{"min":1,"body":["",""]}},"d2":{{"min":4,"body":[]}},"d3":{{"min":7,"body":[]}}}},"parts":[],"beyond":[],"warn":""}}]}}

주제:
{items}"""


def wiki(title, _again=True):
    if not title: return ""
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": title, "format": "json", "formatversion": 2})
    try:
        pg = (BR.http_json("https://en.wikipedia.org/w/api.php?" + q, timeout=30).get("query") or {}).get("pages") or []
        txt = (pg[0].get("extract") or "") if pg else ""
        txt = re.split(r"\n== (See also|References|Notes|Further reading|External links) ==", txt)[0].strip()[:6000]
        if not txt and _again: import time; time.sleep(2); return wiki(title, False)
        return txt
    except Exception:
        if _again: import time; time.sleep(2); return wiki(title, False)
        return ""


def main():
    dry = "--dry" in sys.argv
    doc = BR.rj(OUT, None) or {"items": []}
    have = {x["id"] for x in doc["items"]}
    todo = [(f"cl-{i + 1:03d}", g, n, w) for i, (g, n, w) in enumerate(T) if f"cl-{i + 1:03d}" not in have][:int(os.environ.get("IYAGI_N") or 30)]
    BR.log(f"목록 {len(T)}편 · 쓴 것 {len(have)} · 이번에 {len(todo)}")
    if not todo: return 0
    if os.environ.get("IYAGI_FAST"): os.environ["CLAUDE_NO_DAILY"] = "1"
    groups = "신화와 전승 · 사람의 생애 · 소설과 창작 · 역사와 사건 · 웃음과 말"

    def prompt_of(batch):
        return PROMPT.format(groups=groups, moods=" · ".join(MOODS), items="\n\n".join(
            f"■ id={i} · 갈래: {g} · 주제: {n}" + (f"\n[위키백과 '{w}' 발췌]\n{x}" if (x := wiki(w)) else "\n[위키백과 없음 — 확실히 아는 것만]") for i, g, n, w in batch))
    batches = [todo[i:i + PER] for i in range(0, len(todo), PER)]
    if dry: p = prompt_of(batches[0]); BR.log(p[:2000]); BR.log(f"… {len(p):,}자"); return 0
    if not os.environ.get("ANTHROPIC_API_KEY"): BR.log("Claude 열쇠 없음"); return 0

    def one(b): return BR.claude(prompt_of(b), os.environ.get("IYAGI_MODEL") or "claude-sonnet-5-5", 24000), b
    got = 0
    with ThreadPoolExecutor(4) as ex:
        for f in as_completed([ex.submit(one, b) for b in batches]):
            (res, err), b = f.result()
            if not res: BR.log(f"Claude: {err}"); continue
            meta = {x[0]: x for x in b}
            try:
                for it in BR.parse_json(res[0]).get("items") or []:
                    m = meta.get(it.get("id")); dp = it.get("depths") or {}
                    if not m or not it.get("title") or not ((dp.get("d1") or {}).get("body")) or any(x["id"] == m[0] for x in doc["items"]): continue
                    S = lambda v, n: str(v or "")[:n]
                    clean_d = {k: {"min": int((dp[k] or {}).get("min") or 1), "body": [S(p, 900) for p in (dp[k] or {}).get("body") or [] if str(p).strip()]} for k in ("d1", "d2", "d3") if dp.get(k)}
                    doc["items"].append({"id": m[0], "title": S(it["title"], 60), "orig": S(it.get("orig") or m[2], 120), "group": it.get("group") or m[1],
                        "kind": S(it.get("kind"), 30), "region": S(it.get("region"), 30), "era": S(it.get("era"), 80), "basis": S(it.get("basis"), 30),
                        "form": "Claude가 위키백과를 바탕으로 다시 씀", "mood": [x for x in it.get("mood") or [] if x in MOODS][:2] or ["기묘한"],
                        "tags": [S(x, 20) for x in it.get("tags") or []][:5], "hook": S(it.get("hook"), 300), "depths": clean_d,
                        "parts": [{"t": S(x.get("t"), 60), "b": S(x.get("b"), 300)} for x in it.get("parts") or [] if isinstance(x, dict)][:3],
                        "beyond": [{"t": S(x.get("t"), 60), "b": S(x.get("b"), 300)} for x in it.get("beyond") or [] if isinstance(x, dict)][:3],
                        **({"warn": S(it.get("warn"), 120)} if it.get("warn") else {}),
                        "sources": [{"t": f"Wikipedia, ‘{m[3]}’", "u": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(m[3].replace(" ", "_"))}] if m[3] else [],
                        "links": [], "api": 1})
                    got += 1
            except Exception as e:
                BR.log(f"답을 못 읽음 ({e})")
            doc["at"] = datetime.now(BR.KST).isoformat(timespec="minutes"); doc["items"].sort(key=lambda x: x["id"])
            OUT.parent.mkdir(parents=True, exist_ok=True); BR.wj(OUT, doc)
    BR.log(f"새로 {got}편 · 모두 {len(doc['items'])}편")
    return 0


if __name__ == "__main__":
    sys.exit(main())
