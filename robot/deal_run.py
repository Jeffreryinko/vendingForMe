"""deal_run.py — '딜' 앱 로봇 (GitHub Actions, 하루 4번). 토큰 0.

세계 투자 유치·인수합병(M&A)·사모(PE)·상장(IPO)·펀드 결성 소식을 모아 같은 거래끼리 묶고,
금액(원 환산)·단계·분야·나라·회사·투자사를 붙인다. 공식 신고 자료도 함께 쌓는다.

  뉴스   : 직접 RSS 15곳 + 구글 뉴스 검색(13개 나라판·약 35개 검색어, 하루치)           → 묶기·번역
  미국   : SEC Form D (비상장 회사·펀드가 투자받으면 내는 신고서) — 분기 자료 3년치 + 매일 새 신고
           SEC 상장·합병 서류 목록(S-1·F-1·424B4·S-4·DEFM14A·SC TO-T 등) — 3년치 + 매일
  한국   : DART(전자공시) 합병·지분 인수·영업양수·제3자배정 증자·최대주주 변경·증권신고서 — DART_API_KEY 있을 때만, 3년치 + 매일

번역은 자판기 공통 무료 기계번역(robot/nllb_multi.py: TranslateGemma → NLLB). 분류 낱말은 robot/deal_sources.py.

출력 (data/deal/)
  now.json                   지금 화면 (최근 4일 거래 + 오늘 미국 공시 + 이번 주 돈 흐름)
  news/<날짜>.json            그날 처음 본 거래 (계속 쌓음)
  formd/<YYYY>Q<n>.json       미국 Form D 신고 (분기별)
  sec/<YYYY>.json             미국 상장·합병 서류 목록 (연도별)
  dart/<YYYY>.json            한국 공시 (연도별)
  stats.json · people.json    숫자로 보기 · 자주 나오는 투자사·회사
  _index.json / _meta.json / _health.json / _tr.json / _state/

  python robot/deal_run.py --no-translate     # 번역 없이 빨리 (확인용)
  python robot/deal_run.py --no-filings       # 뉴스만
"""
from __future__ import annotations

import csv, gzip, io, json, os, re, sys, time, unicodedata, zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests
import ai_run as A
import deal_sources as S

ROOT = A.ROOT
OUT = ROOT / "data/deal"; NEWS = OUT / "news"; ST = OUT / "_state"
FD, SECD, DARTD = OUT / "formd", OUT / "sec", OUT / "dart"
KST = A.KST
get, clean, hid, rj, wj, log, now_iso, today = A.get, A.clean, A.hid, A.rj, A.wj, A.log, A.now_iso, A.today
NO_TR = "--no-translate" in sys.argv
NO_FIL = "--no-filings" in sys.argv
YEARS = int(os.environ.get("DEAL_YEARS", "3"))                          # 공시 되돌아보기 햇수
NOW_DAYS = 4                                                           # 지금 화면에 두는 날 수
SEC_MAIL = os.environ.get("SEC_CONTACT_EMAIL", "").strip()                 # SEC는 연락처 이메일이 들어간 이름표(User-Agent)를 요구함 → 비밀 설정에 넣음
SEC_UA = f"vendingForMe-bot/1.0 {SEC_MAIL}"
SEC_DOCS = int(os.environ.get("DEAL_SEC_DOCS", "1500"))               # 한 번에 읽는 Form D 원문 수 (SEC 한도 초당 10회 안에서)
DART_KEY = os.environ.get("DART_API_KEY", "").strip()
DART_CALLS = int(os.environ.get("DEAL_DART_CALLS", "4000"))           # 한 번 실행에 DART 호출 수 (하루 한도 20,000)

DEAL = re.compile(S.DEAL_WORDS, re.I)
SKIP = re.compile(S.SKIP_WORDS)
KINDS = [(k, re.compile(rx, re.I)) for k, _, rx in S.KIND_RX]
STAGES = [(k, re.compile(rx, re.I)) for k, _, rx in S.STAGE_RX]
SECTS = [(k, re.compile(rx, re.I)) for k, _, rx in S.SECTORS]
CTRY = [(k, re.compile(rx, re.I)) for k, rx in S.COUNTRY_RX]
KO_ABBR = re.compile(r"(?:^|[\s\[\(·,'\"‘“])(美|日|中|英|獨|独|佛|印|濠|越|伊|加)(?=[가-힣A-Za-z\s,·])")
ABBR = {"美": "US", "日": "JP", "中": "CN", "英": "GB", "獨": "DE", "独": "DE", "佛": "FR", "印": "IN", "濠": "AU", "越": "VN", "伊": "IT", "加": "CA"}
HANGUL = re.compile(r"[가-힣]")


def fail(health, key, e):
    err = f"{type(e).__name__}: {str(e)[:90]}"
    h = health.setdefault(key, {"since": now_iso(), "n": 0}); h["n"] += 1; h["err"] = err; h["last"] = now_iso()
    log(f"실패 {key}: {err}")


def ok(health, key): health.pop(key, None)


# ───────── 환율 ─────────
def fx_rates(health):
    f = ST / "fx.json"; old = rj(f, {})
    if old.get("day") == today(): return old["r"]
    try:
        j = get("https://api.frankfurter.dev/v1/latest", params={"base": "KRW"}).json()
        r = {c: round(1 / v, 6) for c, v in j["rates"].items() if v}; r["KRW"] = 1
        for c, v in S.FX_DEFAULT.items(): r.setdefault(c, v)
        wj(f, {"day": today(), "date": j.get("date"), "r": r}); ok(health, "fx"); return r
    except Exception as e:
        fail(health, "fx", e)
        return old.get("r") or dict(S.FX_DEFAULT)


# ───────── 금액 읽기 ─────────
CUR_SYM = {"$": "USD", "US$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR", "£": "GBP", "GBP": "GBP", "₹": "INR", "RS": "INR", "RS.": "INR", "INR": "INR", "¥": "JPY", "JPY": "JPY",
           "S$": "SGD", "SGD": "SGD", "A$": "AUD", "AUD": "AUD", "C$": "CAD", "CAD": "CAD", "R$": "BRL", "BRL": "BRL", "HK$": "HKD", "HKD": "HKD", "CHF": "CHF", "AED": "AED", "SAR": "SAR", "SEK": "SEK", "IDR": "IDR", "RP": "IDR", "ILS": "ILS", "CNY": "CNY", "RMB": "CNY"}
CUR_WORD = {"달러": "USD", "dollars": "USD", "유로": "EUR", "euros": "EUR", "euro": "EUR", "Euro": "EUR", "파운드": "GBP", "pounds": "GBP", "엔": "JPY", "円": "JPY", "yen": "JPY",
            "위안": "CNY", "元": "CNY", "人民币": "CNY", "美元": "USD", "美金": "USD", "港元": "HKD", "루피": "INR", "ドル": "USD", "ユーロ": "EUR", "원": "KRW", "US-Dollar": "USD", "dólares": "USD", "reais": "BRL"}
MULT = {"billion": 1e9, "bn": 1e9, "b": 1e9, "bln": 1e9, "milliard": 1e9, "milliards": 1e9, "mrd": 1e9, "milliarden": 1e9, "bilhões": 1e9, "bilhão": 1e9, "miliar": 1e9,
        "million": 1e6, "millions": 1e6, "mn": 1e6, "m": 1e6, "mln": 1e6, "mio": 1e6, "millionen": 1e6, "milhões": 1e6, "milhão": 1e6, "juta": 1e6,
        "k": 1e3, "thousand": 1e3, "crore": 1e7, "cr": 1e7, "lakh": 1e5, "": 1}
NUM = r"(\d{1,3}(?:[,.]\d{3})+|\d+(?:[.,]\d+)?)"
RX_SYM = re.compile(r"(US\$|S\$|A\$|C\$|R\$|HK\$|\$|€|£|₹|¥|Rs\.?|INR|USD|EUR|GBP|SGD|CHF|AED|SAR|Rp)\s?" + NUM + r"\s?(billion|bn|bln|million|mn|mln|m|k|thousand|crore|cr|lakh|bilhões|milhões|juta|miliar)?\b", re.I)
RX_WORD = re.compile(NUM + r"\s?(billion|million|bn|mn|Mio\.?|Millionen|Mrd\.?|Milliarden|millions?|milliards?|bilhões|milhões)\s?(?:de |d')?(US-Dollar|dollars|euros?|Euro|pounds|dólares|reais|USD|EUR|GBP)", re.I)
RX_KO = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s?조(?:\s?(\d[\d,]*)\s?억)?\s?(원|달러|유로|엔|위안)?|(\d[\d,]*(?:\.\d+)?)\s?(천억|억|천만|백만|만)\s?(원|달러|유로|파운드|엔|위안|루피|ドル|円)?")
RX_CJK = re.compile(r"(?:(\d[\d,]*(?:\.\d+)?)\s?兆\s?)?(\d[\d,]*(?:\.\d+)?)\s?(億|亿|万|萬|千万)\s?(円|ドル|元|人民币|美元|美金|港元|ユーロ)|(\d[\d,]*(?:\.\d+)?)\s?兆\s?(円|ドル|元)")
VAL_AFTER = re.compile(r"^\s*(valuation|valued|밸류|기업가치|가치|評価額|估值)", re.I)
VAL_BEFORE = re.compile(r"(valuation of|valued at|worth|market cap(italization)? of|at an? |at |기업가치|밸류에이션|몸값|시가총액|시총|가치|評価額|估值|市值)\s*$", re.I)
CUM_BEFORE = re.compile(r"(total(ing)?|bringing|cumulative|누적|총|累計|累计|to date)\s*\S{0,12}$", re.I)


def _num(s):
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(?:[,.]\d{3})+", s): return float(re.sub(r"[,.]", "", s))
    return float(s.replace(",", ".")) if s.count(",") == 1 and "." not in s and len(s.split(",")[1]) <= 2 else float(s.replace(",", ""))


