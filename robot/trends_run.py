"""trends_run.py — 트렌드 로봇 (GitHub Actions, 3시간마다). 토큰 0.

나라별로 "지금 사람들이 뭘 찾나"를 모읍니다.
  google : 구글 트렌드 공식 RSS (나라별 급상승 검색어)           튼튼
  wiki   : 위키백과 어제 많이 본 문서 (공식 API, 하루 1번 갱신)   튼튼
  yt     : 유튜브 인기 (뉴스 분류 + 전체) — YOUTUBE_API_KEY 있을 때만
  x      : X(트위터) 트렌드 — trends24.in (민간 집계)             깨질 수 있음
  local  : 한국 시그널(signal.bz) / 일본 야후 리얼타임 / 중국 바이두·웨이보   깨질 수 있음

출력 (data/trends/)
  _index.json          나라 목록·갱신 시각·세계 공통 띠·출처 건강
  <CC>.json            나라 하나의 모든 출처
  hist/<CC>_<날짜>.json  하루 스냅샷(7일 보관), hist/_top1.json 그 이전은 1위만
  _tr.json / _seen.json / _usage.json  번역 기억 / 처음 본 시각 / 번역 사용량
"""
from __future__ import annotations

import json, os, re, sys, time, html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus, unquote
import xml.etree.ElementTree as ET

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler.translate import Translator, deepl_month_usage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/trends"; HIST = OUT / "hist"
KST = timezone(timedelta(hours=9))
UA = "vendingForMe-bot/1.0 (personal, non-commercial; +https://github.com/Jeffreryinko/vendingForMe)"
DRY = "--dry" in sys.argv
RUNS_PER_DAY = 8
TREND_MONTH_CAP = int(os.environ.get("TRENDS_MONTHLY_CAP", "150000"))   # 트렌드가 쓸 DeepL 글자 (월)
TOP_TR = 5                                                              # 출처마다 번역하는 개수
KEEP_DAYS = 7

# cc: 이름, 구글 geo, 위키 언어, X(trends24) 주소, 현지 출처, 원문 언어
C = {
 "KR": ("한국",      "KR", "ko", "korea",          ["signal"],        "ko"),
 "US": ("미국",      "US", "en", "united-states",  [],                "en"),
 "JP": ("일본",      "JP", "ja", "japan",          ["yahoojp"],       "ja"),
 "CN": ("중국",      None, "zh", None,             ["baidu","weibo"], "zh"),
 "GB": ("영국",      "GB", "en", "united-kingdom", [],                "en"),
 "DE": ("독일",      "DE", "de", "germany",        [],                "de"),
 "FR": ("프랑스",    "FR", "fr", "france",         [],                "fr"),
 "IN": ("인도",      "IN", "en", "india",          [],                "en"),
 "BR": ("브라질",    "BR", "pt", "brazil",         [],                "pt"),
 "ID": ("인도네시아","ID", "id", "indonesia",      [],                "id"),
 "RU": ("러시아",    "RU", "ru", "russia",         [],                "ru"),
 "TW": ("대만",      "TW", "zh", None,         [],                "zh"),
 "VN": ("베트남",    "VN", "vi", "vietnam",        [],                "vi"),
 "MX": ("멕시코",    "MX", "es", "mexico",         [],                "es"),
 "AR": ("아르헨티나","AR", "es", "argentina",      [],                "es"),
 "CL": ("칠레",      "CL", "es", "chile",          [],                "es"),
 "CO": ("콜롬비아",  "CO", "es", "colombia",       [],                "es"),
 "PE": ("페루",      "PE", "es", "peru",           [],                "es"),
 "NG": ("나이지리아","NG", "en", "nigeria",        [],                "en"),
 "ZA": ("남아공",    "ZA", "en", "south-africa",   [],                "en"),
 "EG": ("이집트",    "EG", "ar", "egypt",          [],                "ar"),
 "CA": ("캐나다",    "CA", "en", "canada",         [],                "en"),
}
SRC_NAME = {"google":"구글 급상승", "wiki":"위키백과 어제 많이 본", "yt":"유튜브 인기", "x":"X 트렌드",
            "signal":"시그널 실시간 (네이버·다음 등 집계)", "yahoojp":"야후재팬 리얼타임", "baidu":"바이두 핫검색", "weibo":"웨이보 핫검색"}
