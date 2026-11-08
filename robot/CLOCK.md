# 로봇 정시 알람 (Supabase)

GitHub 무료 예약(schedule)은 붐비면 1~4시간 늦거나 아예 건너뜁니다(11월 초 기록: 시사 하루 8번 중 3번).
그래서 Supabase(무료)의 pg_cron 이 정각마다 GitHub의 '실행 버튼'(workflow_dispatch)을 대신 누릅니다. 토큰 0, 돈 0.

- Supabase 프로젝트 `vendingforme` → `robot.dispatch('<파일>.yml')` 함수, `cron.job` 의 `vfm-*` 알람 (UTC, 워크플로의 cron 과 같은 시각)
- GitHub 열쇠: Supabase Vault 비밀 `github_dispatch` (세밀 토큰, 이 저장소만, 권한 Actions: Read and write)
- 기록: `select * from robot.clock_log order by id desc limit 20;` / 응답: `select * from net._http_response order by id desc limit 5;`
- GitHub 자체 예약은 '예비'로 남김. 각 워크플로의 `guard` 작업이 "정시 알람이 최근에 이미 돌렸으면" 건너뜀 (기준: 시사·트렌드 150분, 도구 240분, 뇌·라디오 600분, AI·역사 1,200분, 원문 번역 2,880분)

열쇠가 없거나 만료되면 알람은 기록만 남기고, 로봇은 예전처럼 GitHub 예약으로만 돕니다.
