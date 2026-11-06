# -*- coding: utf-8 -*-
"""뇌 로봇 — 뇌과학 소식 모으기 (하루 2번, 토큰 0) → data/brain/

  한국어 기사: 구글 뉴스 RSS 검색 (뇌과학·신경과학·뇌 연구 …)
  영문 대중 매체: ScienceDaily 신경과학 · Neuroscience News · Science News 신경과학 · The Transmitter
                  → 제목·요약을 NLLB 로 한국어 번역 (AI·도구 탭과 같은 모델)
  기사마다 나온 부위를 robot/brain_regions.py 의 낱말로 찾아 붙임 → 화면 지도에 불이 들어옴
  위키백과 첫 문단(부위 52개)은 7일에 한 번 받아 data/brain/wiki.json 에 둠 ('깊게' 보기용)

출처가 깨지면 직전 기사를 그대로 두고, 4번(약 2일) 넘게 계속 실패하면 화면 맨 위·설정 '출처 상태'에 표시.
"""
from __future__ import annotations
import json, os, re, sys, time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
import ai_run as A                                   # get · clean · hid · NLLB 번역
import brain_regions as BR

KST = timezone(timedelta(hours=9))
OUT = Path(__file__).resolve().parent.parent / "data" / "brain"
KEEP_DAYS = 30
log = A.log

KO_QUERIES = ["뇌과학", "신경과학", "뇌 연구", "뇌 영상 연구", "치매 뇌 연구", "뇌 신경 회로"]
EN_FEEDS = [
    ("sd", "ScienceDaily", "https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml"),
    ("nn", "Neuroscience News", "https://neurosciencenews.com/feed/"),
    ("sn", "Science News", "https://www.sciencenews.org/topic/neuroscience/feed"),
    ("tt", "The Transmitter", "https://www.thetransmitter.org/feed/"),
]
SRC_HOME = {"gn": ["한국어 기사", "https://news.google.com/search?q=%EB%87%8C%EA%B3%BC%ED%95%99&hl=ko"],
            **{k: [n, u.split("/rss")[0].split("/feed")[0]] for k, n, u in EN_FEEDS}}
BRAIN_KO = re.compile(r"뇌|신경|치매|알츠하이머|파킨슨|기억력|도파민|세로토닌|뉴런")
ADS = re.compile(r"광고|분양|할인|이벤트|쇼핑|주가|증시|특징주")

# ───── 부위 찾기 ─────
KO_FIX = {"시상": r"시상(?![식자대금품])", "백질": r"(?<!단)(?<!단 )백질", "피질": r"(?<![가-힣])피질"}   # '시상식'·'단백질' 같은 말은 빼기
def _ko_pats():
    pats = []
    for r in BR.R:
        for w in r["kw"]:
            pats.append((len(w), re.compile(KO_FIX.get(w, re.escape(w))), r["id"]))
    return sorted(pats, key=lambda x: -x[0])
def _en_pats():
    return [(re.compile(r"\b" + re.escape(w), re.I), r["id"]) for r in BR.R for w in r["kwen"]]
KO_P, EN_P = _ko_pats(), _en_pats()

def regions_of(ko_text, en_text=""):
    found, t = [], ko_text or ""
    for _, p, rid in KO_P:                              # 긴 낱말부터 찾고 지움 ('시상하부' 안의 '시상'을 또 세지 않게)
        if p.search(t):
            if rid not in found: found.append(rid)
            t = p.sub(" ", t)
    for p, rid in EN_P:
        if en_text and p.search(en_text) and rid not in found: found.append(rid)
    if "hypothalamus" in found and "thalamus" in found and not re.search(r"(?<!hypo)thalam", en_text or "", re.I) and not re.search(KO_FIX["시상"] + r"(?!하부)", ko_text or ""):
        found.remove("thalamus")
    return found[:6]

