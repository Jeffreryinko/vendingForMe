"""tools_run.py — '도구' 탭 로봇 (GitHub Actions, 하루 4번). 토큰 0.

요즘 뜨는 AI·개발 도구, 오픈소스, 클로드 코드·바이브코딩 활용법을 원천에서 바로 모은다.
(쇼츠 해설 영상은 대개 이 원천들에 먼저 올라온 것을 며칠 뒤 다룬 것)

  gh   : GitHub 오늘의 인기(trending 페이지) + 최근 7일 새로 생겨 별이 빨리 붙는 저장소(검색 API)
         + 지난번보다 별이 얼마나 늘었나(_state/stars.tsv)로 '하루 +N'
  gn   : GeekNews(긱뉴스) — 한국어 요약, 번역 불필요                                   RSS
  hn   : Hacker News 'Show HN'(직접 만든 도구 자랑) + AI·개발 화제 글                  Algolia API
  yt   : 유튜브 채널 RSS(한도 안 씀) + 하루 한 번 검색(YOUTUBE_API_KEY 있을 때)
  list : 모음 목록(awesome-*) 저장소에 새로 추가된 줄 + 목록 전체 보관(모음집)
  hf   : Hugging Face Spaces 인기 앱(바로 써 보는 AI 데모)
  rd   : Reddit r/ClaudeAI 등 — REDDIT_CLIENT_ID/SECRET 있을 때만 (GitHub 서버에서는 공개 주소가 막힘)

번역은 AI 탭과 같은 NLLB(토큰 0). 분류·거르기 낱말은 robot/tools_sources.py.

출력 (data/tools/)
  now.json            지금 화면 (구역별 목록 + '지금 뜨는 것')
  days/<날짜>.json     그날 처음 본 것 (찾기·지난 날 보기용, 30일 보관)
  lists/<id>.json     모음집 전체
  _index.json / _meta.json / _health.json / _tr.json / _seen.json / _state/

  python robot/tools_run.py --no-translate    # 번역 없이 빨리 (확인용)
"""
from __future__ import annotations

import html, json, os, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests
import ai_run as A                       # 같은 도구 (get·clean·번역)를 씀
import tools_sources as T

ROOT = A.ROOT
OUT = ROOT / "data/tools"; DAYS = OUT / "days"; ST = OUT / "_state"; LISTS = OUT / "lists"
KST = A.KST
KEEP_DAYS = 30
get, clean, hid, rj, wj, log, now_iso, today = A.get, A.clean, A.hid, A.rj, A.wj, A.log, A.now_iso, A.today
BLOCK = re.compile(T.BLOCK, re.I)
CATS = [(c, n, re.compile(rx, re.I)) for c, n, rx in T.CATS]
HN_KEEP = re.compile(T.HN_KEEP, re.I)
YT_KEEP = re.compile(T.YT_KEEP, re.I)
YT_KEEP_EN = re.compile(T.YT_KEEP_EN, re.I)
HAN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]{3,}")
SEC_NAME = {"gh": "GitHub 급상승", "gn": "긱뉴스", "hn": "해커뉴스", "yt": "유튜브 해설", "ye": "영어 유튜브", "list": "모음집 새 항목", "hf": "써 보는 AI 앱", "rd": "레딧"}
SEC_HOME = {"gh": "https://github.com/trending", "gn": "https://news.hada.io", "hn": "https://news.ycombinator.com/show", "yt": "https://www.youtube.com", "ye": "https://www.youtube.com",
            "list": "https://github.com/hesreallyhim/awesome-claude-code", "hf": "https://huggingface.co/spaces", "rd": "https://www.reddit.com/r/ClaudeAI/"}


def ago_days(d):
    try: return (datetime.now(KST).date() - datetime.fromisoformat(d[:10]).date()).days
    except Exception: return 999


def cats_of(text):
    out = [c for c, _, rx in CATS if rx.search(text or "")]
    return out[:2] or ["etc"]


def gh_headers():
    hdr = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok: hdr["Authorization"] = f"Bearer {tok}"
    return hdr


