<script setup lang="ts">
import * as THREE from 'three'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CategoryRow, Subitem } from '@/types'
import ProjectDetailDrawer from './ProjectDetailDrawer.vue'
import CategoryGalaxy from './CategoryGalaxy.vue'

const store = useAppStore()

const mountRef = ref<HTMLDivElement | null>(null)
const labelsRef = ref<HTMLDivElement | null>(null)
const tooltipRef = ref<HTMLDivElement | null>(null)
const webglOk = ref(true)
const level = ref(0) // 0 = 总览, 1 = 类别内部
const selectedCategory = ref<CategoryRow | null>(null)
const colorMode = ref<'batch' | 'province'>('batch')
const drawer = ref<{ visible: boolean; subitem: Subitem | null }>({ visible: false, subitem: null })

// 本地专属低饱和宇宙色板（仅本组件使用）
const GALAXY_COLORS: Record<string, string> = {
  民间文学: '#aeb9cf',
  传统音乐: '#7fa6b8',
  传统舞蹈: '#8fb0a8',
  传统戏剧: '#9d8fc0',
  曲艺: '#c9a98a',
  '传统体育、游艺与杂技': '#7f9bb8',
  传统美术: '#b78fa6',
  传统技艺: '#b8a877',
  传统医药: '#7fa99f',
  民俗: '#a8947a',
}

// 批次同色系渐变（2006 → 2021 由暗到亮）
const BATCH_RAMP = ['#6e5f3a', '#8a7446', '#a58a54', '#c2a468', '#dfc384']
const PROVINCE_PALETTE = [
  '#9fb4c7', '#c7b0a0', '#a8c0ae', '#b8a8cc', '#c9c4a8', '#8fb4c4',
  '#c9a8b8', '#a8c9b8', '#c4b89e', '#9ec4c4', '#b8a8c9', '#c4c0a8',
]

const BATCH_YEARS = [2006, 2008, 2011, 2014, 2021]

// ---------- Three.js 资源 ----------
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let raf = 0
let last = 0

interface CatBody {
  row: CategoryRow
  pos: THREE.Vector3
  group: THREE.Group
  core: THREE.Sprite
  halo: THREE.Sprite
  dust: THREE.Points
  proxy: THREE.Mesh
  coreBase: number
  haloBase: number
  dustBase: number
  fade: number
  fadeTarget: number
}

let catBodies: CatBody[] = []

interface DetailParticle {
  subitem: Subitem
  province: string
  batch: number
  anchorIdx: number
}

let detailPoints: THREE.Points | null = null
let detailParticles: DetailParticle[] = []
let detailOpacity = 0

// 相机
const CAM = { theta: 0.6, phi: 1.15, radius: 560 }
const CAM_TARGET = { theta: 0.6, phi: 1.15, radius: 560, fov: 55 }
const camTarget = new THREE.Vector3()
const ORIGIN = new THREE.Vector3(0, 0, 0)
let detailCenter = new THREE.Vector3()
const THETA_MIN = -1.5
const THETA_MAX = 1.5
const PHI_MIN = 0.85
const PHI_MAX = 1.4
const R_MIN = 340
const R_MAX = 780
const FOV_MIN = 38
const FOV_MAX = 62

let parallaxX = 0
let parallaxY = 0

// 过渡
let trans: { kind: 'enter' | 'exit'; t: number; dur: number } | null = null

// 交互
let dragging = false
let lastX = 0
let lastY = 0
let downX = 0
let downY = 0
let hoverCat = -1
let hoverParticle = -1
let tooltipPos = { x: 0, y: 0 }

// 背景资源
let bgStars: THREE.Points | null = null
let midDust: THREE.Points | null = null
let nebulas: THREE.Sprite[] = []
let galaxyPlane: THREE.Mesh | null = null

const reduced =
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// ---------- 工具 ----------
function makeRadialTexture(color: string, innerAlpha: number, outerAlpha: number, size = 128): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (ctx) {
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    g.addColorStop(0, color)
    g.addColorStop(0.15, `${color}${Math.round(innerAlpha * 255).toString(16).padStart(2, '0')}`)
    g.addColorStop(1, `${color}${Math.round(outerAlpha * 255).toString(16).padStart(2, '0')}`)
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
  }
  return new THREE.CanvasTexture(canvas)
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

