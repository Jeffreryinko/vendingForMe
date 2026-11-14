"""iyagi_topics.py — 이야기 자판기에 Claude(API)가 쓸 이야기 목록. (갈래, 이름, 영어 위키백과 제목)
이미 있는 이야기(SEED·로봇·Claude 12편)와 겹치지 않게 골랐어요. 소설은 줄거리 + 읽는 맛만(본문 전체는 싣지 않음)."""
T = []
def add(g, rows):
    for r in rows: T.append((g, r[0], r[1]))

add("신화와 전승", [
 ("이자나기와 이자나미 (일본 창세 신화)", "Izanagi"), ("아마테라스와 동굴 (일본)", "Amaterasu"), ("반고의 천지개벽 (중국)", "Pangu"), ("여와가 사람을 빚다 (중국)", "Nüwa"),
 ("백사전 (중국)", "Legend of the White Snake"), ("양축 — 나비가 된 연인 (중국)", "Butterfly Lovers"), ("손오공의 탄생 (서유기 앞부분)", "Sun Wukong"),
 ("라마야나 — 시타를 구하러 (인도)", "Ramayana"), ("가네샤의 코끼리 머리 (인도)", "Ganesha"), ("우유 바다 휘젓기 (인도)", "Samudra manthana"),
 ("길가메시 이후: 아다파와 영생 (메소포타미아)", "Adapa"), ("이난나의 저승 하강 (수메르)", "Inanna's descent to the netherworld"),
 ("호루스와 세트의 다툼 (이집트)", "The Contendings of Horus and Seth"), ("라의 비밀 이름 (이집트)", "Ra"),
 ("오디세우스와 키클롭스 (그리스)", "Polyphemus"), ("이아손과 황금 양털 (그리스)", "Golden Fleece"), ("헤라클레스의 열두 과업 (그리스)", "Labours of Hercules"),
 ("페르세우스와 메두사 (그리스)", "Perseus"), ("에코와 나르키소스 (그리스)", "Narcissus (mythology)"), ("아라크네의 베 짜기 (그리스)", "Arachne"),
 ("파에톤의 태양 마차 (그리스)", "Phaethon"), ("필레몬과 바우키스 (그리스·로마)", "Baucis and Philemon"), ("큐피드와 프시케 (로마)", "Cupid and Psyche"),
 ("로물루스와 레무스 (로마)", "Romulus and Remus"), ("토르와 거인 우트가르다로키 (북유럽)", "Útgarða-Loki"), ("발드르의 죽음 (북유럽)", "Baldr"),
 ("오딘의 눈과 지혜의 샘 (북유럽)", "Mímisbrunnr"), ("라그나로크 (북유럽)", "Ragnarök"), ("쿠훌린 (아일랜드)", "Cú Chulainn"), ("티르 나 노그의 오신 (아일랜드)", "Oisín"),
 ("아서 왕과 바위 속의 칼 (영국)", "Excalibur"), ("성배를 찾아서 (아서왕 전설)", "Holy Grail"), ("트리스탄과 이졸데", "Tristan and Iseult"),
 ("칼레발라 — 삼포를 만든 대장장이 (핀란드)", "Sampo"), ("바바 야가 (슬라브)", "Baba Yaga"), ("불새 (러시아)", "Firebird (Slavic folklore)"),
 ("포폴 부 — 영웅 쌍둥이 (마야)", "Maya Hero Twins"), ("케찰코아틀 (아스테카)", "Quetzalcoatl"), ("만코 카팍과 황금 지팡이 (잉카)", "Manco Cápac"),
 ("까마귀가 빛을 훔치다 (북서 해안 원주민)", "Raven in mythology"), ("스카이 우먼 (이로쿼이)", "Sky Woman"), ("아난시와 지혜의 항아리 (서아프리카)", "Anansi"),
 ("순디아타 서사시 (말리)", "Epic of Sundiata"), ("드림타임과 무지개뱀 (오스트레일리아 원주민)", "Rainbow Serpent"), ("펠레와 하와이 화산", "Pele (deity)"),
 ("주몽 이후: 유리의 부러진 칼 (고구려)", "Yuri of Goguryeo"), ("박혁거세와 알 (신라)", "Hyeokgeose of Silla"), ("김수로왕과 허황옥 (가야)", "Heo Hwang-ok"),
 ("연오랑 세오녀 (신라)", "Yeono-rang and Seo-nyeo"), ("설문대할망 (제주)", "Seolmundae Halmang"), ("자청비 (제주 신화)", "Jacheongbi"),
 ("구렁덩덩 신선비 (한국)", ""), ("콩쥐팥쥐 (한국)", "Kongjwi and Patjwi"), ("장화홍련전 (한국)", "Janghwa Hongryeon jeon"), ("우렁각시 (한국)", ""),
 ("은혜 갚은 까치 (한국)", ""), ("견훤과 지렁이 (후백제 설화)", "Gyeon Hwon"), ("아랑 전설 (밀양)", "Arang (legend)"), ("에밀레종 전설", "Bell of King Seongdeok"),
 ("모모타로 (일본)", "Momotarō"), ("학의 보은 (일본)", "Tsuru no Ongaeshi"), ("가구야 공주 (일본)", "The Tale of the Bamboo Cutter"), ("설녀 (일본)", "Yuki-onna"),
 ("뮬란 (중국)", "Hua Mulan"), ("견우직녀 이후: 항아와 달 (중국)", "Chang'e"), ("엑스칼리버의 반대편: 지그프리트와 용 (독일)", "Sigurd"),
 ("골렘 (프라하 전설)", "Golem"), ("하멜른 이후: 로렐라이 (독일)", "Lorelei"), ("돌로 변한 트롤 (노르웨이)", "Troll"),
])
add("사람의 생애", [
 ("세종과 훈민정음", "Hunminjeongeum"), ("이순신의 명량", "Battle of Myeongnyang"), ("허난설헌", "Heo Nanseolheon"), ("김만덕 — 제주의 거상", "Kim Man-deok"),
 ("안중근", "An Jung-geun"), ("유관순", "Yu Gwan-sun"), ("석주명 — 나비 박사", "Seok Joo-myung"), ("우장춘", "Woo Jang-choon"),
 ("레오나르도 다빈치의 노트", "Leonardo da Vinci"), ("에이다 러브레이스", "Ada Lovelace"), ("니콜라 테슬라와 에디슨", "War of the currents"),
 ("마리 퀴리 이후: 리제 마이트너", "Lise Meitner"), ("로절린드 프랭클린", "Rosalind Franklin"), ("앨런 튜링", "Alan Turing"), ("이그나즈 이후: 존 해리슨의 시계", "John Harrison"),
 ("벤저민 프랭클린의 연", "Benjamin Franklin"), ("헬렌 켈러와 앤 설리번", "Anne Sullivan"), ("프리다 칼로", "Frida Kahlo"), ("빈센트 이후: 폴 고갱의 타히티", "Paul Gauguin"),
 ("베토벤의 하일리겐슈타트 유서", "Heiligenstadt Testament"), ("모차르트와 레퀴엠", "Requiem (Mozart)"), ("로알 아문센과 남극점", "Amundsen's South Pole expedition"),
 ("어니스트 섀클턴 이후: 스콧의 비극", "Terra Nova Expedition"), ("넬슨 만델라의 27년", "Nelson Mandela"), ("로자 파크스의 버스", "Rosa Parks"),
 ("마하트마 간디의 소금 행진", "Salt March"), ("링컨과 게티즈버그 연설", "Gettysburg Address"), ("나이팅게일과 숫자", "Florence Nightingale"),
 ("찰스 다윈과 비글호", "Second voyage of HMS Beagle"), ("멘델의 완두콩", "Gregor Mendel"), ("갈릴레오 이후: 케플러와 어머니의 마녀재판", "Katharina Kepler"),
 ("라이트 형제", "Wright brothers"), ("아멜리아 에어하트", "Amelia Earhart"), ("유리 가가린", "Yuri Gagarin"), ("스티브 잡스의 차고", "Steve Jobs"),
 ("코코 샤넬", "Coco Chanel"), ("월트 디즈니와 미키", "Walt Disney"), ("찰리 채플린의 위대한 독재자", "The Great Dictator"), ("무하마드 알리", "Muhammad Ali"),
 ("손기정과 베를린 마라톤", "Sohn Kee-chung"),
])
add("소설과 창작", [
 ("돈키호테 이후: 걸리버 여행기", "Gulliver's Travels"), ("로빈슨 크루소", "Robinson Crusoe"), ("지킬 박사와 하이드 씨", "Strange Case of Dr Jekyll and Mr Hyde"),
 ("프랑켄슈타인", "Frankenstein"), ("드라큘라", "Dracula"), ("셜록 홈스: 빨간 머리 연맹", "The Red-Headed League"), ("오만과 편견", "Pride and Prejudice"),
 ("제인 에어", "Jane Eyre"), ("폭풍의 언덕", "Wuthering Heights"), ("레 미제라블", "Les Misérables"), ("노트르담의 꼽추", "The Hunchback of Notre-Dame"),
 ("몬테크리스토 백작", "The Count of Monte Cristo"), ("80일간의 세계 일주", "Around the World in Eighty Days"), ("해저 2만 리", "Twenty Thousand Leagues Under the Seas"),
 ("보바리 부인", "Madame Bovary"), ("죄와 벌", "Crime and Punishment"), ("안나 카레니나", "Anna Karenina"), ("이반 일리치의 죽음", "The Death of Ivan Ilyich"),
 ("사람은 무엇으로 사는가 (톨스토이)", "What Men Live By"), ("외투 (고골)", "The Overcoat"), ("귀여운 여인 (체호프)", "The Darling (short story)"),
 ("크리스마스 선물 (오 헨리)", "The Gift of the Magi"), ("어셔가의 몰락 (포)", "The Fall of the House of Usher"), ("고자질하는 심장 (포)", "The Tell-Tale Heart"),
 ("허클베리 핀의 모험", "Adventures of Huckleberry Finn"), ("모비 딕", "Moby-Dick"), ("주홍 글씨", "The Scarlet Letter"), ("작은 아씨들", "Little Women"),
 ("이상한 나라의 앨리스", "Alice's Adventures in Wonderland"), ("피터 팬", "Peter Pan"), ("오즈의 마법사", "The Wonderful Wizard of Oz"), ("행복한 왕자 (와일드)", "The Happy Prince and Other Tales"),
 ("도리언 그레이의 초상", "The Picture of Dorian Gray"), ("인형의 집 (입센)", "A Doll's House"), ("햄릿 이후: 리어왕", "King Lear"), ("맥베스", "Macbeth"),
 ("베니스의 상인", "The Merchant of Venice"), ("한여름 밤의 꿈", "A Midsummer Night's Dream"), ("데카메론 — 매 이야기", "The Decameron"), ("캔터베리 이야기 — 바스 여인", "The Wife of Bath's Tale"),
 ("신곡 — 지옥편", "Inferno (Dante)"), ("천일야화 — 셰에라자드", "One Thousand and One Nights"), ("신드바드의 항해", "Sinbad the Sailor"), ("겐지 이야기", "The Tale of Genji"),
 ("삼국지 — 적벽대전", "Battle of Red Cliffs"), ("수호지", "Water Margin"), ("홍길동전", "Hong Gildong jeon"), ("구운몽 (김만중)", "Guunmong"), ("허생전 (박지원)", "Heosaengjeon"),
 ("운수 좋은 날 (현진건)", "A Lucky Day"), ("메밀꽃 필 무렵 (이효석)", "When Buckwheat Flowers Bloom"), ("소나기 (황순원)", "Sonagi (short story)"),
 ("날개 (이상)", "Wings (short story)"), ("변신 이후: 소송 (카프카)", "The Trial"),
])
add("역사와 사건", [
 ("폼페이의 마지막 날", "Pompeii"), ("타이타닉의 밤", "Titanic"), ("런던 대화재 (1666)", "Great Fire of London"), ("체르노빌의 밤", "Chernobyl disaster"),
 ("아폴로 13호", "Apollo 13"), ("크리스마스 휴전 (1914)", "Christmas truce"), ("베를린 장벽이 열린 밤", "Fall of the Berlin Wall"), ("로제타석 해독", "Rosetta Stone"),
 ("투탕카멘 무덤 발견", "Discovery of the tomb of Tutankhamun"), ("페니실린의 발견", "Penicillin"), ("튤립 파동", "Tulip mania"), ("남해 거품 사건", "South Sea Company"),
])
add("웃음과 말", [
 ("오성과 한음", "Yi Hang-bok"), ("김삿갓", "Kim Sat-gat"), ("정수동의 재담", ""), ("방귀쟁이 며느리 (한국 민담)", ""), ("바보 이반 (톨스토이)", "Ivan the Fool"),
 ("뮌히하우젠 남작의 허풍", "Baron Munchausen"), ("이솝: 해와 바람", "The North Wind and the Sun"), ("이솝: 개미와 베짱이", "The Ant and the Grasshopper"),
 ("잇큐 스님의 재치 (일본)", "Ikkyū"), ("아반티의 이야기 (위구르)", "Afanti"),
])

if __name__ == "__main__":
    import collections
    print(len(T), collections.Counter(g for g, _, _ in T))
