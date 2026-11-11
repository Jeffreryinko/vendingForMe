# 시사 자판기 (vendingForMe)

**시사 · 도구 · AI · 딜** — 자판기를 세 사이트로 나눈 것 중 하나예요 (2026-11-08). 서버 없이 GitHub 하나로 돌아가요 (카드 결제 0원, **유지 토큰 0**).
- 주소: https://jeffreryinko.github.io/vendingForMe/
- 다른 자판기: [이야기 자판기](https://jeffreryinko.github.io/vfm-story/) (이야기·역사·뇌) · [사람 자판기](https://jeffreryinko.github.io/vfm-mind/) (배댓·맨탈)
- 같은 주소(jeffreryinko.github.io)라서 폰에 저장된 별표·메모·보관함은 세 사이트가 함께 써요.
- [매일 업무 플래너](https://jeffreryinko.github.io/vendingForMe/planner/) — `planner/` 폴더. 자판기와는 따로 도는 개인 플래너(설명은 [planner/README.md](planner/README.md)). 로그인만 함께 써요.

| 로봇 | 무엇 | 언제 |
|---|---|---|
| 시사 로봇 `robot/sisa_run.py` | 수집 → 제목 번역(DeepL·Google, 모자라면 무료 기계번역 NLLB) → 사건 묶기 → 댓글 | 3시간마다 (`sisa.yml`) |
| **로봇 편집장** `robot/sisa_edit.py` | 예전 클로드 '편집장' 예약 작업 대신: 이슈 이름(대표 기사 제목)·분야·요약(피드 설명 기계번역)·꼭 알아야 할 5개(점수 순)·용어(이름 사전)·나라별 시각·먼저 읽을 기사·단신 50개·흐름·나라별 2줄·이름 사전 자동 추가(위키데이터). AI가 쓴 문장 없음(`method: auto-v1`) | 시사 로봇 바로 뒤 |
| 트렌드 로봇 `robot/trends_run.py` | 22개국 검색어·영상 순위 | 3시간마다 (`trends.yml`) |
| AI 로봇 `robot/ai_run.py` + `easy_tools.py auto` | 논문·발표·코드·소식 + 새 기능 정리·풀이 요청(초록 기계번역 정리) — 예전 편집장 07시 회차 대신 | 매일 04:30 (`ai.yml`) |
| 도구 로봇 `robot/tools_run.py` | GitHub 급상승·긱뉴스·해커뉴스·유튜브 해설·모음 목록 | 하루 4번 (`tools.yml`) |
| 배댓 로봇 `robot/baedat_run.py` | 지난달 한국 유튜브 인기 영상 50개 × 배댓 10개, 유형·감정은 낱말 규칙(토큰 0). 예전 클로드 '배댓 월간판' 예약 작업 대신. 화면은 [사람 자판기](https://jeffreryinko.github.io/vfm-mind/baedat/) 가 이 자료를 읽어요 | 매월 1일 05:23 (`baedat.yml`) |
| **딜 로봇** `robot/deal_run.py` | 세계 투자 유치·인수합병·사모·상장·펀드 결성 뉴스(직접 RSS 15곳 + 구글 뉴스 13개 나라판) → 같은 거래끼리 묶기·금액 원 환산·단계·분야·나라·회사·투자사, 무료 기계번역. 미국 SEC Form D·상장·합병 서류, 한국 DART 공시를 3년치 + 매일 쌓음. 분류 낱말은 `robot/deal_sources.py`. 판정(성사·소문·무산·소식, 믿음 등급 f/m/s/c, 금액 검사, 위키데이터 회사 사전, 지난 이야기, 크기 자, 돈의 지도, 아침 6시 '오늘의 딜 12')은 `robot/deal_judge.py` | 하루 4번 07:50·13:50·19:50·00:50 (`deal.yml`) |
| 라디오 `robot/radio_run.py` | 그날 카드를 오픈소스 음성으로 | `radio.yml` |

## 비밀 설정 (저장소 Settings → Secrets and variables → Actions)
`DEEPL_API_KEY`, `GOOGLE_TRANSLATE_API_KEY`, `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `SEC_CONTACT_EMAIL`(딜: 미국 SEC가 요구하는 연락처 이메일), `DART_API_KEY`(딜: opendart.fss.or.kr 무료 인증키)
(없는 키는 그 부분만 건너뜁니다. 번역 키가 둘 다 없으면 제목은 원문으로 보입니다.)

## 데이터 모양
- `data/<앱>/<컬렉션>/_index.json` — 작은 컬렉션은 문서 전체 `[{id,…}]`, 큰 컬렉션은 id 목록 `["…"]`
- `data/<앱>/<컬렉션>/<id>.json` — 문서 하나
- `data/<앱>/_meta.json` — 마지막 갱신 시각 (사이트 오른쪽 아래 점 색깔)
- 읽은 기록·설정은 폰 브라우저(localStorage)에만 있음 → 설정에서 내보내기/불러오기

## 로컬에서 보기
`python -m http.server 8000` 후 http://localhost:8000/

## 뒤로가기 규칙 (모든 앱 공통 — assets/shell.js)
- 앱 안에서 화면을 옮길 때 브라우저 기록을 쌓지 않는다 (`history.replaceState`). 앱끼리 옮길 때도 마찬가지.
- 휴대폰 뒤로가기 = 한 단계 위로: 열린 창 닫기 → 앞 화면 → 그 앱 첫 화면 → 자판기 홈 → 나가기.
- 각 앱은 `window.vfmApp = { back(), go(hash), route(), top() }` 를 내놓는다. `back()` 은 처리했으면 true.

## 도구 탭 자료 (`data/tools/`)
- `now.json` 지금 화면 — `sec.<구역>` 목록(gh·gn·hn·yt·list·hf·rd) + `hot`('지금 뜨는 것' id 18개)
- `days/<날짜>.json` 그날 처음 본 것 (찾기용, 30일) · `lists/<id>.json` 모음집 전체(번역 포함)
- `_state/stars.tsv` 저장소별 지난 별 수(하루 +N 계산) · `_state/awesome.json` 모음 목록에 이미 있던 줄(처음 돌 때 있던 건 `0` = 새 항목 아님) · `_state/yt.json` 하루 한 번 검색 결과
- 유튜브 채널 더하기: 채널 주소(@이름)에서 UC로 시작하는 ID를 찾아 `robot/tools_sources.py` 의 `CHANNELS` 에 한 줄


## 배움 (투자 교실 `deal/learn/`)
- 화면 엔진 `assets/learn.js` + 모양 `assets/learn.css` (시사 배움도 같이 씀). 하루 몫(코스 1장 · 용어 · 역사)과 '이어서 하기', 수준 확인, 라이트너 상자 복습(1·3·7·16·35일). 기록은 기기에만(`vfm:learn:<앱>:*`).
- 글·그림은 사람이 써 둔 파일(로봇·토큰 0): `terms.js` 용어 130개(뜻·비유·기사 예문·찾을 낱말 `k`), `course.js` 8장 + 수준 확인 12문제, `history.js` 세계·미국·유럽·일본·중국·한국 69편, `figs.js` 손으로 그린 SVG 25장.
- 시사 배움 `sisa/learn/` (세상 읽기 교실): 같은 엔진. 용어 129개(뉴스 읽기·정치·법·경제·무역·국제기구·분쟁·에너지·기술), 코스 8장 + 수준 확인 12문제, 역사 77편(세계·미국·유럽·러시아·중동·중국·일본·한국), 그림 16장. 시사 아래 메뉴 여섯째 '배움'.
- 딜 자세히 창의 '이 기사에 나온 말'은 `terms.js` 의 `k` 낱말을 제목·요약에서 찾아 붙임.

## 딜 앱 자료 (`data/deal/`)
- `now.json` 지금 화면 (오늘 거래·소문·무산 + 오늘의 딜 12 `daily` · 크기 자 `bench` · 돈의 지도 `map`(분야×지역 [건수, 한가운데값, 합, 가장 큰 한 건 뺀 합, 지난 4주 평균 건수]) · 이번 주 `week` · 미국 공시 `secToday`). 거래마다 `st` 성사/소문/무산/소식, `g` 믿음 f 공시·m 여러 매체·s 한 매체·c 확인 필요, `hist` 지난 이야기, `follow` 또 넣은 투자사, `quiet` 기사 없이 공시만
- `_state/recent.json` 다음 실행에서 이어 묶을 최근 거래(출처 전부) · `_state/codict.json` 위키데이터 회사 사전
- `news/<날짜>.json` 그날 처음 본 거래 (계속 쌓음, 요약 빼고 가볍게)
- `formd/<YYYY>Q<n>.json` 미국 Form D 한 줄 = [신고일, 이름, 주/나라, 업종, 펀드종류, 판매액$, 모집액$(-1 무기한), 투자자 수, CIK, 접수번호, 설립연도]
- `sec/<연도>.json` 상장·합병 서류 [날짜, 서류, 회사, CIK, 경로] · `dart/<연도>.json` [날짜, 종류, 내용, 회사, 시장, 상대, 금액원, 지분%, 사업, 접수번호, 보고서명]
- `stats.json` 숫자로 보기 · `people.json` 자주 나오는 투자사·회사
- `firms.json` · `firms/<id>.json` 주요 투자사 145곳 (`robot/deal_firms.py` 표 + 위키데이터·위키백과 소개 30일마다 + 최근 90일 거래·Form D 펀드 신고·함께 나온 투자사) · `_state/` 진행 기록(되돌아보기 위치·이미 센 기사 주소)
- `kvca.json` · `kvca/<id>.json` 한국 VC 전체 (한국벤처캐피탈협회 벤처투자회사 전자공시 DIVA — 올해·작년 투자 실적, 운용 조합, 설립·직원·시/구, 최근 90일 기사). `robot/deal_kvca.py`, 3일마다
- 거래 묶기: 같은 회사+종류, 또는 금액이 10% 안 + 같은 영문 낱말, 또는 제목 낱말 60% 겹침 (4일 안, 같은 회사면 7일)
