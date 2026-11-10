"""baedat_daily.py — 배댓 창고 매일 로봇 (토큰 0, 검색 0번). 기획서 '배댓 수집 개편' 1·2·3·4·6단계.

1) 영상 찾기: 한국 인기 차트(전체 + 분야 7개, 최대 50개씩 4쪽) + 채널 씨앗 목록(seeds.json)의 새 영상 + 링크 제보함(daily/links.txt)
2) 댓글 받기: 올라온 지 3일째·14일째 두 번, 인기순 100개 + 답글 5개 (영상당 1단위)
3) 영상 관문·4) 댓글 거르기: robot/baedat_gate.py (웃음 표시 20%↑, 응원·칭찬·감동 제외, 비슷한 댓글 묶기, 영상당 5개)
6) 30일 규칙: 25일 넘게 확인 안 한 자료(창고·명댓글·월간판의 댓글)는 다시 받아 좋아요를 고치고, 지워진 댓글·영상은 뺌

  YOUTUBE_API_KEY=… python robot/baedat_daily.py
작성자 이름·프로필은 저장하지 않아요. 원문은 바꾸지 않아요.
"""
from __future__ import annotations

import glob, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baedat_gate as G

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/baedat"
DAILY = OUT / "daily"
KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.date().isoformat()
KEY = os.environ.get("YOUTUBE_API_KEY", "")
API = "https://www.googleapis.com/youtube/v3/"
CAP = 2500                     # 하루 쓸 최대 단위 (무료 1만의 1/4)
units = 0
CATS = {"23": "코미디", "24": "엔터테인먼트", "22": "인물/블로그", "20": "게임", "15": "동물", "17": "스포츠", "1": "영화/애니", "10": "음악", "26": "노하우", "2": "자동차"}
CHARTS = [None, "23", "24", "15", "17", "1", "20", "22"]
BAD = re.compile(r"(1등|첫댓|알고리즘|누가.*20\d\d|20\d\d년.*(보는|들으러)|사랑해|화이팅|파이팅|응원|축하|구독|좋아요 ?눌|스트리밍|투표|이벤트|당첨|광고|협찬|http|www\.|@\w)")


class Quota(Exception): pass


def yt(path, **q):
    global units
    if units >= CAP: raise Quota("오늘 몫을 다 썼어요")
    q["key"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(q)
    for i in range(3):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                units += 1
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]; units += 1
            if "quota" in body.lower(): raise Quota(body)
            if e.code in (400, 403, 404): return {"_err": e.code, "_body": body}
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return {"_err": "network"}


def jload(p, d):
    try: return json.loads(Path(p).read_text())
    except Exception: return d


def jsave(p, o, compact=True):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(o, ensure_ascii=False, indent=1))


def days_since(iso):
    try: return (NOW - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 86400
    except Exception: return 999


# ── 1) 영상 찾기 ──
def find_videos(state, seeds):
    V = state.setdefault("videos", {})
    block = set(seeds.get("block", []))
    def add(vid, pub, src):
        if vid in V or days_since(pub) > 16: return
        V[vid] = {"pub": pub, "src": src, "f": []}
    for cat in CHARTS:
        tok = None
        for _ in range(4):
            p = dict(part="snippet", chart="mostPopular", regionCode="KR", maxResults=50)
            if cat: p["videoCategoryId"] = cat
            if tok: p["pageToken"] = tok
            r = yt("videos", **p)
            for it in r.get("items", []):
                if it["snippet"]["channelId"] not in block: add(it["id"], it["snippet"]["publishedAt"], "chart")
            tok = r.get("nextPageToken")
            if not tok: break
    for ch in seeds.get("channels", []):
        if ch["id"] in block or not ch["id"].startswith("UC"): continue
        r = yt("playlistItems", part="contentDetails", playlistId="UU" + ch["id"][2:], maxResults=10)
        for it in r.get("items", []):
            cd = it["contentDetails"]; add(cd["videoId"], cd.get("videoPublishedAt", NOW.isoformat()), "seed")
    lp = DAILY / "links.txt"
    if lp.exists():
        for ln in lp.read_text().splitlines():
            m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", ln) or re.fullmatch(r"\s*([\w-]{11})\s*", ln)
            if m and m.group(1) not in V: V[m.group(1)] = {"pub": NOW.isoformat(), "src": "link", "f": [], "now": True}
        lp.write_text("".join(l + "\n" for l in lp.read_text().splitlines() if l.startswith("#")))


# ── 영상 정보 ──
def video_info(ids):
    out = {}
    for i in range(0, len(ids), 50):
        r = yt("videos", part="snippet,statistics,contentDetails,player", id=",".join(ids[i:i + 50]), maxWidth=1000)
        for it in r.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            d = it["contentDetails"].get("duration", ""); mm = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d)
            dur = sum(int(x or 0) * k for x, k in zip(mm.groups(), (3600, 60, 1))) if mm else 0
            pl = it.get("player", {}); w, h = pl.get("embedWidth"), pl.get("embedHeight")
            out[it["id"]] = dict(title=sn["title"], channel=sn["channelTitle"], ch=sn["channelId"], pub=sn["publishedAt"],
                                 views=int(st.get("viewCount", 0)), comments=int(st.get("commentCount", 0) or 0), dur=dur,
                                 ar=round(int(w) / int(h), 3) if w and h else None, cat=CATS.get(sn.get("categoryId"), sn.get("categoryId")),
                                 lang=(sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or ""), desc=sn.get("description", ""),
                                 has_c="commentCount" in st)
    return out