SRC_HOME = {"google":"https://trends.google.com/trending?geo={geo}", "wiki":"https://{lang}.wikipedia.org", "yt":"https://www.youtube.com/feed/trending",
            "x":"https://trends24.in/{slug}/", "signal":"https://signal.bz/news", "yahoojp":"https://search.yahoo.co.jp/realtime",
            "baidu":"https://top.baidu.com/board?tab=realtime", "weibo":"https://s.weibo.com/top/summary"}


def log(*a): print(datetime.now(KST).strftime("%H:%M:%S"), *a, flush=True)
def rj(p, d=None):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d
def wj(p, o): Path(p).parent.mkdir(parents=True, exist_ok=True); Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
def now_iso(): return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
def clean(s, n=120): return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()[:n]


def get(url, retries=1, **kw):
    for i in range(retries + 1):
        r = requests.get(url, headers={"User-Agent": UA, **kw.pop("headers", {})}, timeout=30, **kw)
        if r.status_code in (429, 503) and i < retries: time.sleep(15 * (i + 1)); continue
        r.raise_for_status(); return r


# ───────── 출처별 수집: 반환은 [{kw, url, n(규모·조회수 등), sub(부제), tag}] ─────────
def src_google(cc):
    geo = C[cc][1]
    if not geo: return None
    x = ET.fromstring(get(f"https://trends.google.com/trending/rss?geo={geo}").content)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for it in x.iter("item"):
        kw = clean(it.findtext("title"))
        if not kw: continue
        traffic = clean(it.findtext("ht:approx_traffic", namespaces=ns))
        news = [{"t": clean(n.findtext("ht:news_item_title", namespaces=ns), 160), "u": n.findtext("ht:news_item_url", namespaces=ns),
                 "s": clean(n.findtext("ht:news_item_source", namespaces=ns), 40)} for n in it.findall("ht:news_item", ns)][:3]
        out.append({"kw": kw, "url": f"https://www.google.com/search?q={quote_plus(kw)}", "n": traffic, "news": news})
    return out[:20]


WIKI_SKIP = re.compile(r"^(Main_Page|Special:|Wikipedia:|File:|Help:|Portal:|Talk:|Category:|Template:|User:|Draft:|-$|메인_페이지|특수:|위키백과:|파일:|분류:|틀:|メインページ|特別:|Wikipedia:|Википедия:|Заглавная_страница|Wikipédia:|Página_principal|Pagina_principale|Hauptseite|Halaman_Utama|Trang_Chính|首页|Wikipedia:首页|الصفحة_الرئيسية)", re.I)
_wiki_cache = {}
def src_wiki(cc):
    lang = C[cc][2]
    if lang in _wiki_cache: return _wiki_cache[lang]
    def day(d): return get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{lang}.wikipedia/all-access/{d:%Y/%m/%d}").json()["items"][0]["articles"]
    y = datetime.now(timezone.utc) - timedelta(days=1); yy = y - timedelta(days=1)
    a = {r["article"]: r["views"] for r in day(y) if not WIKI_SKIP.match(r["article"])}
    try: b = {r["article"]: r["views"] for r in day(yy)}
    except Exception: b = {}
    # 어제보다 많이 뛴 순서 (전날 자료 없으면 조회수 순)
    rows = sorted(a.items(), key=lambda kv: (kv[1] - b.get(kv[0], 0)) if b else kv[1], reverse=True)
    out = [{"kw": k.replace("_", " "), "url": f"https://{lang}.wikipedia.org/wiki/{quote_plus(k)}", "n": f"{v:,}회", "sub": (f"어제보다 +{v - b[k]:,}" if k in b else "새로 등장")} for k, v in rows[:20]]
    _wiki_cache[lang] = out
    return out


