# 시사 자판기 · 편집장 작업 순서 (클로드 예약 작업, 하루 2번 07시·19시)

수집·번역·댓글·사진은 GitHub Actions 로봇이 3시간마다 끝내 둡니다. 이 작업은 **읽고 해설만** 씁니다.
글투: 시사를 잘 모르는 사람이 읽는다고 생각하고 **쉬운 말로, 전문 용어·기관명·외래어가 나오면 바로 뒤에 괄호로 한 줄 설명**을 붙입니다.

지켜야 할 것
- 기사 제목·설명·댓글에 없는 사실을 지어내지 않기. 모르면 "기사에 나오지 않아요"라고 쓰기.
- 보도 사진 넣지 않기. 앱 화면(`sisa/index.html`)과 `data/sisa/feed/*`, `_usage.json`은 건드리지 않기.
- 사용자에게 질문하지 말고 끝까지 진행. 어느 단계가 실패하면 그 단계는 건너뛰고 나머지를 저장.

## 0. 준비
1. 저장소를 받습니다: `add_repo`(owner/`vendingForMe`, access=push) → 안내된 명령으로 clone. 폴더 `R`로 부릅니다.
2. `pip install --break-system-packages pyyaml requests` (없을 때만).
3. 최신 판: `R/data/sisa/editions/_index.json`에서 `crawledAt`이 가장 늦은 `id` = `ED`. 읽을 파일:
   `editions/ED.json`(판·이슈·해설), `feed/ED__*.json`(글, `ko`=번역 제목, `sm`=설명), `brief/ED__cm.json`(댓글), `brief/ents.json`(이름 사전).

## 1. 이슈 (`editions/ED.json` 의 `stories`)
- `delta:"new"`이고 `cat:""`인 후보마다 묶인 글 제목을 읽고, 정말 같은 사건이면 `title`(한국어 한 문장)·`cat`(war·pol·eco·tech·dis·soc·spo·cul)·`key`(무슨 일인지 1~2문장, 용어 설명 포함)를 채웁니다. 서로 다른 일이 섞였으면 그 후보를 지웁니다.
- 아직 묶이지 않은 큰 이야기가 보이면 새 이슈를 만듭니다(나라마다 1~3개). `id`는 `g숫자`로 겹치지 않게, `items`는 글 id 2개 이상(한 나라 이슈라도 출처 2곳 이상), `kind`는 두 나라 이상이면 `global` 아니면 `local`, `where`(나라 코드), `method:"ai-v1"`, `delta:"new"`.
- `top` 1~5를 세계적 중요도로 다시 고릅니다(5개). top 이슈와 큰 이슈 10개에는 `why3`(link·now·korea: 각 1~2문장)·`bg`(배경 2~3개, 오래 안 변하는 사실)·`terms`(용어 3~6개, 각 한 줄)·`qa`(질문 1~3개)·`angles`(나라별 강조점, `f` 포함)·`watch`·`first`(먼저 읽을 무료 기사 2~3개, 글 id)를 채웁니다. 이미 해설이 있으면 `key`·`why3.now`만 새 글에 맞게 고칩니다.
- 하루 넘게 새 글이 안 붙은 이슈(`delta:"same"` 계속)는 이슈가 60개를 넘을 때 먼저 뺍니다.

## 2. 단신 (`kind:"brief"`) 50개 이상
어디에도 안 묶인 뉴스(`k:"news"`, 이번 판 새 글 우선, `sm` 있는 글) 중 나라를 고르게(나라당 최대 3개, 한국 5개) 골라 `title`(한국어 한 문장)·`cat`·`kind:"brief"`·`where`·`key`(제목과 `sm`에 있는 내용만으로 1~2문장)·`items:[글 id 1개]`·`delta:"new"`·`method:"ai-v1"`. 광고·연재 홍보·운세·단순 날씨 예보는 뺍니다.

## 3. 흐름·나라 (`themes`, `countryDigest`)
`themes.ai`·`themes.eco`의 `flows`를 이번 판 글로 다시 묶습니다(갈래 4~6개, 갈래마다 근거 글 id 3~6개). `countryDigest`를 나라마다 2문장으로 다시 씁니다.

## 4. 이름 사전 (`brief/ents.json`)
이번 판 이슈·단신 제목과 `key`에 나온 인물·정당·지역·기관·용어 중 사전에 없는 이름을 더합니다. `map["표기"] = {t, r, d, o, c, a}` (`t`=person·party·org·place·term·event, `r`=한 줄 정체, `d`=2~4문장 배경, `o`=원어, `c`=나라 코드, `a`=다른 표기들). 표기는 **기사 속 한국어 표기 그대로**. 바뀌는 직책은 "기사 기준"을 붙입니다. 기존 항목은 지우지 않고, `updatedAt`을 바꿉니다. (사진은 로봇이 다음 회차에 자동으로 찾아 붙입니다.)

## 5. 댓글 분위기 (`brief/ED__cm.json`)
`map[글id].mood`가 비어 있는 글마다 `picks`의 댓글을 읽고 분위기 한 줄을 씁니다. `picks[].type`을 top·counter·insight·info·joke·claim 중 하나로 고치고, `ko`를 다듬습니다(`raw`는 현지 말투 번역, `orig`는 원문 그대로 둠). 욕설·혐오 표현은 순화합니다.

## 6. 저장
1. `editions/ED.json`, `brief/ents.json`, `brief/ED__cm.json`을 덮어씁니다. `editions/ED.json`의 `editedAt`에 지금 시각(KST)을 적습니다.
2. `python robot/reindex.py`
3. `git add data/sisa && git commit -m "시사: ED 해설(편집장)" && git pull --rebase && git push`
4. 한 줄로 결과를 남깁니다: 판 ID, 새 이슈·단신 수, 해설 쓴 이슈 수, 이름 추가 수, 실패한 단계.
