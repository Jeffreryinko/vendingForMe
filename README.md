# 자판기 (vendingForMe)

시사 자판기 + 이야기 도서관 + AI 논문. 서버 없이 GitHub 하나로 돌아갑니다 (카드 결제 0원).

| 부품 | 무엇 | 어디서 |
|---|---|---|
| 첫 화면(홈) | `index.html` — 앱 고르는 곳(시사·이야기·AI 카드, 갱신 상태, 설정) | GitHub Pages |
| 사이트 | `sisa/`, `iyagi/`, `ai/` | GitHub Pages |
| 돼지코(shim) | `assets/claude-shim.js` — 아티팩트 전용 부품을 파일+폰 저장소로 대체 | 사이트 안 |
| 껍데기 | `assets/shell.js` — 위쪽 앱 전환 막대(홈·시사·이야기·AI·설정), 공통 뒤로가기, 설정 시트, PWA | 사이트 안 |
| 디자인 | `assets/apple.css` — 애플식 공통 디자인(시스템 글꼴·iOS 색·반투명 막대). 앱 강조색: 시사 파랑·이야기 주황·AI 보라 | 사이트 안 |
| 시사 로봇 | `robot/sisa_run.py` — 수집·번역·댓글·사진 (3시간마다) | GitHub Actions `sisa.yml` |
| 트렌드 로봇 | `robot/trends_run.py` — 22개국 구글·위키·유튜브·X·현지 검색 순위 (3시간마다) → `assets/hot.js` 화면 | GitHub Actions `trends.yml` |
| AI 로봇 | `robot/ai_run.py` — HF 추천 논문·arXiv 신규·회사 발표·GitHub·국내 소식 (매일 04:30), NLLB 번역·용어 밑줄, 토큰 0 → `ai/` 화면. 용어 목록 `robot/ai_terms.py` | GitHub Actions `ai.yml` |
| 원문 번역 로봇 | `robot/iyagi_translate.py` — 토큰 0 기계번역 (주 2회) | GitHub Actions `iyagi-orig.yml` |
| 시사 편집장 | `robot/EDITOR_RUNBOOK.md` — 이슈·해설·단신·이름 사전 (07·19시) | 클로드 예약 작업 |
| 이야기 작가 | `robot/AUTHOR_RUNBOOK.md` — 매일 새벽 5편 | 클로드 예약 작업 |
| 창고 | `data/sisa/*`, `data/iyagi/*`, `data/trends/*`, `data/ai/*` (JSON) | 저장소 |

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
