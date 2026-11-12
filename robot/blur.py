"""흐린 미리보기 — 이슈 사진마다 16px 짜리 아주 작은 그림(약 100~200바이트)을 판에 같이 실어요.
화면은 이 그림을 먼저 깔고(기다림 0), 진짜 사진이 오면 그 위에 얹어요.
작은 그림은 무료 축소 서비스(wsrv.nl)에서 받아요 — 토큰 0, 이 저장소에 사진 파일을 쌓지 않아요.
"""
import base64
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

W = 16


def _warm(big):
    """화면이 실제로 쓰는 크기(목록 168px·큰 사진 820px)를 축소 서비스에 한 번 만들어 둠 → 사람이 처음 열 때 기다림이 줄어듦"""
    q = urllib.parse.quote(big, safe="")
    for a in ("&w=168&h=168&fit=cover&output=webp&q=72", "&w=820&output=webp&q=72"):
        try:
            req = urllib.request.Request("https://wsrv.nl/?url=" + q + a, headers={"User-Agent": "Mozilla/5.0 (compatible; vendingForMe/1.0)"})
            with urllib.request.urlopen(req, timeout=6) as r:
                r.read(200000)
        except Exception:
            pass


def _one(u):
    try:
        big = __import__("re").sub(r"(ichef\.bbci\.co\.uk/(?:ace/standard|ace/ws|news))/\d{2,3}/", r"\1/976/", u)
        x = "https://wsrv.nl/?url=" + urllib.parse.quote(big, safe="") + f"&w={W}&h={W}&fit=cover&output=webp&q=40"
        req = urllib.request.Request(x, headers={"User-Agent": "Mozilla/5.0 (compatible; vendingForMe/1.0)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            b = r.read(2000)
        if 20 < len(b) < 1200 and b[:4] == b"RIFF":
            _warm(big)                                   # 원본을 받을 수 있는 사진만 미리 만들어 둠
            return base64.b64encode(b).decode()
    except Exception:
        pass
    return ""


def add_blur(stories, prev_stories=(), limit=150):
    """s['ph']['b'] 를 채움. 지난 판에 이미 있던 사진은 그대로 물려받고, 새 사진만 받아 옴. 받은 수를 돌려줌"""
    have = {s["ph"]["u"]: s["ph"]["b"] for s in prev_stories if (s.get("ph") or {}).get("b")}
    need = []
    for s in stories:
        ph = s.get("ph")
        if not ph or not ph.get("u") or ph.get("b"):
            continue
        if ph["u"] in have:
            ph["b"] = have[ph["u"]]
        else:
            need.append(ph)
    need = need[:limit]
    if need:
        with ThreadPoolExecutor(12) as ex:
            for ph, b in zip(need, ex.map(_one, [p["u"] for p in need])):
                if b:
                    ph["b"] = b
    return sum(1 for p in need if p.get("b")), len(need)
