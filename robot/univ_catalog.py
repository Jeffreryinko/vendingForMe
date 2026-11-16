#!/usr/bin/env python3
"""univ. 화면이 쓰는 목차(univ/catalog.json)를 다시 만든다. 로봇·토큰 0.

세 교실(sisa/learn, deal/learn, gicho)의 글 파일을 크롬(화면 없이)으로 실제 화면과 똑같이 읽어
장·용어·역사 목록과 개수를 뽑는다. 교실에 장이나 용어를 더했을 때 한 번 돌리면 된다:
    python3 robot/univ_catalog.py        (크롬이 있어야 함: google-chrome 또는 chromium)
"""
import json, os, re, shutil, subprocess, sys, tempfile, threading, http.server, functools, socketserver, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOMS = [("sisa", "sisa/learn"), ("deal", "deal/learn"), ("gicho", "gicho")]
DUMP = r"""<script>
(function(){var L=window.VFM_LEARN||{},T=window.VFM_TERMS||[],C=window.VFM_TERM_CATS||[],HS=L.history||[],seen={};
HS.forEach(function(h){if(!h.virt)h.items.forEach(function(e){if(!e._k)e._k=h.id+"|"+e.t;});});
var G=L.chGroups||{},HG=L.histGroups||{};
var out={name:L.name||"",diag:(L.diag||[]).length,
 chGroups:Object.keys(G).map(function(k){return [k,G[k][0]];}),
 ch:(L.chapters||[]).map(function(c){var tm={};(c.cards||[]).forEach(function(k){(k.tm||[]).forEach(function(t){tm[t]=1;});});return {id:c.id,t:c.t,g:c.g||"",cards:(c.cards||[]).length,quiz:(c.quiz||[]).length,tm:Object.keys(tm).length};}),
 cats:C,terms:T.map(function(t){return [t.id,t.w||t.t||t.name||t.id,t.c||t.cat||""];}),
 hist:HS.filter(function(h){return !h.virt;}).map(function(h){return {id:h.id,name:h.name,flag:h.flag||"",g:h.g||"",keys:h.items.map(function(e){return e._k;}).filter(function(k){if(seen[k])return false;seen[k]=1;return true;})};}).filter(function(h){return h.keys.length;})};
var p=document.createElement("pre");p.id="univ-out";p.textContent=JSON.stringify(out);document.body.appendChild(p);})();
</script>"""

def main():
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
    if not chrome: sys.exit("크롬을 찾지 못했어요")
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=ROOT)
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    cat, made = {}, []
    try:
        for app, d in ROOMS:
            src = open(os.path.join(ROOT, d, "index.html"), encoding="utf-8").read()
            # 화면 엔진(learn.js)과 껍데기(shell.js)는 빼고 글 파일만 읽는다
            src = re.sub(r'<script src="[^"]*assets/(learn|shell)\.js[^"]*"></script>', "", src)
            src = src.replace("</body>", DUMP + "</body>") if "</body>" in src else src + DUMP
            tmp = os.path.join(ROOT, d, "_univ_probe.html"); open(tmp, "w", encoding="utf-8").write(src); made.append(tmp)
            prof = tempfile.mkdtemp()
            dom = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--user-data-dir=" + prof, "--virtual-time-budget=8000", "--dump-dom",
                                  "http://127.0.0.1:%d/%s/_univ_probe.html" % (port, d)], capture_output=True, text=True, timeout=120).stdout
            shutil.rmtree(prof, ignore_errors=True)
            m = re.search(r'<pre id="univ-out">(.*?)</pre>', dom, re.S)
            if not m: sys.exit(app + ": 목차를 읽지 못했어요")
            cat[app] = json.loads(html.unescape(m.group(1)))
            c = cat[app]; print(app, c["name"], "장", len(c["ch"]), "용어", len(c["terms"]), "역사", sum(len(h["keys"]) for h in c["hist"]), "수준확인", c["diag"])
    finally:
        for t in made:
            if os.path.exists(t): os.remove(t)
        srv.shutdown()
    # 첫 화면 카드도 같은 개수를 쓰도록 assets/univ.js 의 TOT 줄을 고쳐 쓴다 (ch 장 수, chMin 한 장 평균 분, tm 용어, ep 역사)
    tot = {a: {"ch": len(c["ch"]), "chMin": round(sum(x["cards"] * 1.3 + x["quiz"] * 0.6 for x in c["ch"]) / max(1, len(c["ch"])), 1),
               "tm": len(c["terms"]), "ep": sum(len(h["keys"]) for h in c["hist"])} for a, c in cat.items()}
    uj = os.path.join(ROOT, "assets", "univ.js")
    if os.path.exists(uj):
        js = open(uj, encoding="utf-8").read()
        js2 = re.sub(r"var TOT = \{.*?\}; /\*@totals\*/", lambda m: "var TOT = " + json.dumps(tot, separators=(",", ":")) + "; /*@totals*/", js, count=1)
        if js2 != js: open(uj, "w", encoding="utf-8").write(js2); print("assets/univ.js 개수 고침")
    print(json.dumps(tot))
    os.makedirs(os.path.join(ROOT, "univ"), exist_ok=True)
    json.dump(cat, open(os.path.join(ROOT, "univ", "catalog.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

if __name__ == "__main__":
    main()