function disposeObject(o: THREE.Object3D) {
  const mesh = o as THREE.Mesh
  if (mesh.geometry) mesh.geometry.dispose()
  const mat = mesh.material as THREE.Material | THREE.Material[] | undefined
  if (Array.isArray(mat)) mat.forEach((m) => m.dispose())
  else mat?.dispose()
  const mm = mat as THREE.MeshBasicMaterial | undefined
  mm?.map?.dispose()
  const sprite = o as THREE.Sprite
  const sm = sprite.material as THREE.SpriteMaterial | undefined
  sm?.map?.dispose()
  sm?.dispose()
}

function clearScene() {
  if (!scene) return
  const list: THREE.Object3D[] = []
  scene.traverse((o) => {
    if (o !== scene) list.push(o)
  })
  list.forEach((o) => {
    scene!.remove(o)
    disposeObject(o)
  })
}

// ---------- 背景 ----------
function makeGalaxyTexture(): THREE.CanvasTexture {
  const size = 1024
  const c = document.createElement('canvas')
  c.width = size
  c.height = size
  const ctx = c.getContext('2d')
  if (!ctx) return new THREE.CanvasTexture(c)
  let a = 987654321
  const rng = () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  // 中央亮核
  const core = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size * 0.16)
  core.addColorStop(0, 'rgba(225,230,248,0.5)')
  core.addColorStop(0.3, 'rgba(130,150,210,0.26)')
  core.addColorStop(1, 'rgba(40,60,120,0)')
  ctx.fillStyle = core
  ctx.fillRect(0, 0, size, size)
  // 旋臂
  const arms = [
    { color: 'rgba(96,138,214,0.17)', off: 0 },
    { color: 'rgba(138,116,204,0.15)', off: (Math.PI * 2) / 3 },
    { color: 'rgba(64,152,184,0.15)', off: (Math.PI * 4) / 3 },
  ]
  ctx.globalCompositeOperation = 'lighter'
  arms.forEach((arm) => {
    for (let i = 0; i < 2600; i += 1) {
      const t = rng()
      const r = size * (0.05 + 0.42 * Math.pow(t, 0.7))
      const theta = arm.off + t * Math.PI * 4.2 + (rng() - 0.5) * 0.35
      const x = size / 2 + Math.cos(theta) * r
      const y = size / 2 + Math.sin(theta) * r * 0.55
      ctx.globalAlpha = 0.05 + rng() * 0.12
      ctx.fillStyle = arm.color
      ctx.fillRect(x, y, 2, 2)
    }
  })
  // 椭圆盘面星尘
  const palette = ['#5f82b8', '#6fb4c9', '#7d6fc4', '#9fb4c7', '#b08a5f']
  for (let i = 0; i < 2600; i += 1) {
    let x = 0
    let y = 0
    do {
      x = rng() * 2 - 1
      y = rng() * 2 - 1
    } while (x * x + y * y > 1)
    ctx.globalAlpha = 0.05 + rng() * 0.12
    ctx.fillStyle = palette[Math.floor(rng() * palette.length)]
    ctx.fillRect(size / 2 + x * size * 0.46, size / 2 + y * size * 0.24, 1.4, 1.4)
  }
  ctx.globalCompositeOperation = 'source-over'
  ctx.globalAlpha = 1
  ctx.filter = 'blur(5px)'
  ctx.drawImage(c, 0, 0)
  ctx.filter = 'none'
  return new THREE.CanvasTexture(c)
}

