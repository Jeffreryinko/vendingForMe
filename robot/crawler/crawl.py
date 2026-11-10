"""시사 자판기 수집기.

실행 예)
  python crawl.py --slot am                 # GitHub Actions (Supabase 에 저장)
  python crawl.py --slot manual --local data.json   # 키 없이 내 PC 에서 테스트
순서: 수집처 등록 → 피드 수집 → 중복 제거 → 한국어 번역(예산 안에서) → 저장 → 사건 묶기
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import html
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
import yaml

from cluster import build_stories
from db import get_db, now_iso
from translate import Translator, deepl_month_usage
import reddit_api

KST = timezone(timedelta(hours=9))
HERE = Path(__file__).parent
UA = "Mozilla/5.0 (compatible; SisaVending/1.0; personal news reader)"
REDDIT_UA = "python:sisa-vending:v1.0 (personal news digest)"

DEEPL_MONTHLY_CAP = int(os.environ.get("DEEPL_MONTHLY_CAP", "490000"))    # 무료 50만 자 중 여유 1만 자
GOOGLE_MONTHLY_CAP = int(os.environ.get("GOOGLE_MONTHLY_CAP", "480000"))  # 무료 50만 자($10 크레딧) 이내
SUMMARY_TRANSLATE_TOP = int(os.environ.get("SUMMARY_TRANSLATE_TOP", "3"))  # 출처별 상위 N개는 설명도 번역
SUMMARY_TRANSLATE_CHARS = 180


# ── 유틸 ────────────────────────────────────────────────
def h(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:20]


TAG_RE = re.compile(r"<[^>]+>")


def clean(text: str | None, limit=500) -> str:
    if not text:
        return ""
    t = html.unescape(TAG_RE.sub(" ", text))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit]


def to_iso(struct) -> str | None:
    if not struct:
        return None
    try:
        return datetime(*struct[:6], tzinfo=timezone.utc).isoformat()
    except Exception:
        return None


def kst_today() -> str:
    return datetime.now(KST).date().isoformat()


def load_sources():
    cfg = yaml.safe_load((HERE / "sources.yaml").read_text())
    default_max = cfg.get("defaults", {}).get("max_items", {})
    has_yt = bool(os.environ.get("YOUTUBE_API_KEY"))
    out = []
    for s in cfg["sources"]:
        s = {**s}
        s.setdefault("max_items", default_max.get(s["kind"], 10) if isinstance(default_max, dict) else default_max)
        if s["method"] == "youtube" and has_yt and s["status"] == "needs_key":
            s["status"] = "active"
        out.append(s)
    return out


# ── 수집 (방식별) ─────────────────────────────────────────
def http_get(url, ua=UA, retries=1):
    for attempt in range(retries + 1):
        r = requests.get(url, headers={"User-Agent": ua, "Accept": "application/rss+xml, application/xml, */*"},
                         timeout=25)
        if r.status_code == 429 and attempt < retries:
            time.sleep(20 * (attempt + 1))       # 20초, 40초 기다렸다 재시도
            continue
        r.raise_for_status()
        return r.content


def rss_img(e):
    """RSS 항목에 딸린 대표 사진 주소 (media:content/thumbnail · enclosure · 본문 첫 img). 없으면 None"""
    def ok(u):
        if not u or not isinstance(u, str): return None
        u = u.strip().replace("&amp;", "&")
        if u.startswith("//"): u = "https:" + u
        if u.startswith("http://"): u = "https://" + u[7:]                 # 사이트가 https 라 섞인 콘텐츠 막힘 방지
        u = re.sub(r"(ichef\.bbci\.co\.uk/(?:ace/standard|ace/ws|news))/\d{2,3}/", r"\1/976/", u)   # BBC RSS 사진은 240px → 같은 사진의 976px 판
        if not u.startswith("https://") or re.search(r"(pixel|spacer|1x1|blank)\.(gif|png)|feeds\.feedburner|/ad[sx]?/", u, re.I): return None
        return u[:600]
    for key in ("media_content", "media_thumbnail"):
        best = None
        for m in e.get(key) or []:
            if m.get("medium") not in (None, "image") and not re.search(r"\.(jpe?g|png|webp)", m.get("url", ""), re.I): continue
            w = int(m.get("width") or 0) if str(m.get("width") or "0").isdigit() else 0
            if w and w < 120: continue
            if best is None or w > best[0]: best = (w, m.get("url"))
        if best and ok(best[1]): return ok(best[1])
    for l in e.get("links") or []:
        if l.get("rel") == "enclosure" and str(l.get("type", "")).startswith("image") and ok(l.get("href")): return ok(l.get("href"))
    html = (e.get("summary") or "") + " ".join(c.get("value", "") for c in (e.get("content") or []))
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)", html)
    if m and not re.search(r'width=["\']?1["\'\s>]', m.group(0)): return ok(m.group(1))
    return None


def parse_rss(src, content):
    f = feedparser.parse(content)
    rows = []
    for rank, e in enumerate(f.entries[: src["max_items"]], start=1):
        title = clean(e.get("title"), 300)
        link = e.get("link") or ""
        if not title or not link:
            continue
        raw_summary = e.get("summary") or ""
        summary = clean(raw_summary)
        metric = {}
        if src["id"] == "hackernews":
            m = re.search(r"Points:\s*(\d+)", raw_summary); c = re.search(r"#\s*Comments:\s*(\d+)", raw_summary)
            if m: metric["points"] = int(m.group(1))
            if c: metric["comments"] = int(c.group(1))
            summary = ""
        if e.get("hatena_bookmarkcount"):
            try: metric["bookmarks"] = int(e["hatena_bookmarkcount"])
            except ValueError: pass
        if "reddit.com" in link or summary.lower().startswith("submitted by") or summary == title:
            summary = ""
        if "news.google.com" in src["url"]:            # Google 뉴스 경유: 제목 끝 " - 매체명" 제거, 설명은 링크 묶음이라 버림
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title)
            summary = ""
        img = rss_img(e)
        if img: metric["img"] = img                          # 대표 사진 (DB 칸을 새로 만들지 않고 metric 에 담음)
        tg = [clean(x.get("term") or x.get("label") or "", 40) for x in (e.get("tags") or [])]
        tg = [x for x in dict.fromkeys(tg) if x and len(x) <= 40][:4]
        if tg: metric["tg"] = tg                             # 언론사가 붙인 분류 꼬리표(국제·경제·스포츠…) — 분야 가르기에 씀
        rows.append({
            "guid_hash": h(e.get("id") or link),
            "url": link,
            "title": title,
            "summary": summary or None,
            "published_at": to_iso(e.get("published_parsed") or e.get("updated_parsed")),
            "rank": rank,
            "metric": metric,
        })
    return rows


def parse_trends(src, content):
    f = feedparser.parse(content)
    day = kst_today()
    rows = []
    for rank, e in enumerate(f.entries[: src["max_items"]], start=1):
        kw = clean(e.get("title"), 120)
        if not kw:
            continue
        traffic = (e.get("ht_approx_traffic") or "").strip()
        tmin = int(re.sub(r"[^\d]", "", traffic) or 0) if traffic else None
        news_title = clean(e.get("ht_news_item_title"), 300)
        news_url = e.get("ht_news_item_url")
        rows.append({
            "guid_hash": h(f"{src['geo']}|{kw}|{day}"),     # 같은 검색어라도 날짜가 다르면 새로 기록
            "url": news_url or f"https://www.google.com/search?q={quote_plus(kw)}",
            "title": kw,
            "summary": news_title or None,
            "published_at": to_iso(e.get("published_parsed")),
            "rank": rank,
            "metric": {"approx_traffic": traffic, "traffic_min": tmin} if traffic else {},
        })
    return rows


def fetch_youtube(src):
    key = os.environ["YOUTUBE_API_KEY"]
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=25, params={
        "part": "snippet,statistics", "chart": "mostPopular", "regionCode": src["geo"],
        "maxResults": src["max_items"], "key": key})
    r.raise_for_status()
    rows = []
    for rank, v in enumerate(r.json().get("items", []), start=1):
        sn, st = v["snippet"], v.get("statistics", {})
        rows.append({
            "guid_hash": h(v["id"]),
            "url": f"https://www.youtube.com/watch?v={v['id']}",
            "title": clean(sn.get("title"), 300),
            "summary": clean(sn.get("channelTitle"), 120) or None,
            "published_at": sn.get("publishedAt"),
            "rank": rank,
            "metric": {k: int(st[k]) for k in ("viewCount", "likeCount", "commentCount") if k in st},
        })
    return rows


def fetch_source(src):
    """한 수집처 수집. 한 곳의 오류가 전체를 멈추지 않도록 예외를 결과로 돌려줌."""
    t0 = time.time()
    try:
        if src["method"] == "rss":
            is_reddit = "reddit.com" in src["url"]
            if is_reddit and reddit_api.enabled():          # 공식 API (GitHub 서버에서 RSS가 막히므로)
                rows = reddit_api.top_posts(src["url"], src["max_items"])
            else:
                rows = parse_rss(src, http_get(src["url"], REDDIT_UA if is_reddit else UA, retries=2 if is_reddit else 0))
        elif src["method"] == "google_trends":
            rows = parse_trends(src, http_get(f"https://trends.google.com/trending/rss?geo={src['geo']}"))
        elif src["method"] == "youtube":
            rows = fetch_youtube(src)
        else:
            return src, None, "미연결"
        if not rows:
            return src, None, "응답은 왔지만 글 0개"
        return src, rows, None
    except Exception as e:
        return src, None, f"{type(e).__name__}: {str(e)[:160]}"
    finally:
        src["_secs"] = round(time.time() - t0, 1)


def fetch_all(sources):
    runnable = [s for s in sources if s["status"] in ("active", "unstable")]
    reddit = [s for s in runnable if "reddit.com" in (s.get("url") or "")]
    others = [s for s in runnable if s not in reddit]
    results = []
    with ThreadPoolExecutor(8) as ex:
        fut = ex.map(fetch_source, others)
        for s in reddit:                         # Reddit 은 순차 + 간격 (429 방지)
            results.append(fetch_source(s))
            time.sleep(8)
        results += list(fut)
    return results


# ── 번역 예산 ─────────────────────────────────────────────
def run_budgets(db, slot):
    now = datetime.now(KST)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    runs_left = max(1, (days_in_month - now.day) * 2 + (2 if slot == "am" else 1))
    used_deepl_db, used_google = db.month_chars(month_start)
    u = deepl_month_usage(os.environ.get("DEEPL_API_KEY"))
    used_deepl = u[0] if u else used_deepl_db
    cap_deepl = min(DEEPL_MONTHLY_CAP, u[1] - 5000) if u else DEEPL_MONTHLY_CAP
    b_deepl = max(0, (cap_deepl - used_deepl) // runs_left)
    b_google = max(0, (GOOGLE_MONTHLY_CAP - used_google) // runs_left)
    return b_deepl, b_google, {"used_deepl_month": used_deepl, "used_google_month": used_google, "runs_left": runs_left}


KIND_PRIORITY = {"news": 0, "community": 0, "trend": 1, "video": 2}


def translate_rows(tr: Translator, rows: list[dict]):
    """rows: lang, title, summary, rank, source_id 포함. 제목 → (남으면) 상위 글 설명 순으로 번역."""
    rows = sorted(rows, key=lambda r: (KIND_PRIORITY.get(r["kind"], 3), r.get("rank") or 99))
    # 1) 제목: 예산 안에 들어가는 만큼 앞에서부터
    by_lang: dict[str, list] = {}
    budget = tr.available
    for r in rows:
        if r["lang"] == "ko":
            r["title_ko"] = r["title"]; continue
        if budget < len(r["title"]):
            continue
        budget -= len(r["title"])
        by_lang.setdefault(r["lang"], []).append(r)
    for lang, group in by_lang.items():
        res, eng = tr.translate([g["title"] for g in group], lang)
        if res:
            ts = now_iso()
            for g, t in zip(group, res):
                g.update(title_ko=t, translated_by=eng, translated_at=ts)
    # 2) 설명: 출처별 상위 N개
    by_lang = {}
    for r in rows:
        if r.get("title_ko") and r.get("summary") and (r.get("rank") or 99) <= SUMMARY_TRANSLATE_TOP:
            by_lang.setdefault(r["lang"], []).append(r)
    for lang, group in by_lang.items():
        texts = [g["summary"][:SUMMARY_TRANSLATE_CHARS] for g in group]
        res, eng = tr.translate(texts, lang)
        if res:
            for g, t in zip(group, res):
                g["summary_ko"] = t + ("…" if len(g["summary"]) > SUMMARY_TRANSLATE_CHARS else "")


# ── 메인 ────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", default="manual", choices=["am", "pm", "manual"])
    ap.add_argument("--local", help="Supabase 대신 JSON 파일에 저장 (테스트용)")
    ap.add_argument("--no-translate", action="store_true")
    ap.add_argument("--only", help="쉼표로 구분한 수집처 id 만 실행")
    args = ap.parse_args()

    db = get_db(args.local)
    sources = load_sources()
    db.upsert_sources([{k: v for k, v in s.items() if k in (
        "id", "lang", "country", "kind", "name", "method", "url", "homepage", "status", "tier", "note", "max_items")}
        for s in sources])
    if args.only:
        keep = set(args.only.split(","))
        sources = [s for s in sources if s["id"] in keep]

    run_id = db.start_run(args.slot)
    b_deepl, b_google, budget_info = (0, 0, {}) if args.no_translate else run_budgets(db, args.slot)
    tr = Translator.from_env(b_deepl, b_google)
    print(f"[run {run_id}] slot={args.slot} 번역 예산 DeepL {b_deepl:,}자 / Google {b_google:,}자 {budget_info}")

    results = fetch_all(sources)
    now = now_iso()
    stats = {"sources": {}, "budget": {"deepl": b_deepl, "google": b_google, **budget_info}}
    new_rows, existing_updates, snapshot_keys = [], [], []

    for src, rows, err in results:
        st = {"secs": src.get("_secs")}
        upd = {"last_checked_at": now}
        if err:
            st["error"] = err
            upd["last_error"] = err
            print(f"  ✗ {src['id']:<20} {err}")
        else:
            existing = db.existing_items(src["id"], [r["guid_hash"] for r in rows])
            n_new = 0
            for r in rows:
                if r["guid_hash"] in existing:
                    iid = existing[r["guid_hash"]]
                    existing_updates.append({"id": iid, "last_seen_at": now, "metric": r["metric"] or None})
                    snapshot_keys.append((iid, None, r["rank"], r["metric"]))
                else:
                    n_new += 1
                    new_rows.append({**r, "source_id": src["id"], "lang": src["lang"], "country": src["country"],
                                     "kind": src["kind"]})
            st.update(fetched=len(rows), new=n_new)
            upd.update(last_success_at=now, last_error=None, last_new_count=n_new)
            print(f"  ✓ {src['id']:<20} {len(rows):>3}개 (새 글 {n_new})")
        stats["sources"][src["id"]] = st
        db.update_source(src["id"], upd)

    # 번역 (새 글 우선, 남으면 지난 48시간 번역 대기분)
    if not args.no_translate and tr.available > 0:
        translate_rows(tr, new_rows)
        if tr.available > 500:
            since = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
            backlog = [b for b in db.untranslated_items(since) if b.get("kind") != "social"]
            for b in backlog:
                b["rank"] = b.get("first_rank")
            translate_rows(tr, backlog)
            done = [{"id": b["id"], "title_ko": b.get("title_ko"), "summary_ko": b.get("summary_ko"),
                     "translated_by": b.get("translated_by"), "translated_at": b.get("translated_at")}
                    for b in backlog if b.get("title_ko")]
            existing_updates += done
            stats["backlog_translated"] = len(done)

    # 저장
    inserted = []
    if new_rows:
        payload = []
        for r in new_rows:
            payload.append({
                "source_id": r["source_id"], "guid_hash": r["guid_hash"], "url": r["url"], "title": r["title"],
                "summary": r.get("summary"), "title_ko": r.get("title_ko"), "summary_ko": r.get("summary_ko"),
                "translated_by": r.get("translated_by"), "translated_at": r.get("translated_at"),
                "content_level": "summary" if r.get("summary") else "title",
                "lang": r["lang"], "country": r["country"], "kind": r["kind"],
                "published_at": r.get("published_at"), "first_rank": r["rank"], "metric": r.get("metric") or {},
                "first_seen_at": now, "last_seen_at": now,
            })
        inserted = db.insert_items(payload)
        key = {(r["source_id"], r["guid_hash"]): r for r in new_rows}
        for ins in inserted:
            r = key.get((ins["source_id"], ins["guid_hash"]))
            if r:
                snapshot_keys.append((ins["id"], None, r["rank"], r.get("metric") or {}))
    if existing_updates:
        db.bulk_update_items(existing_updates)
    db.insert_snapshots([{"item_id": i, "run_id": run_id, "rank": rk, "metric": m or {}}
                         for i, _, rk, m in snapshot_keys])

    # 사건 묶기: 최근 30시간 글 기준으로 오늘(한국시간) 사건 다시 계산
    since = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    recent = db.items_since(since, kinds=["news", "community"])
    stories = build_stories(recent, kst_today())
    db.replace_stories(kst_today(), stories)

    stats.update(new_items=len(inserted), stories=len(stories), translate_errors=tr.errors[:10],
                 chars=tr.used)
    db.finish_run(run_id, stats, tr.used["deepl"], tr.used["google"])
    if args.slot == "pm":
        stats["pruned"] = db.prune(45)
    if args.local:
        db.save()

    ok = sum(1 for s in stats["sources"].values() if "error" not in s)
    print(f"[run {run_id}] 완료: 수집처 {ok}/{len(stats['sources'])} 성공, 새 글 {len(inserted)}개, "
          f"사건 {len(stories)}개, 번역 DeepL {tr.used['deepl']:,}자 / Google {tr.used['google']:,}자")
    if tr.errors:
        print("  번역 오류:", tr.errors[:5])
    # 절반 이상 실패하면 Actions 에 빨간불
    if ok < len(stats["sources"]) / 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