# ───────── GitHub ─────────
def src_gh_trending():
    """github.com/trending — 오늘 별이 많이 붙은 저장소 25개 (페이지 읽기)"""
    h = get("https://github.com/trending?since=daily", headers={"Accept": "text/html"}).text
    out = []
    for blk in h.split('<article class="Box-row')[1:]:
        m = re.search(r"<h2[^>]*>.*?href=\"/([^\"/]+/[^\"/?#]+)\"", blk, re.S)
        if not m: continue
        full = m.group(1)
        d = re.search(r"<p class=\"col-9[^\"]*\">(.*?)</p>", blk, re.S)
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', blk)
        st = re.search(r'href="/' + re.escape(full) + r'/stargazers"[^>]*>.*?([\d,]+)\s*</a>', blk, re.S)
        td = re.search(r"([\d,]+)\s+stars?\s+today", blk)
        out.append({"full": full, "sum": clean(d.group(1) if d else "", 300), "lang": lang.group(1).strip() if lang else "",
                    "stars": int(st.group(1).replace(",", "")) if st else 0, "today": int(td.group(1).replace(",", "")) if td else 0})
    if not out: raise RuntimeError("trending 0개 (페이지 모양 바뀜?)")
    return out


def src_gh_new():
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    j = get("https://api.github.com/search/repositories", params={"q": f"created:>{since} stars:>80", "sort": "stars", "order": "desc", "per_page": 60}, headers=gh_headers()).json()
    out = []
    for r in j.get("items", []):
        if r.get("fork") or r.get("archived"): continue
        age = max((datetime.now(timezone.utc) - datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).total_seconds() / 86400, 1)
        out.append({"full": r["full_name"], "sum": clean(r.get("description"), 300), "lang": r.get("language") or "", "stars": r.get("stargazers_count", 0),
                    "created": (r.get("created_at") or "")[:10], "topics": (r.get("topics") or [])[:6], "perday": round(r.get("stargazers_count", 0) / age)})
    return out


def collect_gh(health, prev):
    stars = {}
    f = ST / "stars.tsv"
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            p = ln.split("\t")
            if len(p) == 3: stars[p[0]] = (int(p[1]), p[2])
    rows = {}
    try:
        tr = src_gh_trending(); health.pop("gh/trending", None); log(f"github 오늘의 인기 {len(tr)}개")
    except Exception as e:
        tr = []; log(f"github trending 못 읽음 (검색으로 대신): {str(e)[:80]}")       # 막혀도 고장으로 치지 않음 — 검색이 대신
    for r in tr:
        rows[r["full"]] = dict(r, kind="오늘의 인기", gain=r["today"])
    try:
        nw = src_gh_new(); health.pop("gh/search", None); log(f"github 새 저장소 {len(nw)}개")
    except Exception as e:
        nw = []; A_fail(health, "gh/search", e)
    for r in nw:
        if r["full"] in rows: rows[r["full"]].update({k: r[k] for k in ("created", "topics") if r.get(k)}); continue
        rows[r["full"]] = dict(r, kind="새로 뜬 저장소", gain=r["perday"])
    if not rows: return [dict(p, stale=True) for p in prev]
    # 지난번보다 늘어난 별 (6시간 넘게 지났을 때) → 더 정확한 '하루 +N'
    now = datetime.now(timezone.utc)
    for full, r in rows.items():
        if full in stars and r.get("stars"):
            s0, t0 = stars[full]
            try: dt = (now - datetime.fromisoformat(t0)).total_seconds() / 86400
            except Exception: dt = 0
            if dt >= 0.25 and r["stars"] >= s0 and not r.get("today"): r["gain"] = round((r["stars"] - s0) / dt)
        if r.get("stars") and (full not in stars or (now - datetime.fromisoformat(stars[full][1])).total_seconds() > 5 * 3600):
            stars[full] = (r["stars"], now.isoformat(timespec="seconds"))
    keep = sorted(stars.items(), key=lambda kv: kv[1][1], reverse=True)[:4000]
    ST.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(f"{k}\t{v[0]}\t{v[1]}" for k, v in sorted(keep)) + "\n", encoding="utf-8")
    out = []
    for full, r in rows.items():
        txt = " ".join([full, r.get("sum", ""), " ".join(r.get("topics", []))])
        if BLOCK.search(txt): continue
        out.append({"id": "g" + hid(full.lower()), "sec": "gh", "kind": r["kind"], "title": full.split("/")[1], "owner": full.split("/")[0], "sum": r.get("sum", ""),
                    "url": f"https://github.com/{full}", "stars": r.get("stars", 0), "gain": r.get("gain", 0), "lang": r.get("lang", ""), "created": r.get("created", ""),
                    "topics": r.get("topics", []), "cats": cats_of(txt), "en": True})
    out.sort(key=lambda o: -(o["gain"] or 0))
    return out[:50]


