# 시사 자판기 (vendingForMe)

**시사 · 도구 · AI** — 자판기를 세 사이트로 나눈 것 중 하나예요 (2026-11-08). 서버 없이 GitHub 하나로 돌아가요 (카드 결제 0원, **유지 토큰 0**).
- 주소: https://jeffreryinko.github.io/vendingForMe/
- 다른 자판기: [이야기 자판기](https://jeffreryinko.github.io/vfm-story/) (이야기·역사·뇌) · [사람 자판기](https://jeffreryinko.github.io/vfm-mind/) (배댓·맨탈)
- 같은 주소(jeffreryinko.github.io)라서 폰에 저장된 별표·메모·보관함은 세 사이트가 함께 써요.

| 로봇 | 무엇 | 언제 |
|---|---|---|
| 시사 로봇 `robot/sisa_run.py` | 수집 → 제목 번역(DeepL·Google, 모자라면 무료 기계번역 NLLB) → 사건 묶기 → 댓글 | 3시간마다 (`sisa.yml`) |
| **로봇 편집장** `robot/sisa_edit.py` | 예전 클로드 '편집장' 예약 작업 대신: 이슈 이름(대표 기사 제목)·분야·요약(피드 설명 기계번역)·꼭 알아야 할 5개(점수 순)·용어(이름 사전)·나라별 시각·먼저 읽을 기사·단신 50개·흐름·나라별 2줄·이름 사전 자동 추가(위키데이터). AI가 쓴 문장 없음(`method: auto-v1`) | 시사 로봇 바로 뒤 |
| 트렌드 로봇 `robot/trends_run.py` | 22개국 검색어·영상 순위 | 3시간마다 (`trends.yml`) |
| AI 로봇 `robot/ai_run.py` + `easy_tools.py auto` | 논문·발표·코드·소식 + 새 기능 정리·풀이 요청(초록 기계번역 정리) — 예전 편집장 07시 회차 대신 | 매일 04:30 (`ai.yml`) |
| 도구 로봇 `robot/tools_run.py` | GitHub 급상승·긱뉴스·해커뉴스·유튜브 해설·모음 목록 | 하루 4번 (`tools.yml`) |
| 라디오 `robot/radio_run.py` | 그날 카드를 오픈소스 음성으로 | `radio.yml` |

## 비밀 설정 (저장소 Settings → Secrets and variables → Actions)
`DEEPL_API_KEY`, `GOOGLE_TRANSLATE_API_KEY`, `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`
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

