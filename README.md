# 자판기 (vendingForMe)

시사 자판기 + 이야기 도서관 + AI 논문. 서버 없이 GitHub 하나로 돌아갑니다 (카드 결제 0원).

| 부품 | 무엇 | 어디서 |
|---|---|---|
| 첫 화면(홈) | `index.html` — 앱 고르는 곳(시사·이야기·AI 카드, 갱신 상태, 설정) | GitHub Pages |
| 사이트 | `sisa/`, `iyagi/`, `ai/` | GitHub Pages |
| 돼지코(shim) | `assets/claude-shim.js` — 아티팩트 전용 부품을 파일+폰 저장소로 대체 | 사이트 안 |
| 껍데기 | `assets/shell.js` — 위쪽 앱 전환 막대(홈·시사·이야기·AI·설정), 공통 뒤로가기, 설정 시트, PWA | 사이트 안 |
| 넘겨보기 | `assets/deck.js` — 세 앱 공통: 카드 한 장씩 옆으로 밀기, 본 것은 다시 안 나옴(폰 저장소), 좋아요·공유, 원문을 한국어 번역(`*.translate.goog`)으로 열기 | 사이트 안 |
| 디자인 | `assets/apple.css` — 애플식 공통 디자인(시스템 글꼴·iOS 색·반투명 막대). 앱 강조색: 시사 파랑·이야기 주황·AI 보라 | 사이트 안 |
| 시사 로봇 | `robot/sisa_run.py` — 수집·번역·댓글·사진 (3시간마다) | GitHub Actions `sisa.yml` |
| 트렌드 로봇 | `robot/trends_run.py` — 22개국 구글·위키·유튜브·X·현지 검색 순위 (3시간마다) → `assets/hot.js` 화면 | GitHub Actions `trends.yml` |
| AI 로봇 | `robot/ai_run.py` — HF 추천 논문·arXiv 신규·회사 발표·GitHub·국내 소식 (매일 04:30), NLLB 번역·용어 밑줄, 토큰 0 → `ai/` 화면. 용어 목록 `robot/ai_terms.py` | GitHub Actions `ai.yml` |
| 이야기 위키 로봇 | `robot/iyagi_wiki.py` — 목록 약 1,500개를 위키백과에서 한 번에 모아 정리(토큰 0, 손으로 실행) | GitHub Actions `iyagi-wiki.yml` |
| 요청함 | 앱의 "풀어 주세요" 버튼 → GitHub 이슈 → `data/requests.json` → 다음 루틴 때 만들기 | GitHub Actions `requests.yml` |
| AI 쉬운 풀이 | `robot/AI_RUNBOOK.md`, `robot/easy_tools.py` — 하루 최대 3편, 요청 먼저 → `data/ai/easy/` | 편집장 루틴 07시 회차 |
| 역사 로봇 | `robot/history_run.py` — 위키데이터 '역사 종류' 90여 개(하위 포함)·역사 인물·한국어 위키백과 분류·'N년 출생/사망' 분류에서 한국어 위키백과 역사 글을 전부 받아 요약·단락으로 자르고 연도·나라·테마를 자동으로 (매일 05:00, 남으면 다음 회차 자동, 토큰 0) → `history/` 화면. 분류표 `robot/history_tables.py` | GitHub Actions `history.yml` |
| 원문 번역 로봇 | `robot/iyagi_translate.py` — 토큰 0 기계번역 (주 2회) | GitHub Actions `iyagi-orig.yml` |
| 시사 편집장 | `robot/EDITOR_RUNBOOK.md` — 이슈·해설·단신·이름 사전 (07·19시) | 클로드 예약 작업 |
| 이야기 작가 | `robot/AUTHOR_RUNBOOK.md` — 매일 새벽 5편 | 클로드 예약 작업 |
| 창고 | `data/sisa/*`, `data/iyagi/*`, `data/trends/*`, `data/ai/*`, `data/history/*` (JSON) | 저장소 |

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

## 역사 탭 자료 (`data/history/`)
본문은 한국어 위키백과(CC BY-SA 4.0), 속성은 위키데이터(CC0). 색인 한 줄은 배열 — 칸 순서는 `_index.json` 의 `cols`.
- `pages/xx/k<번호>.json` 글 한 편 (요약·단락·연도·나라·테마·관계·출처). 용량 한도(`HIST_BUDGET_MB`, 380MB)를 넘은 뒤 받은 글은 요약판(`full:false`) — 화면이 본문을 위키백과에서 바로 불러옴
- `idx/<권역>-<시대>.json` 권역×시대 목록 · `cty/<나라>.json` 나라별(연도순) · `dec/<연대>.json` 같은 시기 · `th/<테마>.json` · `tag/B|P.json` 야사·대명사 · `s/<첫 글자>.json` 제목 찾기 · `days/MM-DD.json` 역사 속 오늘 · `top.json` 첫 화면
- `_state/` 로봇 기억: `pages.tsv` 받은 글 · `queue.tsv` 받을 차례 · `skip.tsv` 뺀 글(이유) · `closure.json` 하위 종류 표 · `countries.json`·`labels.json` 위키데이터 캐시 · `seeds.json` 종자 시각 · `health.json` 출처 건강
- 처음 큰 수확: Actions → 역사 로봇 → Run workflow (기본값). 한 회차 약 5시간, 남으면 스스로 다음 회차(최대 30회). 그 뒤 매일 새벽 5시
