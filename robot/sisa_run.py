"""sisa_run.py — 시사 자판기 로봇 (GitHub Actions 에서 3시간마다 실행, 토큰 0).

순서: 이전 판 준비 → 수집 → 제목 번역(DeepL→Google) → 판 만들기 → 댓글 수집·번역 → 이름 사진 → data/sisa 에 저장 → 7일 지난 판 정리
해설(이슈 제목·꼭 알아야 할 5개·단신·이름 사전)은 클로드 예약 작업이 따로 채웁니다 (robot/EDITOR_RUNBOOK.md).

  python robot/sisa_run.py            # 전체 실행
  python robot/sisa_run.py --dry      # 번역 API 호출 없이 흐름만 확인
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROBOT = ROOT / "robot"
DATA = ROOT / "data" / "sisa"
WORK = Path(os.environ.get("WORK", "/tmp/sv/work"))
SEED = WORK / "seed"
KST = timezone(timedelta(hours=9))
KEEP_DAYS = int(os.environ.get("SISA_KEEP_DAYS", "7"))
RUNS_PER_DAY = 8
CM_PER_RUN = int(os.environ.get("SISA_CM_PER_RUN", "20"))      # 댓글 수집할 글 수
CM_PICKS = 3                                                   # 글당 번역할 댓글 수

sys.path.insert(0, str(ROBOT / "crawler"))
import yaml  # noqa: E402
from translate import Translator, deepl_month_usage  # noqa: E402

DRY = "--dry" in sys.argv
if DRY:
    os.environ["FAKE_TRANSLATE"] = "1"


def log(*a):
    print(*a, flush=True)


def rj(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def wj(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def run(*args, cwd=None):
    env = {**os.environ, "WORK": str(WORK)}
    r = subprocess.run([sys.executable, *map(str, args)], cwd=str(cwd or ROOT), env=env, capture_output=True, text=True)
    if r.stdout: log(r.stdout.strip()[-3000:])
    if r.returncode != 0:
        log(r.stderr.strip()[-3000:]); raise SystemExit(f"실패: {args[0]}")
    return r.stdout


# ── 0. 판 ID ──
def new_edition_id():
    now = datetime.now(KST)
    return now.strftime("%Y-%m-%d_h%H"), f"{now.month}월 {now.day}일 {now.hour}시판"


def prev_edition_id():
    idx = rj(DATA / "editions/_index.json", [])
    if not idx: return None
    return max(idx, key=lambda e: e.get("crawledAt", ""))["id"]


# ── 1. 이전 판 준비 ──
def prep(prev):
    if WORK.exists(): shutil.rmtree(WORK)
    SEED.mkdir(parents=True)
    n = 0
    for col, pat in (("editions", f"{prev}.json"), ("feed", f"{prev}__*.json"), ("brief", f"{prev}__cm.json")):
        for f in (DATA / col).glob(pat):
            shutil.copy(f, SEED / f"{col}__{f.name}"); n += 1
    log(f"이전 판 {prev} 문서 {n}개 준비")


# ── 3. 번역 ──
def month_usage_path():
    return DATA / "_usage.json"


def translator_for_run():
    u = rj(month_usage_path(), {})
    mk = datetime.now(KST).strftime("%Y-%m")
    used = u.get(mk, {"deepl": 0, "google": 0})
    now = datetime.now(KST)
    import calendar
    days = calendar.monthrange(now.year, now.month)[1]
    runs_left = max(1, (days - now.day) * RUNS_PER_DAY + (RUNS_PER_DAY - now.hour // 3))
    deepl_cap = int(os.environ.get("DEEPL_MONTHLY_CAP", "480000"))
    google_cap = int(os.environ.get("GOOGLE_MONTHLY_CAP", "480000"))
    du = deepl_month_usage(os.environ.get("DEEPL_API_KEY")) if not DRY else None
    used_deepl = du[0] if du else used["deepl"]
    if du: deepl_cap = min(deepl_cap, du[1] - 5000)
    b_deepl = max(0, (deepl_cap - used_deepl) // runs_left)
    b_google = max(0, (google_cap - used["google"]) // runs_left)
    if DRY:
        b_deepl = b_google = 10 ** 7
    tr = Translator.from_env(b_deepl, b_google)
    log(f"번역 예산 이번 회차: DeepL {b_deepl:,}자 / Google {b_google:,}자 (이달 사용 DeepL {used_deepl:,} / Google {used['google']:,})")
    return tr, mk


def save_usage(tr, mk):
    u = rj(month_usage_path(), {})
    m = u.setdefault(mk, {"deepl": 0, "google": 0})
    m["deepl"] += tr.used["deepl"]; m["google"] += tr.used["google"]
    wj(month_usage_path(), u)


def translate_titles(tr, totr_tsv: str, lang_of_source: dict) -> dict:
    rows = [l.split("\t", 2) for l in totr_tsv.splitlines() if l and not l.startswith("#") and "\t" in l]
    by_lang = {}
    for iid, sid, title in rows:
        lang = lang_of_source.get(sid, "en")
        if lang == "ko": continue
        by_lang.setdefault(lang, []).append((iid, title))
    ko = {}
    for lang, group in by_lang.items():
        res, eng = tr.translate([t for _, t in group], lang)
        if res:
            for (iid, _), t in zip(group, res): ko[iid] = t
        else:
            log(f"  번역 예산 부족: {lang} {len(group)}개 건너뜀")
    log(f"제목 번역 {len(ko)}/{len(rows)}개 (DeepL {tr.used['deepl']:,}자, Google {tr.used['google']:,}자)")
    return ko


# ── 5. 댓글 ──
def comment_targets(ed, prev_cm: dict, lang_of_source: dict):
    E = rj(SEED / f"editions__{ed}.json", {})
    items = {}
    for f in SEED.glob(f"feed__{ed}__*.json"):
        d = rj(f, {})
        for it in d.get("items", []):
            it["_lang"] = d.get("lang"); items[it["id"]] = it
    wanted = []
    for s in E.get("stories", []):                     # 이슈에 묶인 커뮤니티 글 우선
        for iid in s.get("items", []):
            it = items.get(iid)
            if it and it.get("k") == "community" and iid not in prev_cm and iid not in [w["id"] for w in wanted]:
                wanted.append({"id": iid, "s": it["s"], "u": it["u"], "lang": it["_lang"]})
    for it in sorted([i for i in items.values() if i.get("k") == "community"], key=lambda i: i.get("r", 99)):
        if len(wanted) >= CM_PER_RUN: break
        if it["id"] not in prev_cm and it["id"] not in [w["id"] for w in wanted]:
            wanted.append({"id": it["id"], "s": it["s"], "u": it["u"], "lang": it["_lang"]})
    return wanted[:CM_PER_RUN]


def collect_comments(ed, tr, lang_of_source):
    cm_path = SEED / f"brief__{ed}__cm.json"
    cm = rj(cm_path, {"edition": ed, "map": {}})
    targets = comment_targets(ed, cm.get("map", {}), lang_of_source)
    if not targets or DRY:
        log(f"댓글 대상 {len(targets)}개 (dry={DRY})"); wj(cm_path, cm); return
    tpath, rpath = WORK / "cm_targets.json", WORK / "cm_raw.json"
    wj(tpath, [{k: t[k] for k in ("id", "s", "u")} for t in targets])
    try:
        run(ROBOT / "crawler/comments.py", tpath, rpath, cwd=ROBOT / "crawler")
    except SystemExit:
        log("댓글 수집 실패 — 건너뜀"); return
    raw = rj(rpath, {})
    lang_of = {t["id"]: t["lang"] for t in targets}
    by_lang, meta = {}, {}
    for iid, res in raw.items():
        cs = [c for c in res.get("comments", []) if len(c.get("t", "")) >= 8][:CM_PICKS]
        if not cs: continue
        meta[iid] = {"n": len(res.get("comments", [])), "order": res.get("order", ""), "push": res.get("push")}
        by_lang.setdefault(lang_of.get(iid, "en"), []).append((iid, cs))
    n = 0
    for lang, group in by_lang.items():
        texts = [c["t"][:280] for _, cs in group for c in cs]
        res, eng = tr.translate(texts, lang) if lang != "ko" else (texts, "ko")
        if not res: continue
        k = 0
        for iid, cs in group:
            picks = []
            for c in cs:
                picks.append({"type": "top", "ko": res[k], "raw": res[k], "orig": c["t"][:280]}); k += 1
            cm["map"][iid] = {"mood": "", "picks": picks, **{a: b for a, b in meta[iid].items() if b}}
            n += 1
    cm.update(edition=ed, fetchedAt=datetime.now(KST).isoformat(), method="comments.py + 기계번역(DeepL/Google)")
    wj(cm_path, cm)
    log(f"댓글 정리 {n}개 글 (분위기 한 줄은 편집장이 채움)")


# ── 6. 이름 사진 ──
def photos():
    ents, pics = DATA / "brief/ents.json", DATA / "brief/entpics.json"
    if not ents.exists(): return
    out = WORK / "newpics.json"
    try:
        run(ROBOT / "pipeline/photos.py", ents, out, pics if pics.exists() else "")
    except SystemExit:
        log("사진 찾기 실패 — 건너뜀"); return
    new = rj(out, {})
    if new:
        d = rj(pics, {"map": {}}); d.setdefault("map", {}).update(new); d["updatedAt"] = datetime.now(KST).isoformat()
        wj(pics, d); log(f"이름 사진 {len(new)}개 추가")


# ── 7. 저장 + 정리 ──
def publish(ed, prev, label):
    # 판·피드·댓글
    shutil.copy(SEED / f"editions__{ed}.json", DATA / "editions" / f"{ed}.json")
    (DATA / "feed").mkdir(exist_ok=True)
    for f in SEED.glob(f"feed__{ed}__*.json"):
        shutil.copy(f, DATA / "feed" / f.name.replace("feed__", ""))
    cm = SEED / f"brief__{ed}__cm.json"
    if cm.exists(): shutil.copy(cm, DATA / "brief" / f"{ed}__cm.json")
    # 이전 판 해설 문서(brief/<판>)는 새 판으로 이어받음 (글 요약은 글 id 기준이라 그대로 유효)
    if prev and (DATA / "brief" / f"{prev}.json").exists() and not (DATA / "brief" / f"{ed}.json").exists():
        b = rj(DATA / "brief" / f"{prev}.json", {}); b["edition"] = ed; b["carriedFrom"] = prev
        wj(DATA / "brief" / f"{ed}.json", b)
    # 7일 지난 판 정리
    cut = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    removed = 0
    for f in list((DATA / "editions").glob("*.json")) + list((DATA / "feed").glob("*.json")) + list((DATA / "brief").glob("*.json")):
        if f.name.startswith("_") or f.stem in ("ents", "entpics", "entnames"): continue
        if f.name[:10] < cut:
            f.unlink(); removed += 1
    reindex()
    E = rj(DATA / "editions" / f"{ed}.json", {})
    wj(DATA / "_meta.json", {"updatedAt": E.get("crawledAt") or datetime.now(timezone.utc).isoformat(), "edition": ed, "label": label,
                             "by": "github-actions", "counts": E.get("counts", {})})
    log(f"저장 완료: {ed} ({label}), 오래된 파일 {removed}개 정리")


def ent_names():
    """이름 사전에서 '밑줄 칠 이름'만 뽑은 작은 파일 (앱은 처음에 이것만 받고, 설명은 이름을 누를 때 받음)."""
    src = DATA / "brief/ents.json"
    if not src.exists(): return
    m = (rj(src, {}) or {}).get("map", {})
    out = {n: [e.get("t", "term"), e.get("c", "")] + [a for a in (e.get("a") or []) if a] for n, e in m.items()}
    wj(DATA / "brief/entnames.json", {"map": out, "updatedAt": (rj(src, {}) or {}).get("updatedAt", "")})


def reindex():
    ent_names()
    eds = []
    for f in sorted((DATA / "editions").glob("*.json")):
        if f.name.startswith("_"): continue
        d = rj(f, {}); eds.append({**d, "id": f.stem})
    # 화면이 처음 받는 파일을 가볍게: 최신 판 2개만 통째로, 나머지는 이름·시각만 (고르면 화면이 그 판 파일을 따로 받음)
    eds.sort(key=lambda e: e.get("crawledAt", ""))
    for k, e in enumerate(eds[:-2]):
        eds[k] = {"id": e["id"], "label": e.get("label", e["id"]), "crawledAt": e.get("crawledAt", ""), "stub": True}
    wj(DATA / "editions/_index.json", eds)
    for col in ("feed", "brief", "tr"):
        (DATA / col).mkdir(exist_ok=True)
        wj(DATA / col / "_index.json", sorted(f.stem for f in (DATA / col).glob("*.json") if not f.name.startswith("_")))


def main():
    t0 = time.time()
    ed, label = new_edition_id()
    prev = prev_edition_id()
    if not prev:
        raise SystemExit("이전 판이 없어요. data/sisa/editions/_index.json 확인")
    if prev == ed:
        log("이번 시간 판이 이미 있어요 — 종료"); return
    log(f"새 판 {ed} ({label}) ← 이전 판 {prev}")
    cfg = yaml.safe_load((ROBOT / "crawler/sources.yaml").read_text(encoding="utf-8"))
    lang_of_source = {s["id"]: s["lang"] for s in cfg["sources"]}

    prep(prev)
    H = ROBOT / "pipeline/hourly.py"
    run(H, "crawl", ed)
    totr = run(H, "totr", ed, prev)
    tr, mk = translator_for_run()
    ko = translate_titles(tr, totr, lang_of_source)
    wj(WORK / "ko.json", ko)
    run(H, "build", ed, prev, WORK / "ko.json", label)
    collect_comments(ed, tr, lang_of_source)
    # 이름 사진은 미리 찾지 않음 — 앱이 이름을 누를 때 위키백과(자유 이용 사진만)에서 바로 받아 옴
    save_usage(tr, mk)
    publish(ed, prev, label)
    log(f"끝: {round(time.time() - t0)}초")


if __name__ == "__main__":
    main()
