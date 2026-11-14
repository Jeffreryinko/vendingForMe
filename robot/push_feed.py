"""알림거리 쪽지(data/sisa/push.json) 만들기.

수파베이스가 15분마다 이 작은 파일만 읽어 가서, 처음 보는 id면 알림을 보낸다.
- brief: 최신 아침·저녁 브리핑 (id = 브리핑 id)
- big:   이번 판에 새로 생긴 큰 소식 (여러 나라가 한꺼번에 다룬 것)
"""
import json, os, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "sisa")
OUT = os.path.join(D, "push.json")
KST = dt.timezone(dt.timedelta(hours=9))

BIG_COUNTRIES = 8   # 이만큼 많은 나라 매체가 같은 일을 다루면 '큰 소식'
BIG_ITEMS = 15
SKIP_CAT = {"spo", "ent"}


def load(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def cut(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def deal():
    """딜: 오늘·어제 새로 들어온 거래 — 수파베이스가 '따라가는 이름'과 맞춰 봄"""
    d = load(os.path.join(ROOT, "data", "deal", "now.json"), {}) or {}
    today = dt.datetime.now(KST).date()
    keep = {str(today), str(today - dt.timedelta(days=1))}
    out = []
    for x in d.get("deals") or []:
        if x.get("date") not in keep or x.get("st") == "rumor":
            continue
        hay = " ".join(str(v) for v in [x.get("title"), x.get("ko"), x.get("co"), x.get("tgt"), " ".join(x.get("inv") or [])] if v).lower()
        out.append({"id": "deal:" + x["id"], "hay": cut(hay, 400), "body": cut(x.get("ko") or x.get("title"), 110)})
    with open(os.path.join(ROOT, "data", "deal", "push.json"), "w", encoding="utf-8") as f:
        json.dump({"v": 1, "at": dt.datetime.now(KST).isoformat(timespec="minutes"), "deals": out[:150]}, f, ensure_ascii=False, separators=(",", ":"))
    print("deal push.json:", len(out))


def main():
    old = load(OUT, {}) or {}
    out = {"v": 1, "at": dt.datetime.now(KST).isoformat(timespec="minutes")}

    b = load(os.path.join(D, "briefing", "latest.json"))
    if b and b.get("id") and b.get("items"):
        first = b["items"][0].get("t", "")
        out["brief"] = {
            "id": "brief:" + b["id"],
            "title": {"am": "☀️ ", "noon": "🌤️ "}.get(b.get("slot"), "🌙 ") + b.get("label", "브리핑"),
            "body": cut(first + " 외 " + str(len(b["items"]) - 1) + "가지", 110),
            "url": "sisa/",
        }

    big = [x for x in (old.get("big") or []) if x.get("at", "") >= (dt.datetime.now(KST) - dt.timedelta(hours=12)).isoformat()]
    idx = load(os.path.join(D, "editions", "_index.json"), []) or []
    eid = idx[-1]["id"] if idx else None
    ed = load(os.path.join(D, "editions", eid + ".json")) if eid else None
    seen = {x["id"] for x in big}
    nice = {}   # 브리핑에 같은 소식이 있으면 다듬어진 제목을 씀
    for it in (b or {}).get("items", []):
        for sid in it.get("sids") or []:
            nice.setdefault(sid, it.get("t"))
    for s in (ed or {}).get("stories", []):
        if s.get("delta") != "new" or s.get("cat") in SKIP_CAT or s.get("kind") == "kr":
            continue
        if len(s.get("countries") or []) < BIG_COUNTRIES or len(s.get("items") or []) < BIG_ITEMS:
            continue
        i = "big:" + s["sid"]
        if i in seen:
            continue
        big.append({"id": i, "title": "⚡ 큰 소식", "body": cut(nice.get(s["sid"]) or s.get("title") or s.get("label"), 110),
                    "url": "sisa/#issue-" + s["sid"], "at": out["at"]})
        seen.add(i)
    out["big"] = big[-4:]

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("push.json:", "brief" in out, len(out["big"]))


if __name__ == "__main__":
    import sys
    deal() if "deal" in sys.argv[1:] else main()
