"""deal_judge.py — '딜' 거래를 가리고 재고 잇기 (토큰 0). deal_run.py 가 번역 뒤·저장 전에 부름.

1단계 (믿을 수 있게)
  status()     ✅ done 발표·완료 / 💬 rumor 협상·소문 / ❌ fail 무산·철회 / 📰 news 거래 아닌 딜 소식
  amount_kind  거래 금액 / 빚(debt) / 회사 숫자(매출·자산 → 버림) / 범위(~)·상식 밖 → 확인 필요(chk)
  garbled()    깨진 번역(같은 말 반복·한자 남음·길이 이상) → 번역 버리고 원문
  grade        f 공시로 확인 · m 여러 매체 일치 · s 한 매체 · c 확인 필요
  CoDict       회사 사전 (위키데이터: 나라·업종·설립·한 줄) — 한 번 찾으면 _state/codict.json 에 기억
2단계 (한 장 읽을거리)
  history      같은 회사의 지난 기사·DART·Form D (최근 90일 기사 + 공시) · 투자사 처음/후속
3단계 (잣대)
  bench        크기 자: Form D 분기 중앙값(분야별) · 한국 VC 한 건 평균(전자공시) · 단계별 중앙값(기사, 30건 넘을 때만)
  money_map    돈의 지도: 분야 × 권역, 지난 7일 건수·중앙값 vs 그 전 28일 주평균
4단계
  daily_pick   오늘의 딜 (아침 첫 판에서 고정): 큰 거래 3 · 한국 3 · 사모·인수 2 · 조용한 돈 1
"""
from __future__ import annotations

import re, statistics, time, unicodedata
from datetime import date, timedelta, datetime

import ai_run as A

rj, wj, log, now_iso = A.rj, A.wj, A.log, A.now_iso

# ───────── 상태 ─────────
RX_FAIL = re.compile(r"\b(withdraw[sn]?|withdrew|terminat\w*|scrap(s|ped)?|call(s|ed)? off|abandon\w*|reject\w*|rebuff\w*|turn(s|ed)? down|postpone\w*|"
                     r"pull(s|ed)? (its |the )?(IPO|listing|offer)|block(s|ed)|collaps\w*|fall(s|en)? through|fell through|shelve[sd]?|walks? away)\b"
                     r"|철회|무산|결렬|거절|좌초|불발|백지화|해지|파기|연기|중단|무효|撤回|中止|白紙|見送り|终止|放弃|撤销|暂停", re.I)
RX_RUMOR = re.compile(r"\b(in talks|talks (to|with|for)|considering|consider(s)?|weigh(s|ing)?|explor(es|ing)|nears?|nearing|plans? to|planning|set to|seek(s|ing)?|"
                      r"said to|reportedly|sources say|people familiar|could|may|might|in discussions|eyes|eyeing|mulls?|mulling|bid(s)? for|offer(s)? for|proposal|"
                      r"prepar(es|ing)|expected to|poised|set for|plan|planned|rumou?rs?|speculat\w*)\b|Gerücht|erwägt|envisage|envisagerait|negocia"
                      r"|추진|검토|임박|협상|타진|물밑|저울질|나설|나선다|노린다|노려|가능성이|관측|거론|유력|예정|채비|원매자|본입찰|예비입찰|우선협상|인수전|매각전|매물|소문|루머|분수령|본격화|관건|기로|변수|"
                      r"検討|交渉|調整|観測|噂|拟|计划|洽谈|商谈|传出|或将|传闻|传言|意向|推进", re.I)
RX_DONE = re.compile(r"\b(raised|raises|secured|secures|closed|closes|completed|completes|announced|lands|landed|bags|acquired|acquires|agreed|agrees|signed|signs|"
                     r"buys|bought|merged|priced|prices|debut(s|ed)|lists|listed|went public|schließt|abgeschlossen|übernimmt|sammelt|lève|rachète|rachat|annonce|"
                     r"adquire|adquiriu|capta|levanta|recebe|conclui|mendapat|meraih|accepte|back(s|ed)?|files|filed|DRHP|invests?|invested|takes? (a )?stake)\b|클로징|투자했|투자한|"
                     r"유치|완료|체결|확정|마무리|인수했|인수한|합병했|결성|조성|상장했|상장한|"
                     r"完了|締結|調達|完成|获得|收购了|融资|买收|签约|签署|入股|参投", re.I)
