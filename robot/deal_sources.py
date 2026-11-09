"""deal_sources.py — '딜' 앱 출처표·분류 낱말. 고치면 다음 실행부터 적용 (robot/deal_run.py 가 읽음).

  FEEDS      직접 받는 RSS (나라·언어·이름)
  GNEWS      구글 뉴스 검색 RSS (나라판·언어·검색어) — 하루치(when:1d)
  KIND_RX    종류(투자·M&A·사모·상장·펀드) 낱말
  STAGE_RX   투자 단계 낱말
  SECTORS    분야 낱말 (영어·한국어 둘 다, 번역 뒤 한국어로도 한 번 더 봄)
  COUNTRY_RX 제목 속 나라 낱말 → 나라 코드
"""

# (id, 이름, 주소, 나라 기본값, 언어, 거르기: True 면 투자·M&A 낱말이 있을 때만)
# Tech.eu·The Bridge(일본)는 GitHub 서버에서 403으로 막혀 뺌 (일본은 구글 뉴스 일본판으로)
FEEDS = [
    ("cb", "Crunchbase News", "https://news.crunchbase.com/feed/", "US", "en", True),
    ("tc", "TechCrunch 벤처", "https://techcrunch.com/category/venture/feed/", "US", "en", True),
    ("sifted", "Sifted (유럽)", "https://sifted.eu/feed", "EU", "en", True),
    ("pew", "Private Equity Wire", "https://www.privateequitywire.co.uk/feed", "", "en", True),
    ("inc42", "Inc42 (인도)", "https://inc42.com/feed/", "IN", "en", True),
    ("tcabal", "TechCabal (아프리카)", "https://techcabal.com/feed/", "AF", "en", True),
    ("wamda", "Wamda (중동)", "https://www.wamda.com/feed", "ME", "en", True),
    ("latam", "LatamList (중남미)", "https://latamlist.com/feed/", "LATAM", "en", True),
    ("platum", "플래텀", "https://platum.kr/feed", "KR", "ko", True),
    ("vsq", "벤처스퀘어", "https://www.venturesquare.net/feed", "KR", "ko", True),
    ("stn", "스타트업엔", "https://www.startupn.kr/rss/allArticle.xml", "KR", "ko", True),
    ("srecipe", "스타트업레시피", "https://www.startuprecipe.co.kr/feed", "KR", "ko", True),
    ("ichosun", "인베스트조선", "https://www.investchosun.com/rss/", "KR", "ko", True),
]

# (나라판 hl, gl, ceid, 언어, 나라 기본값, [검색어]) — 검색어마다 하루치(when:1d) 최대 100개
GNEWS = [
    ("ko", "KR", "KR:ko", "ko", "KR", ["투자 유치 시리즈", "프리A OR 시드 투자 유치", "억원 투자 유치", "인수합병 OR M&A 인수", "지분 인수 계약", "경영권 인수", "사모펀드 OR PEF 인수", "IPO 공모 상장", "벤처펀드 결성 OR 모태펀드"]),
    ("en-US", "US", "US:en", "en", "US", ["raises Series", "raises seed round", "funding round led by", "to acquire OR acquires OR acquisition", "agrees to buy deal billion", "private equity buyout OR take-private", "IPO prices OR files for IPO", "venture fund closes OR closes fund"]),
    ("en-GB", "GB", "GB:en", "en", "", ["startup raises funding", "acquisition deal agreed"]),
    ("en-IN", "IN", "IN:en", "en", "IN", ["startup raises funding", "acquires stake"]),
    ("en-SG", "SG", "SG:en", "en", "", ["Southeast Asia startup raises", "Singapore startup funding"]),
    ("en-US", "US", "US:en", "en", "IL", ["Israeli startup raises"]),
    ("en-US", "US", "US:en", "en", "ME", ["UAE OR Saudi startup raises"]),
    ("ja", "JP", "JP:ja", "ja", "JP", ["資金調達 シリーズ", "買収 合意"]),
    ("zh-CN", "CN", "CN:zh-Hans", "zh", "CN", ["融资 轮", "收购 并购"]),
    ("de", "DE", "DE:de", "de", "DE", ["Finanzierungsrunde Millionen", "Übernahme Milliarden"]),
    ("fr", "FR", "FR:fr", "fr", "FR", ["lève millions d'euros", "rachat acquisition"]),
    ("pt-BR", "BR", "BR:pt-419", "pt", "BR", ["rodada de investimento", "aquisição compra empresa"]),
    ("id", "ID", "ID:id", "id", "ID", ["pendanaan seri startup"]),
]

