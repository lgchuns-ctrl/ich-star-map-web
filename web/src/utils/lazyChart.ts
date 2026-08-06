import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, shallowRef, type Ref } from 'vue'

export function useLazyChart(
  el: Ref<HTMLDivElement | null>,
  build: () => echarts.EChartsOption,
) {
  const chart = shallowRef<echarts.ECharts | null>(null)
  let io: IntersectionObserver | null = null
  let ro: ResizeObserver | null = null

  function render() {
    if (chart.value) chart.value.setOption(build(), { notMerge: true })
  }

  function init() {
    if (!chart.value && el.value) {
      chart.value = echarts.init(el.value)
      ro = new ResizeObserver(() => chart.value?.resize())
      if (el.value.parentElement) ro.observe(el.value.parentElement)
      render()
      io?.disconnect()
    }
  }

  onMounted(() => {
    io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) init()
      },
      { rootMargin: '240px 0px' },
    )
    if (el.value) io.observe(el.value)
  })

  onBeforeUnmount(() => {
    io?.disconnect()
    ro?.disconnect()
    chart.value?.dispose()
    chart.value = null
  })

  return { chart, render }
}