function buildBackground() {
  if (!scene) return
  // 银河盘面（主背景，位于所有天体之后）
  const galaxyTex = makeGalaxyTexture()
  const galaxyMat = new THREE.MeshBasicMaterial({
    map: galaxyTex,
    transparent: true,
    opacity: 0.62,
    depthWrite: false,
    side: THREE.DoubleSide,
  })
  galaxyPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), galaxyMat)
  galaxyPlane.scale.set(2600, 1300, 1)
  galaxyPlane.rotation.x = -Math.PI / 2 + 0.16
  galaxyPlane.rotation.z = 0.25
  galaxyPlane.renderOrder = -1
  scene.add(galaxyPlane)

  // 远景恒星
  const starGeo = new THREE.BufferGeometry()
  const starCount = 1500
  const starPos = new Float32Array(starCount * 3)
  for (let i = 0; i < starCount; i += 1) {
    const r = 650 + Math.random() * 300
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    starPos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    starPos[i * 3 + 1] = r * Math.cos(phi)
    starPos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta)
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3))
  const starMat = new THREE.PointsMaterial({
    size: 1.1,
    color: '#9fb4c7',
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  })
  bgStars = new THREE.Points(starGeo, starMat)
  scene.add(bgStars)

  // 中景星尘
  const dustGeo = new THREE.BufferGeometry()
  const dustCount = 420
  const dustPos = new Float32Array(dustCount * 3)
  for (let i = 0; i < dustCount; i += 1) {
    const r = 280 + Math.random() * 360
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    dustPos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    dustPos[i * 3 + 1] = r * Math.cos(phi) * 0.6
    dustPos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta)
  }
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
  const dustMat = new THREE.PointsMaterial({
    size: 1.6,
    color: '#7d93a8',
    transparent: true,
    opacity: 0.3,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  })
  midDust = new THREE.Points(dustGeo, dustMat)
  scene.add(midDust)

  // 极淡星云
  const nebulaSpecs = [
    { color: '#1b2a4a', pos: new THREE.Vector3(-260, 120, -260), scale: 620, opacity: 0.1 },
    { color: '#2a2140', pos: new THREE.Vector3(280, -100, -220), scale: 560, opacity: 0.09 },
    { color: '#143a40', pos: new THREE.Vector3(-140, -160, 260), scale: 520, opacity: 0.08 },
    { color: '#3a2f1a', pos: new THREE.Vector3(180, 140, 240), scale: 480, opacity: 0.07 },
  ]
  nebulas = nebulaSpecs.map((n) => {
    const tex = makeRadialTexture(n.color, 0.5, 0)
    const spr = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: n.opacity, depthWrite: false }),
    )
    spr.position.copy(n.pos)
    spr.scale.setScalar(n.scale)
    scene?.add(spr)
    return spr
  })
}

// ---------- 类别天体（LEVEL 1） ----------
function categorySize(count: number, min: number, max: number): number {
  const t = max > min ? Math.sqrt((count - min) / (max - min)) : 0.5
  return 26 + 14 * t
}

function buildCatBodies() {
  if (!scene || !store.dataset) return
  const cats = store.dataset.categories
  const counts = cats.map((c) => c.subitem_count)
  const min = Math.min(...counts)
  const max = Math.max(...counts)
  // 十颗天体排成一圈（XZ 平面圆环，轻微错位避免机械感）
  const RING_R = 250
  const layout: Array<[number, number, number]> = cats.map((_, i) => {
    const angle = (i / cats.length) * Math.PI * 2 - Math.PI / 2
    const jx = i % 2 === 0 ? 6 : -6
    const jz = i % 3 === 0 ? 5 : -4
    return [Math.cos(angle) * RING_R + jx, (i % 4) - 2, Math.sin(angle) * RING_R + jz]
  })
  catBodies = cats.map((row, i) => {
    const pos = new THREE.Vector3(...layout[i])
    const color = GALAXY_COLORS[row.category] ?? '#aeb9cf'
    const size = categorySize(row.subitem_count, min, max)
    const group = new THREE.Group()

    const coreTex = makeRadialTexture(color, 0.95, 0)
    const core = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: coreTex, transparent: true, depthWrite: false }),
    )
    core.scale.setScalar(size * 1.4)

    const haloTex = makeRadialTexture(color, 0.3, 0)
    const halo = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: haloTex, transparent: true, opacity: 0.16, depthWrite: false }),
    )
    halo.scale.setScalar(size * 5.2)

    const dustCount = 70 + Math.round((row.subitem_count / max) * 90)
    const dustGeo = new THREE.BufferGeometry()
    const dustPos = new Float32Array(dustCount * 3)
    for (let d = 0; d < dustCount; d += 1) {
      const rr = size * (1.15 + Math.random() * 1.3)
      const th = Math.random() * Math.PI * 2
      const ph = Math.acos(2 * Math.random() - 1)
      dustPos[d * 3] = rr * Math.sin(ph) * Math.cos(th)
      dustPos[d * 3 + 1] = rr * Math.cos(ph) * 0.7
      dustPos[d * 3 + 2] = rr * Math.sin(ph) * Math.sin(th)
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
    const dustMat = new THREE.PointsMaterial({
      size: 1.3,
      color,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
      sizeAttenuation: true,
    })
    const dust = new THREE.Points(dustGeo, dustMat)

    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(size * 1.8, 10, 10),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
    )

    group.add(core)
    group.add(halo)
    group.add(dust)
    group.add(proxy)
    group.position.copy(pos)
    scene!.add(group)
    proxy.userData.index = i

    return {
      row,
      pos,
      group,
      core,
      halo,
      dust,
      proxy,
      coreBase: 1,
      haloBase: 0.16,
      dustBase: 0.5,
      fade: 1,
      fadeTarget: 1,
    }
  })
}

