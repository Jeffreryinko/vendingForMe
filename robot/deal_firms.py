"""deal_firms.py — '딜' 앱 '주요 투자사' (토큰 0). deal_run.py 가 매 실행 끝에 부름.

  FIRMS 표(이름·종류·나라·찾을 낱말) → 위키데이터·위키백과에서 소개·설립·본사·운용자산·홈페이지를 받고(30일마다),
  쌓인 거래 뉴스(최근 90일)·미국 Form D 펀드 신고에서 그 투자사가 나온 것을 모아 붙인다.
  소개·숫자는 위키에서 온 것만 씀 (표에는 이름·종류·나라만 적음 — 사람이 지어낸 숫자 없음).

출력: data/deal/firms.json (목록) · data/deal/firms/<id>.json (자세히)
투자사 더하기: FIRMS 에 한 줄 (id, 한국어, 영어, 종류, 나라, [찾을 낱말]) — 낱말이 비면 한국어·영어 이름으로 찾음
"""
from __future__ import annotations

import re, time
from datetime import date, timedelta
from pathlib import Path

import ai_run as A


def _get(url, **kw):                                                   # 위키는 한 번만 시도 (429면 바로 멈추게)
    return A.get(url, retries=0, **kw)


get = _get
rj, wj, log, now_iso, clean = A.rj, A.wj, A.log, A.now_iso, A.clean
TYPE = {"vc": "벤처캐피털(VC)", "pe": "사모펀드(PE)", "cvc": "기업 투자(CVC)", "ac": "액셀러레이터·초기", "sov": "국부펀드·공공", "gr": "그로스·크로스오버"}

