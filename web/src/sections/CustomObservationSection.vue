<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Reveal from '@/components/Reveal.vue'
import { parseIntent, type IntentQuery, type QueryMetric } from '@/services/intentParser'
import { useAppStore } from '@/stores/appStore'
import { CATEGORY_COLORS, CATEGORY_ORDER } from '@/types'

defineProps<{ id: string }>()

const store = useAppStore()

const input = ref('')
const stage = ref<'idle' | 'parsing' | 'generating' | 'done'>('idle')
const query = ref<IntentQuery | null>(null)
const error = ref('')
const listening = ref(false)
const voiceError = ref('')
const shareMsg = ref('')
const pendingQuery = ref('')

const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let ro: ResizeObserver | null = null

interface SpeechRecognitionInstance {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null
  onend: (() => void) | null
  onerror: ((e: { error: string }) => void) | null
  start: () => void
  stop: () => void
}
interface SpeechRecognitionCtor {
  new (): SpeechRecognitionInstance
}

let recognition: SpeechRecognitionInstance | null = null

const examples = [
  '对比浙江和山东的传统技艺',
  '哪个省份民间文学的子项最多',
  '浙江省都有哪些类别的非遗',
  '传承人最多的省份',
  '传统技艺的分布',
  '传统戏剧五批的变化',
  '民间文学在全国的分布地图',
  '对比浙江和山东的传承人',
]

const metricLabel: Record<QueryMetric, string> = {
  subitem: '地区子项',
  project: '独立项目',
  inheritor: '传承人',
  coverage: '覆盖率',
}

const provRows = computed(() => {
  const d = store.dataset
  return (name: string) => d?.provinces.find((p) => p.province === name)
})

let mapRegistered = false

function countSubitems(region: string | null, category: string | null): number {
  const items = store.dataset?.subitems ?? []
  let n = 0
  for (const s of items) {
    if (region && s.province !== region) continue
    if (category && s.category !== category) continue
    n += 1
  }
  return n
}

function projectCount(region: string | null, category: string | null): number {
  const codes = new Set<string>()
  for (const s of store.dataset?.subitems ?? []) {
    if (region && s.province !== region) continue
    if (category && s.category !== category) continue
    codes.add(s.project_code)
  }
  return codes.size
}

function topProvinces(metric: QueryMetric, category: string | null, limit = 10) {
  const d = store.dataset
  if (!d) return []
  return d.provinces
    .map((p) => {
      let value: number
      if (metric === 'inheritor') value = p.inheritor_count
      else if (metric === 'coverage') value = Math.round((p.inheritor_coverage ?? 0) * 1000)
      else if (metric === 'project') value = projectCount(p.province, category)
      else value = countSubitems(p.province, category)
      return { province: p.province, value }
    })
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}

function categoryShare(region: string): Array<{ category: string; count: number }> {
  const d = store.dataset
  if (!d) return []
  const map = new Map<string, number>()
  for (const s of d.subitems) {
    if (s.province !== region) continue
    map.set(s.category, (map.get(s.category) ?? 0) + 1)
  }
  return CATEGORY_ORDER.filter((c) => map.has(c)).map((c) => ({
    category: c,
    count: map.get(c) ?? 0,
  }))
}

function batchTrendCounts(category: string | null, region: string | null): number[] {
  const counts = [0, 0, 0, 0, 0]
  for (const s of store.dataset?.subitems ?? []) {
    if (category && s.category !== category) continue
    if (region && s.province !== region) continue
    counts[s.batch_no - 1] += 1
  }
  return counts
}

function inheritorRowsFor(regions: string[]) {
  const d = store.dataset
  if (!d) return []
  return regions.map((r) => {
    const row = d.provinces.find((p) => p.province === r)
    return {
      province: r,
      inheritor: row?.inheritor_count ?? 0,
      coverage: row ? (row.inheritor_coverage ?? 0) * 100 : 0,
      per100: row?.inheritors_per_100_subitems ?? 0,
    }
  })
}

