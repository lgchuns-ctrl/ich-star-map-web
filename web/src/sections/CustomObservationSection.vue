<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
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

onBeforeUnmount(() => {
  ro?.disconnect()
  chart?.dispose()
  chart = null
})

watch(
  () => store.dataset,
  () => {
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
            <button type="button" class="btn btn-sm" @click="clearResult">清除</button>
          </div>

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

          <div ref="chartEl" class="result-chart"></div>

          <p class="small muted result-note">
            数据来源：中国非物质文化遗产网公开接口 · 数据版本
            {{ store.dataset?.metadata.data_version }} · 仅反映公开数据配置情况，不代表官方濒危等级或保护成效评价。
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
