# 이름 사전 사진 붙이기 — 위키백과/커먼즈의 '자유 이용' 사진만, 50개씩 묶어서 천천히 요청 (토큰 0)
import json,sys,time,re,urllib.parse,urllib.request
UA={"User-Agent":"sisa-vending-photo-fetch/1.0 (personal hobby project; non-commercial; low volume)"}
def api(host,params):
    url=f"https://{host}/w/api.php?"+urllib.parse.urlencode(dict(params,format="json",maxlag=5))
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=25))
        except urllib.error.HTTPError as e:
            if e.code in (429,503): time.sleep(20*(i+1)); continue
            return None
        except Exception: time.sleep(3)
    return None
def batch(host,titles):
    """titles -> {입력제목: {url,file,page}} (자유 사진 있는 문서만, 동음이의 문서 제외)"""
    res={}
    for i in range(0,len(titles),50):
        part=titles[i:i+50]
        r=api(host,{"action":"query","prop":"pageimages|pageprops","ppprop":"disambiguation","piprop":"thumbnail|name","pithumbsize":320,"pilicense":"free","redirects":1,"titles":"|".join(part)})
        time.sleep(2)
        if not r: continue
        q=r.get("query",{}); back={}
        for x in q.get("normalized",[]): back[x["to"]]=x["from"]
        red={x["to"]:x["from"] for x in q.get("redirects",[])}
        for p in q.get("pages",{}).values():
            if "missing" in p or "pageprops" in p: continue
            th=p.get("thumbnail"); nm=p.get("pageimage")
            if not(th and nm): continue
            t=p["title"]; src=red.get(t,t); src=back.get(src,src)
            res[src]={"url":th["source"],"file":nm,"page":t}
    return res
def credits(files):
    out={}
    for i in range(0,len(files),50):
        part=files[i:i+50]
        r=api("commons.wikimedia.org",{"action":"query","prop":"imageinfo","iiprop":"extmetadata","titles":"|".join("File:"+f for f in part)})
        time.sleep(2)
        if not r: continue
        for p in r.get("query",{}).get("pages",{}).values():
            ii=(p.get("imageinfo") or [{}])[0].get("extmetadata",{})
            a=re.sub(r"<[^>]+>","",ii.get("Artist",{}).get("value","")).strip()
            l=ii.get("LicenseShortName",{}).get("value","")
            out[p["title"].replace("File:","").replace(" ","_")]=((a[:40]+" · ") if a else "")+l
    return out
def lat(x): return bool(x) and all(ord(c)<0x250 for c in x)
if __name__=="__main__":
    # 사용법: python3 photos.py brief_ents.json 새사진.json [기존 entpics map.json]
    # 결과: {이름:{u:사진주소, c:작가·라이선스, p:위키문서제목, h:en|ko}} — 새로 찾은 것만. (토큰 0, 사진 파일은 저장 안 함)
    m=json.load(open(sys.argv[1])); m=m.get("map",m)
    have=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
    have=have.get("map",have)
    want={k:v for k,v in m.items() if v.get("t") in("person","party","org","place") and k not in have}
    en=batch("en.wikipedia.org",[v["o"] for v in want.values() if v.get("o") and lat(v["o"])])
    got={}
    for k,v in want.items():
        if v.get("o") in en: got[k]=("en",en[v["o"]])
    rest=[k for k,v in want.items() if k not in got and not (v["t"]=="person" and lat(v.get("o")))]   # 영문 이름이 있는 사람은 영문판에서 못 찾으면 동명이인 위험 → 건너뜀
    ko=batch("ko.wikipedia.org",rest)
    for k in rest:
        if k in ko: got[k]=("ko",ko[k])
    cr=credits(sorted({g["file"] for _,g in got.values()}))
    out={k:{"u":g["url"].split("?")[0],"c":re.sub(r"\s+"," ",cr.get(g["file"].replace(" ","_"),"").replace("&amp;","&")).split(" File:")[0][:60],"p":g["page"],"h":h} for k,(h,g) in got.items()}
    json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False)
    print(len(out),"/",len(want))