def money(text):
    """제목에서 거래 금액 찾기 → (금액, 통화, 원문 조각, 기업가치) / 못 찾으면 None. 기업가치·누적 금액은 거래 금액으로 안 씀"""
    t = unicodedata.normalize("NFKC", text or ""); hits = []
    for m in RX_SYM.finditer(t):
        sym = m.group(1).upper(); cur = CUR_SYM.get(sym, CUR_SYM.get(sym.rstrip("."), "USD"))
        mult = MULT.get((m.group(3) or "").lower(), 1)
        if sym in ("₹", "RS", "RS.", "INR") and not m.group(3): mult = 1
        if mult == 1 and cur not in ("INR", "JPY", "IDR"): continue                 # '$5' 같은 건 거래 금액 아님
        hits.append((m.start(), m.end(), _num(m.group(2)) * mult, cur, m.group(0)))
    for m in RX_WORD.finditer(t):
        u = m.group(2).lower().rstrip("."); mult = MULT.get(u, 1e6)
        hits.append((m.start(), m.end(), _num(m.group(1)) * mult, CUR_WORD.get(m.group(3), CUR_SYM.get(m.group(3).upper(), "USD")), m.group(0)))
    for m in RX_KO.finditer(t):
        if m.group(1):
            v = _num(m.group(1)) * 1e12 + (_num(m.group(2)) * 1e8 if m.group(2) else 0); cur = CUR_WORD.get(m.group(3) or "원", "KRW")
        else:
            if not m.group(6) and not re.match(r"\s?(규모|투자|대|을|를|의|에|어치)", t[m.end():m.end() + 4]): continue     # '3억 명' 같은 건 빼고
            u = {"천억": 1e11, "억": 1e8, "천만": 1e7, "백만": 1e6, "만": 1e4}[m.group(5)]; v = _num(m.group(4)) * u; cur = CUR_WORD.get(m.group(6) or "원", "KRW")
            if cur == "KRW" and v < 1e8: continue
        hits.append((m.start(), m.end(), v, cur, m.group(0)))
    for m in RX_CJK.finditer(t):
        if m.group(5): v = _num(m.group(5)) * 1e12; cur = m.group(6)
        else:
            u = {"億": 1e8, "亿": 1e8, "万": 1e4, "萬": 1e4, "千万": 1e7}[m.group(3)]; v = _num(m.group(2)) * u + (_num(m.group(1)) * 1e12 if m.group(1) else 0); cur = m.group(4)
        hits.append((m.start(), m.end(), v, CUR_WORD.get(cur, "CNY"), m.group(0)))
    if not hits: return None
    hits.sort(); amt = val = None
    for s0, e0, v, cur, frag in hits:
        is_val = VAL_AFTER.search(t[e0:e0 + 14]) or VAL_BEFORE.search(t[max(0, s0 - 16):s0])
        if is_val:
            if val is None: val = (v, cur)
            continue
        if CUM_BEFORE.search(t[max(0, s0 - 22):s0]) and amt is not None: continue
        if amt is None: amt = (v, cur, frag.strip())
    if not amt: return (None, None, "", val)
    return (amt[0], amt[1], amt[2], val)


# ───────── 이름 뽑기 ─────────
DESC = re.compile(r"^.*?-backed\s+|^.*\b(startup|start-up|company|firm|platform|maker|developer|provider|unicorn|specialist|operator|giant|group|outfit|player|upstart|lender|insurer|bank)\s+", re.I)
RX_RAISE = re.compile(r"^(.{2,90}?)\s+(raises|raised|secures|secured|lands|closes|closed|bags|nabs|gets|scores|snags|picks up|announces|completes|nets|attracts|draws|receives|wins)\b", re.I)
RX_BUY = re.compile(r"^(.{2,70}?)\s+(to acquire|acquires|acquired|agrees to (?:buy|acquire)|buys|bought|snaps up|completes (?:the )?acquisition of|to buy|in talks to (?:buy|acquire)|to take over|takes over|nears deal (?:to buy|for))\s+(.{2,70}?)(?:\s+for\s|\s+in\s|\s+at\s|,|\s+-\s|\s+–\s|\s+to\s|$)", re.I)
RX_LED = re.compile(r"\b(?:led by|co-led by|from|backed by|with participation from)\s+([A-Z][\w&.'’\- ]{1,60}?(?:(?:,\s*|\s+and\s+)[A-Z][\w&.'’\- ]{1,40}?){0,3})(?=$|,\s*(?:to|with|as|for)\b|\s+(?:to|for|as|in|amid|at|with)\b|\s+-|\s+–|\.)", re.I)
RX_KO_HEAD = re.compile(r"^(?:\[[^\]]{1,12}\]\s*|【[^】]{1,12}】\s*|\([^)]{1,10}\)\s*)*([^,，…·:]{1,24}?)\s*[,，…]\s*")
RX_KO_INV = re.compile(r"([가-힣A-Za-z0-9&.]{2,20})(?:\s?등)?(?:으로부터|로부터|에서|이|가)?\s?(?:주도|리드|단독|참여)")
RX_KO_INV2 = re.compile(r"([가-힣A-Za-z0-9&.]{2,20})\s?(?:등\s?)?(?:으로부터|로부터)|서\s([가-힣A-Za-z][가-힣A-Za-z0-9&.]{1,19})\s투자\s?유치")
RX_KO_TGT = re.compile(r"[,，]\s*(.{2,30}?)\s?(?:을|를)?\s?(?:인수|합병|경영권 인수|지분 인수)")
RX_JA_HEAD = re.compile(r"^(?:【[^】]{1,12}】\s*)?([^、,，]{1,30}?)[、,，]")
RX_ZH_HEAD = re.compile(r"^(?:「[^」]{1,10}」|【[^】]{1,12}】|首发\s*[|｜])?(.{2,20}?)(?:完成|获|宣布|官宣|拿下|斩获|获得|签约|拟收购|收购|入股)")
NAME_STOP = re.compile(r"^(공동|단독|재편|매각|국내|해외|글로벌|the|a|an|exclusive|breaking|report|reports|sources|update|new|this|how|why|startup|startups|ai|단독|속보|종합|특징주|인사|부고|오늘)$|억원|만원|달러|시리즈|투자|유치|규모|후속|추가|신규|전략적|프리|시드|브릿지|라운드", re.I)


def tidy_name(s):
    s = re.sub(r"^(?:exclusive|breaking|update|report|[A-Za-z&]{2,12})\s*:\s*", "", (s or "").strip(), flags=re.I)
    s = re.sub(r"^\d[\d,.]*\s?(조|억|만)?\s?(원|달러)?\s+|\s+\d[\d,.]*\s?(조|억|만)?\s?(원|달러)?에?$|에$", "", s).strip()
    s = re.split(r",\s+(?:a|an|the)\s", s)[0]
    s = DESC.sub("", s).strip(" '\"‘’“”·-–:")
    s = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", s)
    s = re.sub(r"['’]s$", "", s)
    s = re.sub(r"^[美日中英獨独佛印濠越]\s?", "", s)
    s = re.sub(r"^.*(?:기업|업체|스타트업|회사|플랫폼|전문|핀테크)\s+", "", s).strip()
    if re.search(r"\b(startup|start-up|company|firm|platform|maker|developer|provider)$", s, re.I): return ""
    if not s or len(s) > 40 or NAME_STOP.search(s) or len(s.split()) > 5: return ""
    return s


def names(title, lang, kind):
    """→ (회사, 대상 회사, [투자사])"""
    t = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", title or "")                          # ' - 언론사' 떼기
    co = tgt = ""; inv = []
    if lang == "ko":
        m = RX_KO_HEAD.match(t)
        if m: co = tidy_name(m.group(1))
        if kind in ("ma", "pe"):
            m = RX_KO_TGT.search(t)
            if m: tgt = tidy_name(m.group(1))
        for m in list(RX_KO_INV.finditer(t)) + list(RX_KO_INV2.finditer(t)):
            x = tidy_name(m.group(1) or m.group(2) or "")
            if x and x != co and x not in inv: inv.append(x)
    elif lang == "ja":
        m = RX_JA_HEAD.match(t); co = tidy_name(m.group(1)) if m else ""
    elif lang == "zh":
        m = RX_ZH_HEAD.match(t); co = tidy_name(m.group(1)) if m else ""
    else:
        m = RX_BUY.match(t)
        if m and kind in ("ma", "pe"): co, tgt = tidy_name(m.group(1)), tidy_name(m.group(3))
        else:
            m = RX_RAISE.match(t)
            if m: co = tidy_name(m.group(1))
        m = RX_LED.search(t)
        if m and m.group(0).lower().startswith("from") and not re.search(r"(fund|round|financ|invest|\$|€|£|raise|seed|series)", t[max(0, m.start() - 45):m.start()], re.I): m = None
        if m:
            for x in re.split(r",\s*|\s+and\s+", m.group(1)):
                x = tidy_name(x)
                if x and x != co and not re.search(r"\b(investors?|backers|others|existing|new|round|series|seed)\b", x, re.I) and x not in inv: inv.append(x)
    return co, tgt, inv[:5]


def kind_of(text):
    for k, rx in KINDS:
        if rx.search(text): return k
    return "etc"


def stage_of(text):
    for k, rx in STAGES:
        if rx.search(text): return k
    return ""


def sectors_of(text):
    out = [k for k, rx in SECTS if rx.search(text)]
    if "health" in out and "bio" in out: out.remove("health")
    return out[:2] or ["etc"]


