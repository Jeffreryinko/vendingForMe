"""baedat_run.py — 배댓 월간판 로봇 (매월 1일, 토큰 0). 클로드 '배댓 월간판 갱신' 예약 작업 대신.

규칙(예전 판과 같음): 그 달 업로드 · 조회수 순 · 한국 채널 · 영상 50개 · 배댓은 관련성 순 상위 10개(채널 주인 댓글 제외).
분류(유형·감정·드립 기법)는 낱말 규칙으로 — 사람이 읽고 붙인 예전 판보다 거칠 수 있어서 by:"robot" 으로 표시합니다.
리포트도 숫자로 만든 문장만 씁니다(지어내는 해석 없음).

  YOUTUBE_API_KEY=… python robot/baedat_run.py            # 지난달
  YOUTUBE_API_KEY=… python robot/baedat_run.py 2026-11    # 그 달 (이미 있으면 건너뜀, --force 면 다시)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/baedat"
KST = timezone(timedelta(hours=9))
KEY = os.environ.get("YOUTUBE_API_KEY", "")
API = "https://www.googleapis.com/youtube/v3/"
units = 0

CAT = {"1": "영화·애니", "2": "자동차", "10": "음악", "15": "동물", "17": "스포츠", "19": "여행", "20": "게임", "22": "인물·블로그", "23": "코미디",
       "24": "엔터테인먼트", "25": "뉴스·정치", "26": "노하우·스타일", "27": "교육", "28": "과학·기술", "29": "비영리·사회운동"}

# ── 낱말 규칙 (앞에서부터 먼저 맞는 것) ──
TS = re.compile(r"\b\d{1,2}:\d{2}\b")
TYPES = [
    ("타임스탬프", lambda t: bool(TS.search(t))),
    ("이벤트 참여", lambda t: re.search(r"응모|이벤트|참여합니다|당첨|추첨|giveaway", t, re.I)),
    ("질문", lambda t: t.rstrip().endswith("?") or re.search(r"(인가요|나요|까요|던가요|뭐예요|뭐에요|누구|어디서|언제)\??$", t.strip())),
    ("응원·감사", lambda t: re.search(r"응원|화이팅|파이팅|감사합니다|고마워|고맙|사랑해|축하|수고|덕분|힘내|love you|thank|proud|congrat|streaming|🔥|❤|💜|🩷", t, re.I)),
    ("비판", lambda t: re.search(r"실망|별로|왜 이렇게|아쉽|최악|그만|싫다|짜증|불편|광고 너무|억지|논란|문제", t)),
    ("반전·지적", lambda t: re.search(r"근데|사실은|사실 |오히려|정작|알고 보니|아닌데|틀렸|아니라", t)),
    ("정보 보충", lambda t: re.search(r"참고로|원래|출처|\d{4}년|정보|알려|설명|원곡|원작|번역", t)),
    ("밈 인용", lambda t: re.search(r"ㄹㅇ|실화냐|국룰|킹받|폼 미쳤|레전드|도랏|가보자고|ㅇㅈ|어쩔|무야호|추억", t)),
    ("드립", lambda t: re.search(r"ㅋㅋ|ㅎㅎ|ㅋ{2,}|웃기|빵 터|미쳤|드립|lol|lmao|😂|🤣", t, re.I)),
]
DEVICE = [("과장", r"\d{2,}번|평생|세상에서|역대|우주|100%|만 번|무한"), ("상황극", r"^\s*[가-힣A-Za-z]+\s*:|\b나:|엄마:|아빠:"),
          ("말장난", r"말장난|아재|ㅋㅋ.*ㅋㅋ.*ㅋㅋ"), ("자기비하", r"나만|내 인생|저는 왜|나는 왜|솔로|모쏠"), ("반전", r"근데|알고 보니|사실은"),
          ("비유", r"같다|같아|처럼|마냥"), ("패러디", r"패러디|따라|흉내")]
EMO = [("웃음", r"ㅋ|ㅎㅎ|웃기|빵|😂|🤣|lol|lmao|haha"), ("감동", r"눈물|울컥|감동|소름|ㅠ|😭|🥹|뭉클|최고|명곡|beautiful|amazing|❤"),
       ("분노", r"화나|짜증|열받|어이없|분노|😡|최악"), ("냉소", r"ㅉ|뭐하냐|그럼 그렇지|역시나|하긴"), ("공감", r"나도|저도|공감|내 얘기|맞아|ㄹㅇ|인정|same|me too")]
STOP = set("진짜 너무 정말 그냥 이거 이건 저는 나는 우리 근데 그리고 하는 있는 없는 같은 영상 이렇게 the and you this that for with are was".split())


def tag(t):
    ty = next((n for n, f in TYPES if f(t)), "공감")
    em = next((n for n, p in EMO if re.search(p, t, re.I)), "중립")
    dv = next((n for n, p in DEVICE if re.search(p, t)), None) if ty == "드립" else None
    kw = [w for w in re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", t) if w.lower() not in STOP][:4]
    o = {"type": ty, "emotion": em, "kw": kw, "by": "robot"}
    if dv: o["device"] = dv
    return o


def yt(path, **q):
    global units
    q["key"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(q)
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=20) as r:
                units += 100 if path == "search" else 1
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (403, 404) and ("commentsDisabled" in body or "disabled comments" in body): return {"items": [], "_off": True}
            if "quota" in body.lower(): raise SystemExit("유튜브 하루 한도(quota)가 다 찼어요 — 내일 다시")
            if i == 2: print("  실패", path, e.code, body[:120]); return {}
        except Exception as e:
            if i == 2: print("  실패", path, e); return {}
        time.sleep(2 + i * 3)


def iso_dur(s):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    return 0 if not m else sum(int(x or 0) * k for x, k in zip(m.groups(), (86400, 3600, 60, 1)))


def main():
    if not KEY: raise SystemExit("YOUTUBE_API_KEY 가 없어요 (저장소 Settings → Secrets → Actions)")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    now = datetime.now(KST)
    month = args[0] if args else (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    if (OUT / f"{month}.json").exists() and "--force" not in sys.argv:
        print(f"{month} 판은 이미 있어요 — 건너뜀"); return
    y, m = map(int, month.split("-"))
    start = datetime(y, m, 1, tzinfo=KST); end = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=KST)
    z = lambda d: d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 1. 후보: 그 달 업로드, 조회수 순
    ids, tok = [], None
    for _ in range(6):
        r = yt("search", part="id", type="video", order="viewCount", regionCode="KR", relevanceLanguage="ko", maxResults=50,
               publishedAfter=z(start), publishedBefore=z(end), **({"pageToken": tok} if tok else {}))
        ids += [x["id"]["videoId"] for x in r.get("items", []) if x.get("id", {}).get("videoId")]
        tok = r.get("nextPageToken")
        if not tok: break
    ids = list(dict.fromkeys(ids)); print(f"후보 {len(ids)}개")
    vids = {}
    for b in range(0, len(ids), 50):
        r = yt("videos", part="snippet,statistics,contentDetails,player", id=",".join(ids[b:b + 50]), maxHeight=720)
        for v in r.get("items", []): vids[v["id"]] = v
    chs = {}
    cids = list({v["snippet"]["channelId"] for v in vids.values()})
    for b in range(0, len(cids), 50):
        r = yt("channels", part="snippet,statistics", id=",".join(cids[b:b + 50]))
        for c in r.get("items", []): chs[c["id"]] = c
    skipped = Counter(); out = []
    order = sorted(vids.values(), key=lambda v: -int(v["statistics"].get("viewCount", 0)))
    for v in order:
        if len(out) >= 50: break
        sn = v["snippet"]; ch = chs.get(sn["channelId"], {})
        country = (ch.get("snippet") or {}).get("country")
        if country != "KR" and not (country is None and re.search(r"[가-힣]", sn.get("title", ""))):
            skipped["not_kr"] += 1; continue
        if "commentCount" not in v["statistics"]: skipped["comments_off"] += 1; continue
        r = yt("commentThreads", part="snippet", videoId=v["id"], order="relevance", maxResults=20, textFormat="plainText")
        if r.get("_off"): skipped["comments_off"] += 1; continue
        cs, own = [], 0
        for it in r.get("items", []):
            c = it["snippet"]["topLevelComment"]["snippet"]
            if (c.get("authorChannelId") or {}).get("value") == sn["channelId"]: own += 1; continue
            cs.append((it, c))
        if not cs: skipped["no_comments"] += 1; continue
        views = int(v["statistics"].get("viewCount", 0)); d = iso_dur(v["contentDetails"].get("duration"))
        pl = v.get("player") or {}
        try: ar = round(int(pl["embedWidth"]) / int(pl["embedHeight"]), 3)
        except Exception: ar = 1.778
        best = []
        for k, (it, c) in enumerate(cs[:10]):
            t = c.get("textOriginal") or c.get("textDisplay") or ""
            likes = int(c.get("likeCount", 0))
            best.append({"id": it["id"], "rank": k + 1, "text": t, "likes": likes, "replies": int(it["snippet"].get("totalReplyCount", 0)),
                         "at": c.get("publishedAt"), "len": len(t), "ts": bool(TS.search(t)),
                         "emoji": len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", t)), "lines": t.count("\n") + 1,
                         "power": round(likes / views, 4) if views else None, "tags": tag(t)})
        out.append({"id": v["id"], "rank": len(out) + 1, "title": sn.get("title", ""), "channel": sn.get("channelTitle", ""), "channelId": sn["channelId"],
                    "category": CAT.get(sn.get("categoryId"), "기타"), "publishedAt": sn.get("publishedAt"), "dur": d, "short": d <= 60 or ar < 1,
                    "views": views, "likes": int(v["statistics"].get("likeCount", 0)), "comments": int(v["statistics"].get("commentCount", 0)),
                    "subs": int((ch.get("statistics") or {}).get("subscriberCount", 0)), "ownerComments": own, "thumb": True,
                    "best": best, "desc": "", "ar": ar})
    allc = [c for v in out for c in v["best"]]
    types = Counter(c["tags"]["type"] for c in allc).most_common(); emos = Counter(c["tags"]["emotion"] for c in allc).most_common()
    kws = Counter(w for c in allc for w in c["tags"]["kw"]).most_common(30)
    n = max(len(allc), 1); pct = lambda x: round(x * 100 / n)
    pm = (start - timedelta(days=1)).strftime("%Y-%m")
    prev = json.loads((OUT / f"{pm}.json").read_text(encoding="utf-8")) if (OUT / f"{pm}.json").exists() else None
    rep = [f"{m}월판은 영상 {len(out)}개 · 배댓 {len(allc)}개예요. 가장 많은 유형은 ‘{types[0][0]}’({pct(types[0][1])}%), 그다음 ‘{types[1][0]}’({pct(types[1][1])}%)이에요."
           if len(types) > 1 else f"{m}월판은 영상 {len(out)}개 · 배댓 {len(allc)}개예요."]
    rep.append(f"감정은 ‘{emos[0][0]}’이 {pct(emos[0][1])}%로 가장 많아요." + (f" 지난달 1위 유형은 ‘{prev['summary']['types'][0][0]}’였어요." if prev and prev.get("summary", {}).get("types") else ""))
    top = sorted([c for c in allc if c["power"]], key=lambda c: -c["power"])[:1]
    if top:
        tv = next(v for v in out if top[0] in v["best"])
        rep.append(f"배댓 파워(좋아요 ÷ 조회수)가 가장 높은 댓글은 「{tv['title'][:40]}」에 달렸어요. 유형·감정은 낱말 규칙으로 로봇이 붙인 것이라 거칠 수 있어요.")
    doc = {"month": month, "collectedAt": now.isoformat(timespec="seconds"), "region": "KR",
           "rule": "그 달 업로드 · 조회수 순 · 한국 채널 · 배댓은 관련성 순 상위 10개(채널 주인 댓글 제외)", "skipped": dict(skipped), "units": units,
           "classified": 1.0, "by": "robot", "videos": out, "summary": {"types": types, "emotions": emos, "keywords": kws}, "report": "\n\n".join(rep)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{month}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    ix = json.loads((OUT / "index.json").read_text(encoding="utf-8")) if (OUT / "index.json").exists() else {"months": []}
    ix["months"] = sorted(set(ix.get("months", [])) | {month}); ix["updatedAt"] = now.isoformat(timespec="seconds")
    (OUT / "index.json").write_text(json.dumps(ix, ensure_ascii=False), encoding="utf-8")
    meta = json.loads((OUT / "_meta.json").read_text(encoding="utf-8")) if (OUT / "_meta.json").exists() else {}
    meta.update({"updatedAt": now.isoformat(timespec="seconds"), "latest": max(ix["months"]), "comments": len(allc)})
    meta["months"] = sorted(set(meta.get("months", [])) | {month})
    (OUT / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"{month}: 영상 {len(out)} · 배댓 {len(allc)} · 1위 유형 {types[0][0] if types else '-'} · 유튜브 {units}단위 · 뺀 것 {dict(skipped)}")


if __name__ == "__main__":
    main()
