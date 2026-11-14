#!/usr/bin/env python3
"""위키백과 첫머리 가져오기 — 배움 글을 쓸 때 숫자·날짜·이름을 대조하는 도구.
   python robot/wikifact.py [-n 글자수] "en:Cuban Missile Crisis" "ko:6월 항쟁" …
   (천천히 한 개씩 부름. 글을 베끼는 용도가 아니라 사실 확인용)"""
import json, sys, time, urllib.parse, urllib.request
UA = "vendingForMe-learn/1.0 (https://github.com/Jeffreryinko/vendingForMe; fact-check)"
def get(key, n):
    lang, title = key.split(":", 1) if ":" in key[:4] else ("en", key)
    u = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&redirects=1&format=json&titles=" + urllib.parse.quote(title.replace("_", " "))
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=20) as r:
                p = list(json.loads(r.read())["query"]["pages"].values())[0]
                return (p.get("extract") or "(없음)")[:n]
        except Exception as e:
            err = str(e); time.sleep(4 * (k + 1))
    return "(실패: " + err + ")"
if __name__ == "__main__":
    a = sys.argv[1:]; n = 1100
    if a and a[0] == "-n": n = int(a[1]); a = a[2:]
    for k in a:
        print("##", k); print(get(k, n).replace("\n", " ")); print(); time.sleep(2.5)
