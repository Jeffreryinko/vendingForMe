#!/usr/bin/env python3
"""시사 브리핑 로봇 — 아침 7시 · 저녁 7시에 '브리핑 글'을 무료 AI 로 씀.

 무엇을 하나
   1) 가장 새 판(data/sisa/editions/_index.json)에서 중요한 이슈 40개 안팎을 고름 (스포츠는 뺌)
   2) 이슈마다 나라·매체별 기사 제목을 묶어 AI 에게 건넴  ← AI 는 이 제목·요약에 있는 것만 쓸 수 있음
   3) AI 가 같은 일을 다룬 이슈를 합치고, 중요한 순서로 12~20개를 골라
        제목 · 한두 줄 · 요약 · 왜 중요 · 어제와 달라진 점 · 나라마다 이렇게 전해요 · 배경(배움 글 번호) 를 씀
   4) 답을 검사(없는 이슈 번호·없는 배움 글 번호·너무 긴 글은 버림)해서
        data/sisa/briefing/latest.json  +  data/sisa/briefing/<날짜>_<am|pm>.json  에 저장

 AI: Google Gemini(무료) 먼저 → 안 되면 Groq(무료). 열쇠는 GitHub 비밀 설정 GEMINI_API_KEY · GROQ_API_KEY.
     열쇠가 하나도 없으면 아무것도 바꾸지 않고 끝냄 (화면은 전에 있던 브리핑을 그대로 보여 줌).
 모델 이름은 자주 바뀌므로 실행할 때 서비스에 '지금 쓸 수 있는 모델 목록'을 물어 고름
     (GEMINI_MODEL · GROQ_MODEL 로 직접 정할 수도 있음).

 배경 설명을 AI 가 지어내지 않게: 배경은 '배움 글 번호'만 고르게 하고, 화면이 그 배움 글로 연결함.

 시험:  python robot/briefing.py --dry   (AI 에게 보낼 글만 만들어 길이를 보여 줌)
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "sisa"
OUT = D / "briefing"
KST = timezone(timedelta(hours=9))
CAT = {"war": "전쟁·안보", "pol": "정치·외교", "eco": "경제·시장", "tech": "기술·과학", "dis": "재난·사고", "soc": "사회", "cul": "문화", "etc": "기타"}
MAX_STORIES = 42          # AI 에게 보여 줄 이슈 수
MAX_HEADS = 9             # 이슈 하나에 보여 줄 기사 제목 수
MIN_ITEMS, MAX_ITEMS = 8, 20


def log(*a): print(*a, flush=True)
def rj(p, d=None):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d
def wj(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


# ───────── 자료 모으기 ─────────
def latest_edition():
    ix = rj(D / "editions" / "_index.json", [])
    full = [e for e in ix if not e.get("stub") and e.get("stories")]
    return full[-1] if full else None


def feed_items(ed_id):
    by = {}
    for f in (D / "feed").glob(f"{ed_id}__*.json"):
        for it in (rj(f, {}) or {}).get("items", []):
            by[it["id"]] = it
    return by


def source_names():
    """매체 번호 → 한국어 이름·나라·성향. robot/crawler/sources.yaml 과 sisa/lean.json(성향표)에서."""
    names, lean = {}, {}
    try:
        import yaml  # type: ignore
        for f in (ROOT / "robot" / "crawler").glob("sources*.y*ml"):
            y = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for s in (y.get("sources") if isinstance(y, dict) else y) or []:
                if isinstance(s, dict) and s.get("id"):
                    names[s["id"]] = (s.get("name_ko") or s.get("name") or s["id"]) + (f"〔{s['lean']}〕" if s.get("lean") else "")
                    if s.get("lean"): lean[s["id"]] = s["lean"]
    except Exception as e:
        log("매체 이름표를 못 읽음:", e)
    return names, lean


def learn_index():
    """배경으로 연결할 수 있는 배움 글 목록 (tools/learn_index.mjs 가 만든 data/sisa/learn_index.json)."""
    li = rj(D / "learn_index.json", {}) or {}
    return {"term": li.get("term", {}), "hist": li.get("hist", {}), "ch": li.get("ch", {})}


def pick_stories(ed):
    ss = [s for s in ed["stories"] if s.get("kind") != "brief" and s.get("cat") != "spo" and s.get("life") != "cool" and len(s.get("items", [])) >= 2]
    def score(s):
        return (0 if s.get("top") else 1, -(len(s.get("countries") or [])) * 3 - len(s.get("items", [])) - (8 if s.get("wk") else 0) - (4 if s.get("delta") == "new" else 0))
    ss.sort(key=score)
    return ss[:MAX_STORIES]


OP = re.compile(r"opinion|editorial|column|comment|kommentar|meinung|tribune|opini[oó]n|opinie|analys|사설|칼럼|社説|社论|评论|editoriale|leitartikel", re.I)
def is_opinion(it):
    """사설·칼럼 같은 의견 글인지 — 주소와 RSS 꼬리표로 어림."""
    return bool(OP.search(it.get("u", "")) or any(OP.search(str(t)) for t in ((it.get("m") or {}).get("tg") or [])))


def story_block(s, by, names):
    heads, seen, cs = [], set(), set()
    its = [by[i] for i in s.get("items", []) if i in by]
    # 나라가 고루 나오게: 나라마다 한 개씩 먼저, 그다음 남은 것
    its.sort(key=lambda it: (0 if it.get("k") == "news" else 1))
    first, rest = [], []
    for it in its:
        ko = (it.get("ko") or (it["t"] if it.get("c") == "KR" else "")).strip()
        if not ko: continue
        k = re.sub(r"\W", "", ko)[:26]
        if k in seen: continue
        seen.add(k)
        (first if it["c"] not in cs else rest).append((it, ko)); cs.add(it["c"])
    for it, ko in (first + rest)[:MAX_HEADS]:
        heads.append(f"  - {it['c']}|{names.get(it['s'], it['s'])}{'|의견' if is_opinion(it) else ''}: {ko[:120]}")
    kr = any(it.get("c") == "KR" for it in its)
    key = re.sub(r"^.*?기사 요약\(기계번역\):\s*", "", s.get("key") or "")[:220]
    return (f"[{s.get('sid') or s['id']}] {CAT.get(s.get('cat'), '기타')} · 기사 {len(s.get('items', []))}개 · {len(s.get('countries') or cs)}개 나라"
            f"{' · 새 이슈' if s.get('delta') == 'new' else ''}{'' if kr else ' · 한국 매체 없음'}\n  지금 제목: {s.get('title', '')}\n"
            + (f"  요약(기계번역): {key}\n" if key else "") + "\n".join(heads))


def buzz_block():
    out = []
    for cc in ("KR", "US", "JP"):
        d = rj(ROOT / "data" / "trends" / f"{cc}.json", {}) or {}
        g = ((d.get("src") or {}).get("google") or {}).get("items") or []
        for x in g[:4]:
            n = (x.get("news") or [{}])[0].get("t", "")
            out.append(f"  - {cc}|{x.get('kw', '')}" + (f" (관련 기사: {n[:70]})" if n else ""))
    return "\n".join(out)


PROMPT = """너는 한국어 뉴스 브리핑 편집자야. 아래 [이슈 목록]은 세계 여러 나라 매체의 기사 제목을 같은 사건끼리 묶은 것이고, 제목은 기계번역이라 어색할 수 있어.
이걸로 "{label}"을 써 줘. 읽는 사람은 아침에 5분만 읽고 세상에서 무슨 일이 있었는지 알고 싶어 해.

