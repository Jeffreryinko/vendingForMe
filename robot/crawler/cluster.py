"""사건 묶기 (keyword-v1).

번역된 한국어 제목에서 핵심 단어를 뽑아, 서로 다른 출처의 글이 '드문 단어 2개 이상'을 공유하면
같은 사건 후보로 묶습니다. AI 의미 분석이 아닌 단어 기반 자동 묶음이므로 화면에 그렇게 표시합니다.

  - 아주 흔한 단어(전체 글의 15% 이상에 등장)는 사건 판별에 쓰지 않음  → "미국", "정부" 같은 단어로 엉뚱하게 합쳐지는 것 방지
  - 사건 = 글 3개 이상 + 출처 2곳 이상 (또는 서로 다른 언어권 2개 글)
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

JOSA = sorted(["으로부터", "에게서", "으로서", "으로써", "에서는", "에서도", "이라는", "라는", "까지", "부터", "에게",
               "에서", "으로", "라고", "이라", "처럼", "보다", "에는", "에도", "와의", "과의", "들이", "들은", "들의",
               "은", "는", "이", "가", "을", "를", "의", "에", "와", "과", "로", "도", "만", "들", "서"], key=len, reverse=True)

STOP = set("""
뉴스 속보 기사 오늘 내일 어제 이번 관련 대한 대해 위해 통해 따르면 가운데 이후 이전 지난 최근 현지 공식 발표 보도
영상 사진 단독 종합 업데이트 라이브 생중계 실시간 결과 사람 사람들 우리 그들 가장 모든 이상 이하 이미 계속 다시 처음
지금 당시 정도 경우 때문 그리고 하지만 또는 없는 있는 하는 했다 한다 된다 있다 없다 이다 했던 하며 해야 밝혀 밝혔다
말했다 전했다 주장 위한 대해서 중인 같은 다른 많은 새로운 올해 내년 작년 이날 오전 오후 연속 무엇 어떻게 sobre
하나 다섯 여섯 일곱 여덟 아홉 번째 첫번째 처음으로 마지막
있습니다 합니다 했습니다 됩니다 되었습니다 우리는 우리의 그들은 그는 그녀는 그것은 것은 것을 것이 이제 했다고 말했습니다 밝혔습니다
따라 대해 위한 통해 그리고 하지만 때문에 이것은 이것이 어떻게 무엇을 있는 있다고 없다고 하고 했고 사람들은 사람들이
만에 이어 문제 제기 있었 있었다 없었다 입었다 보인다 밝히고 나섰다 이어져 이어진 전망 예고 가능성
the and for with from that this are was its his her new news live update video
""".split())

# 여러 사건에 두루 나오는 말: 점수엔 보태지만 '같은 사건' 판정의 핵심 단어 2개에는 세지 않음
GENERIC = set("""
미국 중국 러시아 일본 영국 프랑스 독일 한국 북한 이란 이스라엘 우크라이나 유럽 대만 브라질 멕시코 스페인 인도네시아
트럼프 대통령 총리 정부 경찰 의회 선거 경고 비판 촉구 공개 발표 조사 결정 대응 사망 부상 공격 시사 위협 우려 논란
세계 국제 전국 지역 시장
""".split())
UNIT_RE = re.compile(r"[0-9]+(년|월|일|시|분|초|명|개|만|억|조|세|위|차|호|번|건|퍼센트|%)?")
TOKEN_RE = re.compile(r"[가-힣]{2,}|[A-Za-z][A-Za-z0-9\-]{1,}|[0-9]+[가-힣A-Za-z]+")


def tokens(text: str) -> set[str]:
    out = set()
    for t in TOKEN_RE.findall(text or ""):
        if re.fullmatch(r"[가-힣]+", t):
            for j in JOSA:
                if t.endswith(j) and len(t) - len(j) >= 2:
                    t = t[: -len(j)]
                    break
        else:
            t = t.lower()
        if len(t) >= 2 and t not in STOP and not t.isdigit() and not UNIT_RE.fullmatch(t):
            out.add(t)
    return out


def item_text(it) -> str:
    return it.get("title_ko") or ""


def build_stories(items: list[dict], day: str, min_items=3, min_sources=2, max_stories=40):
    # 한국어로 번역된 글만 사용 (원문끼리 묶으면 'por', 'die' 같은 외국어 기능어로 엉뚱하게 합쳐짐)
    pool = [it for it in items if it.get("kind") in ("news", "community") and it.get("title_ko")]
    if not pool:
        return []
    toks = {it["id"]: tokens(item_text(it)) for it in pool}
    df = Counter(t for ts in toks.values() for t in ts)
    n = len(pool)
    common = max(8, int(n * 0.15))
    idf = {t: math.log(n / c) for t, c in df.items()}
    useful = {iid: {t for t in ts if 2 <= df[t] <= common} for iid, ts in toks.items()}
    # 겹친 단어 2개의 '드문 정도' 합이 기준 이상이어야 같은 사건 (글 수가 많을수록 기준이 자동으로 올라감)
    threshold = 2 * math.log(max(n, 2) / common) if n > common else 0.5

    # 단어 → 글 역색인
    inv = defaultdict(set)
    for iid, ts in useful.items():
        for t in ts:
            inv[t].add(iid)

    by_id = {it["id"]: it for it in pool}
    clusters: list[dict] = []          # {"items": set, "profile": Counter}
    item_cluster: dict[int, int] = {}

    # 오래된 글부터 순서대로, 가장 많이 겹치는 기존 사건에 합류 (연쇄적으로 거대 묶음이 생기는 것 방지)
    for it in sorted(pool, key=lambda x: x.get("published_at") or x.get("first_seen_at") or ""):
        iid, ts = it["id"], useful[it["id"]]
        if len(ts) < 2:
            continue
        cand = set()
        for t in ts:
            for other in inv[t]:
                if other != iid and other in item_cluster:
                    cand.add(item_cluster[other])
        best, best_score = None, 0.0
        for cid in cand:
            prof = clusters[cid]["profile"]
            shared = [t for t in ts if prof[t] > 0]
            specific = [t for t in shared if t not in GENERIC]
            if len(shared) < 2 or len(specific) < 2 and not (len(specific) == 1 and len(shared) >= 3):
                continue
            score = sum(idf[t] for t in shared)
            if score > best_score:
                best, best_score = cid, score
        if best is not None and best_score >= threshold:
            clusters[best]["items"].add(iid)
            clusters[best]["profile"].update(ts)
            item_cluster[iid] = best
        else:
            clusters.append({"items": {iid}, "profile": Counter(ts)})
            item_cluster[iid] = len(clusters) - 1

    stories = []
    for c in clusters:
        its = [by_id[i] for i in c["items"]]
        sources = {i["source_id"] for i in its}
        langs = {i["lang"] for i in its}
        # 3개 이상 + 출처 2곳 이상, 또는 2개뿐이어도 서로 다른 언어권이면 사건으로 인정
        if len(sources) < min_sources or (len(its) < min_items and len(langs) < 2):
            continue
        kw = [t for t, cnt in sorted(c["profile"].items(), key=lambda kv: (-kv[1], -idf[kv[0]])) if cnt >= 2][:5]
        times = sorted(i.get("published_at") or i["first_seen_at"] for i in its)
        stories.append({
            "day": day,
            "label": " · ".join(kw[:3]),
            "keywords": kw,
            "item_ids": sorted(i["id"] for i in its),
            "langs": sorted({i["lang"] for i in its}),
            "countries": sorted({i["country"] for i in its}),
            "source_count": len(sources),
            "item_count": len(its),
            "first_at": times[0],
            "last_at": times[-1],
            "method": "keyword-v1",
        })
    stories.sort(key=lambda s: (-len(s["langs"]), -s["source_count"], -s["item_count"]))
    return stories[:max_stories]
