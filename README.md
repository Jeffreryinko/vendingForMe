# 자판기 (vendingForMe)

시사 자판기 + 이야기 도서관 + AI 논문. 서버 없이 GitHub 하나로 돌아갑니다 (카드 결제 0원).

| 부품 | 무엇 | 어디서 |
|---|---|---|
| 사이트 | `index.html` → `sisa/`, `iyagi/`, `ai/` | GitHub Pages |
| 돼지코(shim) | `assets/claude-shim.js` — 아티팩트 전용 부품을 파일+폰 저장소로 대체 | 사이트 안 |
| 껍데기 | `assets/shell.js` — 탭 전환·설정·내보내기·PWA | 사이트 안 |
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