RX_ROUND = re.compile(r"\b(startups|companies|firms) (raised|secured)\b|\b\d+ (startups|companies|deals)\b|this week|this month|first (nine|six|three) months|week'?s (top|biggest)|as many as \d+|"
                      r"주간|이번 주|한 주간|스타트업 \d+곳|기업 \d+곳|本周|上周", re.I)
RX_AGG = re.compile(r"올해|연간|누적|상반기|하반기|분기|월간|역대|최고|최대치|사상|this year|year-to-date|so far this|record (year|quarter)|in 20\d\d|\bH[12]\b|\bQ[1-4]\b|今年|上半年|年内", re.I)
RX_TALK = re.compile(r"카드뉴스|한컷|멀티미디어|\[그래픽\]|혼선|논란|우려|오락가락|해부|진단|시사점|관전 ?포인트|①|②|③|④|\[기획|리포트|브리핑|동향|결산|총정리|뒷얘기|비하인드|명암|두 ?얼굴|두 ?가지 ?계산|两笔账|"
                     r"\b(roundup|round-up|recap|ranking|biggest|largest .* (rounds|deals)|explainer|what we know|lessons)\b", re.I)
RX_NEWSY = re.compile(r"실적|수익이|매출|영업이익|주가|목표주가|전망|분석|칼럼|인터뷰|가이드|이유|왜 |어떻게|투자팀|영입|임명|선임|대표 취임|선임|정책|규제|"
                      r"\b(earnings|revenue|profit|quarter|shares (rose|fell|jump|drop)|stock|appoints?|hires?|names? .{0,30}(CEO|partner|chief)|steps down|outlook|analysis|opinion|why|how)\b", re.I)


def status(d):
    t = " ".join(x for x in (d.get("title", ""), d.get("ko", "")) if x)
    if d.get("t") in ("formd", "dart"): return "done"
    if d.get("kind") == "etc": return "news"
    if RX_FAIL.search(t): return "fail"
    if RX_TALK.search(t) or RX_ROUND.search(t): return "news"
    if (not (d.get("co") or d.get("tgt")) or RX_AGG.search(d.get("co") or "")) and RX_AGG.search(t): return "news"   # '올해 홍콩 IPO 69조' 같은 모음 숫자
    if RX_RUMOR.search(t) and not re.search(r"\b(raised|closed|completed|acquired)\b|완료|체결했|마무리", t, re.I):
        return "rumor" if (d.get("co") or d.get("amt")) else "news"
    if d.get("kind") in ("vc", "ma", "pe", "fund", "ipo") and RX_DONE.search(t) and not RX_NEWSY.search(t): return "done"
    has_core = bool(d.get("co") or d.get("tgt") or d.get("amt") or d.get("stage") or d.get("inv")) and bool(d.get("amt") or d.get("tgt") or d.get("inv") or RX_DONE.search(t))
    if not has_core: return "news"
    if RX_NEWSY.search(t) and not d.get("amt") and not RX_DONE.search(t): return "news"
    return "done"


# ───────── 금액 ─────────
RX_DEBT = re.compile(r"채권|사채|회사채|대출|차입|\bCB\b|\bBW\b|bonds?|notes|loan|debt|credit (facility|line)|financing facility|refinanc|대환|借款|社債|融資枠", re.I)
RX_METRIC = re.compile(r"매출|영업이익|순이익|이익|자산|운용자산|운용 자산|수주|거래액|시가총액|시총|revenue|sales|profit|earnings|assets|AUM|under management|market (cap|value)|bookings|GMV|売上|营收|资产", re.I)
STAGE_MAX = {"pre-seed": 3e10, "seed": 1.5e12, "pre-a": 1e11, "a": 2e12, "b": 5e12, "c": 1e13, "d+": 3e13, "growth": 3e13, "tips": 3e10, "grant": 1e12, "debt": 3e13}
KIND_MAX = {"vc": 3e13, "fund": 3e13, "ma": 2e14, "pe": 2e14, "ipo": 1e14, "etc": 1e14}


