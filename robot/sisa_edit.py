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
import readable as R  # noqa: E402

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
        """순위 점수 = 최근 24시간에 불어난 폭 ÷ (가장 새 글 나이 + 2시간)^1.2 — 새 글이 끊기면 내려감 (robot/fresh.py)
        위키백과 '요즘 화제'에 실린 사건이면 ×1.5 (사람 편집자들이 고른 세계적 사건)"""
        return F.heat(s, self.items, self.ed, self.ctry) * (1.5 if s.get("wk") else 1.0)

    # 분야: 언론사가 붙인 꼬리표가 충분하면 그것, 아니면 낱말 사전
    def tags(self, it): return (it.get("m") or {}).get("tg") or []
    def cat_for(self, ids):
        its = [self.items[i] for i in ids if i in self.items]
        return R.cat_from_tags([self.tags(i) for i in its]) or cat_of([self.kt(i) for i in its])

    # ── 1-2. 분야 다시 보기: '사회'로 떨어진 로봇 이슈를 꼬리표로 다시 가름 ──
    def recat(self):
        n = 0
        for s in self.E.get("stories", []):
            if s.get("method") == "ai-v1" or s.get("cat") not in (None, "", "soc"): continue
            c = R.cat_from_tags([self.tags(self.items[i]) for i in s["items"] if i in self.items], 1 if s.get("kind") == "brief" else 2)
            if c and c != s.get("cat"): s["cat"] = c; n += 1
        log(f"분야 다시 가름 {n}개 (언론사 꼬리표)")

    # ── 1-3. 위키백과 '요즘 화제'와 대조 (오늘·어제, 사람 편집자가 고른 세계 사건) ──
    def wiki_news(self):
        cache = rj(DATA / "brief/_wikinews.json", {})
        now = datetime.now(timezone.utc); evs = []
        for d in (now, now - timedelta(days=1)):
            key = f"{d.year} {d.strftime('%B')} {d.day}"
            if key not in cache or d.date() == now.date():
                j = get_json("https://en.wikipedia.org/w/api.php?action=parse&format=json&formatversion=2&prop=wikitext&page="
                             + urllib.parse.quote("Portal:Current_events/" + key.replace(" ", "_")))
                wt = ((j or {}).get("parse") or {}).get("wikitext")
                if wt: cache[key] = R.wiki_events(wt)
            evs += [dict(e, d=key) for e in cache.get(key, [])]
        wj(DATA / "brief/_wikinews.json", dict(list(cache.items())[-6:]))
        best = {}                                           # 사건 하나는 가장 잘 맞는 이슈 하나에만
        for s in self.E.get("stories", []):
            s.pop("wk", None)
            if s.get("kind") == "brief" or not evs: continue
            en = [self.items[i]["t"] for i in s["items"] if i in self.items and self.items[i]["_lang"] not in ("ko", "zh", "ja", "ar", "ru", "th", "hi", "bn", "fa", "uk", "el")]
            m = R.wiki_match(evs, en) if en else None
            if m:
                sc = (m[0], F.breadth(s, self.items, self.ed, self.ctry)); k = m[1]["text"]
                if k not in best or sc > best[k][0]: best[k] = (sc, s, m)
        for _, s, m in best.values(): s["wk"] = {"t": m[1]["text"], "d": m[1]["d"], "hit": m[2][:4]}
        n = len(best)
        log(f"위키백과 요즘 화제: 사건 {len(evs)}개 · 맞춘 이슈 {n}개")

    # ── 6. 하루 정리판: 하루에 한 번(아침 6시 이후 첫 판) 지난 24시간 큰 이슈 10 + 단신 20 을 고정 ──
    def daily(self):
        F.give_sid(self.E["stories"], self.ed)
        today = self.ed[:10]; hour = int(self.ed[-2:]) if self.ed[-2:].isdigit() else 0
        d = self.E.get("daily") or {}
        if d.get("date") == today or hour < 6:
            log(f"하루 정리판: 그대로 ({d.get('date') or '없음'})"); return
        ms = [s for s in self.stories() if len(s.get("items") or []) >= 2]
        ms.sort(key=lambda s: (F.breadth(s, self.items, self.ed, self.ctry) * (1.5 if s.get("wk") else 1)), reverse=True)
        pick, per = [], Counter()
        for s in ms:
            if per[s.get("cat")] >= 3: continue
            per[s.get("cat")] += 1; pick.append(s)
            if len(pick) >= 10: break
        br = [s for s in self.briefs() if s.get("key") and s.get("delta") == "new"] or [s for s in self.briefs() if s.get("key")]
        bp, bc = [], Counter()
        for s in br:
            c = (s.get("countries") or [""])[0]
            if bc[c] >= (6 if c == "KR" else 3): continue
            bc[c] += 1; bp.append(s)
            if len(bp) >= 20: break
        snap = lambda s: {"sid": s.get("sid"), "id": s.get("id"), "title": s.get("title", ""), "key": short(s.get("key") or s.get("sum") or "", 200),
                          "cat": s.get("cat", ""), "c": (s.get("countries") or [])[:5], "n": len(s.get("items") or []), **({"wk": 1} if s.get("wk") else {})}
        self.E["daily"] = {"date": today, "ed": self.ed, "label": self.E.get("label", self.ed), "at": self.E.get("crawledAt", ""),
                           "stories": [snap(s) for s in pick], "briefs": [snap(s) for s in bp]}
        log(f"하루 정리판 새로 만듦: {today} · 큰 이슈 {len(pick)} · 단신 {len(bp)}")

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
            s["cat"] = self.cat_for(s["items"])
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
                if s.get("wk") and not h.get("wk"): h["wk"] = s["wk"]          # 합쳐진 쪽의 위키백과 표시도 넘겨받음
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


    # ── 3-2. 읽을거리: 여러 출처 요약 · 숫자 · 말말말 · 이어진 이야기 · 대표 제목 · 사진 규칙 (robot/readable.py) ──
    def readables(self):
        proper = self.proper(); m = self.ents.get("map") or {}
        persons = sorted([n for n, e in m.items() if e.get("t") == "person" and len(n) >= 2], key=len, reverse=True)
        plist = sorted(proper, key=len, reverse=True); nc = {}
        def names_of(text):                                   # 글에 든 고유명사 (조사가 붙어도 찾게 '들어 있나'로), 나온 순서대로
            text = text or ""
            if text not in nc:
                hit = []
                for n in plist:
                    p = text.find(n)
                    if p >= 0 and not any(n in h for _, h in hit): hit.append((p, n))
                nc[text] = [n for _, n in sorted(hit)]
            return nc[text]
        CN = {"KR": "한국", "US": "미국", "CN": "중국", "JP": "일본", "GB": "영국", "FR": "프랑스", "DE": "독일", "RU": "러시아", "IN": "인도", "BR": "브라질", "TR": "튀르키예", "UA": "우크라이나", "IL": "이스라엘", "IR": "이란"}
        big = [s for s in self.stories() if len(s.get("items") or []) >= 2][:R.MAX_READ]
        n_title = n_ph = 0; need = []
        for s in big:
            its = [self.items[i] for i in s["items"] if i in self.items]
            # 대표 제목: 새 이슈이거나 지금 제목이 조각·너무 길면 다시 고름 (사람이 쓴 해설 ai-v1 은 그대로)
            if s.get("method") != "ai-v1":
                cur = R.title_score(s.get("title"), proper, False)
                if s.get("born") == self.ed or cur is None or cur < 0:
                    cand = []
                    for it in its:
                        tt = clean_title(self.kt(it))
                        sc = R.title_score(tt, proper, it["_lang"] == "ko")
                        if sc is not None: cand.append((sc + (1 if it["k"] == "news" else 0) + (1 if it.get("id") == s.get("rep_id") else 0), tt))
                    if cand:
                        best = max(cand)[1]
                        if best != s.get("title"): s["title"] = best; n_title += 1
                    elif cur is None:
                        c = Counter(self.ctry(i) for i in its).most_common(1)
                        fb = R.fallback_title(CN.get(c[0][0], c[0][0]) if c else "", [w for w in (s.get("core") or []) if w in proper] + list(s.get("core") or []))
                        if fb: s["title"] = fb; n_title += 1
            # 사진: 제목의 첫 고유명사가 사진 기사 제목에 없으면 사진 대신 지도
            nm = names_of(s.get("title"))
            ph = s.get("ph"); pit = self.items.get((ph or {}).get("i"))
            if ph and nm and pit and nm[0] not in (self.kt(pit) + " " + pit.get("t", "")):
                s.pop("ph", None); n_ph += 1
            # 지금까지: 출처마다 피드 설명 첫 문장 1개 (한국어 원문 먼저 → 무료 뉴스 → 순위)
            seen_s, picks = set(), []
            for it in sorted([i for i in its if i.get("sm") and i["k"] == "news"], key=lambda i: (i["_lang"] != "ko", i["s"] in PAYWALL, i.get("r", 9))):
                if it["s"] in seen_s: continue
                ld = R.lead_sentence(it["sm"])
                if not ld: continue
                seen_s.add(it["s"]); picks.append((it, ld))
                if len(picks) >= R.LINES_MAX + 2: break
            need.append((s, picks))
        # 번역 한 번에 (이미 번역한 문장은 기억에서)
        flat = [(ld, it["_lang"]) for _, ps in need for it, ld in ps]
        tr = self.ko.many(flat, deadline=DEADLINE) if flat else []
        k = 0; n_lines = n_nums = n_q = 0
        for s, ps in need:
            core = set(s.get("core") or []) | set(re.findall(r"[가-힣A-Za-z0-9]{2,}", s.get("title") or ""))
            lines, toks = [], []
            for it, ld in ps:
                ko = tr[k] if k < len(tr) else None; k += 1
                if not ko: continue
                tk = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", ko))
                if not (tk & core) and len(ps) > 2: continue                    # 이 사건과 낱말이 하나도 안 겹치는 문장은 뺌
                if any(R.jacc(tk, o) > 0.45 for o in toks): continue             # 비슷한 문장은 하나만
                toks.append(tk)
                lines.append({"t": short(ko, 200), "s": it["s"], "c": self.ctry(it), "i": it["id"], "mt": it["_lang"] != "ko"})
                if len(lines) >= R.LINES_MAX: break
            if len(lines) >= 2: s["lines"] = lines; n_lines += 1
            else: s.pop("lines", None)
            its = [self.items[i] for i in s["items"] if i in self.items]
            rows = [(clean_title(self.kt(i)), self.sname(i), self.ctry(i), i["id"]) for i in its if self.kt(i)]
            rows += [(x["t"], self.sname(self.items[x["i"]]), x["c"], x["i"]) for x in lines]
            nums = R.nums_of(rows, s.get("title") or "")
            if nums: s["nums"] = nums; n_nums += 1
            else: s.pop("nums", None)
            qs = R.quotes_of(rows[:len(its)], persons)
            if qs: s["quotes"] = qs; n_q += 1
            else: s.pop("quotes", None)
        # 이어진 이야기: 제목의 고유명사가 겹치는 다른 이슈 (지금 판 먼저, 그다음 지난 7일 판)
        cur_sids = {s.get("sid") for s in self.E["stories"] if s.get("sid")}
        cur_titles = {s.get("title") for s in self.E["stories"]}
        past = []
        idx = sorted([e for e in rj(DATA / "editions/_index.json", []) if e.get("id") != self.ed], key=lambda e: e.get("crawledAt", ""))[-56:]
        for e in reversed(idx):
            d = rj(DATA / f"editions/{e['id']}.json", {})
            for x in d.get("stories", []):
                if x.get("kind") == "brief" or not x.get("title"): continue
                if x.get("sid") in cur_sids or x.get("title") in cur_titles: continue
                if any((x.get("sid") and x.get("sid") == p["sid"]) or x["title"] == p["t"] for p in past): continue
                past.append({"sid": x.get("sid") or "", "t": x["title"][:80], "ed": e["id"], "label": e.get("label", e["id"])})
        n_rel = 0
        for s in big:
            nm = set(names_of(s.get("title"))) | (set(s.get("core") or []) & proper)
            if not nm: continue
            rel = [{"sid": o.get("sid") or o["id"], "id": o["id"], "t": o["title"][:80], "cur": True} for o in big
                   if o is not s and set(names_of(o.get("title"))) & nm][:2]
            rel += [dict(p, cur=False) for p in past if set(names_of(p["t"])) & nm][:3 - len(rel)]
            if rel: s["rel"] = rel; n_rel += 1
            else: s.pop("rel", None)
        log(f"읽을거리: 이슈 {len(big)}개 · 여러 출처 요약 {n_lines} · 숫자 {n_nums} · 말말말 {n_q} · 이어진 이야기 {n_rel} · 제목 다시 고름 {n_title} · 엉뚱한 사진 뺌 {n_ph}")

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
            new.append({"id": f"g{mx}", "kind": "brief", "cat": R.cat_from_tags([self.tags(i)], 1, 0) or cat_of([t]), "where": [self.ctry(i)], "title": t,
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
        F.give_sid(self.E["stories"], self.ed)          # 새로 생긴 이슈·단신에도 고정 번호
        self.E["explainMethod"] = "auto-v1 (기사 제목·피드 설명을 모아 기계번역 · AI가 쓴 해설 아님)"
        self.E["editedAt"] = datetime.now(KST).isoformat(timespec="seconds"); self.E["editedBy"] = "robot"
        wj(DATA / f"editions/{self.ed}.json", self.E); wj(DATA / f"brief/{self.ed}.json", self.brief); self.ko.save()


def main():
    ed = sys.argv[1] if len(sys.argv) > 1 else max(rj(DATA / "editions/_index.json", []), key=lambda e: e.get("crawledAt", ""))["id"]
    t0 = time.time(); X = Ed(ed); log(f"로봇 편집장: {ed}")
    for step in (X.name_candidates, X.recat, X.wiki_news, X.rank, X.extras, X.readables, X.add_briefs, X.daily, X.themes, X.grow_ents):
        try: step()
        except Exception as e: log(f"  {step.__name__} 실패 — 건너뜀: {e!r}")
    X.save()
    log(f"끝 {round(time.time() - t0)}초")


if __name__ == "__main__":
    main()
