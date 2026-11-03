"""커뮤니티 글의 '현지 반응(베스트 댓글)' 수집기.

지원: Reddit(댓글 RSS), Hacker News(Algolia API), PTT(推/噓/→ 집계 + 추천 댓글), 하테나 북마크(코멘트), Lemmy(API)
그 밖의 사이트는 '댓글 미연결'로 남깁니다. 글마다 상위 댓글 최대 15개만 가져오고, 화면에는 그중 3개만 씁니다.

  python comments.py targets.json out.json
  targets.json = [{"id":..., "s":"reddit-france", "u":"https://..."}, ...]
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

H = {"User-Agent": "Mozilla/5.0 (sisa-vending; personal news reader)"}
TAG = re.compile(r"<[^>]+>")


def clean(t: str) -> str:
    t = html.unescape(TAG.sub(" ", t or ""))
    return re.sub(r"\s+", " ", t).strip()


def get(url, **kw):
    for wait in (0, 12, 30):
        if wait:
            time.sleep(wait)
        r = requests.get(url, headers=H, timeout=25, **kw)
        if r.status_code != 429:
            return r
    return r


def reddit(u):
    try:
        import reddit_api
        if reddit_api.enabled():
            return reddit_api.comments(u)
    except Exception as e:  # noqa: BLE001
        pass
    # 글 주소 + .rss → 댓글 피드(기본 '베스트' 순). 첫 항목은 본문이라 건너뜀
    r = get(u.rstrip("/") + "/.rss?limit=20")
    if r.status_code != 200:
        return {"err": f"http {r.status_code}"}
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.content)
    out = []
    for e in root.findall("a:entry", ns)[1:]:
        body = clean((e.findtext("a:content", "", ns)))
        body = re.sub(r"submitted by .*$", "", body).strip()
        if body and body not in ("[deleted]", "[removed]"):
            out.append({"t": body[:600], "by": (e.findtext("a:author/a:name", "", ns) or "").replace("/u/", "")})
        if len(out) >= 15:
            break
    return {"comments": out, "order": "베스트순(Reddit 기본)"}


def hackernews(u):
    r = get("https://hn.algolia.com/api/v1/search", params={"query": u, "restrictSearchableAttributes": "url", "tags": "story"})
    hits = r.json().get("hits", [])
    if not hits:
        return {"err": "HN 글을 찾지 못함"}
    sid = max(hits, key=lambda h: h.get("points") or 0)["objectID"]
    item = get(f"https://hn.algolia.com/api/v1/items/{sid}").json()
    kids = [k for k in item.get("children", []) if k.get("text")]
    # HN 은 페이지 순서가 곧 순위. 답글이 많이 달린 댓글을 먼저
    kids.sort(key=lambda k: -len(k.get("children") or []))
    out = [{"t": clean(k["text"])[:600], "by": k.get("author", ""), "replies": len(k.get("children") or [])} for k in kids[:15]]
    return {"comments": out, "order": "답글 많은 순", "link": f"https://news.ycombinator.com/item?id={sid}"}


def ptt(u):
    r = get(u, cookies={"over18": "1"})
    if r.status_code != 200:
        return {"err": f"http {r.status_code}"}
    pushes = re.findall(r'<span class="[^"]*push-tag">([^<]+)</span><span class="[^"]*push-userid">([^<]+)</span><span class="[^"]*push-content">([^<]*)</span>', r.text)
    cnt = {"推": 0, "噓": 0, "→": 0}
    out = []
    for tag, uid, content in pushes:
        tag = tag.strip()
        if tag in cnt:
            cnt[tag] += 1
        c = clean(content).lstrip(":").strip()
        if tag in ("推", "噓") and len(c) >= 6:
            out.append({"t": c[:300], "by": uid.strip(), "tag": tag})
    # 길고 내용 있는 推·噓 댓글을 고루
    tui = [x for x in out if x["tag"] == "推"][:8]
    xu = [x for x in out if x["tag"] == "噓"][:5]
    return {"comments": tui + xu, "order": "推(추천)·噓(야유) 댓글", "push": cnt}


def hatena(u):
    r = get("https://b.hatena.ne.jp/entry/jsonlite/", params={"url": u})
    if r.status_code != 200 or not r.text.strip() or r.text.strip() == "null":
        return {"err": "북마크 없음"}
    j = r.json()
    bms = [b for b in j.get("bookmarks", []) if b.get("comment")]
    # jsonlite 는 최신순. 긴 코멘트를 우선
    bms.sort(key=lambda b: -len(b["comment"]))
    return {"comments": [{"t": clean(b["comment"])[:300], "by": b.get("user", "")} for b in bms[:15]], "order": "북마크 코멘트(긴 순)", "count": j.get("count")}


def lemmy(u):
    m = re.match(r"https?://([^/]+)/post/(\d+)", u)
    if not m:
        return {"err": "주소 형식"}
    host, pid = m.groups()
    r = get(f"https://{host}/api/v3/comment/list", params={"post_id": pid, "sort": "Top", "max_depth": 1, "limit": 15})
    cs = r.json().get("comments", [])
    return {"comments": [{"t": clean(c["comment"]["content"])[:600], "by": c["creator"]["name"], "score": c["counts"]["score"]} for c in cs[:15]], "order": "추천순"}


ADAPTERS = {"hackernews": hackernews, "ptt-gossiping": ptt, "hatena-hot": hatena, "lemmy": lemmy}


def fetch(t):
    s = t["s"]
    fn = reddit if s.startswith("reddit-") else ADAPTERS.get(s)
    if not fn:
        return {"err": "댓글 미연결"}
    try:
        return fn(t["u"])
    except Exception as e:  # noqa: BLE001
        return {"err": str(e)[:120]}


if __name__ == "__main__":
    targets = json.load(open(sys.argv[1]))
    out = {}
    for t in targets:
        res = fetch(t)
        out[t["id"]] = res
        n = len(res.get("comments", []))
        print(f'{t["s"]:22} {t["id"]} {"댓글 " + str(n) if n else res.get("err")}', flush=True)
        if t["s"].startswith("reddit-"):
            time.sleep(8)
    json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