# ───────── 긱뉴스 ─────────
def src_gn():
    x = ET.fromstring(get("https://news.hada.io/rss/news").content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in x.findall("a:entry", ns):
        title = clean(e.findtext("a:title", namespaces=ns), 200)
        tid = clean(e.findtext("a:id", namespaces=ns), 200)
        m = re.search(r"id=(\d+)", tid)
        if not title or not m: continue
        body = e.findtext("a:content", namespaces=ns) or ""
        lis = [clean(li, 160) for li in re.findall(r"<li>(.*?)</li>", body, re.S)]
        lis = [l for l in lis if len(l) > 8]
        summ = " · ".join(lis[:3]) if lis else clean(body, 300)
        url = f"https://news.hada.io/topic?id={m.group(1)}"
        out.append({"id": "n" + m.group(1), "sec": "gn", "kind": "Show GN" if title.lower().startswith("show gn") else ("Show HN" if title.lower().startswith("show hn") else "긱뉴스"),
                    "title": title, "sum": summ[:360], "url": url, "date": A.parse_date(e.findtext("a:published", namespaces=ns) or "") or today(),
                    "cats": cats_of(title + " " + summ)})
    if not out: raise RuntimeError("0개")
    return out


# ───────── 해커뉴스 ─────────
def hn_search(tags, days, pts, n):
    t0 = int(time.time() - days * 86400)
    j = get("https://hn.algolia.com/api/v1/search", params={"tags": tags, "numericFilters": f"created_at_i>{t0},points>={pts}", "hitsPerPage": n}).json()
    return j.get("hits", [])


def src_hn():
    out, seen = [], set()
    for kind, tags, days, pts, n in (("Show HN", "show_hn", 4, 15, 60), ("화제", "story", 2, 120, 120)):
        for h in hn_search(tags, days, pts, n):
            title = clean(h.get("title"), 240); oid = h.get("objectID")
            if not title or oid in seen or BLOCK.search(title): continue
            if kind == "화제" and (title.lower().startswith("show hn") or not HN_KEEP.search(title)): continue
            seen.add(oid)
            disc = f"https://news.ycombinator.com/item?id={oid}"
            out.append({"id": "h" + oid, "sec": "hn", "kind": kind, "title": re.sub(r"^Show HN:\s*", "", title), "url": h.get("url") or disc, "disc": disc,
                        "pts": int(h.get("points") or 0), "cm": int(h.get("num_comments") or 0), "date": datetime.fromtimestamp(h.get("created_at_i") or time.time(), KST).strftime("%Y-%m-%d"),
                        "cats": cats_of(title), "en": True})
    out.sort(key=lambda o: (o["kind"] != "Show HN", -o["pts"]))
    shows = [o for o in out if o["kind"] == "Show HN"][:35]; tops = sorted([o for o in out if o["kind"] == "화제"], key=lambda o: -o["pts"])[:25]
    if not shows and not tops: raise RuntimeError("0개")
    return shows + tops


# ───────── 유튜브 ─────────
def iso_dur(s):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m: return 0
    d, h, mi, se = (int(x or 0) for x in m.groups()); return d * 86400 + h * 3600 + mi * 60 + se


def src_yt_channels(health, chans=None, keep=None):
    chans = chans or T.CHANNELS; keep = keep or YT_KEEP
    out = []
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
    for name, cid in chans:
        try:
            x = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}").content); health.pop(f"yt/{cid}", None)
        except Exception as e:
            A_fail(health, f"yt/{cid}", e); continue
        for e in x.findall("a:entry", ns):
            vid = e.findtext("yt:videoId", namespaces=ns); title = clean(e.findtext("a:title", namespaces=ns), 160)
            link = (e.find("a:link", ns).get("href") if e.find("a:link", ns) is not None else "") or ""
            g = e.find("m:group", ns); desc = clean(g.findtext("m:description", namespaces=ns) if g is not None else "", 300)
            st = g.find("m:community/m:statistics", ns) if g is not None else None
            date = A.parse_date(e.findtext("a:published", namespaces=ns) or "")
            if not vid or ago_days(date) > 14 or not keep.search(title) or BLOCK.search(title): continue
            out.append({"vid": vid, "title": title, "ch": name, "sum": desc, "date": date, "views": int(st.get("views") or 0) if st is not None else 0, "short": "/shorts/" in link})
        time.sleep(0.3)
    return out


