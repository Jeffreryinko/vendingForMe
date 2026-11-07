"""유튜브 베스트 댓글 5개 — 트렌드·도구·AI 로봇이 같이 씀 (유튜브 API 1회 = 할당량 1, 토큰 0)

    from ytcomments import Comments
    cm = Comments(path, key, budget=150)          # 한 번 실행에 새로 물어볼 최대 영상 수
    lst = cm.get(vid)                             # [{"a": 글쓴이, "t": 댓글, "l": 좋아요}] 최대 5개 (없으면 [])
    cm.save()

· '관련성 순'(유튜브가 보여 주는 인기 댓글 순)으로 5개
· 한 번 받은 영상은 12시간 동안 기억 → 다시 묻지 않음. 댓글이 꺼진 영상은 빈 목록으로 기억
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


class Comments:
    def __init__(self, path, key, budget=150, ttl=12 * 3600):
        self.path = Path(path); self.key = key; self.budget = budget; self.ttl = ttl; self.asked = 0
        try: self.mem = json.loads(self.path.read_text())
        except Exception: self.mem = {}

    def get(self, vid):
        if not vid: return []
        m = self.mem.get(vid)
        if m and time.time() - m.get("at", 0) < self.ttl: return m.get("cm", [])
        if not self.key or self.asked >= self.budget: return (m or {}).get("cm", [])
        self.asked += 1
        cm = top_comments(vid, self.key)
        if cm is None: return (m or {}).get("cm", [])
        self.mem[vid] = {"at": int(time.time()), "cm": cm}
        return cm

    def save(self):
        if len(self.mem) > 3000:
            self.mem = dict(sorted(self.mem.items(), key=lambda kv: kv[1].get("at", 0))[-2200:])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.mem, ensure_ascii=False, separators=(",", ":")))
        print(f"  베스트 댓글: 새로 물어본 영상 {self.asked}개 · 기억 {len(self.mem)}개")
