"""사용: 저장소 맨 위에서  python robot/tests/sisa_one_edition.py <이전판> <새판>   (예: 2026-11-10_h12 2026-11-10_h15)
실제 로봇 코드(hourly.cmd_build → sisa_edit)로 한 판을 다시 만들어 봄. 저장소 자료를 임시 폴더에 복사해서 씀 (저장소는 안 바뀜)."""
import json, glob, os, shutil, sys, tempfile, collections
from pathlib import Path
prev, ed = sys.argv[1], sys.argv[2]
T = tempfile.mkdtemp(prefix="vfm-integ-")
os.environ["WORK"] = T + "/work"; os.environ["SISA_EDIT_NO_NET"] = "1"; os.environ["SISA_EDIT_MINUTES"] = "0"
sys.path.insert(0, "robot"); sys.path.insert(0, "robot/crawler"); sys.path.insert(0, "robot/pipeline"); sys.path.insert(0, "robot/builder")
import hourly, build_edition
from cluster import build_stories
seed = hourly.SEED
shutil.copy(f"data/sisa/editions/{prev}.json", seed / f"editions__{prev}.json")
for e in (prev, ed):
    for f in glob.glob(f"data/sisa/feed/{e}__*.json"):
        d = json.load(open(f)); lang = f.split("__")[1][:-5]
        if e == ed: d["items"] = [x for x in d["items"] if not x.get("carried")]
        (seed / f"feed__{e}__{lang}.json").write_text(json.dumps(d, ensure_ascii=False))
def fake_run(*a):                      # build_edition 의 'build' 대신: 저장소의 그 판 피드로 낱말 묶음만 다시 만듦
    items = hourly.load_items(ed)
    raw = [{"id": i["id"], "kind": i["k"], "title_ko": i.get("ko") or (i["t"] if i["_lang"] == "ko" else ""), "published_at": i.get("p"), "first_seen_at": i.get("p") or "",
            "source_id": i["s"], "lang": i["_lang"], "country": i["c"]} for i in items.values()]
    st = [{"id": f"s{k+1}", "label": s["label"], "kw": s["keywords"], "items": s["item_ids"], "langs": s["langs"], "countries": s["countries"], "method": "keyword-v1"} for k, s in enumerate(build_stories(raw, ed[:10]))]
    E = json.load(open(f"data/sisa/editions/{ed}.json")); E["stories"] = st
    (seed / f"editions__{ed}.json").write_text(json.dumps(E, ensure_ascii=False))
hourly.run = fake_run; build_edition.og_image = lambda u: ""; build_edition.OG_CACHE = Path(T) / "_og.json"      # 저장소의 사진 기억 파일을 건드리지 않게
hourly.cmd_build(ed, prev, "", "시험판")
# 로봇 편집장: 임시 data 폴더에서
D = T + "/data/sisa"; os.makedirs(D + "/editions"); os.makedirs(D + "/feed"); os.makedirs(D + "/brief")
shutil.copy(seed / f"editions__{ed}.json", f"{D}/editions/{ed}.json")
for f in seed.glob(f"feed__{ed}__*.json"): shutil.copy(f, f"{D}/feed/{ed}__{f.stem.split('__')[2]}.json")
shutil.copy("data/sisa/brief/ents.json", D + "/brief/ents.json")
if os.path.exists("data/sisa/brief/_wiki.json"): shutil.copy("data/sisa/brief/_wiki.json", D + "/brief/_wiki.json")     # 위키백과 첫 문장 기억 (네트워크 없이 배경 설명 시험)
shutil.copy("data/sisa/editions/_index.json", D + "/editions/_index.json")
if os.environ.get("SISA_TEST_WIKI"): shutil.copy(os.environ["SISA_TEST_WIKI"], D + "/brief/_wikinews.json")   # 위키백과 요즘 화제 시험용 (네트워크 없이)          # '이어진 이야기'용 지난 판
for e in json.load(open("data/sisa/editions/_index.json"))[-20:]:
    if e["id"] != ed and os.path.exists(f"data/sisa/editions/{e['id']}.json"): shutil.copy(f"data/sisa/editions/{e['id']}.json", f"{D}/editions/{e['id']}.json")
