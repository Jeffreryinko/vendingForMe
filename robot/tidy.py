"""tidy.py — 수집한 글을 '정형'하는 규칙 모음 (토큰 0).

  tidy_title   번역 제목의 머리말([단독]·영상 |·긴급 |)과 꼬리표(| crime | News | …) 떼기
  is_junk      뉴스가 아닌 글(운세·지면 안내·메가스레드·편성표·낱말 하나짜리) 가려내기
  dedupe       한 이슈 안에서 같은 주소·같은 제목의 글은 하나만
  Sig          이슈의 '지문': 제목 속 이름(별칭은 대표 이름으로) · 원문 제목에 되풀이되는 드문 로마자 이름 · 뜻 낱말(조사 뗌)
  same_event   두 이슈가 같은 사건인가 (합침)      — 이름 + 다른 낱말이 함께 겹칠 때만
  same_topic   두 이슈가 같은 주제인가 (묶음 카드) — 같은 이름이 제목에 있을 때
"""
from __future__ import annotations

import re
from collections import Counter

# ── 제목 다듬기 ──
_LABEL = (r"영상|동영상|사진|포토|화보|긴급|속보|실시간|단독|종합|라이브|인터뷰|오피니언|사설|칼럼|분석|해설|팩트체크|뉴스 기사|기사|"
          r"video|vídeo|vidéo|watch|breaking|live|liveblog|en direct|en vivo|ao vivo|opinion|analysis|exclusive|update|urgent")
_PRE = re.compile(r"^\s*(?:" + _LABEL + r")\s*[|｜│:：]\s*", re.I)
_BRK = re.compile(r"^\s*[\[【(（<《][^\]】)）>》]{1,12}[\]】)）>》]\s*")
_TAGTAIL = re.compile(r"(?:\s*[|｜│]\s*[^|｜│]{1,24}){2,}\s*$")           # ' | Busfire | crime | News'
_SRCTAIL = re.compile(r"\s+[-–—|｜│ㅣ]\s+[^-–—|｜│ㅣ]{2,25}$")            # ' - 연합뉴스'
_PAGETAIL = re.compile(r"\s*[-–|]\s*\d+\s*(?:페이지|면|page)\s*$", re.I)


def tidy_title(t: str, src_tail: bool = False) -> str:
    """번역 제목 다듬기. src_tail=True 면 ' - 매체명' 꼬리도 뗌(이슈 대표 제목용 — 낱개 글 제목에선 본문 일부일 수 있어 안 뗌)."""
    t = re.sub(r"\s+", " ", t or "").strip()
    for _ in range(2):
        t = _BRK.sub("", t); t = _PRE.sub("", t)
    t = _PAGETAIL.sub("", t)
    if _TAGTAIL.search(t) and len(_TAGTAIL.sub("", t)) >= 12: t = _TAGTAIL.sub("", t)
    if "│" in t or "｜" in t:                                          # 제목 여러 개를 이어 붙인 것 → 첫 제목만
        first = re.split(r"\s*[│｜]\s*", t)[0]
        if len(first) >= 12: t = first
    if src_tail and len(_SRCTAIL.sub("", t)) >= 12: t = _SRCTAIL.sub("", t)
    t = t.strip(" -–|·")
    for a, b in (("“", "”"), ('"', '"'), ("‘", "’"), ("'", "'")):
        if len(t) > 2 and t[0] == a and t[-1] == b and t.count(a) == (1 if a != b else 2): t = t[1:-1]
    return t.strip()


# ── 뉴스가 아닌 글 ──
_JUNK = re.compile(
    r"운세|별자리|띠별|오늘의 날씨|주간 날씨|편성표|시간표|로또|당첨 ?번호|십자말|낱말 ?퀴즈|퀴즈:|오늘의 (?:사진|만평|한자|영어)|만평|부고|인사\]|"
    r"megathread|메가스레드|daily (?:discussion|thread)|weekly (?:discussion|thread)|자유 ?토론 ?스레드|일일 ?토론|"
    r"horoscope|horóscopo|horoskop|wordle|sudoku|crossword|newsletter|뉴스레터|팟캐스트 ?\d|podcast:|e-?paper|지면 ?보기|"
    r"sponsored|advertorial|광고\]|\[광고|\bAD\b|쿠폰|할인 ?코드|특가|세일 ?정보|best deals|구매할 만한", re.I)
