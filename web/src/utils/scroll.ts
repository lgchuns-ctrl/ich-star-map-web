import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

export function useScrollSpy(ids: string[]) {
  const activeId = ref('')
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) activeId.value = entry.target.id
        }
      },
      { rootMargin: '-25% 0px -65% 0px' },
    )
    for (const id of ids) {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    }
  })
  onBeforeUnmount(() => observer?.disconnect())
  return { activeId }
}

export function useInViewOnce(el: Ref<HTMLElement | null>) {
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
      { rootMargin: '80px 0px' },
    )
    if (el.value) observer.observe(el.value)
  })
  onBeforeUnmount(() => observer?.disconnect())
  return { visible }
}
