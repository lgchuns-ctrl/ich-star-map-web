<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CategoryRow } from '@/types'
import { CATEGORY_COLORS } from '@/types'

const store = useAppStore()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const selected = ref<CategoryRow | null>(null)

interface GalaxyStar {
  x: number
  y: number
  z: number
  r: number
  color: string
  row: CategoryRow
}

interface View {
  scale: number
  tx: number
  ty: number
}

const stars = computed<GalaxyStar[]>(() => {
  const cats = store.dataset?.categories ?? []
  if (!cats.length) return []
  const max = Math.max(1, ...cats.map((c) => c.subitem_count))
  return cats.map((row, i) => {
    const t = cats.length > 1 ? i / (cats.length - 1) : 0.5
    const angle = t * Math.PI * 2 * 1.7 - Math.PI / 2
    const radius = 0.3 + 0.62 * t
    return {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius * 0.52,
      z: 0.55 + 0.45 * Math.sin(angle * 2 + 1),
      r: 11 + 17 * (row.subitem_count / max),
      color: CATEGORY_COLORS[row.category] ?? '#d9b877',
      row,
    }
  })
})

let raf = 0
let W = 0
let H = 0
let dpr = 1
let hoverIndex = -1
let view: View = { scale: 1, tx: 0, ty: 0 }
let targetView: View = { scale: 1, tx: 0, ty: 0 }
let zooming = false
const localStars: Array<{ x: number; y: number; r: number; p: number }> = []

