// 真实时间验证 ECharts 柱状图生长动画（需要 Chrome --remote-debugging-port=9222 指向测试页）
const list = await (await fetch('http://127.0.0.1:9222/json')).json()
const page = list.find((t) => t.type === 'page')
if (!page) throw new Error('no page target')
const ws = new WebSocket(page.webSocketDebuggerUrl)
await new Promise((res) => (ws.onopen = res))
let id = 0
const pending = new Map()
ws.onmessage = (e) => {
  const m = JSON.parse(e.data)
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m.result)
    pending.delete(m.id)
  }
}
function send(method, params) {
  return new Promise((res) => {
    const i = ++id
    pending.set(i, res)
    ws.send(JSON.stringify({ id: i, method, params }))
  })
}
await send('Runtime.enable')
await new Promise((r) => setTimeout(r, 600))
const res = await send('Runtime.evaluate', {
  expression: `document.body.getAttribute('data-h')`,
  returnByValue: true,
})
console.log('页面自身采样（t=300/900/2600ms, c1单阶段/c2两阶段）:', res.result.value)
process.exit(0)