_PAGE = re.compile(r"\d+\s*(?:페이지|면)\s*$|^\s*\d{4}년 \d{1,2}월 \d{1,2}일[^가-힣A-Za-z]*$|,\s*\d{4}년 \d{1,2}월 \d{1,2}일,?\s*[월화수목금토일]요일\s*(?:[|–-].*)?$")


def is_junk(ko: str, orig: str = "", kind: str = "news") -> bool:
    """이슈·단신의 근거로 쓰지 않을 글 (운세·지면 안내·토론 스레드·광고·방송 회차 안내 …)"""
    t = (ko or "") + " ‖ " + (orig or "")
    if _JUNK.search(t) or _PAGE.search(ko or ""): return True
    if kind == "news" and ko and len(re.sub(r"\s", "", ko)) < 8: return True      # 낱말 하나짜리 제목
    if ko and ko.count("│") + ko.count("｜") >= 2: return True                    # 제목 목록
    return False


# ── 중복 ──
def _nurl(u): return re.sub(r"[?#].*$", "", (u or "").strip()).rstrip("/").lower()
def _ntitle(t): return re.sub(r"[\W_]+", "", (t or "").lower())[:60]


def dedupe(ids, items, title_of):
    """한 이슈의 글 목록에서 같은 주소, 또는 같은 출처의 같은 제목은 처음 것만 남김. (다른 출처의 같은 제목 = 통신사 기사 전재 → 둘 다 남겨 '몇 곳이 실었나'를 셈)"""
    seen_u, seen_t, out = set(), set(), []
    for i in ids:
        it = items.get(i)
        if not it: out.append(i); continue
        u = _nurl(it.get("u")); k = (it.get("s"), _ntitle(title_of(it) or it.get("t")))
        if (u and u in seen_u) or (k[1] and k in seen_t): continue
        if u: seen_u.add(u)
        if k[1]: seen_t.add(k)
        out.append(i)
    return out


# ── 이슈 지문 ──
_JOSA = re.compile(r"(?:에서는|에서도|으로는|에게는|에서|으로|에게|까지|부터|보다|이라고|라고|이며|이고|과의|와의|에는|에도|은|는|이|가|을|를|의|에|와|과|도|로|만)$")
_LAT = re.compile(r"\b[A-Z][A-Za-z'’\-]{3,}\b")
_LAT_STOP = set("""this that these those what when where which while with from after before over under about into than then they their there here have has
had will would could should says said say new news live update video watch more most first last year years week day days amid among against
president minister government police court report reports people world state states city country national international breaking opinion analysis
monday tuesday wednesday thursday friday saturday sunday january february march april june july august september october november december
los las del der die das und les des aux une pour dans avec sur por para como que est the and for""".split())


def stem(t: str) -> str:
    """한국어 낱말에서 조사 떼기 ('엔비디아에' → '엔비디아'). 3글자 이상일 때만 (짧은 낱말은 뜻이 바뀜)."""
    if len(t) >= 3 and re.search(r"[가-힣]$", t):
        s = _JOSA.sub("", t)
        if len(s) >= 2: return s
    return t


