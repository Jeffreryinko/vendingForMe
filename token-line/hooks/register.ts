import type { Register } from 'claude-code'

// 토큰량 상태 줄 — 턴이 끝날 때마다 프롬프트 아래 한 줄을 고쳐 씀.
// 입력 = 새 입력 + 캐시 쓰기 + 캐시 읽기. 합계는 모드가 다시 불러와지면 0부터 다시 셈.
const k = (n: number) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(n))

export const register: Register = on => {
  let input = 0
  let output = 0
  let turns = 0

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const u = done.usage ?? e.usage
    if (u) {
      input += u.input_tokens + u.cache_creation_input_tokens + u.cache_read_input_tokens
      output += u.output_tokens
      turns++
    }
    const s = await $.session.usage()
    const ctx = s.context.percent != null ? ` · 문맥 ${s.context.percent}% (${k(s.context.tokens ?? 0)}/${k(s.context.window)})` : ''
    const usd = s.cost ? ` · $${s.cost.usd.toFixed(2)}` : ''
    // 요금제 한도: 5시간 창·주간 창을 얼마나 썼는지 (마지막 응답이 알려 준 값)
    const NAME: Record<string, string> = { five_hour: '5시간', seven_day: '주간', spend_limit: '지출 한도' }
    const lim = s.rateLimits.map(r => `${NAME[r.kind] ?? r.kind} ${r.percentUsed}%`).join(' · ')
    $.ui.status(`토큰 입력 ${k(input)} · 출력 ${k(output)} · ${turns}턴${ctx}${usd}${lim ? ' · 한도 ' + lim : ''}`)
    return done
  })
}
