// 验证：TOP15 图表在进站时不初始化；滚动到它附近后才开始生长动画
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
const evalv = async (expression) => {
  const res = await send('Runtime.evaluate', { expression, returnByValue: true })
  return res.result.value
}
const opaqueExpr = `(() => {
  const c = [...document.querySelectorAll('canvas')].find((x) => x.height === 440 && x.width > 1000);
  if (!c) return 'NO_CHART';
  const img = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 3; i < img.length; i += 4) if (img[i] > 10) n++;
  return c.width + 'x' + c.height + ':' + n;
})()`
await send('Runtime.enable')
await sleep(3500)
console.log('进站未滚动:', await evalv(opaqueExpr))
await evalv(`(() => {
  document.getElementById('inheritors').scrollIntoView({ block: 'center' });
})()`)
for (const t of [0, 250, 600, 1100, 2000]) {
  if (t) await sleep(t)
  console.log(`滚动后 +${t}ms:`, await evalv(opaqueExpr))
}
process.exit(0)