def amount_check(d):
    """거래 금액이 맞는지 따져 amtK(debt/…)·chk(확인 필요)를 붙이거나 금액을 버림"""
    a = d.get("amt")
    if not a: return
    src = unicodedata.normalize("NFKC", d.get("title", "")); frag = unicodedata.normalize("NFKC", d.get("amtS", ""))
    if d.get("t") == "news" and frag and frag not in src and frag not in unicodedata.normalize("NFKC", d.get("sum", "")):
        d["amt"] = d["usd"] = None; d["amtS"] = ""; return                          # 번역문에서 읽었던 금액(옛 자료) → 버림
    i = src.find(frag) if frag else -1
    win = src[max(0, i - 24): i + len(frag) + 24] if i >= 0 else src
    if i >= 0 and (src[max(0, i - 2):i].strip().endswith(("~", "-", "–")) or src[i + len(frag): i + len(frag) + 2].strip().startswith(("~", "–"))): d["chk"] = "범위로 나온 금액"
    if RX_METRIC.search(win) and not re.search(r"투자|유치|인수|raise|acqui|funding|round|deal", win, re.I):
        d["val2"] = a; d["amt"] = d["usd"] = None; d["amtS"] = ""; return              # 회사 숫자 → 거래 금액 아님
    if RX_DEBT.search(win): d["amtK"] = "debt"
    lim = STAGE_MAX.get(d.get("stage") or "", KIND_MAX.get(d.get("kind"), 1e14))
    if a > lim: d["chk"] = d.get("chk") or "이 단계치고 너무 큰 금액"
    if d.get("cc") == "KR" and d.get("kind") == "vc" and a > 5e12: d["chk"] = d.get("chk") or "한국 투자치고 너무 큰 금액"
    if d.get("amtFrom") == "sum" and a > 1e12: d["chk"] = d.get("chk") or "제목이 아니라 요약에서 읽은 큰 금액"


# ───────── 깨진 번역 ─────────
RX_REPEAT = re.compile(r"(\S{1,8}?)(?:[,\s]+\1){3,}")


def garbled(ko, src, lang):
    if not ko: return ""
    if RX_REPEAT.search(ko): return "같은 말 반복"
    if len(re.findall(r"[一-鿿]", ko)) >= 2 and lang != "ko": return "한자 남음"
    if len(re.findall(r"[぀-ヿ]", ko)) >= 2: return "일본 글자 남음"
    try:
        from ko_polish import bad
        r = bad(src, ko, lang)
        if r: return r
    except Exception:
        pass
    return ""


# ───────── 회사 사전 (위키데이터) ─────────
ISO = {"Q30": "US", "Q884": "KR", "Q148": "CN", "Q17": "JP", "Q668": "IN", "Q145": "GB", "Q183": "DE", "Q142": "FR", "Q801": "IL", "Q334": "SG", "Q252": "ID", "Q881": "VN",
       "Q878": "AE", "Q851": "SA", "Q155": "BR", "Q96": "MX", "Q16": "CA", "Q408": "AU", "Q1033": "NG", "Q258": "ZA", "Q34": "SE", "Q55": "NL", "Q39": "CH", "Q29": "ES",
       "Q38": "IT", "Q8646": "CN", "Q865": "TW", "Q20": "NO", "Q35": "DK", "Q33": "FI", "Q40": "AT", "Q31": "BE", "Q27": "IE", "Q36": "PL", "Q43": "TR", "Q79": "EG",
       "Q414": "AR", "Q298": "CL", "Q739": "CO", "Q419": "PE", "Q843": "PK", "Q902": "BD", "Q928": "PH", "Q833": "MY", "Q869": "TH", "Q664": "NZ", "Q846": "QA", "Q159": "RU", "Q212": "UA"}
CO_DESC = re.compile(r"company|startup|start-up|business|corporation|enterprise|manufacturer|developer|provider|firm|bank|brand|platform|maker|retailer|operator|conglomerate|"
                     r"기업|회사|스타트업|업체|제조|그룹|은행|브랜드|플랫폼|会社|企業|公司", re.I)