꼭 지킬 것
1. [이슈 목록]의 제목·요약에 **있는 내용만** 써. 네가 따로 아는 사실, 배경 지식, 숫자, 이름을 보태지 마. 모르면 쓰지 마.
2. 같은 사건을 다룬 이슈가 여러 개면 **하나로 합쳐** (sids 에 번호를 모두 넣어). 한 묶음 안에 사건과 상관없는 제목이 섞여 있으면 무시해.
3. 세계적으로 중요한 순서로 {lo}~{hi}개를 골라. 중요도 = 다룬 나라·매체 수 + 세상에 미치는 영향(전쟁·외교·경제·기술이 먼저) . 스포츠·연예·작은 사건 사고는 빼.
4. 말투는 쉬운 **해요체**("올렸어요", "전했어요"). 한자어·전문 용어는 쉬운 말로 풀어. 번역투("~에 대해", "~함에 따라")를 쓰지 마.
5. 사람·회사·나라 이름은 한국에서 흔히 쓰는 표기로 고쳐 (예: 젠슨 황, 러트닉, 튀르키예).
6. 숫자가 매체마다 다르면 "매체에 따라 ○~○"처럼 써.
7. 누가 전했는지 문장 안에 매체 이름을 넣어 ("BBC에 따르면", "닛케이는").
8. 매체 이름 뒤 〔 〕 안은 그 매체의 성향·소유 구조야. 〔관영〕·〔국영〕 매체가 전한 것은 사실처럼 쓰지 말고 "~라고 주장했어요", "~라고 전했어요"로 써. 글에는 〔 〕 표시를 넣지 마.

