"""시사 자판기 1시간 갱신 도우미 (예약 작업 세션이 RUNBOOK.md 순서대로 실행).

  python hourly.py prep  <다운로드폴더> <이전판ID>        DB에서 받은 이전 판 문서를 WORK/seed 형식으로 정리
  python hourly.py crawl <새판ID>                         수집 (번역 없이)
  python hourly.py totr  <새판ID> <이전판ID>              번역할 제목 목록 (이미 번역된 글 제외)
  python hourly.py build <새판ID> <이전판ID> <ko.json> "<이름>"   판 만들기 + 이전 판 이슈·해설·댓글 이어붙이기
  python hourly.py ops   <새판ID>                         DB에 쓸 묶음(batch) 파일 만들기 → WORK/ops_*.json

환경변수 WORK = 작업 폴더 (기본 /tmp/sv/work)
"""
import hashlib, json, re
import os
import time
from datetime import datetime
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = Path(os.environ.get("WORK", "/tmp/sv/work")); WORK.mkdir(parents=True, exist_ok=True)
SEED = WORK / "seed"; SEED.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "crawler"))
sys.path.insert(0, str(ROOT))


def run(*args):
    subprocess.run([sys.executable, str(next(p for p in (ROOT / "builder" / "build_edition.py", ROOT / "prototype" / "build_edition.py") if p.exists())), *args], check=True, env={**os.environ, "WORK": str(WORK)})


def _strip(d):
    # ArtifactData 로 저장한 파일이 {data:{...}} 로 감싸져 있으면 벗김
    return d.get("data", d) if isinstance(d, dict) and set(d) >= {"data"} and isinstance(d.get("data"), dict) else d


def cmd_prep(dl, prev):
    dl = Path(dl); n = 0
    for f in dl.rglob("*.json"):
        col = f.parent.name; doc = f.stem
        if col not in ("editions", "feed", "brief"):
            continue
        (SEED / f"{col}__{doc}.json").write_text(json.dumps(_strip(json.loads(f.read_text())), ensure_ascii=False)); n += 1
    assert (SEED / f"editions__{prev}.json").exists(), f"이전 판 문서 없음: {prev}"
    print(f"정리한 문서 {n}개 → {SEED}")


def load_items(ed):
    items = {}
    for f in SEED.glob(f"feed__{ed}__*.json"):
        d = json.loads(f.read_text())
        for it in d["items"]:
            it["_lang"] = d["lang"]; items[it["id"]] = it
    return items


