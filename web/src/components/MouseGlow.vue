<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const glow = ref<HTMLDivElement | null>(null)

function onMove(e: MouseEvent) {
  if (!glow.value) return
  glow.value.style.setProperty('--mx', `${e.clientX}px`)
  glow.value.style.setProperty('--my', `${e.clientY}px`)
}

onMounted(() => window.addEventListener('mousemove', onMove, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('mousemove', onMove))
</script>

<template>
  <div ref="glow" class="mouse-glow" aria-hidden="true"></div>
</template>

<style scoped>
.mouse-glow {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 60;
  background: radial-gradient(
    420px circle at var(--mx, 50vw) var(--my, 30vh),
    rgba(217, 184, 119, 0.07),
    transparent 70%
  );
}
@media (pointer: coarse) {
  .mouse-glow {
    display: none;
  }
}
</style>