def src_yt_search(cache, queries=None, lang="ko", region="KR"):
    queries = queries or T.YT_QUERIES
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key: return cache.get("items", [])
    if cache.get("day") == today(): return cache.get("items", [])                      # 검색은 하루 한 번만 (한도 아끼기)
    after = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    items, seen = [], set()
    for q in queries:
        try:
            r = requests.get("https://www.googleapis.com/youtube/v3/search", params={"part": "snippet", "q": q, "type": "video", "maxResults": 12, "key": key, "relevanceLanguage": lang,
                             "regionCode": region, "order": "viewCount", "publishedAfter": after, "safeSearch": "strict"}, timeout=30)
            r.raise_for_status()
        except Exception as e:
            log(f"유튜브 검색 실패 ({q}): {str(e)[:80]}"); break
        for v in r.json().get("items", []):
            vid = v["id"].get("videoId"); sn = v["snippet"]
            if not vid or vid in seen or BLOCK.search(sn.get("title", "")): continue
            seen.add(vid)
            items.append({"vid": vid, "title": clean(sn["title"], 160), "ch": clean(sn["channelTitle"], 60), "sum": clean(sn.get("description"), 300), "date": (sn.get("publishedAt") or "")[:10], "q": q})
    if items:                                                                            # 조회수·길이 (1단위/50개)
        for b in range(0, len(items), 50):
            chunk = items[b:b + 50]
            try:
                r = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "statistics,contentDetails", "id": ",".join(i["vid"] for i in chunk), "key": key}, timeout=30)
                info = {v["id"]: v for v in r.json().get("items", [])}
                for i in chunk:
                    v = info.get(i["vid"], {}); i["views"] = int((v.get("statistics") or {}).get("viewCount") or 0)
                    i["short"] = 0 < iso_dur((v.get("contentDetails") or {}).get("duration")) <= 180
            except Exception as e:
                log(f"유튜브 조회수 실패: {str(e)[:60]}")
        cache.update(day=today(), items=items)
    log(f"유튜브 검색 {len(items)}개")
    return items


def collect_yt(health, en=False):
    """en=False: 한국어 해설(칸 yt) / en=True: 영어 유튜브(칸 ye, 제목·설명은 NLLB 기계번역)"""
    sid = "ye" if en else "yt"; yc = rj(ST / f"{sid}.json", {})
    vids = src_yt_channels(health, T.CHANNELS_EN, YT_KEEP_EN) + src_yt_search(yc, T.YT_QUERIES_EN, "en", "US") if en else src_yt_channels(health) + src_yt_search(yc)
    if en: vids = [v for v in vids if not HAN.search(v["title"]) and not re.search(r"[가-힣]", v["title"])]   # 영어 칸엔 영어 영상만
    wj(ST / f"{sid}.json", yc)
    out, seen = [], set()
    for v in vids:
        if v["vid"] in seen: continue
        seen.add(v["vid"])
        out.append({"id": "y" + v["vid"], "sec": sid, "en": en, "kind": "쇼츠" if v.get("short") else "영상", "title": v["title"], "ch": v["ch"], "vid": v["vid"], "sum": v.get("sum", ""),
                    "url": f"https://www.youtube.com/{'shorts/' if v.get('short') else 'watch?v='}{v['vid']}", "date": v.get("date") or today(), "views": v.get("views", 0),
                    "cats": cats_of(v["title"])})                                             # 설명은 광고·링크가 많아 제목만
    out.sort(key=lambda o: -(o["views"] or 0) / max(ago_days(o["date"]) + 0.5, 0.5))      # 하루당 조회수 (새것 우대)
    return out[:60]


