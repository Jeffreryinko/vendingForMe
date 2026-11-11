/* 시사 '세상 읽기 교실' 그림 자료 — 역사 사진 이름(위키백과 문서)과 코스 카드 만화 대본. 사람이 써 둔 것(로봇·토큰 0).
   사진은 사람 얼굴 대신 장소·물건·지도로 골랐어요. 만화 표정: n보통 s웃음 o놀람 t생각 a화남 d시무룩 w윙크 */
window.VFM_PICS = {
  "world:0": "en:Trench warfare", "world:1": "en:Wall Street crash of 1929", "world:2": "en:Normandy landings", "world:3": "en:Headquarters of the United Nations", "world:4": "en:Berlin Wall", "world:5": "en:1973 oil crisis", "world:6": "en:Fall of the Berlin Wall", "world:7": "en:National September 11 Memorial & Museum", "world:8": "en:New York Stock Exchange", "world:9": "en:Surgical mask", "world:10": "en:Kyiv", "world:11": "en:Globe",
  "us:0": "en:Independence Hall", "us:1": "en:Gettysburg Battlefield", "us:2": "en:Hoover Dam", "us:3": "en:The Pentagon", "us:4": "en:Lincoln Memorial", "us:5": "en:United States Capitol", "us:6": "en:Kabul", "us:7": "en:Wall Street", "us:8": "en:White House", "us:9": "en:Container ship",
  "eu:0": "en:Peace of Westphalia", "eu:1": "en:Storming of the Bastille", "eu:2": "en:Zollverein Coal Mine Industrial Complex", "eu:3": "en:Brandenburg Gate", "eu:4": "en:Euro", "eu:5": "en:Acropolis of Athens", "eu:6": "en:Lesbos", "eu:7": "en:Palace of Westminster", "eu:8": "en:Nord Stream 1",
  "ru:0": "en:Winter Palace", "ru:1": "en:Reichstag building", "ru:2": "en:Moscow Kremlin", "ru:3": "en:Budapest", "ru:4": "en:Saint Basil's Cathedral", "ru:5": "en:Crimean Bridge", "ru:6": "en:Maidan Nezalezhnosti", "ru:7": "en:Russian ruble",
  "me:0": "en:Hagia Sophia", "me:1": "en:Jerusalem", "me:2": "en:Golan Heights", "me:3": "en:Azadi Tower", "me:4": "en:Oslo", "me:5": "en:Baghdad", "me:6": "en:Tahrir Square", "me:7": "en:Gas centrifuge", "me:8": "en:Abu Dhabi", "me:9": "en:Gaza Strip",
  "cn:0": "en:Old Summer Palace", "cn:1": "en:Taiwan Strait", "cn:2": "en:Yalu River", "cn:3": "en:Big-character poster", "cn:4": "en:Table tennis", "cn:5": "en:Shenzhen", "cn:6": "en:Tiananmen Square", "cn:7": "en:Port of Shanghai", "cn:8": "en:Great Hall of the People", "cn:9": "en:Semiconductor device fabrication",
  "jp:0": "en:Meiji Shrine", "jp:1": "en:Hiroshima Peace Memorial", "jp:2": "en:National Diet Building", "jp:3": "en:Tokyo Tower", "jp:4": "en:Korea Strait", "jp:5": "en:Tokyo Stock Exchange", "jp:6": "en:Fukushima Daiichi Nuclear Power Plant", "jp:7": "en:Bank of Japan", "jp:8": "en:Japanese yen",
  "kr:0": "en:Korean Demilitarized Zone", "kr:1": "en:War Memorial of Korea", "kr:2": "en:Gyeongbu Expressway", "kr:3": "en:May 18th National Cemetery", "kr:4": "en:Myeongdong Cathedral", "kr:5": "en:Bank of Korea", "kr:6": "en:Joint Security Area", "kr:7": "en:Gwanghwamun", "kr:8": "en:National Assembly Proceeding Hall"
};
window.VFM_CARDCM = window.VFM_ART.cms({
  "s1:2": ["기사 A|me:n:'정부 고위 관계자에 따르면…'|you:t:누군지는 안 나오네요.", "기사 B|me:n:'대변인이 브리핑에서 밝혔다.'|you:s:이건 이름 걸고 한 말이네요.", "읽는 법|me:w:이름 없는 말은 한 단계 낮춰 믿어요.|you:s:"],
  "s1:3": ["같은 법안|me:a:세금 폭탄이다!|you:s:공정 과세다!", "어리둥절|you:o:둘이 같은 얘기를 하는 거예요?|me:t:낱말이 인상을 바꿔요. 프레임이에요.", "그래서|me:s:창문 두 개로 보면 덜 속아요.|you:s:"],
  "s2:3": ["1단계 국회|me:n:탄핵 소추안 가결! (3분의 2)|you:o:그럼 바로 물러나요?", "아직|me:n:직무만 멈춰요. 결론은 헌법재판소가 내요.|you:t:", "2단계 헌재|me:n:6명 이상 찬성이면 파면, 아니면 복귀.|you:s:국회가 기소, 헌재가 판결이네요."],
  "s2:4": ["기사 제목|you:o:'징역 10년 구형'! 10년 사는 거예요?|me:n:아니요. 그건 검사의 요청이에요.", "판사의 결론|me:n:'징역 5년 선고'. 이게 판사가 정한 거예요.|you:t:그럼 끝?", "세 번까지|me:w:1심, 2심, 대법원. '확정'이 진짜 끝.|you:s:"],
  "s2:5": ["미국 대선|you:t:표를 더 많이 받으면 이기는 거죠?|me:n:주마다 걸린 선거인단을 따요. 538명 중 270명.", "그래서|me:n:늘 엎치락뒤치락하는 몇 개 주가 승부를 갈라요.|you:o:경합주!", "의회는|me:s:상원 100명, 하원 435명. 법은 둘 다 통과해야 해요.|you:s:"],
  "s3:1": ["장바구니|you:d:작년엔 5만 원이었는데 올해는 5만 5천 원…|me:n:그게 인플레이션이에요.", "반대로|you:s:값이 계속 내리면 좋잖아요?|me:t:다들 '내일 사야지' 해서 경제가 식어요. 디플레이션.", "목표|me:s:그래서 중앙은행은 연 2%쯤을 노려요.|you:s:"],
  "s3:3": ["미국이 금리를 올리면|me:n:돈이 이자 많이 주는 미국으로 몰려요.|you:t:우리랑 무슨 상관이죠?", "환율|me:n:원화 값이 떨어져요. 수입품이 비싸져요.|you:o:기름값, 밀가루값!", "그래서|me:s:한국은행도 따라 올리거나 못 내려요.|you:d:내 대출 이자…"],
  "s3:4": ["나라 가계부|me:n:번 돈(세금)보다 쓴 돈이 많으면 적자.|you:t:모자라면요?", "빌리기|me:n:국채를 찍어 빌려요. 쌓이면 국가 채무.|you:o:못 갚으면?", "디폴트|me:d:부도예요. 그 전에 이자가 치솟아요.|you:t:결국 누가 내고 누가 받느냐의 다툼이네요."],
  "s4:3": ["물건 하나|me:n:설계는 미국, 칩은 대만, 조립은 베트남.|you:s:싸게 만들 수 있네요.", "한 고리가 막히면|me:d:공장 한 곳이 멈추니 전부 멈췄어요.|you:o:코로나 때 그랬죠.", "바뀐 생각|me:t:이제는 '싼 곳'보다 '믿을 수 있는 곳'.|you:s:"],
  "s4:4": ["달러가 바닥|me:d:외국 돈이 떨어져 수입도, 빚 갚기도 못 해요.|you:o:", "IMF|you:n:빌려줄게요. 대신 조건이 있어요.|me:t:구조조정, 금리 인상, 시장 개방…", "한국도|me:n:1997년에 이 길을 지났어요.|you:t:"],
  "s5:2": ["동맹|me:n:네가 공격받으면 내가 도울게. 조약으로 약속!|you:s:든든해요.", "값이 있어요|me:t:대신 방위비는 누가 얼마나 낼까?|you:d:늘 그게 문제네요.", "공동성명|me:w:무엇이 빠졌는지도 뉴스예요.|you:o:"],
  "s5:3": ["나라 사이의 법|you:t:어기면 누가 잡아가요?|me:d:세계 경찰이 없어요.", "두 재판소|me:n:ICC는 '사람'을, ICJ는 '나라 사이 다툼'을 다뤄요.|you:t:", "그래도|me:s:'누가 규칙을 어겼나'의 기준이 돼요.|you:s:제재와 여론의 근거군요."],
  "s5:4": ["두 나라|me:a:관세! 반도체 통제!|you:a:희토류 통제!", "그런데|me:t:서로가 가장 큰 손님이기도 해요.|you:t:끊기도 어렵고 붙어 있기도 불편…", "한국은|me:d:안보는 미국, 무역은 중국.|you:o:늘 선택을 요구받겠네요."],
  "s6:1": ["핵을 가진 두 나라|me:a:쏘면 나도 쏜다.|you:a:나도.", "그래서|me:t:둘 다 끝나니 직접은 안 싸워요. 억지.|you:t:", "대신|me:n:다른 나라를 지원해 싸우게 해요. 대리전.|you:d:"],
  "s6:2": ["NPT의 약속|me:n:다섯 나라만 핵무기 인정. 나머지는 안 갖기.|you:t:대신 뭘 받아요?", "받는 것|me:s:원자력을 평화적으로 쓸 권리. 감시는 IAEA.|you:n:", "숫자 읽기|me:n:발전용은 농축 3~5%, 무기급은 약 90%.|you:o:60%면 꽤 가까운 거네요."],
  "s6:3": ["전쟁에도 규칙|me:n:민간인을 일부러 공격하면 전쟁범죄예요.|you:t:", "기사 읽기|you:n:'집단학살이라고 주장했다'|me:w:'주장'인지 법원이 '인정'했는지 보세요.", "숫자 뒤에|me:d:난민 100만 명. 한 명 한 명이 사람이에요.|you:d:"],
  "s6:4": ["질문 1|me:n:누가 말했나? 양쪽 다 유리하게 발표해요.|you:t:", "질문 2|me:n:지도에서 어디인가?|you:o:찾아보니 기사가 달리 읽혀요.", "질문 3|me:w:누가 뒤에서 무기와 돈을 대나?|you:s:구도가 보이네요."],
  "s7:1": ["산유국 모임|me:n:생산을 줄이자. (감산)|you:d:기름값이 오르겠네요.", "좁은 길목|me:o:호르무즈 해협이 막혔다!|you:o:값이 뛰어요!", "달라진 점|me:s:미국은 셰일로 세계 최대 산유국이 됐어요.|you:t:중동에 덜 매이겠네요."],
  "s7:2": ["전쟁 전|you:s:러시아 가스관으로 싸게 받아요.|me:n:", "전쟁 뒤|you:d:끊었어요. 배로 오는 LNG는 비싸요…|me:t:공장들이 힘들어졌죠.", "교훈|me:n:에너지를 누구에게서 사느냐가 안보예요.|you:n:"],
  "s7:3": ["파리협정|me:s:기온 상승을 1.5~2도 안으로 막자!|you:s:좋아요!", "그런데|me:a:부자 나라가 더 줄여야지!|you:a:돈은 누가 대고?", "늘 같은 쟁점|me:t:누가 줄이나, 누가 내나, 안 지키면?|you:t:"],
  "s7:4": ["해가 지면|you:d:태양광이 멈췄어요…|me:n:그래서 배터리와 튼튼한 전력망이 같이 필요해요.", "원자력|me:t:탄소는 거의 안 나오지만 사고와 폐기물이 숙제.|you:t:", "새 변수|me:o:AI 데이터센터가 전기를 엄청 써요.|you:o:전기를 어디서 구하죠?"],
  "s8:1": ["예전 무역 다툼|me:n:관세로 값을 비싸게.|you:n:", "지금|me:a:첨단 칩과 장비를 아예 안 팔아!|you:a:그럼 희토류를 조이지!", "달라진 점|me:t:'값'이 아니라 '못 만들게' 하는 싸움.|you:o:"],
  "s8:2": ["AI에 필요한 셋|me:n:칩, 전기, 데이터.|you:t:", "규칙은 제각각|me:n:EU는 위험도에 따라 규제, 미국은 기업 자율.|you:t:", "소버린 AI|you:s:우리 것을 갖겠다는 말이군요.|me:s:"],
  "s8:3": ["웬만한 나라보다 큰 회사|you:o:빅테크가 그렇게 커요?|me:n:그래서 나라들이 규칙을 만들어요.", "세 가지|me:n:독점 깨기, 개인정보 지키기, 플랫폼 책임.|you:t:", "그러다|me:t:유럽 규제가 미국과 무역 갈등이 되기도 해요.|you:o:"],
  "s8:4": ["총 없이|me:o:병원 전산이 멈췄다!|you:o:누가 했죠?", "어려운 점|me:d:누가 했는지 밝히기 어려워요.|you:t:보복도 어렵겠네요.", "새 전략 시설|me:n:해저 케이블, 위성, 데이터센터.|you:t:'이게 왜 안보 문제지?'를 물어볼게요."]
});
