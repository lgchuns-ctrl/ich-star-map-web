import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, shallowRef, type Ref } from 'vue'

type Option = echarts.EChartsOption

/** 将系列数据归零：数字 -> 0；{value} -> 0；heatmap 三元组 [x,y,v] -> [x,y,0]。 */
export function zeroSeriesData(option: Option): Option {
  const out = structuredClone(option) as Option
  const series = (out.series ?? []) as Array<Record<string, unknown>>
  for (const s of series) {
    const data = s.data
    if (!Array.isArray(data)) continue
    s.data = data.map((d: unknown) => {
      if (typeof d === 'number') return 0
      if (Array.isArray(d)) {
        return d.length >= 3 ? [d[0], d[1], 0] : d.map(() => 0)
      }
      if (d && typeof d === 'object') {
        const obj = d as Record<string, unknown>
        if ('value' in obj) {
          return {
            ...obj,
            value: Array.isArray(obj.value) ? (obj.value as unknown[]).map(() => 0) : 0,
          }
        }
      }
      return d
    })
  }
  return out
}

export function useLazyChart(
  el: Ref<HTMLDivElement | null>,
  build: () => Option,
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
      // 两阶段渲染：先以 0 值（关闭动画）渲染，下一帧再渲染真实数据，
      // 强制触发“柱子从 0 长出来”的更新动画，不依赖首次渲染动画。
      const real = build()
      const zeroed = zeroSeriesData(real)
      chart.value.setOption({ ...zeroed, animation: false }, { notMerge: true })
      requestAnimationFrame(() => {
        if (!chart.value) return
        chart.value.setOption(
          {
            ...real,
            animation: true,
            animationDuration: 1100,
            animationEasing: 'cubicOut',
            animationDurationUpdate: 900,
            animationEasingUpdate: 'cubicOut',
          },
          { notMerge: true },
        )
      })
      io?.disconnect()
    }
  }

  onMounted(() => {
    io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) init()
      },
      { rootMargin: '0px 0px -40px 0px' },
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