// ---------- 类别内部星系（LEVEL 2） ----------
function buildDetail(cat: CategoryRow) {
  if (!scene || !store.dataset) return
  const items = store.dataset.subitems.filter((s) => s.category === cat.category)
  // 粒子球体：该类别全部真实子项，围绕球心形成 3D 高斯球
  const R = 125 + 25 * Math.sqrt(items.length / 629)
  const palIdx = new Map<string, number>()
  for (const s of items) {
    if (!palIdx.has(s.province)) palIdx.set(s.province, palIdx.size)
  }
  detailParticles = items.map((s) => ({
    subitem: s,
    province: s.province,
    batch: s.batch_no,
    anchorIdx: palIdx.get(s.province) ?? 0,
  }))

  const geo = new THREE.BufferGeometry()
  const pos = new Float32Array(detailParticles.length * 3)
  const col = new Float32Array(detailParticles.length * 3)
  detailParticles.forEach((p, i) => {
    const th = Math.random() * Math.PI * 2
    const ph = Math.acos(2 * Math.random() - 1)
    const u = Math.max(1e-6, Math.random())
    const r = Math.min(R, R * Math.sqrt(-2 * Math.log(u)) * 0.8)
    pos[i * 3] = Math.sin(ph) * Math.cos(th) * r
    pos[i * 3 + 1] = Math.cos(ph) * r * 0.92
    pos[i * 3 + 2] = Math.sin(ph) * Math.sin(th) * r
  })
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  applyParticleColors(geo, col)
  const mat = new THREE.PointsMaterial({
    size: 2.4,
    vertexColors: true,
    transparent: true,
    opacity: 0,
    depthWrite: false,
    sizeAttenuation: true,
  })
  detailPoints = new THREE.Points(geo, mat)
  scene.add(detailPoints)
}

function applyParticleColors(geo: THREE.BufferGeometry, col: Float32Array) {
  detailParticles.forEach((p, i) => {
    const c = new THREE.Color('#dfc384')
    if (colorMode.value === 'batch') {
      const idx = Math.max(0, Math.min(4, BATCH_YEARS.indexOf(p.subitem.publish_year)))
      c.set(BATCH_RAMP[idx])
    } else {
      c.set(PROVINCE_PALETTE[p.anchorIdx % PROVINCE_PALETTE.length])
    }
    c.multiplyScalar(0.7 + Math.random() * 0.4)
    col[i * 3] = c.r
    col[i * 3 + 1] = c.g
    col[i * 3 + 2] = c.b
  })
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3))
}

function destroyDetail() {
  if (detailPoints && scene) {
    scene.remove(detailPoints)
    detailPoints.geometry.dispose()
    ;(detailPoints.material as THREE.Material).dispose()
  }
  detailPoints = null
  detailParticles = []
}

// ---------- 相机 ----------
function clampCam() {
  CAM_TARGET.theta = Math.max(THETA_MIN, Math.min(THETA_MAX, CAM_TARGET.theta))
  CAM_TARGET.phi = Math.max(PHI_MIN, Math.min(PHI_MAX, CAM_TARGET.phi))
  CAM_TARGET.radius = Math.max(R_MIN, Math.min(R_MAX, CAM_TARGET.radius))
  CAM_TARGET.fov = Math.max(FOV_MIN, Math.min(FOV_MAX, CAM_TARGET.fov))
}

function updateCamera(dt: number) {
  if (!camera) return
  const k = 1 - Math.exp(-5 * dt)
  CAM.theta += (CAM_TARGET.theta - CAM.theta) * k
  CAM.phi += (CAM_TARGET.phi - CAM.phi) * k
  CAM.radius += (CAM_TARGET.radius - CAM.radius) * k
  camera.fov += (CAM_TARGET.fov - camera.fov) * k
  camera.updateProjectionMatrix()
  const th = CAM.theta + parallaxX * 0.06
  const ph = Math.max(0.3, Math.min(Math.PI - 0.3, CAM.phi + parallaxY * 0.04))
  const sinPhi = Math.sin(ph)
  camera.position.set(
    camTarget.x + CAM.radius * sinPhi * Math.sin(th),
    camTarget.y + CAM.radius * Math.cos(ph),
    camTarget.z + CAM.radius * sinPhi * Math.cos(th),
  )
  camera.lookAt(camTarget)
}

