"""역사 편집 에피소드 검사 + 색인 다시 만들기 (토큰 0, 손으로 돌림)

쓰는 법:  python3 robot/history_editorial.py
  1) data/history/editorial/episodes/*.json 을 모두 검사
  2) 통과하면 data/history/editorial/index.json 의 episodes 목록을 다시 만듦 (programs·moods·series·featured 는 그대로 둠)
  하나라도 틀리면 색인을 건드리지 않고 무엇이 틀렸는지 보여 줌.
절차와 규칙은 robot/HISTORY_EDITORIAL_RUNBOOK.md
"""
import json, re, glob, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ED = ROOT / "data/history/editorial"
TYPES = {"intro", "narr", "choice", "doc", "info", "tabs", "rel", "result", "meaning"}
MARKS = {"fact", "recon", "interp", "hypo", "lore"}
MOODS = {"odd", "op", "people", "big"}
REGIONS = {"ea", "sa", "me", "eu", "af", "na", "la", "oc", "xx"}


def page_titles():
    t = set()
    for f in glob.glob(str(ROOT / "data/history/s/*.json")):
        for x in json.load(open(f)): t.add(x[0])
    return t


def check(e, ids, idx, titles):
    err, warn = [], []
    need = ["id", "program", "mood", "mins", "title", "hook", "cover", "place", "when", "ctx", "r", "y", "scenes", "next", "sources", "ver", "log"]
    for k in need:
        if k not in e: err.append(f"칸 없음: {k}")
    if err: return err, warn
    if e["program"] not in idx.get("programs", {}): err.append(f"없는 코너: {e['program']}")
    if e["mood"] not in MOODS: err.append(f"없는 기분: {e['mood']}")
    if e["r"] not in REGIONS: err.append(f"없는 권역: {e['r']}")
    srcn = {s["n"] for s in e["sources"]}
    for s in e["sources"]:
        if not s.get("url", "").startswith("http") or not s.get("supports"): err.append(f"출처 {s.get('n')}: 주소나 '뒷받침' 설명 없음")
    sids = [s["id"] for s in e["scenes"]]
    if len(set(sids)) != len(sids): err.append("장면 id 겹침")
    has_result = False
    for sc in e["scenes"]:
        where = f"장면 {sc.get('id')}"
        if sc.get("type") not in TYPES: err.append(f"{where}: 모르는 종류 {sc.get('type')}")
        if sc.get("mark") not in MARKS: err.append(f"{where}: 표시(mark) 없음/틀림")
        if sc["type"] == "result": has_result = True
        texts = [sc.get("text", "")] + [i.get("text", "") for i in sc.get("items", [])] + [t.get("text", "") for t in sc.get("tabs", [])] + [o.get("reply", "") for o in sc.get("opts", [])]
        for t in texts:
            for n in re.findall(r"\[(\d+)\]", t):
                if int(n) not in srcn: err.append(f"{where}: [{n}] 출처가 목록에 없음")
            for ref in re.findall(r"\{(\w+)\}", t):
                if ref not in sids or sids.index(ref) >= sids.index(sc["id"]) + (1 if sc["type"] != "choice" else 0) and ref != sc["id"]:
                    if ref not in sids: err.append(f"{where}: {{{ref}}} 장면이 없음")
        if sc["type"] == "choice":
            if not 2 <= len(sc.get("opts", [])) <= 4: err.append(f"{where}: 선택지는 2~4개")
            if not sc.get("q"): err.append(f"{where}: 질문 없음")
        if sc.get("mark") == "fact" and sc["type"] in ("narr", "info", "result") and not re.search(r"\[\d+\]", " ".join(texts)):
            warn.append(f"{where}: ‘기록’ 표시인데 출처 번호가 하나도 없음")
    if not has_result: err.append("결과(result) 장면이 없음")
    if len(e["next"]) > 3: err.append("다음 질문은 3개까지")
    for n in e["next"]:
        if n.get("ep") and n["ep"] not in ids: err.append(f"다음 질문: 없는 이야기 {n['ep']}")
        if n.get("page") and titles and n["page"] not in titles: warn.append(f"다음 질문: 원문 자료에 「{n['page']}」 없음 (화면엔 누를 수 없게 나옴)")
    if re.search(r"충격|소름|역대급", e["title"]): warn.append("제목에 ‘충격·소름·역대급’ — 재미를 단어로 대신하지 않기")
    return err, warn


def main():
    idx = json.load(open(ED / "index.json"))
    eps = [json.load(open(p)) for p in sorted(glob.glob(str(ED / "episodes/*.json")))]
    ids = {e["id"] for e in eps}
    titles = page_titles()
    bad = 0
    for e in eps:
        err, warn = check(e, ids, idx, titles)
        for w in warn: print(f"  주의 {e.get('id')}: {w}")
        for x in err: print(f"  틀림 {e.get('id')}: {x}"); bad += 1
    for s in idx.get("series", []):
        for i in s["eps"]:
            if i not in ids: print(f"  틀림 시리즈 {s['id']}: 없는 이야기 {i}"); bad += 1
    for i in idx.get("featured", []):
        if i not in ids: print(f"  틀림 대표작 편성: 없는 이야기 {i}"); bad += 1
    if bad:
        print(f"틀린 곳 {bad}개 — 색인은 그대로 둠"); sys.exit(1)
    order = {k: i for i, k in enumerate(idx.get("featured", []))}
    idx["episodes"] = sorted([{k: e.get(k) for k in ("id", "program", "mood", "mins", "title", "hook", "cover", "place", "when", "ctx", "ver", "r", "y", "wt")} | {"scenes": len(e["scenes"])} for e in eps],
                             key=lambda m: order.get(m["id"], 99))
    idx["v"] = max(e["ver"] for e in eps)
    json.dump(idx, open(ED / "index.json", "w"), ensure_ascii=False, indent=1)
    print(f"통과 · 이야기 {len(eps)}편 · 색인 다시 만듦")


if __name__ == "__main__":
    main()