# 이 낱말이 하나도 없으면 투자·M&A 글이 아님 (직접 받는 RSS 거르기)
DEAL_WORDS = (r"\b(raise[sd]?|raising|funding|financing|round|seed|series [a-h]\b|invest(s|ment|or)?|acquir(e|es|ed|ing|ition)|buy(s|out)?|bought|merger|merge|takeover|take-private|stake|IPO|listing|went public|go public|SPAC|private equity|buyout|fund (close|closes|closed)|closes? .*fund|valuation|unicorn|backed|led by)\b"
              r"|투자|유치|인수|합병|M&A|매각|지분|상장|IPO|공모|펀드|PEF|사모|시리즈|프리\s?A|시드|밸류|기업가치|엑시트"
              r"|資金調達|調達|買収|出資|上場|融资|收购|并购|上市|Finanzierung|Übernahme|lève|rachat|rodada|aquisição|pendanaan")
SKIP_WORDS = (r"(?i)\b(podcast|webinar|newsletter|opinion|how to|guide|tips|weekly|roundup|recap|this week in|should (the|we|you|i)|explained|what (it|this) means|raises (the bar|concerns?|questions?|prices?|rates?|guidance|forecast|outlook|dividend|awareness|alarm|eyebrows|the stakes)|"
              r"securiti[sz]ation|biggest (rounds|deals)|funding (recap|report|tracker)|^(series [a-h]|seed|venture|vc|funding|m&a|ipos?) (in|for) \d{4}|NFL|NBA|MLB|NHL|MLS|quarterback|outfielder|pitcher|linebacker|free agent|draft pick|trade deadline|via trade|roster|transfer window|signs with)\b|\?\s*$|？\s*$"
              r"|칼럼|사설|기고|기자수첩|썰|위클리|브리핑\]|인터뷰\]|\[포토\]|\[사진\]|채용|세미나|설명회 개최|IR 행사|데모데이|모집|공모전|수상|선정$|전망\]|점검\]|분석\]|특징주|주가|목표가|네이버 블로그|티스토리")

# 종류 — 위에서부터 먼저 맞는 것 (펀드·사모·인수합병·상장이 투자보다 먼저)
KIND_RX = [
    ("fund", "펀드 결성", r"\b(closes?|closed|launches|raises?)\b.{0,40}\b(fund|vehicle)\b|\bfund (I|II|III|IV|V|VI|VII|VIII|IX|X)\b|debut fund|\bfinal close\b|venture fund|growth fund|펀드 결성|펀드 조성|모태펀드|출자사업|결성총회|LP 출자|ファンド(を)?組成|基金"),
    ("pe", "사모·바이아웃", r"private equity|buyout|take-private|take private|LBO|leveraged|PE firm|사모펀드|PEF|바이아웃|경영권 매각|私募|Private-Equity"),
    ("ma", "인수합병", r"\b(acquir(e|es|ed|ing)|acquisition|to buy|buys|bought|merger|merge[sd]?|takeover|deal to buy|snaps up|purchase of)\b|인수|합병|M&A|매각|경영권|買収|経営統合|收购|并购|Übernahme|übernimmt|rachat|rachète|acquisizione|aquisição|adquire|akuisisi"),
    ("ipo", "상장", r"\bIPO\b|initial public offering|goes public|go public|went public|listing on|debut on (the )?(NYSE|Nasdaq)|SPAC|direct listing|상장|공모가|공모주|증권신고서|코스닥 입성|上場|上市|Börsengang|introduction en bourse|abertura de capital"),
    ("vc", "투자 유치", r"\b(raise[sd]?|raising|funding|financing|seed|series [a-h]\b|pre-seed|round|invest(s|ment)|backed by|led by|secures?|lands|bags|nets)\b|투자 유치|투자유치|투자를 유치|시리즈|프리\s?A|시드|브릿지 투자|資金調達|調達|出資|融资|Finanzierungsrunde|lève|rodada|pendanaan|investimento"),
]
KIND_NAME = {k: n for k, n, _ in KIND_RX} | {"etc": "기타"}

