"""번역기: DeepL(무료 50만 자/월) 우선 → 남은 건 Google Cloud Translation(무료 50만 자/월).

글자 예산(budget)을 넘기면 번역하지 않고 '번역 대기'로 남깁니다. 화면에서는 원문 제목과
'Google 번역으로 원문 보기' 링크가 대신 표시됩니다.
"""
from __future__ import annotations

import html
import os
import time

import requests

# DeepL 원문 언어 코드 (zh 는 간체·번체 모두 ZH 로 처리됨)
DEEPL_SRC = {"en": "EN", "zh": "ZH", "es": "ES", "ar": "AR", "id": "ID", "pt": "PT",
             "fr": "FR", "ja": "JA", "ru": "RU", "de": "DE", "tr": "TR", "it": "IT", "pl": "PL", "nl": "NL"}


class Translator:
    def __init__(self, deepl_key=None, google_key=None, deepl_budget=0, google_budget=0):
        self.deepl_key = deepl_key
        self.google_key = google_key
        self.deepl_left = deepl_budget if deepl_key else 0
        self.google_left = google_budget if google_key else 0
        self.used = {"deepl": 0, "google": 0}
        self.errors = []
        self.deepl_url = ("https://api-free.deepl.com/v2/translate" if (deepl_key or "").endswith(":fx")
                          else "https://api.deepl.com/v2/translate")

    @classmethod
    def from_env(cls, deepl_budget, google_budget):
        return cls(os.environ.get("DEEPL_API_KEY"), os.environ.get("GOOGLE_TRANSLATE_API_KEY"),
                   deepl_budget, google_budget)

    @property
    def available(self):
        return self.deepl_left + self.google_left

    # ── 내부 호출 ──
    def _deepl(self, texts, lang):
        out = []
        for i in range(0, len(texts), 50):                    # DeepL: 요청당 최대 50개
            part = texts[i:i + 50]
            body = {"text": part, "target_lang": "KO"}
            if lang in DEEPL_SRC:
                body["source_lang"] = DEEPL_SRC[lang]
            for attempt in range(3):
                r = requests.post(self.deepl_url, json=body, timeout=60,
                                  headers={"Authorization": f"DeepL-Auth-Key {self.deepl_key}"})
                if r.status_code in (429, 503) and attempt < 2:
                    time.sleep(5 * (attempt + 1)); continue
                break
            if r.status_code == 456:                           # 월 한도 초과
                self.deepl_left = 0
                raise RuntimeError("DeepL 월 한도 초과")
            r.raise_for_status()
            out += [t["text"] for t in r.json()["translations"]]
        return out

    def _google(self, texts, lang):
        out = []
        for i in range(0, len(texts), 100):                   # Google: 요청당 최대 128개
            part = texts[i:i + 100]
            body = {"q": part, "target": "ko", "format": "text"}
            if lang in DEEPL_SRC and lang != "zh":            # 중국어는 간/번체 자동 감지
                body["source"] = lang
            r = requests.post("https://translation.googleapis.com/language/translate/v2",
                              params={"key": self.google_key}, timeout=60, json=body)
            r.raise_for_status()
            out += [html.unescape(t["translatedText"]) for t in r.json()["data"]["translations"]]
        return out

    # ── 공개 함수 ──
    def translate(self, texts: list[str], lang: str):
        """texts 를 한국어로. 예산이 모자라면 None 반환. 반환: (번역 리스트, 사용한 엔진)"""
        texts = [t or "" for t in texts]
        need = sum(len(t) for t in texts)
        if need == 0:
            return [""] * len(texts), None
        if os.environ.get("FAKE_TRANSLATE"):                  # 테스트 전용: 실제 API 호출 없이 흐름만 확인
            self.used["deepl"] += need
            return [f"[번역]{t}" for t in texts], "test"
        # DeepL 지원 목록에 없는 언어(힌디어·벵골어 등)는 바로 Google 로
        if self.deepl_left >= need and lang in DEEPL_SRC:
            try:
                res = self._deepl(texts, lang)
                self.deepl_left -= need; self.used["deepl"] += need
                return res, "deepl"
            except Exception as e:                            # DeepL 실패 시 Google 로 넘김
                self.errors.append(f"deepl/{lang}: {str(e)[:120]}")
        if self.google_left >= need:
            try:
                res = self._google(texts, lang)
                self.google_left -= need; self.used["google"] += need
                return res, "google"
            except Exception as e:
                self.errors.append(f"google/{lang}: {str(e)[:120]}")
        return None, None


def deepl_month_usage(key):
    """DeepL 이 직접 알려주는 이번 달 사용량 (정확). 실패하면 None."""
    if not key:
        return None
    base = "https://api-free.deepl.com" if key.endswith(":fx") else "https://api.deepl.com"
    try:
        r = requests.get(f"{base}/v2/usage", headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=20)
        r.raise_for_status()
        j = r.json()
        return j["character_count"], j["character_limit"]
    except Exception:
        return None
