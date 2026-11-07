# 자판기 (vendingForMe)

시사 자판기 + 이야기 도서관 + AI 논문 + 역사 + 도구 + 뇌. 서버 없이 GitHub 하나로 돌아갑니다 (카드 결제 0원).

| 부품 | 무엇 | 어디서 |
|---|---|---|
| 첫 화면(홈) | `index.html` — 앱 고르는 곳(시사·이야기·AI 카드, 갱신 상태, 설정) | GitHub Pages |
| 사이트 | `sisa/`, `iyagi/`, `ai/`, `history/`, `tools/`, `brain/` | GitHub Pages |
| 돼지코(shim) | `assets/claude-shim.js` — 아티팩트 전용 부품을 파일+폰 저장소로 대체 | 사이트 안 |
| 껍데기 | `assets/shell.js` — 위쪽 앱 전환 막대(홈·시사·이야기·AI·설정), 공통 뒤로가기, 설정 시트, PWA | 사이트 안 |
| 넘겨보기 | `assets/deck.js` — 세 앱 공통: 카드 한 장씩 옆으로 밀기, 본 것은 다시 안 나옴(폰 저장소), 좋아요·공유, 원문을 한국어 번역(`*.translate.goog`)으로 열기 | 사이트 안 |
| 홈 랜덤 | `assets/mix.js` — 홈 첫 화면: 시사·트렌드·레딧/밈·AI 새 기능·나라별 오늘·이야기/역사를 비율대로 섞어 넘겨보기, 한 번에 찾기, 종류별 비율(많이·보통·적게·끄기) | 사이트 안 |
| 트렌드 카드 | `assets/trendcard.js` — 트렌드·레딧·밈 카드 (시사 트렌드 탭과 홈이 같이 씀) | 사이트 안 |
| 디자인 | `assets/apple.css` — 애플식 공통 디자인(시스템 글꼴·iOS 색·반투명 막대). 앱 강조색: 시사 파랑·이야기 주황·AI 보라·역사 갈색·도구 청록 | 사이트 안 |
| 시사 로봇 | `robot/sisa_run.py` — 수집·번역·댓글·사진 (3시간마다) | GitHub Actions `sisa.yml` |
| 트렌드 로봇 | `robot/trends_run.py` — 22개국 구글·위키·유튜브·X·현지 검색 순위 (3시간마다) → `assets/hot.js` 화면 | GitHub Actions `trends.yml` |
| AI 로봇 | `robot/ai_run.py` — HF 추천 논문·arXiv 신규·회사 발표·GitHub·국내 소식 (매일 04:30), NLLB 번역·용어 밑줄, 토큰 0 → `ai/` 화면. 용어 목록 `robot/ai_terms.py` | GitHub Actions `ai.yml` |
| 도구 로봇 | `robot/tools_run.py` — 요즘 뜨는 AI·개발 도구·오픈소스·활용법: GitHub 급상승(오늘의 인기+새 저장소+별 증가)·긱뉴스·해커뉴스(Show HN·화제)·유튜브 해설 채널 RSS(+하루 한 번 검색)·모음 목록(awesome-*) 새 줄·허깅페이스 인기 앱 (하루 4번 06:40·12:40·18:40·23:40, NLLB 번역, 토큰 0) → `tools/` 화면. 채널·모음 목록·분류 낱말은 `robot/tools_sources.py` | GitHub Actions `tools.yml` |
| 뇌 로봇 | `robot/brain_run.py` — 뇌과학 소식: 한국어 기사(구글 뉴스 RSS) + 영문 대중 매체 4곳(ScienceDaily·Neuroscience News·Science News·The Transmitter, NLLB 번역), 기사에 나온 부위를 찾아 붙임, 위키백과 첫 문단 7일마다 (하루 2번 07:20·19:20, 토큰 0) → `brain/` 화면. 부위 52개 표 `robot/brain_regions.py`, 그림 만들기 `robot/brain_build.py`(한 번만) | GitHub Actions `brain.yml` |
| 배댓 | `baedat/` — 한국 유튜브 월간 인기 영상 50개 × 배댓 10개 카드, 썸네일 누르면 바로 재생, 유형·감정 분석. 자료 `data/baedat/<YYYY-MM>.json` (매월 1일 클로드 예약 작업이 수집·분류) | GitHub Pages |
| 맨탈 | `mental/` — 미드 「멘탈리스트」 패트릭 제인의 기술을 회차·장면별 카드로, 오늘의 훈련·훈련 기록(폰 저장, 구글 로그인 시 기기끼리 이어짐). 자료 `data/mental/{meta,eps,uses,analysis}/_index.json` | GitHub Pages |
| 이야기 위키 로봇 | `robot/iyagi_wiki.py` — 목록 약 1,500개를 위키백과에서 한 번에 모아 정리(토큰 0, 손으로 실행) | GitHub Actions `iyagi-wiki.yml` |
| 요청함 | 앱의 "풀어 주세요" 버튼 → GitHub 이슈 → `data/requests.json` → 다음 루틴 때 만들기 | GitHub Actions `requests.yml` |
| AI 쉬운 풀이 | `robot/AI_RUNBOOK.md`, `robot/easy_tools.py` — 하루 최대 3편, 요청 먼저 → `data/ai/easy/` | 편집장 루틴 07시 회차 |
| 역사 로봇 | `robot/history_run.py` — 위키데이터 '역사 종류' 90여 개(하위 포함)·역사 인물·한국어 위키백과 분류·'N년 출생/사망' 분류에서 한국어 위키백과 역사 글을 전부 받아 요약·단락으로 자르고 연도·나라·테마를 자동으로 (매일 05:00, 남으면 다음 회차 자동, 토큰 0) → `history/` 화면. 분류표 `robot/history_tables.py` | GitHub Actions `history.yml` |
| 원문 번역 로봇 | `robot/iyagi_translate.py` — 토큰 0 기계번역 (주 2회) | GitHub Actions `iyagi-orig.yml` |
| 시사 편집장 | `robot/EDITOR_RUNBOOK.md` — 이슈·해설·단신·이름 사전 (07·19시) | 클로드 예약 작업 |
| 이야기 작가 | `robot/AUTHOR_RUNBOOK.md` — 매일 새벽 5편 | 클로드 예약 작업 |
| 창고 | `data/sisa/*`, `data/iyagi/*`, `data/trends/*`, `data/ai/*`, `data/history/*`, `data/tools/*`, `data/brain/*`, `data/baedat/*` (JSON) | 저장소 |

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

