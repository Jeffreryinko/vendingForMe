"""nllb_multi.py — 여러 언어 → 한국어 무료 기계번역 (토큰 0). 먼저 구글 TranslateGemma(tgemma.py, 시간 예산 안), 남으면 NLLB-200 600M.
AI·이야기 로봇이 쓰는 영어 전용 번역기를 여러 언어로 넓힌 것. 같은 모델 폴더(/tmp/nllb-600m-ct2)를 함께 씀.

  from nllb_multi import Ko
  ko = Ko(mem_path)               # 번역 기억 파일(같은 글은 다시 안 함)
  out = ko.many([(text, "ja"), (text2, "de")], deadline=time.time()+600)
  ko.save()
라이브러리(ctranslate2·transformers)가 없으면 번역 없이 None 을 돌려줌 (화면은 원문으로).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

MODEL_DIR = Path(os.environ.get("NLLB_CT2_DIR", "/tmp/nllb-600m-ct2"))
HF_MODEL = "facebook/nllb-200-distilled-600M"
CODE = {"en": "eng_Latn", "ja": "jpn_Jpan", "zh": "zho_Hans", "zh-tw": "zho_Hant", "es": "spa_Latn", "fr": "fra_Latn",
        "de": "deu_Latn", "ru": "rus_Cyrl", "ar": "arb_Arab", "pt": "por_Latn", "id": "ind_Latn", "hi": "hin_Deva",
        "bn": "ben_Beng", "tr": "tur_Latn", "vi": "vie_Latn", "th": "tha_Thai", "it": "ita_Latn", "pl": "pol_Latn",
        "nl": "nld_Latn", "uk": "ukr_Cyrl", "fa": "pes_Arab", "he": "heb_Hebr"}
SPLIT = re.compile(r"(?<=[.!?。！？])\s*")


def hid(t, lang):
    return hashlib.md5((lang + "|" + t).encode()).hexdigest()[:16]


class Ko:
    def __init__(self, mem_path: Path | None = None):
        self.mem_path = mem_path
        try: self.mem = json.loads(Path(mem_path).read_text(encoding="utf-8")) if mem_path else {}
        except Exception: self.mem = {}
        self._tr = None; self._tok = None; self.ok = None; self.used = set()

    def _load(self):
        if self.ok is not None: return self.ok
        try:
            import ctranslate2, transformers
        except Exception as e:
            print(f"번역 라이브러리 없음 → 기계번역 건너뜀 ({e})", flush=True); self.ok = False; return False
        if not (MODEL_DIR / "model.bin").exists():
            print("번역 모델 변환 중 (처음 한 번)…", flush=True)
            import subprocess
            subprocess.run(["ct2-transformers-converter", "--model", HF_MODEL, "--output_dir", str(MODEL_DIR), "--quantization", "int8", "--force"], check=True)
        self._tok = transformers.AutoTokenizer.from_pretrained(HF_MODEL)
        self._tr = ctranslate2.Translator(str(MODEL_DIR), device="cpu", compute_type="int8", inter_threads=1, intra_threads=os.cpu_count() or 2)
        self.ok = True; return True

    def _run(self, sents, lang):
        tok, tr = self._tok, self._tr
        tok.src_lang = CODE.get(lang, "eng_Latn")
        tgt = tok.convert_ids_to_tokens(tok.convert_tokens_to_ids(["kor_Hang"]))
        res = [""] * len(sents)
        order = sorted(range(len(sents)), key=lambda k: len(sents[k]))
        for b in range(0, len(order), 24):
            idxs = order[b:b + 24]
            toks = [tok.convert_ids_to_tokens(tok.encode(sents[k][:600])) for k in idxs]
            outs = tr.translate_batch(toks, target_prefix=[tgt] * len(toks), beam_size=2, max_decoding_length=300)
            for k, o in zip(idxs, outs):
                hyp = o.hypotheses[0][1:] if o.hypotheses[0][:1] == tgt else o.hypotheses[0]
                res[k] = tok.decode(tok.convert_tokens_to_ids(hyp), skip_special_tokens=True).replace("⁇", "").strip()
        return res

    def many(self, pairs, deadline=None):
        """pairs: [(글, 언어)] → [한국어 또는 None]. 한국어 글은 그대로."""
        out = [None] * len(pairs); need = {}
        for i, (t, lang) in enumerate(pairs):
            t = (t or "").strip()
            if not t: continue
            if lang == "ko": out[i] = t; continue
            k = hid(t, lang)
            if k in self.mem: out[i] = self.mem[k]; self.used.add(k)
            else: need.setdefault(lang, []).append(i)
        # 1) 구글 TranslateGemma (시간 예산 안에서, 글 통째로 — 문맥이 살아 더 자연스러움)
        if need:
            try:
                from tgemma import TG
                tg = TG.get()
            except Exception:
                tg = None
            if tg is not None:
                for lang in list(need):
                    rest = []
                    for i in need[lang]:
                        y = tg.tr(pairs[i][0], lang, "ko", deadline) if tg.ok() else None
                        if y:
                            out[i] = y; k = hid(pairs[i][0].strip(), lang); self.mem[k] = y; self.used.add(k)
                        else:
                            rest.append(i)
                    if rest: need[lang] = rest
                    else: del need[lang]
        # 2) 남은 것은 예전 NLLB
        if not need or not self._load(): return out
        for lang, idxs in need.items():
            if deadline and time.time() > deadline: print("번역 시간 한도 — 나머지는 다음에", flush=True); break
            sents, owner = [], []
            for i in idxs:
                parts = [s.strip() for s in SPLIT.split(pairs[i][0]) if s.strip()] or [pairs[i][0]]
                for s in parts[:4]: sents.append(s); owner.append(i)
            res = self._run(sents, lang); got = {}
            for k, r in enumerate(res): got.setdefault(owner[k], []).append(r)
            for i, parts in got.items():
                t = " ".join(p for p in parts if p).strip()
                if t:
                    out[i] = t; k = hid(pairs[i][0].strip(), lang); self.mem[k] = t; self.used.add(k)
        return out

    def save(self, keep=6000):
        if not self.mem_path: return
        m = self.mem
        if len(m) > keep:   # 이번에 쓴 것 먼저 남기고, 나머지는 최근 것부터
            m = {k: v for k, v in m.items() if k in self.used} | dict(list(m.items())[-(keep - len(self.used)):])
        Path(self.mem_path).write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
