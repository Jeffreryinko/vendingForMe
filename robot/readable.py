"""readable.py — 이슈 한 장을 '읽을거리'로 (토큰 0, 지어내는 문장 없음).

로봇 편집장(sisa_edit.py)이 순위를 정한 뒤 큰 이슈마다 붙이는 칸:
  lines   지금까지   — 서로 다른 출처의 피드 설명 첫 문장들(기계번역), 줄마다 출처
  nums    숫자로 보기 — 제목·설명에서 '사망 17명' 같은 숫자를 출처별로 (출처마다 다르면 나란히)
  quotes  말말말     — 제목 따옴표 안의 말 + 누가(이름 사전)
  rel     이어진 이야기 — 같은 인물·장소가 나온 다른 이슈 (지금 판 + 지난 판)
그리고 대표 제목 다듬기(조각·너무 긴 제목 고르기)와 사진 규칙(첫 고유명사가 사진 기사 제목에 있어야).
나라마다 다른 제목 · 한국 언론엔? · 흐름(날마다 첫 소식)은 화면이 기사 목록으로 바로 계산함.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

MAX_READ = 20          # 읽을거리를 붙일 큰 이슈 수 (번역 시간 때문에)
LINES_MAX = 4

# ── 대표 제목 ──
FRAG = re.compile(r"^\s*(?:[은는이가을를의에와과도로만]|에서|으로|하고|라고|및|그리고|하지만|또)\s")
BADEND = re.compile(r"(?:습니다|합니다|입니다|했습니다|됩니다)[.!]?\s*$")


def title_score(t, proper, ko_orig):
    """대표 제목 점수 (높을수록 좋음). None = 탈락."""
    t = (t or "").strip()
    if not t or FRAG.match(t) or t[0] in ".,·:;)]」』”’": return None
    n = len(t); sc = 0.0
    if n < 12: return None
    sc += 2 if 18 <= n <= 60 else -3 if n > 90 else -1
    if ko_orig: sc += 3                                      # 한국어 원문 = 번역을 안 거침
    if re.search(r"\d", t): sc += 1
    toks = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", t))
    if toks & proper: sc += 2
    if BADEND.search(t): sc -= 2
    if re.search(r"[.!?。]\s+\S", t): sc -= 2                # 두 문장짜리
    if re.search(r"[A-Za-z]{4,}\s+[A-Za-z]{4,}\s+[A-Za-z]{4,}", t): sc -= 3   # 번역 안 된 외국어가 길게 남음
    return sc


def fallback_title(country_name, core_words):
    w = [x for x in core_words if len(x) >= 2][:3]
    return f"{country_name} · " + " · ".join(w) if w else ""


# ── 숫자 ──
NUM = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(만|억|조|천)?\s?(명|달러|원|유로|파운드|엔|위안|루블|%|퍼센트|km|킬로미터|건|채|가구|척|대|발|톤|배럴|도)(?![가-힣]{0,1}(?:년|월|일|시|분|세기))")
LABELS = ["사망", "숨진", "숨져", "사망자", "부상", "다친", "실종", "구조", "체포", "구금", "대피", "이재민", "피해", "확진", "감염", "탈취", "해킹", "손실", "벌금", "투자",
          "매출", "영업이익", "인상", "인하", "하락", "상승", "급등", "급락", "증가", "감소", "득표", "지지율", "관세", "기온", "난민", "시위", "인질", "포로", "미사일", "드론"]
SOFT = {"금액", "비율", "증가", "감소", "상승", "하락", "인상", "인하", "투자", "피해"}   # 혼자서는 무슨 숫자인지 모호한 꼬리표 → 두 곳 이상일 때만
LBL_NORM = {"숨진": "사망", "숨져": "사망", "사망자": "사망", "다친": "부상", "구금": "체포", "급등": "상승", "급락": "하락"}


def find_nums(text):
    out = []
    for m in NUM.finditer(text or ""):
        unit = m.group(3)
        if unit == "도" and not re.search(r"기온|섭씨|폭염|한파|최고|최저", text[max(0, m.start() - 15):m.start()]): continue
        if unit == "대" and not re.search(r"차|전투기|항공기|드론|탱크", text[max(0, m.start() - 12):m.end() + 2]): continue
        back = text[max(0, m.start() - 14):m.start()]
        lab = next((l for l in sorted(LABELS, key=len, reverse=True) if l in back), None)
        if not lab: lab_after = text[m.end():m.end() + 8]; lab = next((l for l in LABELS if l in lab_after), None)
        if not lab and unit not in ("달러", "원", "유로", "파운드", "엔", "위안", "%", "퍼센트"): continue
        v = (m.group(1) + (m.group(2) or "") + ("%" if unit == "퍼센트" else unit)).replace(" ", "")
        out.append((LBL_NORM.get(lab, lab) if lab else ("금액" if unit not in ("%", "퍼센트") else "비율"), v))
    return out


def nums_of(rows, title=""):
    """rows: [(text, src_name, country, item_id)] → [{w, vals:[{v,s,c,i}], diff}]  (한 출처는 꼬리표마다 숫자 하나 — 먼저 나온 것)"""
    g = defaultdict(list); seen = set()
    for text, sname, c, iid in rows:
        for w, v in find_nums(text):
            k = (w, sname)
            if k in seen: continue
            seen.add(k); g[w].append({"v": v, "s": sname, "c": c, "i": iid})
    out = []
    for w, vals in g.items():
        srcs = {x["s"] for x in vals}
        if len(srcs) < 2 and not (w not in SOFT and w in (title or "")): continue    # 두 곳 이상이 말한 숫자, 또는 이슈 제목에 나온 꼬리표(예: 사망)
        out.append({"w": w, "vals": vals[:5], "diff": len({x["v"] for x in vals}) > 1})
    out.sort(key=lambda x: (-len({v["s"] for v in x["vals"]}), x["w"] in ("금액", "비율")))
    return out[:3]


# ── 따옴표 ──
QUOTE = re.compile(r"[“\"‘']([^“”\"‘’']{6,80})[”\"’']")


def quotes_of(rows, person_names, n=3):
    """제목의 따옴표 안 말. 누가 했는지(이름 사전의 사람) 아는 말 먼저. 제목 통째로 따옴표인 것·조각은 뺌."""
    out, seen = [], set()
    for text, sname, c, iid in rows:
        for m in QUOTE.finditer(text or ""):
            q = m.group(1).strip()
            k = re.sub(r"\W", "", q)[:30]
            if k in seen or len(re.findall(r"[가-힣]", q)) < 5 or FRAG.match(q + " ") or re.match(r"^[을를은는이가의에도]", q): continue
            if len(q) > 0.8 * len(text.strip()): continue                 # 제목 전체를 따옴표로 감싼 것 (발언이 아님)
            seen.add(k)
            rest = text[:m.start()] + " " + text[m.end():]
            who = next((p for p in person_names if p in rest), "")
            out.append({"q": q, "who": who, "s": sname, "c": c, "i": iid})
    out.sort(key=lambda x: not x["who"])
    return out[:n]


# ── 지금까지: 출처마다 첫 문장 ──
SENT = re.compile(r"(?<=[.!?。！？])\s+|(?<=다\.)\s*")


BYLINE = re.compile(r"^\s*(?:\([^)]{0,30}=[^)]{0,20}\)\s*)?(?:[가-힣]{2,4}\s*(?:기자|특파원|통신원)\s*=?\s*)?|^\s*\[[^\]]{0,20}\]\s*")


def lead_sentence(sm, n=220):
    sm = re.sub(r"\s+", " ", sm or "").strip()
    sm = BYLINE.sub("", sm, count=1).strip()
    if len(re.findall(r"[“\"]", sm)) >= 4 and sm.count(".") <= 1: return ""     # 기사 제목 여러 개를 이어 붙인 설명(목록)
    sm = re.split(r"\s*(?:المصدر|Source:|출처:|Read more|Continue reading|Leia mais|Lesen Sie)", sm)[0]
    for s in SENT.split(sm):
        s = s.strip()
        if 30 <= len(s) <= n and re.search(r"[.!?。！？…”\"']$|다$", s) and not re.search(r"[”\"][가-힣]", s): return s   # 끝맺은 문장만 (제목을 이어 붙인 목록은 뺌)
    return ""


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


# ── 4단계: 언론사가 붙인 분류 꼬리표로 분야 가르기 ──
TAGCAT = [  # (분야, 꼬리표에 들어 있으면 그 분야로 보는 말 — 여러 언어, 소문자)
    ("spo", "sport deporte esporte futebol fútbol football soccer calcio fussball fußball basketball tennis olymp スポーツ 体育 足球 스포츠 축구 야구"),
    ("tech", "tech technolog tecnolog science ciencia ciência wissenschaft digital internet cyber ai ia 科技 テクノロジー 科学 it·과학 과학 기술 테크"),
    ("eco", "business econom wirtschaft finanz finance market mercado bolsa negocios empresas money 経済 经济 财经 金融 경제 증권 금융 산업 부동산"),
    ("cul", "culture cultura kultur entertainment arts music cinema film movie celebrity showbiz 文化 娱乐 エンタメ 문화 연예 엔터"),
    ("pol", "politic polític politik politique election elecciones government gobierno 政治 时政 정치 선거"),
    ("war", "war guerra krieg guerre conflict defen military militar 军事 군사 국방 안보"),
    ("dis", "disaster weather climate clima desastre accident 灾害 災害 재난 사고 날씨"),
    ("soc", "society sociedad sociedade gesellschaft health salud saúde crime justice education 社会 社会 사회 건강 교육 사건"),
]
_GENERIC_TAG = re.compile(r"^(world|news|top|international|internacional|mundo|welt|monde|国际|国際|세계|국제|latest|breaking|home|главное|мир)\b", re.I)


def cat_from_tags(tag_lists, min_votes=2, share=0.4):
    """여러 기사의 분류 꼬리표 → 분야 하나 (표가 모자라면 None → 낱말 사전으로)"""
    votes = Counter(); n = 0
    for tg in tag_lists:
        hit = set()
        for x in tg or []:
            x = x.lower().strip()
            if not x or _GENERIC_TAG.match(x): continue
            for c, ws in TAGCAT:
                if any(w in x for w in ws.split()): hit.add(c); break
        if hit: n += 1; votes.update(hit)
    if not votes: return None
    c, v = votes.most_common(1)[0]
    return c if v >= min_votes and v >= share * n else None


# ── 4단계: 위키백과 '요즘 화제'(Portal:Current events) 대조 ──
_LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
_SKIPLINK = re.compile(r"^(File|Image|Category|Template|Wikipedia|Portal):|^\d{4}$|^(List of|Timeline of)", re.I)


def wiki_events(wikitext):
    """하루치 위키텍스트 → [{text, names}] (맨 아래 글머리표 한 줄 = 사건 하나, 위 줄의 주제 이름도 이어받음)"""
    out, ctx = [], {}
    for line in (wikitext or "").splitlines():
        m = re.match(r"^(\*+)\s*(.*)", line)
        if not m: continue
        lv, body = len(m.group(1)), m.group(2)
        names = []
        for a, b in _LINK.findall(body):
            if _SKIPLINK.search(a): continue
            for n in {a.strip(), (b or "").strip()}:
                n = re.sub(r"\s*\([^)]*\)$", "", n)
                if len(n) >= 4 and re.search(r"[A-Z]", n): names.append(n)
        ctx[lv] = names; [ctx.pop(k) for k in list(ctx) if k > lv]
        text = re.sub(r"\s+", " ", re.sub(r"<ref.*?(</ref>|/>)|''+|\{\{[^}]*\}\}", "", _LINK.sub(lambda x: x.group(2) or x.group(1), body))).strip()
        if len(text) >= 40:                                   # 사건 문장 (주제 제목 줄은 짧음)
            allnames = list(dict.fromkeys(names + [n for k in sorted(ctx) if k < lv for n in ctx[k]]))
            if allnames: out.append({"text": text[:300], "names": allnames[:12]})
    return out


COMMON = {"united states", "donald trump", "european union", "united nations", "china", "russia", "ukraine", "israel", "india", "united kingdom",
          "president of the united states", "prime minister", "joe biden", "vladimir putin", "xi jinping"}


def wiki_match(events, titles):
    """이슈의 영어(라틴 문자) 기사 제목들에 같은 사건의 이름이 2개 이상 나오고, 그중 하나는 흔하지 않은 이름일 때 그 사건.
    점수 = 흔하지 않은 이름이 든 제목의 비율 (이슈의 중심 사건인지) — 20% 아래면 곁가지로 보고 안 맞춤"""
    freq = Counter(n.lower() for ev in events for n in set(ev["names"]))
    low = " ".join(titles).lower(); tl = [x.lower() for x in titles]; best = None
    def pat(n):                                              # 'Pete Hegseth' 은 'Hegseth' 만 나와도 맞음 (성만 쓰는 제목이 많음)
        v = [n] + ([n.split()[-1]] if len(n.split()) == 2 and n.split()[0][0].isupper() and len(n.split()[-1]) >= 5 and n.split()[-1][0].isupper() and n.lower() not in COMMON else [])
        return re.compile(r"\b(?:" + "|".join(re.escape(x.lower()) for x in v) + r")\b")
    for ev in events:
        hit = [n for n in ev["names"] if pat(n).search(low)]
        rare = [n for n in hit if n.lower() not in COMMON and freq[n.lower()] <= 3]
        if len(hit) < 2 or not rare: continue
        ps = [pat(n) for n in rare]
        share = sum(1 for x in tl if any(p.search(x) for p in ps)) / max(1, len(tl))
        if share >= 0.2 and (best is None or share > best[0]): best = (share, ev, hit)
    return best