// ---------- 标签 / 工具提示 ----------
function updateLabels() {
  if (!labelsRef.value || !camera) return
  const cam = camera
  const w = labelsRef.value.clientWidth
  const h = labelsRef.value.clientHeight
  const v = new THREE.Vector3()
  catBodies.forEach((b, i) => {
    const el = labelsRef.value!.children[i] as HTMLElement
    if (!el) return
    v.copy(b.pos).project(cam)
    if (v.z > 1) {
      el.style.display = 'none'
      return
    }
    el.style.display = 'block'
    el.style.left = `${(v.x * 0.5 + 0.5) * w}px`
    el.style.top = `${(-v.y * 0.5 + 0.5) * h}px`
    const dist = cam.position.distanceTo(b.pos)
    const distFade = Math.max(0.35, Math.min(1, 1.35 - dist / 900))
    const hover = hoverCat === i ? 1 : 0.6
    el.style.opacity = String(b.fade * distFade * hover)
  })
}

function showTooltip(html: string) {
  if (!tooltipRef.value) return
  tooltipRef.value.innerHTML = html
  tooltipRef.value.style.display = 'block'
  tooltipRef.value.style.left = `${Math.min(tooltipPos.x + 14, (tooltipRef.value.parentElement?.clientWidth ?? 800) - 220)}px`
  tooltipRef.value.style.top = `${tooltipPos.y + 16}px`
}

function hideTooltip() {
  if (tooltipRef.value) tooltipRef.value.style.display = 'none'
}

// ---------- 主循环 ----------
function loop(t: number) {
  const dt = Math.min(0.05, (t - last) / 1000 || 0.016)
  last = t
  const time = t / 1000

  if (trans) {
    trans.t += dt
    const p = Math.min(1, trans.t / trans.dur)
    const e = easeInOutCubic(p)
    if (trans.kind === 'enter') {
      const b = catBodies.find((x) => x.row.category === selectedCategory.value?.category)
      if (b) {
        CAM_TARGET.theta = Math.atan2(b.pos.x, b.pos.z)
        CAM_TARGET.phi = 1.05
        CAM_TARGET.radius = b.pos.length() * 0.45 + 150
        CAM_TARGET.fov = 45
        camTarget.lerpVectors(ORIGIN, detailCenter, e)
        b.dust.scale.setScalar(1 + e * 0.5)
      }
      catBodies.forEach((x) => {
        x.fadeTarget = x.row.category === selectedCategory.value?.category ? 1 : 1 - e
      })
      detailOpacity = p > 0.55 ? (p - 0.55) / 0.45 : 0
      if (p >= 1) {
        level.value = 1
        camTarget.copy(detailCenter)
        trans = null
      }
    } else {
      CAM_TARGET.theta = 0.6
      CAM_TARGET.phi = 1.15
      CAM_TARGET.radius = 560
      CAM_TARGET.fov = 55
      camTarget.lerpVectors(detailCenter, ORIGIN, e)
      catBodies.forEach((x) => {
        x.fadeTarget = e
        if (x.row.category === selectedCategory.value?.category) x.dust.scale.setScalar(1 + (1 - e) * 0.5)
      })
      detailOpacity = 1 - e
      if (p >= 1) {
        destroyDetail()
        camTarget.copy(ORIGIN)
        detailCenter.set(0, 0, 0)
        selectedCategory.value = null
        level.value = 0
        trans = null
      }
    }
  }

  // 天体淡入淡出与呼吸
  catBodies.forEach((b, i) => {
    const k = 1 - Math.exp(-3 * dt)
    b.fade += (b.fadeTarget - b.fade) * k
    const breathe = 1 + Math.sin(time * 0.4 + i) * 0.04
    const hover = hoverCat === i ? 1.25 : 1
    ;(b.core.material as THREE.SpriteMaterial).opacity = b.coreBase * b.fade * hover
    ;(b.halo.material as THREE.SpriteMaterial).opacity = b.haloBase * b.fade * hover * breathe
    ;(b.dust.material as THREE.PointsMaterial).opacity = b.dustBase * b.fade
    b.dust.rotation.y += dt * (0.05 + (hoverCat === i ? 0.03 : 0))
  })
  if (detailPoints) {
    ;(detailPoints.material as THREE.PointsMaterial).opacity = detailOpacity
    detailPoints.rotation.y += dt * 0.04
  }

  // 背景
  if (galaxyPlane) {
    const gTarget = level.value === 1 ? 0 : 0.62
    const gk = 1 - Math.exp(-3 * dt)
    const gm = galaxyPlane.material as THREE.MeshBasicMaterial
    gm.opacity += (gTarget - gm.opacity) * gk
  }
  if (galaxyPlane) galaxyPlane.rotation.z += dt * 0.004
  if (bgStars) {
    bgStars.rotation.y += dt * 0.002
    ;(bgStars.material as THREE.PointsMaterial).opacity = 0.45 + 0.08 * Math.sin(time * 0.25)
  }
  if (midDust) {
    midDust.rotation.y += dt * 0.012
    midDust.rotation.x += dt * 0.004
  }
  nebulas.forEach((n, i) => {
    const s = n.scale.x
    n.scale.setScalar(s * (1 + Math.sin(time * 0.12 + i * 1.7) * 0.03))
  })

  updateCamera(dt)
  updateLabels()
  renderer?.render(scene!, camera!)
  raf = requestAnimationFrame(loop)
}

