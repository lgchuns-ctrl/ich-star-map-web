<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const el = ref<HTMLDivElement | null>(null)
const visible = ref(false)
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        visible.value = true
        observer?.disconnect()
      }
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' },
  )
  if (el.value) observer.observe(el.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div ref="el" class="reveal" :class="{ revealed: visible }">
    <slot />
  </div>
</template>

<style scoped>
.reveal {
  opacity: 0;
  transform: translateY(26px);
  transition:
    opacity 0.7s ease,
    transform 0.7s ease;
}
.revealed {
  opacity: 1;
  transform: none;
}
</style>