function buildOption(q: IntentQuery): EChartsOption {
  const d = store.dataset
  const baseTooltip = {
    backgroundColor: 'rgba(16,24,38,0.92)',
    borderColor: 'rgba(217,184,119,0.4)',
    textStyle: { color: '#f2e8d5', fontSize: 12 },
  }
  if (q.template === 'compare' && q.regions.length >= 2) {
    const [a, b] = q.regions
    const cats = CATEGORY_ORDER.filter((c) => (d?.categories ?? []).some((x) => x.category === c))
    return {
      animation: true,
      animationDuration: 900,
      tooltip: { ...baseTooltip, trigger: 'axis' },
      legend: { textStyle: { color: '#b9ad96' }, top: 0, data: [a, b] },
      grid: { left: 46, right: 20, top: 46, bottom: 30 },
      xAxis: {
        type: 'category',
        data: cats,
        axisLabel: { color: '#8a7f6a', rotate: q.regions.length ? 0 : 0, interval: 0 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#8a7f6a' },
        splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
      },
      series: [
        {
          name: a,
          type: 'bar',
          data: cats.map((c) => countSubitems(a, c)),
          itemStyle: { color: '#d9b877', borderRadius: [4, 4, 0, 0] },
        },
        {
          name: b,
          type: 'bar',
          data: cats.map((c) => countSubitems(b, c)),
          itemStyle: { color: '#5a9e8b', borderRadius: [4, 4, 0, 0] },
        },
      ],
    }
  }
  if (q.template === 'inheritor-compare') {
    const rows = inheritorRowsFor(q.regions)
    const cats = rows.map((r) => r.province)
    if (q.regions.length === 1) cats.push('全国')
    const values = rows.map((r) => r.inheritor)
    if (q.regions.length === 1) values.push(d?.metadata.inheritor_count ?? 0)
    return {
      animation: true,
      animationDuration: 900,
      tooltip: { ...baseTooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 90, right: 50, top: 20, bottom: 30 },
      xAxis: {
        type: 'value',
        axisLabel: { color: '#8a7f6a' },
        splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
      },
      yAxis: {
        type: 'category',
        data: cats,
        axisLabel: { color: '#b9ad96', fontSize: 12 },
      },
      series: [
        {
          name: '代表性传承人（公开）',
          type: 'bar',
          data: values.map((v) => ({
            value: v,
            itemStyle: { color: '#d9b877', borderRadius: [0, 4, 4, 0] },
          })),
          label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11 },
        },
      ],
    }
  }
  if (q.template === 'batch-trend') {
    const labels = d?.batches.map((b) => `第${b.batch_no}批\n${b.publish_year}`) ?? []
    const values = batchTrendCounts(q.category, q.regions[0] ?? null)
    return {
      animation: true,
      animationDuration: 900,
      tooltip: { ...baseTooltip, trigger: 'axis' },
      grid: { left: 46, right: 30, top: 30, bottom: 30 },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: { color: '#8a7f6a' },
      },
      yAxis: {
        type: 'value',
        name: '地区子项',
        nameTextStyle: { color: '#8a7f6a' },
        axisLabel: { color: '#8a7f6a' },
        splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
      },
      series: [
        {
          name: q.category ?? q.regions[0] ?? '全部',
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#d9b877', width: 2 },
          itemStyle: { color: '#d9b877' },
          areaStyle: { color: 'rgba(217,184,119,0.12)' },
          label: { show: true, color: '#b9ad96', fontSize: 11 },
        },
      ],
    }
  }
  if (q.template === 'map') {
    if (!mapRegistered && d) {
      echarts.registerMap('china', d.geoJson as Parameters<typeof echarts.registerMap>[1])
      mapRegistered = true
    }
    const rows = topProvinces(q.metric, q.category, 34)
    const data = rows
      .filter((r) => d?.provinces.find((p) => p.province === r.province)?.map_name)
      .map((r) => ({
        name: d!.provinces.find((p) => p.province === r.province)!.map_name,
        value: q.metric === 'coverage' ? r.value / 10 : r.value,
      }))
    return {
      animation: true,
      animationDuration: 900,
      tooltip: {
        ...baseTooltip,
        formatter: (p: unknown) => {
          const v = (p as { name?: string; value?: number }).value ?? 0
          return `${(p as { name?: string }).name ?? ''}<br/>${metricLabel[q.metric]}：${v}`
        },
      },
      visualMap: {
        min: 0,
        max: Math.max(1, ...data.map((x) => x.value)),
        calculable: true,
        left: 12,
        bottom: 12,
        textStyle: { color: '#b9ad96' },
        inRange: { color: ['#131c2b', '#3a2f1e', '#8a6a35', '#d9b877'] },
      },
      series: [
        {
          name: metricLabel[q.metric],
          type: 'map',
          map: 'china',
          roam: true,
          label: { show: false, color: '#b9ad96' },
          emphasis: { label: { show: true, color: '#0b101a' } },
          itemStyle: { borderColor: 'rgba(217,184,119,0.55)', borderWidth: 0.6 },
          data,
        },
      ],
    }
  }
  if (q.template === 'category-dist') {
    if (q.regions.length === 1 && !q.category) {
      const rows = categoryShare(q.regions[0])
      return {
        animation: true,
        animationDuration: 900,
        tooltip: { ...baseTooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 40, top: 10, bottom: 30 },
        xAxis: {
          type: 'value',
          axisLabel: { color: '#8a7f6a' },
          splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
        },
        yAxis: {
          type: 'category',
          data: rows.map((r) => r.category),
          axisLabel: { color: '#b9ad96', fontSize: 11 },
        },
        series: [
          {
            name: '地区子项',
            type: 'bar',
            data: rows.map((r) => ({
              value: r.count,
              itemStyle: {
                color: CATEGORY_COLORS[r.category] ?? '#d9b877',
                borderRadius: [0, 4, 4, 0],
              },
            })),
            label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11 },
          },
        ],
      }
    }
    const rows = topProvinces('subitem', q.category)
    return {
      animation: true,
      animationDuration: 900,
      tooltip: { ...baseTooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 90, right: 40, top: 10, bottom: 30 },
      xAxis: {
        type: 'value',
        axisLabel: { color: '#8a7f6a' },
        splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
      },
      yAxis: {
        type: 'category',
        data: rows.map((r) => r.province),
        axisLabel: { color: '#b9ad96', fontSize: 12 },
      },
      series: [
        {
          name: q.category ? `${q.category} · 地区子项` : '地区子项',
          type: 'bar',
          data: rows.map((r) => ({
            value: r.value,
            itemStyle: {
              color: q.regions.includes(r.province) ? '#d9b877' : '#5a9e8b',
              borderRadius: [0, 4, 4, 0],
            },
          })),
          label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11 },
        },
      ],
    }
  }
  // top
  const rows = topProvinces(q.metric, q.category)
  const unit =
    q.metric === 'coverage' ? '%' : q.metric === 'inheritor' ? '人' : q.metric === 'project' ? '项' : '个'
  return {
    animation: true,
    animationDuration: 900,
    tooltip: { ...baseTooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 90, right: 50, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#8a7f6a' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.province),
      axisLabel: { color: '#b9ad96', fontSize: 12 },
    },
    series: [
      {
        name: `${metricLabel[q.metric]}${unit}`,
        type: 'bar',
        data: rows.map((r) => ({
          value: q.metric === 'coverage' ? r.value / 10 : r.value,
          itemStyle: { color: '#d9b877', borderRadius: [0, 4, 4, 0] },
        })),
        label: {
          show: true,
          position: 'right',
          color: '#b9ad96',
          fontSize: 11,
          formatter: (p: unknown) => {
            const v = (p as { value: number }).value
            return q.metric === 'coverage' ? `${v.toFixed(1)}%` : String(v)
          },
        },
      },
    ],
  }
}

