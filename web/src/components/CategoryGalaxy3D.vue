<script setup lang="ts">
import * as THREE from 'three'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CategoryRow } from '@/types'
import { CATEGORY_COLORS } from '@/types'
import CategoryGalaxy from './CategoryGalaxy.vue'

const store = useAppStore()

const mountRef = ref<HTMLDivElement | null>(null)
const videoRef = ref<HTMLVideoElement | null>(null)
const panelRef = ref<HTMLDivElement | null>(null)
const selected = ref<CategoryRow | null>(null)
const webglOk = ref(true)
const gestureState = ref<'idle' | 'loading' | 'on' | 'error'>('idle')
const gestureMsg = ref('')

interface Cluster {
  row: CategoryRow
  pos: THREE.Vector3
  proxy: THREE.Mesh
  glow: THREE.Sprite
  label: THREE.Sprite
  particleCount: number
}

const clusters = computed<Cluster[]>(() => {
  const cats = store.dataset?.categories ?? []
  return cats.map((row, i) => {
    const t = cats.length > 1 ? i / (cats.length - 1) : 0.5
    const angle = t * Math.PI * 2 * 1.7
    const R = 70 + t * 95
    const pos = new THREE.Vector3(
      Math.cos(angle) * R,
      Math.sin(angle * 2) * 24,
      Math.sin(angle) * R * 0.5,
    )
    const proxy = new THREE.Mesh(
      new THREE.SphereGeometry(36, 12, 12),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
    )
    proxy.position.copy(pos)
    proxy.userData.index = i
    const color = CATEGORY_COLORS[row.category] ?? '#d9b877'
    const glow = makeGlowSprite(color)
    glow.position.copy(pos)
    glow.scale.setScalar(120)
    const label = makeLabelSprite(row.category, color)
    label.position.set(pos.x, pos.y - 46, pos.z)
    return { row, pos, proxy, glow, label, particleCount: row.subitem_count }
  })
})

function makeGlowSprite(color: string): THREE.Sprite {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (ctx) {
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    g.addColorStop(0, `${color}ff`)
    g.addColorStop(0.35, `${color}66`)
    g.addColorStop(1, `${color}00`)
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
  }
  const tex = new THREE.CanvasTexture(canvas)
  return new THREE.Sprite(
    new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }),
  )
}

function makeLabelSprite(text: string, color: string): THREE.Sprite {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 64
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.font = 'bold 30px "PingFang SC","Microsoft YaHei",sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = 'rgba(10,14,22,0.75)'
    ctx.fillRect(0, 0, 256, 64)
    ctx.fillStyle = color
    ctx.fillText(text, 128, 32)
  }
  const tex = new THREE.CanvasTexture(canvas)
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }),
  )
  sprite.scale.set(92, 23, 1)
  return sprite
}

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let points: THREE.Points | null = null
let raf = 0
let last = 0

// 相机球坐标
const sph = { theta: 0.6, phi: 1.15, radius: 340 }
const sphTarget = { theta: 0.6, phi: 1.15, radius: 340 }
const MIN_R = 110
const MAX_R = 720

// 粒子
let particleData: Array<{
  center: THREE.Vector3
  offset: THREE.Vector3
  axis: THREE.Vector3
  speed: number
}> = []
let positions: Float32Array | null = null

// 鼠标
let dragging = false
let lastX = 0
let lastY = 0
let downX = 0
let downY = 0

// 手势
let hands: {
  setOptions: (o: Record<string, unknown>) => void
  onResults: (cb: (r: unknown) => void) => void
  send: (i: { image: unknown }) => Promise<void>
  close: () => void
} | null = null
let camStream: { stop: () => void } | null = null
let smoothedPalm = 0

