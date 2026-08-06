<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { computed, ref, watch } from 'vue'
import Reveal from '@/components/Reveal.vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import { useAppStore } from '@/stores/appStore'
import { CATEGORY_COLORS, CATEGORY_ORDER } from '@/types'
import { useLazyChart } from '@/utils/lazyChart'

defineProps<{ id: string }>()

const store = useAppStore()
const barEl = ref<HTMLDivElement | null>(null)
const catEl = ref<HTMLDivElement | null>(null)
const heatEl = ref<HTMLDivElement | null>(null)

const batchLabels = computed(() =>
  store.dataset
    ? store.dataset.batches.map((b) => `第${b.batch_no}批\n${b.publish_year}`)
    : [],
)

const batchBar = useLazyChart(barEl, () => {
  const batches = store.dataset?.batches ?? []
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
    },
    legend: {
      textStyle: { color: '#b9ad96' },
      top: 0,
    },
    grid: { left: 46, right: 60, top: 46, bottom: 30 },
    xAxis: {
      type: 'category',
      data: batchLabels.value,
      axisLabel: { color: '#8a7f6a' },
    },
    yAxis: [
      {
        type: 'value',
        name: '子项数',
        nameTextStyle: { color: '#8a7f6a' },
        axisLabel: { color: '#8a7f6a' },
        splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
      },
      {
        type: 'value',
        name: '累计',
        nameTextStyle: { color: '#8a7f6a' },
        axisLabel: { color: '#8a7f6a' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '新增项目',
        type: 'bar',
        stack: 'total',
        data: batches.map((b) => b.new_count),
        itemStyle: { color: '#d9b877' },
        emphasis: { focus: 'series' },
      },
      {
        name: '扩展项目',
        type: 'bar',
        stack: 'total',
        data: batches.map((b) => b.extension_count),
        itemStyle: { color: '#5a9e8b' },
        emphasis: { focus: 'series' },
      },
      {
        name: '累计子项',
        type: 'line',
        yAxisIndex: 1,
        data: batches.map((b) => b.cumulative),
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { color: '#f2e8d5', width: 2 },
        itemStyle: { color: '#f2e8d5' },
      },
    ],
  }
})

const catBatch = useLazyChart(catEl, () => {
  const d = store.dataset
  if (!d) return {} as echarts.EChartsOption
  const cats = CATEGORY_ORDER.filter((c) => d.categories.some((x) => x.category === c))
  const series = cats.map((c) => ({
    name: c,
    type: 'bar' as const,
    stack: 'total',
    emphasis: { focus: 'series' as const },
    itemStyle: { color: CATEGORY_COLORS[c] ?? '#d9b877' },
    data: d.batches.map((b) => {
      const key = `${b.batch_no}|${c}`
      return batchCatCount.value.get(key) ?? 0
    }),
  }))
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
    },
    legend: {
      type: 'scroll',
      textStyle: { color: '#b9ad96' },
      top: 0,
    },
    grid: { left: 46, right: 20, top: 46, bottom: 30 },
    xAxis: {
      type: 'category',
      data: batchLabels.value,
      axisLabel: { color: '#8a7f6a' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8a7f6a' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    series,
  }
})

const batchCatCount = computed(() => {
  const m = new Map<string, number>()
  for (const s of store.dataset?.subitems ?? []) {
    const key = `${s.batch_no}|${s.category}`
    m.set(key, (m.get(key) ?? 0) + 1)
  }
  return m
})

const provBatch = useLazyChart(heatEl, () => {
  const d = store.dataset
  if (!d) return {} as echarts.EChartsOption
  const counts = new Map<string, number[]>()
  for (const s of d.subitems) {
    const arr = counts.get(s.province) ?? [0, 0, 0, 0, 0]
    arr[s.batch_no - 1] += 1
    counts.set(s.province, arr)
  }
  const totals = [...counts.entries()].map(([p, arr]) => [p, arr.reduce((a, b) => a + b, 0)] as const)
  totals.sort((a, b) => b[1] - a[1])
  const provinces = totals.slice(0, 15).map(([p]) => p)
  const data: Array<[number, number, number]> = []
  provinces.forEach((p, yi) => {
    const arr = counts.get(p)!
    arr.forEach((v, xi) => data.push([xi, yi, v]))
  })
  const max = Math.max(1, ...data.map((x) => x[2]))
  return {
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
      formatter: (params: unknown) => {
        const p = params as { value: [number, number, number] }
        return `${provinces[p.value[1]]} · 第${p.value[0] + 1}批<br/>子项：${p.value[2]}`
      },
    },
    grid: { left: 90, right: 24, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: d.batches.map((b) => `第${b.batch_no}批`),
      splitArea: { show: true },
      axisLabel: { color: '#8a7f6a' },
    },
    yAxis: {
      type: 'category',
      data: provinces,
      axisLabel: { color: '#b9ad96', fontSize: 12 },
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#8a7f6a' },
      inRange: { color: ['#131c2b', '#3a2f1e', '#8a6a35', '#d9b877'] },
    },
    series: [
      {
        name: '子项数',
        type: 'heatmap',
        data,
        label: { show: true, color: '#f2e8d5', fontSize: 10 },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(217,184,119,0.5)' } },
      },
    ],
  }
})

watch(
  () => store.dataset,
  () => {
    batchBar.render()
    catBatch.render()
    provBatch.render()
  },
  { deep: false },
)
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">TIMELINE</p>
          <h2 class="section-title">五批名录演化</h2>
          <p class="section-sub">
            2006-2021 五个批次的新增与扩展结构、类别构成变化，以及省份 × 批次子项热力分布。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <div class="grid-2">
          <div class="card chart-card hoverable">
            <h3>各批次新增与扩展</h3>
            <div ref="barEl" class="chart chart-lg"></div>
          </div>
          <div class="card chart-card hoverable">
            <h3>批次 × 类别构成</h3>
            <div ref="catEl" class="chart chart-lg"></div>
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div class="card chart-card hoverable heat-card">
          <h3>省份 × 批次子项热力图（TOP15）</h3>
          <div ref="heatEl" class="chart chart-lg"></div>
        </div>
      </Reveal>

      <div class="note-block">
        <DataDisclaimer />
      </div>
    </div>
  </section>
</template>

<style scoped>
.grid-2 {
  margin-top: 16px;
}
.chart-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}
.chart {
  width: 100%;
}
.chart-lg {
  height: 380px;
}
.heat-card {
  margin-top: 16px;
}
.note-block {
  margin-top: 18px;
}
@media (max-width: 860px) {
  .chart-lg {
    height: 320px;
  }
}
</style>
