// 验证懒加载：页面加载后【不滚动】统计 canvas，检查图表是否过早初始化
const port = process.env.CDP_PORT ?? '9222'
const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json()
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
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
await send('Runtime.enable')
await sleep(4000)
const expr = `(() => {
  const out = [];
  for (const c of document.querySelectorAll('canvas')) {
    out.push(c.width + 'x' + c.height);
  }
  return JSON.stringify({
    scrollY: window.scrollY,
    bodyH: document.body.scrollHeight,
    innerH: window.innerHeight,
    canvases: out,
  });
})()`
const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true })
console.log(res.result.value)
process.exit(0)