# (id, 한국어, 영어(위키데이터 찾기), 종류, 나라, [찾을 낱말 — 정규식, 비면 이름으로])
FIRMS = [
    # 미국·글로벌 VC
    ("a16z", "앤드리슨 호로위츠", "Andreessen Horowitz", "vc", "US", [r"\bAndreessen Horowitz\b", r"\ba16z\b", "앤드리슨", "안드레센"]),
    ("sequoia", "세쿼이아 캐피털", "Sequoia Capital", "vc", "US", [r"\bSequoia\b", "세쿼이아", "세콰이어"]),
    ("accel", "액셀", "Accel", "vc", "US", [r"\bAccel\b(?!-| Partners India)", "액셀파트너스"]),
    ("lightspeed", "라이트스피드", "Lightspeed Venture Partners", "vc", "US", [r"\bLightspeed\b", "라이트스피드"]),
    ("founders", "파운더스 펀드", "Founders Fund", "vc", "US", [r"\bFounders Fund\b", "파운더스펀드", "파운더스 펀드"]),
    ("benchmark", "벤치마크", "Benchmark (venture capital firm)", "vc", "US", [r"\bBenchmark Capital\b", r"\bBenchmark\b(?= (led|and|,))"]),
    ("kleiner", "클라이너 퍼킨스", "Kleiner Perkins", "vc", "US", [r"\bKleiner Perkins\b", "클라이너"]),
    ("gv", "GV (구글 벤처스)", "GV (company)", "cvc", "US", [r"\bGV\b", r"\bGoogle Ventures\b", "구글벤처스"]),
    ("gc", "제너럴 카탈리스트", "General Catalyst", "vc", "US", [r"\bGeneral Catalyst\b", "제너럴 카탈리스트", "제너럴카탈리스트"]),
    ("thrive", "스라이브 캐피털", "Thrive Capital", "vc", "US", [r"\bThrive Capital\b", "스라이브"]),
    ("khosla", "코슬라 벤처스", "Khosla Ventures", "vc", "US", [r"\bKhosla\b", "코슬라"]),
    ("index", "인덱스 벤처스", "Index Ventures", "vc", "GB", [r"\bIndex Ventures\b", "인덱스벤처스"]),
    ("insight", "인사이트 파트너스", "Insight Partners", "gr", "US", [r"\bInsight Partners\b", "인사이트파트너스"]),
    ("tiger", "타이거 글로벌", "Tiger Global Management", "gr", "US", [r"\bTiger Global\b", "타이거글로벌", "타이거 글로벌"]),
    ("coatue", "코튜", "Coatue Management", "gr", "US", [r"\bCoatue\b", "코튜"]),
    ("greylock", "그레이록", "Greylock Partners", "vc", "US", [r"\bGreylock\b", "그레이록"]),
    ("bessemer", "베세머 벤처 파트너스", "Bessemer Venture Partners", "vc", "US", [r"\bBessemer\b", "베세머"]),
    ("nea", "NEA", "New Enterprise Associates", "vc", "US", [r"\bNEA\b", r"\bNew Enterprise Associates\b"]),
    ("ivp", "IVP", "Institutional Venture Partners", "gr", "US", [r"\bIVP\b"]),
    ("battery", "배터리 벤처스", "Battery Ventures", "vc", "US", [r"\bBattery Ventures\b"]),
    ("redpoint", "레드포인트", "Redpoint Ventures", "vc", "US", [r"\bRedpoint\b"]),
    ("felicis", "펠리시스", "Felicis Ventures", "vc", "US", [r"\bFelicis\b"]),
    ("yc", "와이 콤비네이터", "Y Combinator", "ac", "US", [r"\bY Combinator\b", r"\bYC\b", "와이콤비네이터", "와이 콤비네이터"]),
    ("500", "500 글로벌", "500 Global", "ac", "US", [r"\b500 Global\b", r"\b500 Startups\b", "500글로벌"]),
    ("lux", "럭스 캐피털", "Lux Capital", "vc", "US", [r"\bLux Capital\b"]),
    ("ribbit", "리빗 캐피털", "Ribbit Capital", "vc", "US", [r"\bRibbit Capital\b"]),
    ("paradigm", "패러다임", "Paradigm (investment firm)", "vc", "US", [r"\bParadigm\b(?= (led|and|,))", "패러다임"]),
    ("pantera", "판테라 캐피털", "Pantera Capital", "vc", "US", [r"\bPantera\b", "판테라"]),
    ("iconiq", "아이코닉", "ICONIQ Capital", "gr", "US", [r"\bICONIQ\b"]),
    ("menlo", "멘로 벤처스", "Menlo Ventures", "vc", "US", [r"\bMenlo Ventures\b"]),
    ("spark", "스파크 캐피털", "Spark Capital", "vc", "US", [r"\bSpark Capital\b"]),
    ("usv", "유니언 스퀘어 벤처스", "Union Square Ventures", "vc", "US", [r"\bUnion Square Ventures\b", r"\bUSV\b"]),
    ("firstround", "퍼스트 라운드", "First Round Capital", "vc", "US", [r"\bFirst Round Capital\b"]),
    ("crv", "CRV", "Charles River Ventures", "vc", "US", [r"\bCRV\b"]),
    ("8vc", "8VC", "8VC", "vc", "US", [r"\b8VC\b"]),
    ("techstars", "테크스타스", "Techstars", "ac", "US", [r"\bTechstars\b", "테크스타스"]),
    ("pnp", "플러그앤플레이", "Plug and Play Tech Center", "ac", "US", [r"\bPlug and Play\b", "플러그앤플레이"]),
    ("ga", "제너럴 애틀랜틱", "General Atlantic", "gr", "US", [r"\bGeneral Atlantic\b", "제너럴 애틀랜틱", "제너럴애틀랜틱"]),
    # 기업 투자(CVC)
    ("nvidia", "엔비디아 (NVentures)", "NVIDIA", "cvc", "US", [r"\bNVentures\b", r"\bNvidia\b(?=.{0,40}\b(invest|led|back|participat|round|funding))", "엔비디아"]),
    ("m12", "M12 (마이크로소프트)", "M12 (venture capital)", "cvc", "US", [r"\bM12\b"]),
    ("intel", "인텔 캐피털", "Intel Capital", "cvc", "US", [r"\bIntel Capital\b", "인텔캐피털"]),
    ("salesforce", "세일즈포스 벤처스", "Salesforce Ventures", "cvc", "US", [r"\bSalesforce Ventures\b"]),
    ("samsungnext", "삼성 넥스트", "Samsung Next", "cvc", "KR", [r"\bSamsung Next\b", "삼성넥스트", "삼성 넥스트"]),
    ("samsungvc", "삼성벤처투자", "Samsung Venture Investment", "cvc", "KR", ["삼성벤처투자", r"\bSamsung Ventures\b", r"\bSamsung Venture Investment\b"]),
    ("lgtv", "LG테크놀로지벤처스", "LG Technology Ventures", "cvc", "US", ["LG테크놀로지벤처스", r"\bLG Technology Ventures\b"]),
    ("kakaov", "카카오벤처스", "Kakao Ventures", "vc", "KR", ["카카오벤처스", r"\bKakao Ventures\b"]),
    ("d2sf", "네이버 D2SF", "Naver D2 Startup Factory", "cvc", "KR", ["D2SF", "디투에스에프"]),
    ("zer01ne", "현대차 제로원", "ZER01NE", "cvc", "KR", ["제로원", r"\bZER01NE\b"]),
    ("cj", "CJ인베스트먼트", "CJ Investment", "cvc", "KR", ["CJ인베스트먼트"]),
    ("lotte", "롯데벤처스", "Lotte Ventures", "cvc", "KR", ["롯데벤처스", r"\bLotte Ventures\b"]),
    ("gsv", "GS벤처스", "GS Ventures", "cvc", "KR", ["GS벤처스"]),
    # 국부펀드·아시아·유럽
    ("sbvf", "소프트뱅크 비전펀드", "SoftBank Vision Fund", "gr", "JP", [r"\bSoftBank\b", r"\bVision Fund\b", "소프트뱅크(?!벤처스)", "비전펀드"]),
    ("temasek", "테마섹", "Temasek Holdings", "sov", "SG", [r"\bTemasek\b", "테마섹"]),
    ("gic", "GIC", "GIC (sovereign wealth fund)", "sov", "SG", [r"\bGIC\b", "싱가포르투자청"]),
    ("mubadala", "무바달라", "Mubadala Investment Company", "sov", "AE", [r"\bMubadala\b", "무바달라"]),
    ("pif", "사우디 국부펀드(PIF)", "Public Investment Fund", "sov", "SA", [r"\bPIF\b", r"\bPublic Investment Fund\b", "사우디 국부펀드", "공공투자펀드"]),
    ("qia", "카타르투자청(QIA)", "Qatar Investment Authority", "sov", "QA", [r"\bQIA\b", r"\bQatar Investment Authority\b", "카타르투자청"]),
    ("adia", "아부다비투자청(ADIA)", "Abu Dhabi Investment Authority", "sov", "AE", [r"\bADIA\b", "아부다비투자청"]),
    ("mgx", "MGX", "MGX (investment firm)", "sov", "AE", [r"\bMGX\b"]),
    ("hillhouse", "힐하우스", "Hillhouse Investment", "pe", "CN", [r"\bHillhouse\b", "힐하우스", "高瓴"]),
    ("hongshan", "홍산(옛 세쿼이아 차이나)", "HongShan", "vc", "CN", [r"\bHongShan\b", "红杉", "홍산"]),
    ("qiming", "치밍 벤처 파트너스", "Qiming Venture Partners", "vc", "CN", [r"\bQiming\b", "启明"]),
    ("idg", "IDG 캐피털", "IDG Capital", "vc", "CN", [r"\bIDG Capital\b", "IDG资本"]),
    ("tencent", "텐센트", "Tencent", "cvc", "CN", [r"\bTencent\b(?=.{0,40}\b(invest|led|back|participat|round|funding))", "腾讯投资", "텐센트(?=.{0,20}(투자|주도|참여))"]),
    ("peakxv", "피크 XV (옛 세쿼이아 인도)", "Peak XV Partners", "vc", "IN", [r"\bPeak XV\b"]),
    ("prosus", "프로서스", "Prosus", "cvc", "NL", [r"\bProsus\b"]),
    ("atomico", "아토미코", "Atomico", "vc", "GB", [r"\bAtomico\b"]),
    ("balderton", "볼더턴", "Balderton Capital", "vc", "GB", [r"\bBalderton\b"]),
    ("northzone", "노스존", "Northzone", "vc", "SE", [r"\bNorthzone\b"]),
    ("creandum", "크리안덤", "Creandum", "vc", "SE", [r"\bCreandum\b"]),
    ("antler", "앤틀러", "Antler (company)", "ac", "SG", [r"\bAntler\b", "앤틀러"]),
    ("vertex", "버텍스 벤처스", "Vertex Holdings", "vc", "SG", [r"\bVertex Ventures\b"]),
    ("eastv", "이스트 벤처스", "East Ventures", "vc", "ID", [r"\bEast Ventures\b"]),
    ("jafco", "자프코", "JAFCO", "vc", "JP", [r"\bJAFCO\b", "ジャフコ"]),
    ("globalbrain", "글로벌 브레인", "Global Brain Corporation", "vc", "JP", [r"\bGlobal Brain\b", "グローバル・ブレイン"]),
    # 사모펀드(PE)
    ("blackstone", "블랙스톤", "Blackstone Inc.", "pe", "US", [r"\bBlackstone\b", "블랙스톤"]),
    ("kkr", "KKR", "KKR & Co.", "pe", "US", [r"\bKKR\b"]),
    ("carlyle", "칼라일", "The Carlyle Group", "pe", "US", [r"\bCarlyle\b", "칼라일"]),
    ("apollo", "아폴로", "Apollo Global Management", "pe", "US", [r"\bApollo Global\b", r"\bApollo\b(?= (to|has|agrees|-backed|funds|Global))", "아폴로 글로벌"]),
    ("tpg", "TPG", "TPG Inc.", "pe", "US", [r"\bTPG\b"]),
    ("eqt", "EQT", "EQT AB", "pe", "SE", [r"\bEQT\b"]),
    ("cvc", "CVC 캐피털", "CVC Capital Partners", "pe", "GB", [r"\bCVC\b"]),
    ("bain", "베인캐피털", "Bain Capital", "pe", "US", [r"\bBain Capital\b", "베인캐피털", "베인 캐피털"]),
    ("advent", "어드벤트 인터내셔널", "Advent International", "pe", "US", [r"\bAdvent International\b", "어드벤트"]),
    ("thoma", "토마 브라보", "Thoma Bravo", "pe", "US", [r"\bThoma Bravo\b", "토마브라보", "토마 브라보"]),
    ("silverlake", "실버레이크", "Silver Lake Partners", "pe", "US", [r"\bSilver Lake\b", "실버레이크"]),
    ("hf", "헬만 앤 프리드먼", "Hellman & Friedman", "pe", "US", [r"\bHellman & Friedman\b", r"\bH&F\b"]),
    ("warburg", "워버그 핀커스", "Warburg Pincus", "pe", "US", [r"\bWarburg Pincus\b", "워버그"]),
    ("permira", "퍼미라", "Permira", "pe", "GB", [r"\bPermira\b"]),
    ("brookfield", "브룩필드", "Brookfield Asset Management", "pe", "CA", [r"\bBrookfield\b", "브룩필드"]),
    ("ardian", "아디안", "Ardian (company)", "pe", "FR", [r"\bArdian\b"]),
    ("cinven", "신벤", "Cinven", "pe", "GB", [r"\bCinven\b"]),
    ("pai", "PAI 파트너스", "PAI Partners", "pe", "FR", [r"\bPAI Partners\b", r"\bPAI\b(?= (to|has|-backed|Partners))"]),
    ("cdr", "CD&R", "Clayton, Dubilier & Rice", "pe", "US", [r"\bCD&R\b", r"\bClayton,? Dubilier"]),
    ("vista", "비스타 에쿼티", "Vista Equity Partners", "pe", "US", [r"\bVista Equity\b", r"\bVista\b(?= and Elliott)"]),
    ("affinity", "어피니티", "Affinity Equity Partners", "pe", "HK", [r"\bAffinity Equity\b", "어피니티"]),
    ("mbk", "MBK파트너스", "MBK Partners", "pe", "KR", [r"\bMBK\b", "MBK파트너스", "엠비케이"]),
    ("hahn", "한앤컴퍼니", "Hahn & Company", "pe", "KR", ["한앤컴퍼니", "한앤코", r"\bHahn & Co"]),
    ("immpe", "IMM프라이빗에쿼티", "IMM Private Equity", "pe", "KR", ["IMM프라이빗에쿼티", "IMM PE", "IMM\\s?PE"]),
    ("stic", "스틱인베스트먼트", "STIC Investments", "pe", "KR", ["스틱인베스트먼트", r"\bSTIC Investments\b"]),
    ("vig", "VIG파트너스", "VIG Partners", "pe", "KR", ["VIG파트너스", "브이아이지"]),
    ("glenwood", "글랜우드PE", "Glenwood Private Equity", "pe", "KR", ["글랜우드"]),
    ("eqp", "어펄마캐피탈", "Affirma Capital", "pe", "SG", ["어펄마", r"\bAffirma\b"]),
    ("uck", "UCK파트너스", "UCK Partners", "pe", "KR", ["UCK파트너스", "유니슨캐피탈"]),
    ("skylake", "스카이레이크", "Skylake Equity Partners", "pe", "KR", ["스카이레이크"]),
    ("jkl", "JKL파트너스", "JKL Partners", "pe", "KR", ["JKL파트너스"]),
    ("praxis", "프랙시스캐피탈", "Praxis Capital Partners", "pe", "KR", ["프랙시스"]),
    ("qcap", "큐캐피탈", "Q Capital Partners", "pe", "KR", ["큐캐피탈"]),
    ("godo", "고도파트너스", "Godo Partners", "pe", "KR", ["고도파트너스", r"\bGodo Partners\b"]),
    # 한국 VC·액셀러레이터
    ("kip", "한국투자파트너스", "Korea Investment Partners", "vc", "KR", ["한국투자파트너스", "한투파", r"\bKorea Investment Partners\b"]),
    ("sbva", "SBVA (옛 소프트뱅크벤처스)", "SBVA", "vc", "KR", ["SBVA", "소프트뱅크벤처스"]),
    ("altos", "알토스벤처스", "Altos Ventures", "vc", "KR", ["알토스", r"\bAltos Ventures\b"]),
    ("stonebridge", "스톤브릿지벤처스", "Stonebridge Ventures", "vc", "KR", ["스톤브릿지"]),
    ("immi", "IMM인베스트먼트", "IMM Investment", "vc", "KR", ["IMM인베스트먼트"]),
    ("lb", "LB인베스트먼트", "LB Investment", "vc", "KR", ["LB인베스트먼트"]),
    ("ajuib", "아주IB투자", "AJU IB Investment", "vc", "KR", ["아주IB"]),
    ("miraevc", "미래에셋벤처투자", "Mirae Asset Venture Investment", "vc", "KR", ["미래에셋벤처투자", "미래에셋캐피탈"]),
    ("kbi", "KB인베스트먼트", "KB Investment", "vc", "KR", ["KB인베스트먼트"]),
    ("dsc", "DSC인베스트먼트", "DSC Investment", "vc", "KR", ["DSC인베스트먼트"]),
    ("companyk", "컴퍼니케이파트너스", "Company K Partners", "vc", "KR", ["컴퍼니케이"]),
    ("intervest", "인터베스트", "InterVest", "vc", "KR", ["인터베스트"]),
    ("atinum", "에이티넘인베스트먼트", "Atinum Investment", "vc", "KR", ["에이티넘"]),
    ("premier", "프리미어파트너스", "Premier Partners", "vc", "KR", ["프리미어파트너스"]),
    ("hanavc", "하나벤처스", "Hana Ventures", "vc", "KR", ["하나벤처스"]),
    ("shinhanvc", "신한벤처투자", "Shinhan Venture Investment", "vc", "KR", ["신한벤처투자"]),
    ("woorivc", "우리벤처파트너스", "Woori Venture Partners", "vc", "KR", ["우리벤처파트너스"]),
    ("svi", "SV인베스트먼트", "SV Investment", "vc", "KR", ["SV인베스트먼트"]),
    ("tsi", "TS인베스트먼트", "TS Investment", "vc", "KR", ["TS인베스트먼트"]),
    ("murex", "뮤렉스파트너스", "Murex Partners", "vc", "KR", ["뮤렉스"]),
    ("capstone", "캡스톤파트너스", "Capstone Partners", "vc", "KR", ["캡스톤파트너스"]),
    ("poscovc", "포스코기술투자", "POSCO Technology Investment", "cvc", "KR", ["포스코기술투자"]),
    ("kvic", "한국벤처투자(모태펀드)", "Korea Venture Investment Corporation", "sov", "KR", ["한국벤처투자", "모태펀드"]),
    ("kdb", "한국산업은행", "Korea Development Bank", "sov", "KR", ["산업은행", "KDB산업은행", r"\bKDB\b"]),
    ("ibk", "IBK기업은행", "Industrial Bank of Korea", "sov", "KR", ["IBK기업은행", "기업은행"]),
    ("growthfund", "국민성장펀드", "", "sov", "KR", ["국민성장펀드"]),
    ("bonangels", "본엔젤스", "Bon Angels", "ac", "KR", ["본엔젤스"]),
    ("primer", "프라이머", "Primer (accelerator)", "ac", "KR", [r"(?<![가-힣])프라이머(?!리|즈|가 되)"]),
    ("mashup", "매쉬업벤처스", "Mashup Ventures", "ac", "KR", ["매쉬업"]),
    ("futureplay", "퓨처플레이", "FuturePlay", "ac", "KR", ["퓨처플레이"]),
    ("bluepoint", "블루포인트파트너스", "Bluepoint Partners", "ac", "KR", ["블루포인트"]),
    ("sparklabs", "스파크랩", "SparkLabs", "ac", "KR", ["스파크랩", r"\bSparkLabs\b"]),
    ("theventures", "더벤처스", "The Ventures", "ac", "KR", ["더벤처스"]),
    ("strong", "스트롱벤처스", "Strong Ventures", "vc", "KR", ["스트롱벤처스"]),
    ("snuh", "서울대기술지주", "SNU Holdings", "ac", "KR", ["서울대기술지주"]),
    ("dcamp", "디캠프", "D.CAMP", "ac", "KR", ["디캠프", r"\bD\.?CAMP\b"]),
]