이슈마다 쓸 것
- sids: 합친 이슈 번호들 (대괄호 안의 번호 그대로)
- cat: war|pol|eco|tech|dis|soc|cul 중 하나
- t: 제목. 25자 안팎, 해요체 한 문장 ("~했어요"). 기계번역 제목을 베끼지 말고 무슨 일인지 바로 알게.
- one: 한두 문장 (90자 안팎). 무슨 일이 있었는지만.
- sum: 3~4문장 요약. 매체 이름을 넣어서.
- why: 2~3문장. 이 일이 왜 중요한지 — 제목들에서 읽히는 영향·파장만. 없으면 빈 글자.
- chg: [지난 브리핑]에 같은 일이 있었고 달라진 점이 있을 때만 1~2문장. 아니면 빈 글자.
- views: 나라마다 초점이 다를 때 2~5개. [{{"cc":"나라 두 글자","src":"매체 이름","t":"그 나라 매체가 무엇을 앞세웠는지 한 문장"}}]. 초점 차이가 안 보이면 빈 목록.
- op: 제목에 "|의견" 표시가 붙은 글(사설·칼럼)이 있을 때만 1~3개. [{{"cc":"나라","src":"매체 이름","t":"그 글의 주장을 한 문장으로"}}]. 서로 다른 주장을 고루. 없으면 빈 목록.
- bg: 이 일을 이해하는 데 도움이 될 배움 글을 [배움 글 목록]에서 0~4개. [{{"k":"term|hist|ch","id":"목록에 있는 번호"}}]. 목록에 없는 번호는 쓰지 마.

그리고
- lead: 오늘 전체를 3~4문장으로 묶은 첫머리. 가장 큰 일 두세 가지를 이어서.
- kr: "한국 매체 없음" 표시가 있고 여러 나라가 다룬 이슈 중 0~3개. [{{"sid":"번호","t":"짧은 제목","one":"한 문장"}}]
- buzz: [요즘 화제]에서 뉴스로서 뜻이 있는 것 0~4개. [{{"cc":"나라","t":"검색어","one":"왜 뜨는지 한 문장 (관련 기사 제목에 있는 만큼만)"}}]

답은 JSON 하나만: {{"lead":"…","items":[…],"kr":[…],"buzz":[…]}}

[지난 브리핑]
{prev}

[배움 글 목록]  (k:id=이름)
{learn}

[요즘 화제]
{buzz}

