// 真实浏览器验证：滚动整页后统计每个 canvas 的不透明像素数（空图表约为 0）
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
await sleep(2500)
await send('Runtime.evaluate', {
  expression: `window.scrollTo(0, document.body.scrollHeight)`,
  returnByValue: true,
})
await sleep(2500)
const expr = `(() => {
  const out = [];
  for (const c of document.querySelectorAll('canvas')) {
    try {
      const ctx = c.getContext('2d');
      const img = ctx.getImageData(0, 0, c.width, c.height).data;
      let n = 0;
      for (let i = 3; i < img.length; i += 4) if (img[i] > 10) n++;
      out.push(c.width + 'x' + c.height + ':' + n);
    } catch (e) {
      out.push('err:' + e.message);
    }
  }
  return out.join('\\n');
})()`
const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true })
console.log(res.result.value)
process.exit(0)