def matchers():
    out = []
    for fid, ko, en, ty, cc, al in FIRMS:
        pats = al or [re.escape(ko)] + ([r"\b" + re.escape(en) + r"\b"] if en else [])
        out.append((fid, re.compile("|".join(pats))))
    return out


# ───────── 위키데이터·위키백과 ─────────
def wd_entity(qid):
    j = get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": qid, "props": "claims|sitelinks|labels|descriptions", "languages": "ko|en", "format": "json"}).json()
    return j["entities"][qid]


def wd_find(en, ko):
    """영어 이름(없으면 한국어)으로 위키데이터 항목 찾기 — 설명에 투자·회사 낱말이 있는 것만"""
    for name, lang in ((en, "en"), (ko, "ko")):
        if not name: continue
        q = re.sub(r"\s*\(.*\)$", "", name)
        j = get("https://www.wikidata.org/w/api.php", params={"action": "wbsearchentities", "search": q, "language": lang, "format": "json", "limit": 5}).json()
        for r in j.get("search", []):
            desc = (r.get("description") or "").lower()
            if re.search(r"venture|capital|equity|invest|fund|accelerat|firm|company|bank|sovereign|asset|holding|corporation|기업|회사|투자|은행", desc) or (lang == "ko" and r.get("label") == q):
                return r["id"]
    return ""


