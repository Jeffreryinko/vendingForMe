"""deal_kvca.py — 한국 벤처투자회사 전체 (DIVA 전자공시, 토큰 0). deal_run.py 가 부름.

한국벤처캐피탈협회 '벤처투자회사 전자공시(DIVA, diva.kvca.or.kr)'는 법으로 공시하는 공개 자료라서
창업투자회사·신기술금융사·액셀러레이터 등 약 400곳의 투자 실적·운용 조합(펀드)·회사 기본 정보가 다 나온다.

  투자 실적  : 올해 1월~공시월, 작년 1~12월 — 투자한 회사 수·금액 (고유계정 / 조합)
  조합(펀드) : 운용 중인 조합 이름·등록일·결성총액·만기·투자 분야·모태펀드 출자 여부 (공동 운용사 포함)
  회사 정보  : 설립일·직원 수·주소(시·구까지만)·홈페이지 — 전화·사업자번호·담당자 이름은 담지 않음

3일마다 새로 받음 (공시는 한 달에 한 번). 회사 정보는 30일마다, 한 번에 150곳까지.
출력: data/deal/kvca.json (목록) · data/deal/kvca/<id>.json (자세히)
"""
from __future__ import annotations

import html, re, time
from datetime import date, timedelta
from pathlib import Path

import requests
import ai_run as A

rj, wj, log, now_iso = A.rj, A.wj, A.log, A.now_iso
BASE = "http://diva.kvca.or.kr"
UA = {"User-Agent": "Mozilla/5.0 (compatible; vendingForMe-bot/1.0; +https://jeffreryinko.github.io/vendingForMe/)"}
SUFFIX = r"(창업투자|벤처투자|벤처캐피탈|인베스트먼트|인베스트|파트너스|벤처스|투자파트너스|캐피탈|캐피털|기술투자|투자|홀딩스|액셀러레이터|기술지주회사|기술지주)$"


def _req(path, data=None, timeout=90):
    for i in range(3):
        try:
            r = requests.post(BASE + path, data=data, headers=UA, timeout=timeout) if data is not None else requests.get(BASE + path, headers=UA, timeout=timeout)
            r.raise_for_status(); r.encoding = "utf-8"; return r.text
        except requests.RequestException:
            if i == 2: raise
            time.sleep(5 * (i + 1))


def _txt(x): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x or ""))).strip()
def _num(x):
    try: return int(re.sub(r"[^\d]", "", x) or 0)
    except Exception: return 0