def country_of(text, default, lang):
    found = [k for k, rx in CTRY if rx.search(text)]
    if lang == "ko":
        m = KO_ABBR.search(text)
        if m and ABBR[m.group(1)] != "KR": return ABBR[m.group(1)]
    foreign = [k for k in found if k not in ("KR", "US")]
    if default == "KR":
        if foreign and "KR" not in found: return foreign[0]
        if "US" in found and "KR" not in found and re.search(r"미국|실리콘밸리|뉴욕|美", text): return "US"
        return "KR"
    if foreign: return foreign[0]
    if "KR" in found: return "KR"
    if default: return default
    return "US" if "US" in found else "WW"


# ───────── 뉴스 모으기 ─────────
def gnews_url(q, hl, gl, ceid):
    return f"https://news.google.com/rss/search?q={quote(q + ' when:1d')}&hl={hl}&gl={gl}&ceid={ceid}"


def collect_news(health):
    raw = []
    for fid, name, url, cc, lang, filt in S.FEEDS:
        try:
            its = A.rss_items(url, limit=60); ok(health, f"rss/{fid}")
        except Exception as e:
            fail(health, f"rss/{fid}", e); continue
        n0 = len(raw)
        for it in its:
            txt = it["title"] + " " + it.get("sum", "")
            if filt and not DEAL.search(it["title"]): continue
            if SKIP.search(it["title"]): continue
            raw.append({"title": it["title"], "sum": LEAD_SKIP.sub("", clean(it.get("sum"), 300)), "url": it["url"], "src": name, "date": A.parse_date(it.get("date", "")) or today(), "lang": lang, "cc0": cc, "via": fid})
        log(f"RSS {name}: {len(raw) - n0}개")
    for hl, gl, ceid, lang, cc, qs in S.GNEWS:
        for q in qs:
            key = f"gn/{gl}/{hid(q)}"
            try:
                its = A.rss_items(gnews_url(q, hl, gl, ceid), limit=100); ok(health, key)
            except Exception as e:
                fail(health, key, e); continue
            n0 = len(raw)
            for it in its:
                m = re.match(r"^(.*)\s+-\s+([^-]{2,60})$", it["title"])
                title, pub = (m.group(1), m.group(2)) if m else (it["title"], "")
                if not DEAL.search(title) or SKIP.search(title): continue
                raw.append({"title": clean(title, 220), "sum": "", "url": re.sub(r"\?oc=\d+$", "", it["url"]), "src": pub or "구글 뉴스", "date": A.parse_date(it.get("date", "")) or today(), "lang": lang, "cc0": cc, "via": "gn"})
            log(f"구글 뉴스 [{gl}] {q}: {len(raw) - n0}개")
            time.sleep(0.6)
    for q in S.BING_KR:
        try:
            its = bing_items(q, "&qft=sortbydate%3d%221%22&setlang=ko&cc=KR"); ok(health, "bing/kr")
        except Exception as e:
            fail(health, "bing/kr", e); break
        n0 = len(raw); cut = (date.today() - timedelta(days=2)).isoformat()
        for it in its:
            if not it["date"] or it["date"] < cut or not DEAL.search(it["title"]) or SKIP.search(it["title"]): continue
            raw.append({"title": it["title"], "sum": LEAD_SKIP.sub("", it["sum"]), "url": it["url"], "src": it["src"], "date": it["date"], "lang": "ko", "cc0": "KR", "via": "bing"})
        log(f"빙 뉴스 [KR] {q}: {len(raw) - n0}개")
        time.sleep(1.0)
    return raw


# ───────── 빙 뉴스 (진짜 기사 주소 + 첫 문단이 같이 옴, 토큰 0) ─────────
from urllib.parse import unquote, quote_plus


def bing_items(q, extra=""):
    """빙 뉴스 검색 RSS → [{title, url(진짜 기사), sum(첫 문단), date, src}]"""
    x = get(f"https://www.bing.com/news/search?q={quote_plus(q)}&format=rss{extra}", headers={"Accept-Language": "ko,en;q=0.8"}).text
    out = []
    for it in re.findall(r"<item>(.*?)</item>", x, re.S):
        t = re.search(r"<title>(.*?)</title>", it, re.S); l = re.search(r"<link>(.*?)</link>", it, re.S)
        if not t or not l: continue
        link = A.html.unescape(l.group(1)); m = re.search(r"[?&]url=([^&]+)", link)
        url = unquote(m.group(1)) if m else link
        d = re.search(r"<description>(.*?)</description>", it, re.S); p = re.search(r"<pubDate>(.*?)</pubDate>", it)
        src = re.search(r"<News:Source>(.*?)</News:Source>", it) or re.search(r"<source[^>]*>(.*?)</source>", it)
        out.append({"title": clean(t.group(1), 220), "url": url, "sum": clean(d.group(1) if d else "", 400), "date": A.parse_date(p.group(1)) if p else "",
                    "src": clean(src.group(1), 60) if src else re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", url))})
    return out


def sum_lang(t):
    if re.search(r"[가-힣]", t): return "ko"
    if re.search(r"[\u3040-\u30ff]", t): return "ja"
    if re.search(r"[\u4e00-\u9fff]{4,}", t): return "zh"
    return "en"


class _LeadSkip:                                                                  # 기사 첫 문단 앞의 안내문·기자 이름 떼기
    RX = [re.compile(r"^\s*\[?(이 기사에 나온|스타트업에 대한 보다)[^\]]*\]\s*"),
          re.compile(r"^\s*[\[\(（【][^\]\)）】]{0,40}(기자|특파원|=)[^\]\)）】]{0,30}[\]\)）】]\s*(=\s*)?"),
          re.compile(r"^\s*[^|]{0,40}기자\s*[|=]\s*"), re.compile(r"^\s*[가-힣]{2,4}\s?기자\s*=\s*")]
    def sub(self, _, t):
        t = t or ""
        for _i in range(2):
            for rx in self.RX: t = rx.sub("", t)
        return t.strip()


LEAD_SKIP = _LeadSkip()


def page_lead(url):
    """기사 페이지의 소개글(og:description·description) → 없으면 첫 문단"""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent)); from ogimg import _html
        h = _html(url, 250_000)
    except Exception:
        return ""
    for p in (r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']{40,})', r'<meta[^>]+content=["\']([^"\']{40,})["\'][^>]+property=["\']og:description',
              r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{40,})', r'<meta[^>]+content=["\']([^"\']{40,})["\'][^>]+name=["\']description'):
        m = re.search(p, h, re.I)
        if m: return clean(m.group(1), 400)
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", h, re.S | re.I):
        t = clean(m.group(1), 400)
        if len(t) >= 80 and not re.search(r"copyright|저작권|무단|구독|로그인|cookie", t, re.I): return t
    return ""


def fill_leads(deals, health, deadline, bing_budget=120, page_budget=80):
    """요약 없는 거래에 기사 첫 문단 붙이기 (토큰 0): ① 빙 뉴스에서 같은 제목 찾기 ② 진짜 기사 주소면 그 페이지 소개글"""
    mem = rj(ST / "lead.json", {}); nb = npg = got = 0
    need = [d for d in deals if not d.get("sum")]
    need.sort(key=lambda d: (not (d.get("cc") == "KR" and d.get("kind") == "vc"), -(d.get("amt") or 0), -(d.get("n") or 1)))   # 한국 벤처 먼저, 그다음 큰 거래
    for d in need:
        if time.time() > deadline: break
        k = hid(d["title"])
        if k in mem:
            v = mem[k]
        else:
            v = None; tried = False
            real = d["url"] if "news.google." not in d["url"] else next((x[1] for x in d.get("srcs", []) if "news.google." not in x[1]), "")
            if not real and nb < bing_budget:
                nb += 1; tried = True
                try:
                    q = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", d["title"])[:120]
                    tk = toks(q); best = None
                    for it in bing_items(q):
                        ov = len(tk & toks(it["title"])) / max(min(len(tk), len(toks(it["title"]))), 1)
                        if ov >= 0.5 and (best is None or ov > best[0]): best = (ov, it)
                    if best: v = {"u": best[1]["url"], "s": LEAD_SKIP.sub("", best[1]["sum"]), "src": best[1]["src"]}
                    ok(health, "bing/lookup")
                except Exception as e:
                    fail(health, "bing/lookup", e)
                    if "429" in str(e): nb = bing_budget
                time.sleep(1.0)
            elif real and npg < page_budget:
                npg += 1; tried = True; t = LEAD_SKIP.sub("", page_lead(real))
                if t: v = {"u": real, "s": t}
            if not tried: continue                                                           # 이번엔 한도가 다 차서 못 봄 → 다음에
            mem[k] = v or {}
        if v and v.get("s"):
            d["sum"] = v["s"]; got += 1
            if v.get("u") and "news.google." in d.get("url", ""): d["gurl"] = d["url"]; d["url"] = v["u"]           # 진짜 기사 주소로
    if len(mem) > 8000: mem = dict(list(mem.items())[-6000:])
    wj(ST / "lead.json", mem)
    log(f"기사 첫 문단: {got}건 붙임 (빙 찾기 {nb} · 기사 페이지 {npg})")


# ───────── 같은 거래 묶기 ─────────
STOP_TOK = set("the a an and of for to in on at by with from its as is are new raises raise raised funding round series seed led startup startups company firm million billion deal acquire acquires acquisition buy buys ipo fund capital ventures venture partners investment invest investors announces secures closes growth global group inc ltd llc corp us uk ai".split())


def toks(t):
    t = unicodedata.normalize("NFKC", t or "").lower()
    out = {w for w in re.findall(r"[a-z][a-z0-9&'.-]{2,}", t) if w not in STOP_TOK}
    out |= {w for w in re.findall(r"[가-힣]{2,}", t) if w not in ("투자", "유치", "인수", "합병", "시리즈", "억원", "규모", "스타트업", "기업", "추진", "결정", "완료", "확보", "단독", "글로벌", "국내", "해외")}
    out |= set(re.findall(r"[぀-ヿ一-鿿]{2,4}", t)) - {"資金調達", "シリーズ", "融资", "完成", "收购", "买收", "買収"}
    return out


