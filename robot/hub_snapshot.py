#!/usr/bin/env python3
"""브로제이 영업 허브(아티팩트) → 종이판용 자료 한 벌.  python3 robot/hub_snapshot.py <허브 index.html> <rec/cards.js> <출력.json> [--with-cost]
허브 화면의 글·표만 남기고(버튼·입력칸·그림·스크립트 빼기) JSON 으로 저장해요.
--with-cost 가 없으면 '판매가·원가 메모'·'확인 필요' 칸은 빼요 (공개 저장소에는 원가를 올리지 않아요)."""
import sys, re, json
from html.parser import HTMLParser

src, cards_js, out = sys.argv[1:4]
with_cost = "--with-cost" in sys.argv
s = open(src, encoding="utf8").read()

def jblock(i):
    m = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % i, s, re.S)
    return json.loads(m.group(1)) if m else None

KEEP = {"h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "b", "strong", "em",
        "a", "br", "dl", "dt", "dd", "blockquote", "small", "div", "section", "article", "figure", "figcaption", "details", "summary"}
DROP = {"script", "style", "svg", "button", "input", "select", "textarea", "img", "nav", "form", "template", "canvas", "noscript", "option", "label", "picture", "video", "iframe"}
VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr", "col"}

class San(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.o = []; self.skip = 0
    def handle_starttag(self, t, a):
        if self.skip:
            if t not in VOID: self.skip += 1
            return
        if t in DROP:
            if t not in VOID: self.skip = 1
            return
        if t in ("section", "article", "figure"): t = "div"
        if t not in KEEP: return self.o.append(" ")   # span 같은 것은 빈칸으로 (붙어 보이지 않게)
        at = ""
        d = dict(a)
        if t == "a":
            h = d.get("href") or ""
            if not re.match(r"https?:", h): return self.o.append("<span>")  # 안쪽 링크는 글만
            at = ' href="%s"' % h.replace('"', "&quot;")
        for k in ("colspan", "rowspan"):
            if d.get(k): at += ' %s="%s"' % (k, d[k])
        self.o.append("<%s%s>" % (t, at))
    def handle_startendtag(self, t, a):
        if not self.skip and t == "br": self.o.append("<br>")
    def handle_endtag(self, t):
        if self.skip:
            if t not in VOID: self.skip -= 1
            return
        if t in ("section", "article", "figure"): t = "div"
        if t == "a": self.o.append("</a>"); return
        if t in KEEP and t not in VOID: self.o.append("</%s>" % t)
        elif t not in KEEP: self.o.append(" ")
    def handle_data(self, d):
        if not self.skip: self.o.append(d.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def clean(h):
    p = San(); p.feed(h); x = "".join(p.o)
    x = re.sub(r"<span>(.*?)</a>", r"\1", x, flags=re.S)   # 안쪽 링크 정리
    x = x.replace("<span>", "")
    x = re.sub(r"\s+", " ", x)
    x = re.sub(r"([>])\s*[A-Za-z][A-Za-z0-9 ·.,&'/()-]{1,40}\s*<h([1-3])>", r"\1<h\2>", x)   # 영어 머리말(eyebrow) 빼기
    for _ in range(6): x = re.sub(r"<(div|p|li|td|th|b|strong|em|small|dd|dt|ul|ol|tr|summary)>\s*</\1>", "", x)
    for _ in range(6): x = re.sub(r"<div>\s*(<div>.*?</div>)\s*</div>", r"\1", x, flags=re.S) if False else x
    return x.strip()

def view(v):
    i = s.find('id="v-%s"' % v)
    if i < 0: return ""
    i = s.find(">", i) + 1
    j = s.find('role="tabpanel"', i)
    j = s.rfind("<", 0, j) if j > 0 else len(s)
    return s[i:j]

views = {}
for v in ["overview", "products", "texts", "proof", "calc", "evidence", "bench", "global", "internal"]:
    views[v] = clean(view(v))

# 내부 메모: h2 칸별로 나눠 원가 칸 빼기
if not with_cost:
    parts = re.split(r"(?=<h2>)", views["internal"])
    views["internal"] = "".join(p for p in parts if not re.match(r"<h2>\s*(판매가·원가 메모|확인 필요)", p))

cards = []
m = re.search(r"window\.BJ_CARDS\s*=\s*(\[.*\])\s*;?", open(cards_js, encoding="utf8").read(), re.S)
if m:
    cards = json.loads(m.group(1))
    for c in cards:
        for k in list(c):
            if k not in ("id", "n", "s", "x", "tp", "tm", "m", "l"): c.pop(k)

json.dump({"views": views, "data": jblock("data"), "read": jblock("readdata"), "evx": jblock("evxdata"), "cards": cards, "withCost": with_cost},
          open(out, "w", encoding="utf8"), ensure_ascii=False)
print("ok", out, {k: len(v) for k, v in views.items()}, "read", len(jblock("readdata") or []), "cards", len(cards))