# 단계 (투자 유치일 때)
STAGE_RX = [
    ("pre-seed", "프리시드", r"pre-?seed|프리\s?시드|エンジェル|天使轮|angel round"),
    ("seed", "시드", r"\bseed\b|시드|シード|种子轮|Seed-"),
    ("pre-a", "프리A", r"pre-?series ?a|pre-?a\b|프리\s?A|Pre-A"),
    ("a", "시리즈 A", r"series[ -]?a\b|series[ -]?a-?\d|시리즈\s?A|シリーズA|A轮|Serie[ -]A|Série A|seri A"),
    ("b", "시리즈 B", r"series[ -]?b\b|시리즈\s?B|シリーズB|B轮|Serie[ -]B|Série B|seri B"),
    ("c", "시리즈 C", r"series[ -]?c\b|시리즈\s?C|シリーズC|C轮|Serie[ -]C|Série C|seri C"),
    ("d+", "시리즈 D 이상", r"series[ -]?[d-h]\b|시리즈\s?[D-H]|シリーズ[D-H]|[D-H]轮|Serie[ -][D-H]"),
    ("growth", "그로스·후기", r"growth (round|equity|financing)|late-stage|pre-IPO|프리\s?IPO|그로스|戦略的|战略融资"),
    ("debt", "대출·채권", r"debt (financing|facility)|credit facility|venture debt|loan|convertible|대출|사채|CB 발행|전환사채|融資枠"),
    ("grant", "지원금", r"\bgrant\b|지원금|정부 지원|보조금"),
]
STAGE_NAME = {k: n for k, n, _ in STAGE_RX}