class Sig:
    """이슈들의 지문을 만들고 비교함. 판 하나에 한 번 만들어 씀."""

    def __init__(self, items, ents_map, tokens, GENERIC, title_of, weak=()):
        self.items, self.tokens, self.GENERIC, self.title_of, self.weak = items, tokens, GENERIC, title_of, set(weak)
        # 이름 → 대표 이름 (별칭 포함), 긴 이름부터 찾음. 사람·기관·정당·지역·사건만 (용어는 주제 이름으로 안 씀)
        self.canon = {}; self.typ = {}
        for n, e in (ents_map or {}).items():
            if e.get("t") not in ("person", "org", "party", "place", "event"): continue
            self.typ[n] = e.get("t")
            for k in [n] + [a for a in (e.get("a") or []) if a]:
                if len(k) >= 2: self.canon[k] = n
        self.keys = sorted(self.canon, key=len, reverse=True)
        # 로마자 이름의 흔한 정도: 이 판 글 가운데 몇 %의 원문 제목에 나오나
        df = Counter(); n = 0
        for it in items.values():
            if it.get("_lang") in ("ko", "zh", "ja", "ar", "ru", "th", "hi", "bn", "fa", "uk", "el"): continue
            n += 1
            for w in {x.lower() for x in _LAT.findall(it.get("t") or "")}: df[w] += 1
        self.lat_df, self.lat_n = df, max(1, n)
        self._c = {}

    def names_in(self, text):
        """글에 든 이름(대표 이름으로), 나온 순서대로. 낱말 첫머리에서만, 두 글자 한글 이름은 뒤에 조사·띄어쓰기일 때만."""
        text = text or ""; hit = []; taken = []
        for k in self.keys:
            i = text.find(k)
            while i >= 0:
                prev = text[i - 1] if i else " "; nxt = text[i + len(k):i + len(k) + 1] or " "
                ok = not re.match(r"[가-힣A-Za-z]", prev) and not (re.search(r"[A-Za-z]$", k) and re.match(r"[A-Za-z]", nxt))
                if ok and len(k) <= 2 and re.fullmatch(r"[가-힣]+", k) and re.match(r"[가-힣]", nxt) and nxt not in "은는이가을를의에와과도로만": ok = False
                if ok and not any(a <= i < b for a, b in taken):
                    taken.append((i, i + len(k))); hit.append((i, self.canon[k])); break
                i = text.find(k, i + 1)
        out = []
        for _, n in sorted(hit):
            if n not in out: out.append(n)
        return out

    def of(self, s):
        k = id(s)
        if k in self._c: return self._c[k]
        title = s.get("title") or ""
        its = [self.items[i] for i in s.get("items", []) if i in self.items]
        names = self.names_in(title)
        nset = set(names)
        toks = {stem(t) for t in self.tokens(title) if t not in self.GENERIC}
        toks = {t for t in toks if t not in self.GENERIC and t not in self.weak and not re.search(r"\d", t)
                and not any(t == n or t in n.split() or n in t for n in nset)}
        # 원문(로마자) 제목에 되풀이되는 드문 이름: 번역이 이름을 다르게 옮겨도('헤그세스'/'헤게스') 같은 사건을 알아봄
        lat = Counter()
        for it in its:
            if it.get("_lang") in ("ko", "zh", "ja", "ar", "ru", "th", "hi", "bn", "fa", "uk", "el"): continue
            words = _LAT.findall(it.get("t") or "")
            for w in {x.lower() for x in words[1:] + ([words[0]] if words and len(words[0]) >= 6 else [])}:
                if w not in _LAT_STOP: lat[w] += 1
        need = 2 if len(its) >= 3 else 1
        rare = {w for w, c in lat.items() if c >= need and self.lat_df[w] / self.lat_n <= 0.012}
        sig = {"names": names, "nset": nset, "toks": toks, "lat": rare}
        self._c[k] = sig
        return sig

    def drop(self, s): self._c.pop(id(s), None)

    def same_event(self, a, b):
        """같은 사건: 이름만 같아선 안 되고(엔비디아 수사 ≠ 엔비디아 새 칩) 다른 낱말·드문 로마자 이름이 함께 겹쳐야 함."""
        A, B = self.of(a), self.of(b)
        n = len(A["nset"] & B["nset"]); t = len(A["toks"] & B["toks"]); l = len(A["lat"] & B["lat"])
        return (n >= 1 and t >= 2) or (n >= 2 and t >= 1) or (l >= 2 and n + t >= 1) or l >= 3 or t >= 4

    def topic_names(self, s):
        """묶음 카드의 열쇠가 될 이름: 제목에 나온 이름 (사람·기관·정당 먼저, 그다음 지역·사건)"""
        ns = self.of(s)["names"]
        return sorted(ns, key=lambda n: (self.typ.get(n) in ("place", "event"), ns.index(n)))