def claim(e, p):
    try: return e["claims"][p]
    except KeyError: return []


def labels(qids):
    if not qids: return {}
    j = get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": "|".join(qids[:50]), "props": "labels", "languages": "ko|en", "format": "json"}).json()
    return {q: (v.get("labels", {}).get("ko") or v.get("labels", {}).get("en") or {}).get("value", "") for q, v in j.get("entities", {}).items()}


CUR = {"Q4917": "USD", "Q4916": "EUR", "Q25224": "GBP", "Q8146": "JPY", "Q202040": "KRW", "Q39099": "CNY", "Q190951": "SGD"}


def wiki_info(e):
    info = {"qid": e["id"]}
    sl = e.get("sitelinks", {})
    if "kowiki" in sl: info["kowiki"] = sl["kowiki"]["title"]
    if "enwiki" in sl: info["enwiki"] = sl["enwiki"]["title"]
    for c in claim(e, "P856")[:1]:
        info["site"] = c["mainsnak"].get("datavalue", {}).get("value", "")
    for c in claim(e, "P571")[:1]:
        t = c["mainsnak"].get("datavalue", {}).get("value", {}).get("time", "")
        m = re.match(r"\+(\d{4})", t)
        if m: info["since"] = m.group(1)
    best = None                                                                    # 운용자산(P4103) — 가장 최근 것
    for c in claim(e, "P4103"):
        v = c["mainsnak"].get("datavalue", {}).get("value", {})
        if not v.get("amount"): continue
        yr = ""
        for q in c.get("qualifiers", {}).get("P585", []):
            m = re.match(r"\+(\d{4})", q.get("datavalue", {}).get("value", {}).get("time", ""))
            if m: yr = m.group(1)
        cur = CUR.get(v.get("unit", "").rsplit("/", 1)[-1], "USD")
        if best is None or yr > best[2]: best = (float(v["amount"]), cur, yr)
    if best: info["aum"] = list(best)
    for c in claim(e, "P1128")[:1]:
        try: info["emp"] = int(float(c["mainsnak"]["datavalue"]["value"]["amount"]))
        except Exception: pass
    refs = {}
    for p in ("P159", "P112"):
        refs[p] = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in claim(e, p)][:4]
    lab = labels([q for v in refs.values() for q in v if q])
    if refs["P159"]: info["hq"] = lab.get(refs["P159"][0], "")
    if refs["P112"]: info["founders"] = [lab.get(q, "") for q in refs["P112"] if lab.get(q)]
    d = e.get("descriptions", {})
    info["wdDesc"] = (d.get("ko") or d.get("en") or {}).get("value", "")
    return info