# 분야 (id, 이름, 낱말) — 최대 2개
SECTORS = [
    ("ai", "AI", r"\bAI\b|artificial intelligence|machine learning|LLM|generative|agentic|\bagents?\b|foundation model|인공지능|AI |생성형|에이전트|LLM|人工知能|人工智能|大模型|\bKI\b"),
    ("chip", "반도체·하드웨어", r"semiconductor|chip|GPU|silicon|photonic|quantum|hardware|data ?center|반도체|칩|팹리스|양자|데이터센터|半導体|芯片|算力|Halbleiter"),
    ("bio", "바이오·제약", r"biotech|pharma|drug|therap|clinical|oncology|antibod|gene|mRNA|vaccine|biolog|바이오|제약|신약|항체|임상|治験|创新药|生物|Biotech"),
    ("health", "헬스케어·의료", r"health|medical|hospital|patient|clinic|diagnos|medtech|care\b|헬스케어|의료|병원|진단|디지털 헬스|医療|医疗|Gesundheit"),
    ("fin", "핀테크·금융", r"fintech|payment|bank|lending|insur|wealth|neobank|stablecoin|card|금융|핀테크|결제|보험|은행|대출|증권|フィンテック|金融|支付"),
    ("crypto", "크립토·블록체인", r"crypto|blockchain|web3|token|bitcoin|ethereum|defi|가상자산|블록체인|코인|암호화폐|仮想通貨|区块链"),
    ("energy", "에너지·기후", r"energy|solar|battery|climate|carbon|nuclear|fusion|hydrogen|grid|EV charging|renewable|에너지|배터리|태양광|탄소|원전|수소|기후|電池|新能源|储能|Energie"),
    ("mob", "모빌리티·자동차", r"mobility|autonomous|self-driving|vehicle|automotive|\bEV\b|car\b|ride|logistics|freight|drone|모빌리티|자율주행|자동차|전기차|물류|드론|自動運転|物流|汽车|无人机"),
    ("robot", "로봇·제조", r"robot|automation|manufactur|industrial|factory|3D print|humanoid|로봇|제조|스마트팩토리|자동화|ロボット|机器人|制造"),
    ("defense", "우주·방산", r"defen[cs]e|military|space|satellite|rocket|aerospace|방산|국방|우주|위성|발사체|防衛|航天|卫星|Rüstung"),
    ("sw", "기업용 소프트웨어", r"SaaS|software|enterprise|developer|cloud|cyber|security|data platform|B2B|소프트웨어|SaaS|클라우드|보안|사이버|B2B|ソフトウェア|软件|网络安全"),
    ("com", "커머스·소비재", r"e-?commerce|retail|consumer|brand|fashion|beauty|marketplace|D2C|커머스|이커머스|소비재|뷰티|패션|유통|리테일|小売|电商|消费"),
    ("food", "푸드·농업", r"food|restaurant|delivery|agri|farm|grocery|beverage|푸드|식품|외식|배달|농업|스마트팜|食品|農業|餐饮|农业"),
    ("fit", "스포츠·피트니스", r"fitness|gym|sport|wellness|athlet|workout|피트니스|헬스장|체육|스포츠|운동|웰니스|フィットネス|健身|体育"),
    ("edu", "교육", r"edtech|education|learning|school|tutor|에듀테크|교육|학습|教育"),
    ("media", "미디어·게임·콘텐츠", r"media|gaming|game|music|video|stream|entertainment|creator|K-?pop|미디어|게임|콘텐츠|엔터|음악|웹툰|ゲーム|游戏|娱乐"),
    ("real", "부동산·건설", r"real estate|proptech|property|construction|housing|REIT|부동산|건설|프롭테크|不動産|房地产"),
    ("tel", "통신·인터넷", r"telecom|5G|network|internet|broadband|통신|네트워크|通信"),
]
SECTOR_NAME = {k: n for k, n, _ in SECTORS} | {"etc": "기타"}