function toScreen(star: GalaxyStar, v: View) {
  return {
    x: star.x * W * 0.5 * v.scale + v.tx,
    y: star.y * H * 0.5 * v.scale + v.ty,
    r: star.r * (0.7 + 0.6 * star.z) * v.scale,
  }
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, W, H)

  // 背景点缀星
  for (const s of localStars) {
    const tw = 0.35 + 0.3 * Math.sin(performance.now() * 0.001 + s.p)
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(217,184,119,${tw})`
    ctx.fill()
  }

  if (!stars.value.length) return
  ctx.save()
  ctx.translate(view.tx, view.ty)
  ctx.scale(view.scale, view.scale)

  // 星座连线
  const n = stars.value.length
  ctx.lineWidth = 1.2 / view.scale
  for (let i = 0; i < n; i += 1) {
    const a = stars.value[i]
    const b = stars.value[(i + 1) % n]
    ctx.strokeStyle = `rgba(217,184,119,${0.14 * a.z * b.z})`
    ctx.beginPath()
    ctx.moveTo(a.x * W * 0.5, a.y * H * 0.5)
    ctx.lineTo(b.x * W * 0.5, b.y * H * 0.5)
    ctx.stroke()
  }

  // 星点
  stars.value.forEach((s, i) => {
    const sx = s.x * W * 0.5
    const sy = s.y * H * 0.5
    const r = s.r * (0.7 + 0.6 * s.z)
    const hot = i === hoverIndex || selected.value?.category === s.row.category
    const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, r * 3)
    glow.addColorStop(0, s.color)
    glow.addColorStop(0.35, `${s.color}55`)
    glow.addColorStop(1, `${s.color}00`)
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(sx, sy, r * (hot ? 3.2 : 2.6), 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = s.color
    ctx.beginPath()
    ctx.arc(sx, sy, r, 0, Math.PI * 2)
    ctx.fill()
    if (hot) {
      ctx.strokeStyle = 'rgba(242,232,213,0.9)'
      ctx.lineWidth = 1.5 / view.scale
      ctx.beginPath()
      ctx.arc(sx, sy, r + 4 / view.scale, 0, Math.PI * 2)
      ctx.stroke()
    }
    const labelSize = Math.max(10, 13 * view.scale) / view.scale
    ctx.font = `${labelSize}px "PingFang SC","Microsoft YaHei",sans-serif`
    ctx.textAlign = 'center'
    ctx.fillStyle = hot ? '#f2e8d5' : 'rgba(185,173,150,0.85)'
    ctx.fillText(s.row.category, sx, sy + r + 18 / view.scale)
  })
  ctx.restore()
}

function step() {
  const k = 0.12
  view.scale += (targetView.scale - view.scale) * k
  view.tx += (targetView.tx - view.tx) * k
  view.ty += (targetView.ty - view.ty) * k
  if (Math.abs(targetView.scale - view.scale) < 0.002) {
    view = { ...targetView }
    zooming = false
  }
  draw()
  raf = requestAnimationFrame(step)
}

function zoomTo(star: GalaxyStar, row: CategoryRow) {
  selected.value = row
  targetView = {
    scale: 2.8,
    tx: W / 2 - star.x * W * 0.5 * 2.8,
    ty: H / 2 - star.y * H * 0.5 * 2.8,
  }
  zooming = true
}

function zoomOut() {
  selected.value = null
  targetView = { scale: 1, tx: 0, ty: 0 }
  zooming = true
}

function onMove(e: MouseEvent) {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  hoverIndex = -1
  stars.value.forEach((s, i) => {
    const p = toScreen(s, view)
    if ((mx - p.x) ** 2 + (my - p.y) ** 2 < (p.r + 14) ** 2) hoverIndex = i
  })
}

function onClick(e: MouseEvent) {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  for (let i = 0; i < stars.value.length; i += 1) {
    const s = stars.value[i]
    const p = toScreen(s, view)
    if ((mx - p.x) ** 2 + (my - p.y) ** 2 < (p.r + 12) ** 2) {
      if (selected.value?.category === s.row.category) zoomOut()
      else zoomTo(s, s.row)
      return
    }
  }
  if (selected.value) zoomOut()
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const parent = canvas.parentElement
  W = parent?.clientWidth ?? canvas.clientWidth
  H = parent?.clientHeight ?? canvas.clientHeight
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = W * dpr
  canvas.height = H * dpr
  canvas.style.width = `${W}px`
  canvas.style.height = `${H}px`
  localStars.length = 0
  const count = Math.min(70, Math.floor((W * H) / 18000))
  for (let i = 0; i < count; i += 1) {
    localStars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.1 + 0.3,
      p: Math.random() * Math.PI * 2,
    })
  }
  if (!zooming) {
    view = { scale: 1, tx: 0, ty: 0 }
    targetView = { ...view }
  }
  draw()
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  raf = requestAnimationFrame(step)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resize)
})
</script>

<template>
  <div class="galaxy-wrap">
    <div class="galaxy-head">
      <h3>十类互动星系</h3>
      <p class="small muted">星点大小 = 地区子项数量 · 点击星点放大查看类别详情</p>
    </div>
    <div class="galaxy-canvas card">
      <canvas
        ref="canvasRef"
        class="galaxy"
        @mousemove="onMove"
        @mouseleave="hoverIndex = -1"
        @click="onClick"
      ></canvas>
    </div>

    <div v-if="selected" class="galaxy-panel card">
      <div class="panel-top">
        <h4 :style="{ color: CATEGORY_COLORS[selected.category] }">{{ selected.category }}</h4>
        <button type="button" class="btn btn-sm" @click="zoomOut">返回星图</button>
      </div>
      <div class="panel-stats">
        <div class="p-stat"><b>{{ selected.subitem_count }}</b><span>地区子项</span></div>
        <div class="p-stat"><b>{{ selected.project_count }}</b><span>独立项目</span></div>
        <div class="p-stat"><b>{{ selected.inheritor_count }}</b><span>传承人</span></div>
        <div class="p-stat">
          <b>{{ selected.inheritor_coverage ? (selected.inheritor_coverage * 100).toFixed(1) : 0 }}%</b>
          <span>覆盖率</span>
        </div>
        <div class="p-stat"><b>{{ selected.province_count }}</b><span>覆盖省份</span></div>
        <div class="p-stat"><b>{{ selected.batch_count }}</b><span>批次</span></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.galaxy-wrap {
  margin-top: 16px;
}
.galaxy-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.galaxy-head h3 {
  margin: 0;
  font-size: 16px;
}
.galaxy-canvas {
  overflow: hidden;
  padding: 0;
}
.galaxy {
  display: block;
  cursor: pointer;
  min-height: 420px;
}
.galaxy-panel {
  margin-top: 12px;
}
.panel-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.panel-top h4 {
  margin: 0;
  font-size: 18px;
}
.panel-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  margin-top: 12px;
}
.p-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-0);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 4px;
}
.p-stat b {
  color: var(--ink-0);
  font-size: 16px;
}
.p-stat span {
  font-size: 11px;
  color: var(--ink-2);
}
@media (max-width: 860px) {
  .galaxy {
    min-height: 320px;
  }
  .panel-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