# ── 2) 댓글 받기 ──
def comments(vid, owner):
    r = yt("commentThreads", part="snippet,replies", videoId=vid, maxResults=100, order="relevance", textFormat="plainText")
    if "_err" in r: return None
    out = []
    for it in r.get("items", []):
        s = it["snippet"]["topLevelComment"]["snippet"]
        if (s.get("authorChannelId") or {}).get("value") == owner: continue
        tx = (s.get("textDisplay") or "").strip(); L = len(tx); han = len(re.findall("[가-힣]", tx))
        if L < 4 or L > 90 or han < max(3, L * 0.35) or BAD.search(tx): continue
        if len(re.sub(r"[ㅋㅎㅠㅜ!?.~ \n]", "", tx)) < 4: continue
        if s.get("likeCount", 0) < 30: continue
        reps = []
        for rp in (it.get("replies") or {}).get("comments", []):
            rs = rp["snippet"]; rt = (rs.get("textDisplay") or "").strip()
            if (rs.get("authorChannelId") or {}).get("value") == owner or not rt or len(rt) > 90 or BAD.search(rt): continue
            if rs.get("likeCount", 0) >= 30: reps.append([rp["id"], rt, rs["likeCount"]])
        reps.sort(key=lambda x: -x[2])
        out.append(dict(id=it["id"], text=tx, likes=s["likeCount"], replies=it["snippet"].get("totalReplyCount", 0), at=s["publishedAt"][:10], reps=reps[:2]))
    out.sort(key=lambda c: -c["likes"])
    return out


def month_of(pub):
    return (datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(KST)).strftime("%Y-%m")


def put(month_files, vid, info, picks):
    M = month_of(info["pub"])
    d = month_files.setdefault(M, jload(OUT / f"raw-{M}.json", {"month": M, "checkedAt": TODAY, "rule": "gate-v1", "videos": {}, "comments": []}))
    d["comments"] = [c for c in d["comments"] if c[0] != vid]
    d["videos"].pop(vid, None)
    if not picks: return
    d["videos"][vid] = [info["title"], info["channel"], info["pub"][:10], info["views"], info["cat"], info["ar"], info["dur"], info["ch"], G.short_line(info["desc"])]
    for c in picks:
        row = [vid, c["id"], c["text"], c["likes"], c["replies"], c["at"]]
        if c.get("reps"): row.append([[r[1], r[2]] for r in c["reps"]])
        d["comments"].append(row)
    d["comments"].sort(key=lambda r: -r[3])
    d["live"] = True


def collect(state, month_files):
    V = state["videos"]
    due = [v for v, s in V.items() if (not s["f"] and (days_since(s["pub"]) >= 3 or s.get("now"))) or (len(s["f"]) == 1 and days_since(s["pub"]) >= 14)]
    info = video_info(due)
    passed = 0
    for vid in due:
        s = V[vid]; s["f"].append(TODAY)
        i = info.get(vid)
        if not i or not i["has_c"] or i["comments"] < 30: continue
        if not (i["lang"].startswith("ko") or len(re.findall("[가-힣]", i["title"])) >= 2): continue
        if not G.video_ok(i["title"], i["channel"], i["cat"]): s["skip"] = "music/idol"; continue
        cs = comments(vid, i["ch"])
        if cs is None: continue
        ok = G.laugh_ratio([c["text"] for c in cs]) >= G.LAUGH_MIN
        s["gate"] = ok
        picks = G.pick(cs) if ok else []
        put(month_files, vid, i, picks)
        passed += bool(picks)
    return len(due), passed


# ── 6) 30일 규칙: 다시 확인 ──
def refresh_ids(ids):
    """댓글 id → 지금 좋아요 수 (없어진 댓글은 빠짐)"""
    now = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 50):
        r = yt("comments", part="snippet", id=",".join(ids[i:i + 50]), textFormat="plainText")
        if "_err" in r: continue
        for it in r.get("items", []): now[it["id"]] = it["snippet"].get("likeCount", 0)
    return now