def norm(n):
    n = unicodedata.normalize("NFKC", n or "").lower()
    n = re.sub(r"\(주\)|㈜|주식회사|\b(inc|corp|corporation|co|ltd|limited|llc|plc|ag|sa|gmbh|holdings?|group|technologies|technology|labs?)\b\.?", "", n)
    return re.sub(r"[\s.,'’\"·\-()]", "", n)


class CoDict:
    def __init__(self, path):
        self.path = path; self.d = rj(path, {}); self.n = 0; self.stop = False

    def save(self):
        if len(self.d) > 6000: self.d = dict(list(self.d.items())[-5000:])
        wj(self.path, self.d)

    def get(self, name):
        return self.d.get(norm(name)) if name else None

    def look(self, name, budget):
        k = norm(name)
        if not k or len(k) < 2 or k in self.d or self.stop or self.n >= budget: return self.d.get(k)
        self.n += 1
        lang = "ko" if re.search(r"[가-힣]", name) else "ja" if re.search(r"[぀-ヿ]", name) else "zh" if re.search(r"[一-鿿]", name) else "en"
        info = {"day": date.today().isoformat()}
        try:
            j = A.get("https://www.wikidata.org/w/api.php", params={"action": "wbsearchentities", "search": name, "language": lang, "uselang": "ko", "format": "json", "limit": 4}, retries=0).json()
            hit = None
            for r in j.get("search", []):
                lab = (r.get("label") or "")
                if norm(lab) == k and CO_DESC.search(r.get("description") or ""): hit = r; break
            if hit:
                e = A.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": hit["id"], "props": "claims|descriptions", "languages": "ko|en", "format": "json"}, retries=0).json()["entities"][hit["id"]]
                c = e.get("claims", {})
                val = lambda p: [x["mainsnak"].get("datavalue", {}).get("value") for x in c.get(p, [])]
                for q in val("P17"):
                    if isinstance(q, dict) and q.get("id") in ISO: info["cc"] = ISO[q["id"]]; break
                for t in val("P571"):
                    m = re.match(r"\+(\d{4})", (t or {}).get("time", "") if isinstance(t, dict) else "")
                    if m: info["since"] = m.group(1); break
                ds = e.get("descriptions", {}); info["desc"] = (ds.get("ko") or ds.get("en") or {}).get("value", "")[:120]
                info["qid"] = hit["id"]
            time.sleep(0.6)
        except Exception as ex:
            if "429" in str(ex): self.stop = True
            return None
        self.d[k] = info
        return info


