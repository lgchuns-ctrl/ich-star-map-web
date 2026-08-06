import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, shallowRef, type Ref } from 'vue'

type Option = echarts.EChartsOption

/** 保留函数的深拷贝：structuredClone 无法处理函数（tooltip formatter 等）。 */
function cloneKeepFns<T>(value: T): T {
  if (typeof value === 'function') return value
  if (Array.isArray(value)) {
    return value.map((v) => cloneKeepFns(v)) as unknown as T
  }
  if (value !== null && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const key of Object.keys(value as Record<string, unknown>)) {
      out[key] = cloneKeepFns((value as Record<string, unknown>)[key])
    }
    return out as T
  }
  return value
}

/** 将系列数据归零：数字 -> 0；{value} -> 0；heatmap 三元组 [x,y,v] -> [x,y,0]。 */
export function zeroSeriesData(option: Option): Option {
  const out = cloneKeepFns(option)
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
      try {
        const real = build()
        const zeroed = zeroSeriesData(real)
        chart.value.setOption({ ...zeroed, animation: false }, { notMerge: true })
        requestAnimationFrame(() => {
          if (!chart.value) return
          try {
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
          } catch (err) {
            // 两阶段异常时兜底：直接渲染真实数据，避免空白图表
            console.error('[lazyChart] animate render failed, fallback:', err)
            chart.value.setOption(real, { notMerge: true })
          }
        })
      } catch (err) {
        console.error('[lazyChart] zero render failed, fallback:', err)
        render()
      }
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
