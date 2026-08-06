<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let raf = 0

interface Star {
  x: number
  y: number
  r: number
  base: number
  phase: number
  speed: number
}

onMounted(() => {
  const canvasEl = canvasRef.value
  if (!canvasEl) return
  const canvas: HTMLCanvasElement = canvasEl
  const rawCtx = canvas.getContext('2d')
  if (!rawCtx) return
  const ctx: CanvasRenderingContext2D = rawCtx

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const stars: Star[] = []
  let width = 0
  let height = 0

  function resize() {
    const rect = canvas.parentElement?.getBoundingClientRect()
    width = rect?.width ?? canvas.clientWidth
    height = rect?.height ?? canvas.clientHeight
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  function init() {
    stars.length = 0
    const count = Math.min(220, Math.floor((width * height) / 5000))
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.2 + 0.3,
        base: 0.25 + Math.random() * 0.45,
        phase: Math.random() * Math.PI * 2,
        speed: 0.003 + Math.random() * 0.01,
      })
    }
  }

  function draw(t: number) {
    ctx.clearRect(0, 0, width, height)
    for (const s of stars) {
      const alpha = reduced ? s.base : s.base * (0.55 + 0.45 * Math.sin(t * s.speed + s.phase))
      ctx.beginPath()
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(217, 184, 119, ${alpha})`
      ctx.fill()
    }
  }

  function loop(t: number) {
    draw(t)
    raf = requestAnimationFrame(loop)
  }

  resize()
  init()
  raf = requestAnimationFrame(loop)
  window.addEventListener('resize', resize)

  onBeforeUnmount(() => {
    cancelAnimationFrame(raf)
    window.removeEventListener('resize', resize)
  })
})
</script>

<template>
  <canvas ref="canvasRef" class="starfield" aria-hidden="true"></canvas>
</template>

<style scoped>
.starfield {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
</style>
