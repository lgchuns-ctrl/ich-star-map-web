<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    delay?: number
    direction?: 'up' | 'left' | 'right'
  }>(),
  { delay: 0, direction: 'up' },
)

const el = ref<HTMLDivElement | null>(null)
const visible = ref(false)
let observer: IntersectionObserver | null = null

const style = computed(() => ({
  transitionDelay: `${props.delay}ms`,
}))

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
  <div
    ref="el"
    class="reveal"
    :class="[`reveal-${props.direction}`, { revealed: visible }]"
    :style="style"
  >
    <slot />
  </div>
</template>

<style scoped>
.reveal {
  opacity: 0;
  transition:
    opacity 0.7s ease,
    transform 0.7s ease;
  will-change: opacity, transform;
}
.reveal-up {
  transform: translateY(30px);
}
.reveal-left {
  transform: translateX(-40px);
}
.reveal-right {
  transform: translateX(40px);
}
.revealed {
  opacity: 1;
  transform: none;
}
</style>
