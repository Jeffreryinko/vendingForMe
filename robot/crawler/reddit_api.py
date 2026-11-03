"""Reddit 공식 API (무료, 개인용 '스크립트' 앱).
GitHub 서버에서는 Reddit RSS가 자주 차단(429)되므로, 키가 있으면 이 모듈로 정식 경로를 씁니다.

필요한 비밀 설정: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET  (https://www.reddit.com/prefs/apps 에서 발급)
"""
from __future__ import annotations

import hashlib
import os
import re
import time
from datetime import datetime, timezone

import requests

UA = "python:vendingForMe:v1.0 (personal news digest; by u/" + os.environ.get("REDDIT_USERNAME", "anon") + ")"
_token = {"v": None, "exp": 0}


def enabled() -> bool:
    return bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))


def token() -> str | None:
    if not enabled():
        return None
    if _token["v"] and time.time() < _token["exp"] - 60:
        return _token["v"]
    r = requests.post("https://www.reddit.com/api/v1/access_token",
                      auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
                      data={"grant_type": "client_credentials"}, headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    j = r.json()
    _token.update(v=j["access_token"], exp=time.time() + int(j.get("expires_in", 3600)))
    return _token["v"]


def _get(path, params=None):
    r = requests.get("https://oauth.reddit.com" + path, params=params, timeout=25,
                     headers={"Authorization": "bearer " + token(), "User-Agent": UA})
    if r.status_code == 429:
        time.sleep(15)
        r = requests.get("https://oauth.reddit.com" + path, params=params, timeout=25,
                         headers={"Authorization": "bearer " + token(), "User-Agent": UA})
    r.raise_for_status()
    return r.json()


def subreddit_from_url(url: str) -> str | None:
    m = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)", url or "")
    return m.group(1) if m else None


def top_posts(url: str, limit=10):
    """sources.yaml 의 RSS 주소를 받아 같은 모양(parse_rss 결과)으로 글 목록을 돌려줌."""
    sub = subreddit_from_url(url)
    if not sub:
        raise ValueError("subreddit 없음: " + url)
    t = "day" if "t=day" in url else ("week" if "t=week" in url else "day")
    listing = "top" if "/top" in url else ("hot" if "/hot" in url else "top")
    j = _get(f"/r/{sub}/{listing}", {"t": t, "limit": limit, "raw_json": 1})
    rows = []
    for rank, ch in enumerate(j.get("data", {}).get("children", []), start=1):
        d = ch.get("data", {})
        if d.get("stickied") or d.get("over_18"):
            continue
        link = "https://www.reddit.com" + d.get("permalink", "")
        title = (d.get("title") or "").strip()
        if not title:
            continue
        rows.append({
            "guid_hash": hashlib.sha1((d.get("name") or link).encode()).hexdigest()[:20],
            "url": link,
            "title": title[:300],
            "summary": None,
            "published_at": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat(),
            "rank": rank,
            "metric": {"score": d.get("score", 0), "comments": d.get("num_comments", 0)},
        })
    return rows


def comments(url: str, limit=20):
    """글 주소 → 추천순 상위 댓글 (comments.py 가 씀)."""
    m = re.search(r"/comments/([a-z0-9]+)", url or "")
    if not m:
        return {"err": "주소 형식"}
    j = _get(f"/comments/{m.group(1)}", {"sort": "top", "limit": limit, "depth": 1, "raw_json": 1})
    out = []
    for ch in (j[1].get("data", {}).get("children", []) if isinstance(j, list) and len(j) > 1 else []):
        d = ch.get("data", {})
        body = (d.get("body") or "").strip()
        if not body or body in ("[deleted]", "[removed]") or d.get("stickied"):
            continue
        out.append({"t": body[:600], "by": d.get("author", ""), "score": d.get("score", 0)})
        if len(out) >= 15:
            break
    return {"comments": out, "order": "추천순(Reddit top)"}