const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function buildParticles() {
  const d = store.dataset
  if (!d || !scene) return
  const cl = clusters.value
  const counts = cl.map((c) => c.particleCount)
  const total = counts.reduce((a, b) => a + b, 0)
  positions = new Float32Array(total * 3)
  const pos = positions
  const colors = new Float32Array(total * 3)
  particleData = []
  let idx = 0
  const colorOf = (hex: string) => new THREE.Color(hex)
  cl.forEach((cluster, ci) => {
    const base = colorOf(CATEGORY_COLORS[cluster.row.category] ?? '#d9b877')
    for (let p = 0; p < counts[ci]; p += 1) {
      const offset = new THREE.Vector3(
        (Math.random() - 0.5) * 2 * 26,
        (Math.random() - 0.5) * 2 * 18,
        (Math.random() - 0.5) * 2 * 26,
      )
      const axis = new THREE.Vector3(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).normalize()
      particleData.push({
        center: cluster.pos.clone(),
        offset,
        axis,
        speed: reduced ? 0 : 0.15 + Math.random() * 0.5,
      })
      const c = base.clone().multiplyScalar(0.7 + Math.random() * 0.55)
      pos[idx * 3] = cluster.pos.x + offset.x
      pos[idx * 3 + 1] = cluster.pos.y + offset.y
      pos[idx * 3 + 2] = cluster.pos.z + offset.z
      colors[idx * 3] = c.r
      colors[idx * 3 + 1] = c.g
      colors[idx * 3 + 2] = c.b
      idx += 1
    }
  })
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  const mat = new THREE.PointsMaterial({
    size: 2.4,
    vertexColors: true,
    transparent: true,
    opacity: 0.95,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  })
  points = new THREE.Points(geo, mat)
  scene.add(points)
}

function disposeObject(o: THREE.Object3D) {
  const mesh = o as THREE.Mesh
  if (mesh.geometry) mesh.geometry.dispose()
  const mat = mesh.material as THREE.Material | THREE.Material[] | undefined
  if (Array.isArray(mat)) mat.forEach((m) => m.dispose())
  else mat?.dispose()
  const sprite = o as THREE.Sprite
  const sm = sprite.material as THREE.SpriteMaterial | undefined
  sm?.map?.dispose()
  sm?.dispose()
}

function rebuildScene() {
  if (!scene || !store.dataset) return
  const toRemove: THREE.Object3D[] = []
  scene.traverse((o) => {
    if (o !== scene) toRemove.push(o)
  })
  toRemove.forEach((o) => {
    scene!.remove(o)
    disposeObject(o)
  })
  for (const c of clusters.value) {
    scene.add(c.proxy)
    scene.add(c.glow)
    scene.add(c.label)
  }
  particleData = []
  buildParticles()
}

function updateParticles(dt: number) {
  if (!positions || !points) return
  for (let i = 0; i < particleData.length; i += 1) {
    const pd = particleData[i]
    if (pd.speed > 0) pd.offset.applyAxisAngle(pd.axis, pd.speed * dt)
    positions[i * 3] = pd.center.x + pd.offset.x
    positions[i * 3 + 1] = pd.center.y + pd.offset.y
    positions[i * 3 + 2] = pd.center.z + pd.offset.z
  }
  ;(points.geometry.getAttribute('position') as THREE.BufferAttribute).needsUpdate = true
}

function updateCamera(dt: number) {
  if (!camera) return
  const k = 1 - Math.exp(-6 * dt)
  sph.theta += (sphTarget.theta - sph.theta) * k
  sph.phi += (sphTarget.phi - sph.phi) * k
  sph.radius += (sphTarget.radius - sph.radius) * k
  const sinPhi = Math.sin(sph.phi)
  camera.position.set(
    sph.radius * sinPhi * Math.sin(sph.theta),
    sph.radius * Math.cos(sph.phi),
    sph.radius * sinPhi * Math.cos(sph.theta),
  )
  camera.lookAt(0, 0, 0)
}

function loop(t: number) {
  const dt = Math.min(0.05, (t - last) / 1000 || 0.016)
  last = t
  updateParticles(dt)
  updateCamera(dt)
  renderer?.render(scene!, camera!)
  raf = requestAnimationFrame(loop)
}