def iso(d):
    try: return parsedate_to_datetime(d).astimezone(KST).strftime("%Y-%m-%dT%H:%M")
    except Exception:
        m = re.match(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?", d or ""); return m.group(0) if m else ""

# ───── 출처 ─────
def src_gn():
    out, seen = [], set()
    for q in KO_QUERIES:
        x = ET.fromstring(A.get(f"https://news.google.com/rss/search?q={quote(q)}+when:7d&hl=ko&gl=KR&ceid=KR:ko").content)
        for it in x.iter("item"):
            title = A.clean(it.findtext("title"), 240); srcn = A.clean(it.findtext("source"), 60)
            if srcn and title.endswith(" - " + srcn): title = title[: -len(srcn) - 3]
            key = re.sub(r"\W", "", title)[:40]
            if key in seen or not BRAIN_KO.search(title) or ADS.search(title): continue
            seen.add(key)
            out.append({"id": "gn" + A.hid(it.findtext("link") or title), "src": "gn", "lang": "ko", "title": title, "pub": srcn,
                        "url": (it.findtext("link") or "").strip(), "date": iso(it.findtext("pubDate"))})
        time.sleep(1)
    out.sort(key=lambda p: p["date"], reverse=True)
    kept = []                                            # 같은 보도자료를 여러 매체가 낸 것은 하나로 (낱말 절반 이상 겹치면)
    for p in out:
        w = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", p["title"]))
        dup = next((k for k in kept if len(w & k["_w"]) >= 0.5 * min(len(w), len(k["_w"]))), None)
        if dup: dup["dup"] = dup.get("dup", 0) + 1; continue
        p["_w"] = w; kept.append(p)
    for p in kept: p.pop("_w", None)
    return kept[:60]

def src_en(key, name, url):
    out = []
    for p in A.rss_items(url, 40)[:30]:
        if not p.get("url"): continue
        s = re.sub(r"\s*(The post .*|Read more.*|Continue reading.*)$", "", p.get("sum", ""))
        out.append({"id": key + A.hid(p["url"]), "src": key, "lang": "en", "title": p["title"], "pub": name, "url": p["url"],
                    "date": iso(p.get("date", "")), "sum": s[:400]})
    return out

def fail(health, k, e):
    h = health.setdefault(k, {"n": 0}); h["n"] += 1; h["last"] = str(e)[:200]; h["at"] = A.now_iso()
    log(f"⚠ {k}: {e}")

# ───── 위키백과 첫 문단 (7일에 한 번) ─────
def wiki_refresh(force=False):
    path = OUT / "wiki.json"; cur = A.rj(path, {})
    if not force and cur.get("_at", "") > (datetime.now(KST) - timedelta(days=7)).strftime("%Y-%m-%d"): return
    hdr = {"User-Agent": A.UA}
    out = {"_at": A.today()}
    def query(lang, titles):
        for i in range(3):
            r = A.requests.get(f"https://{lang}.wikipedia.org/w/api.php", headers=hdr, timeout=40,
                               params={"action": "query", "format": "json", "formatversion": 2, "prop": "extracts", "exintro": 1, "explaintext": 1,
                                       "redirects": 1, "titles": "|".join(titles), "maxlag": 5})
            if r.status_code == 200 and "error" not in r.json(): return r.json()["query"]
            time.sleep(15 * (i + 1))
        raise RuntimeError(f"{lang} wiki {r.status_code}")
    def pick(q, t):
        m = {x["from"]: x["to"] for x in q.get("normalized", []) + q.get("redirects", [])}
        tt = m.get(m.get(t, t), m.get(t, t)); pg = {p["title"]: p for p in q.get("pages", [])}.get(tt)
        return (tt, pg["extract"]) if pg and not pg.get("missing") and pg.get("extract") else (None, None)
    regs = BR.R
    for b in range(0, len(regs), 10):
        part = regs[b:b + 10]
        q = query("ko", [r["wiki"] for r in part]); time.sleep(2)
        miss = []
        for r in part:
            tt, x = pick(q, r["wiki"])
            if not tt and not re.search(r"[A-Za-z]", r["wiki"]):   # 한국어 제목이 없으면 대표 이름으로 한 번 더
                q2 = query("ko", [r["ko"]]); tt, x = pick(q2, r["ko"]); time.sleep(1)
            if tt: out[r["id"]] = {"t": tt, "x": x[:1500], "u": "https://ko.wikipedia.org/wiki/" + quote(tt.replace(" ", "_")), "l": "ko"}
            else: miss.append(r)
        if miss:
            q = query("en", [r["en"] for r in miss]); time.sleep(2)
            for r in miss:
                tt, x = pick(q, r["en"])
                if tt: out[r["id"]] = {"t": tt, "x": x[:1500], "u": "https://en.wikipedia.org/wiki/" + quote(tt.replace(" ", "_")), "l": "en"}
    if len(out) > 20: A.wj(path, out); log(f"위키 첫 문단 {len(out) - 1}개 (영문 {sum(1 for v in out.values() if isinstance(v, dict) and v.get('l') == 'en')})")


def main():
    t0 = time.time(); deadline = t0 + int(os.environ.get("BRAIN_MAX_MINUTES", "30")) * 60
    OUT.mkdir(parents=True, exist_ok=True)
    health = A.rj(OUT / "_health.json", {}); day = A.today()
    old = A.rj(OUT / "news.json", {}).get("items", [])
    olds = {}
    for p in old: olds.setdefault(p["src"], []).append(p)

    got = []
    try: g = src_gn(); got += g; health.pop("gn", None); log(f"한국어 기사 {len(g)}")
    except Exception as e: fail(health, "gn", e)
    for k, n, u in EN_FEEDS:
        try: g = src_en(k, n, u); got += g; health.pop(k, None); log(f"{n} {len(g)}")
        except Exception as e: fail(health, k, e)
        time.sleep(1)

    # 합치기 (옛 기사 유지, 30일)
    by = {p["id"]: p for p in old}
    seen_first = A.rj(OUT / "_seen.json", {})
    for p in got:
        o = by.get(p["id"], {})
        for f in ("ko", "ksum", "first"):
            if o.get(f): p[f] = o[f]
        by[p["id"]] = p
    cut = (datetime.now(KST) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    items = [p for p in by.values() if (p.get("date") or day) >= cut]
    for p in items:
        p["first"] = p.get("first") or seen_first.get(p["id"]) or day
        seen_first[p["id"]] = p["first"]
        p["new"] = p["first"] == day

    # 번역 (영문)
    mem = A.rj(OUT / "_tr.json", {}); run = A.nllb()
    jobs = []
    for p in items:
        if p["lang"] != "en": continue
        if not p.get("ko"): jobs.append((p, "ko", p["title"]))
        if p.get("sum") and not p.get("ksum"): jobs.append((p, "ksum", p["sum"]))
    res = A.translate_texts(run, [j[2] for j in jobs], mem, deadline)
    for (p, f, _), v in zip(jobs, res):
        if v: p[f] = v
    if len(mem) > 6000: mem = dict(list(mem.items())[-4000:])
    A.wj(OUT / "_tr.json", mem)

    # 부위 붙이기
    for p in items:
        p["rs"] = regions_of(p.get("title", "") if p["lang"] == "ko" else "",                     # 영문 기사는 원문 영어로만 (기계번역 띄어쓰기 탓에 헛것이 걸림)
                             " ".join([p.get("title", ""), p.get("sum", "")]) if p["lang"] == "en" else "")
    items.sort(key=lambda p: (p.get("date") or p["first"]), reverse=True)
    items = items[:400]

    cnt = {}
    for p in items:
        for r in p["rs"]: cnt[r] = cnt.get(r, 0) + 1
    broken = {k: v for k, v in health.items() if v.get("n", 0) >= 4}
    A.wj(OUT / "news.json", {"at": A.now_iso(), "day": day, "items": items})
    A.wj(OUT / "_seen.json", {k: v for k, v in seen_first.items() if v >= cut})
    A.wj(OUT / "_index.json", {"at": A.now_iso(), "day": day, "n": len(items), "new": sum(1 for p in items if p["new"]), "count": cnt,
                               "broken": broken, "srcs": SRC_HOME, "translated": run is not None})
    A.wj(OUT / "_health.json", health)
    A.wj(OUT / "_meta.json", {"updatedAt": A.now_iso(), "by": "brain-robot", "label": datetime.now(KST).strftime("%m월 %d일 %H시판")})
    try:
        if not os.environ.get("BRAIN_NO_WIKI"): wiki_refresh("--wiki" in sys.argv)
    except Exception as e: fail(health, "wiki", e); A.wj(OUT / "_health.json", health)
    log(f"끝 {round(time.time() - t0)}초 · 기사 {len(items)} (새 {sum(1 for p in items if p['new'])}) · 부위 붙은 기사 {sum(1 for p in items if p['rs'])} · 고장 {len(broken)}")


if __name__ == "__main__":
    main()
