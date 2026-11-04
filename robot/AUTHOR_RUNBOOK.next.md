# (제안) 이야기 작가 루틴 — 새 방식. 사용자가 고르기 전까지는 쓰지 않아요.

지금 루틴(`AUTHOR_RUNBOOK.md`)은 매일 새벽 5편을 AI로 새로 씁니다. 새 방식은 이렇게 바꿔요.

1. 원문은 한 번에 크게 모아 둡니다 — `이야기 위키백과 한꺼번에 모으기` 작업(Actions, 손으로 한 번 실행, 토큰 0)이
   목록 약 1,500개를 위키백과에서 가져와 `data/iyagi/wiki/` 에 정리합니다. 앱은 AI 글이 없는 이야기도 이 정리본으로 바로 보여 줘요.
2. AI 풀어쓰기는 "많이 보는 이야기"만 — 루틴은 매일 새로 5편 대신 아래 순서로 **최대 2편**:
   - `python robot/easy_tools.py requests iyagi` 의 사용자 요청 먼저
   - 그다음 `data/iyagi/wiki/_ai_queue.json` 위에서부터 (위키백과 조회수 높은 순)
3. 쓰는 모양·저장은 지금 `AUTHOR_RUNBOOK.md` 와 같습니다. 다만 자료는 `data/iyagi/wiki/<catId>.json`(이미 모은 원문)을 먼저 읽고, 모자랄 때만 웹을 찾습니다(토큰 절약).
4. 요청으로 쓴 이야기는 `python robot/easy_tools.py done iyagi <catId>` 로 완료 표시.
5. 요청도 없고 후보도 다 썼으면 그날은 쉽니다.

바꾸려면: `AUTHOR_RUNBOOK.md` 를 이 내용으로 바꾸고, 예약 작업 시간·이름은 그대로 두면 됩니다.
