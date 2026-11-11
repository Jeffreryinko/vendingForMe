/* 딜 '투자 교실' 그림 자료 — 역사 사진 이름(위키백과 문서)과 코스 카드 만화 대본. 사람이 써 둔 것(로봇·토큰 0).
   사진은 사람 얼굴·회사 로고 대신 장소·물건으로 골랐어요. 만화 표정: n보통 s웃음 o놀람 t생각 a화남 d시무룩 w윙크 */
window.VFM_PICS = {
  "world:0": "en:Dutch East India Company", "world:1": "en:Tulip mania", "world:2": "en:South Sea Company", "world:3": "en:New York Stock Exchange Building", "world:4": "en:Harvard Business School", "world:5": "en:Wall Street", "world:6": "en:Nasdaq MarketSite", "world:7": "en:Subprime mortgage crisis", "world:8": "en:Unicorn", "world:9": "en:Eccles Building", "world:10": "en:Winter", "world:11": "en:Graphics processing unit",
  "us:0": "en:Buttonwood Agreement", "us:1": "en:Steel mill", "us:2": "en:Transistor", "us:3": "en:Sand Hill Road", "us:4": "en:Piggy bank", "us:5": "en:Apple II", "us:6": "en:Biscuit", "us:7": "en:Web browser", "us:8": "en:Googleplex", "us:9": "en:Instant camera", "us:10": "en:Coworking", "us:11": "en:Cheque", "us:12": "en:Bank run",
  "eu:0": "en:Amsterdam Stock Exchange", "eu:1": "en:Waddesdon Manor", "eu:2": "en:Stock certificate", "eu:3": "en:London Stock Exchange", "eu:4": "en:Euro banknotes", "eu:5": "en:Mobile phone", "eu:6": "en:Webcam", "eu:7": "en:European Central Bank", "eu:8": "en:Central processing unit", "eu:9": "en:Headphones", "eu:10": "en:Shopping cart",
  "jp:0": "en:Tokyo Stock Exchange", "jp:1": "en:Marunouchi", "jp:2": "en:Plaza Hotel", "jp:3": "en:Ginza", "jp:4": "en:Shibuya", "jp:5": "en:Hangzhou", "jp:6": "en:Board of directors", "jp:7": "en:Roppongi", "jp:8": "en:Medication", "jp:9": "en:Laptop", "jp:10": "en:Nikkei 225",
  "cn:0": "en:Shenzhen", "cn:1": "en:Shanghai Stock Exchange", "cn:2": "en:Cayman Islands", "cn:3": "en:Penguin", "cn:4": "en:New York Stock Exchange", "cn:5": "en:Lujiazui", "cn:6": "en:Shanghai Tower", "cn:7": "en:QR code", "cn:8": "en:Zhongguancun", "cn:9": "en:Integrated circuit",
  "kr:0": "en:Korea Exchange", "kr:1": "en:Blast furnace", "kr:2": "en:Gangnam District", "kr:3": "en:Ticker tape", "kr:4": "en:International Monetary Fund", "kr:5": "en:Dot-com bubble", "kr:6": "en:Bank vault", "kr:7": "en:Pangyo Techno Valley", "kr:8": "en:Smartphone", "kr:9": "en:Food delivery", "kr:10": "en:Cardboard box", "kr:11": "en:Electric vehicle battery"
};
window.VFM_CARDCM = window.VFM_ART.cms({
  "c2:2": ["2021년|me:s:우리 회사 가치 1조 원! 유니콘이다!|you:s:축하해요!", "2023년|you:n:이번엔 6천억으로 쳐 드릴게요.|me:d:지난번보다 낮네… 다운 라운드.", "뜻|me:t:기존 주주 조각이 크게 묽어져요.|you:t:분위기가 안 좋다는 신호군요."],
  "c2:4": ["징검다리|you:t:시드 다음이 바로 A 아니에요?|me:n:그 사이에 '프리 A', 버티는 돈 '브릿지'가 있어요.", "팁스|me:s:투자사가 고르면 정부가 연구비를 얹어 줘요.|you:o:좋은 제도네요.", "후속 투자|me:w:넣었던 곳이 또 넣었다 = 안을 아는 사람이 다시 걸었다.|you:s:좋은 신호!"],
  "c2:5": ["한 라운드|me:n:투자자 다섯이 같이 들어와요.|you:t:조건은 누가 정해요?", "리드|me:s:가장 크게 넣는 '리드 투자자'가 정해요.|you:n:", "영어 기사|you:o:'led by ○○'가 그 뜻이군요!|me:w:유명한 곳이면 그 자체가 뉴스예요."],
  "c3:4": ["SI|me:s:우리 사업에 딱 필요해. 비싸도 살게!|you:o:", "FI|me:t:얼마에 사서 얼마에 팔 수 있지? 깎아 주세요.|you:n:", "기사에서|you:t:'SI 참전'은요?|me:n:같은 업종 기업이 인수전에 뛰어들었다는 뜻."],
  "c3:5": ["나라의 저금통|me:n:국부펀드. 석유 판 돈, 수출로 번 돈.|you:o:규모가 엄청나겠네요.", "노후 자금|me:n:연기금. 국민연금 같은 곳.|you:t:", "큰손이 지갑을 닫으면|me:d:전 세계 투자 분위기가 식어요.|you:o:"],
  "c4:5": ["대기업|me:t:이 사업부는 우리랑 안 맞아. 떼어 내자.|you:n:", "두 길|me:n:독립시키면 분할, 남에게 팔면 카브아웃.|you:t:누가 사요?", "단골 손님|me:w:대개 사모펀드가 줄 서 있어요.|you:s:"],
  "c5:3": ["상장사의 고민|you:d:분기마다 성적표 내느라 길게 못 봐요.|me:t:", "사모펀드|me:s:주식을 다 사서 비상장으로 만들게요.|you:o:공개매수!", "그다음|me:n:조용히 몇 년 고쳐서 다시 팔아요.|you:t:"],
  "c5:4": ["나가는 문 셋|me:n:기업에 팔기, 다른 펀드에 팔기, 다시 상장.|you:t:", "안 팔리면|me:d:만기를 넘겨 들고 있어야 해요.|you:n:'매각 지연' 기사가 그거군요.", "행동주의|me:a:지분 조금 샀으니 경영을 바꾸세요!|you:o:통째로 안 사고 목소리만?"],
  "c6:0": ["상장 전|me:n:회원만 조각을 살 수 있는 가게.|you:d:나도 사고 싶은데…", "상장 날|me:s:시장에 좌판을 폈어요. 누구나 사세요!|you:s:", "대신|me:t:분기마다 성적표, 매일 주가로 평가.|you:o:"],
  "c6:2": ["수요예측|me:n:얼마에 얼마나 사실래요?|you:s:3만 원에 100주요!", "공모가|me:s:인기가 많네. 희망 범위 맨 위로 확정!|you:o:'상단 확정'!", "첫날|you:s:올랐다!|me:w:내리면 '공모가 하회'."],
  "c6:3": ["상장 첫날|you:s:나 초기 투자자인데 이제 팔아야지!|me:n:아직 못 팔아요. 자물쇠(보호예수).", "몇 달 뒤|me:n:자물쇠가 풀려요.|you:s:이제 판다!", "그날|me:d:물량이 쏟아지면 주가가 흔들려요.|you:t:'오버행 우려'가 이거군요."],
  "c6:4": ["스팩|me:n:돈만 든 껍데기 회사가 먼저 상장해요.|you:t:그다음에요?", "합치기|me:s:진짜 회사와 합쳐요. 그 회사도 상장 완료!|you:o:뒷문이네요.", "주의|me:w:'S-1 제출'은 시작했다는 뜻. 상장한 게 아니에요.|you:n:"],
  "c6:5": ["상장 뒤에도|me:n:새 주식을 찍어 돈을 더 받아요. 유상증자.|you:t:", "누구에게|me:n:정한 사람에게만 팔면 '제3자배정'.|you:o:공시에 자주 보이던 말!", "전환사채|me:w:빚인데 나중에 주식으로 바꿀 수 있어요.|you:t:"],
  "c7:2": ["PER 30배|you:t:비싼 거예요?|me:n:지금 이익이 30년 이어져야 본전이라는 뜻.", "높다는 건|me:s:앞으로 훨씬 더 벌 거란 기대.|you:t:", "견주기|me:w:같은 업종끼리만. 소프트웨어는 높고 제조업은 낮아요.|you:s:"],
  "c7:3": ["헬스장|me:n:회원이 매달 회비를 내요.|you:t:", "두 헬스장|me:s:여긴 회원이 안 빠져요.|you:d:여긴 석 달이면 반이 나가요.", "구독 회사도|me:w:안 빠지는 쪽이 훨씬 값져요. 이탈률!|you:s:"],
  "c8:2": ["제목|you:o:'최대 1조 원 투자'!|me:t:'최대'는 조건이 다 맞을 때의 상한.", "또 하나|you:n:'1조 가치로 500억 유치'|me:n:받은 돈은 500억이에요.", "달러 기사|me:w:10억 달러는 1조 원이 넘어요.|you:o:"],
  "c8:3": ["20억 원 투자|you:t:큰 거예요, 작은 거예요?|me:t:견줄 자가 있어야 알아요.", "자 대 보기|me:n:한국 시드에선 큰 편, 미국 시드에선 보통.|you:o:같은 20억인데!", "그래서|me:s:같은 단계, 같은 나라의 보통과 견줘요.|you:s:"],
  "c8:4": ["질문 1|me:n:돈이 어디서 와서 어디로 갔나?|you:t:회사로? 기존 주주에게?", "질문 2|me:n:누가 이득을 보나?|you:t:", "질문 3|me:w:다음에 무슨 일이 생기나?|you:s:하루 한 건씩 적어 볼게요."]
});