function renderChart() {
  if (!chart || !query.value) return
  chart.setOption(buildOption(query.value), { notMerge: true })
}

function ensureChart() {
  if (!chartEl.value) return
  if (chart && chart.getDom() !== chartEl.value) {
    chart.dispose()
    chart = null
  }
  if (!chart) {
    chart = echarts.init(chartEl.value)
    ro?.disconnect()
    ro = new ResizeObserver(() => chart?.resize())
    if (chartEl.value.parentElement) ro.observe(chartEl.value.parentElement)
  }
  renderChart()
}

function generate() {
  if (!input.value.trim()) {
    error.value = '请先输入或说出你想看的内容。'
    return
  }
  stage.value = 'parsing'
  error.value = ''
  const q = parseIntent(input.value, store.dataset?.provinces.map((p) => p.province) ?? [])
  if (q.error) {
    error.value = q.error
    query.value = null
    stage.value = 'idle'
    return
  }
  stage.value = 'generating'
  query.value = q
  void nextTick(ensureChart)
  stage.value = 'done'
}

const exportRows = computed(() => {
  const q = query.value
  const d = store.dataset
  if (!q || !d) return []
  if (q.template === 'compare') {
    return q.regions.map((r) => ({
      地区: r,
      类别: q.category ?? '全部',
      子项: countSubitems(r, q.category),
      项目: projectCount(r, q.category),
      传承人: provRows.value(r)?.inheritor_count ?? 0,
      覆盖率: provRows.value(r) ? Math.round(((provRows.value(r)?.inheritor_coverage ?? 0) * 100) * 10) / 10 : 0,
    }))
  }
  if (q.template === 'inheritor-compare') {
    return inheritorRowsFor(q.regions).map((r) => ({
      地区: r.province,
      传承人: r.inheritor,
      覆盖率: Math.round(r.coverage * 10) / 10,
      每百子项传承人: Math.round(r.per100 * 10) / 10,
    }))
  }
  if (q.template === 'batch-trend') {
    const counts = batchTrendCounts(q.category, q.regions[0] ?? null)
    return d.batches.map((b, i) => ({
      批次: `第${b.batch_no}批(${b.publish_year})`,
      子项: counts[i],
    }))
  }
  if (q.template === 'map') {
    return topProvinces(q.metric, q.category, 34).map((r) => ({
      地区: r.province,
      指标: metricLabel[q.metric],
      值: q.metric === 'coverage' ? Math.round((r.value / 10) * 10) / 10 : r.value,
    }))
  }
  return topProvinces(q.metric, q.category).map((r) => ({
    地区: r.province,
    指标: metricLabel[q.metric],
    值: q.metric === 'coverage' ? Math.round((r.value / 10) * 10) / 10 : r.value,
  }))
})