# ───────── 이름 색인 (지난 이야기·공시 맞추기·처음/후속) ─────────
def build_index(news_dir, dart_dir, fd_dir, days=90):
    """정규화 이름 → [(날짜, 종류, 글, 금액, id/주소, 투자사들)]"""
    idx = {}
    cut = (date.today() - timedelta(days=days)).isoformat()
    for f in sorted(news_dir.glob("????-??-??.json")):
        if f.stem < cut: continue
        for d in rj(f, {}).get("items", []):
            if d.get("t") in ("formd", "dart"): continue
            for who in (d.get("co"), d.get("tgt")):
                k = norm(who)
                if len(k) >= 2: idx.setdefault(k, []).append((d["date"], "news", d.get("ko") or d.get("title", ""), d.get("amt") or 0, d["id"], d.get("inv") or [], d.get("kind")))
    for f in sorted(dart_dir.glob("*.json"))[-2:]:
        for r in rj(f, {}).get("rows", []):
            iso, k_, what, corp, cls, tgt, amt, eq, biz, rcp, nm = r
            txt = f"{corp}{' → ' + tgt if tgt else ''} {what}" + (f" {eq}%" if eq and eq not in ("-", "") else "")
            for who in (corp, tgt):
                k = norm(who)
                if len(k) >= 2: idx.setdefault(k, []).append((iso, "dart", txt, amt or 0, "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rcp, [], k_))
    for f in sorted(fd_dir.glob("*.json"))[-4:]:
        for r in rj(f, {}).get("rows", []):
            if r[3] == "Pooled Investment Fund" or r[5] < 1_000_000: continue
            k = norm(r[1])
            if len(k) >= 3: idx.setdefault(k, []).append((r[0], "formd", f"{r[1]} — 미국 비상장 투자 신고 ${r[5] / 1e6:,.1f}M", r[5], f"https://www.sec.gov/Archives/edgar/data/{r[8]}/{str(r[9]).replace('-', '')}/xslFormDX01/primary_doc.xml", [], "vc"))
    return idx


def history(d, idx, usd_krw):
    """→ (지난 이야기 목록, 공시 맞춤 여부, 후속 투자사 목록)"""
    ev, filed, follow = [], False, []
    keys = {norm(d.get("co")), norm(d.get("tgt"))} - {""}
    me = d["id"]
    for k in keys:
        for e in idx.get(k, []):
            if e[4] == me or e[4] == d.get("url"): continue
            days_apart = abs((date.fromisoformat(e[0]) - date.fromisoformat(d["date"])).days)
            if e[1] in ("dart", "formd") and days_apart <= 12 and d.get("t") == "news":
                if (e[6] in ("ma", "pe") and d.get("kind") in ("ma", "pe")) or (e[6] in ("vc", "ipo", "fund") and d.get("kind") in ("vc", "ipo", "fund")): filed = True
            if e[0] < d["date"]:
                for inv in d.get("inv") or []:
                    if inv in e[5] and inv not in follow: follow.append(inv)
            amt = e[3] * usd_krw if e[1] == "formd" else e[3]
            ev.append([e[0], e[1], e[2][:110], round(amt) if amt else 0, e[4]])
    ev.sort(key=lambda x: x[0], reverse=True)
    seen, out = set(), []
    for e in ev:
        key = (e[0], e[2][:30])
        if key in seen: continue
        seen.add(key); out.append(e)
    return out[:6], filed, follow


# ───────── 믿음 등급 ─────────
def grade(d):
    if d.get("t") in ("formd", "dart") or d.get("filed"): return "f"
    if d.get("st") in ("rumor",) or d.get("chk") or (d.get("garb") and d.get("amt")): return "c"
    amts = [x for x in (d.get("amts") or []) if x]
    if d.get("amt") and len(amts) >= 2:
        ok = sum(1 for x in amts if abs(x - d["amt"]) <= 0.1 * d["amt"])
        if ok >= 2: return "m"
        return "c" if len(set(round(x, -8) for x in amts)) > 1 else "s"
    if (d.get("n") or 1) >= 2: return "m"
    return "s"


def counted(d):
    """합계·지도·자에 넣어도 되는 거래인가"""
    return d.get("st", "done") == "done" and d.get("g") in ("f", "m", "s") and d.get("amt") and d.get("amtK") != "debt"


# ───────── 잣대 ─────────
def median(v): return statistics.median(v) if v else 0


def bench(fd_dir, kvca_path, news_dir, fx_usd, formd_ind_map):
    out = {"formd": {}, "kvca": None, "stage": {}}
    qs = sorted(fd_dir.glob("*.json"))
    for f in reversed(qs[:-1] or qs):                                                   # 진행 중인 분기 말고 다 모인 최근 분기
        rows = [r for r in rj(f, {}).get("rows", []) if r[3] != "Pooled Investment Fund" and r[5] > 0]
        if len(rows) < 500: continue
        by = {}
        for r in rows: by.setdefault(formd_ind_map.get(r[3], "etc"), []).append(r[5])
        out["formd"] = {"q": f.stem, "n": len(rows), "med": round(median([r[5] for r in rows]) * fx_usd),
                        "sec": {k: [len(v), round(median(v) * fx_usd)] for k, v in by.items() if len(v) >= 30}}
        break
    kv = rj(kvca_path, {})
    if kv.get("vcs"):
        n = sum(v["cur"][0] for v in kv["vcs"]); a = sum(v["cur"][1] for v in kv["vcs"])
        if n: out["kvca"] = {"yymm": kv.get("yymm"), "n": n, "avg": round(a / n)}
    cut = (date.today() - timedelta(days=90)).isoformat(); st = {}
    for f in sorted(news_dir.glob("????-??-??.json")):
        if f.stem < cut: continue
        for d in rj(f, {}).get("items", []):
            if d.get("kind") == "vc" and d.get("stage") and counted(d): st.setdefault(d["stage"], []).append(d["amt"])
    out["stage"] = {k: [len(v), round(median(v))] for k, v in st.items()}
    return out


REG = {"KR": "KR", "US": "US", "CN": "CN", "HK": "CN", "TW": "CN", "JP": "JP", "IN": "IN", "GB": "EU", "DE": "EU", "FR": "EU", "EU": "EU", "SE": "EU", "NL": "EU", "CH": "EU", "ES": "EU", "IT": "EU"}


def money_map(news_dir):
    """분야 × 권역: 지난 7일 [건수, 중앙값, 합, 가장 큰 한 건 뺀 합] + 그 전 28일 주평균 건수"""
    t = date.today(); c7 = (t - timedelta(days=7)).isoformat(); c35 = (t - timedelta(days=35)).isoformat()
    cur, prev = {}, {}
    for f in sorted(news_dir.glob("????-??-??.json")):
        if f.stem < c35: continue
        for d in rj(f, {}).get("items", []):
            if d.get("st", "done") != "done" or d.get("kind") not in ("vc", "ma", "pe", "fund", "ipo"): continue
            s = (d.get("sec") or ["etc"])[0]; r = REG.get(d.get("cc"), "ETC")
            tgt = cur if d["date"] >= c7 else prev
            x = tgt.setdefault(s, {}).setdefault(r, [])
            x.append(d.get("amt") or 0 if counted(d) else 0)
    out = {}
    for s, m in cur.items():
        for r, v in m.items():
            a = [x for x in v if x]; p = len(prev.get(s, {}).get(r, [])) / 4
            out.setdefault(s, {})[r] = [len(v), round(median(a)) if a else 0, sum(a), sum(a) - (max(a) if a else 0), round(p, 1)]
    for s, m in prev.items():
        for r, v in m.items():
            if r not in out.get(s, {}): out.setdefault(s, {})[r] = [0, 0, 0, 0, round(len(v) / 4, 1)]
    return out


# ───────── 오늘의 딜 ─────────
def daily_pick(deals, state, now_kst):
    """아침 6시 뒤 첫 판에서 한 번 고정. → {day, label, items:[[id, 칸]]}"""
    day = now_kst.date().isoformat()
    cur = state.get("daily") or {}
    if cur.get("day") == day or now_kst.hour < 6: return cur
    since = (now_kst.date() - timedelta(days=1)).isoformat()
    pool = [d for d in deals if d["date"] >= since and d.get("st") == "done"]
    picked, used, sec_n, cc_n = [], set(), {}, {}

    def take(cands, slot, k):
        n = 0
        for d in cands:
            if n >= k: break
            if d["id"] in used: continue
            s = (d.get("sec") or ["etc"])[0]; c = d.get("cc", "WW")
            if s != "etc" and sec_n.get(s, 0) >= 3: continue
            if cc_n.get(c, 0) >= 4: continue
            used.add(d["id"]); picked.append([d["id"], slot]); n += 1
            sec_n[s] = sec_n.get(s, 0) + 1; cc_n[c] = cc_n.get(c, 0) + 1

    big = sorted([d for d in pool if d.get("g") in ("f", "m") and d.get("amt") and d.get("t") == "news" and d.get("amtK") != "debt"], key=lambda d: -d["amt"])
    take(big, "big", 3)
    kr = sorted([d for d in pool if d.get("cc") == "KR" and d.get("kind") == "vc" and d.get("t") == "news"], key=lambda d: (-(bool(d.get("amt")) + bool(d.get("inv")) + bool(d.get("sum"))), -(d.get("n") or 1)))
    take(kr, "kr", 3)
    pm = sorted([d for d in pool if d.get("kind") in ("ma", "pe") and d.get("g") != "c" and d.get("t") == "news" and (d.get("amt") or d.get("tgt"))], key=lambda d: (-(d.get("amt") or 0), -(d.get("n") or 1)))
    take(pm, "ma", 2)
    quiet = sorted([d for d in pool if d.get("quiet")], key=lambda d: -(d.get("amt") or 0))
    take(quiet, "quiet", 1)
    out = {"day": day, "label": now_kst.strftime("%m월 %d일 %H시판"), "items": picked}
    state["daily"] = out
    return out