def src_yt(cc):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key: return None
    def pull(cat=None):
        p = {"part": "snippet,statistics", "chart": "mostPopular", "regionCode": cc, "maxResults": 20, "key": key}
        if cat: p["videoCategoryId"] = cat
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params=p, timeout=30); r.raise_for_status()
        return [{"kw": clean(v["snippet"]["title"], 100), "url": f"https://www.youtube.com/watch?v={v['id']}", "n": f"{int(v.get('statistics', {}).get('viewCount', 0)):,}회",
                 "sub": clean(v["snippet"]["channelTitle"], 40), "img": v["snippet"]["thumbnails"].get("medium", {}).get("url")} for v in r.json().get("items", [])]
    try: news = pull("25")
    except Exception: news = []
    allv = pull()
    for v in news: v["tag"] = "뉴스"
    return (news + [v for v in allv if v["url"] not in {n["url"] for n in news}])[:30]


def src_x(cc):
    slug = C[cc][3]
    if not slug: return None
    h = get(f"https://trends24.in/{slug}/").content.decode("utf-8", "replace")
    m = re.search(r"<ol class=trend-card__list>(.*?)</ol>", h, re.S)
    if not m: raise RuntimeError("목록 못 찾음")
    out = []
    for a, cnt in re.findall(r'class=trend-link>([^<]+)</a><span class=tweet-count data-count="?([^">]*)"?', m.group(1)):
        kw = clean(a); n = cnt.strip()
        out.append({"kw": kw, "url": f"https://x.com/search?q={quote_plus(kw)}", "n": (f"{int(n):,}건" if n.isdigit() else "")})
    return out[:20]


def src_signal(cc):
    j = get("https://api.signal.bz/news/realtime").json()
    st = {"n": "NEW", "u": "↑", "d": "↓", "s": ""}
    return [{"kw": clean(r["keyword"]), "url": f"https://search.naver.com/search.naver?query={quote_plus(r['keyword'])}", "n": "", "tag": st.get(r.get("state"), "")} for r in j.get("top10", [])]


def src_yahoojp(cc):
    h = get("https://search.yahoo.co.jp/realtime").text
    i = h.find("__NEXT_DATA__"); j = h.find("</script>", i)
    d = json.loads(h[h.find(">", i) + 1:j])
    items = d["props"]["pageProps"]["pageData"]["buzzTrend"]["items"]
    return [{"kw": clean(r["query"]), "url": "https://search.yahoo.co.jp" + r["url"], "n": (f"{r['tweetCount']}건" if r.get("tweetCount") else ""), "sub": clean(r.get("genre"), 20),
             "tag": ("↑" if r.get("rankUp") else "")} for r in items[:20]]


def src_baidu(cc):
    h = get("https://top.baidu.com/board?tab=realtime").content.decode("utf-8", "replace")
    seen, out = set(), []
    for s, u, w in re.findall(r'"hotScore":"(\d+)".{0,1200}?"rawUrl":"([^"]+)".{0,400}?"word":"([^"]+)"', h, re.S):
        w = clean(w)
        if w in seen: continue
        seen.add(w); out.append({"kw": w, "url": u.replace("\\/", "/"), "n": f"{int(s):,}"})
    if not out: raise RuntimeError("목록 못 찾음")
    return out[:20]


def src_weibo(cc):
    # 웨이보는 로그인 없이 막혀 있어 공개 보관소(justjavac/weibo-trending-hot-search, 매시간 갱신)에서 오늘 등장한 핫검색을 받습니다
    d = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    j = get(f"https://raw.githubusercontent.com/justjavac/weibo-trending-hot-search/master/raw/{d}.json").json()
    rows = list(reversed(j))[:20]
    return [{"kw": clean(r["title"]), "url": "https://s.weibo.com" + r["url"], "n": "", "sub": "오늘 등장 · 최근순"} for r in rows]


SRC_FN = {"google": src_google, "wiki": src_wiki, "yt": src_yt, "x": src_x, "signal": src_signal, "yahoojp": src_yahoojp, "baidu": src_baidu, "weibo": src_weibo}