def invest(bf, to):
    """투자 실적 (기간) → {id: [이름, 고유 회사수, 고유 금액, 조합 회사수, 조합 금액, 합계 회사수, 합계 금액]}"""
    t = _req("/div/dii/DivItmInvstPrfmInq", {"TOTAL_YN": "Y", "PAGE_INDEX": "1", "S_PRFM_TP_CD": "", "S_TRD_DD_BF": bf, "S_TRD_DD_TO": to})
    out = {}
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        m = re.search(r"openPopOperInstInfo\('([^']+)'", r)
        if not m: continue
        tds = [_txt(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        nums = [_num(x) for x in tds if re.fullmatch(r"[\d,]+", x)]
        name = next((x for x in tds if x and not re.fullmatch(r"[\d,]+", x)), "")
        if len(nums) >= 6: out[m.group(1)] = [name] + nums[:6]
    return out


def funds(yymm):
    """조합 현황 전체 → [[조합ID, [운용사 ID들], [운용사 이름들], 조합명, 등록일, 결성총액, 만기, 분야, 목적, 지원]]"""
    t = _req("/div/dii/DivItmAssoInq", {"TOTAL_YN": "Y", "PAGE_INDEX": "1", "S_DISCLS_YYMM": yymm}, timeout=180)
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        if len(tds) < 8: continue
        ids = re.findall(r'name="OPER_INST_ID" value="(OP\w+)"', tds[1]); names = [_txt(a) for a in re.findall(r"<a[^>]*>(.*?)<input", tds[1], re.S)]
        aid = re.search(r'name="ASCT_ID" value="(\w+)"', tds[2])
        out.append([aid.group(1) if aid else "", ids, names, _txt(tds[2]).rstrip(" *"), _txt(tds[3]), _num(tds[4]), _txt(tds[5]), _txt(tds[6]), _txt(tds[7]), _txt(tds[8]) if len(tds) > 8 else ""])
    return out


def company(oid, yymm):
    """회사 기본 정보 (공개 항목 중 설립일·직원 수·시/구·홈페이지만)"""
    t = _req(f"/div/cmn/DivCmnComInfo/pop1?OPER_INST_ID={oid}&DISCLS_YYMM={yymm}", timeout=40)
    cells = [_txt(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", t, re.S)]
    kv = {cells[i]: cells[i + 1] for i in range(0, len(cells) - 1, 2)}
    addr = re.sub(r"^\(\d+\)\s*", "", kv.get("주소", ""))
    city = " ".join(addr.split()[:2])                                               # '서울특별시 강남구' 까지만
    site = kv.get("홈페이지주소", "")
    if site and not site.startswith("http"): site = "https://" + site
    return {"name": kv.get("회사명", ""), "since": kv.get("설립일자", ""), "emp": _num(kv.get("종업원수", "").split("명")[0]), "city": city, "site": site}


def stem(name):
    s = re.sub(r"\(주\)|㈜|주식회사|\s", "", name)
    return re.sub(SUFFIX, "", s)


def variants(name):
    """'새한창업투자' → 새한창업투자 · 새한벤처스 · 새한인베스트먼트 … (기사에선 브랜드 이름을 많이 씀)"""
    st = stem(name); out = {re.sub(r"\s", "", name)}
    if len(st) >= 2 and re.search(r"[가-힣A-Za-z]", st):
        for sx in ("창업투자", "벤처투자", "벤처스", "인베스트먼트", "파트너스", "벤처파트너스", "투자파트너스", "캐피탈"): out.add(st + sx)
    return [v for v in out if len(v) >= 4]


def build(out_dir: Path, news_dir: Path, now_deals, deadline):
    st_path = out_dir / "_state" / "kvca.json"; state = rj(st_path, {})
    today = date.today()
    if state.get("day", "") > (today - timedelta(days=3)).isoformat() and (out_dir / "kvca.json").exists():
        log("한국 VC 공시: 3일 안에 받음 → 건너뜀 (기사 맞추기만)")
    else:
        try:
            page = _req("/div/dii/DivItmAssoInq")
            m = re.search(r'id="S_DISCLS_YYMM"[^>]*value="(\d{6})"', page) or re.search(r'name="S_DISCLS_YYMM"[^>]*value="(\d{6})"', page)
            yymm = m.group(1) if m else today.strftime("%Y%m")
            y, mm = int(yymm[:4]), yymm[4:]
            cur = invest(f"{y}-01", f"{y}-{mm}"); prev = invest(f"{y - 1}-01", f"{y - 1}-12")
            fl = funds(yymm)
            state.update({"day": today.isoformat(), "yymm": yymm, "cur": cur, "prev": prev, "funds": fl})
            log(f"한국 VC 공시 {yymm}: 투자 실적 {len(cur)}곳 · 조합 {len(fl):,}개")
        except Exception as e:
            log(f"한국 VC 공시 못 받음 — 지난 자료로: {str(e)[:80]}")
    if not state.get("cur"): wj(st_path, state); return
    yymm = state["yymm"]; cur, prev, fl = state["cur"], state.get("prev", {}), state.get("funds", [])
    # 회사 정보 (30일마다, 한 번에 150곳)
    info = state.setdefault("info", {}); cut = (today - timedelta(days=30)).isoformat(); n = 0
    ids = set(cur) | set(prev) | {i for f in fl for i in f[1]}
    for oid in sorted(ids, key=lambda i: -(cur.get(i, [0] * 7)[6])):
        if n >= 150 or time.time() > deadline: break
        if info.get(oid, {}).get("day", "") >= cut: continue
        try: info[oid] = dict(company(oid, yymm), day=today.isoformat()); n += 1; time.sleep(0.4)
        except Exception as e: log(f"VC 정보 실패 {oid}: {str(e)[:50]}"); break
    wj(st_path, state)
    # 이름
    names = {}
    for oid, v in list(cur.items()) + list(prev.items()): names.setdefault(oid, v[0])
    for f in fl:
        for oid, nm in zip(f[1], f[2]): names.setdefault(oid, nm)
    for oid, v in info.items():
        if v.get("name"): names[oid] = v["name"]
    # 기사 맞추기 (최근 90일)
    pool, seen = [], set()
    for d in now_deals:
        if d["id"] not in seen: seen.add(d["id"]); pool.append(d)
    dcut = (today - timedelta(days=90)).isoformat()
    for f in sorted(news_dir.glob("????-??-??.json"), reverse=True):
        if f.stem < dcut: break
        for d in rj(f, {}).get("items", []):
            if d["id"] not in seen: seen.add(d["id"]); pool.append(d)
    rx = {oid: re.compile("|".join(map(re.escape, variants(nm)))) for oid, nm in names.items() if variants(nm)}
    hits = {oid: [] for oid in names}
    for d in pool:
        if d.get("t") in ("formd", "dart"): continue
        txt = re.sub(r"\s", "", " ".join([" ".join(d.get("inv") or []), d.get("title", ""), d.get("ko", ""), d.get("sum", "")]))
        for oid, r in rx.items():
            if r.search(txt): hits[oid].append(d)
    # 조합: 운용사별
    byvc = {}
    for f in fl:
        for oid in f[1]: byvc.setdefault(oid, []).append(f)
    (out_dir / "kvca").mkdir(parents=True, exist_ok=True)
    lst = []
    tdy = today.isoformat()
    for oid, nm in names.items():
        c, p, fs = cur.get(oid), prev.get(oid), byvc.get(oid, [])
        live = [f for f in fs if f[6] >= tdy]
        i = info.get(oid, {})
        hs = sorted(hits.get(oid, []), key=lambda d: d["date"], reverse=True)
        base = {"id": oid, "name": nm, "since": i.get("since", "")[:4], "city": i.get("city", ""),
                "cur": [c[5], c[6]] if c else [0, 0], "prev": [p[5], p[6]] if p else [0, 0], "funds": len(live), "fundSum": sum(f[5] for f in live), "n90": len(hs)}
        lst.append(base)
        det = dict(base, sinceFull=i.get("since", ""), emp=i.get("emp", 0), site=i.get("site", ""), curD=c[1:] if c else [], prevD=p[1:] if p else [], yymm=yymm,
                   fundList=[[f[3], f[4], f[5], f[6], f[7], f[8], f[9], [x for x in f[2] if x != nm]] for f in sorted(fs, key=lambda f: f[4], reverse=True)[:40]],
                   allFunds=len(fs), allFundSum=sum(f[5] for f in fs),
                   deals=[{k: d.get(k) for k in ("id", "date", "kind", "stage", "title", "ko", "amt", "amtS", "cc", "co", "tgt", "url", "sec", "inv", "n", "src", "t", "lang", "sum") if d.get(k) not in (None, "", [])} for d in hs[:30]])
        wj(out_dir / "kvca" / f"{oid}.json", det)
    lst.sort(key=lambda x: (-x["cur"][1], -x["fundSum"]))
    wj(out_dir / "kvca.json", {"at": now_iso(), "yymm": yymm, "src": BASE, "vcs": lst})
    log(f"한국 VC {len(lst)}곳 정리 · 회사 정보 새로 {n}곳 · 최근 90일 기사에 나온 곳 {sum(1 for x in lst if x['n90'])}곳")
