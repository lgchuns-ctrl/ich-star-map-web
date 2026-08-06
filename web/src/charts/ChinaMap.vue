<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ProvinceRow } from '@/types'
import type { MapMetric } from '@/types'
import { MAP_METRIC_LABELS } from '@/types'

const props = defineProps<{
  geoJson: GeoJSON.FeatureCollection
  provinceData: ProvinceRow[]
  selected: string
  loading: boolean
  error: string
  metric: MapMetric
}>()

const emit = defineEmits<{ (e: 'select', province: string): void }>()

const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let observer: ResizeObserver | null = null
let mapRegistered = false

const byName = new Map<string, ProvinceRow>()

function buildOption(): EChartsOption {
  const data = props.provinceData
    .filter((p) => p.map_name)
    .map((p) => ({
      name: p.map_name,
      value:
        props.metric === 'project'
          ? p.project_count
          : props.metric === 'inheritor'
            ? p.inheritor_count
            : props.metric === 'category'
              ? p.categories_covered
              : p.subitem_count,
    }))
  const maxValue = Math.max(1, ...data.map((d) => d.value))
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5', fontSize: 13 },
      formatter: (params: unknown) => {
        const p = params as { name?: string; value?: number | string }
        const name = p.name ?? ''
        const row = byName.get(name)
        if (!row) return `${name}<br/>暂无试点数据`
        return [
          `<b>${row.province}</b>`,
          `${MAP_METRIC_LABELS[props.metric]}：${p.value ?? 0}`,
          `地区子项：${row.subitem_count} · 独立项目：${row.project_count}`,
          `传承人：${row.inheritor_count} · 类别覆盖：${row.categories_covered}`,
        ].join('<br/>')
      },
    },
    visualMap: {
      min: 0,
      max: maxValue,
      calculable: true,
      left: 12,
      bottom: 12,
      text: ['多', '少'],
      textStyle: { color: '#b9ad96' },
      inRange: {
        color: ['#131c2b', '#3a2f1e', '#7a5f30', '#c9a15f', '#e8cf9a'],
      },
    },
    series: [
      {
        name: MAP_METRIC_LABELS[props.metric],
        type: 'map',
        map: 'china',
        roam: true,
        scaleLimit: { min: 0.9, max: 5 },
        selectedMode: false,
        label: {
          show: false,
          color: '#b9ad96',
          fontSize: 9,
        },
        emphasis: {
          label: { show: true, color: '#0b101a' },
          itemStyle: { areaColor: '#e8cf9a' },
        },
        itemStyle: {
          borderColor: 'rgba(217,184,119,0.55)',
          borderWidth: 0.6,
          areaColor: '#131c2b',
        },
        data,
      },
    ],
  }
}

function applySelection(option: EChartsOption) {
  const series = option.series
  if (Array.isArray(series) && series[0] && typeof series[0] === 'object') {
    const s = series[0] as { data?: Array<{ name: string; value: number; itemStyle?: object }> }
    s.data = s.data?.map((d) => ({
      ...d,
      itemStyle: d.name === props.selected ? { areaColor: '#d9b877' } : undefined,
    }))
  }
}

function render() {
  if (!chart) return
  byName.clear()
  for (const p of props.provinceData) if (p.map_name) byName.set(p.map_name, p)
  const option = buildOption()
  applySelection(option)
  chart.setOption(option, { notMerge: true })
}

onMounted(() => {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value)
  if (!mapRegistered) {
    echarts.registerMap('china', props.geoJson as Parameters<typeof echarts.registerMap>[1])
    mapRegistered = true
  }
  chart.on('click', (params: unknown) => {
    const p = params as { name?: string }
    if (!p.name) return
    const row = byName.get(p.name)
    if (row) emit('select', row.province)
  })
  render()
  observer = new ResizeObserver(() => chart?.resize())
  if (chartEl.value.parentElement) observer.observe(chartEl.value.parentElement)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})

watch(() => props.provinceData, render, { deep: false })
watch(() => props.selected, render)
watch(() => props.geoJson, render)
watch(() => props.metric, render)
</script>

<template>
  <div class="map-wrap">
    <div v-if="loading" class="loading-box">地图数据加载中…</div>
    <div v-else-if="error" class="error-box">地图加载失败：{{ error }}</div>
    <div v-else ref="chartEl" class="chart"></div>
  </div>
</template>

<style scoped>
.map-wrap {
  position: relative;
  min-height: 420px;
}
.chart {
  width: 100%;
  height: 520px;
}
@media (max-width: 860px) {
  .chart {
    height: 420px;
  }
  .map-wrap {
    min-height: 320px;
  }
}
</style>
