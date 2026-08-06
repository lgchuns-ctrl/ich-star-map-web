<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    decimals?: number
    duration?: number
  }>(),
  { decimals: 0, duration: 1200 },
)

const el = ref<HTMLSpanElement | null>(null)
const display = ref(0)
let raf = 0

const formatted = computed(() =>
  display.value.toLocaleString('zh-CN', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  }),
)

function animate() {
  const t0 = performance.now()
  const from = 0
  const step = (t: number) => {
    const p = Math.min(1, (t - t0) / props.duration)
    const eased = 1 - Math.pow(1 - p, 3)
    display.value = from + (props.value - from) * eased
    if (p < 1) raf = requestAnimationFrame(step)
    else display.value = props.value
  }
  raf = requestAnimationFrame(step)
}

onMounted(() => {
  const io = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        animate()
        io.disconnect()
      }
    },
    { threshold: 0.4 },
  )
  if (el.value) io.observe(el.value)
  onBeforeUnmount(() => {
    io.disconnect()
    cancelAnimationFrame(raf)
  })
})
</script>

<template>
  <span ref="el">{{ formatted }}</span>
</template>
