"""radio_run.py — 자판기 라디오: 그날 카드를 무료 음성(MeloTTS, 오픈소스·MIT)으로 읽어 소리 파일로 (토큰 0).

순서 (한 회차에 약 15~20분 분량):
  여는 말 → 시사 큰 이야기(해설 있는 것) → 시사 단신 몇 개 → 나라별 트렌드 1위들 → AI 새 기능 → 닫는 말

출력 (data/radio/)
  _index.json          {at, label, engine, items:[{id, kind, title, text, file, sec, link}]}
  <회차>/NN.mp3         조각 하나 = 카드 하나 (32kbps 모노, 1분에 약 240KB)
  최근 2회차만 남기고 지움

  python robot/radio_run.py                  # MeloTTS (기본)
  python robot/radio_run.py --engine edge    # MeloTTS 설치가 안 될 때: edge-tts (비공식, 막힐 수 있음)
  python robot/radio_run.py --dry            # 소리 없이 읽을 글만 만들어 보기
"""
from __future__ import annotations

import argparse, asyncio, json, re, shutil, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"; OUT = DATA / "radio"
KST = timezone(timedelta(hours=9))
CAT = {"war": "전쟁·안보", "pol": "정치·외교", "eco": "경제", "tech": "기술·과학", "dis": "재난·사고", "soc": "사회", "spo": "스포츠", "cul": "문화"}
COUNTRY_KO = {"KR": "한국", "US": "미국", "JP": "일본", "GB": "영국", "DE": "독일", "FR": "프랑스", "IN": "인도", "BR": "브라질", "ID": "인도네시아"}


def log(*a): print(datetime.now(KST).strftime("%H:%M:%S"), *a, flush=True)
def rj(p, d=None):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d


def clean(t, n=600):
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", str(t or ""))      # 이모지·국기 빼기
    t = re.sub(r"https?://\S+", "", t)
    t = t.replace("·", ", ").replace("…", ". ").replace("→", " ").replace("‘", "").replace("’", "").replace("“", "").replace("”", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"([.!?])\s*\.", r"\1", t)
    if len(t) <= n: return t
    cut = t[:n]; m = max(cut.rfind("요. "), cut.rfind("다. "), cut.rfind(". "))      # 문장 끝에서 자르기
    return cut[:m + 2].strip() if m > n * 0.5 else cut.rsplit(" ", 1)[0] + "."


def script():
    """읽을 조각들 [{id, kind, title, text, link}]"""
    now = datetime.now(KST)
    parts = [{"id": "open", "kind": "intro", "title": "여는 말", "link": "",
              "text": f"자판기 라디오입니다. {now.month}월 {now.day}일 {'아침' if now.hour < 12 else '저녁'} 소식을 들려드릴게요. 시사, 세계 트렌드, AI 새 소식 순서예요."}]
    # 시사
    meta = rj(DATA / "sisa/_meta.json", {}) or {}
    ed = rj(DATA / f"sisa/editions/{meta.get('edition', '')}.json", {}) or {}
    st = [s for s in ed.get("stories", []) if s.get("title") and (s.get("key") or s.get("sum"))]
    tops = sorted([s for s in st if s.get("top")], key=lambda s: s["top"])
    big = [s for s in st if not s.get("top") and s.get("kind") != "brief" and (s.get("why3") or s.get("bg"))][:4]
    briefs = [s for s in st if s.get("kind") == "brief" and s.get("delta") == "new"][:5]
    for i, s in enumerate(tops + big):
        w3 = s.get("why3") or {}
        body = f"{'첫' if i == 0 else '다음'} 소식, {CAT.get(s.get('cat'), '')}입니다. {s['title']}. {s.get('key') or s.get('sum')}"
        if w3.get("now"): body += f" 왜 중요할까요? {w3['now']}"
        if w3.get("korea") and "나오지 않" not in w3["korea"]: body += f" 한국과는, {w3['korea']}"
        parts.append({"id": "s-" + s["id"], "kind": "sisa", "title": s["title"], "text": clean(body, 900), "link": f"sisa/#issue-{s['id']}"})
    if briefs:
        parts.append({"id": "briefs", "kind": "sisa", "title": "짧은 소식", "link": "sisa/#today",
                      "text": clean("짧은 소식입니다. " + " ".join(f"{s['title']}." for s in briefs), 900)})
    # 트렌드: 나라별 구글 급상승 1위 + 이유(관련 뉴스 제목)
    tr = []
    for cc in ["KR", "US", "JP", "GB", "DE", "FR", "IN", "BR", "ID"]:
        d = rj(DATA / f"trends/{cc}.json", {}) or {}
        g = ((d.get("src") or {}).get("google") or {}).get("items") or []
        if not g: continue
        it = g[0]; kw = it.get("ko") or it.get("kw"); n = (it.get("news") or [{}])[0]
        why = n.get("ko") or (n.get("t") if cc == "KR" else "")
        tr.append(f"{COUNTRY_KO.get(cc, cc)}에서는 {kw}{'.' if not why else ', 관련 소식은 ' + why + '.'}")
    if tr:
        parts.append({"id": "trends", "kind": "trend", "title": "세계 검색어", "link": "sisa/#hot",
                      "text": clean("이번엔 나라마다 지금 가장 많이 찾는 말이에요. " + " ".join(tr), 1200)})
    # AI 새 기능 (정리된 것 먼저)
    feed = rj(DATA / "ai/feed.json", {}) or {}; feat = rj(DATA / "ai/feat.json", {}) or {}
    allp = sorted(feed.get("posts", []), key=lambda p: str(p.get("date", "")), reverse=True)
    posts = [p for p in allp if p["id"] in feat]
    by = {}
    for p in allp:
        if p["id"] not in feat: by.setdefault(p.get("sid"), []).append(p)
    while len(posts) < 5 and any(by.values()):                                      # 회사별로 번갈아
        for k in list(by):
            if by[k] and len(posts) < 5: posts.append(by[k].pop(0))
    for p in posts:
        f = feat.get(p["id"]) or {}
        body = f"AI 소식, {p.get('name', '')}. {p.get('ko') or p.get('title')}. {f.get('one') or p.get('ksum') or ''}"
        if f.get("how"): body += f" 써 보려면, {f['how']}"
        parts.append({"id": "a-" + p["id"], "kind": "ai", "title": p.get("ko") or p.get("title"), "text": clean(body, 700), "link": f"ai/#f={p['id']}"})
    parts.append({"id": "close", "kind": "intro", "title": "닫는 말", "link": "", "text": "오늘 자판기 라디오는 여기까지예요. 자세한 내용은 자판기 앱에서 카드로 보세요. 들어 주셔서 고맙습니다."})
    return parts


