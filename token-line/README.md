# token-line — 토큰량 상태 줄

Claude Code 프롬프트 아래에 이번 대화의 토큰량을 한 줄로 띄워요. 턴이 끝날 때마다 고쳐 써요.

```
토큰 입력 182.4k · 출력 6.1k · 7턴 · 문맥 23% (46.0k/200.0k) · $0.84 · 한도 5시간 18% · 주간 41%
```

- **입력**: 새 입력 + 캐시 쓰기 + 캐시 읽기 토큰을 모두 더한 값
- **출력**: Claude가 쓴 토큰
- **문맥**: 지금 문맥 창을 얼마나 채웠는지
- **한도**: 요금제의 5시간·주간 사용 한도를 몇 % 썼는지 (Claude가 알려 줄 때만 보임)
- **$**: `/cost` 와 같은 이번 대화의 비용 (구독 사용자는 참고용)

입력·출력 합계는 모드가 다시 불러와지면(새 대화, 다시 시작) 0부터 다시 세요. AI를 따로 부르지 않아서 이 줄 자체는 토큰을 쓰지 않아요.

## 설치

터미널의 Claude Code 프롬프트에서:

```
/plugin install token-line --marketplace Jeffreryinko/vendingForMe
```

마켓플레이스를 추가할지 물으면 `y`, 그다음 설치 범위를 고르면 돼요.

셸에서:

```bash
claude plugin install token-line --marketplace Jeffreryinko/vendingForMe
```
