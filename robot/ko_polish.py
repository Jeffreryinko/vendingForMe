"""ko_polish.py — 기계번역 결과 다듬기·검사 (토큰 0). TranslateGemma·NLLB 가 같이 씀.

  from ko_polish import glossary_for, headline, nllb_fix, bad
  gl = glossary_for(text)          # 이 글에 나오는 이름의 한국어 표기 [(원어, 한국어)] — 번역기에 귀띔
  y = headline(y)                  # 제목: '~했습니다.' → '~했다' (신문 제목체)
  y = nllb_fix(y)                  # NLLB 띄어쓰기 버릇: '센터 는 우리 가' → '센터는 우리가'
  if bad(src, y, lang): ...        # 엉뚱한 번역이면 True (다른 글을 번역함·잘림·외국 문자 남음)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 자주 나오는 이름 — 번역기가 자주 틀리는 것 위주 (원어 → 한국어 표기)
STATIC = {
    "Jensen Huang": "젠슨 황", "黃仁勳": "젠슨 황", "黄仁勋": "젠슨 황", "Nvidia": "엔비디아", "NVIDIA": "엔비디아",
    "Zelensky": "젤렌스키", "Zelenskyy": "젤렌스키", "Netanyahu": "네타냐후", "Putin": "푸틴", "Xi Jinping": "시진핑", "习近平": "시진핑", "習近平": "시진핑",
    "Erdogan": "에르도안", "Erdoğan": "에르도안", "Modi": "모디", "Macron": "마크롱", "Merz": "메르츠", "Starmer": "스타머", "Takaichi": "다카이치", "高市": "다카이치",
    "Lula": "룰라", "Milei": "밀레이", "Sheinbaum": "셰인바움", "Musk": "머스크", "Altman": "올트먼", "Zuckerberg": "저커버그",
    "Zaporizhzhia": "자포리자", "Запорожск": "자포리자", "Kyiv": "키이우", "Kiev": "키이우", "Киев": "키이우", "Kharkiv": "하르키우", "Donetsk": "도네츠크",
    "Gaza": "가자", "Hamas": "하마스", "Hezbollah": "헤즈볼라", "Houthi": "후티", "Houthis": "후티",
    "OpenAI": "오픈AI", "Anthropic": "앤트로픽", "DeepSeek": "딥시크", "Kraków": "크라쿠프", "Krakow": "크라쿠프", "Tusk": "투스크",
}
# 이것이 원문에 있으면 번역에도 그 한국어가 있어야 정상 (없으면 다른 글을 번역했거나 크게 빠뜨린 것)
ANCHOR = {"Trump": "트럼프", "Iran": "이란", "Israel": "이스라엘", "Ukraine": "우크라이나", "Russia": "러시아", "China": "중국",
          "Putin": "푸틴", "Zelensky": "젤렌스키", "Netanyahu": "네타냐후", "Gaza": "가자", "Nvidia": "엔비디아", "Tesla": "테슬라",
          "Japan": "일본", "India": "인도", "Germany": "독일", "France": "프랑스", "Brazil": "브라질", "Mexico": "멕시코",
          "Biden": "바이든", "Musk": "머스크", "Apple": "애플", "Google": "구글", "Microsoft": "마이크로소프트"}

_GL = None


def _load():
    global _GL
    if _GL is not None: return _GL
    gl = dict(STATIC)
    try:   # 시사 편집장이 만든 이름 사전: 원어(o) → 한국어 이름
        m = json.loads((ROOT / "data/sisa/brief/ents.json").read_text(encoding="utf-8")).get("map", {})
        for ko, v in m.items():
            o = (v or {}).get("o") or ""
            if 3 <= len(o) <= 60 and o != ko and not re.search(r"[가-힣]", o): gl.setdefault(o, ko)
    except Exception:
        pass
    _GL = gl
    return gl


def glossary_for(text: str, n: int = 8):
    t = text or ""; tl = t.lower(); out = []
    seen = set()
    for o, ko in _load().items():
        if o.lower() in seen: continue
        if re.match(r"[A-Za-z]", o):
            tail = r"[a-zà-ÿа-я]{0,3}" if len(o) >= 5 else ""          # 폴란드어 Krakowie·독일어 Nvidias 처럼 끝이 바뀐 꼴도
            if re.search(r"(?<![A-Za-z])" + re.escape(o.lower()) + tail + r"(?![a-z])", tl): out.append((o, ko))
        elif o in t: out.append((o, ko))
        if out and out[-1][0] == o: seen.add(o.lower())
        if len(out) >= n: break
    return out


# ── 제목체 ──
_VERB_I = set("보줄높붙먹죽속녹늘끓들낮맞쌓기숨")   # '~입니다' 가 동사(보입니다=보인다)인 앞 글자


def _plain(w: str) -> str:
    if w.endswith("습니다"): return w[:-3] + "다"
    if w.endswith("입니다"):
        return w[:-3] + ("인다" if len(w) >= 4 and w[-4] in _VERB_I else "이다")
    c = w[-3]; code = ord(c) - 0xAC00
    if 0 <= code < 11172 and code % 28 == 17: return w[:-3] + chr(ord(c) - 17 + 4) + "다"   # 합니다→한다, 됩니다→된다
    return w


def headline(y: str) -> str:
    """'~했습니다.' '~합니다' → '~했다' '~한다'. 묻는 말(~까요?)과 따옴표 안은 그대로"""
    if not y: return y
    y = re.sub(r"([가-힣]+니다)(?=\.?\s*$|\.\s|[,;]\s)", lambda m: _plain(m.group(1)), y)
    y = re.sub(r"(?<=[가-힣]다)\.\s*$", "", y)
    return y.strip()


# ── NLLB 띄어쓰기 버릇 ──
_PART = r"(?:은|는|이|가|을|를|에|의|와|과|도|로|으로|에서|에게|보다|까지|부터|만|하는|하고|하다|했다|된|한|될|할)"


def nllb_fix(y: str) -> str:
    if not y: return y
    return re.sub(r"(?<=[가-힣]) (" + _PART + r")(?=[\s.,?!]|$)", r"\1", y)


# ── 엉뚱한 번역 거르기 ──
_FOREIGN = re.compile(r"[Ѐ-ӿ؀-ۿ฀-๿ऀ-ॿঀ-৿က-႟֐-׿Ͱ-Ͽ぀-ヿ]")
_HAN = re.compile(r"[一-鿿]")


def bad(src: str, y: str, lang: str = "en") -> str:
    """문제가 있으면 이유(글), 없으면 '' """
    s, y = (src or "").strip(), (y or "").strip()
    if not y: return "빈 번역"
    if len(_FOREIGN.findall(y)) > 2: return "외국 문자가 남음"
    if len(_HAN.findall(y)) > 3: return "한자가 남음"
    if not re.search(r"[가-힣]", y) and re.search(r"[A-Za-z]{4,}", s) and not re.fullmatch(r"[\x00-\x7F]+", y): return "한국어가 없음"
    cjk = lang in ("zh", "zh-tw", "zh-cn", "ja")
    r = len(y) / max(1, len(s))
    if len(s) >= 40 and (r < (0.4 if cjk else 0.16) or r > (4.5 if cjk else 2.6)): return f"길이가 이상함({r:.2f})"   # 한국어는 짧게 줄어드는 편이라 넉넉히
    for o, ko in ANCHOR.items():
        if re.search(r"(?<![A-Za-z])" + o + r"(?![a-z])", s) and ko not in y and o.lower() not in y.lower(): return f"'{o}'가 번역에 없음"
    return ""