function exportImage() {
  if (!chart) return
  const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#0b101a' })
  const a = document.createElement('a')
  a.href = url
  a.download = `非遗星图-${query.value?.note ?? '自定义观察'}.png`
  a.click()
}

function exportData() {
  if (!query.value) return
  const payload = {
    query: query.value.note,
    updated_at: store.dataset?.metadata.updated_at ?? '',
    disclaimer: '相关指标基于公开国家级名录及国家级代表性传承人数据构建，仅反映公开数据中的资源配置与覆盖情况，不代表官方濒危等级或保护成效评价。',
    rows: exportRows.value,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `非遗星图-${query.value.note.replace(/[·：]/g, '-')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function currentShareUrl() {
  const base = `${location.origin}${location.pathname}`
  const q = input.value.trim()
  return q ? `${base}?q=${encodeURIComponent(q)}#custom` : `${base}#custom`
}

async function share() {
  const url = currentShareUrl()
  const text = `非遗星图 · 自定义观察：${input.value || '看看我的定制图表'}`
  try {
    if (navigator.share) {
      await navigator.share({ title: '非遗星图', text, url })
      return
    }
    await navigator.clipboard.writeText(url)
    shareMsg.value = '链接已复制，可直接发给别人。'
  } catch {
    try {
      await navigator.clipboard.writeText(url)
      shareMsg.value = '链接已复制，可直接发给别人。'
    } catch {
      shareMsg.value = '复制失败，请手动复制地址栏链接。'
    }
  }
}

function exportPoster() {
  if (!chart || !query.value) return
  const chartUrl = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#101826' })
  const img = new Image()
  img.onload = () => {
    const W = 1080
    const H = 1440
    const canvas = document.createElement('canvas')
    canvas.width = W
    canvas.height = H
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const grad = ctx.createLinearGradient(0, 0, 0, H)
    grad.addColorStop(0, '#101826')
    grad.addColorStop(1, '#0b101a')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, W, H)
    ctx.strokeStyle = 'rgba(217,184,119,0.6)'
    ctx.lineWidth = 3
    ctx.strokeRect(24, 24, W - 48, H - 48)
    ctx.textAlign = 'center'
    ctx.fillStyle = '#d9b877'
    ctx.font = 'bold 44px "Noto Serif SC","Songti SC","SimSun",serif'
    ctx.fillText('非遗星图 · 自定义观察', W / 2, 110)
    ctx.fillStyle = '#f2e8d5'
    ctx.font = '26px "PingFang SC","Microsoft YaHei",sans-serif'
    ctx.fillText(query.value!.note, W / 2, 170)
    const chartW = W - 160
    const chartH = (img.height / img.width) * chartW
    ctx.drawImage(img, 80, 210, chartW, Math.min(chartH, 760))
    const y0 = 210 + Math.min(chartH, 760) + 60
    ctx.textAlign = 'left'
    ctx.fillStyle = '#b9ad96'
    ctx.font = '22px "PingFang SC","Microsoft YaHei",sans-serif'
    const meta = store.dataset?.metadata
    const lines = [
      `数据版本 ${meta?.data_version ?? ''} · 更新于 ${meta?.updated_at ?? ''}`,
      '数据来源：中国非物质文化遗产网（ihchina.cn）公开接口',
      '相关指标基于公开国家级名录及国家级代表性传承人数据构建，仅反映公开数据中的资源配置',
      '与覆盖情况，不代表官方濒危等级或保护成效评价。',
    ]
    lines.forEach((line, i) => ctx.fillText(line, 80, y0 + i * 40))
    ctx.textAlign = 'right'
    ctx.fillStyle = '#8a7f6a'
    ctx.font = '20px "PingFang SC","Microsoft YaHei",sans-serif'
    ctx.fillText('非遗星图 · 国家级非物质文化遗产项目传承观察', W - 80, H - 60)
    canvas.toBlob((blob) => {
      if (!blob) return
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `非遗星图-海报-${query.value!.note.replace(/[·：]/g, '-')}.png`
      a.click()
      URL.revokeObjectURL(a.href)
    }, 'image/png')
  }
  img.src = chartUrl
}

