"""시제품용 '판(edition)' 만들기 도구.

  1) python build_edition.py crawl  <판ID>                      → 수집 (번역 없이)
  2) python build_edition.py totr   <판ID> <이전판ID>            → 번역할 제목 목록 (이전 판에서 번역된 글은 재사용)
  3) python build_edition.py build  <판ID> <이전판ID> <번역.json> "<이름>"  → 사건 묶기 + 이전 판 대비 변화 + 저장용 문서

판ID 예: 2026-11-01_pm   작업 폴더: 환경변수 WORK (기본: 현재 폴더)
"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
CRAWLER = HERE.parent / "crawler"
sys.path.insert(0, str(CRAWLER))
from cluster import build_stories, tokens  # noqa: E402

WORK = Path(os.environ.get("WORK", "."))
LIMIT = {"news": 8, "community": 10, "trend": 10}
TR_TOP = {"news": 6, "community": 8, "trend": 5}   # 이야기를 늘리려고 번역 범위를 넓힘


def raw_path(ed): return WORK / f"raw_{ed}.json"


def load_raw(ed):
    d = json.loads(raw_path(ed).read_text())
    items = [i for i in d["items"] if i["first_rank"] <= LIMIT.get(i["kind"], 10)]
    return d, items


def load_prev(prev):
    """이전 판 문서(seed 폴더)에서 글 목록과 사건을 읽음."""
    ed = json.loads((WORK / "seed" / f"editions__{prev}.json").read_text())
    items = {}
    for f in (WORK / "seed").glob(f"feed__{prev}__*.json"):
        for it in json.loads(f.read_text())["items"]:
            items[it["id"]] = it
    extra = WORK / f"tr_{prev}.json"            # 화면에서 Claude로 번역한 것 (있으면)
    if extra.exists():
        for k, v in json.loads(extra.read_text()).items():
            if k in items and "__" not in k and not items[k].get("ko"):
                items[k]["ko"] = v
    return ed, items


def cmd_crawl(ed):
    out = raw_path(ed)
    if out.exists(): out.unlink()
    subprocess.run([sys.executable, str(CRAWLER / "crawl.py"), "--slot", "manual", "--local", str(out), "--no-translate"],
                   check=True, cwd=str(CRAWLER))


def cmd_totr(ed, prev):
    _, items = load_raw(ed)
    _, prev_items = load_prev(prev)
    todo = [i for i in items if i["first_rank"] <= TR_TOP.get(i["kind"], 3)
            and not (prev_items.get(i["guid_hash"][:12], {}).get("ko"))]
    new_total = sum(1 for i in items if i["guid_hash"][:12] not in prev_items)
    print(f"# 글 {len(items)}개 중 이전 판에 없던 새 글 {new_total}개, 번역할 제목 {len(todo)}개")
    for i in todo:
        print(f'{i["guid_hash"][:12]}\t{i["source_id"]}\t{i["title"]}')


def match_story(s, prev_stories):
    best, score = None, 0
    for p in prev_stories:
        ov = len(set(s.get("items", [])) & set(p.get("items", [])))
        kw = len(set(s.get("kw", [])) & set(p.get("kw", [])))
        sc = ov * 3 + kw
        if (ov >= 1 or kw >= 3) and sc > score:   # 같은 글이 겹치거나 핵심어 3개 이상 겹칠 때만 같은 사건
            best, score = p, sc
    return best


def cmd_build(ed, prev, ko_file, label):
    d, items = load_raw(ed)
    prev_ed, prev_items = load_prev(prev)
    ko = json.loads(Path(ko_file).read_text()) if ko_file and Path(ko_file).exists() else {}
    run = d["crawl_runs"][-1]
    for i in items:
        sid = i["guid_hash"][:12]
        p = prev_items.get(sid)
        i["title_ko"] = ko.get(sid) or (p or {}).get("ko")
        i["_first"] = (p or {}).get("first", prev) if p else ed
    stories = build_stories(items, ed[:10])
    idmap = {i["id"]: i["guid_hash"][:12] for i in items}
    out_stories = [{"id": f"s{k+1}", "label": s["label"], "kw": s["keywords"], "items": [idmap[x] for x in s["item_ids"]],
                    "langs": s["langs"], "countries": s["countries"], "method": "keyword-v1"} for k, s in enumerate(stories)]
    matched = set()
    for s in out_stories:
        p = match_story(s, prev_ed.get("stories", []))
        if not p:
            s["delta"] = "new"
        else:
            matched.add(p["id"])
            grow = len(set(s["items"]) - set(p["items"]))
            more_c = len(set(s["countries"]) - set(p.get("countries", [])))
            s["delta"] = "grown" if (grow or more_c) else "same"
            s["grow"] = grow
            s["prev"] = p["id"]
    gone = [p.get("label") or p.get("title") or p.get("id") for p in prev_ed.get("stories", []) if p.get("id") not in matched]

    stats = run["stats"]["sources"]
    import yaml
    cfg = yaml.safe_load((CRAWLER / "sources.yaml").read_text())
    sources = []
    for s in cfg["sources"]:                       # 수집처 목록은 항상 최신 sources.yaml 기준
        st = stats.get(s["id"])
        sources.append({"id": s["id"], "n": s["name"], "l": s["lang"], "c": s["country"], "k": s["kind"], "st": s["status"],
                        "ax": s.get("axis", ""), "lean": s.get("lean", ""),
                        "note": s.get("note", ""), "tier": s.get("tier", ""), "home": s.get("homepage", ""),
                        "ok": None if st is None else ("error" not in st), "cnt": sum(1 for i in items if i["source_id"] == s["id"])})
    edition = {"label": label, "crawledAt": run["started_at"], "slot": ed[-2:], "sources": sources, "stories": out_stories,
               "delta": {"prev": prev, "gone": gone},
               "counts": {"items": len(items), "ko": sum(1 for i in items if i.get("title_ko")),
                          "sources_ok": sum(1 for v in stats.values() if "error" not in v), "sources_run": len(stats),
                          "new_items": sum(1 for i in items if i["_first"] == ed),
                          "new_news": sum(1 for i in items if i["_first"] == ed and i.get("kind") != "trend")}}   # 시사 첫 화면 숫자와 같은 기준 (트렌드 제외)
    seed = WORK / "seed"; seed.mkdir(exist_ok=True)
    (seed / f"editions__{ed}.json").write_text(json.dumps(edition, ensure_ascii=False))
    for lang in sorted({i["lang"] for i in items}):
        arr = []
        for i in sorted([x for x in items if x["lang"] == lang], key=lambda x: (x["source_id"], x["first_rank"])):
            o = {"id": i["guid_hash"][:12], "s": i["source_id"], "k": i["kind"], "c": i["country"], "t": i["title"],
                 "u": i["url"], "r": i["first_rank"], "first": i["_first"]}
            if i.get("title_ko"): o["ko"] = i["title_ko"]
            if i.get("summary"): o["sm"] = i["summary"][:220 if i["kind"] != "trend" else 160]
            if i.get("published_at"): o["p"] = i["published_at"]
            if i.get("metric"): o["m"] = i["metric"]
            arr.append(o)
        (seed / f"feed__{ed}__{lang}.json").write_text(json.dumps({"edition": ed, "lang": lang, "items": arr}, ensure_ascii=False))
    print(json.dumps(edition["counts"], ensure_ascii=False))
    for s in out_stories:
        print(f'  [{s["delta"]}{"+"+str(s.get("grow")) if s.get("grow") else ""}] {s["label"]}  ({len(s["items"])}개, {",".join(s["langs"])})')
    print("  사라진 사건:", gone)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "crawl": cmd_crawl(sys.argv[2])
    elif c == "totr": cmd_totr(sys.argv[2], sys.argv[3])
    elif c == "build": cmd_build(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "", sys.argv[5] if len(sys.argv) > 5 else sys.argv[2])
