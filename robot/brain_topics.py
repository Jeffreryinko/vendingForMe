"""brain_topics.py — 뇌 탭 '유명한 실험·사례' 목록 (Claude가 고름). brain_cases.py 가 한 줄씩 카드로 씀.
한 줄 = (주제 갈래, 한국어 이름, 영어 위키백과 문서 제목 — 없으면 "")
이미 손으로 쓴 44장(vfm-story/brain/exp.js · exp-2.js)과 겹치는 것은 넣지 않았어요.
"""
T = []
def add(ch, rows):
    for r in rows: T.append((ch, r[0], r[1] if len(r) > 1 else ""))

add("기억", [
 ("에빙하우스의 망각 곡선", "Forgetting curve"), ("간격 반복 효과", "Spacing effect"), ("시험 효과 (인출 연습)", "Testing effect"),
 ("밀러의 마법의 숫자 7±2", "The Magical Number Seven, Plus or Minus Two"), ("작업 기억 모형 (배들리·히치)", "Baddeley's model of working memory"),
 ("처리 수준 이론 (크레이크·록하트)", "Levels of processing model"), ("맥락 의존 기억: 물속 잠수부 실험", "Context-dependent memory"),
 ("상태 의존 기억", "State-dependent memory"), ("섬광 기억: 챌린저호 폭발 기억 연구", "Flashbulb memory"),
 ("DRM 거짓 기억 실험 (단어 목록)", "Deese–Roediger–McDermott paradigm"), ("오정보 효과", "Misinformation effect"),
 ("기억술사 S. (셰레솁스키)", "Solomon Shereshevsky"), ("과잉기억증후군 (질 프라이스)", "Hyperthymesia"),
 ("서번트 킴 피크", "Kim Peek"), ("서번트 스티븐 윌트셔", "Stephen Wiltshire"), ("기억의 궁전 (장소법)", "Method of loci"),
 ("세계 기억력 대회와 조슈아 포어", "Moonwalking with Einstein"), ("계열 위치 효과 (처음·끝이 잘 기억됨)", "Serial-position effect"),
 ("자이가르닉 효과 (끝내지 못한 일)", "Zeigarnik effect"), ("혀끝에서 맴도는 현상", "Tip of the tongue"),
 ("기억 재공고화 (네이더의 쥐)", "Memory reconsolidation"), ("프로프라놀롤과 공포 기억 지우기", "Propranolol"),
 ("코르사코프 증후군", "Korsakoff syndrome"), ("해리성 둔주", "Dissociative fugue"), ("일과성 전기억상실", "Transient global amnesia"),
 ("유아 기억상실", "Childhood amnesia"), ("구글 효과 (디지털 기억상실)", "Google effect"), ("사진 찍기 손상 효과", "Photo-taking impairment effect"),
 ("생성 효과", "Generation effect"), ("그림 우월 효과", "Picture superiority effect"), ("자기 참조 효과", "Self-reference effect"),
 ("바틀릿의 '유령들의 전쟁' 기억 실험", "Frederic Bartlett"), ("HM 이후의 해마 환자 EP", ""), ("정보의 덩어리화 (청킹)", "Chunking (psychology)"),
 ("기억 흔적 세포 (도네가와의 쥐)", "Engram (neuropsychology)"), ("광유전학으로 거짓 기억 심기 (2013)", "Optogenetics"),
 ("목격자 지목과 라인업 연구", "Eyewitness identification"), ("로널드 코튼 오판 사건", "Ronald Cotton"), ("기억 왜곡: 존 딘의 워터게이트 증언", "John Dean"),
 ("데자뷔 연구", "Déjà vu"),
])
add("주의와 지각", [
 ("칵테일파티 효과", "Cocktail party effect"), ("체리의 양쪽 귀 듣기 실험", "Dichotic listening"), ("주의 깜빡임", "Attentional blink"),
 ("시각 탐색과 특징 통합 이론 (트리스먼)", "Feature integration theory"), ("포스너의 단서 주기 과제", "Posner cueing task"),
 ("반측 공간 무시", "Hemispatial neglect"), ("동시 실인증", "Simultanagnosia"), ("운동맹 (움직임을 못 보는 환자 LM)", "Akinetopsia"),
 ("뇌성 색맹", "Cerebral achromatopsia"), ("시각 실인증과 '아내를 모자로 착각한 남자'", "The Man Who Mistook His Wife for a Hat"),
 ("뮐러-라이어 착시와 문화 차이", "Müller-Lyer illusion"), ("체커 그림자 착시", "Checker shadow illusion"), ("드레스 색깔 논쟁 (2015)", "The dress"),
 ("야니·로렐 소리 논쟁", "Yanny or Laurel"), ("에임스 방", "Ames room"), ("달 착시", "Moon illusion"), ("속이 빈 얼굴 착시", "Hollow-Face illusion"),
 ("공감각", "Synesthesia"), ("맛 공감각자 '모양 있는 맛' (사이토윅)", "Richard Cytowic"), ("맥거크와 다른 감각 통합: 이중 섬광 착시", "Sound-induced flash illusion"),
 ("색의 범주와 언어 (러시아어 파랑)", "Linguistic relativity and the color naming debate"), ("음악 착각: 셰퍼드 음", "Shepard tone"),
 ("트라이톤 역설 (도이치)", "Tritone paradox"), ("절대음감", "Absolute pitch"), ("선천성 실음악증", "Amusia"),
 ("시각 피질의 재배치: 점자 읽는 맹인의 시각 피질", "Neuroplasticity"), ("반향정위로 보는 맹인 대니얼 키시", "Daniel Kish"),
 ("감각 대체: 혀로 보는 장치 (바크-이-리타)", "Paul Bach-y-Rita"), ("시각 회복 후에도 못 보는 사람 (SB 사례)", ""),
 ("몰리뉴 문제와 시력을 찾은 아이들 (프로젝트 프라카시)", "Molyneux's problem"), ("거꾸로 보는 안경 실험 (스트래턴)", "George M. Stratton"),
 ("주의력 착각: 휴대전화와 운전", "Mobile phones and driving safety"), ("멀티태스킹의 대가 (헤비 멀티태스커 연구)", "Human multitasking"),
 ("플린 효과", "Flynn effect"), ("시간 지각과 위험한 순간 (번지 낙하 실험)", "Time perception"), ("마감 시간이 다가오면 느려지는 시간", ""),
 ("이명", "Tinnitus"), ("통증 관문 이론", "Gate control theory"), ("선천성 무통각증", "Congenital insensitivity to pain"),
 ("가려움의 신경과학", "Itch"), ("냄새와 기억 (프루스트 현상)", "Involuntary memory"), ("후각 상실과 코로나19", "Anosmia"),
 ("페로몬 논쟁과 땀 티셔츠 실험", "Major histocompatibility complex and sexual selection"), ("맛 지도는 틀렸다", "Tongue map"),
 ("미각과 기대: 와인 전문가 속이기 (색 입힌 화이트와인)", ""), ("가격이 맛을 바꾼다 (와인 가격 fMRI)", ""),
 ("변화맹: 비행기 사진 깜빡임 과제", "Change blindness"), ("부주의 맹시: 숫자 세다 놓친 광대", "Inattentional blindness"),
 ("전문 방사선과 의사도 놓친 고릴라", ""), ("얼굴 파레이돌리아", "Pareidolia"),
])
add("감정과 판단", [
 ("카너먼의 시스템 1과 2", "Thinking, Fast and Slow"), ("기준점 효과 (닻 내림)", "Anchoring effect"), ("가용성 휴리스틱", "Availability heuristic"),
 ("린다 문제 (결합 오류)", "Conjunction fallacy"), ("틀 짓기 효과: 아시아 질병 문제", "Framing effect (psychology)"), ("손실 회피", "Loss aversion"),
 ("보유 효과 (머그컵 실험)", "Endowment effect"), ("전망 이론", "Prospect theory"), ("매몰 비용 오류", "Sunk cost"),
 ("현재 편향과 쌍곡형 할인", "Hyperbolic discounting"), ("선택의 역설: 잼 24종 실험", "The Paradox of Choice"), ("디폴트 효과: 장기 기증 동의", "Default effect"),
 ("넛지와 학교 급식", "Nudge theory"), ("최후통첩 게임", "Ultimatum game"), ("독재자 게임", "Dictator game"), ("죄수의 딜레마와 액설로드 대회", "Tit for tat"),
 ("공공재 게임과 처벌", "Public goods game"), ("과신 효과", "Overconfidence effect"), ("더닝-크루거 효과", "Dunning–Kruger effect"),
 ("계획 오류: 시드니 오페라하우스", "Planning fallacy"), ("사후 확신 편향", "Hindsight bias"), ("확증 편향: 웨이슨 카드 과제", "Wason selection task"),
 ("2-4-6 과제", ""), ("기저율 무시: 택시 문제", "Base rate fallacy"), ("도박사의 오류", "Gambler's fallacy"), ("핫핸드 논쟁의 반전", "Hot hand"),
 ("후광 효과", "Halo effect"), ("단순 노출 효과", "Mere-exposure effect"), ("피크엔드 법칙: 대장 내시경 연구", "Peak–end rule"),
 ("정서 예측 오류: 복권 당첨자와 사고 환자", "Affective forecasting"), ("쾌락 적응", "Hedonic treadmill"), ("이케아 효과", "IKEA effect"),
 ("의사 결정 피로: 가석방 판사 연구와 반론", "Decision fatigue"), ("트롤리 딜레마와 뇌", "Trolley problem"), ("도덕적 말문 막힘 (하이트)", "Moral dumbfounding"),
 ("혐오와 도덕 판단", ""), ("감정의 두 요인 이론: 흔들다리 실험", "Two-factor theory of emotion"), ("샥터·싱어 아드레날린 실험", ""),
 ("얼굴 표정의 보편성 (에크먼)", "Paul Ekman"), ("구성된 감정 이론 (배럿)", "Theory of constructed emotion"), ("감정 명명의 진정 효과", "Affect labeling"),
 ("편도체 없는 여자 S.M.", "S.M. (patient)"), ("위르바흐-비테 병", "Urbach–Wiethe disease"), ("웃음의 전염", "Contagious laughter"),
 ("사이코패스의 뇌 (제임스 팰런)", "James Fallon"), ("휘트먼 사건과 뇌종양", "Charles Whitman"), ("소아성애로 변한 남자와 뇌종양 (2003)", ""),
 ("마음 이론과 샐리-앤 과제", "Sally–Anne test"), ("직관 대 분석: 인지 반사 테스트", "Cognitive reflection test"),
])
add("사회 속의 뇌", [
 ("로버스 동굴 실험", "Realistic conflict theory"), ("최소 집단 패러다임 (타지펠)", "Minimal group paradigm"), ("파란 눈 갈색 눈 수업 (제인 엘리엇)", "Jane Elliott"),
 ("제3의 물결 실험", "The Third Wave (experiment)"), ("좋은 사마리아인 실험 (서두름)", ""), ("사회적 태만: 링겔만 효과", "Ringelmann effect"),
 ("사회적 촉진 (트리플렛 자전거)", "Social facilitation"), ("집단 극화", "Group polarization"), ("집단 사고: 피그만 침공", "Groupthink"),
 ("문간에 발 들여놓기", "Foot-in-the-door technique"), ("면전에서 문 닫기", "Door-in-the-face technique"), ("상호성: 크리스마스 카드 실험", "Reciprocity (social psychology)"),
 ("치알디니의 수건 재사용 실험", "Social proof"), ("벤저민 프랭클린 효과", "Ben Franklin effect"), ("근접성: 기숙사 우정 연구 (페스팅거)", "Propinquity"),
 ("36가지 질문으로 사랑에 빠지기", "The 36 Questions That Lead to Love"), ("얇게 썰어 보기: 30초 강의 평가", "Thin-slicing"),
 ("실험자 기대: 영리한 한스", "Clever Hans"), ("피그말리온 효과 (로젠탈)", "Pygmalion effect"), ("고정관념 위협", "Stereotype threat"),
 ("암묵적 연합 검사 논쟁", "Implicit-association test"), ("근본적 귀인 오류: 카스트로 에세이", "Fundamental attribution error"),
 ("거짓 합의 효과: 샌드위치 광고판", "False consensus effect"), ("스포트라이트 효과: 배리 매닐로 티셔츠", "Spotlight effect"),
 ("투명성 착각", "Illusion of transparency"), ("사회적 배제와 사이버볼", "Social rejection"), ("사회적 고통과 타이레놀 연구", ""),
 ("옥시토신 신뢰 게임 논쟁", "Oxytocin"), ("공감의 뇌: 사랑하는 사람이 아플 때 (싱어)", "Tania Singer"),
 ("거울 자기 인식 검사", "Mirror test"), ("눈 그림만 있어도 정직해진다 (정직 상자)", "Watching-eye effect"), ("익명성과 몰개성화: 할로윈 아이들", "Deindividuation"),
 ("방관자 효과의 메타분석", "Bystander effect"), ("영웅적 행동 연구", ""), ("던바의 수", "Dunbar's number"), ("작은 세상 실험 (밀그램 편지)", "Small-world experiment"),
 ("감정의 전염: 페이스북 실험 (2014)", "Emotional contagion"), ("행복은 전염된다 (프레이밍햄 연구)", "Framingham Heart Study"),
 ("외로움과 건강", "Loneliness"), ("하버드 성인 발달 연구", "Grant Study"), ("돈으로 행복 사기: 남에게 쓰기", ""),
 ("부의 착각: 모노폴리 게임 실험", "Paul Piff"), ("정의로운 세상 믿음", "Just-world hypothesis"), ("세일럼 마녀재판과 집단 히스테리", "Salem witch trials"),
 ("탕가니카 웃음병 (1962)", "Tanganyika laughter epidemic"), ("1518년 춤 전염병", "Dancing plague of 1518"), ("확증과 사이비 종교: 예언이 빗나갔을 때", "When Prophecy Fails"),
 ("인질과 스톡홀름 증후군", "Stockholm syndrome"), ("BBC 감옥 실험 (2002)", "BBC Prison Study"),
])
add("학습과 두려움", [
 ("파블로프의 조건 반사", "Classical conditioning"), ("손다이크의 문제 상자", "Law of effect"), ("스키너 상자와 강화 계획", "Operant conditioning chamber"),
 ("비둘기의 미신 행동 (스키너)", ""), ("가르시아 효과: 맛 혐오 학습", "Conditioned taste aversion"), ("톨먼의 쥐와 인지 지도", "Cognitive map"),
 ("잠재 학습", "Latent learning"), ("통찰 학습: 쾰러의 침팬지", "Wolfgang Köhler"), ("각인: 로렌츠의 거위", "Imprinting (psychology)"),
 ("준비된 공포: 원숭이와 뱀", ""), ("노출 치료와 공포 소거", "Exposure therapy"), ("체계적 둔감화", "Systematic desensitization"),
 ("PTSD와 해마 크기 (쌍둥이 연구)", "Posttraumatic stress disorder"), ("공포의 두 길 (르두)", "Joseph LeDoux"), ("깜짝 놀람 반사와 공포", "Startle response"),
 ("마인드셋 연구 (드웩)와 재현 논쟁", "Mindset"), ("칭찬의 역설: 노력 칭찬 vs 재능 칭찬", ""), ("1만 시간과 의도적 연습", "Practice (learning method)"),
 ("교차 연습 (섞어서 연습하기)", "Interleaved practice"), ("바람직한 어려움", "Desirable difficulty"), ("학습 양식(시각형·청각형) 신화", "Learning styles"),
 ("모차르트 효과 신화", "Mozart effect"), ("뇌 훈련 게임 논쟁", "Brain training"), ("수면 중 학습은 가능할까", "Sleep-learning"),
 ("거울 그리기와 운동 학습", ""), ("머릿속 연습 (심상 훈련)", "Motor imagery"), ("저글링을 배우면 뇌가 바뀐다 (2004)", ""),
 ("음악 훈련과 뇌", ""), ("이중 언어와 뇌", "Cognitive effects of bilingualism"), ("벌의 학습과 춤 언어", "Waggle dance"),
])
add("보상과 중독", [
 ("쥐 공원의 반론과 재검토", "Rat Park"), ("니코틴과 측좌핵", "Nicotine"), ("도박 중독과 거의 이길 뻔한 효과", "Near-miss effect"),
 ("슬롯머신과 변동 비율 강화", ""), ("좋아요 버튼과 도파민 논쟁", ""), ("스마트폰 없이 있기 실험", "Nomophobia"),
 ("파킨슨병 약과 갑작스러운 도박 충동", "Impulse control disorder"), ("설탕 중독은 있을까", "Sugar addiction"), ("단맛의 진화", ""),
 ("음식 광고와 아이들 (fMRI)", ""), ("베트남전 귀환병의 헤로인 연구 (로빈스)", "Lee Robins"), ("금연과 건강 습관 형성 66일", "Habit"),
 ("습관 고리 (신호-행동-보상)", "The Power of Habit"), ("뇌심부 자극과 우울증 (메이버그)", "Helen S. Mayberg"), ("케타민과 우울증", "Ketamine"),
 ("실로시빈 치료 연구", "Psilocybin therapy"), ("굿 프라이데이 실험 (1962)", "Marsh Chapel Experiment"), ("LSD와 창의성 연구의 역사", ""),
 ("카페인과 아데노신", "Caffeine"), ("알코올과 블랙아웃", "Blackout (drug-related amnesia)"), ("흡연 광고와 말보로맨", ""),
 ("쇼핑의 뇌: 가격과 고통 (insula)", ""), ("기대와 보상: 크리스마스 선물 연구", ""), ("내재 동기와 보상의 역효과 (데시)", "Overjustification effect"),
 ("상을 주면 그림 그리기가 싫어진다 (레퍼 연구)", ""),
])
add("몸과 나", [
 ("유체 이탈 체험 실험 (가상 현실)", "Out-of-body experience"), ("자기 몸 일부를 남의 것으로 여기는 증상 (신체 망상)", "Somatoparaphrenia"),
 ("팔다리를 잘라내고 싶은 사람들 (신체 통합 정체성 장애)", "Body integrity dysphoria"), ("외계인 손 증후군", "Alien hand syndrome"),
 ("자신의 마비를 부정하는 환자 (질병인식불능증)", "Anosognosia"), ("고유 감각을 잃은 남자 이언 워터먼", "Ian Waterman"),
 ("간지럼은 왜 스스로 못 태울까", "Tickling"), ("내수용 감각과 심장 박동 세기", "Interoception"), ("미주신경과 마음", "Vagus nerve"),
 ("장-뇌 축과 미생물", "Gut–brain axis"), ("운동과 해마 (노인 걷기 연구)", ""), ("운동이 우울증에 미치는 효과", ""),
 ("자세 연구(파워 포즈)의 재현 실패", "Power posing"), ("안면 피드백 가설 (펜 물기)과 재검증", "Facial feedback hypothesis"),
 ("보톡스와 우울감", ""), ("뇌-컴퓨터 인터페이스로 로봇팔 움직이기", "Brain–computer interface"), ("생각으로 글씨 쓰기 (2021)", ""),
 ("마비 환자가 다시 걷다 (척수 자극)", ""), ("인공 와우와 소리를 처음 듣는 순간", "Cochlear implant"), ("인공 망막", "Visual prosthesis"),
 ("팔 이식 환자의 뇌 지도 변화", ""), ("통증과 문화", ""), ("만성 통증과 뇌", "Chronic pain"), ("욕설이 통증을 줄인다 (얼음물 실험)", ""),
 ("공포와 장 (나비가 날아다니는 배)", ""), ("호흡 리듬과 기억", ""), ("배고픔 호르몬 그렐린과 결정", "Ghrelin"),
 ("미네소타 굶주림 실험", "Minnesota Starvation Experiment"), ("체온과 친절 (따뜻한 커피 컵)", ""), ("노화와 뇌: 수녀 연구", "Nun Study"),
])
add("의식", [
 ("마취는 의식을 어떻게 끄나", "General anaesthesia"), ("식물인간 환자와 테니스 상상 (오언, 2006)", "Adrian Owen"),
 ("잠금 증후군과 『잠수종과 나비』", "Locked-in syndrome"), ("임사 체험 연구", "Near-death experience"), ("가수면 상태의 환각", "Hypnagogia"),
 ("최면은 무엇일까", "Hypnosis"), ("명상과 뇌 (승려 연구)", ""), ("마음 방황과 명상", ""), ("자유 의지와 fMRI 예측 (순, 2008)", ""),
 ("통합 정보 이론", "Integrated information theory"), ("전역 작업 공간 이론", "Global workspace theory"), ("의식의 신경 상관물 (크릭·코흐)", "Neural correlates of consciousness"),
 ("양안 경쟁", "Binocular rivalry"), ("마스킹: 보이지 않는 그림의 영향", ""), ("무의식적 지각 광고 (서브리미널) 신화", "Subliminal stimuli"),
 ("자기 인식과 섬엽", ""), ("이인증", "Depersonalization-derealization disorder"), ("코타르 증후군 (내가 죽었다고 믿는 사람)", "Cotard delusion"),
 ("해리성 정체성 장애 논쟁", "Dissociative identity disorder"), ("환각제를 쓰지 않은 환각: 샤를 보네 증후군", "Charles Bonnet syndrome"),
 ("감각 차단 탱크", "Isolation tank"), ("신을 느끼게 하는 헬멧 실험", "God helmet"), ("측두엽 뇌전증과 종교 체험", "Geschwind syndrome"),
 ("우주비행사의 조망 효과", "Overview effect"), ("시간이 멈춘 듯한 몰입", "Flow (psychology)"),
])
add("언어", [
 ("지니 사례 (언어 결정적 시기)", "Genie (feral child)"), ("아베롱의 야생 소년", "Victor of Aveyron"), ("니카라과 수화의 탄생", "Nicaraguan Sign Language"),
 ("침팬지 님 침스키", "Nim Chimpsky"), ("고릴라 코코", "Koko (gorilla)"), ("보노보 칸지", "Kanzi"), ("앵무새 알렉스", "Alex (parrot)"),
 ("보더콜리 체이서의 1,000단어", "Chaser (dog)"), ("부바-키키 효과", "Bouba/kiki effect"), ("사피어-워프 가설과 방향 언어 (구구 이미티르)", "Guugu Yimithirr language"),
 ("피라하어와 수 개념", "Pirahã language"), ("아기는 모든 소리를 듣는다 (쿨)", "Patricia K. Kuhl"), ("통계적 학습: 8개월 아기 실험 (새프런)", "Statistical learning in language acquisition"),
 ("외국어 억양 증후군", "Foreign accent syndrome"), ("실독증: 쓸 수 있는데 못 읽는 사람", "Pure alexia"), ("난독증과 뇌", "Dyslexia"),
 ("말더듬의 뇌", "Stuttering"), ("욕설의 뇌 (투렛 증후군)", "Tourette syndrome"), ("손짓과 생각", ""), ("수어를 쓰는 뇌와 브로카 영역", ""),
 ("독서하는 뇌: 글자 상자 영역 (드앤)", "Visual word form area"), ("어른이 되면 못 듣는 소리: 일본어 화자의 L·R 구별", ""), ("반향어와 자폐", "Echolalia"),
 ("이야기를 들으면 뇌가 동기화된다 (해슨)", ""), ("거짓말하는 뇌와 fMRI 거짓말 탐지 논쟁", "Lie detection"),
])
add("아이와 발달", [
 ("피아제의 보존 실험", "Conservation (psychology)"), ("대상 영속성", "Object permanence"), ("시각 절벽 실험", "Visual cliff"),
 ("낯선 상황 실험 (에인스워스)", "Strange situation"), ("무표정 실험 (트로닉)", "Still face experiment"), ("루마니아 고아원 연구", "Bucharest Early Intervention Project"),
 ("쌍둥이 연구: 따로 자란 쌍둥이 (미네소타)", "Minnesota Twin Family Study"), ("짐 쌍둥이", ""), ("세 쌍둥이 형제의 재회 (Three Identical Strangers)", "Three Identical Strangers"),
 ("데이비드 라이머 사례", "David Reimer"), ("청소년 뇌와 위험 행동", ""), ("거울 앞 루주 검사 (아기의 자기 인식)", ""),
 ("아기의 도덕 감각: 도와주는 인형 실험", ""), ("아기는 공평을 안다", ""), ("마시멜로 이후: 믿을 만한 어른 실험 (2013)", ""),
 ("말하는 단어 수 3천만 격차 논쟁", "Word gap"), ("페리 유치원 프로젝트", "HighScope"), ("놀이의 중요성: 쥐의 놀이 (판크세프)", "Jaak Panksepp"),
 ("기대 위반: 아기는 놀라면 더 오래 본다", "Violation of expectation paradigm"), ("사회적 참조", "Social referencing"), ("모국어 울음 (프랑스 아기와 독일 아기)", ""),
 ("자폐와 백신 논문 조작 사건", "Lancet MMR autism fraud"), ("ADHD와 뇌 성숙 지연 (쇼, 2007)", ""), ("영재와 아인슈타인의 뇌", "Albert Einstein's brain"),
 ("납 중독과 범죄율 가설", "Lead–crime hypothesis"), ("영양과 IQ: 요오드 결핍", ""), ("디지털 기기와 아이의 뇌 논쟁", ""),
 ("오른손잡이·왼손잡이의 뇌", "Handedness"), ("공룡을 좋아하는 아이: 강한 관심의 비밀", ""), ("아이의 거짓말 발달 (뒤돌아보지 마 실험)", ""),
])
add("수면과 꿈", [
 ("수면 박탈 기록: 랜디 가드너 264시간", "Randy Gardner sleep deprivation experiment"), ("치명적 가족성 불면증", "Fatal familial insomnia"),
 ("렘수면의 발견 (1953)", "Rapid eye movement sleep"), ("자각몽 신호 실험", "Lucid dream"), ("꿈 내용 분석 (홀·반 드 캐슬)", ""),
 ("수면 마비와 가위눌림", "Sleep paralysis"), ("몽유병과 수면 중 범죄 (케네스 파크스)", "Sleepwalking"), ("기면증과 오렉신", "Narcolepsy"),
 ("동굴 속 시간 실험 (미셸 시프르)", "Michel Siffre"), ("생체 시계와 노벨상 (초파리)", "Circadian rhythm"), ("사춘기 수면 지연과 등교 시간", ""),
 ("낮잠의 효과 (NASA 낮잠 연구)", "Nap"), ("뇌의 청소 시스템 (글림프)", "Glymphatic system"), ("수면과 감정 기억", ""),
 ("한쪽 뇌만 자는 돌고래", "Unihemispheric slow-wave sleep"), ("잠과 창의성: 멘델레예프와 화학자의 꿈", ""), ("일주기 리듬과 교대 근무", "Shift work"),
 ("수면 부족과 사고 (체르노빌·엑슨 발데즈)", ""), ("야간 불빛과 멜라토닌", "Melatonin"), ("서머타임과 심장마비", ""),
])
add("스트레스와 건강", [
 ("셀리에의 일반 적응 증후군", "General adaptation syndrome"), ("화이트홀 연구 (직급과 건강)", "Whitehall Study"), ("개코원숭이의 스트레스 (새폴스키)", "Robert Sapolsky"),
 ("스트레스는 나쁘다는 믿음 연구", ""), ("어린 시절 역경 경험 연구 (ACE)", "Adverse Childhood Experiences Study"), ("스트레스와 텔로미어", ""),
 ("호텔 청소부 연구 (운동이라는 생각)", ""), ("노화 시계 되돌리기 실험 (랭어)", "Ellen Langer"), ("요양원 화분 실험", ""),
 ("감사 일기 연구", ""), ("글쓰기 치료 (페니베이커)", "James W. Pennebaker"), ("자연 풍경이 있는 병실 (울리히, 1984)", ""),
 ("숲 치유 연구", "Forest bathing"), ("소음과 아이의 읽기 (공항 근처 학교)", ""), ("돈 걱정과 IQ (사탕수수 농부 연구)", ""),
 ("결핍의 심리 (멀레이너선·샤퍼)", "Scarcity (social psychology)"), ("번아웃", "Occupational burnout"), ("상실과 회복탄력성 (보나노)", "George Bonanno"),
 ("외상 후 성장", "Post-traumatic growth"), ("웃음 치료와 노먼 커즌스", "Norman Cousins"), ("우울증 세로토닌 가설 재검토", "Biochemistry of depression"),
 ("전기경련치료의 오늘", "Electroconvulsive therapy"), ("전두엽 절제술과 모니스", "Lobotomy"), ("로즈메리 케네디", "Rosemary Kennedy"),
 ("가짜 수술 연구 (무릎 관절경)", ""),
])
add("신경학 사례", [
 ("올리버 색스의 '어웨이크닝스' 환자들", "Awakenings"), ("뇌가 거의 없는데 정상인 남자 (2007, 프랑스)", ""), ("뇌 반쪽을 떼어낸 아이들 (반구 절제술)", "Hemispherectomy"),
 ("뇌졸중을 겪은 뇌과학자 질 볼트 테일러", "Jill Bolte Taylor"), ("피니어스 게이지 이후: 앞이마엽 환자 EVR", ""), ("H.M. 이전: 브로카와 뇌 지도 논쟁", ""),
 ("헨리 몰레이슨의 뇌 조각 프로젝트", ""), ("뇌전증 수술과 자기 얼굴 바뀜 (방추상 자극)", ""), ("음악 소리가 들리는 환청 (음악 환청)", "Musical ear syndrome"),
 ("갑자기 화가가 된 사람들 (전두측두엽 치매)", "Frontotemporal dementia"), ("머리를 다친 뒤 천재가 된 사람 (제이슨 패짓)", "Acquired savant syndrome"),
 ("클라이브 이후: 기억 없이 사는 사람들의 일기", ""), ("치매 환자와 음악 (얼라이브 인사이드)", "Alive Inside"), ("알츠하이머의 첫 환자 아우구스테 데터", "Auguste Deter"),
 ("파킨슨병과 마이클 J. 폭스", ""), ("헌팅턴병과 낸시 웩슬러의 베네수엘라 연구", "Nancy Wexler"), ("ALS와 아이스버킷 챌린지", "Ice Bucket Challenge"),
 ("루게릭과 스티븐 호킹", ""), ("다발성 경화증", "Multiple sclerosis"), ("광우병과 쿠루병", "Kuru (disease)"), ("수막종과 성격 변화", ""),
 ("뇌진탕과 미식축구 (CTE, 오말루)", "Bennet Omalu"), ("권투 선수의 뇌", "Chronic traumatic encephalopathy"), ("편두통 오라와 이상한 나라의 앨리스 증후군", "Alice in Wonderland syndrome"),
 ("두통 수술의 역사: 천공술", "Trepanning"), ("신경 매독과 근대 정신의학", "General paresis of the insane"), ("수은과 '미친 모자 장수'", "Erethism"),
 ("일산화탄소와 기억", ""), ("체르노빌 이후 아이들의 뇌 연구", ""), ("기적의 회복: 테리 월리스 19년 만에 말하다", "Terry Wallis"),
])
add("뇌 연구법과 역사", [
 ("골상학의 흥망", "Phrenology"), ("골지와 카할의 뉴런 논쟁", "Neuron doctrine"), ("뇌파의 발견 (한스 베르거)", "Hans Berger"),
 ("오징어 거대 축삭과 활동 전위 (호지킨·헉슬리)", "Hodgkin–Huxley model"), ("오토 뢰비의 꿈과 신경전달물질", "Otto Loewi"), ("fMRI 죽은 연어 실험", ""),
 ("뇌 영상의 부두 상관관계 논쟁", ""), ("광유전학의 탄생", "Optogenetics"), ("커넥톰: 예쁜꼬마선충의 302개 뉴런", "Caenorhabditis elegans"),
 ("초파리 뇌 지도 완성 (2024)", ""), ("유리처럼 투명한 뇌 (CLARITY)", "CLARITY"), ("뇌 오가노이드", "Cerebral organoid"),
 ("인간 뇌 프로젝트의 실패", "Human Brain Project"), ("경두개 자기 자극", "Transcranial magnetic stimulation"), ("뇌를 녹화하는 신경 기록 (뉴로픽셀)", ""),
 ("파블로프부터 딥러닝까지: 퍼셉트론", "Perceptron"), ("헵의 규칙: 함께 켜지면 함께 연결된다", "Hebbian theory"), ("장기 강화 (LTP)의 발견", "Long-term potentiation"),
 ("어른 뇌에서도 새 뉴런이 생길까 논쟁", "Adult neurogenesis"), ("10%만 쓴다는 뇌 신화", "Ten percent of the brain myth"),
])
add("재현의 위기", [
 ("오픈 사이언스 협업: 100개 연구 다시 하기 (2015)", "Reproducibility Project"), ("벰의 예지력 논문 (2011)", "Daryl Bem"), ("디데릭 스타펠 조작 사건", "Diederik Stapel"),
 ("댄 애리얼리 데이터 논란", "Dan Ariely"), ("프란체스카 지노 사건", "Francesca Gino"), ("p-해킹", "Data dredging"), ("사전 등록의 등장", "Preregistration (science)"),
 ("빨간색이 매력을 높인다는 연구", ""), ("배고픈 판사 연구 다시 보기", ""), ("자기 통제와 포도당 가설", ""), ("뇌 사진이 있으면 더 믿는다", ""),
 ("음식 연구 브라이언 완싱크 사건", "Brian Wansink"), ("스탠퍼드 감옥 이후: 짐바르도 재검토", ""), ("과학 언론의 과장 연구", ""), ("출판 편향과 서랍 문제", "Publication bias"),
 ("메타분석의 힘과 한계", "Meta-analysis"), ("많은 실험실 프로젝트 (Many Labs)", "Many Labs"), ("WEIRD 표본 문제", "WEIRD"),
 ("통계적 유의성 논쟁 (p<0.005 제안)", ""), ("마시멜로 실험 재현의 교훈", ""),
])
add("동물의 마음", [
 ("까마귀의 도구 만들기 (베티)", "New Caledonian crow"), ("까마귀는 얼굴을 기억하고 원한을 품는다", ""), ("문어의 지능", "Cephalopod intelligence"),
 ("침팬지 아유무의 숫자 기억", "Ayumu (chimpanzee)"), ("코끼리의 거울 인식", ""), ("돌고래의 이름 휘파람", "Signature whistle"), ("꿀벌의 숫자 0 개념", ""),
 ("쥐의 공감: 갇힌 친구 꺼내 주기", ""), ("쥐는 간지럼을 타며 웃는다", ""), ("개는 사람 표정을 읽는다", ""), ("늑대와 개의 길들이기 (벨랴예프 여우)", "Domesticated red fox"),
 ("원숭이의 공정성: 오이와 포도", "Frans de Waal"), ("앵무새 춤추는 스노볼", "Snowball (cockatoo)"), ("청소놀래기의 거울 인식", ""), ("물고기도 아플까", "Pain in fish"),
 ("비둘기는 피카소와 모네를 구별한다", ""), ("박새의 언어 문법", ""), ("다람쥐의 도토리 기억", ""), ("철새의 자기장 나침반", "Magnetoreception"),
 ("거미의 깜짝 놀랄 계획 능력", ""),
])

if __name__ == "__main__":
    import collections
    print(len(T), collections.Counter(c for c, _, _ in T))