## 도구 탭 자료 (`data/tools/`)
- `now.json` 지금 화면 — `sec.<구역>` 목록(gh·gn·hn·yt·list·hf·rd) + `hot`('지금 뜨는 것' id 18개)
- `days/<날짜>.json` 그날 처음 본 것 (찾기용, 30일) · `lists/<id>.json` 모음집 전체(번역 포함)
- `_state/stars.tsv` 저장소별 지난 별 수(하루 +N 계산) · `_state/awesome.json` 모음 목록에 이미 있던 줄(처음 돌 때 있던 건 `0` = 새 항목 아님) · `_state/yt.json` 하루 한 번 검색 결과
- 유튜브 채널 더하기: 채널 주소(@이름)에서 UC로 시작하는 ID를 찾아 `robot/tools_sources.py` 의 `CHANNELS` 에 한 줄

## 뇌 탭 자료 (`data/brain/`)
- `regions.json` 부위 52개(1단계 12 + 2단계 40): 이름·영어·뜻풀이·한 줄·하는 일·비유·어디쯤·다치면·짝·기사 낱말. 원본은 `robot/brain_regions.py` → `python robot/brain_build.py --text`
- `atlas.json` + `img/*.webp` 평면 그림 6면(옆면·안쪽 면·아래 면 = 입체 음영 / 앞 단면·해마 단면·가로 단면 = MRI) — 조각(atom)별 SVG 경로와 넓이. `mesh.bin`·`mesh.json` 3D 조각 92개(약 1MB)
  - 재료: MNI152 표준 뇌 1mm, AAL·Harvard-Oxford 피질하·JHU 백질(neuroparc 저장소), 배경 MRI 는 nilearn 내장 MNI152 2009. 작은 핵(시상하부·흑질·복측피개영역·청반·솔기핵·뇌하수체·송과선)은 논문 좌표에 대략 크기로
  - 다시 만들기: neuroparc 를 받아 `python robot/brain_build.py --atlas <neuroparc 경로>` (nibabel·nilearn·scikit-image·trimesh·fast-simplification 필요)
- `news.json` 소식 30일치(부위 `rs` 붙음) · `_index.json` 부위별 기사 수·출처 상태 · `wiki.json` 위키백과 첫 문단
- 외우기 기록은 폰 `vfm:brain:*` (srs = 부위별 상자·다음 복습일). 구글 로그인하면 기기끼리 맞춤
- 가족 점수판: Supabase 표 `brain_board` — 만드는 SQL 은 `robot/brain_board.sql` (한 번만 실행)
