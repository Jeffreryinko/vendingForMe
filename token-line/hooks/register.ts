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
    $.ui.status(`토큰 입력 ${k(input)} · 출력 ${k(output)} · ${turns}턴${ctx}${usd}`)
    return done
  })
}
