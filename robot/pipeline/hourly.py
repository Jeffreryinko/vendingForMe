"""시사 자판기 1시간 갱신 도우미 (예약 작업 세션이 RUNBOOK.md 순서대로 실행).

  python hourly.py prep  <다운로드폴더> <이전판ID>        DB에서 받은 이전 판 문서를 WORK/seed 형식으로 정리
  python hourly.py crawl <새판ID>                         수집 (번역 없이)
  python hourly.py totr  <새판ID> <이전판ID>              번역할 제목 목록 (이미 번역된 글 제외)
  python hourly.py build <새판ID> <이전판ID> <ko.json> "<이름>"   판 만들기 + 이전 판 이슈·해설·댓글 이어붙이기
  python hourly.py ops   <새판ID>                         DB에 쓸 묶음(batch) 파일 만들기 → WORK/ops_*.json

환경변수 WORK = 작업 폴더 (기본 /tmp/sv/work)
"""
import hashlib, json
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
    # 이전 판 AI 이슈를 이어받음: 아직 남아 있는 글 + 새 글 중 핵심 단어가 2개 이상 겹치는 글
    used = set(); out = []; carried = {}
    for s in [x for x in P.get("stories", []) if x.get("method") == "ai-v1"]:
        keep = [i for i in s["items"] if i in items]
        # 이번 수집에서 피드 밖으로 밀려난 글도 30시간까지는 이슈에 남김 (판에 함께 실어 줌)
        for i in s["items"]:
            it = prev_items.get(i)
            if i not in items and it and it["k"] != "trend":
                t = it.get("p") or ""
                try:
                    old = (time.time() - datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()) / 3600 if t else 0
                except Exception:
                    old = 0
                if old <= 30:
                    carried.setdefault(it["_lang"], []).append({k: v for k, v in it.items() if k != "_lang"})
                    items[i] = it; keep.append(i)
        prof = set()
        for i in s["items"]:
            it = items.get(i) or prev_items.get(i)
            if it: prof |= {t for t in tokens(title(it)) if t not in GENERIC}
        added = []
        for i, it in items.items():
            if i in keep or i in used or it["k"] == "trend" or it.get("first") != ed:
                continue
            # 단신은 단어 2개만 겹쳐도 엉뚱한 글이 붙기 쉬워서 3개 이상일 때만
            if len(tokens(title(it)) & prof) >= (3 if s.get("kind") == "brief" else 2):
                added.append(i)
        ids = keep + added
        # 단신(kind=brief)은 글 1개로도 유지. 다른 출처 글이 붙으면 이야기로 승격
        if len(ids) < (1 if s.get("kind") == "brief" else 2):
            continue
        used |= set(ids)
        s2 = dict(s); s2["items"] = ids
        s2["countries"] = sorted({ctry(items[i]) for i in ids}); s2["langs"] = sorted({items[i]["_lang"] for i in ids})
        if s2.get("kind") == "brief" and len(ids) >= 2:
            s2["kind"] = "global" if len(s2["countries"]) >= 2 else "local"
        elif not s2.get("kind"):
            s2["kind"] = "global" if len(s2["countries"]) >= 2 else "local"
        s2["delta"] = "grown" if added else "same"; s2["grow"] = len(added)
        # 해설(key·why3.now) 뒤에 붙은 새 글: 편집장이 해설을 고치면(글자가 바뀌면) 다시 0부터 (토큰 0, 화면에 '해설 뒤 새 소식' 표시용)
        kh = hashlib.md5(((s.get("key") or "") + ((s.get("why3") or {}).get("now") or "")).encode()).hexdigest()[:8]
        since = [] if s.get("keyh") != kh else [i for i in s.get("since", []) if i in ids]
        s2["keyh"] = kh; s2["since"] = since + [i for i in added if i not in since]
        out.append(s2)
    # 새 판의 단어 묶음 중 어디에도 안 붙은 큰 묶음은 '새 이슈 후보'로 남김 (해설은 다음 정리 때)
    cand = []
    for s in E.get("stories", []):
        rest = [i for i in s["items"] if i not in used]
        srcs = {items[i]["s"] for i in rest if i in items}
        # 나라 안 이슈도 후보로: 글 2개 이상 + 출처 2곳 이상
        if len(rest) >= 2 and len(srcs) >= 2:
            s["items"] = rest; s["delta"] = "new"; s["title"] = s.get("label", ""); s["cat"] = ""
            cand.append(s)
    E["stories"] = out + cand
    for k in ("themes", "countryDigest", "explainMethod", "storyMethod"):
        if k in P and k not in E:
            E[k] = P[k]
    E["carriedFrom"] = prev
    for k, s in enumerate(E["stories"]):
        s["id"] = f"g{k+1}"
        # 대표 기사 사진 하나 (홈 카드처럼 글 목록 없이 그리는 곳에서 씀). 뉴스 기사 사진을 먼저
        ph = sorted([items[i] for i in s["items"] if i in items and (items[i].get("m") or {}).get("img")], key=lambda it: it["k"] != "news")
        if ph: s["ph"] = {"u": ph[0]["m"]["img"], "s": ph[0]["s"], "i": ph[0]["id"]}
        else: s.pop("ph", None)
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
    print(f"이슈 {len(out)}개 이어받음 (새 글 붙은 것 {sum(1 for s in out if s['delta']=='grown')}), 새 이슈 후보 {len(cand)}개")
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