// ---------- 初始化 ----------
function initThree(): boolean {
  if (!mountRef.value) return false
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  } catch {
    return false
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(mountRef.value.clientWidth, mountRef.value.clientHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.domElement.style.display = 'block'
  mountRef.value.appendChild(renderer.domElement)
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(55, mountRef.value.clientWidth / mountRef.value.clientHeight, 1, 3000)
  camera.position.set(0, 0, 560)
  buildBackground()
  buildCatBodies()
  createLabelEls()
  bindPointer()
  return true
}

function createLabelEls() {
  if (!labelsRef.value || !store.dataset) return
  labelsRef.value.innerHTML = ''
  store.dataset.categories.forEach((c) => {
    const div = document.createElement('div')
    div.className = 'galaxy-label'
    div.innerHTML = `<b>${c.category}</b><span>${c.subitem_count.toLocaleString()} 个地区子项</span>`
    labelsRef.value!.appendChild(div)
  })
}

// ---------- 交互 ----------
function bindPointer() {
  const el = renderer?.domElement
  if (!el) return
  el.addEventListener('pointerdown', (e) => {
    dragging = true
    lastX = e.clientX
    lastY = e.clientY
    downX = e.clientX
    downY = e.clientY
  })
  window.addEventListener('pointermove', (e) => {
    tooltipPos = { x: e.clientX, y: e.clientY }
    if (dragging) {
      if (trans) return
      CAM_TARGET.theta -= (e.clientX - lastX) * 0.004
      CAM_TARGET.phi -= (e.clientY - lastY) * 0.003
      clampCam()
      lastX = e.clientX
      lastY = e.clientY
      return
    }
    const rect = el.getBoundingClientRect()
    parallaxX = ((e.clientX - rect.left) / rect.width) * 2 - 1
    parallaxY = ((e.clientY - rect.top) / rect.height) * 2 - 1
    if (level.value === 0) pickCategory(e.clientX, e.clientY)
    else pickParticle(e.clientX, e.clientY)
  })
  window.addEventListener('pointerup', (e) => {
    dragging = false
    if (Math.hypot(e.clientX - downX, e.clientY - downY) < 6) {
      if (level.value === 0) clickCategory(e.clientX, e.clientY)
      else clickParticle(e.clientX, e.clientY)
    }
  })
  el.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault()
      if (trans) return
      CAM_TARGET.radius = Math.max(R_MIN, Math.min(R_MAX, CAM_TARGET.radius + e.deltaY * 0.6))
    },
    { passive: false },
  )
}