# 나라 (제목·요약 속 낱말 → 코드). 'EU'·'ME'·'AF'·'LATAM'·'SEA' 는 권역
COUNTRY_RX = [
    ("KR", r"Korea|Korean|Seoul|한국|국내|서울|판교|코스닥|코스피|韓国|韩国"),
    ("JP", r"Japan|Japanese|Tokyo|일본|도쿄|日本|東京"),
    ("CN", r"China|Chinese|Beijing|Shanghai|Shenzhen|Hong Kong|중국|베이징|상하이|홍콩|中国|北京|上海|深圳|香港"),
    ("IN", r"India|Indian|Bengaluru|Bangalore|Mumbai|Delhi|인도|뭄바이|Rs\.? ?\d|₹|crore"),
    ("GB", r"\bUK\b|British|London|Britain|영국|런던"),
    ("DE", r"German|Germany|Berlin|Munich|독일|베를린|뮌헨"),
    ("FR", r"France|French|Paris|프랑스|파리"),
    ("IL", r"Israel|Israeli|Tel Aviv|이스라엘"),
    ("SG", r"Singapore|싱가포르"),
    ("ID", r"Indonesia|Jakarta|인도네시아"),
    ("VN", r"Vietnam|베트남"),
    ("AE", r"\bUAE\b|Dubai|Abu Dhabi|Emirat|두바이|아랍에미리트|아부다비"),
    ("SA", r"Saudi|Riyadh|사우디"),
    ("BR", r"Brazil|Brazilian|São Paulo|브라질"),
    ("MX", r"Mexico|Mexican|멕시코"),
    ("CA", r"Canada|Canadian|Toronto|Vancouver|캐나다"),
    ("AU", r"Australia|Australian|Sydney|호주"),
    ("NG", r"Nigeria|Lagos|나이지리아"),
    ("ZA", r"South Africa|남아공"),
    ("SE", r"Sweden|Swedish|Stockholm|스웨덴"),
    ("NL", r"Netherlands|Dutch|Amsterdam|네덜란드"),
    ("CH", r"Switzerland|Swiss|Zurich|스위스"),
    ("ES", r"Spain|Spanish|Madrid|Barcelona|스페인"),
    ("US", r"\bU\.?S\.?\b|American|Silicon Valley|San Francisco|New York|미국|실리콘밸리|뉴욕|NYSE|Nasdaq|나스닥|美国|米国"),
]
REGION = {"KR": "한국", "US": "미국", "CN": "중국", "JP": "일본", "IN": "인도", "GB": "영국", "DE": "독일", "FR": "프랑스", "IL": "이스라엘", "SG": "싱가포르", "ID": "인도네시아", "VN": "베트남",
          "AE": "아랍에미리트", "SA": "사우디", "BR": "브라질", "MX": "멕시코", "CA": "캐나다", "AU": "호주", "NG": "나이지리아", "ZA": "남아공", "SE": "스웨덴", "NL": "네덜란드", "CH": "스위스", "ES": "스페인",
          "EU": "유럽(기타)", "ME": "중동(기타)", "AF": "아프리카(기타)", "LATAM": "중남미(기타)", "SEA": "동남아(기타)", "WW": "세계·미상"}

# 금액대 (원) — 화면 칩
BANDS = [("s", "10억 미만", 0, 1e9), ("m", "10억~100억", 1e9, 1e10), ("l", "100억~1,000억", 1e10, 1e11), ("xl", "1,000억~1조", 1e11, 1e12), ("xxl", "1조 이상", 1e12, 1e20)]

# 환율 (1 단위 = 원). 매 실행 frankfurter(유럽중앙은행 기준, 무료)로 새로 받고, 못 받으면 이 값
FX_DEFAULT = {"USD": 1400, "EUR": 1550, "GBP": 1820, "JPY": 9.0, "CNY": 200, "INR": 15.5, "SGD": 1050, "AUD": 900, "CAD": 1000, "CHF": 1650, "SEK": 135, "BRL": 250, "HKD": 180, "AED": 380, "SAR": 373, "IDR": 0.086, "ILS": 380, "KRW": 1}

# SEC Form D 업종 → 분야
FORMD_IND = {"Biotechnology": "bio", "Pharmaceuticals": "bio", "Health Insurance": "health", "Hospitals and Physicians": "health", "Other Health Care": "health",
             "Computers": "chip", "Telecommunications": "tel", "Other Technology": "sw", "Manufacturing": "robot", "Energy Conservation": "energy", "Electric Utilities": "energy",
             "Environmental Services": "energy", "Oil and Gas": "energy", "Coal Mining": "energy", "Other Energy": "energy", "Agriculture": "food", "Restaurants": "food", "Retailing": "com",
             "Business Services": "sw", "Airlines and Airports": "mob", "Lodging and Conventions": "com", "Tourism and Travel Services": "com", "Other Travel": "com",
             "Commercial Banking": "fin", "Insurance": "fin", "Investment Banking": "fin", "Other Banking and Financial Services": "fin", "Investing": "fin",
             "Commercial": "real", "Construction": "real", "REITS and Finance": "real", "Residential": "real", "Other Real Estate": "real", "Pooled Investment Fund": "fund"}