import sisa_edit
from pathlib import Path
sisa_edit.DATA = Path(D)
class NoKo:
    def __init__(self, *a): pass
    def many(self, pairs, **k): return [t if l == "ko" else None for t, l in pairs]    # 한국어 글은 그대로 (실제 번역기와 같음), 외국어는 번역 안 함
    def save(self): pass
sisa_edit.Ko = NoKo
sys.argv = ["sisa_edit", ed]; sisa_edit.main()
E = json.load(open(f"{D}/editions/{ed}.json")); O = json.load(open(f"data/sisa/editions/{ed}.json"))
items = hourly.load_items(ed)
import fresh as F
now = F.now_of(ed)
def show(name, E):
    st = E["stories"]; main = [s for s in st if s.get("kind") != "brief"]
    big = max(len(s["items"]) for s in st)
    def newest(s):
        a = [F.age_h(items[i], now) for i in s["items"] if i in items]; return round(min(a)) if a else None
    stale = sum(1 for s in main if (newest(s) is None or newest(s) > 48))
    print(f"\n── {name}: 이슈 {len(main)} · 단신 {len(st) - len(main)} · 가장 큰 이슈 글 {big}개 · 48시간 넘게 새 글 없는 이슈 {stale}개 · 분야 {dict(collections.Counter(s.get('cat') for s in main).most_common(5))}")
    for s in sorted([s for s in st if s.get("top")], key=lambda s: s["top"]):
        print(f"   {s['top']}. [{s.get('life', '-'):4}] 글 {len(s['items']):4} · 새 글 {newest(s)}시간 전 | {s['title'][:52]}")
show("지금 사이트에 있는 판", O); show("새 규칙으로 만든 판", E)
print("\n내려간 이슈", len(E.get("ended", [])), [e["title"][:30] for e in E.get("ended", []) if e.get("kind") != "brief"][:12])
# 읽을거리 칸 보기
OUT = os.environ.get("SISA_TEST_OUT")
if OUT: shutil.copy(f"{D}/editions/{ed}.json", OUT)
ms = [s for s in E["stories"] if s.get("kind") != "brief"]
print(f"\n고정 번호 있는 이슈 {sum(1 for s in E['stories'] if s.get('sid'))}/{len(E['stories'])} · 겹친 번호 {len(E['stories']) - len({s.get('sid') for s in E['stories']})}")
for s in ms[:8]:
    print(f"\n▶ {s['title'][:60]}  (sid {s.get('sid')}, 사진 {'있음' if s.get('ph') else '지도'})")
    for x in s.get("lines", []): print("   지금까지:", x["t"][:90])
    for x in s.get("nums", []): print("   숫자:", x["w"], " / ".join(f"{v['v']}({v['s']})" for v in x["vals"]), "← 출처마다 다름" if x["diff"] else "")
    for x in s.get("quotes", []): print("   말:", x.get("who") or "?", "“" + x["q"][:60] + "”", f"({x['s']})")
    for x in s.get("bg", []): print("   알아야 할 것:", x[:110])
    if s.get("terms"): print("   용어:", " / ".join(f"{x['t']}={x['d'][:20]}" for x in s["terms"]))
    if s.get("wk"): print("   위키:", s["wk"]["t"][:80], s["wk"]["hit"])
    for x in s.get("rel", []): print("   이어진:", "지금판" if x["cur"] else x.get("label"), x["t"][:50])
dl = E.get("daily") or {}
print(f"\n하루 정리판 {dl.get('date')} · 큰 이슈 {len(dl.get('stories', []))} · 단신 {len(dl.get('briefs', []))}")
for x in dl.get("stories", []): print("   ", x["cat"], x["title"][:50], "(위키)" if x.get("wk") else "")
print("분야", dict(collections.Counter(s.get("cat") for s in E["stories"]).most_common()))
shutil.rmtree(T)
