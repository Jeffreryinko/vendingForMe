# .claude — Claude가 이 저장소에서 쓰는 도구 (2026-11-06 설치)

사이트·로봇 동작과는 상관없음. Claude가 이 저장소를 고칠 때만 읽는다. 폴더를 지우면 원래대로.

| 도구 | 하는 일 | 부르는 법 | 출처 |
|---|---|---|---|
| ponytail | 코드를 가장 짧게 고치고, 답 끝에 '안 한 것·위험' 1~2줄 | 코딩할 때 자동 / `ponytail lite·ultra·off` | DietrichGebert/ponytail (MIT) |
| impeccable | 화면 비평·점검·다듬기, 'AI 티 나는 디자인' 검사 | `/impeccable critique 뇌 탭 오늘 화면` 등 | pbakaus/impeccable (Apache-2.0) |
| security-audit | 보안 조언 / "전체 점검해 줘"라고 하면 보고서 작성 | "로그인·Supabase 보안 점검해 줘" | cloudflare/security-audit-skill (MIT) |

- impeccable 자동 검사(`settings.json`): 대화 시작 · 파일 고칠 때마다(5초) · 끝날 때(30초). AI 안 씀. 화면 파일(html·css·js)만 봄.
- impeccable 엔진(22MB)은 저장소에 안 올림 → 처음 쓸 때 GitHub 공식 배포에서 받아 지문(체크섬) 확인 후 씀.
- 끄기: impeccable 자동 검사만 끄려면 `settings.json` 삭제. 도구 하나를 빼려면 `skills/` 안 그 폴더 삭제.
- 설치하지 않은 것: ponytail의 대화 훅·상태줄·비용 기록(설명 파일만 넣음).