function pickCategory(px: number, py: number) {
  if (!camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((px - rect.left) / rect.width) * 2 - 1, -((py - rect.top) / rect.height) * 2 + 1)
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObjects(catBodies.map((b) => b.proxy))
  if (hits.length) {
    const i = (hits[0].object as THREE.Mesh).userData.index as number
    if (hoverCat !== i) {
      hoverCat = i
      const b = catBodies[i]
      const pct = ((b.row.subitem_count / (store.dataset?.metadata.cleaned_subitem_count ?? 1)) * 100).toFixed(1)
      showTooltip(
        `<b>${b.row.category}</b><br/>地区子项：${b.row.subitem_count.toLocaleString()}<br/>占全部非遗：${pct}%<br/><span class="tip-hint">点击进入星系 →</span>`,
      )
    }
  } else if (hoverCat !== -1) {
    hoverCat = -1
    hideTooltip()
  }
}

function clickCategory(px: number, py: number) {
  if (!camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((px - rect.left) / rect.width) * 2 - 1, -((py - rect.top) / rect.height) * 2 + 1)
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObjects(catBodies.map((b) => b.proxy))
  if (hits.length) {
    const i = (hits[0].object as THREE.Mesh).userData.index as number
    enterCategory(i)
  }
}

function enterCategory(i: number) {
  const b = catBodies[i]
  selectedCategory.value = b.row
  level.value = 0
  buildDetail(b.row)
  if (detailPoints) detailPoints.position.copy(b.pos)
  detailCenter.copy(b.pos)
  detailOpacity = 0
  hoverCat = -1
  hideTooltip()
  trans = { kind: 'enter', t: 0, dur: 1.8 }
}

function exitToOverview() {
  if (trans) return
  trans = { kind: 'exit', t: 0, dur: 1.6 }
}

function pickParticle(px: number, py: number) {
  if (!camera || !renderer || !detailPoints) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((px - rect.left) / rect.width) * 2 - 1, -((py - rect.top) / rect.height) * 2 + 1)
  const raycaster = new THREE.Raycaster()
  raycaster.params.Points.threshold = 12
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObject(detailPoints)
  if (hits.length) {
    const idx = hits[0].index ?? -1
    if (idx >= 0 && idx < detailParticles.length) {
      if (hoverParticle !== idx) {
        hoverParticle = idx
        const p = detailParticles[idx].subitem
        showTooltip(
          `<b>${p.project_name}</b><br/>编号：${p.project_code}<br/>地区：${p.region_raw}<br/>批次：${p.publish_year} · ${p.entry_type === 'new' ? '新增' : '扩展'}<br/>保护单位：${p.protection_unit || '—'}`,
        )
      }
    }
  } else if (hoverParticle !== -1) {
    hoverParticle = -1
    hideTooltip()
  }
}

function clickParticle(px: number, py: number) {
  if (!camera || !renderer || !detailPoints) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((px - rect.left) / rect.width) * 2 - 1, -((py - rect.top) / rect.height) * 2 + 1)
  const raycaster = new THREE.Raycaster()
  raycaster.params.Points.threshold = 12
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObject(detailPoints)
  if (hits.length) {
    const idx = hits[0].index ?? -1
    if (idx >= 0 && idx < detailParticles.length) {
      drawer.value = { visible: true, subitem: detailParticles[idx].subitem }
    }
  }
}

function applyColorMode() {
  if (detailPoints) {
    const col = new Float32Array(detailParticles.length * 3)
    applyParticleColors(detailPoints.geometry as THREE.BufferGeometry, col)
    ;(detailPoints.geometry.getAttribute('color') as THREE.BufferAttribute).needsUpdate = true
  }
}

// ---------- 详情信息 ----------
const detailInfo = computed(() => {
  const cat = selectedCategory.value
  if (!cat || !store.dataset) return null
  const items = store.dataset.subitems.filter((s) => s.category === cat.category)
  const years = items.map((s) => s.publish_year)
  const provinces = new Set(items.map((s) => s.province))
  return {
    name: cat.category,
    count: cat.subitem_count,
    provinceCount: provinces.size,
    firstYear: years.length ? Math.min(...years) : null,
    lastYear: years.length ? Math.max(...years) : null,
  }
})