FORMD_KO = {"Biotechnology": "바이오", "Pharmaceuticals": "제약", "Other Technology": "기타 기술", "Computers": "컴퓨터·하드웨어", "Telecommunications": "통신", "Other Health Care": "기타 헬스케어",
            "Hospitals and Physicians": "병원·의료", "Health Insurance": "건강보험", "Manufacturing": "제조", "Business Services": "기업 서비스", "Retailing": "소매", "Restaurants": "외식",
            "Agriculture": "농업", "Oil and Gas": "석유·가스", "Other Energy": "기타 에너지", "Energy Conservation": "에너지 절약", "Electric Utilities": "전력", "Environmental Services": "환경",
            "Coal Mining": "석탄", "Airlines and Airports": "항공", "Lodging and Conventions": "숙박", "Tourism and Travel Services": "여행", "Other Travel": "기타 여행", "Commercial Banking": "은행",
            "Insurance": "보험", "Investment Banking": "투자은행", "Other Banking and Financial Services": "기타 금융", "Investing": "투자", "Commercial": "상업용 부동산", "Construction": "건설",
            "REITS and Finance": "리츠", "Residential": "주거용 부동산", "Other Real Estate": "기타 부동산", "Pooled Investment Fund": "투자 펀드", "Other": "기타"}
FUND_KO = {"Venture Capital Fund": "벤처캐피털(VC) 펀드", "Private Equity Fund": "사모(PE) 펀드", "Hedge Fund": "헤지펀드", "Other Investment Fund": "기타 투자 펀드"}
# 오늘 화면 '큰 거래'에 올릴 Form D (펀드·부동산·금융 서류 회사는 빼고, 이 금액 이상)
FORMD_FEED_MIN = 20_000_000
FORMD_FUND_FEED_MIN = 100_000_000
FORMD_SKIP_IND = {"Pooled Investment Fund", "Commercial", "Construction", "REITS and Finance", "Residential", "Other Real Estate", "Commercial Banking", "Investing",
                  "Investment Banking", "Other Banking and Financial Services", "Insurance", "Oil and Gas"}

# SEC 공시 종류 (daily/full index) → (종류, 한국어)
SEC_FORMS = {"S-1": ("ipo", "상장 신청(S-1)"), "F-1": ("ipo", "외국 기업 상장 신청(F-1)"), "424B4": ("ipo", "공모가 확정(424B4)"),
             "S-4": ("ma", "합병 등록(S-4)"), "F-4": ("ma", "외국 기업 합병 등록(F-4)"), "DEFM14A": ("ma", "합병 주총 안내(DEFM14A)"), "PREM14A": ("ma", "합병 주총 예비(PREM14A)"),
             "SC TO-T": ("ma", "공개매수(SC TO-T)"), "SC 14D9": ("ma", "공개매수 의견(SC 14D9)"), "SC 13E3": ("pe", "비상장 전환(SC 13E3)")}

# DART 보고서 이름 → (종류, 한국어, 자세히 API)
DART_RX = [
    (r"회사합병결정", "ma", "회사 합병", "cmpMgDecsn"),
    (r"분할합병결정", "ma", "분할합병", "cmpDvmgDecsn"),
    (r"주식교환ㆍ?이전결정|주식교환.이전결정", "ma", "주식 교환·이전", "stkExtrDecsn"),
    (r"타법인주식및출자증권양수결정", "ma", "다른 회사 지분 인수", "otcprStkInvscrInhDecsn"),
    (r"영업양수결정", "ma", "영업 양수", "bsnInhDecsn"),
    (r"최대주주변경을수반하는주식양수도계약", "ma", "최대주주 바뀌는 주식 매매 계약", ""),
    (r"공개매수신고서", "ma", "공개매수", ""),
    (r"유상증자결정", "vc", "유상증자(제3자배정)", "piicDecsn"),
    (r"증권신고서\(지분증권\)", "ipo", "상장 공모(증권신고서)", ""),
]
