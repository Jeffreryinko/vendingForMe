"""sisa_edit.py — 시사 '로봇 편집장' (토큰 0). 클로드 편집장 예약 작업을 대신함.
sisa_run.py 가 판을 만든 뒤 바로 실행 (3시간마다). AI 글쓰기 없이 '모으고 고르고 옮기기'만 합니다.

  1. 새 이슈 후보(낱말 묶음)에 제목·분야·요약을 붙임 — 제목 = 가장 대표적인 기사 제목, 요약 = 그 기사 피드 설명(기계번역)
  2. 꼭 알아야 할 5개(top) = 나라 수·출처 수·새 글 수 점수 순
  3. 큰 이슈 10개: 용어(이름 사전) · 배경(이름 사전/위키백과 첫 문장) · 나라별 시각(나라마다 대표 기사 제목) · 먼저 읽을 기사
  4. 단신 50개 = 어디에도 안 묶인 새 뉴스, 나라마다 고르게, 요약 = 피드 설명(기계번역)
  5. 흐름(AI·경제) · 나라별 2줄 · 이름 사전(위키데이터에서 사람·기관·장소만 자동 추가)
지어내는 문장이 없으므로 '해설' 대신 '기사 요약'으로 표시합니다 (method: auto-v1).

  python robot/sisa_edit.py [판ID]      # 판ID 없으면 가장 최근 판
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/sisa"
KST = timezone(timedelta(hours=9))
sys.path.insert(0, str(ROOT / "robot/crawler")); sys.path.insert(0, str(ROOT / "robot"))
from cluster import tokens, GENERIC  # noqa: E402
import fresh as F  # noqa: E402
from nllb_multi import Ko  # noqa: E402

UA = "vendingForMe/1.0 (https://jeffreryinko.github.io/; robot)"
NO_NET = os.environ.get("SISA_EDIT_NO_NET") == "1"
DEADLINE = time.time() + int(os.environ.get("SISA_EDIT_MINUTES", "12")) * 60
MAX_STORIES, MAX_BRIEFS, BRIEF_TARGET = 45, 60, 50
PAYWALL = {"nyt-world", "lemonde", "lefigaro", "folha", "uol", "spiegel", "bild", "elpais", "ft-world", "nikkei-wor"}
SKIP_RE = re.compile(r"운세|날씨|기상|광고|이벤트|구독|시간표|horoscope|weather|sponsored|promo|wordle|crossword|live updates?", re.I)

CATS = [  # (분야, 낱말) — 앞에 있을수록 먼저
    ("war", "전쟁 공습 폭격 미사일 휴전 교전 침공 포격 드론 군사 병력 하마스 헤즈볼라 탈레반 반군 무장 포로 전선 참전 국방"),
    ("dis", "지진 홍수 태풍 허리케인 산불 화재 폭발 추락 붕괴 폭우 폭설 쓰나미 사망자 실종 구조 대피 참사 사고 탈선 전염병 감염"),
    ("spo", "축구 야구 농구 배구 경기 우승 월드컵 올림픽 감독 리그 선수 골 득점 결승 테니스 골프 F1 챔피언스 시즌 이적"),
    ("tech", "AI 인공지능 반도체 칩 엔비디아 오픈AI 챗GPT 구글 애플 메타 마이크로소프트 앱 스마트폰 해킹 사이버 데이터센터 로봇 우주 로켓 위성 테슬라 삼성전자 소프트웨어"),
    ("eco", "경제 증시 주가 주식 금리 물가 환율 관세 수출 무역 실적 인플레이션 성장률 은행 투자 유가 석유 부동산 집값 예산 세금 기업 시장 달러 비트코인 암호화폐 노조 파업 임금 일자리"),
    ("cul", "영화 드라마 음악 가수 배우 콘서트 앨범 전시 축제 아이돌 케이팝 K팝 소설 작가 박물관 공연 넷플릭스 시상식"),
    ("pol", "선거 대통령 총리 의회 국회 정당 법안 장관 탄핵 정상회담 외교 제재 투표 내각 여당 야당 대선 총선 개헌 연정 정부 대사 협상"),
    ("soc", "시위 경찰 재판 법원 판결 체포 범죄 살인 학교 교육 이민 난민 인권 의료 병원 환경 기후 여성 노동"),
]
CATS = [(c, set(w.split())) for c, w in CATS]
AIW = re.compile(r"AI|인공지능|챗GPT|오픈AI|엔비디아|반도체|데이터센터|생성형|LLM|제미나이|클로드|앤트로픽|딥시크", re.I)


def log(*a): print(*a, flush=True)
def rj(p, d=None):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d
def wj(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def get_json(url, timeout=12):
    if NO_NET: return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log(f"  네트워크 실패: {url[:80]} ({e})"); return None


# ── 읽기 ──
def load(ed):
    E = rj(DATA / f"editions/{ed}.json", {})
    items = {}
    for f in (DATA / "feed").glob(f"{ed}__*.json"):
        d = rj(f, {})
        for it in d.get("items", []): it["_lang"] = d.get("lang", "en"); items[it["id"]] = it
    src = {s["id"]: s for s in E.get("sources", [])}
    return E, items, src


def clean_title(t):
    t = re.sub(r"^\s*[\[【(（][^\]】)）]{1,8}[\]】)）]\s*", "", t or "")          # [속보] (종합) 같은 머리표
    t = re.sub(r"\s+[-–|ㅣ·]\s+[^-–|ㅣ·]{2,25}$", "", t)                        # ' - 연합뉴스' 같은 꼬리
    t = t.strip()
    for a, b in (("“", "”"), ('"', '"'), ("‘", "’"), ("'", "'")):
        if len(t) > 2 and t[0] == a and t[-1] == b and t.count(a) == (1 if a != b else 2): t = t[1:-1]
    return t


def short(t, n=170):
    t = re.sub(r"\s+", " ", t or "").strip()
    t = re.split(r"\s*(?:المصدر|Source:|출처:)", t)[0]
    if len(t) <= n: return t
    cut = max(t.rfind(x, 0, n) for x in (". ", "다. ", "요. ", "。", "! ", "? "))
    return (t[:cut + 1] if cut > 40 else t[:n].rsplit(" ", 1)[0] + "…").strip()


def cat_of(texts):
    toks = Counter()
    for t in texts:
        for c, ws in CATS:
            for w in ws:
                if w in t: toks[c] += 1 + (len(w) > 2)
    return toks.most_common(1)[0][0] if toks else "soc"


class Ed:
    def __init__(self, ed):
        self.ed = ed
        self.E, self.items, self.src = load(ed)
        self.ents = rj(DATA / "brief/ents.json", {"map": {}})
        self.brief = rj(DATA / f"brief/{ed}.json", {"edition": ed, "map": {}})
        self.ko = Ko(DATA / "_nllb.json")
        self.SC = {"reddit-worldnews": "WW"}

    # 글 하나
    def ctry(self, it): return self.SC.get(it["s"], it["c"])
    def kt(self, it): return it.get("ko") or (it["t"] if it["_lang"] == "ko" else "")
    def sname(self, it):
        n = (self.src.get(it["s"]) or {}).get("n", it["s"])
        return re.sub(r"\s*\([^)]*\)", "", n).strip() or n

    @staticmethod
    def eun(name):
        """'한겨레는' / '연합뉴스는' / '중앙일보는' — 받침 있으면 '은'"""
        c = name[-1] if name else ""
        if "가" <= c <= "힣": return name + ("은" if (ord(c) - 0xAC00) % 28 else "는")
        return name + "는"

    def stories(self): return [s for s in self.E.get("stories", []) if s.get("kind") != "brief"]
    def briefs(self): return [s for s in self.E.get("stories", []) if s.get("kind") == "brief"]

    def rep(self, s):
        """이슈의 대표 기사: 다른 글과 낱말이 가장 많이 겹치는 뉴스 (한국어 제목 있는 것)"""
        its = [self.items[i] for i in s["items"] if i in self.items and self.kt(self.items[i])]
        if not its: return None
        tk = {it["id"]: tokens(self.kt(it)) - GENERIC for it in its}
        def sc(it):
            c = sum(len(tk[it["id"]] & tk[o["id"]]) for o in its if o is not it)
            return c + (2 if it["k"] == "news" else 0) + (1 if it["_lang"] == "ko" else 0) + (1 if it.get("sm") else 0) - len(self.kt(it)) / 400
        return max(its, key=sc)

    def score(self, s):
        """순위 점수 = 최근 24시간에 불어난 폭 ÷ (가장 새 글 나이 + 2시간)^1.2 — 새 글이 끊기면 내려감 (robot/fresh.py)"""
        return F.heat(s, self.items, self.ed, self.ctry)

    # ── 번역 묶음: 대표 기사·단신의 피드 설명 ──
    def translate_sm(self, ids):
        pairs = [(short(self.items[i].get("sm", ""), 400), self.items[i]["_lang"]) for i in ids]
        out = self.ko.many(pairs, deadline=DEADLINE)
        return {i: short(o, 200) for i, o in zip(ids, out) if o}

    def tighten(self, s, r):
        """대표 기사와 핵심 낱말이 2개 이상(고유명사면 1개) 겹치는 글만 남김 — 흔한 말로 엉뚱한 글이 줄줄이 묶이는 것 막기"""
        rt = tokens(self.kt(r)) - GENERIC; keep = []
        for i in s["items"]:
            it = self.items.get(i)
            if not it: continue
            if it is r: keep.append(i); continue
            sh = (tokens(self.kt(it)) - GENERIC) & rt
            if len(sh) >= 2 or sh & self.proper(): keep.append(i)
        srcs = {self.items[i]["s"] for i in keep}
        if len(keep) < 2 or len(srcs) < 2: return False
        s["items"] = keep
        s["countries"] = sorted({self.ctry(self.items[i]) for i in keep}); s["langs"] = sorted({self.items[i]["_lang"] for i in keep})
        return True

    # ── 1. 새 이슈 후보 ──
    def name_candidates(self):
        n = 0; need = {}
        for s in self.stories():
            if s.get("method") == "auto-v1" and s.get("rep_id") in self.items:
                if not self.tighten(s, self.items[s["rep_id"]]): s["_drop"] = True
                continue
            if s.get("cat") or s.get("method") in ("ai-v1", "auto-v1"): continue
            r = self.rep(s)
            if not r or not self.tighten(s, r): s["_drop"] = True; continue
            s["title"] = clean_title(self.kt(r))
            s["cat"] = cat_of([self.kt(self.items[i]) for i in s["items"] if i in self.items])
            s["method"] = "auto-v1"; s["rep"] = r["id"]; s["rep_id"] = r["id"]
            cs = sorted({self.ctry(self.items[i]) for i in s["items"] if i in self.items})
            s["kind"] = "global" if len(cs) >= 2 else "local"; s["where"] = cs[:3] if len(cs) <= 3 else [Counter(self.ctry(self.items[i]) for i in s["items"] if i in self.items).most_common(1)[0][0]]
            if r.get("sm"): need[s["id"]] = r["id"]
            n += 1
        tr = self.translate_sm(list(dict.fromkeys(need.values())))
        for s in self.stories():
            if s.get("rep") in tr and not s.get("key"):
                s["sum"] = tr[s["rep"]]
                s["key"] = f"{self.sname(self.items[s['rep']])} 기사 요약(기계번역): {tr[s['rep']]}"
        self.E["stories"] = [s for s in self.E["stories"] if not s.pop("_drop", False)]
        log(f"새 이슈 이름 붙임 {n}개 (요약 번역 {len(tr)}개)")

    # ── 2. 정리 + top ──
    def rank(self):
        for s in self.stories(): F.stamp(s, self.items, self.ed, added=bool(s.get("grow")))     # 수명 표시(new·hot·on·cool)
        st = sorted(self.stories(), key=self.score, reverse=True)
        # 같은 사건이 두 이슈로 갈라진 것 합치기: 제목 핵심 낱말이 2개 이상 겹치면 큰 쪽으로
        kept = []
        for s in st:
            tk = {t for t in tokens(s.get("title", "")) if t not in GENERIC}
            # 2개 이상 겹치거나, 이름 사전에 있는 고유명사(사람·장소·기관·사건)가 1개라도 겹치면 같은 사건
            host = next((k for k in kept if len(tk & k[1]) >= 2 or (tk & k[1] & self.proper())), None)
            if host and s.get("method") != "ai-v1":
                h = host[0]; h["items"] = h["items"] + [i for i in s["items"] if i not in h["items"]]
                h["delta"] = "grown" if h.get("delta") == "same" else h.get("delta"); continue
            kept.append((s, tk))
        st = [k[0] for k in kept]
        for s in st: F.stamp(s, self.items, self.ed, added=bool(s.get("grow")))
        st.sort(key=self.score, reverse=True)
        keep = st[:MAX_STORIES]
        br = self.briefs()
        br.sort(key=lambda s: (s.get("delta") != "new", -(s.get("grow") or 0)))
        self.E["stories"] = keep + br[:MAX_BRIEFS]
        for s in self.E["stories"]: s.pop("top", None)
        # 꼭 알아야 할 것: 새 이슈·커지는 이슈만, 2개국·2곳 이상이 다룬 것, 같은 분야·나라 2개까지 (모자라면 억지로 안 채움)
        tops = F.pick_top(keep, tokens, GENERIC, wide=lambda s: F.breadth(s, self.items, self.ed, self.ctry), proper=self.proper())
        for k, s in enumerate(tops): s["top"] = k + 1
        log(f"이슈 {len(keep)}개 (뺀 것 {len(st) - len(keep)}) · 꼭 알아야 할 {len(tops)}개: " + " / ".join(f"[{s.get('life')}] " + s.get("title", "")[:20] for s in tops))

    def proper(self):
        if not hasattr(self, "_proper"):
            m = self.ents.get("map") or {}
            self._proper = {n for n, e in m.items() if e.get("t") in ("person", "place", "org", "party", "event") and len(n) >= 3 and n not in GENERIC}
        return self._proper

    # ── 3. 큰 이슈 10개 곁들임 ──
    def ent_index(self):
        if hasattr(self, "_eidx"): return self._eidx
        idx = []
        for name, e in (self.ents.get("map") or {}).items():
            for n in [name] + [a for a in (e.get("a") or []) if a]:
                if len(n) >= 2: idx.append((n, name))
        idx.sort(key=lambda x: -len(x[0])); self._eidx = idx; return idx

    def ents_in(self, text, k=5):
        hit = Counter(); used = []
        for n, name in self.ent_index():
            if n in text and not any(n in u for u in used):
                hit[name] += text.count(n); used.append(n)
        return [n for n, _ in hit.most_common(k)]

    def wiki_first(self, title, cache):
        if title in cache: return cache[title]
        if time.time() > DEADLINE: return ""
        d = get_json("https://ko.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=2&redirects=1&format=json&titles=" + urllib.parse.quote(title))
        txt = ""
        for p in ((d or {}).get("query", {}).get("pages", {}) or {}).values(): txt = (p.get("extract") or "").strip()
        cache[title] = short(re.sub(r"\s*\([^)]*\)", "", txt), 220); return cache[title]

    def extras(self):
        cache = rj(DATA / "brief/_wiki.json", {}); m = self.ents.get("map") or {}; n = 0
        for s in self.stories()[:10]:
            if s.get("method") == "ai-v1" and s.get("why3"): continue      # 사람이(클로드가) 쓴 해설은 그대로
            its = [self.items[i] for i in s["items"] if i in self.items]
            text = " ".join(filter(None, [s.get("title", "")] + [self.kt(i) for i in its]))
            names = self.ents_in(text)
            s["terms"] = [{"t": nm, "d": m[nm].get("r", "")} for nm in names if m[nm].get("r")][:5]
            bg = []
            for nm in names[:3]:
                e = m[nm]; b = e.get("d") or (self.wiki_first(e.get("w") or nm, cache) if e.get("w") or e.get("t") in ("person", "org", "place", "party") else "")
                if b and b not in bg: bg.append(b if b.startswith(nm) else f"{nm}: {b}")
            s["bg"] = bg[:3]
            cnt = Counter(self.ctry(i) for i in its)
            ang = []
            for c, _ in cnt.most_common(6):
                cand = [i for i in its if self.ctry(i) == c and self.kt(i) and i["k"] == "news"] or [i for i in its if self.ctry(i) == c and self.kt(i)]
                if cand: ang.append({"c": c, "f": self.sname(cand[0]), "t": clean_title(self.kt(cand[0]))})
            s["angles"] = ang[:5]
            first, seen_c = [], set()
            for i in sorted([i for i in its if i["k"] == "news" and i["s"] not in PAYWALL], key=lambda i: (i["_lang"] != "ko", i.get("r", 9))):
                if self.ctry(i) in seen_c: continue
                first.append(i["id"]); seen_c.add(self.ctry(i))
                if len(first) >= 3: break
            s["first"] = first; n += 1
        wj(DATA / "brief/_wiki.json", dict(list(cache.items())[-800:]))
        log(f"큰 이슈 곁들임 {n}개")

    # ── 4. 단신 ──
    def add_briefs(self):
        used = {i for s in self.E["stories"] for i in s["items"]}
        have = len(self.briefs())
        want = max(0, BRIEF_TARGET - sum(1 for s in self.briefs() if s.get("delta") == "new")) if have < MAX_BRIEFS else 0
        want = min(want, MAX_BRIEFS - have + 20)
        now = F.now_of(self.ed)
        pool = [i for i in self.items.values() if i["k"] == "news" and i["id"] not in used and i.get("first") == self.ed
                and F.age_h(i, now) <= F.COOL_H            # 처음 본 글이라도 발행된 지 24시간 넘었으면 단신으로 안 올림
                and self.kt(i) and not SKIP_RE.search(self.kt(i) + " " + i["t"]) and len(self.kt(i)) >= 12]
        pool.sort(key=lambda i: (not i.get("sm"), i.get("r", 9)))
        per, pick = Counter(), []
        for i in pool:
            c = self.ctry(i)
            if per[c] >= (5 if c == "KR" else 3): continue
            per[c] += 1; pick.append(i)
            if len(pick) >= want: break
        tr = self.translate_sm([i["id"] for i in pick if i.get("sm")])
        mx = max([int(s["id"][1:]) for s in self.E["stories"] if re.fullmatch(r"g\d+", s.get("id", ""))] or [0])
        new = []
        for i in pick:
            mx += 1; t = clean_title(self.kt(i))
            new.append({"id": f"g{mx}", "kind": "brief", "cat": cat_of([t]), "where": [self.ctry(i)], "title": t,
                        "key": tr.get(i["id"]) or "", "items": [i["id"]], "delta": "new", "method": "auto-v1",
                        "countries": [self.ctry(i)], "langs": [i["_lang"]], "grow": 0})
            if tr.get(i["id"]):
                self.brief["map"][i["id"]] = {"basis": "설명", "note": "피드 설명을 기계번역했어요", "sum": tr[i["id"]]}
        self.E["stories"] += new
        br = self.briefs()
        if len(br) > MAX_BRIEFS:   # 오래 이어진(새 글 안 붙은) 단신부터 덜어 냄
            drop = {id(s) for s in sorted(br, key=lambda s: (s.get("delta") == "new", s.get("grow") or 0))[:len(br) - MAX_BRIEFS]}
            self.E["stories"] = [s for s in self.E["stories"] if id(s) not in drop]
        log(f"단신 {len(new)}개 추가 (전체 {len(self.briefs())})")

    # ── 5. 흐름 · 나라 ──
    def themes(self):
        th = self.E.get("themes") or {}
        def flows(pred):
            out = []
            for s in self.E["stories"]:
                if pred(s) and len(out) < 6:
                    out.append({"h": re.split(r"[,，…]", s.get("title", ""))[0][:40], "issue": s["id"], "items": s["items"][:6],
                                "t": s.get("sum") or s.get("key") or ""})
            return out
        for key, title, pred in (("ai", "AI 흐름", lambda s: AIW.search(s.get("title", "") + " " + (s.get("key") or ""))),
                                 ("eco", "경제 흐름", lambda s: s.get("cat") == "eco")):
            f = flows(pred)
            if len(f) >= 2:
                th[key] = {"title": title, "lead": "이번 판 소식은 " + ", ".join(f"‘{x['h']}’" for x in f[:4]) + f" 등 {len(f)}갈래예요. 제목이 같은 낱말을 쓴 기사끼리 로봇이 모았어요.", "flows": f, "by": "robot"}
        self.E["themes"] = th
        cd = {}
        by = {}
        for it in self.items.values():
            if it["k"] == "news" and self.kt(it): by.setdefault(self.ctry(it), []).append(it)
        for c, arr in by.items():
            arr.sort(key=lambda i: (i.get("first") != self.ed, i.get("r", 9)))
            pick, srcs = [], set()
            for i in arr:
                if i["s"] in srcs or SKIP_RE.search(self.kt(i)): continue
                pick.append(i); srcs.add(i["s"])
                if len(pick) >= 2: break
            if pick: cd[c] = " ".join(f"{self.eun(self.sname(i))} ‘{clean_title(self.kt(i))}’ 소식을 실었어요." for i in pick)
        self.E["countryDigest"] = cd

    # ── 6. 이름 사전: 위키데이터에서 사람·정당·기관·장소만 ──
    WD_T = {"Q5": "person", "Q7278": "party", "Q43229": "org", "Q4830453": "org", "Q484652": "org", "Q327333": "org", "Q7210356": "org",
            "Q6256": "place", "Q515": "place", "Q1549591": "place", "Q35657": "place", "Q107390": "place", "Q10864048": "place", "Q1637706": "place",
            "Q3624078": "place", "Q5119": "place", "Q1190554": "event", "Q178561": "event", "Q198": "event"}

    def grow_ents(self, cap=120):
        if NO_NET: return
        chk = rj(DATA / "brief/_entchk.json", {}); m = self.ents.setdefault("map", {})
        known = set(m) | {a for e in m.values() for a in (e.get("a") or [])}
        cnt = Counter()
        for s in self.E["stories"]:
            for i in s["items"]:
                it = self.items.get(i)
                if it and self.kt(it):
                    for t in tokens(self.kt(it)):
                        if re.fullmatch(r"[가-힣]{2,8}", t) and t not in GENERIC and t not in known and t not in chk: cnt[t] += 1
        cand = [t for t, c in cnt.most_common(cap) if c >= 2]
        added = 0
        for b in range(0, len(cand), 40):
            if time.time() > DEADLINE: break
            part = cand[b:b + 40]
            d = get_json("https://ko.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item|disambiguation&format=json&titles=" + urllib.parse.quote("|".join(part)))
            if not d: break
            norm = {x["to"]: x["from"] for x in (d["query"].get("normalized") or [])}
            qids = {}
            for p in d["query"].get("pages", {}).values():
                t = norm.get(p.get("title"), p.get("title"))
                pp = p.get("pageprops") or {}
                if "missing" in p or "disambiguation" in pp or not pp.get("wikibase_item"): continue
                qids[pp["wikibase_item"]] = t
            for t in part: chk[t] = 0
            if not qids: continue
            w = get_json("https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims|descriptions&languages=ko|en&format=json&ids=" + "|".join(qids))
            for q, e in ((w or {}).get("entities") or {}).items():
                p31 = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in (e.get("claims", {}).get("P31") or [])]
                typ = next((self.WD_T[x] for x in p31 if x in self.WD_T), None)
                if not typ: continue
                desc = (e.get("descriptions", {}).get("ko") or {}).get("value", "")
                name = qids[q]
                m[name] = {"t": typ, "r": desc or "", "w": name, "by": "robot"}; chk[name] = 1; added += 1
        self.ents["updatedAt"] = datetime.now(KST).isoformat(timespec="seconds")
        wj(DATA / "brief/ents.json", self.ents); wj(DATA / "brief/_entchk.json", dict(list(chk.items())[-20000:]))
        log(f"이름 사전 +{added}개 (확인 {len(cand)}개)")

    def save(self):
        for k, s in enumerate(self.E["stories"]): s.pop("rep", None)
        self.E["explainMethod"] = "auto-v1 (기사 제목·피드 설명을 모아 기계번역 · AI가 쓴 해설 아님)"
        self.E["editedAt"] = datetime.now(KST).isoformat(timespec="seconds"); self.E["editedBy"] = "robot"
        wj(DATA / f"editions/{self.ed}.json", self.E); wj(DATA / f"brief/{self.ed}.json", self.brief); self.ko.save()


def main():
    ed = sys.argv[1] if len(sys.argv) > 1 else max(rj(DATA / "editions/_index.json", []), key=lambda e: e.get("crawledAt", ""))["id"]
    t0 = time.time(); X = Ed(ed); log(f"로봇 편집장: {ed}")
    for step in (X.name_candidates, X.rank, X.extras, X.add_briefs, X.themes, X.grow_ents):
        try: step()
        except Exception as e: log(f"  {step.__name__} 실패 — 건너뜀: {e!r}")
    X.save()
    log(f"끝 {round(time.time() - t0)}초")


if __name__ == "__main__":
    main()