[이슈 목록]
{stories}
"""


def build_prompt(ed, by, names, li, prev, label):
    stories = "\n\n".join(story_block(s, by, names) for s in pick_stories(ed))
    learn = "\n".join(f"{k}: " + ", ".join(f"{i}={n}" for i, n in v.items()) for k, v in li.items() if v)
    pv = "\n".join(f"  - {it.get('t', '')}: {it.get('one', '')}" for it in (prev or {}).get("items", [])[:14]) or "  (없음)"
    return PROMPT.format(label=label, lo=MIN_ITEMS + 4, hi=MAX_ITEMS, prev=pv, learn=learn or "(없음)", buzz=buzz_block() or "(없음)", stories=stories)


# ───────── 무료 AI 부르기 ─────────
def http_json(url, body=None, headers=None, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "vendingForMe-briefing/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key: return None, "열쇠 없음"
    base = "https://generativelanguage.googleapis.com/v1beta"
    model = os.environ.get("GEMINI_MODEL", "").strip()
    cands = [model] if model else []
    if not cands:
        try:
            ms = http_json(f"{base}/models?key={key}&pageSize=200", timeout=30).get("models", [])
            names = [m["name"].split("/")[-1] for m in ms if "generateContent" in (m.get("supportedGenerationMethods") or [])]
            flash = [n for n in names if "flash" in n and not re.search(r"lite|image|tts|live|audio|embedding|8b|thinking|preview-0[0-9]", n)]
            ver = lambda n: [float(x) for x in re.findall(r"\d+(?:\.\d+)?", n)[:1]] or [0]
            flash.sort(key=lambda n: (ver(n), "latest" in n, "preview" not in n and "exp" not in n), reverse=True)
            cands = flash[:3]
        except Exception as e:
            return None, f"모델 목록 실패: {e}"
    err = "쓸 모델 없음"
    for m in cands + cands[:1]:   # 붐빔(503)이면 잠깐 쉬고 맨 앞 모델로 한 번 더
        try:
            r = http_json(f"{base}/models/{m}:generateContent?key={key}",
                          {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                           "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json", "maxOutputTokens": 16000}})
            txt = "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
            return (txt, "gemini:" + m), None
        except urllib.error.HTTPError as e:
            err = f"{m}: HTTP {e.code} {e.read()[:200].decode('utf-8', 'ignore')}"
            log("  Gemini 실패 →", err)
            if e.code in (429, 503): time.sleep(20)
        except Exception as e:
            err = f"{m}: {e}"; log("  Gemini 실패 →", err)
    return None, err


def groq(prompt):
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key: return None, "열쇠 없음"
    base, H = "https://api.groq.com/openai/v1", {"Authorization": "Bearer " + key}
    model = os.environ.get("GROQ_MODEL", "").strip()
    cands = [model] if model else []
    if not cands:
        try:
            ids = [m["id"] for m in http_json(base + "/models", headers=H, timeout=30).get("data", []) if m.get("active", True)]
            pref = [r"gpt-oss-120b", r"kimi", r"llama-4", r"llama-3\.3-70b", r"qwen", r"70b", r"gpt-oss"]
            for p in pref:
                cands += [i for i in ids if re.search(p, i) and i not in cands and not re.search(r"guard|whisper|tts|vision|safeguard", i)]
            cands = cands[:3]
        except Exception as e:
            return None, f"모델 목록 실패: {e}"
    err = "쓸 모델 없음"
    for m in cands:
        try:
            r = http_json(base + "/chat/completions", {"model": m, "temperature": 0.3, "response_format": {"type": "json_object"},
                                                       "messages": [{"role": "user", "content": prompt}]}, headers=H)
            return (r["choices"][0]["message"]["content"], "groq:" + m), None
        except urllib.error.HTTPError as e:
            err = f"{m}: HTTP {e.code} {e.read()[:200].decode('utf-8', 'ignore')}"; log("  Groq 실패 →", err)
        except Exception as e:
            err = f"{m}: {e}"; log("  Groq 실패 →", err)
    return None, err


# ───────── 답 검사 ─────────
def parse_json(txt):
    txt = txt.strip()
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0) if m else txt)


def clean(o, ed, li):
    sids = {s.get("sid") or s["id"] for s in ed["stories"]}
    S = lambda v, n: re.sub(r"\s+", " ", str(v or "")).strip()[:n]
    items, used = [], set()
    for it in o.get("items") or []:
        ss = [x for x in (it.get("sids") or []) if x in sids and x not in used]
        t, one = S(it.get("t"), 60), S(it.get("one"), 220)
        if not ss or not t or not one: continue
        used.update(ss)
        views = [{"cc": S(v.get("cc"), 2).upper(), "src": S(v.get("src"), 40), "t": S(v.get("t"), 200)} for v in (it.get("views") or [])[:5] if isinstance(v, dict) and re.fullmatch(r"[A-Za-z]{2}", str(v.get("cc") or "")) and v.get("t")]
        op = [{"cc": S(v.get("cc"), 2).upper(), "src": S(v.get("src"), 40), "t": S(v.get("t"), 200)} for v in (it.get("op") or [])[:3] if isinstance(v, dict) and re.fullmatch(r"[A-Za-z]{2}", str(v.get("cc") or "")) and v.get("t")]
        bg = []
        for b in (it.get("bg") or [])[:4]:
            k, i = (b or {}).get("k"), str((b or {}).get("id") or "")
            if k in li and i in li[k]: bg.append({"k": k, "id": i, "t": li[k][i]})
        items.append({"sids": ss, "cat": it.get("cat") if it.get("cat") in CAT else "etc", "t": t, "one": one, "sum": S(it.get("sum"), 520),
                      "why": S(it.get("why"), 380), **({"chg": S(it.get("chg"), 240)} if S(it.get("chg"), 240) else {}), "views": views, **({"op": op} if op else {}), "bg": bg})
    kr = [{"sid": x["sid"], "t": S(x.get("t"), 50), "one": S(x.get("one"), 120)} for x in (o.get("kr") or [])[:3] if isinstance(x, dict) and x.get("sid") in sids and x.get("t")]
    buzz = [{"cc": S(x.get("cc"), 2).upper(), "t": S(x.get("t"), 40), "one": S(x.get("one"), 120)} for x in (o.get("buzz") or [])[:4] if isinstance(x, dict) and x.get("t")]
    return {"lead": S(o.get("lead"), 420), "items": items[:MAX_ITEMS], "kr": kr, "buzz": buzz}


def main():
    dry = "--dry" in sys.argv
    ed = latest_edition()
    if not ed: log("판이 없어요"); return 0
    now = datetime.now(KST)
    slot = "am" if now.hour < 13 else "pm"
    bid = f"{now:%Y-%m-%d}_{slot}"
    label = f"{now.month}월 {now.day}일 {'아침' if slot == 'am' else '저녁'} 브리핑"
    by, (names, _lean), li = feed_items(ed["id"]), source_names(), learn_index()
    prev = rj(OUT / "latest.json")
    prompt = build_prompt(ed, by, names, li, prev, label)
    log(f"판 {ed['id']} · 이슈 {len(pick_stories(ed))}개 · AI 에게 보낼 글 {len(prompt):,}자")
    if dry:
        log(prompt[:3000]); return 0
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        log("무료 AI 열쇠(GEMINI_API_KEY · GROQ_API_KEY)가 없어요 → 브리핑을 바꾸지 않고 끝내요"); return 0
    out = None
    for name, fn in (("Gemini", gemini), ("Groq", groq)):
        for attempt in (1, 2):
            res, err = fn(prompt)
            if not res: log(f"{name}: {err}"); break
            try:
                o = clean(parse_json(res[0]), ed, li)
                if len(o["items"]) >= MIN_ITEMS and o["lead"]:
                    out = (o, res[1]); break
                log(f"{name}: 쓸 만한 이슈가 {len(o['items'])}개뿐 → 다시")
            except Exception as e:
                log(f"{name}: 답을 못 읽음 ({e}) → 다시")
        if out: break
    if not out:
        log("AI 가 브리핑을 쓰지 못했어요 → 전에 있던 브리핑을 그대로 둬요"); return 0
    o, who = out
    doc = {"id": bid, "slot": slot, "label": label, "at": now.isoformat(timespec="minutes"), "ed": ed["id"], "by": who.split(":")[0], "model": who,
           "note": "기사 제목과 요약에 있는 내용만으로 썼어요. 틀린 곳이 있을 수 있으니 중요한 일은 원문을 확인하세요.", **o}
    wj(OUT / "latest.json", doc); wj(OUT / f"{bid}.json", doc)
    wj(D / "lean.json", _lean)                                  # 매체 성향표 (화면이 매체 이름 옆에 보여 줌)
    olds = sorted(p for p in OUT.glob("20*.json"))
    for p in olds[:-30]: p.unlink()
    ix = [{"id": p.stem, "label": (rj(p, {}) or {}).get("label", p.stem)} for p in sorted(OUT.glob("20*.json"))]
    wj(OUT / "_index.json", ix)
    log(f"브리핑 저장: {bid} · 이슈 {len(o['items'])}개 · {who}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