function onResize() {
  if (!renderer || !camera || !mountRef.value) return
  const w = mountRef.value.clientWidth
  const h = mountRef.value.clientHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

// ---------- 生命周期 ----------
onMounted(async () => {
  await nextTick()
  if (!initThree()) {
    webglOk.value = false
    return
  }
  if (store.dataset) rebuildAll()
  window.addEventListener('resize', onResize)
  raf = requestAnimationFrame(loop)
})

watch(
  () => store.dataset,
  () => {
    if (scene && store.dataset) rebuildAll()
  },
  { deep: false },
)

function rebuildAll() {
  clearScene()
  buildBackground()
  buildCatBodies()
  createLabelEls()
  if (level.value === 1 && selectedCategory.value) {
    buildDetail(selectedCategory.value)
    detailOpacity = 1
  }
}

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', onResize)
  clearScene()
  renderer?.dispose()
  renderer?.domElement.remove()
  renderer = null
  scene = null
  camera = null
})
</script>

<template>
  <div class="galaxy3d-wrap">
    <div class="galaxy3d-head">
      <h3>十类非遗星系</h3>
      <p class="small muted">
        总览十大非遗天体 · 点击进入类别，探索由真实地区子项组成的内部星系。
      </p>
    </div>

    <div ref="mountRef" class="galaxy3d-canvas card">
      <CategoryGalaxy v-if="!webglOk" />
      <div ref="labelsRef" class="galaxy-labels"></div>
      <div ref="tooltipRef" class="galaxy-tooltip"></div>

      <div v-if="level === 1 && detailInfo" class="detail-panel">
        <div class="detail-title">
          <span>{{ detailInfo.name }}</span>
          <button type="button" class="btn btn-sm" @click="exitToOverview">← 返回十类星系</button>
        </div>
        <div class="detail-meta">
          {{ detailInfo.count.toLocaleString() }} 个地区子项 · {{ detailInfo.provinceCount }} 个省级地区 ·
          首次公布 {{ detailInfo.firstYear ?? '—' }} · 最近批次 {{ detailInfo.lastYear ?? '—' }}
        </div>
        <div class="detail-modes">
          <button
            type="button"
            class="chip"
            :class="{ active: colorMode === 'batch' }"
            @click="colorMode = 'batch'; applyColorMode()"
          >
            按批次
          </button>
          <button
            type="button"
            class="chip"
            :class="{ active: colorMode === 'province' }"
            @click="colorMode = 'province'; applyColorMode()"
          >
            按省份
          </button>
        </div>
      </div>

    </div>
  </div>

  <ProjectDetailDrawer
    :subitem="drawer.subitem"
    :visible="drawer.visible"
    @close="drawer.visible = false"
  />
</template>

<style scoped>
.galaxy3d-wrap {
  margin-top: 16px;
}
.galaxy3d-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.galaxy3d-head h3 {
  margin: 0;
  font-size: 16px;
}
.galaxy3d-canvas {
  position: relative;
  overflow: hidden;
  padding: 0;
  height: 560px;
  background: radial-gradient(120% 90% at 50% 40%, #0d1524 0%, #0a1019 55%, #070c13 100%);
}
.galaxy-labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.galaxy-label {
  position: absolute;
  transform: translate(-50%, -130%);
  text-align: center;
  pointer-events: none;
  transition: opacity 0.3s ease;
  white-space: nowrap;
}
.galaxy-label b {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #d8d2c2;
  letter-spacing: 0.08em;
  text-shadow: 0 0 12px rgba(10, 14, 22, 0.9);
}
.galaxy-label span {
  display: block;
  font-size: 10px;
  color: rgba(184, 178, 160, 0.75);
  text-shadow: 0 0 8px rgba(10, 14, 22, 0.9);
}
.galaxy-tooltip {
  position: absolute;
  display: none;
  z-index: 5;
  pointer-events: none;
  max-width: 240px;
  background: rgba(10, 14, 22, 0.88);
  border: 1px solid var(--gold-dim);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ink-0);
  backdrop-filter: blur(4px);
}
.galaxy-tooltip b {
  color: var(--gold);
}
.galaxy-tooltip .tip-hint {
  color: var(--gold);
  opacity: 0.85;
}
.detail-panel {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 6;
  max-width: 320px;
  background: rgba(10, 14, 22, 0.78);
  border: 1px solid var(--gold-dim);
  border-radius: 10px;
  padding: 10px 12px;
  backdrop-filter: blur(6px);
}
.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--gold);
}
.detail-meta {
  margin-top: 6px;
  font-size: 12px;
  color: var(--ink-1);
}
.detail-modes {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
@media (max-width: 860px) {
  .galaxy3d-canvas {
    height: 420px;
  }
  .detail-panel {
    left: 8px;
    right: 8px;
    max-width: none;
  }
}
</style>