def wiki_extract(lang, title):
    j = get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")).json()
    return clean(j.get("extract", ""), 900)


def refresh_wiki(cache, deadline, ko_tr, budget=50):
    """30일 넘은(또는 없는) 투자사만 위키에서 다시 받음"""
    cut = (date.today() - timedelta(days=30)).isoformat(); n = 0; need_tr = []
    for fid, ko, en, ty, cc, al in FIRMS:
        c = cache.get(fid, {})
        if c.get("day", "") >= cut or n >= budget or time.time() > deadline: continue
        n += 1
        try:
            qid = c.get("qid") or wd_find(en, ko)
            info = {"day": date.today().isoformat()}
            if qid:
                info.update(wiki_info(wd_entity(qid)))
                if info.get("kowiki"): info["desc"] = wiki_extract("ko", info["kowiki"]); info["descLang"] = "ko"
                elif info.get("enwiki"): info["desc_en"] = wiki_extract("en", info["enwiki"]); info["descLang"] = "en"
            cache[fid] = info
            if info.get("desc_en"): need_tr.append(fid)
            time.sleep(1.0)
        except Exception as e:
            log(f"투자사 위키 실패 {fid}: {str(e)[:60]}")
            if "429" in str(e): log("위키가 잠시 쉬라고 함 → 나머지는 다음 실행에"); break
    if need_tr and ko_tr is not None:
        try:
            res = ko_tr.many([(cache[f]["desc_en"], "en") for f in need_tr], deadline=deadline)
            for f, v in zip(need_tr, res):
                if v: cache[f]["desc"] = v
        except Exception as e: log(f"투자사 소개 번역 실패: {e}")
    for f in cache.values():                                                       # 번역 못 한 영어 소개는 원문으로라도
        if not f.get("desc") and f.get("desc_en"): f["desc"] = f["desc_en"]; f["descLang"] = "en-raw"
    log(f"투자사 위키 {n}곳 받음")