def alive_videos(vids):
    have = set()
    vids = list(dict.fromkeys(vids))
    for i in range(0, len(vids), 50):
        r = yt("videos", part="id", id=",".join(vids[i:i + 50]))
        if "_err" in r: return set(vids)          # 확인 실패면 지우지 않음
        have |= {it["id"] for it in r.get("items", [])}
    return have


def stale(d):
    return days_since((d.get("checkedAt") or "2000-01-01") + "T00:00:00+09:00") >= 25


def refresh(month_files):
    n = 0
    for p in sorted(glob.glob(str(OUT / "raw-*.json"))):
        M = Path(p).stem[4:]
        d = month_files.get(M) or jload(p, None)
        if not d or not stale(d): continue
        alive = alive_videos(list(d["videos"]))
        now = refresh_ids([c[1] for c in d["comments"] if c[0] in alive])
        d["comments"] = [c[:3] + [now[c[1]]] + c[4:] for c in d["comments"] if c[1] in now]
        keep = {c[0] for c in d["comments"]}
        d["videos"] = {k: v for k, v in d["videos"].items() if k in keep}
        d["comments"].sort(key=lambda r: -r[3]); d["checkedAt"] = TODAY
        month_files[M] = d; n += 1
    for p in sorted(glob.glob(str(OUT / "legend-*.json"))):          # 월간 명댓글
        d = jload(p, None)
        if not d or not stale(d): continue
        now = refresh_ids([x["comment"]["id"] for x in d["picks"]])
        d["picks"] = [x for x in d["picks"] if x["comment"]["id"] in now]
        for x in d["picks"]: x["comment"]["likes"] = now[x["comment"]["id"]]
        d["count"] = len(d["picks"]); d["checkedAt"] = TODAY; jsave(p, d); n += 1
    lp = OUT / "legend.json"; L = jload(lp, None)                     # 명작
    if L and stale(L):
        ids = [m["comment"]["id"] for m in L["moments"] if m.get("source") != "broadcast"] + [x["id"] for m in L["moments"] for x in m.get("more", [])]
        now = refresh_ids(ids)
        for m in L["moments"]:
            if m["comment"]["id"] in now: m["comment"]["likes"] = now[m["comment"]["id"]]
            m["more"] = [dict(x, likes=now[x["id"]]) for x in m.get("more", []) if x["id"] in now]
        L["moments"] = [m for m in L["moments"] if m.get("source") == "broadcast" or m["comment"]["id"] in now]
        L["checkedAt"] = TODAY; jsave(lp, L, compact=False); n += 1
    for p in sorted(glob.glob(str(OUT / "20??-??.json"))):            # 월간판 배댓
        d = jload(p, None)
        if not d or not stale({"checkedAt": d.get("checkedAt") or (d.get("collectedAt") or "")[:10]}): continue
        now = refresh_ids([b["id"] for v in d["videos"] for b in v["best"]])
        for v in d["videos"]:
            v["best"] = [dict(b, likes=now[b["id"]]) for b in v["best"] if b["id"] in now]
        d["videos"] = [v for v in d["videos"] if v["best"]]
        d["checkedAt"] = TODAY; jsave(p, d); n += 1
    return n


def write(month_files):
    for M, d in month_files.items():
        jsave(OUT / f"raw-{M}.json", d)
    lp = OUT / "legend.json"; L = jload(lp, {})
    raws = {r["month"]: r for r in L.get("raws", [])}
    for M, d in month_files.items():
        raws[M] = {"month": M, "file": f"raw-{M}.json", "videos": len(d["videos"]), "comments": len(d["comments"]), "checkedAt": d.get("checkedAt", TODAY), **({"live": True} if d.get("live") else {})}
    L["raws"] = sorted(raws.values(), key=lambda r: r["month"], reverse=True)
    jsave(lp, L, compact=False)


def main():
    if not KEY: sys.exit("YOUTUBE_API_KEY 가 없어요")
    state = jload(DAILY / "state.json", {"videos": {}})
    seeds = jload(OUT / "seeds.json", {"channels": [], "block": []})
    month_files = {}
    msg = ""
    try:
        find_videos(state, seeds)
        due, passed = collect(state, month_files)
        msg = f"영상 후보 {len(state['videos'])} · 댓글 받은 영상 {due} · 관문 통과 {passed}"
        r = refresh(month_files); msg += f" · 다시 확인한 파일 {r}"
    except Quota as e:
        msg += f" · 멈춤: {str(e)[:80]}"
    state["videos"] = {k: v for k, v in state["videos"].items() if days_since(v["pub"]) <= 20 or v.get("now") and len(v["f"]) < 1}
    state["lastRun"] = NOW.isoformat(timespec="seconds"); state["units"] = units
    jsave(DAILY / "state.json", state)
    write(month_files)
    print(msg, "· 단위", units)


if __name__ == "__main__":
    main()
