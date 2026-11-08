"""유튜브 베스트 댓글 5개 — 트렌드·도구·AI 로봇이 같이 씀 (유튜브 API 1회 = 할당량 1, 토큰 0)

    from ytcomments import Comments
    cm = Comments(path, key, budget=150)          # 한 번 실행에 새로 물어볼 최대 영상 수
    lst = cm.get(vid)                             # [{"a": 글쓴이, "t": 댓글, "l": 좋아요}] 최대 5개 (없으면 [])
    cm.save()

· '관련성 순'(유튜브가 보여 주는 인기 댓글 순)으로 5개
· 한 번 받은 영상은 24시간 동안 기억(댓글이 없던 영상은 3시간) → 다시 묻지 않음. 댓글이 꺼진 영상은 빈 목록으로 기억
"""
import json, time, requests
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3/commentThreads"


def top_comments(vid, key, n=5):
    try:
        r = requests.get(API, params={"part": "snippet", "videoId": vid, "order": "relevance", "maxResults": n,
                                      "textFormat": "plainText", "key": key}, timeout=10)
        if r.status_code == 403 and "commentsDisabled" in r.text: return []
        if r.status_code != 200: return None                     # 한도 초과 등 → 다음에 다시
        out = []
        for it in r.json().get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            t = " ".join((s.get("textDisplay") or "").split())
            if not t: continue
            out.append({"a": (s.get("authorDisplayName") or "").lstrip("@")[:40], "t": t[:400], "l": int(s.get("likeCount") or 0)})
        return out[:n]
    except Exception:
        return None


def is_short(vid):
    """세로 쇼츠 영상인지: /shorts/ID 가 200 이면 쇼츠, 일반 영상이면 watch 로 돌려보냄. 모르면 None"""
    try:
        r = requests.head(f"https://www.youtube.com/shorts/{vid}", allow_redirects=False, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200: return True
        if r.status_code in (301, 302, 303, 307): return False
    except Exception: pass
    return None


class Comments:
    def __init__(self, path, key, budget=150, ttl=24 * 3600):
        self.path = Path(path); self.key = key; self.budget = budget; self.ttl = ttl; self.asked = 0
        try: self.mem = json.loads(self.path.read_text())
        except Exception: self.mem = {}

    def get(self, vid):
        if not vid: return []
        m = self.mem.get(vid) if vid != "_short" else None
        if m and time.time() - m.get("at", 0) < (self.ttl if m.get("cm") else 3 * 3600): return m.get("cm", [])   # 댓글이 아직 없던 새 영상은 3시간 뒤 다시
        if not self.key or self.asked >= self.budget: return (m or {}).get("cm", [])
        self.asked += 1
        cm = top_comments(vid, self.key)
        if cm is None: return (m or {}).get("cm", [])
        self.mem[vid] = {"at": int(time.time()), "cm": cm}
        return cm

    def short(self, vid):
        """쇼츠 여부 (한 번 알면 기억)"""
        if not vid: return False
        m = self.mem.setdefault("_short", {})
        if vid not in m:
            v = is_short(vid)
            if v is None: return False
            m[vid] = 1 if v else 0
        return bool(m[vid])

    def save(self):
        sh = self.mem.pop("_short", {})
        if len(self.mem) > 3000:
            self.mem = dict(sorted(self.mem.items(), key=lambda kv: kv[1].get("at", 0))[-2200:])
        if len(sh) > 4000: sh = dict(list(sh.items())[-3000:])
        self.mem["_short"] = sh
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.mem, ensure_ascii=False, separators=(",", ":")))
        print(f"  베스트 댓글: 새로 물어본 영상 {self.asked}개 · 기억 {len(self.mem)}개")