def cmd_build(ed, prev, ko, label):
    run("build", ed, prev, ko, label)
    from cluster import tokens, GENERIC
    E = json.loads((SEED / f"editions__{ed}.json").read_text())
    P = json.loads((SEED / f"editions__{prev}.json").read_text())
    items = load_items(ed); prev_items = load_items(prev)
    SC = {"reddit-worldnews": "WW"}
    ctry = lambda it: SC.get(it["s"], it["c"])
    title = lambda it: it.get("ko") or (it["t"] if it["_lang"] == "ko" else "")
    # 이전 판 이슈를 이어받음 — 규칙은 robot/fresh.py (글 나이 48시간·핵심어 고정·한 이슈 8% 상한 → 좀비·블랙홀 이슈 막기)
    import fresh as F
    out, carried, ended, used = F.carry(P.get("stories", []), items, prev_items, ed, tokens, GENERIC, title, ctry)
    for s2 in out:
        added = s2.pop("_added", [])
        # 해설(key·why3.now) 뒤에 붙은 새 글: 해설 글자가 바뀌면 다시 0부터 (화면의 '해설 뒤 새 소식' 표시용)
        kh = hashlib.md5(((s2.get("key") or "") + ((s2.get("why3") or {}).get("now") or "")).encode()).hexdigest()[:8]
        since = [] if s2.get("keyh") != kh else [i for i in s2.get("since", []) if i in s2["items"]]
        s2["keyh"] = kh; s2["since"] = since + [i for i in added if i not in since]
    now = F.now_of(ed)
    # 새 판의 단어 묶음 중 어디에도 안 붙은 큰 묶음은 '새 이슈 후보'로 남김 (해설은 다음 정리 때)
    cand = []
    for s in E.get("stories", []):
        rest = [i for i in s["items"] if i not in used and i in items and F.age_h(items[i], now) <= F.LIVE_H]   # 48시간 넘은 글은 새 이슈의 근거가 못 됨
        srcs = {items[i]["s"] for i in rest if i in items}
        # 나라 안 이슈도 후보로: 글 2개 이상 + 출처 2곳 이상
        if len(rest) >= 2 and len(srcs) >= 2:
            s["items"] = rest; s["delta"] = "new"; s["title"] = s.get("label", ""); s["cat"] = ""; s["born"] = ed
            used |= set(rest); F.stamp(s, items, ed)
            cand.append(s)
    E["stories"] = F.give_sid(out + cand, ed)     # 판이 바뀌어도 그대로인 이슈 번호 (폰의 '읽은 이슈' 기억용)
    for k in ("themes", "countryDigest", "explainMethod", "storyMethod", "daily"):      # daily = 하루 정리판 (다음 날 아침까지 그대로)
        if k in P and k not in E:
            E[k] = P[k]
    E["carriedFrom"] = prev
    E["ended"] = ended[:60]                      # 이번 판에서 내려간 이슈 (새 글이 48시간 끊김) — 화면의 '끝난 이슈' 표시용
    # 대표 기사 사진: RSS 사진이 있으면 그것, 없으면 앞쪽 뉴스 기사 2개까지 og:image (한 번 본 기사는 _og.json 에 기억, 한 번에 새로 80건까지)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "builder"))
    from build_edition import og_image, OG_CACHE
    try: og = json.loads(OG_CACHE.read_text())
    except Exception: og = {}
    tried = 0
    PROPER = sorted(F.proper_names(), key=len, reverse=True)
    BAD = ("news.google.", "reddit.com", "youtube.com", "x.com/", "twitter.com")
    for k, s in enumerate(E["stories"]):
        s["id"] = f"g{k+1}"
        its = [items[i] for i in s["items"] if i in items]
        cnt = {}
        for x in its: cnt[ctry(x)] = cnt.get(ctry(x), 0) + 1
        stt = set(re.findall(r"[가-힣a-z0-9]{2,}", (s.get("title") or "").lower()))
        fit = lambda it: sum(1 for w in stt if w in (title(it) or it.get("t") or "").lower())   # 조사가 붙어도 맞게 '들어 있나'로 셈
        # 이슈 제목과 낱말이 겹치는 뉴스 기사 위쪽 3개 중에서 사진을 찾음(RSS 사진 → 없으면 og:image). 엉뚱한 기사 사진보다는 차라리 지도
        # 제목의 첫 고유명사(예: 바이낸스)가 기사 제목에 든 기사만 사진 후보 — 없으면 사진 대신 지도 (엉뚱한 사진 막기)
        tt = s.get("title") or ""
        nm = [n for _, n in sorted((tt.find(n), n) for n in PROPER if n in tt)]
        has = (lambda it: nm[0] in ((title(it) or "") + " " + (it.get("t") or ""))) if nm else (lambda it: fit(it) >= 1)
        cand = sorted([x for x in its if x["k"] == "news" and has(x)], key=lambda it: (-fit(it), -cnt.get(ctry(it), 0)))[:3]
        s.pop("ph", None)
        for it in cand:
            u = (it.get("m") or {}).get("img")
            if not u and not any(b in (it.get("u") or "") for b in BAD):
                if it["id"] not in og and tried < 80:
                    og[it["id"]] = og_image(it["u"]); tried += 1
                u = og.get(it["id"])
            if u:
                s["ph"] = {"u": u, "s": it["s"], "i": it["id"]}; break
    if len(og) > 4000: og = dict(list(og.items())[-3000:])
    OG_CACHE.write_text(json.dumps(og, ensure_ascii=False))
    print(f"대표 사진: 이슈 {sum(1 for s in E['stories'] if s.get('ph'))}/{len(E['stories'])}개 (og:image 새로 확인 {tried}건)")
    (SEED / f"editions__{ed}.json").write_text(json.dumps(E, ensure_ascii=False))
    for lang, arr in carried.items():
        f = SEED / f"feed__{ed}__{lang}.json"
        d = json.loads(f.read_text()) if f.exists() else {"edition": ed, "lang": lang, "items": []}
        have = {x["id"] for x in d["items"]}
        d["items"] += [dict(x, carried=True) for x in arr if x["id"] not in have]
        f.write_text(json.dumps(d, ensure_ascii=False))
    # 댓글: 아직 남은 글의 댓글 정리를 이어받음
    pc = SEED / f"brief__{prev}__cm.json"
    if pc.exists():
        c = json.loads(pc.read_text()); c["map"] = {k: v for k, v in c.get("map", {}).items() if k in items}; c["edition"] = ed
        (SEED / f"brief__{ed}__cm.json").write_text(json.dumps(c, ensure_ascii=False))
    big = max((len(s["items"]) for s in E["stories"]), default=0)
    print(f"이슈 {len(out)}개 이어받음 (새 글 붙은 것 {sum(1 for s in out if s.get('grow'))}) · 내려간 이슈 {len(ended)}개 · 새 이슈 후보 {len(cand)}개 · 가장 큰 이슈 글 {big}개")
    for s in E["stories"][:12]:
        print(f'  {s["id"]} [{s["delta"]}{"+"+str(s.get("grow")) if s.get("grow") else ""}] {s.get("title")}  ({len(s["countries"])}개국)')


def cmd_ops(ed):
    files = sorted(SEED.glob(f"feed__{ed}__*.json")) + [p for p in [SEED / f"brief__{ed}__cm.json"] if p.exists()]
    batches, cur, size = [], [], 0
    for f in files:
        col, doc = f.stem.split("__", 1)
        sz = f.stat().st_size
        if cur and (size + sz > 850_000 or len(cur) >= 45):
            batches.append(cur); cur, size = [], 0
        cur.append({"op": "set", "collection": col, "doc_id": doc, "file_path": str(f)}); size += sz
    if cur:
        batches.append(cur)
    batches.append([{"op": "set", "collection": "editions", "doc_id": ed, "file_path": str(SEED / f"editions__{ed}.json")}])
    for k, b in enumerate(batches):
        (WORK / f"ops_{k}.json").write_text(json.dumps(b, ensure_ascii=False, indent=1))
    print(f"묶음 {len(batches)}개: " + ", ".join(f"ops_{k}.json({len(b)})" for k, b in enumerate(batches)) + "  ← 마지막(판 정보)을 맨 나중에 쓰세요")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "prep": cmd_prep(sys.argv[2], sys.argv[3])
    elif c == "crawl": run("crawl", sys.argv[2])
    elif c == "totr": run("totr", sys.argv[2], sys.argv[3])
    elif c == "build": cmd_build(*sys.argv[2:6])
    elif c == "ops": cmd_ops(sys.argv[2])