# ───────── 번역 (TOP5만, 기억해서 다시 안 함) ─────────
def translator():
    usage = rj(OUT / "_usage.json", {}); mk = datetime.now(KST).strftime("%Y-%m")
    used = usage.get(mk, {"deepl": 0, "google": 0})
    now = datetime.now(KST); import calendar
    runs_left = max(1, (calendar.monthrange(now.year, now.month)[1] - now.day) * RUNS_PER_DAY + (RUNS_PER_DAY - now.hour // 3))
    cap = TREND_MONTH_CAP
    du = deepl_month_usage(os.environ.get("DEEPL_API_KEY")) if not DRY else None
    if du: cap = min(cap, du[1] - du[0] - 5000 + used["deepl"])      # DeepL 전체 남은 양도 넘지 않게
    b = min(max(0, cap - used["deepl"]), max(4000, (cap - used["deepl"]) // runs_left))   # 회차당 최소 4,000자 (첫 회차·새 검색어 많은 날 대비)
    if DRY: b = 10 ** 7
    tr = Translator.from_env(b, max(0, (100000 - used["google"]) // runs_left))
    log(f"번역 예산 이번 회차 DeepL {b:,}자 (이달 트렌드 사용 {used['deepl']:,})")
    return tr, mk, usage


def translate_all(data, tr):
    mem = rj(OUT / "_tr.json", {})
    todo = {}                                                     # lang -> set(kw)
    for cc, d in data.items():
        lang = C[cc][5]
        if lang == "ko": continue
        for s, blk in d["src"].items():
            for it in (blk.get("items") or [])[:TOP_TR]:
                if it["kw"] not in mem: todo.setdefault(lang, set()).add(it["kw"])
    for lang, kws in todo.items():
        kws = sorted(kws); fit, used = [], 0
        for k in kws:                                             # 예산에 들어가는 만큼만 (나머지는 다음 회차)
            if used + len(k) > tr.available: break
            fit.append(k); used += len(k)
        kws = fit
        if not kws: log(f"번역 {lang}: 예산 부족, 다음 회차"); continue
        res, eng = tr.translate(kws, lang) if not DRY else ([f"[번역]{k}" for k in kws], "dry")
        if res:
            for k, v in zip(kws, res): mem[k] = v
            log(f"번역 {lang}: {len(kws)}개 ({eng})")
        else: log(f"번역 {lang}: 예산 부족, 원문 유지")
    for cc, d in data.items():
        for s, blk in d["src"].items():
            for it in (blk.get("items") or []):
                if it["kw"] in mem and C[cc][5] != "ko": it["ko"] = mem[it["kw"]]
    if len(mem) > 4000: mem = dict(list(mem.items())[-3000:])
    wj(OUT / "_tr.json", mem)


# ───────── NEW 표시·세계 공통·보관 ─────────
def mark_seen(data):
    seen = rj(OUT / "_seen.json", {}); now = now_iso(); cutoff = (datetime.now(KST) - timedelta(days=14)).strftime("%Y-%m-%dT")
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    for cc, d in data.items():
        for s, blk in d["src"].items():
            for it in (blk.get("items") or []):
                k = f"{cc}|{s}|{it['kw']}"
                it["since"] = seen.setdefault(k, now)
    wj(OUT / "_seen.json", seen)


def norm(s): return re.sub(r"[\s\W_]+", "", str(s or "")).lower()
def world_band(data):
    hits = {}
    for cc, d in data.items():
        for s, blk in d["src"].items():
            if s == "wiki": continue
            for it in (blk.get("items") or [])[:10]:
                for key in {norm(it["kw"]), norm(it.get("ko"))} - {""}:
                    if len(key) < 2: continue
                    e = hits.setdefault(key, {"ko": it.get("ko") or it["kw"], "kw": it["kw"], "c": {}})
                    e["c"][cc] = s
    band = [{"ko": e["ko"], "kw": e["kw"], "cc": sorted(e["c"]), "n": len(e["c"]), "g": sum(1 for v in e["c"].values() if v == "google")} for e in hits.values() if len(e["c"]) >= 3]
    band.sort(key=lambda x: (-x["g"], -x["n"]))
    out, used = [], set()
    for b in band:                                                # 같은 뜻이 번역/원문으로 두 번 잡히면 하나만
        k = norm(b["ko"])
        if k in used: continue
        used.add(k); out.append(b)
    return out[:12]


def archive(data):
    today = datetime.now(KST).strftime("%Y-%m-%d")
    for cc, d in data.items():
        wj(HIST / f"{cc}_{today}.json", d)
    top1 = rj(HIST / "_top1.json", {})
    cutoff = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    for f in HIST.glob("??_*.json"):
        day = f.stem[3:]
        if day < cutoff:
            d = rj(f, {})
            top1.setdefault(day, {})[f.stem[:2]] = {s: ((b.get("items") or [{}])[0].get("ko") or (b.get("items") or [{}])[0].get("kw")) for s, b in d.get("src", {}).items()}
            f.unlink()
    wj(HIST / "_top1.json", top1)


# ───────── 본체 ─────────
def main():
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    prev = {cc: rj(OUT / f"{cc}.json", {}) for cc in C}
    health = rj(OUT / "_health.json", {})
    data = {}
    wiki_done_today = (rj(OUT / "_index.json", {}).get("wikiDay") == datetime.now(KST).strftime("%Y-%m-%d"))
    for cc, (name, geo, lang, slug, local, _) in C.items():
        srcs = [s for s in ["google", "wiki", "yt", "x"] + local if not (s == "google" and not geo) and not (s == "x" and not slug)]
        d = {"cc": cc, "name": name, "at": now_iso(), "src": {}}
        for s in srcs:
            old = (prev[cc].get("src") or {}).get(s) or {}
            blk = {"name": SRC_NAME[s], "home": SRC_HOME[s].format(geo=geo, lang=lang, slug=slug), "at": now_iso(), "ok": True}
            if s == "wiki" and wiki_done_today and old.get("items"):
                d["src"][s] = old; continue
            try:
                items = SRC_FN[s](cc)
                if items is None:                                     # 키 없음 등: 출처 자체를 표시만
                    blk.update(ok=False, err="키 필요" if s == "yt" else "미지원", items=[]); d["src"][s] = blk; continue
                if not items: raise RuntimeError("0개")
                blk["items"] = items; health.pop(f"{cc}/{s}", None)
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:80]}"
                h = health.setdefault(f"{cc}/{s}", {"since": now_iso(), "n": 0}); h["n"] += 1; h["err"] = err; h["last"] = now_iso()
                log(f"실패 {cc}/{s}: {err}")
                if old.get("items"):                                  # 직전 성공본 유지 + 시각 표시
                    blk.update(items=old["items"], at=old.get("at"), ok=False, stale=True, err=err)
                else: blk.update(items=[], ok=False, err=err)
            d["src"][s] = blk
            time.sleep(0.5)
        data[cc] = d
        log(f"{cc} {name}: " + ", ".join(f"{s}{'' if b.get('ok') else '✗'}{len(b.get('items') or [])}" for s, b in d["src"].items()))
    tr, mk, usage = translator()
    translate_all(data, tr)
    m = usage.setdefault(mk, {"deepl": 0, "google": 0}); m["deepl"] += tr.used["deepl"]; m["google"] += tr.used["google"]
    if not DRY: wj(OUT / "_usage.json", usage)
    mark_seen(data)
    for cc, d in data.items(): wj(OUT / f"{cc}.json", d)
    broken = {k: v for k, v in health.items() if v.get("n", 0) >= 3 * RUNS_PER_DAY}   # 3일 넘게 계속 실패
    idx = {"at": now_iso(), "wikiDay": datetime.now(KST).strftime("%Y-%m-%d"), "countries": [[cc, v[0]] for cc, v in C.items()],
           "world": world_band(data), "broken": broken, "days": sorted({f.stem[3:] for f in HIST.glob("??_*.json")} | {datetime.now(KST).strftime("%Y-%m-%d")}), "ytKey": bool(os.environ.get("YOUTUBE_API_KEY")), "trErrors": tr.errors[:5]}
    wj(OUT / "_index.json", idx); wj(OUT / "_health.json", health)
    archive(data)
    wj(OUT / "_meta.json", {"updatedAt": now_iso(), "by": "trends-robot"})
    log(f"끝 {round(time.time() - t0)}초 · 세계 공통 {len(idx['world'])}개 · 고장 {len(broken)}개 · 번역 {tr.used}")


if __name__ == "__main__":
    main()
