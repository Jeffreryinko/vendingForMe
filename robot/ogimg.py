"""글·기사의 대표 사진(og:image) 찾기 — 트렌드·AI·도구 로봇이 같이 씀 (토큰 0)

    from ogimg import Photos
    ph = Photos("data/_img.json", budget=120)     # 한 번 실행에 새로 확인할 최대 개수
    url = ph.get(page_url)                        # 대표 사진 주소 또는 ""
    ph.drop_logos(items, key="img")               # 여러 글에 똑같이 붙은 사진(사이트 로고)은 지움
    ph.save()

· 한 번 본 주소는 파일에 기억 (최대 6,000개) → 다음 실행에서 다시 받지 않음
· 해커뉴스·긱뉴스처럼 '글 소개 페이지'면, 거기 걸린 원문으로 한 번 더 따라가서 그 사진을 씀
· https 사진만 (사이트가 https 라서). 앞부분 300KB 만 읽음
"""
import json, re, urllib.request, hashlib
from pathlib import Path

UA = "Mozilla/5.0 (compatible; vendingForMe/1.0; +https://jeffreryinko.github.io/vendingForMe/)"
PATS = (r'<meta[^>]+property=["\']og:image(?::url|:secure_url)?["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']')
# 글 소개 페이지 → 원문 링크
HOPS = ((r"news\.ycombinator\.com/item", r'<span class="titleline"><a href="(https?://[^"]+)"'),
        (r"news\.hada\.io/topic", r'<div class=["\']?topictitle[^>]*>\s*<a href=["\'](https?://[^"\']+)'),
        (r"news\.google\.", None), (r"(x|twitter)\.com/", None), (r"reddit\.com/", None))


def _html(url, n=300_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Language": "ko,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.read(n).decode("utf-8", "ignore")


def og_from_html(html, base=""):
    for p in PATS:
        m = re.search(p, html, re.I)
        if m:
            u = m.group(1).replace("&amp;", "&").strip()
            if u.startswith("//"): u = "https:" + u
            elif u.startswith("/") and base: u = re.match(r"https?://[^/]+", base).group(0) + u
            if u.startswith("http://"): u = "https://" + u[7:]
            if u.startswith("https://") and not re.search(r"\.svg(\?|$)|favicon|/logo[\-_.]|default[\-_]?(og|share|image)", u, re.I):
                return u[:600]
    return ""


def og_image(url):
    """기사·글 주소 → 대표 사진 주소 ("" = 없음)"""
    try:
        for host, hop in HOPS:
            if re.search(host, url):
                if not hop: return ""
                html = _html(url, 200_000); m = re.search(hop, html)
                if not m: return ""
                url = m.group(1).replace("&amp;", "&"); break
        return og_from_html(_html(url), url)
    except Exception:
        return ""


class Photos:
    def __init__(self, path, budget=120):
        self.path = Path(path); self.budget = budget; self.tried = 0
        try: self.mem = json.loads(self.path.read_text())
        except Exception: self.mem = {}

    def get(self, url):
        if not url: return ""
        k = hashlib.md5(url.encode()).hexdigest()[:14]
        if k in self.mem: return self.mem[k]
        if self.tried >= self.budget: return ""
        self.tried += 1; v = og_image(url); self.mem[k] = v
        return v

    @staticmethod
    def drop_logos(items, key="img", limit=3):
        """같은 사진이 여러 글에 붙었으면 그 사이트 로고·기본 그림 → 지움"""
        cnt = {}
        for it in items:
            if it.get(key): cnt[it[key]] = cnt.get(it[key], 0) + 1
        for it in items:
            if it.get(key) and cnt[it[key]] >= limit: it.pop(key, None)

    def save(self):
        if len(self.mem) > 6000: self.mem = dict(list(self.mem.items())[-4500:])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.mem, ensure_ascii=False, separators=(",", ":")))
        print(f"  대표 사진: 새로 확인 {self.tried}건 · 기억 {len(self.mem)}건")