KG = {"ma": "m", "pe": "m", "vc": "v", "fund": "f", "ipo": "i", "etc": "e"}


def same(a, b):
    gap = abs((a["d0"] - b["d0"]).days)
    if gap > 7: return False
    if a.get("co") and b.get("co") and KG.get(a["kind"]) == KG.get(b["kind"]):
        from deal_judge import norm
        if norm(a["co"]) == norm(b["co"]) and (not a.get("tgt") or not b.get("tgt") or norm(a["tgt"]) == norm(b["tgt"])): return True
    if gap > 4: return False
    ta, tb = a["tk"], b["tk"]
    if not ta or not tb: return False
    common = ta & tb
    if a.get("usd") and b.get("usd") and abs(a["usd"] - b["usd"]) <= 0.1 * max(a["usd"], b["usd"]) and any(re.match(r"[a-z]", w) and len(w) >= 3 for w in common): return True
    return len(common) / max(min(len(ta), len(tb)), 1) >= 0.6 and len(common) >= 3


def enrich(r, fx):
    """기사 한 건 → 종류·단계·분야·나라·금액·이름"""
    txt = r["title"] + " " + r.get("sum", "")[:200]
    r["kind"] = kind_of(r["title"]) if kind_of(r["title"]) != "etc" else kind_of(txt)
    r["stage"] = stage_of(r["title"]) if r["kind"] == "vc" else ""
    mo = money(r["title"]); r["amtFrom"] = "title"
    if not (mo and mo[0]) and r["kind"] != "etc": mo = money(r.get("sum", "")[:200]) or mo; r["amtFrom"] = "sum"
    r["amt"] = r["usd"] = r["val"] = None; r["amtS"] = ""
    if mo:
        v, cur, frag, val = mo
        if v:
            krw = v * fx.get(cur, S.FX_DEFAULT.get(cur, 0)); r["amt"] = round(krw); r["usd"] = round(krw / fx["USD"]); r["amtS"] = frag
            if krw > 2e14 or krw < 1e7: r["amt"] = r["usd"] = None; r["amtS"] = ""                  # 200조 원 넘는 건 거래 금액이 아니라 회사 몸값인 경우가 대부분
        if val: r["val"] = round(val[0] * fx.get(val[1], 1))
    r["sec"] = sectors_of(txt)
    r["cc"] = country_of(txt, r["cc0"], r["lang"])
    CUR_CC = {"CNY": "CN", "JPY": "JP", "INR": "IN", "GBP": "GB", "EUR": "EU", "SGD": "SG", "IDR": "ID", "BRL": "BR", "HKD": "CN"}
    if r["cc"] == "KR" and mo and mo[1] in CUR_CC and not CTRY[0][1].search(txt): r["cc"] = CUR_CC[mo[1]]      # 한국 매체가 쓴 '5억 위안' 거래 → 중국
    if r["cc"] == "KR" and re.search(r"\([A-Z]{1,5}\.(O|N|OQ|K)\)", txt): r["cc"] = "US"           # '폭스(FOXA.O)' 같은 미국 종목 기호
    if r["cc"] in ("US", "WW") and mo and mo[1] == "KRW" and not any(k not in ("KR", "US") and rx.search(txt) for k, rx in CTRY): r["cc"] = "KR"   # '40억원' → 한국
    r["co"], r["tgt"], r["inv"] = names(r["title"], r["lang"], r["kind"])
    try: r["d0"] = date.fromisoformat(r["date"])
    except Exception: r["d0"] = date.today()
    r["tk"] = toks(r["title"])
    return r


PRIO = {"ko": 0, "en": 1}


def better(a, b):
    """대표 기사 고르기: 직접 RSS > 금액 있음 > 한국어(한국 거래) / 영어 > 짧은 출처"""
    def score(x): return ((x["via"] != "gn") * 2 + (x["via"] == "bing") + (x.get("amt") is not None) * 3 + (x.get("co") != "") + (2 if (x["lang"] == "ko" and x["cc"] == "KR") else 1 if x["lang"] == "en" else 0) + (1 if x.get("sum") else 0))
    return a if score(a) >= score(b) else b


def cluster(raw, prev_deals, seen_url):
    """새 기사 + 지난 거래(최근 4일) → 거래 목록. 지난 거래에 붙으면 출처만 늘어남"""
    deals = []
    for d in prev_deals:
        d = dict(d); d["d0"] = date.fromisoformat(d["date"]); d["tk"] = set(d.get("tk", [])) or toks(d["title"]); d["usd"] = d.get("usd")
        if not any(x[1] == d.get("url") for x in d.get("srcs", [])): d["srcs"] = [[d.get("src", ""), d.get("url", ""), d.get("lang", ""), d.get("title", "")[:90], d.get("amtS", "")]] + d.get("srcs", [])
        d.setdefault("via", "gn"); d.setdefault("inv", []); d.setdefault("co", ""); d.setdefault("tgt", ""); d.setdefault("sum", "")
        deals.append(d)
    seen_url |= {s[1] for d in deals for s in d.get("srcs", [])}
    for r in raw:
        if r["url"] in seen_url: continue
        seen_url.add(r["url"])
        hit = None
        for d in deals:
            if same(d, r): hit = d; break
        src = [r["src"], r["url"], r["lang"], r["title"][:90], r.get("amtS", "")]
        if hit is None:
            d = {k: r[k] for k in ("title", "sum", "url", "src", "date", "lang", "via", "kind", "stage", "amt", "usd", "val", "amtS", "amtFrom", "sec", "cc", "co", "tgt", "inv", "d0", "tk")}
            d["id"] = "n" + hid((r["co"] or r["title"]).lower() + r["kind"] + r["date"][:7]); d["srcs"] = [src]; d["n"] = 1; d["t"] = "news"; d["at"] = now_iso()
            d["amts"] = [r["amt"]] if r.get("amt") else []
            deals.append(d)
        else:
            if len(hit["srcs"]) < 8 and r["src"] not in [s[0] for s in hit["srcs"]]: hit["srcs"].append(src)
            hit["n"] = hit.get("n", 1) + 1
            if r.get("amt"): hit["amts"] = (hit.get("amts") or [])[-7:] + [r["amt"]]
            for k in ("amt", "usd", "amtS", "amtFrom", "val", "co", "tgt"):
                if not hit.get(k) and r.get(k): hit[k] = r[k]
            if r["stage"] and not hit.get("stage"): hit["stage"] = r["stage"]
            hit["inv"] = (hit.get("inv") or []) + [x for x in r["inv"] if x not in (hit.get("inv") or [])][:5]
            hit["tk"] = hit["tk"] | r["tk"]
            b = better(hit, r)
            if b is r:
                for k in ("title", "sum", "url", "src", "lang", "via"): hit[k] = r[k]
                hit.pop("ko", None); hit.pop("ksum", None)
    # 같은 id 가 둘이면 하나로
    out, ids = [], {}
    for d in deals:
        if d["id"] in ids:
            o = ids[d["id"]]; o["n"] += d.get("n", 1)
            o["srcs"] = (o["srcs"] + [s for s in d["srcs"] if s[1] not in {x[1] for x in o["srcs"]}])[:8]; continue
        ids[d["id"]] = d; out.append(d)
    return out


# ───────── 미국 SEC ─────────
def sec_get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"}, timeout=60, **kw)
            if r.status_code in (429, 503): time.sleep(5 * (i + 1)); continue
            r.raise_for_status(); time.sleep(0.13); return r
        except requests.RequestException:
            if i == 3: raise
            time.sleep(3 * (i + 1))
    raise RuntimeError("SEC 응답 없음")


def qkey(d): return f"{d.year}Q{(d.month - 1) // 3 + 1}"
def qstart(y, q): return date(y, 3 * (q - 1) + 1, 1)


US_STATES = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR GU VI".split())


def fd_row(filed, name, st, stdesc, ind, ftype, sold, offered, ninv, cik, acc, yinc):
    """Form D 한 줄 (짧은 배열로): [신고일, 이름, 주/나라, 업종, 펀드종류, 판매액, 모집액(-1=무기한), 투자자 수, CIK, 접수번호, 설립연도]"""
    def f(x):
        try: return int(float(x))
        except Exception: return -1 if str(x).strip().lower() == "indefinite" else 0
    sold, offered = f(sold), f(offered)
    if max(sold, offered) < 250_000 and offered != -1: return None
    st = (st or "").strip().upper()
    loc = st if st in US_STATES else (stdesc or st or "").strip().title()
    return [filed, (name or "").strip(), loc, ind or "Other", ftype or "", max(sold, 0), offered, f(ninv) if ninv not in (None, "") else 0, str(int(cik)) if str(cik).strip().isdigit() else cik, acc, (yinc or "")[:4]]