# ───────── 모음 목록 (awesome-*) ─────────
LINE = re.compile(r"^\s*[-*]\s+(?:\*\*)?\[(?:\*\*)?([^\]]{1,120}?)(?:\*\*)?\]\(([^)\s]+)\)(?:\*\*)?(.*)$")      # - [이름](주소) - 설명  /  - **[이름](주소)**  /  - [**이름**](주소)
TROW = re.compile(r"^\s*\|\s*(?:\*\*)?\[(?:\*\*)?([^\]]{1,120}?)(?:\*\*)?\]\(([^)\s]+)\)(?:\*\*)?\s*\|(.*)$")        # | **[이름](주소)** | 설명 |
def md_text(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)                                     # 배지 그림
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)                                 # 링크 → 글자
    s = re.sub(r"[`*_]", "", s)
    return clean(s, 300)


def parse_awesome(text, repo=""):
    rows, sec = [], ""
    for ln in text.splitlines():
        hm = re.match(r"^#{2,4}\s+(.*)", ln)
        if hm: sec = re.sub(r"\s*\([^)]*\)", "", md_text(re.sub(r"[^\w\s&·/,.()\[\]-]", "", hm.group(1)))).strip(" -"); continue
        m = LINE.match(ln); tm = None if m else TROW.match(ln)
        if not m and not tm: continue
        if m: name, url, rest = m.group(1).strip(), m.group(2).strip(), m.group(3)
        else: name, url, rest = tm.group(1).strip(), tm.group(2).strip(), " - " + tm.group(3).split("|")[0]
        if url.startswith("#") or url.startswith("mailto:") or "img.shields.io" in url: continue
        if not url.startswith("http"): url = f"https://github.com/{repo}/blob/HEAD/{url.lstrip('./')}"   # 저장소 안 상대 주소
        if re.search(r"(?i)table of contents|^contents$", sec) and len(rest.strip()) < 5: continue
        rest = re.sub(r"^\s*by\s+\[[^\]]*\]\([^)]*\)", "", rest)
        rest = re.sub(r"^\s*(\([^)]*\)\s*)?[-–—:]\s*", "", rest)
        desc = md_text(rest)
        if len(desc) < 6 and not name: continue
        rows.append({"name": md_text(name)[:100], "url": url, "desc": desc, "sec": sec[:60]})
    seen, out = set(), []
    for r in rows:
        k = r["url"].rstrip("/").lower()
        if k in seen: continue
        seen.add(k); out.append(r)
    return out


def collect_lists(health):
    known = rj(ST / "awesome.json", {})
    new_items, meta = [], []
    for lid, name, repo, path, full in T.AWESOME:
        try:
            txt = get(f"https://raw.githubusercontent.com/{repo}/HEAD/{path}").text; health.pop(f"list/{lid}", None)
        except Exception as e:
            A_fail(health, f"list/{lid}", e); continue
        rows = parse_awesome(txt, repo)
        first_time = lid not in known
        seen = known.setdefault(lid, {})
        for r in rows:
            k = hid(r["url"].rstrip("/").lower())
            if k not in seen: seen[k] = "0" if first_time else today()                  # 처음 돌 때 있던 건 '새 항목' 아님
            r["first"] = seen[k]
            if r["first"] != "0" and ago_days(r["first"]) <= 30 and not BLOCK.search(r["name"] + r["desc"]):
                new_items.append({"id": "l" + k, "sec": "list", "kind": name, "list": lid, "title": r["name"], "sum": r["desc"], "url": r["url"], "date": r["first"], "part": r["sec"],
                                  "cats": cats_of(r["name"] + " " + r["desc"]), "en": True})
        meta.append({"id": lid, "name": name, "repo": repo, "n": len(rows), "full": full})
        if full: wj(LISTS / f"{lid}.json", {"id": lid, "name": name, "repo": repo, "at": now_iso(), "rows": rows})
        log(f"모음 {lid}: {len(rows)}줄" + (" (처음)" if first_time else ""))
        time.sleep(0.5)
    wj(ST / "awesome.json", known)
    new_items.sort(key=lambda o: o["date"], reverse=True)
    return new_items[:80], meta