function initThree() {
  if (!mountRef.value) return false
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  } catch {
    return false
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(mountRef.value.clientWidth, mountRef.value.clientHeight)
  renderer.domElement.style.display = 'block'
  mountRef.value.appendChild(renderer.domElement)
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(55, mountRef.value.clientWidth / mountRef.value.clientHeight, 1, 3000)
  for (const c of clusters.value) {
    scene.add(c.proxy)
    scene.add(c.glow)
    scene.add(c.label)
  }
  buildParticles()
  bindPointer()
  return true
}

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
    if (!dragging) return
    sphTarget.theta -= (e.clientX - lastX) * 0.005
    sphTarget.phi = Math.max(0.25, Math.min(Math.PI - 0.25, sphTarget.phi - (e.clientY - lastY) * 0.005))
    lastX = e.clientX
    lastY = e.clientY
  })
  window.addEventListener('pointerup', (e) => {
    dragging = false
    if (Math.hypot(e.clientX - downX, e.clientY - downY) < 6) pick(e.clientX, e.clientY)
  })
  el.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault()
      sphTarget.radius = Math.max(MIN_R, Math.min(MAX_R, sphTarget.radius + e.deltaY * 0.35))
    },
    { passive: false },
  )
}

function pick(px: number, py: number) {
  if (!camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(((px - rect.left) / rect.width) * 2 - 1, -((py - rect.top) / rect.height) * 2 + 1)
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(ndc, camera)
  const meshes = clusters.value.map((c) => c.proxy)
  const hits = raycaster.intersectObjects(meshes)
  if (hits.length) {
    const idx = (hits[0].object as THREE.Mesh).userData.index as number
    const cluster = clusters.value[idx]
    selectCluster(cluster)
  } else if (selected.value) {
    clearSelect()
  }
}

function selectCluster(cluster: Cluster) {
  selected.value = cluster.row
  const target = cluster.pos.length() * 0.55 + 80
  sphTarget.theta = Math.atan2(cluster.pos.x, cluster.pos.z)
  sphTarget.phi = 1.05
  sphTarget.radius = Math.max(MIN_R, Math.min(MAX_R, target))
  void nextTick(() => {
    panelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  })
}

function clearSelect() {
  selected.value = null
  sphTarget.theta = 0.6
  sphTarget.phi = 1.15
  sphTarget.radius = 340
}

// ---- MediaPipe 手势 ----
function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = src
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('加载手势模型失败'))
    document.head.appendChild(s)
  })
}