function useExample(text: string) {
  input.value = text
  generate()
}

function toggleVoice() {
  const SR = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  const Ctor = SR.SpeechRecognition ?? SR.webkitSpeechRecognition
  if (!Ctor) {
    voiceError.value = '当前浏览器不支持语音识别，请直接输入文字。'
    return
  }
  if (listening.value) {
    recognition?.stop()
    listening.value = false
    return
  }
  const rec = new Ctor()
  recognition = rec
  rec.lang = 'zh-CN'
  rec.continuous = false
  rec.interimResults = true
  rec.onresult = (e) => {
    let text = ''
    for (let i = 0; i < e.results.length; i += 1) {
      text += e.results[i][0].transcript
    }
    input.value = text
  }
  rec.onend = () => {
    listening.value = false
  }
  rec.onerror = (e) => {
    listening.value = false
    voiceError.value =
      e.error === 'not-allowed' || e.error === 'service-not-allowed'
        ? '未获得麦克风权限，可改用文字输入。'
        : `语音识别失败（${e.error}），可改用文字输入。`
  }
  voiceError.value = ''
  rec.start()
  listening.value = true
}

function clearResult() {
  query.value = null
  stage.value = 'idle'
  error.value = ''
}

const compareRows = computed(() => {
  if (!query.value || query.value.template !== 'compare') return []
  return query.value.regions.map((r) => {
    const row = provRows.value(r)
    return {
      province: r,
      subitem: countSubitems(r, query.value!.category),
      project: projectCount(r, query.value!.category),
      inheritor: row?.inheritor_count ?? 0,
      coverage: row ? (row.inheritor_coverage ?? 0) * 100 : 0,
    }
  })
})

