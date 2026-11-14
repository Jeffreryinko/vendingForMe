"""learn_deep.py — 배움 코스 카드를 '5배 깊이'로: 카드마다 긴 글(long) 3~5갈래를 Claude(API)가 써요.

  python robot/learn_deep.py gicho          # 기초 교실 (gicho/course*.js)
  python robot/learn_deep.py gicho --dry

· 코스 파일을 node 로 읽어 장·카드를 꺼냄 → 이미 긴 글이 있는 카드는 건너뜀.
· 결과: data/<앱>/deep_long.json  { at, patch: { "장id|카드 제목": { long: [[소제목, 본문], …] } } }
  → 화면(gicho/index.html)이 불러와 VFM_DEEP_ADD.course({patch}) 로 붙이고 'vfm-long' 신호로 다시 그림.
· 한 번에 카드 4장, 4개 동시에. 돈은 briefing.claude() 한도를 따름 (LEARN_FAST=1 이면 하루 몫 무시).
"""
from __future__ import annotations

import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import briefing as BR

ROOT = Path(__file__).resolve().parent.parent
APPS = {   # 앱: (배움 화면 index.html — 거기 적힌 스크립트를 순서대로 읽어 장·카드를 꺼냄, 이름)
  "gicho": ("gicho/index.html", "기초 교실 — 과학·심리학·철학을 처음부터"),
  "ai": ("ai/learn/index.html", "AI 교실 — 인공지능을 기초부터 최신까지"),
  "sisa": ("sisa/learn/index.html", "세상 읽기 교실 — 뉴스 뒤의 세계"),
  "deal": ("deal/learn/index.html", "딜 교실 — 기업 인수·투자의 세계"),
}
PER = 4

PROMPT = """너는 '{name}'의 수석 필자예요. 아래 코스 카드마다, 카드 본문을 읽은 사람이 '아, 이제 진짜 알겠다'가 되도록 깊이 읽기 글을 써요.
독자는 전공자가 아니고 집중이 쉽게 흩어지는 어른이에요. 쉬운 해요체, 짧은 문장, 구체적인 장면과 숫자.

카드마다 long = 소제목과 본문 쌍 4개:
1) 일상 장면으로 — 생활 속 장면 하나로 개념을 보여 주기
2) 원리를 차근차근 — 왜 그런지 단계별로 (필요하면 간단한 계산이나 비유)
3) 처음 알아낸 사람들 — 실제 인물·연도·실험 이야기 (확실한 사실만, 전설이면 '전설'이라고)
4) 흔한 오해와 한 걸음 더 — 사람들이 자주 틀리는 점, 그리고 다음에 이어 볼 질문
소제목은 그 카드에 맞게 재밌게 바꿔도 돼요. 각 본문 350~550자, 문단은 \\n 으로 나눔. 카드 본문을 그대로 되풀이하지 말고 넓히고 깊게.
사실(이름·연도·숫자)은 확실한 것만. 모르면 빼요.

JSON 하나만: {{"cards":[{{"k":"장id|카드 제목(그대로)","long":[["소제목","본문"],…]}}]}}

카드:
{items}"""


def dump(page):
    import re as _re
    base = (ROOT / page).parent
    srcs = [m for m in _re.findall(r'<script src="([^"]+)"', (ROOT / page).read_text(encoding="utf-8")) if "assets/" not in m]
    files = [str((base / m.split("?")[0]).resolve()) for m in srcs]
    stub = ("window.VFM_DEEP_ADD={course(o){const CH=(window.VFM_LEARN||{}).chapters||[];for(const k in (o.patch||{})){const i=k.indexOf('|'),c=k.slice(0,i),h=k.slice(i+1);"
            "const ch=CH.find(x=>x.id===c),cd=ch&&ch.cards.find(x=>x.h===h);if(cd)Object.assign(cd,o.patch[k])}"
            "for(const c in (o.cards||{})){const ch=CH.find(x=>x.id===c);if(ch)for(const k of o.cards[c])if(!ch.cards.some(x=>x.h===k.h))ch.cards.push(k)}"
            "for(const ch of (o.chapters||[]))if(!CH.some(x=>x.id===ch.id))CH.push(ch)},hist(){},terms(){},tags(){},build(){}};")
    js = ("global.window=global;global.document={addEventListener(){},querySelector(){return null}};global.addEventListener=()=>{};const fs=require('fs');" + stub +
          "".join(f"try{{if(!{json.dumps(f)}.endsWith('/deep.js'))eval(fs.readFileSync({json.dumps(f)},'utf8'))}}catch(e){{}}" for f in files) +
          "const L=window.VFM_LEARN||{};process.stdout.write(JSON.stringify((L.chapters||[]).map(c=>({id:c.id,t:c.t,cards:c.cards.map(k=>({h:k.h,b:k.b,ex:k.ex||'',pt:k.pt||[],long:!!k.long}))}))))")
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


def main():
    app = (sys.argv[1:] or ["gicho"])[0]; dry = "--dry" in sys.argv
    page, name = APPS[app]
    out = ROOT / f"data/{app}/deep_long.json"
    doc = BR.rj(out, None) or {"patch": {}}
    chs = dump(page)
    todo = [(f"{c['id']}|{k['h']}", c, k) for c in chs for k in c["cards"] if not k["long"] and f"{c['id']}|{k['h']}" not in doc["patch"]]
    n = int(os.environ.get("LEARN_N") or 400)
    BR.log(f"{app}: 카드 {sum(len(c['cards']) for c in chs)}장 · 남은 것 {len(todo)}장 · 이번에 {min(n, len(todo))}장")
    todo = todo[:n]
    if not todo: return 0
    if os.environ.get("LEARN_FAST"): os.environ["CLAUDE_NO_DAILY"] = "1"

    def prompt_of(batch):
        return PROMPT.format(name=name, items="\n\n".join(
            f"■ k={key}\n장: {c['t']}\n카드 제목: {k['h']}\n카드 본문: {k['b']}" + (f"\n예: {k['ex']}" if k['ex'] else "") + (f"\n기억할 것: {' / '.join(k['pt'])}" if k['pt'] else "")
            for key, c, k in batch))
    batches = [todo[i:i + PER] for i in range(0, len(todo), PER)]
    if dry: p = prompt_of(batches[0]); BR.log(p[:2500]); BR.log(f"… {len(p):,}자 · 묶음 {len(batches)}개"); return 0
    if not os.environ.get("ANTHROPIC_API_KEY"): BR.log("Claude 열쇠 없음"); return 0

    def one(b): return BR.claude(prompt_of(b), os.environ.get("LEARN_MODEL") or "claude-sonnet-5-5", 16000), b
    got = 0
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(one, b) for b in batches]
        for f in as_completed(futs):
            (res, err), b = f.result()
            if not res: BR.log(f"Claude: {err}"); continue
            keys = {x[0] for x in b}
            try:
                for it in BR.parse_json(res[0]).get("cards") or []:
                    lg = [[str(s[0])[:40], str(s[1])[:1200]] for s in (it.get("long") or []) if isinstance(s, list) and len(s) == 2 and len(str(s[1])) > 120]
                    if it.get("k") in keys and len(lg) >= 3: doc["patch"][it["k"]] = {"long": lg}; got += 1
            except Exception as e:
                BR.log(f"답을 못 읽음 ({e})")
            doc["at"] = datetime.now(BR.KST).isoformat(timespec="minutes")
            out.parent.mkdir(parents=True, exist_ok=True); BR.wj(out, doc)
    BR.log(f"{app}: 새로 {got}장 · 모두 {len(doc['patch'])}장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