# ───────── 쌓인 자료에서 활동 모으기 ─────────
def build(out_dir: Path, news_dir: Path, fd_dir: Path, now_deals, deadline, ko_tr=None):
    st = out_dir / "_state" / "firmwiki.json"; cache = rj(st, {})
    try: refresh_wiki(cache, deadline, ko_tr)
    except Exception as e: log(f"투자사 위키 건너뜀: {e}")
    wj(st, cache)
    cut = (date.today() - timedelta(days=90)).isoformat()
    pool, seen = [], set()
    for d in now_deals:
        if d["id"] not in seen: seen.add(d["id"]); pool.append(d)
    for f in sorted(news_dir.glob("????-??-??.json"), reverse=True):
        if f.stem < cut: break
        for d in rj(f, {}).get("items", []):
            if d["id"] not in seen: seen.add(d["id"]); pool.append(d)
    M = matchers(); hits = {fid: [] for fid, _ in M}
    for d in pool:
        if d.get("t") in ("formd", "dart"): continue
        txt = " ".join([" ".join(d.get("inv") or []), d.get("title", ""), d.get("ko", ""), d.get("co", ""), d.get("tgt", "")])
        for fid, rx in M:
            if rx.search(txt): hits[fid].append(d)
    # 미국 Form D 펀드 신고 (회사 영어 이름이 펀드 이름에 들어간 것)
    funds = {fid: [] for fid, _ in M}
    fd_rx = []
    for fid, ko, en, ty, cc, al in FIRMS:
        base = re.sub(r"\s*\(.*\)$|\b(Inc\.|AB|& Co\.|Management|Holdings|Partners|Group|Investment|Company|Capital|Ventures?)\b\.?", "", en or "").strip(" ,.")
        if len(base) >= 4: fd_rx.append((fid, re.compile(r"\b" + re.escape(base) + r"\b", re.I)))
    for f in sorted(fd_dir.glob("*.json"))[-8:]:
        for r in rj(f, {}).get("rows", []):
            if r[3] != "Pooled Investment Fund": continue
            for fid, rx in fd_rx:
                if rx.search(r[1]): funds[fid].append([r[0], r[1], r[5], r[4]])
    (out_dir / "firms").mkdir(parents=True, exist_ok=True)
    lst = []
    names = {fid: ko for fid, ko, *_ in FIRMS}
    for fid, ko, en, ty, cc, al in FIRMS:
        hs = sorted(hits[fid], key=lambda d: (d["date"], d.get("amt") or 0), reverse=True)
        stages, secs, ccs, co = {}, {}, {}, {}
        for d in hs:
            k = d.get("stage") or d.get("kind"); stages[k] = stages.get(k, 0) + 1
            for s in (d.get("sec") or [])[:1]: secs[s] = secs.get(s, 0) + 1
            ccs[d.get("cc", "WW")] = ccs.get(d.get("cc", "WW"), 0) + 1
            txt = " ".join([" ".join(d.get("inv") or []), d.get("title", ""), d.get("ko", "")])
            for other, rx in M:
                if other != fid and rx.search(txt): co[other] = co.get(other, 0) + 1
        w = cache.get(fid, {})
        fs = sorted(funds[fid], reverse=True)[:12]
        amt = sum(d.get("amt") or 0 for d in hs)
        base = {"id": fid, "ko": ko, "en": re.sub(r"\s*\(.*\)$", "", en or ""), "type": ty, "cc": cc, "n90": len(hs), "amt90": amt,
                "last": hs[0]["date"] if hs else "", "since": w.get("since", ""), "aum": w.get("aum"), "hasWiki": bool(w.get("desc"))}
        lst.append(base)
        det = dict(base, site=w.get("site", ""), hq=w.get("hq", ""), founders=w.get("founders", []), emp=w.get("emp"), desc=w.get("desc", ""), descLang=w.get("descLang", ""),
                   wdDesc=w.get("wdDesc", ""), qid=w.get("qid", ""), kowiki=w.get("kowiki", ""), enwiki=w.get("enwiki", ""),
                   stages=stages, secs=secs, ccs=ccs, co=[[names[k], k, n] for k, n in sorted(co.items(), key=lambda kv: -kv[1])[:10]],
                   deals=[{k: d.get(k) for k in ("id", "date", "kind", "stage", "title", "ko", "amt", "amtS", "cc", "co", "tgt", "url", "sec", "inv", "n", "src", "t", "lang") if d.get(k) not in (None, "", [])} for d in hs[:40]],
                   funds=fs, fundSum=sum(x[2] for x in funds[fid]))
        wj(out_dir / "firms" / f"{fid}.json", det)
    lst.sort(key=lambda x: (-x["n90"], -x["amt90"]))
    by_deal = {}
    for fid, ds in hits.items():
        for d in ds[:40]: by_deal.setdefault(d["id"], []).append(fid)
    wj(out_dir / "firms.json", {"at": now_iso(), "types": TYPE, "firms": lst, "byDeal": by_deal})
    log(f"주요 투자사 {len(lst)}곳 · 최근 90일 거래가 있는 곳 {sum(1 for x in lst if x['n90'])}곳")