async function enableGestures() {
  if (gestureState.value === 'on') {
    camStream?.stop()
    hands?.close()
    gestureState.value = 'idle'
    return
  }
  gestureState.value = 'loading'
  gestureMsg.value = ''
  try {
    await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js')
    await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js')
    const W = window as unknown as {
      Hands: new (cfg: { locateFile: (f: string) => string }) => {
        setOptions: (o: Record<string, unknown>) => void
        onResults: (cb: (r: unknown) => void) => void
        send: (i: { image: unknown }) => Promise<void>
        close: () => void
      }
      Camera: new (
        video: HTMLVideoElement,
        cfg: { onFrame: () => Promise<void>; width: number; height: number },
      ) => { start: () => Promise<void>; stop: () => void }
    }
    const video = videoRef.value
    if (!video) throw new Error('缺少视频元素')
    const Hands = new W.Hands({
      locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}`,
    })
    Hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.6,
      minTrackingConfidence: 0.5,
    })
    Hands.onResults((res: unknown) => {
      const r = res as { multiHandLandmarks?: Array<Array<{ x: number; y: number }>> }
      const lm = r.multiHandLandmarks?.[0]
      if (!lm) return
      const wrist = lm[0]
      const midMcp = lm[9]
      const midTip = lm[12]
      const palm = Math.hypot(midMcp.x - wrist.x, midMcp.y - wrist.y)
      // 握拳检测：食指/中指/无名指/小指 指尖在近端指关节下方
      const curled = [8, 12, 16, 20].filter((tip, i) => lm[tip].y > lm[5 + i * 4].y).length
      // 旋转
      const ang = Math.atan2(midMcp.y - wrist.y, midMcp.x - wrist.x)
      if (smoothedPalm > 0) {
        const delta = palm - smoothedPalm
        if (curled >= 3) {
          sphTarget.radius += Math.sign(-delta) * Math.pow(Math.abs(delta), 1.5) * 2600
        } else if (curled <= 1) {
          sphTarget.radius -= Math.sign(delta) * Math.pow(Math.abs(delta), 1.2) * 2600
        }
        sphTarget.radius = Math.max(MIN_R, Math.min(MAX_R, sphTarget.radius))
        sphTarget.theta += ang * 2.5
      }
      smoothedPalm = palm
    })
    hands = Hands
    const Camera = new W.Camera(video, {
      onFrame: async () => {
        await Hands.send({ image: video })
      },
      width: 320,
      height: 240,
    })
    await Camera.start()
    camStream = Camera
    gestureState.value = 'on'
  } catch (e) {
    gestureState.value = 'error'
    gestureMsg.value = e instanceof Error ? e.message : '手势控制启动失败，可继续使用鼠标。'
  }
}

function onResize() {
  if (!renderer || !camera || !mountRef.value) return
  const w = mountRef.value.clientWidth
  const h = mountRef.value.clientHeight
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

onMounted(async () => {
  await nextTick()
  if (!initThree()) {
    webglOk.value = false
    return
  }
  if (store.dataset) rebuildScene()
  window.addEventListener('resize', onResize)
  raf = requestAnimationFrame(loop)
})

watch(
  () => store.dataset,
  () => {
    if (scene && store.dataset) rebuildScene()
  },
  { deep: false },
)

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', onResize)
  camStream?.stop()
  hands?.close()
  renderer?.dispose()
  scene?.traverse((o) => {
    if (o !== scene) disposeObject(o)
  })
  renderer?.domElement.remove()
  renderer = null
  scene = null
  camera = null
  points = null
})
</script>

<template>
  <div class="galaxy3d-wrap">
    <div class="galaxy3d-head">
      <h3>十类互动星系（3D 粒子）</h3>
      <p class="small muted">
        3610 个地区子项 = 3610 颗粒子，按十类聚成星团。拖拽旋转 · 滚轮缩放 · 点击星团放大查看。
      </p>
      <div class="gesture-row">
        <button type="button" class="btn btn-sm" @click="enableGestures">
          {{ gestureState === 'on' ? '关闭手势' : '开启手势控制' }}
        </button>
        <span v-if="gestureState === 'loading'" class="small muted">正在加载手势模型…</span>
        <span v-else-if="gestureState === 'on'" class="small gesture-on">手势已开启：转手旋转 · 握拳拉远 · 五指张开靠近</span>
        <span v-else-if="gestureState === 'error'" class="small gesture-err">{{ gestureMsg }}</span>
      </div>
    </div>
    <div ref="mountRef" class="galaxy3d-canvas card">
      <CategoryGalaxy v-if="!webglOk" />
      <video
        v-show="gestureState === 'on'"
        ref="videoRef"
        class="gesture-video"
        playsinline
      ></video>
    </div>

    <div v-if="selected" ref="panelRef" class="galaxy3d-panel card">
      <div class="panel-top">
        <h4 :style="{ color: CATEGORY_COLORS[selected.category] }">{{ selected.category }}</h4>
        <button type="button" class="btn btn-sm" @click="clearSelect">返回全貌</button>
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
      <p class="small muted panel-note">
        手势识别使用浏览器本地 MediaPipe 模型（首次需联网加载），摄像头画面仅用于识别，不上传。
      </p>
    </div>
  </div>
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
.gesture-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.gesture-on {
  color: var(--jade);
}
.gesture-err {
  color: #f0a090;
}
.galaxy3d-canvas {
  position: relative;
  overflow: hidden;
  padding: 0;
  height: 460px;
}
.gesture-video {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 160px;
  height: 120px;
  border-radius: 8px;
  border: 1px solid var(--gold-dim);
  opacity: 0.85;
  object-fit: cover;
}
.galaxy3d-panel {
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
.panel-note {
  margin-top: 10px;
}
@media (max-width: 860px) {
  .galaxy3d-canvas {
    height: 340px;
  }
  .panel-stats {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