def formd_datasets(health, state, deadline):
    """SEC 분기 자료(zip) — 3년치 한 번에. 받은 분기는 state['fdq'] 에 기록"""
    try:
        page = sec_get("https://www.sec.gov/data-research/sec-markets-data/form-d-data-sets").text; ok(health, "sec/formd-list")
    except Exception as e:
        fail(health, "sec/formd-list", e); return
    links = dict((m.group(2).upper(), "https://www.sec.gov" + m.group(1)) for m in re.finditer(r'href="(/files/[^"]*form-d-data-sets/(\d{4}q\d)_d\.zip)"', page))
    first = date.today().replace(day=1) - timedelta(days=365 * YEARS)
    done = set(state.setdefault("fdq", []))
    for q, url in sorted(links.items()):
        y, n = int(q[:4]), int(q[5])
        if qstart(y, n) < qstart(first.year, (first.month - 1) // 3 + 1) or q in done: continue
        if time.time() > deadline: log("시간 한도 — Form D 분기 자료 나머지는 다음에"); break
        try:
            z = zipfile.ZipFile(io.BytesIO(sec_get(url).content))
            def tsv(nm):
                p = [x for x in z.namelist() if x.upper().endswith("/" + nm) or x.upper() == nm][0]
                return csv.DictReader(io.TextIOWrapper(z.open(p), encoding="utf-8", errors="ignore"), delimiter="\t")
            sub = {r["ACCESSIONNUMBER"]: r for r in tsv("FORMDSUBMISSION.TSV")}
            iss = {}
            for r in tsv("ISSUERS.TSV"):
                if r.get("IS_PRIMARYISSUER_FLAG") == "YES": iss[r["ACCESSIONNUMBER"]] = r
            rows = []
            for r in tsv("OFFERING.TSV"):
                if r.get("ISAMENDMENT") == "true": continue
                a = r["ACCESSIONNUMBER"]; i = iss.get(a, {}); s = sub.get(a, {})
                try: filed = datetime.strptime(s.get("FILING_DATE", ""), "%d-%b-%Y").strftime("%Y-%m-%d")
                except Exception: filed = ""
                row = fd_row(filed, i.get("ENTITYNAME"), i.get("STATEORCOUNTRY"), i.get("STATEORCOUNTRYDESCRIPTION"), r.get("INDUSTRYGROUPTYPE"), r.get("INVESTMENTFUNDTYPE"),
                             r.get("TOTALAMOUNTSOLD"), r.get("TOTALOFFERINGAMOUNT"), r.get("TOTALNUMBERALREADYINVESTED"), i.get("CIK", ""), a, i.get("YEAROFINC_VALUE_ENTERED"))
                if row: rows.append(row)
            rows.sort(key=lambda x: (x[0], -x[5]))
            wj(FD / f"{q}.json", {"q": q, "src": "dataset", "rows": rows}); done.add(q); state["fdq"] = sorted(done)
            ok(health, f"sec/formd-{q}"); log(f"Form D {q}: {len(rows):,}건 (분기 자료)")
        except Exception as e:
            fail(health, f"sec/formd-{q}", e)


def parse_formd_xml(x, filed, cik, acc):
    try: root = ET.fromstring(x)
    except ET.ParseError: return None
    g = lambda p: (root.findtext(p) or "").strip()
    if g("offeringData/typeOfFiling/newOrAmendment/isAmendment") == "true": return None
    return fd_row(filed, g("primaryIssuer/entityName"), g("primaryIssuer/issuerAddress/stateOrCountry"), g("primaryIssuer/issuerAddress/stateOrCountryDescription"),
                  g("offeringData/industryGroup/industryGroupType"), g("offeringData/industryGroup/investmentFundInfo/investmentFundType"),
                  g("offeringData/offeringSalesAmounts/totalAmountSold"), g("offeringData/offeringSalesAmounts/totalOfferingAmount"),
                  g("offeringData/investors/totalNumberAlreadyInvested"), cik, acc, g("primaryIssuer/yearOfInc/value"))


def sec_daily(health, state, deadline):
    """매일 새 신고: daily-index 의 form 목록 → Form D 원문(xml) + 상장·합병 서류 목록. 분기 자료가 아직 없는 날만"""
    covered = set(state.get("fdq", []))
    # 처음엔 이번 분기 첫날부터 (분기 자료가 아직 없는 날들)
    t = date.today(); d = qstart(t.year, (t.month - 1) // 3 + 1); p = d - timedelta(days=1); pq = qstart(p.year, (p.month - 1) // 3 + 1)
    if qkey(pq) not in covered: d = pq                                                     # 지난 분기 자료가 아직 안 나왔으면 거기부터
    if state.get("secDay"): d = date.fromisoformat(state["secDay"])
    last_ok = None; docs = 0; pend = state.setdefault("fdPend", [])
    end = date.today()
    newforms = {}
    while d <= end and time.time() < deadline:
        ds = d.strftime("%Y%m%d"); url = f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}/QTR{(d.month - 1) // 3 + 1}/form.{ds}.idx"
        try:
            txt = sec_get(url).text; ok(health, "sec/daily")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404): d += timedelta(days=1); continue      # 주말·휴일
            fail(health, "sec/daily", e); break
        except Exception as e:
            fail(health, "sec/daily", e); break
        for ln in txt.splitlines():
            if len(ln) < 100 or ln.startswith("-") or ln.startswith("Form Type"): continue
            form = ln[:17].strip()
            path = ln.split()[-1] if ln.split() else ""
            if not path.startswith("edgar/"): continue
            name = ln[17:79].strip(); cik = ln[79:91].strip()
            iso = d.isoformat()
            if form == "D": pend.append([iso, cik, path])
            elif form in S.SEC_FORMS: newforms.setdefault(d.year, []).append([iso, form, name, cik, path])
        last_ok = d.isoformat(); d += timedelta(days=1)
    if last_ok: state["secDay"] = last_ok                                                  # 마지막으로 읽은 날은 다음에 한 번 더 (늦게 올라온 것)
    uniq = {}
    for x in pend: uniq.setdefault(x[2], x)
    pend[:] = list(uniq.values())
    for y, rows in newforms.items(): add_sec_forms(y, rows)
    # Form D 원문 읽기 (밀린 것부터)
    seen = set(state.setdefault("fdSeen", []))
    rows_by_q = {}
    while pend and docs < SEC_DOCS and time.time() < deadline:
        iso, cik, path = pend.pop(0)
        acc = path.rsplit("/", 1)[-1].replace(".txt", "")
        if acc in seen: continue
        try:
            x = sec_get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/primary_doc.xml").content; docs += 1
        except Exception as e:
            fail(health, "sec/formd-doc", e); pend.insert(0, [iso, cik, path]); break
        row = parse_formd_xml(x, iso, cik, acc); seen.add(acc)
        if row: rows_by_q.setdefault(qkey(date.fromisoformat(iso)), []).append(row)
    if docs: ok(health, "sec/formd-doc")
    state["fdSeen"] = sorted(seen)[-20000:]; state["fdPend"] = pend
    added = []
    for q, rows in rows_by_q.items():
        f = FD / f"{q}.json"; cur = rj(f, {"q": q, "src": "daily", "rows": []})
        if cur.get("src") == "dataset": continue
        have = {r[9] for r in cur["rows"]}
        new = [r for r in rows if r[9] not in have]; cur["rows"] += new; cur["rows"].sort(key=lambda x: (x[0], -x[5])); wj(f, cur); added += new
    log(f"SEC 매일: Form D 원문 {docs}건 읽음 (밀린 것 {len(pend)}) · 상장·합병 서류 {sum(map(len, newforms.values()))}건")
    return added


def add_sec_forms(year, rows):
    f = SECD / f"{year}.json"; cur = rj(f, {"y": year, "rows": []})
    have = {(r[1], r[4]) for r in cur["rows"]}
    for r in rows:
        if (r[1], r[4]) in have:
            continue
        # 같은 서류에 회사가 둘(인수자·대상)이면 이름을 이어 붙임
        same_doc = next((x for x in cur["rows"] if x[4] == r[4] and x[1] == r[1]), None)
        if same_doc: continue
        cur["rows"].append(r); have.add((r[1], r[4]))
    # 같은 접수번호 → 이름 합치기
    by = {}
    for r in cur["rows"]:
        k = (r[1], r[4].rsplit("/", 1)[-1])
        if k in by:
            if r[2] not in by[k][2]: by[k][2] = by[k][2] + " / " + r[2]
        else: by[k] = r
    cur["rows"] = sorted(by.values(), key=lambda x: x[0])
    wj(f, cur)


def sec_full_index(health, state, deadline):
    """상장·합병 서류 3년치 (분기마다 full-index form.gz 한 번)"""
    done = set(state.setdefault("secq", []))
    first = date.today() - timedelta(days=365 * YEARS); y, q = first.year, (first.month - 1) // 3 + 1
    cur_q = qkey(date.today())
    while f"{y}Q{q}" < cur_q:
        k = f"{y}Q{q}"
        if k not in done:
            if time.time() > deadline: break
            try:
                raw = gzip.decompress(sec_get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.gz").content).decode("latin-1")
                rows = {}
                for ln in raw.splitlines():
                    form = ln[:17].strip()
                    if form not in S.SEC_FORMS: continue
                    p = ln.split()
                    if len(p) < 4 or not p[-1].startswith("edgar/"): continue
                    dd = p[-2]; iso = f"{dd[:4]}-{dd[4:6]}-{dd[6:8]}" if len(dd) == 8 else dd
                    rows.setdefault(int(iso[:4]), []).append([iso, form, ln[17:79].strip(), ln[79:91].strip(), p[-1]])
                for yy, rr in rows.items(): add_sec_forms(yy, rr)
                done.add(k); state["secq"] = sorted(done); ok(health, "sec/full-index"); log(f"SEC 서류 목록 {k}: {sum(map(len, rows.values())):,}건")
            except Exception as e:
                fail(health, "sec/full-index", e); break
        q += 1
        if q == 5: y, q = y + 1, 1


# ───────── 한국 DART ─────────
DART_RX = [(re.compile(rx), k, nm, api) for rx, k, nm, api in S.DART_RX]


class Dart:
    def __init__(self, budget): self.left = budget

    def call(self, ep, **p):
        if self.left <= 0: raise RuntimeError("이번 실행 호출 수 다 씀")
        self.left -= 1
        j = get(f"https://opendart.fss.or.kr/api/{ep}.json", params=dict(p, crtfc_key=DART_KEY)).json()
        st = j.get("status")
        if st == "013": return []                                                     # 자료 없음
        if st == "020": raise RuntimeError("DART 하루 한도 넘음")
        if st != "000": raise RuntimeError(f"DART {st} {j.get('message', '')[:40]}")
        return j.get("list", [])

    def reports(self, bgn, end):
        """기간 안 공시 목록 → 자판기가 보는 종류만"""
        out = []
        for ty in ("B", "I", "C"):
            page = 1
            while True:
                j = get("https://opendart.fss.or.kr/api/list.json", params={"crtfc_key": DART_KEY, "bgn_de": bgn, "end_de": end, "pblntf_ty": ty, "page_no": page, "page_count": 100}).json()
                self.left -= 1
                if j.get("status") == "013": break
                if j.get("status") != "000": raise RuntimeError(f"DART list {j.get('status')} {j.get('message', '')[:40]}")
                for r in j.get("list", []):
                    nm = r.get("report_nm", "")
                    if "정정" in nm or "철회" in nm: continue
                    for rx, k, what, api in DART_RX:
                        if rx.search(nm.replace(" ", "")):
                            if k == "ipo" and r.get("corp_cls") != "E": break                    # 증권신고서는 처음 상장하는 회사만
                            out.append(dict(r, _k=k, _w=what, _api=api)); break
                if page >= int(j.get("total_page", 1)) or self.left <= 0: break
                page += 1
        return out


def num0(x):
    try: return int(str(x).replace(",", "").strip() or 0)
    except Exception: return 0


def dart_detail(dart, reps):
    """자세히 API (회사·종류별로 한 번에) → 금액·상대 회사 붙이기"""
    by = {}
    for r in reps:
        if r["_api"]: by.setdefault((r["corp_code"], r["_api"]), []).append(r)
    for (cc, api), rs in by.items():
        if dart.left <= 0: break
        ds = sorted(r["rcept_dt"] for r in rs)
        try: lst = dart.call(api, corp_code=cc, bgn_de=ds[0], end_de=ds[-1])
        except Exception as e: log(f"DART 자세히 실패 {api}: {e}"); continue
        m = {x.get("rcept_no"): x for x in lst}
        for r in rs:
            x = m.get(r["rcept_no"])
            if not x: continue
            if api == "otcprStkInvscrInhDecsn": r["_tgt"] = x.get("iscmp_cmpnm", ""); r["_amt"] = num0(x.get("inhdtl_inhprc")); r["_eq"] = x.get("atinh_eqrt", ""); r["_biz"] = x.get("iscmp_mbsn", "")
            elif api == "bsnInhDecsn": r["_tgt"] = x.get("dlptn_cmpnm", "") or x.get("inh_bsn", ""); r["_amt"] = num0(x.get("inh_prc")); r["_biz"] = x.get("inh_bsn", "")
            elif api in ("cmpMgDecsn", "cmpDvmgDecsn"): r["_tgt"] = x.get("mgptncmp_cmpnm", ""); r["_biz"] = x.get("mgptncmp_mbsn", ""); r["_mth"] = x.get("mg_stn", "")
            elif api == "stkExtrDecsn": r["_tgt"] = x.get("extr_tgcmp_cmpnm", ""); r["_biz"] = x.get("extr_tgcmp_mbsn", "")
            elif api == "piicDecsn":
                r["_mth"] = x.get("ic_mthn", "")
                r["_amt"] = sum(num0(x.get(k)) for k in ("fdpp_fclt", "fdpp_bsninh", "fdpp_op", "fdpp_dtrp", "fdpp_ocsa", "fdpp_etc"))


def dart_rows(reps):
    out = []
    for r in reps:
        if r["_api"] == "piicDecsn" and "제3자" not in r.get("_mth", "제3자"): continue                       # 주주배정·일반공모 증자는 투자 유치가 아님
        d = r["rcept_dt"]; iso = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        out.append([iso, r["_k"], r["_w"], r.get("corp_name", ""), r.get("corp_cls", ""), r.get("_tgt", ""), r.get("_amt", 0), r.get("_eq", ""), r.get("_biz", ""), r["rcept_no"], r.get("report_nm", "").strip()[:60]])
    return out


def add_dart(rows):
    by = {}
    for r in rows: by.setdefault(r[0][:4], []).append(r)
    for y, rr in by.items():
        f = DARTD / f"{y}.json"; cur = rj(f, {"y": y, "rows": []}); have = {r[9] for r in cur["rows"]}
        cur["rows"] += [r for r in rr if r[9] not in have]; cur["rows"].sort(key=lambda x: x[0]); wj(f, cur)


def dart_run(health, state, deadline):
    if not DART_KEY: log("DART_API_KEY 없음 → 한국 공시 건너뜀"); return []
    dart = Dart(DART_CALLS); new = []
    try:
        # 1) 매일: 지난 확인 날부터 오늘까지
        d0 = date.fromisoformat(state.get("dartDay") or (date.today() - timedelta(days=7)).isoformat())
        reps = dart.reports(d0.strftime("%Y%m%d"), date.today().strftime("%Y%m%d"))
        dart_detail(dart, reps); rows = dart_rows(reps); add_dart(rows); new = rows
        state["dartDay"] = date.today().isoformat(); ok(health, "dart/daily"); log(f"DART 매일: {len(rows)}건")
        # 2) 3년치 되돌아보기 (석 달씩, 남은 호출 안에서)
        back = date.fromisoformat(state.get("dartBack") or d0.isoformat()); first = date.today() - timedelta(days=365 * YEARS)
        while back > first and dart.left > 400 and time.time() < deadline:
            b0 = max(back - timedelta(days=89), first)
            reps = dart.reports(b0.strftime("%Y%m%d"), (back - timedelta(days=1)).strftime("%Y%m%d"))
            dart_detail(dart, reps); rows = dart_rows(reps); add_dart(rows)
            state["dartBack"] = b0.isoformat(); log(f"DART 되돌아보기 {b0} ~ {back}: {len(rows)}건 (남은 호출 {dart.left})")
            back = b0
        ok(health, "dart/back")
    except Exception as e:
        fail(health, "dart/daily", e)
    return new


# ───────── 공시 → 오늘 거래 카드 ─────────
def filing_deals(fd_new, dart_new, fx):
    out = []
    usd = fx["USD"]
    for r in fd_new:
        filed, name, loc, ind, ftype, sold, offered, ninv, cik, acc, yinc = r
        if ind == "Pooled Investment Fund":
            if ftype not in ("Venture Capital Fund", "Private Equity Fund") or sold < S.FORMD_FUND_FEED_MIN: continue
            kind, sec = "fund", ["fin"]
        else:
            if ind in S.FORMD_SKIP_IND or sold < S.FORMD_FEED_MIN: continue
            kind, sec = "vc", [S.FORMD_IND.get(ind, "etc")]
        amt = sold * usd
        ko = (f"{name} — {S.FUND_KO.get(ftype, '펀드')} {fmt_usd(sold)} 모음" if kind == "fund" else f"{name} — 비상장 투자 {fmt_usd(sold)} 받음") + " (미국 Form D 신고)"
        out.append({"id": "f" + hid(acc), "t": "formd", "kind": kind, "stage": "", "title": ko, "ko": ko, "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/xslFormDX01/primary_doc.xml",
                    "src": "SEC Form D", "date": filed, "lang": "ko", "amt": round(amt), "usd": sold, "amtS": fmt_usd(sold), "sec": sec, "cc": "US" if len(loc) == 2 else country_of(loc, "", "en"),
                    "co": name, "tgt": "", "inv": [], "n": 1, "srcs": [], "ind": S.FORMD_KO.get(ind, ind), "ninv": ninv, "loc": loc, "at": now_iso()})
    for r in dart_new:
        iso, k, what, corp, cls, tgt, amt, eq, biz, rcp, nm = r
        if k == "vc" and amt < 1e8: continue                                                                    # 1억 미만 증자만 뺌 (작은 투자도 보이게)
        t = f"{corp}, {tgt + ' ' if tgt else ''}{what}" + (f" {eq}%" if eq and eq not in ("-", "") else "") + (f" · {won(amt)}" if amt else "") + " (공시)"
        out.append({"id": "d" + rcp, "t": "dart", "kind": k, "stage": "", "title": t, "ko": t, "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp}", "src": "DART 전자공시", "date": iso, "lang": "ko",
                    "amt": amt or None, "usd": round(amt / usd) if amt else None, "amtS": won(amt) if amt else "", "sec": sectors_of(biz + " " + tgt + " " + corp), "cc": "KR", "co": corp, "tgt": tgt, "inv": [],
                    "n": 1, "srcs": [], "biz": biz, "rep": nm, "cls": cls, "at": now_iso()})
    return out


def fmt_usd(v):
    v = float(v or 0)
    return f"${v / 1e9:.1f}B".replace(".0B", "B") if v >= 1e9 else f"${v / 1e6:.0f}M" if v >= 1e6 else f"${v / 1e3:.0f}K"


def won(v):
    v = float(v or 0)
    if v >= 1e12: jo = int(v // 1e12); ek = int(round((v - jo * 1e12) / 1e8)); return f"{jo}조" + (f" {ek:,}억" if ek else "") + " 원"
    if v >= 1e8: return f"{int(round(v / 1e8)):,}억 원"
    return f"{int(round(v / 1e4)):,}만 원"


# ───────── 숫자로 보기 ─────────
def band(v):
    for k, _, lo, hi in S.BANDS:
        if v is not None and lo <= v < hi: return k
    return ""


def stats(fx):
    import deal_judge as J
    st = {"at": now_iso(), "news": {}, "formd": {}, "sec": {}, "dart": {}}
    for f in sorted(NEWS.glob("????-??-??.json")):
        m = f.stem[:7]; b = st["news"].setdefault(m, {"n": 0, "kind": {}, "sec": {}, "cc": {}, "amt": 0})
        for d in rj(f, {}).get("items", []):
            if d.get("st", "done") == "news": continue                                     # 거래 아닌 딜 소식은 안 셈
            b["n"] += 1; a = (d.get("amt") or 0) if (J.counted(d) or "g" not in d) else 0; b["amt"] += a      # 금액은 확인된 거래만 (등급 생기기 전 자료는 그대로)
            k = b["kind"].setdefault(d["kind"], [0, 0]); k[0] += 1; k[1] += a
            if d["kind"] == "vc":
                for s in d.get("sec", [])[:1]: x = b["sec"].setdefault(s, [0, 0]); x[0] += 1; x[1] += a
            x = b["cc"].setdefault(d.get("cc", "WW"), [0, 0]); x[0] += 1; x[1] += a
    for f in sorted(FD.glob("*.json")):
        b = {"n": 0, "sold": 0, "ind": {}, "fund": {}}
        for r in rj(f, {}).get("rows", []):
            ind, ft, sold = r[3], r[4], r[5]
            if ind == "Pooled Investment Fund":
                x = b["fund"].setdefault(ft or "Other Investment Fund", [0, 0]); x[0] += 1; x[1] += sold
            else:
                b["n"] += 1; b["sold"] += sold; s = S.FORMD_IND.get(ind, "etc"); x = b["ind"].setdefault(s, [0, 0]); x[0] += 1; x[1] += sold
        st["formd"][f.stem] = b
    for f in sorted(SECD.glob("*.json")):
        for r in rj(f, {}).get("rows", []):
            m = r[0][:7]; b = st["sec"].setdefault(m, {}); b[r[1]] = b.get(r[1], 0) + 1
    for f in sorted(DARTD.glob("*.json")):
        for r in rj(f, {}).get("rows", []):
            m = r[0][:7]; b = st["dart"].setdefault(m, {}); x = b.setdefault(r[2], [0, 0]); x[0] += 1; x[1] += r[6] or 0
    st["fx"] = {"USD": fx.get("USD")}
    wj(OUT / "stats.json", st)
    return st


def people(days=90):
    """자주 나오는 투자사·회사 (최근 90일 뉴스) → 따라가기 화면"""
    cut = (date.today() - timedelta(days=days)).isoformat(); inv, co = {}, {}
    for f in sorted(NEWS.glob("????-??-??.json")):
        if f.stem < cut: continue
        for d in rj(f, {}).get("items", []):
            for x in d.get("inv", []):
                e = inv.setdefault(x, {"n": 0, "amt": 0, "last": "", "kinds": {}}); e["n"] += 1; e["amt"] += d.get("amt") or 0; e["last"] = max(e["last"], d["date"])
            for x in (d.get("co"), d.get("tgt")):
                if x: e = co.setdefault(x, {"n": 0, "amt": 0, "last": ""}); e["n"] += 1; e["amt"] += d.get("amt") or 0; e["last"] = max(e["last"], d["date"])
    top = lambda m, k: [[n, v["n"], v["amt"], v["last"]] for n, v in sorted(m.items(), key=lambda kv: (-kv[1]["n"], -kv[1]["amt"]))[:k]]
    wj(OUT / "people.json", {"at": now_iso(), "days": days, "inv": top(inv, 200), "co": top(co, 200)})


# ───────── 실행 ─────────
KEEP = ("id", "amtFrom", "st", "g", "chk", "amtK", "garb", "quiet", "filed", "follow", "hist", "coinfo", "amts", "gurl", "t", "kind", "stage", "title", "ko", "sum", "ksum", "url", "src", "date", "lang", "amt", "usd", "amtS", "val", "sec", "cc", "co", "tgt", "inv", "n", "srcs", "ind", "ninv", "loc", "biz", "rep", "cls", "at", "via")


def slim(d, arch=False):
    o = {k: d[k] for k in KEEP if d.get(k) not in (None, "", [])}
    if arch:                                                                         # 쌓는 파일은 가볍게: 요약 빼고 출처 4개까지
        for k in ("sum", "ksum", "via", "at", "hist", "amts", "coinfo"): o.pop(k, None)
        if o.get("srcs"): o["srcs"] = [x[:3] for x in o["srcs"][:3]]
    return o


def main():
    t0 = time.time(); deadline = t0 + int(os.environ.get("DEAL_MAX_MINUTES", "45")) * 60
    for d in (OUT, NEWS, ST, FD, SECD, DARTD): d.mkdir(parents=True, exist_ok=True)
    health = rj(OUT / "_health.json", {}); state = rj(ST / "state.json", {}); day = today()
    fx = fx_rates(health)

    # 1) 뉴스 → 거래
    raw = [enrich(r, fx) for r in collect_news(health)]
    raw = [r for r in raw if r["kind"] != "etc" or r.get("amt")]
    prev = rj(ST / "recent.json", {}).get("deals") or rj(OUT / "now.json", {}).get("deals", []); tkm = rj(ST / "tk.json", {})
    for d in prev: d["tk"] = tkm.get(d["id"], [])
    cut = (date.today() - timedelta(days=NOW_DAYS)).isoformat()
    prev_news = [d for d in prev if d.get("t") == "news" and d["date"] >= cut and not SKIP.search(d.get("title", ""))]   # 빼는 낱말을 고치면 지난 거래에도 바로 적용
    urls = {u: v for u, v in rj(ST / "urls.json", {}).items() if v >= cut}                   # 이미 센 기사 주소 (같은 기사를 두 번 세지 않게)
    deals = cluster(raw, prev_news, set(urls))
    for r in raw: urls.setdefault(r["url"], day)
    wj(ST / "urls.json", urls)
    log(f"기사 {len(raw)}건 → 거래 {len(deals)}건")

    try: fill_leads(deals, health, t0 + (deadline - t0) * 0.3)
    except Exception as e: log(f"기사 첫 문단 실패 — 건너뜀: {e}")

    # 2) 공시
    fd_new, dart_new = [], []
    if not NO_FIL:
        fil_deadline = t0 + (deadline - t0) * 0.55
        if not SEC_MAIL: log("SEC_CONTACT_EMAIL 없음 → 미국 공시 건너뜀")
        else:
            try: formd_datasets(health, state, fil_deadline)
            except Exception as e: fail(health, "sec/formd", e)
            try: fd_new = sec_daily(health, state, fil_deadline) or []
            except Exception as e: fail(health, "sec/daily", e)
            try: sec_full_index(health, state, fil_deadline)
            except Exception as e: fail(health, "sec/full-index", e)
        try: dart_new = dart_run(health, state, fil_deadline)
        except Exception as e: fail(health, "dart/daily", e)
        wj(ST / "state.json", state)
    prev_fil = [d for d in prev if d.get("t") in ("formd", "dart") and d["date"] >= cut]
    have = {d["id"] for d in prev_fil}
    fil = prev_fil + [d for d in filing_deals(fd_new, dart_new, fx) if d["id"] not in have and d["date"] >= cut]
    for d in fil: d["st"] = "done"; d["g"] = "f"

    # 3) 번역 (한국어가 아닌 제목 + 금액 큰 순 200건 요약)
    mem_path = OUT / "_tr.json"
    if not NO_TR:
        try:
            from nllb_multi import Ko
            ko = Ko(mem_path); pairs, where = [], []
            for d in deals:
                if d["lang"] != "ko" and not d.get("ko"): pairs.append((d["title"], d["lang"])); where.append((d, "ko"))
            for d in sorted([d for d in deals if d.get("sum") and sum_lang(d["sum"]) != "ko" and not d.get("ksum")], key=lambda d: (not (d.get("cc") == "KR"), -(d.get("amt") or 0)))[:260]:
                pairs.append((d["sum"][:300], sum_lang(d["sum"]))); where.append((d, "ksum"))
            res = ko.many(pairs, deadline=deadline - 120)
            for (d, k), v in zip(where, res):
                if v: d[k] = v
            ko.save(keep=20000); log(f"번역 {sum(1 for v in res if v)}/{len(pairs)}건")
        except Exception as e:
            log(f"번역 실패 — 원문으로: {e}")
    try:                                                                                  # 한국어 제목·첫 문단에서 'OO벤처스·OO파트너스' 같은 투자사 이름 더 뽑기
        from deal_firms import investors_in, matchers, FIRMS
        FM = matchers(); FKO = {f[0]: f[1] for f in FIRMS}
        for d in deals:
            stxt = " ".join(x for x in (d.get("sum", ""), d.get("ksum", "")) if x)            # 첫 문단에 나온 주요 투자사 (퓨처플레이·알토스처럼 이름 끝이 평범한 곳)
            if stxt:
                for fid, rx in FM:
                    if rx.search(stxt) and FKO[fid] not in (d.get("inv") or []) and FKO[fid] != d.get("co") and not rx.search(d.get("co") or ""): d["inv"] = (d.get("inv") or []) + [FKO[fid]]
            txt = " ".join(x for x in (d["title"] if d["lang"] == "ko" else "", d.get("sum", "") if sum_lang(d.get("sum", "")) == "ko" else "", d.get("ksum", "")) if x)
            for n in investors_in(txt):
                if n != d.get("co") and n not in (d.get("inv") or []) and not (d.get("co") and n in d["co"]): d["inv"] = (d.get("inv") or []) + [n]
            if d.get("inv"): d["inv"] = d["inv"][:8]
    except Exception as e: log(f"투자사 이름 뽑기 실패: {e}")
    for d in deals:
        if d["lang"] == "ko": d["ko"] = d["title"]
        if d.get("ko") and d["kind"] in ("vc", "etc") and not d.get("stage"): d["stage"] = stage_of(d["ko"])
        if d.get("ko") and d["sec"] == ["etc"]: d["sec"] = sectors_of(d["ko"])

    # 3-2) 가리고 재기 (deal_judge): 깨진 번역 · 금액 · 회사 사전 · 상태 · 지난 이야기 · 공시 맞추기 · 믿음 등급
    import deal_judge as J
    cod = J.CoDict(ST / "codict.json")
    lk_deadline = min(deadline - 90, time.time() + 240)
    for d in sorted(deals, key=lambda d: -(d.get("amt") or 0) - (1e15 if d.get("cc") == "KR" else 0)):
        if d["lang"] != "ko" and d.get("ko"):
            g = J.garbled(d["ko"], d["title"], d["lang"])
            if g: d["garb"] = g; d["ko"] = ""
        if d.get("ksum") and J.garbled(d["ksum"], d.get("sum", ""), sum_lang(d.get("sum", ""))): d.pop("ksum", None)
        J.amount_check(d)
        if time.time() < lk_deadline:
            info = cod.look(d.get("co"), 80)
        else:
            info = cod.get(d.get("co"))
        if info:
            if info.get("cc"): d["cc"] = info["cc"]
            if d["sec"] == ["etc"] and info.get("desc"): d["sec"] = sectors_of(info["desc"])
            if info.get("desc") or info.get("since"): d["coinfo"] = {k: info[k] for k in ("desc", "since", "qid") if info.get(k)}
        if d.get("tgt") and J.norm(d["tgt"]) == J.norm(d.get("co")): d["tgt"] = None             # 사는 쪽 = 팔리는 쪽으로 잘못 뽑힌 것
        d["st"] = J.status(d)
    cod.save(); log(f"회사 사전: 새로 {cod.n}곳 찾음 · 모두 {len(cod.d)}곳")

    try:
        idx = J.build_index(NEWS, DARTD, FD)
        for d in deals:
            d["hist"], d["filed"], d["follow"] = J.history(d, idx, fx["USD"])
            d["g"] = J.grade(d)
        news_names = {J.norm(x) for d in deals for x in (d.get("co"), d.get("tgt")) if x}
        for d in fil:
            d["hist"], _, _ = J.history(d, idx, fx["USD"])
            if J.norm(d.get("co")) not in news_names and J.norm(d.get("tgt")) not in news_names and (d.get("amt") or 0) >= 5e9: d["quiet"] = 1
        log(f"등급: " + ", ".join(f"{k} {sum(1 for d in deals if d.get('g') == k)}" for k in "fmsc") + " · 상태: " + ", ".join(f"{k} {sum(1 for d in deals if d.get('st') == k)}" for k in ("done", "rumor", "fail", "news")))
    except Exception as e:
        log(f"지난 이야기·등급 실패 — 건너뜀: {e}")
        for d in deals: d.setdefault("g", "s")

    # 4) 저장: 지금 화면 + 날짜별로 쌓기
    alld = [slim(d) for d in deals] + [slim(d) for d in fil]
    for d in alld:
        d["new"] = d["date"] == day
        d["band"] = band(d.get("amt"))
    alld.sort(key=lambda d: (d["date"], d.get("amt") or 0), reverse=True)
    wj(ST / "tk.json", {d["id"]: sorted(d.get("tk", []))[:40] for d in deals})                # 묶기용 낱말 (화면엔 안 씀)
    wj(ST / "recent.json", {"at": now_iso(), "deals": [dict(d) for d in alld]})               # 다음 실행에서 이어 묶을 4일치 (출처 전부)
    for d in alld:                                                                    # 화면 파일 가볍게: 대표 기사 빼고 다른 출처 4곳까지
        o = [x for x in d.get("srcs", []) if x[1] != d.get("url")][:4]
        if o: d["srcs"] = o
        else: d.pop("srcs", None)
        if d.get("sum"): d["sum"] = d["sum"][:300]
        if d.get("ksum"): d.pop("sum", None)                                          # 번역이 있으면 원문 요약은 화면에서 뺌
        for k in ("via", "amts", "at"): d.pop(k, None)
    week = {}
    wcut = (date.today() - timedelta(days=7)).isoformat()
    by_day = {}
    for d in alld: by_day.setdefault(d["date"], []).append(d)
    for dd, lst in by_day.items():
        if dd < (date.today() - timedelta(days=NOW_DAYS + 2)).isoformat(): continue
        f = NEWS / f"{dd}.json"; cur = rj(f, {"day": dd, "items": []})
        cur["items"] = [x for x in cur["items"] if not SKIP.search(x.get("title", ""))]                # 빼는 낱말을 고치면 쌓인 것도 정리
        pos = {x["id"]: i for i, x in enumerate(cur["items"])}
        for d in lst:
            a = slim(d, arch=True)
            if d["id"] in pos: cur["items"][pos[d["id"]]] = a
            else: cur["items"].append(a)
        cur["items"].sort(key=lambda x: -(x.get("amt") or 0)); wj(f, cur)
    # 이번 주 돈 흐름 (분야·나라·종류별 합)
    for f in sorted(NEWS.glob("????-??-??.json")):
        if f.stem < wcut: continue
        for d in rj(f, {}).get("items", []):
            if d.get("st", "done") != "done": continue
            a = d.get("amt") if J.counted(d) else 0
            for key, val in (("kind", d["kind"]), ("cc", d.get("cc", "WW"))) + tuple(("sec", s) for s in (d.get("sec") or ["etc"])[:1]):
                x = week.setdefault(key, {}).setdefault(val, [0, 0]); x[0] += 1; x[1] += a
    sec_today = []
    for f in sorted(SECD.glob("*.json"))[-1:]:
        rows = rj(f, {}).get("rows", [])
        last = max((r[0] for r in rows), default="")
        sec_today = [r for r in rows if r[0] >= (date.fromisoformat(last) - timedelta(days=2)).isoformat()] if last else []
    y = (date.today() - timedelta(days=1)).isoformat()
    try: bn = J.bench(FD, OUT / "kvca.json", NEWS, fx["USD"], S.FORMD_IND)
    except Exception as e: log(f"잣대 실패: {e}"); bn = {}
    try: mm = J.money_map(NEWS)
    except Exception as e: log(f"지도 실패: {e}"); mm = {}
    daily = J.daily_pick(alld, state, datetime.now(KST)); wj(ST / "state.json", state)
    keep_ids = {i for i, _ in daily.get("items", [])}
    screen = [dict(d) for d in alld if (d["date"] >= day and d.get("st") != "news") or d["id"] in keep_ids or d.get("st") in ("rumor", "fail")]
    for d in screen:
        if d.get("hist"): d["hist"] = [[e[0], e[1], e[2][:70], e[3], e[4]] for e in d["hist"][:4]]
        for k in ("amtFrom", "gurl", "lang"): d.pop(k, None)
        if d.get("srcs"): d["srcs"] = [[x[0], x[1], (x[3] if len(x) > 3 else "")[:70], (x[4] if len(x) > 4 else "")] for x in d["srcs"][:2]]   # 매체·주소·제목·금액
    now = {"at": now_iso(), "day": day, "deals": screen, "week": week, "secToday": sec_today[-40:], "bench": bn, "map": mm, "daily": daily}
    wj(OUT / "now.json", now)

    st = stats(fx); people()
    try:                                                                                 # 주요 투자사 (위키 소개 + 쌓인 거래·펀드 신고)
        import deal_firms
        ko_tr = None
        if not NO_TR:
            from nllb_multi import Ko
            ko_tr = Ko(OUT / "_tr.json")
        deal_firms.build(OUT, NEWS, FD, alld, min(deadline, time.time() + 300), ko_tr)
        if ko_tr is not None: ko_tr.save(keep=20000)
    except Exception as e: log(f"주요 투자사 실패 — 건너뜀: {e}")
    try:                                                                                 # 한국 VC 전체 (DIVA 전자공시)
        import deal_kvca
        deal_kvca.build(OUT, NEWS, alld, min(deadline, time.time() + 300))
    except Exception as e: log(f"한국 VC 공시 실패 — 건너뜀: {e}")
    broken = {k: v for k, v in health.items() if v.get("n", 0) >= 6}                    # 하루 4번 × 1.5일 넘게 계속 실패
    days = sorted(f.stem for f in NEWS.glob("????-??-??.json"))
    idx = {"at": now_iso(), "today": day, "days": days, "broken": broken, "new": sum(1 for d in alld if d.get("new")), "counts": {"deals": len(alld), "news": len(deals), "filings": len(fil)},
           "kinds": [[k, n] for k, n, _ in S.KIND_RX] + [["etc", "기타"]], "stages": [[k, n] for k, n, _ in S.STAGE_RX], "sectors": [[k, n] for k, n, _ in S.SECTORS] + [["etc", "기타"]],
           "regions": S.REGION, "bands": [[k, n] for k, n, _, _ in S.BANDS], "fx": {"USD": fx.get("USD"), "EUR": fx.get("EUR"), "JPY": fx.get("JPY"), "CNY": fx.get("CNY"), "day": rj(ST / "fx.json", {}).get("date")},
           "formd": sorted(f.stem for f in FD.glob("*.json")), "sec": sorted(f.stem for f in SECD.glob("*.json")), "dart": sorted(f.stem for f in DARTD.glob("*.json")), "dartKey": bool(DART_KEY), "secKey": bool(SEC_MAIL),
           "dartBack": state.get("dartBack"), "fdPend": len(state.get("fdPend", [])),
           "feeds": [[n, u] for _, n, u, _, _, _ in S.FEEDS], "gnews": sum(len(q[5]) for q in S.GNEWS), "formdKo": S.FORMD_KO, "fundKo": S.FUND_KO, "secForms": {k: v[1] for k, v in S.SEC_FORMS.items()},
           "translated": not NO_TR}
    wj(OUT / "_index.json", idx); wj(OUT / "_health.json", health)
    wj(OUT / "_meta.json", {"updatedAt": now_iso(), "by": "deal-robot", "label": datetime.now(KST).strftime("%m월 %d일 %H시판")})
    log(f"끝 {round(time.time() - t0)}초 · 거래 {len(alld)} (뉴스 {len(deals)} · 공시 {len(fil)}) · 고장 {len(broken)}곳")


if __name__ == "__main__":
    main()