# ───────── Hugging Face Spaces ─────────
def src_hf():
    j = get("https://huggingface.co/api/spaces", params={"sort": "trendingScore", "limit": 60, "full": "true"}).json()
    out = []
    for s in j:
        cd = s.get("cardData") or {}
        title = clean(cd.get("title") or s["id"].split("/")[-1], 100); desc = clean(cd.get("short_description"), 200)
        if BLOCK.search(" ".join([s["id"], title, desc, " ".join(s.get("tags") or [])])): continue
        out.append({"id": "f" + hid(s["id"]), "sec": "hf", "kind": "AI 앱", "title": title, "owner": s["id"].split("/")[0], "sum": desc, "emoji": cd.get("emoji") or "",
                    "url": f"https://huggingface.co/spaces/{s['id']}", "likes": int(s.get("likes") or 0), "trend": int(s.get("trendingScore") or 0),
                    "created": (s.get("createdAt") or "")[:10], "cats": cats_of(title + " " + desc), "en": True})
    if not out: raise RuntimeError("0개")
    return out[:30]


# ───────── 레딧 (키 있을 때만) ─────────
def src_reddit():
    from crawler import reddit_api as R
    if not R.enabled(): return None
    out = []
    for sub in ("ClaudeAI", "ClaudeCode", "vibecoding", "LocalLLaMA"):
        try: j = R._get(f"/r/{sub}/top", {"t": "day", "limit": 10, "raw_json": 1})
        except Exception as e: log(f"레딧 {sub} 실패: {str(e)[:60]}"); continue
        for ch in j.get("data", {}).get("children", []):
            d = ch.get("data", {}); title = clean(d.get("title"), 220)
            if not title or d.get("stickied") or d.get("over_18") or BLOCK.search(title): continue
            out.append({"id": "r" + d.get("id", hid(title)), "sec": "rd", "kind": "r/" + sub, "title": title, "sum": clean(d.get("selftext"), 300),
                        "url": "https://www.reddit.com" + d.get("permalink", ""), "pts": int(d.get("score") or 0), "cm": int(d.get("num_comments") or 0),
                        "date": datetime.fromtimestamp(d.get("created_utc") or time.time(), KST).strftime("%Y-%m-%d"), "cats": cats_of(title), "en": True})
    out.sort(key=lambda o: -o["pts"])
    return out[:30]


# ───────── 공통 ─────────
def A_fail(health, key, e):
    err = f"{type(e).__name__}: {str(e)[:80]}"
    h = health.setdefault(key, {"since": now_iso(), "n": 0}); h["n"] += 1; h["err"] = err; h["last"] = now_iso()
    log(f"실패 {key}: {err}")


HEAT_W = {"gh": 1.0, "hn": .9, "gn": .9, "yt": .85, "ye": .8, "list": .75, "hf": .6, "rd": .7}
def heat(sec, items):
    """구역 안 순위 → 0~100 열기. 오래된 것은 깎음"""
    n = len(items)
    for i, it in enumerate(items):
        base = 100 * (1 - i / max(n, 1)) * HEAT_W.get(sec, .6)
        age = ago_days(it.get("date") or it.get("first") or today())
        it["heat"] = round(base * (1 if age <= 1 else .7 if age <= 3 else .4))