# ── 음성 엔진 ──
class Melo:
    name = "MeloTTS (오픈소스, MIT)"
    def __init__(self):
        from melo.api import TTS
        self.m = TTS(language="KR", device="cpu")
        self.spk = self.m.hps.data.spk2id["KR"]
    def say(self, text, wav):
        self.m.tts_to_file(text, self.spk, str(wav), speed=1.05, quiet=True)


class Edge:
    name = "edge-tts (마이크로소프트 온라인 음성, 비공식)"
    def say(self, text, wav):
        import edge_tts
        mp = str(wav).replace(".wav", ".edge.mp3")
        asyncio.run(edge_tts.Communicate(text, "ko-KR-SunHiNeural", rate="+5%").save(mp))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp, str(wav)], check=True); Path(mp).unlink()


def to_mp3(wav, mp3):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-ar", "22050", "-b:a", "32k", str(mp3)], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(mp3)], capture_output=True, text=True).stdout.strip()
    return round(float(out or 0))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--engine", default="melo"); ap.add_argument("--dry", action="store_true"); a = ap.parse_args()
    parts = script()
    log(f"조각 {len(parts)}개 · 글자 {sum(len(p['text']) for p in parts):,}")
    if a.dry:
        for p in parts: print(f"[{p['kind']}] {p['title']}\n  {p['text'][:200]}")
        return
    t0 = time.time()
    try: eng = Melo() if a.engine == "melo" else Edge()
    except Exception as e:
        log(f"MeloTTS 준비 실패 → edge-tts 로: {e}"); eng = Edge()
    now = datetime.now(KST); slot = now.strftime("%Y%m%d_%H"); d = OUT / slot
    d.mkdir(parents=True, exist_ok=True); tmp = OUT / "_tmp"; tmp.mkdir(exist_ok=True)
    items = []
    for i, p in enumerate(parts):
        wav, mp3 = tmp / f"{i:02d}.wav", d / f"{i:02d}.mp3"
        try:
            eng.say(p["text"], wav); sec = to_mp3(wav, mp3)
        except Exception as e:
            log(f"실패 {p['id']}: {e}"); continue
        items.append({**p, "file": f"{slot}/{i:02d}.mp3", "sec": sec})
        log(f"{i:02d} {p['title'][:30]} · {sec}초")
    shutil.rmtree(tmp, ignore_errors=True)
    if not items: raise SystemExit("소리를 하나도 못 만들었어요")
    label = f"{now.month}월 {now.day}일 {'아침' if now.hour < 12 else '저녁'}판"
    (OUT / "_index.json").write_text(json.dumps({"at": now.isoformat(timespec="seconds"), "label": label, "engine": eng.name, "slot": slot,
                                                  "sec": sum(x["sec"] for x in items), "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    keep = sorted(x for x in OUT.iterdir() if x.is_dir() and re.match(r"\d{8}_\d{2}$", x.name))[-2:]
    for x in OUT.iterdir():
        if x.is_dir() and re.match(r"\d{8}_\d{2}$", x.name) and x not in keep: shutil.rmtree(x)
    log(f"끝: {len(items)}조각 · {sum(x['sec'] for x in items) // 60}분 · {round(time.time() - t0)}초 걸림 · {eng.name}")


if __name__ == "__main__":
    main()
