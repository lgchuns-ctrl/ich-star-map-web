<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const labelsRef = ref<HTMLDivElement | null>(null)

// ---------- 固定种子随机 ----------
function hashString(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function mulberry32(seed: number) {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// ---------- 颜色 ----------
const ACCENT: Record<string, string> = {
  民间文学: '#d8b98a',
  传统音乐: '#8a9fd8',
  传统舞蹈: '#8fc4b0',
  传统戏剧: '#a98ab8',
  曲艺: '#d09a74',
  '传统体育、游艺与杂技': '#7fb4cc',
  传统美术: '#c08fb0',
  传统技艺: '#b8c07a',
  传统医药: '#8fc4c4',
  民俗: '#a89fd0',
}
const ENV_BLUE = '#4a6a9a'
const WHITE = '#dfe7f5'

const EN_TITLES: Record<string, string> = {
  民间文学: 'FOLK LITERATURE',
  传统音乐: 'TRADITIONAL MUSIC',
  传统舞蹈: 'TRADITIONAL DANCE',
  传统戏剧: 'TRADITIONAL OPERA',
  曲艺: 'QUYI',
  '传统体育、游艺与杂技': 'SPORTS & ACROBATICS',
  传统美术: 'FINE ARTS',
  传统技艺: 'TRADITIONAL CRAFTS',
  传统医药: 'TRADITIONAL MEDICINE',
  民俗: 'FOLK CUSTOMS',
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function mix(a: [number, number, number], b: [number, number, number], t: number): string {
  const r = Math.round(a[0] + (b[0] - a[0]) * t)
  const g = Math.round(a[1] + (b[1] - a[1]) * t)
  const bl = Math.round(a[2] + (b[2] - a[2]) * t)
  return `rgb(${r},${g},${bl})`
}

// ---------- 2.5D 固定视角参数 ----------
// 银河盘面轻微倾斜 + 弱透视，制造空间感但保持固定构图
const TILT = 0.3
const F = 1500

// 十个类别在银河主平面上的 3D 位置（x,y 为银河平面坐标，z 为轻微前后层次）
interface RegionDef {
  name: string
  x: number
  y: number
  z: number
  shape: 'ellipse' | 'swirl' | 'band' | 'arc' | 'cluster'
  rot: number
}

const REGIONS: RegionDef[] = [
  { name: '传统技艺', x: 0, y: 0, z: 0, shape: 'swirl', rot: 0.2 },
  { name: '民俗', x: 0.16, y: 0.05, z: 8, shape: 'arc', rot: -0.4 },
  { name: '传统音乐', x: -0.06, y: 0.6, z: 30, shape: 'ellipse', rot: 0.5 },
  { name: '传统舞蹈', x: 0.58, y: 0.4, z: 26, shape: 'band', rot: -0.2 },
  { name: '民间文学', x: -0.6, y: 0.34, z: 34, shape: 'swirl', rot: -0.6 },
  { name: '传统戏剧', x: -0.56, y: -0.16, z: 24, shape: 'ellipse', rot: 0.3 },
  { name: '曲艺', x: -0.3, y: -0.56, z: 36, shape: 'cluster', rot: 0.8 },
  { name: '传统美术', x: 0.62, y: -0.14, z: 28, shape: 'band', rot: 0.6 },
  { name: '传统医药', x: 0.32, y: -0.42, z: 32, shape: 'arc', rot: 0.1 },
  { name: '传统体育、游艺与杂技', x: 0.1, y: -0.6, z: 38, shape: 'cluster', rot: -0.3 },
]

const GALAXY_R = 0.62

// ---------- 画布状态 ----------
let W = 0
let H = 0
let raf = 0
let t0 = 0
let reduced = false
let parallaxX = 0
let parallaxY = 0

interface Star {
  x: number
  y: number
  r: number
  o: number
  p: number
  sp: number
  c: string
}
interface Dust {
  x: number
  y: number
  r: number
  o: number
  vx: number
  vy: number
  c: string
}

let farStars: Star[] = []
let dust: Dust[] = []
let microDust: Dust[] = []
let nebulas: Array<{ tex: HTMLCanvasElement; x: number; y: number; s: number; vx: number; vy: number }> = []
let dataCanvas: HTMLCanvasElement | null = null
let regionScreen: Array<{ name: string; x: number; y: number; scale: number }> = []

// ---------- 3D -> 2D 投影 ----------
function project3D(px: number, py: number, pz: number) {
  // 银河盘面绕 X 轴倾斜
  const ct = Math.cos(TILT)
  const st = Math.sin(TILT)
  const y1 = py * ct - pz * st
  const z1 = py * st + pz * ct
  const scale = F / (F - z1)
  const cx = W * 0.5 + parallaxX * 10
  const cy = H * 0.52 + parallaxY * 7
  return { x: cx + px * scale, y: cy + y1 * scale, scale }
}

// ---------- 星云纹理 ----------
function makeNebulaTexture(colors: Array<[string, number]>, seed: number): HTMLCanvasElement {
  const size = 512
  const c = document.createElement('canvas')
  c.width = size
  c.height = size
  const ctx = c.getContext('2d')
  if (!ctx) return c
  const rng = mulberry32(seed)
  ctx.filter = 'blur(28px)'
  for (const [color, alpha] of colors) {
    const x = size * (0.25 + rng() * 0.5)
    const y = size * (0.25 + rng() * 0.5)
    const r = size * (0.25 + rng() * 0.3)
    const g = ctx.createRadialGradient(x, y, 0, x, y, r)
    g.addColorStop(0, color)
    g.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.globalAlpha = alpha
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(x, y, r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.filter = 'none'
  ctx.globalAlpha = 1
  for (let i = 0; i < 260; i += 1) {
    ctx.globalAlpha = 0.03 + rng() * 0.07
    ctx.fillStyle = '#9fb4d8'
    ctx.fillRect(rng() * size, rng() * size, 1 + rng() * 2, 1 + rng() * 2)
  }
  ctx.globalAlpha = 1
  return c
}

// ---------- 数据层（3610 真实子项，仅在类别星团内） ----------
function buildDataLayer() {
  if (!store.dataset) return
  dataCanvas = document.createElement('canvas')
  dataCanvas.width = W
  dataCanvas.height = H
  const ctx = dataCanvas.getContext('2d')
  if (!ctx) return

  const cats = store.dataset.categories
  const counts = new Map(cats.map((c) => [c.category, c.subitem_count]))
  const max = Math.max(...cats.map((c) => c.subitem_count))
  const min = Math.min(...cats.map((c) => c.subitem_count))
  regionScreen = []

  const byCat = new Map<
    string,
    { center: { x: number; y: number; z: number }; radius: number; def: RegionDef }
  >()
  cats.forEach((cat, i) => {
    const def = REGIONS[i]
    const t = max > min ? Math.sqrt((cat.subitem_count - min) / (max - min)) : 0.5
    const radius = (0.1 + 0.055 * t) * Math.min(W, H)
    const center = {
      x: def.x * GALAXY_R * Math.min(W, H),
      y: def.y * GALAXY_R * Math.min(W, H),
      z: def.z,
    }
    const sp = project3D(center.x, center.y, center.z)
    regionScreen.push({ name: cat.category, x: sp.x, y: sp.y, scale: sp.scale })
    byCat.set(cat.category, { center, radius, def })
  })

  for (const s of store.dataset.subitems) {
    const rng = mulberry32(hashString(s.subitem_id))
    const info = byCat.get(s.category)
    if (!info) continue
    const { center, radius, def } = info
    const a = rng() * Math.PI * 2
    const u = Math.max(1e-6, rng())
    let r = radius * Math.sqrt(-2 * Math.log(u)) * 0.85
    let shape = 1
    if (def.shape === 'ellipse') shape = 1 + 0.22 * Math.cos(2 * a)
    else if (def.shape === 'band') shape = 1 + 0.42 * Math.cos(2 * a)
    else if (def.shape === 'arc') shape = 1 + 0.5 * Math.cos(a + def.rot)
    else if (def.shape === 'swirl') shape = 1 + 0.2 * Math.sin(3 * a)
    else shape = 1 + 0.12 * Math.sin(2 * a) + 0.08 * Math.cos(3 * a)
    r *= shape
    let aspect = 0.6
    if (def.shape === 'band') aspect = 0.38
    else if (def.shape === 'ellipse') aspect = 0.55
    else if (def.shape === 'arc') aspect = 0.7
    else if (def.shape === 'swirl') aspect = 0.5
    const twist = 0.14 * Math.pow(r / radius, 2) * radius
    const rot = def.rot
    const lx = Math.cos(a) * r + Math.sin(a) * twist
    const ly = (Math.sin(a) * r + Math.cos(a) * twist * 0.5) * aspect
    const lz = (rng() - 0.5) * radius * 0.4
    const wx = center.x + Math.cos(rot) * lx - Math.sin(rot) * ly
    const wy = center.y + Math.sin(rot) * lx + Math.cos(rot) * ly
    const wz = center.z + lz
    const p = project3D(wx, wy, wz)
    if (p.x < -4 || p.x > W + 4 || p.y < -4 || p.y > H + 4) continue

    const accent = hexToRgb(ACCENT[s.category] ?? '#aeb9cf')
    const env = hexToRgb(ENV_BLUE)
    const roll = rng()
    let color: string
    if (roll < 0.6) color = mix(accent, env, 0.5)
    else if (roll < 0.76) color = mix(accent, [255, 255, 255], 0.45)
    else if (roll < 0.88) color = WHITE
    else color = mix(env, accent, 0.25)
    ctx.globalAlpha = (0.18 + rng() * 0.55) * (0.92 + p.scale * 0.02)
    ctx.fillStyle = color
    const size = (roll < 0.9 ? 1 + rng() * 0.6 : 1.8 + rng() * 0.8) * p.scale
    ctx.fillRect(p.x, p.y, size, size)
  }
  ctx.globalAlpha = 1
}

// ---------- 背景（装饰层） ----------
function buildBackground() {
  const rng = mulberry32(20260807)
  farStars = []
  for (let i = 0; i < 2000; i += 1) {
    let x: number
    let y: number
    if (rng() < 0.55) {
      const a = rng() * Math.PI * 2
      const r = Math.sqrt(rng()) * Math.min(W, H) * 0.55
      x = W * 0.5 + Math.cos(a) * r
      y = H * 0.52 + Math.sin(a) * r * 0.8
    } else {
      x = rng() * W
      y = rng() * H
    }
    x = Math.max(0, Math.min(W - 1, x))
    y = Math.max(0, Math.min(H - 1, y))
    const roll = rng()
    const c = roll < 0.7 ? '#9fb4c7' : roll < 0.88 ? '#c7d4e8' : '#c9b08a'
    farStars.push({
      x,
      y,
      r: rng() < 0.9 ? 0.3 + rng() * 0.7 : 1.2 + rng() * 0.9,
      o: 0.18 + rng() * 0.42,
      p: rng() * Math.PI * 2,
      sp: 0.2 + rng() * 0.6,
      c,
    })
  }

  dust = []
  for (let i = 0; i < 3200; i += 1) {
    const a = rng() * Math.PI * 2
    const r = Math.pow(rng(), 0.75) * Math.min(W, H) * 0.5
    let x = W * 0.5 + Math.cos(a) * r
    let y = H * 0.52 + Math.sin(a) * r * 0.8
    if (rng() < 0.25) {
      x = rng() * W
      y = rng() * H
    }
    const palette = ['#5f82b8', '#6fb4c9', '#7d6fc4', '#4a5f9a', '#b08a5f', '#a86a9a']
    dust.push({
      x,
      y,
      r: 0.4 + rng() * 0.8,
      o: 0.08 + rng() * 0.28,
      vx: (rng() - 0.5) * 0.06,
      vy: (rng() - 0.5) * 0.06,
      c: palette[Math.floor(rng() * palette.length)],
    })
  }

  microDust = []
  for (let i = 0; i < 1500; i += 1) {
    const palette = ['#5f82b8', '#6fb4c9', '#7d6fc4', '#9fb4c7']
    microDust.push({
      x: rng() * W,
      y: rng() * H,
      r: 0.4 + rng() * 0.7,
      o: 0.04 + rng() * 0.09,
      vx: (rng() - 0.5) * 0.04,
      vy: (rng() - 0.5) * 0.04,
      c: palette[Math.floor(rng() * palette.length)],
    })
  }

  nebulas = [
    { tex: makeNebulaTexture([['#24407a', 0.14], ['#1b2a52', 0.1]], 11), x: W * 0.3, y: H * 0.32, s: Math.max(W, H) * 1.05, vx: 0.4, vy: 0.15 },
    { tex: makeNebulaTexture([['#4a2f7a', 0.12], ['#2a1f4a', 0.1]], 22), x: W * 0.68, y: H * 0.42, s: Math.max(W, H) * 0.95, vx: -0.3, vy: 0.2 },
    { tex: makeNebulaTexture([['#1f5a6a', 0.12], ['#143a4a', 0.1]], 33), x: W * 0.5, y: H * 0.66, s: Math.max(W, H) * 0.9, vx: 0.25, vy: -0.2 },
    { tex: makeNebulaTexture([['#3a2f5a', 0.1], ['#24304a', 0.09]], 44), x: W * 0.18, y: H * 0.6, s: Math.max(W, H) * 0.8, vx: -0.2, vy: -0.12 },
    { tex: makeNebulaTexture([['#5a3a22', 0.06], ['#3a2a1a', 0.05]], 55), x: W * 0.82, y: H * 0.28, s: Math.max(W, H) * 0.7, vx: 0.15, vy: 0.1 },
  ]
}

// ---------- 标签 ----------
function buildLabels() {
  if (!labelsRef.value || !store.dataset) return
  const labels = labelsRef.value
  labels.innerHTML = ''
  store.dataset.categories.forEach((cat) => {
    const c = regionScreen.find((r) => r.name === cat.category)
    if (!c) return
    const div = document.createElement('div')
    div.className = 'nebula-label'
    div.innerHTML = `<i>${EN_TITLES[cat.category] ?? ''}</i><b>${cat.category}</b><span>${cat.subitem_count.toLocaleString()} 个地区子项</span>`
    div.style.left = `${c.x}px`
    div.style.top = `${c.y}px`
    div.style.transform = `translate(-50%,-50%) scale(${0.92 + c.scale * 0.08})`
    labels.appendChild(div)
  })
}

// ---------- 主循环 ----------
function draw(t: number) {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const dt = t - t0
  t0 = t
  const sec = t / 1000

  ctx.clearRect(0, 0, W, H)
  const bg = ctx.createRadialGradient(W * 0.5, H * 0.52, 0, W * 0.5, H * 0.52, Math.max(W, H) * 0.72)
  bg.addColorStop(0, '#101b30')
  bg.addColorStop(0.5, '#0a1220')
  bg.addColorStop(1, '#060a12')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, W, H)

  // 星云
  ctx.globalCompositeOperation = 'screen'
  nebulas.forEach((n) => {
    n.x += n.vx * dt * 0.001
    n.y += n.vy * dt * 0.001
    if (n.x < -n.s) n.x = W + n.s
    if (n.x > W + n.s) n.x = -n.s
    if (n.y < -n.s) n.y = H + n.s
    if (n.y > H + n.s) n.y = -n.s
    ctx.globalAlpha = 0.55
    ctx.drawImage(n.tex, n.x - n.s / 2, n.y - n.s / 2, n.s, n.s)
  })
  ctx.globalCompositeOperation = 'source-over'
  ctx.globalAlpha = 1

  // 远景恒星
  for (const s of farStars) {
    const a = s.o * (0.72 + 0.28 * Math.sin(sec * s.sp + s.p))
    ctx.globalAlpha = a
    ctx.fillStyle = s.c
    ctx.fillRect(s.x, s.y, s.r, s.r)
  }

  // 微尘 + 星尘
  ctx.globalCompositeOperation = 'lighter'
  for (const d of microDust) {
    d.x += d.vx * dt * 0.06
    d.y += d.vy * dt * 0.06
    if (d.x < 0) d.x += W
    if (d.x >= W) d.x -= W
    if (d.y < 0) d.y += H
    if (d.y >= H) d.y -= H
    ctx.globalAlpha = d.o
    ctx.fillStyle = d.c
    ctx.fillRect(d.x, d.y, d.r, d.r)
  }
  for (const d of dust) {
    d.x += d.vx * dt * 0.06
    d.y += d.vy * dt * 0.06
    if (d.x < 0) d.x += W
    if (d.x >= W) d.x -= W
    if (d.y < 0) d.y += H
    if (d.y >= H) d.y -= H
    ctx.globalAlpha = d.o
    ctx.fillStyle = d.c
    ctx.fillRect(d.x, d.y, d.r, d.r)
  }
  ctx.globalCompositeOperation = 'source-over'
  ctx.globalAlpha = 1

  // 数据层（含视差整体偏移）
  if (dataCanvas) {
    ctx.save()
    ctx.translate(parallaxX * 10, parallaxY * 7)
    ctx.drawImage(dataCanvas, 0, 0)
    ctx.restore()
  }

  // 类别锚点微光（呼吸），放在数据层之上作为视觉锚点
  regionScreen.forEach((c, i) => {
    const a = 0.05 + 0.025 * Math.sin(sec * 0.4 + i * 1.3)
    const grd = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, 30 * c.scale)
    grd.addColorStop(0, `rgba(180,200,235,${a})`)
    grd.addColorStop(1, 'rgba(180,200,235,0)')
    ctx.fillStyle = grd
    ctx.beginPath()
    ctx.arc(c.x, c.y, 30 * c.scale, 0, Math.PI * 2)
    ctx.fill()
  })

  if (!reduced) raf = requestAnimationFrame(draw)
}

// ---------- 尺寸/重建 ----------
function rebuild() {
  const canvas = canvasRef.value
  const wrap = canvas?.parentElement
  if (!canvas || !wrap) return
  W = wrap.clientWidth
  H = wrap.clientHeight
  if (W < 20 || H < 20) return
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = W * dpr
  canvas.height = H * dpr
  canvas.style.width = `${W}px`
  canvas.style.height = `${H}px`
  const ctx = canvas.getContext('2d')
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  buildBackground()
  buildDataLayer()
  buildLabels()
}

function onPointerMove(e: PointerEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  parallaxX = ((e.clientX - rect.left) / rect.width) * 2 - 1
  parallaxY = ((e.clientY - rect.top) / rect.height) * 2 - 1
}

onMounted(async () => {
  reduced =
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  await new Promise((r) => requestAnimationFrame(r))
  rebuild()
  window.addEventListener('resize', rebuild)
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  if (!reduced) raf = requestAnimationFrame(draw)
  else draw(0)
})

watch(
  () => store.dataset,
  () => {
    if (store.dataset) rebuild()
  },
  { deep: false },
)

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', rebuild)
  window.removeEventListener('pointermove', onPointerMove)
})
</script>

<template>
  <div class="nebula-wrap">
    <div class="nebula-head">
      <h3>十类非遗星系</h3>
      <p class="small muted">3610 颗文化星辰 · 十类非遗银河</p>
    </div>
    <div class="nebula-canvas card">
      <canvas ref="canvasRef"></canvas>
      <div ref="labelsRef" class="nebula-labels"></div>
    </div>
  </div>
</template>

<style scoped>
.nebula-wrap {
  margin-top: 16px;
}
.nebula-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.nebula-head h3 {
  margin: 0;
  font-size: 16px;
}
.nebula-canvas {
  position: relative;
  overflow: hidden;
  padding: 0;
  height: 560px;
  cursor: default;
}
.nebula-labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.nebula-label {
  position: absolute;
  text-align: center;
  pointer-events: none;
  line-height: 1.35;
  transform-origin: center;
}
.nebula-label i {
  display: block;
  font-style: normal;
  font-size: 8px;
  letter-spacing: 0.22em;
  color: rgba(160, 178, 210, 0.55);
  text-shadow: 0 0 8px rgba(6, 10, 18, 0.9);
}
.nebula-label b {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(214, 222, 238, 0.8);
  letter-spacing: 0.1em;
  text-shadow: 0 0 10px rgba(6, 10, 18, 0.95);
}
.nebula-label span {
  display: block;
  font-size: 9px;
  color: rgba(168, 182, 208, 0.6);
  text-shadow: 0 0 8px rgba(6, 10, 18, 0.95);
}
@media (max-width: 860px) {
  .nebula-canvas {
    height: 420px;
  }
  .nebula-label i,
  .nebula-label span {
    display: none;
  }
  .nebula-label b {
    font-size: 12px;
  }
}
</style>