const inheritorRows = computed(() => {
  if (!query.value || query.value.template !== 'inheritor-compare') return []
  return inheritorRowsFor(query.value.regions)
})

onBeforeUnmount(() => {
  ro?.disconnect()
  chart?.dispose()
  chart = null
})

onMounted(() => {
  const q = new URLSearchParams(location.search).get('q')
  if (q) {
    input.value = q
    pendingQuery.value = q
  }
})

watch(
  () => store.dataset,
  () => {
    if (pendingQuery.value && store.dataset) {
      const q = pendingQuery.value
      pendingQuery.value = ''
      input.value = q
      generate()
      return
    }
    if (query.value) void nextTick(ensureChart)
  },
  { deep: false },
)
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">CUSTOM</p>
          <h2 class="section-title">自定义观察</h2>
          <p class="section-sub">
            说出或输入你想看的内容，系统自动理解意图并用真实数据生成定制图表。语音识别不可用时可直接输入文字。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <div class="card input-card">
          <div class="input-row">
            <button
              type="button"
              class="mic-btn"
              :class="{ active: listening }"
              :title="listening ? '停止录音' : '语音输入'"
              @click="toggleVoice"
            >
              {{ listening ? '◼' : '🎤' }}
            </button>
            <input
              v-model="input"
              class="input query-input"
              type="text"
              placeholder="例如：对比浙江和山东的传统技艺"
              @keyup.enter="generate"
            />
            <button type="button" class="btn btn-primary" @click="generate">生成图表</button>
          </div>
          <p v-if="voiceError" class="voice-hint">{{ voiceError }}</p>
          <p v-else class="voice-hint small muted">
            {{ listening ? '正在聆听，请说出你的问题…' : '点击 🎤 用语音提问（Chrome/Edge 支持），或直接输入文字。' }}
          </p>
          <div class="chip-row">
            <span class="small muted">试试：</span>
            <button v-for="ex in examples" :key="ex" type="button" class="chip" @click="useExample(ex)">
              {{ ex }}
            </button>
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div v-if="stage === 'parsing'" class="card loading-box">正在理解意图…</div>
        <div v-else-if="stage === 'generating'" class="card loading-box">正在计算并生成图表…</div>
        <div v-else-if="error" class="card">
          <div class="error-box">{{ error }}</div>
          <p class="small muted">可以试试下面的说法：</p>
          <div class="chip-row">
            <button
              v-for="s in ['对比浙江和山东的传统技艺', '哪个省份民间文学的子项最多', '浙江省都有哪些类别的非遗']"
              :key="s"
              type="button"
              class="chip"
              @click="useExample(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>
        <div v-else-if="query" class="card result-card">
          <div class="result-head">
            <div>
              <h3>{{ input }}</h3>
              <p class="small muted">解析结果：{{ query.note }}</p>
            </div>
            <div class="result-actions">
              <button type="button" class="btn btn-sm" @click="exportImage">导出图片</button>
              <button type="button" class="btn btn-sm" @click="exportData">导出数据</button>
              <button type="button" class="btn btn-sm" @click="exportPoster">导出海报</button>
              <button type="button" class="btn btn-sm" @click="share">分享</button>
              <button type="button" class="btn btn-sm" @click="clearResult">清除</button>
            </div>
          </div>
          <p v-if="shareMsg" class="share-msg">{{ shareMsg }}</p>

          <div v-if="query.template === 'compare' && compareRows.length" class="compare-cards">
            <div v-for="row in compareRows" :key="row.province" class="compare-card">
              <h4>{{ row.province }}</h4>
              <div class="c-grid">
                <div class="c-stat"><b>{{ row.subitem }}</b><span>子项</span></div>
                <div class="c-stat"><b>{{ row.project }}</b><span>项目</span></div>
                <div class="c-stat"><b>{{ row.inheritor }}</b><span>传承人</span></div>
                <div class="c-stat"><b>{{ row.coverage.toFixed(1) }}%</b><span>覆盖率</span></div>
              </div>
            </div>
          </div>

          <div v-if="query.template === 'inheritor-compare' && inheritorRows.length" class="compare-cards">
            <div v-for="row in inheritorRows" :key="row.province" class="compare-card">
              <h4>{{ row.province }}</h4>
              <div class="c-grid">
                <div class="c-stat"><b>{{ row.inheritor }}</b><span>传承人</span></div>
                <div class="c-stat"><b>{{ row.coverage.toFixed(1) }}%</b><span>覆盖率</span></div>
                <div class="c-stat"><b>{{ row.per100.toFixed(1) }}</b><span>每百子项</span></div>
              </div>
            </div>
          </div>

          <div ref="chartEl" class="result-chart"></div>

          <p class="small muted result-note">
            数据来源：中国非物质文化遗产网公开接口 · 数据版本
            {{ store.dataset?.metadata.data_version }} · 仅反映公开数据配置情况，不代表官方濒危等级或保护成效评价。
            <button type="button" class="link-btn" @click="share">复制分享链接</button>
          </p>
        </div>
        <div v-else class="card empty-state">输入或说出你的问题，点击“生成图表”开始。</div>
      </Reveal>
    </div>
  </section>