def main():
    t0 = time.time(); deadline = t0 + int(os.environ.get("TOOLS_MAX_MINUTES", "40")) * 60
    for d in (OUT, DAYS, ST, LISTS): d.mkdir(parents=True, exist_ok=True)
    health = rj(OUT / "_health.json", {}); day = today()
    prev = rj(OUT / "now.json", {}).get("sec", {})

    sec = {}
    sec["gh"] = collect_gh(health, prev.get("gh", []))
    for key, fn in (("gn", src_gn), ("hn", src_hn), ("hf", src_hf)):
        try:
            sec[key] = fn(); health.pop(f"{key}/main", None); log(f"{key}: {len(sec[key])}개")
        except Exception as e:
            A_fail(health, f"{key}/main", e); sec[key] = [dict(p, stale=True) for p in prev.get(key, [])]
    # 긱뉴스는 RSS가 20개뿐 → 지난 7일치를 이어 붙임
    have = {p["id"] for p in sec["gn"]}
    sec["gn"] = sorted(sec["gn"] + [p for p in prev.get("gn", []) if p["id"] not in have and ago_days(p.get("date", "")) <= 7], key=lambda p: p.get("date", ""), reverse=True)[:80]
    sec["yt"] = collect_yt(health) or prev.get("yt", [])
    sec["ye"] = collect_yt(health, en=True) or prev.get("ye", [])
    ko_ids = {p["id"] for p in sec["yt"]}; sec["ye"] = [p for p in sec["ye"] if p["id"] not in ko_ids]
    sec["list"], lists_meta = collect_lists(health)
    try:
        rd = src_reddit()
        if rd is not None: sec["rd"] = rd
    except Exception as e:
        A_fail(health, "rd/main", e)

    # 처음 본 날 · 새것 표시
    seen = rj(OUT / "_seen.json", {}); cut = (datetime.now(KST) - timedelta(days=KEEP_DAYS + 5)).strftime("%Y-%m-%d")
    seen = {k: v for k, v in seen.items() if v >= cut}
    for k, lst in sec.items():
        for p in lst:
            p["first"] = seen.setdefault(p["id"], day)
            if not p.get("date"): p["date"] = p["first"]
            p["new"] = p["first"] == day
    wj(OUT / "_seen.json", seen)

    # 번역 (영문 → 한국어): 해커뉴스·레딧 제목, GitHub·앱·모음 설명
    mem = rj(OUT / "_tr.json", {}); run = A.nllb()
    jobs = []                                                                           # (항목, 칸, 원문)
    for k, lst in sec.items():
        for p in lst:
            if not p.get("en"): continue
            if HAN.search(p.get("title", "") + p.get("sum", "")): continue                 # 중국어·일본어 글은 NLLB(영어→한) 대신 화면의 번역 링크로
            if k in ("hn", "rd", "ye"): jobs.append((p, "ko", p["title"]))
            if p.get("sum"): jobs.append((p, "ksum", p["sum"][:400]))
    full_lists = {}
    for m in lists_meta:
        if m["full"]:
            full_lists[m["id"]] = rj(LISTS / f"{m['id']}.json", {})
            for r in full_lists[m["id"]].get("rows", []):
                if r.get("desc"): jobs.append((r, "ko", r["desc"][:400]))
    # 유튜브 베스트 댓글 5개 (영상마다 할당량 1, 12시간 기억). 영어 댓글은 같이 번역
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent)); from ytcomments import Comments
        CM = Comments(OUT / "_state/cm.json", os.environ.get("YOUTUBE_API_KEY"), budget=120)
        for k in ("yt", "ye"):
            for p in sec.get(k, [])[:40]:
                p["cm"] = CM.get(p.get("vid"))
                for c in p["cm"]:
                    if not HAN.search(c["t"]) and not re.search(r"[가-힣]", c["t"]): jobs.append((c, "ko", c["t"][:300]))
        CM.save()
    except Exception as e: log(f"베스트 댓글 실패 — 건너뜀: {e}")
    res = A.translate_texts(run, [j[2] for j in jobs], mem, deadline)
    for (p, field, _), v in zip(jobs, res):
        if v: p[field] = v
    for lid, d in full_lists.items():
        if d: wj(LISTS / f"{lid}.json", d)
    if len(mem) > 40000: mem = dict(list(mem.items())[-30000:])
    if run is not None or mem: wj(OUT / "_tr.json", mem)

    # 열기 · 지금 뜨는 것
    for k, lst in sec.items(): heat(k, lst)
    pool = [p for lst in sec.values() for p in lst if ago_days(p.get("first", day)) <= 2 and not p.get("stale")]
    pool.sort(key=lambda p: -p.get("heat", 0))
    hot, per = [], {}
    for p in pool:
        if per.get(p["sec"], 0) >= 4: continue
        per[p["sec"]] = per.get(p["sec"], 0) + 1; hot.append(p["id"])
        if len(hot) >= 18: break

    try:                                                          # 대표 사진 (토큰 0, 한 번 본 글은 _state/img.json 에 기억)
        sys.path.insert(0, str(Path(__file__).resolve().parent)); from ogimg import Photos
        ph = Photos(OUT / "_state/img.json", budget=150)
        for k, lst in sec.items():
            for p in lst:
                if p.get("vid") or p.get("img"): continue
                m = re.match(r"https://github\.com/([^/]+/[^/#?]+)", p.get("url") or "")
                if k == "gh" and m: p["img"] = f"https://opengraph.githubassets.com/1/{m.group(1)}"   # 깃허브가 만들어 주는 저장소 카드 그림
                else:
                    u = ph.get(p.get("url"))
                    if u: p["img"] = u
            if k != "gh": Photos.drop_logos(lst)
        ph.save()
    except Exception as e: log(f"대표 사진 실패 — 건너뜀: {e}")
    now = {"at": now_iso(), "day": day, "hot": hot, "sec": sec}
    wj(OUT / "now.json", now)

    # 그날 처음 본 것 (찾기용) — 같은 날 여러 번 돌면 이어 붙임
    df = DAYS / f"{day}.json"; dd = rj(df, {"day": day, "items": []}); ids = {p["id"] for p in dd["items"]}
    keep = ("id", "sec", "kind", "title", "ko", "sum", "ksum", "url", "date", "first", "cats", "stars", "gain", "pts", "views", "ch", "vid", "owner", "emoji", "likes", "disc", "lang")
    for lst in sec.values():
        for p in lst:
            if p["first"] == day and p["id"] not in ids:
                dd["items"].append({k: p[k] for k in keep if p.get(k) not in (None, "", [], 0)}); ids.add(p["id"])
    wj(df, dd)
    cutd = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    for f in DAYS.glob("????-??-??.json"):
        if f.stem < cutd: f.unlink(); log(f"지움: {f.stem}")

    broken = {k: v for k, v in health.items() if v.get("n", 0) >= 6}                    # 하루 4번 × 1.5일 넘게 계속 실패
    counts = {k: len(v) for k, v in sec.items()}
    idx = {"at": now_iso(), "today": day, "days": sorted(f.stem for f in DAYS.glob("????-??-??.json")), "broken": broken, "counts": counts,
           "new": sum(1 for lst in sec.values() for p in lst if p.get("new")), "secs": {k: [SEC_NAME[k], SEC_HOME[k]] for k in sec}, "lists": lists_meta,
           "cats": [[c, n] for c, n, _ in CATS] + [["etc", "기타"]], "channels": [n for n, _ in T.CHANNELS], "channelsEn": [n for n, _ in T.CHANNELS_EN], "ytKey": bool(os.environ.get("YOUTUBE_API_KEY")), "translated": run is not None}
    wj(OUT / "_index.json", idx); wj(OUT / "_health.json", health)
    wj(OUT / "_meta.json", {"updatedAt": now_iso(), "by": "tools-robot", "label": datetime.now(KST).strftime("%m월 %d일 %H시판")})
    log(f"끝 {round(time.time() - t0)}초 · " + " · ".join(f"{k} {v}" for k, v in counts.items()) + f" · 고장 {len(broken)}곳")


if __name__ == "__main__":
    main()