</template>

<style scoped>
.input-card {
  padding: 18px;
}
.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.mic-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid var(--gold-dim);
  background: transparent;
  color: var(--gold);
  font-size: 18px;
  cursor: pointer;
  flex: none;
  transition: all 0.2s ease;
}
.mic-btn:hover {
  background: var(--gold-dim);
}
.mic-btn.active {
  background: var(--cinnabar);
  color: #fff;
  border-color: transparent;
  animation: pulse 1.2s infinite;
}
@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(194, 69, 46, 0.5);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(194, 69, 46, 0);
  }
}
.query-input {
  flex: 1;
  font-size: 15px;
}
.voice-hint {
  margin: 10px 0 4px;
  color: var(--gold);
  font-size: 13px;
}
.result-card {
  margin-top: 16px;
}
.result-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.result-head h3 {
  margin: 0 0 4px;
  font-size: 17px;
}
.result-actions {
  display: flex;
  gap: 8px;
  flex: none;
}
.share-msg {
  color: var(--gold);
  font-size: 13px;
  margin: 8px 0 0;
}
.link-btn {
  background: none;
  border: none;
  color: var(--gold);
  text-decoration: underline;
  cursor: pointer;
  padding: 0 0 0 8px;
  font-size: 12px;
}
@media (max-width: 640px) {
  .result-actions {
    flex-direction: column;
  }
}
.compare-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 14px 0;
}
.compare-card {
  background: var(--bg-0);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
}
.compare-card h4 {
  margin: 0 0 8px;
  color: var(--gold);
  font-size: 15px;
}
.c-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}
.c-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.c-stat b {
  color: var(--ink-0);
  font-size: 15px;
}
.c-stat span {
  font-size: 11px;
  color: var(--ink-2);
}
.result-chart {
  width: 100%;
  height: 400px;
}
.result-note {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
}
@media (max-width: 720px) {
  .compare-cards {
    grid-template-columns: 1fr;
  }
  .result-chart {
    height: 320px;
  }
}
</style>
