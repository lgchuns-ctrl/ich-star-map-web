<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, ref, watch } from 'vue'
import Reveal from '@/components/Reveal.vue'
import { useAppStore } from '@/stores/appStore'
import { CATEGORY_COLORS, CATEGORY_ORDER } from '@/types'
import { useLazyChart } from '@/utils/lazyChart'

defineProps<{ id: string }>()

const store = useAppStore()
const radarEl = ref<HTMLDivElement | null>(null)
const batchEl = ref<HTMLDivElement | null>(null)

const provinceOptions = computed(() =>
  [...(store.dataset?.provinces ?? [])].sort((a, b) => b.subitem_count - a.subitem_count),
)

const provA = ref('浙江省')
const provB = ref('山东省')

watch(
  provinceOptions,
  (list) => {
    if (!provA.value && list[0]) provA.value = list[0].province
    if (list[1] && provB.value === provA.value) provB.value = list[1].province
  },
  { immediate: true },
)

function rowOf(province: string) {
  return provinceOptions.value.find((p) => p.province === province)
}

const catShare = computed(() => {
  const map = new Map<string, Map<string, number>>()
  const total = new Map<string, number>()
  for (const s of store.dataset?.subitems ?? []) {
    if (s.province !== provA.value && s.province !== provB.value) continue
    if (!map.has(s.province)) map.set(s.province, new Map())
    map.get(s.province)!.set(s.category, (map.get(s.province)!.get(s.category) ?? 0) + 1)
    total.set(s.province, (total.get(s.province) ?? 0) + 1)
  }
  return { map, total }
})

const batchCounts = computed(() => {
  const a = [0, 0, 0, 0, 0]
  const b = [0, 0, 0, 0, 0]
  for (const s of store.dataset?.subitems ?? []) {
    if (s.province === provA.value) a[s.batch_no - 1] += 1
    if (s.province === provB.value) b[s.batch_no - 1] += 1
  }
  return { a, b }
})

const radarChart = useLazyChart(radarEl, () => {
  const { map, total } = catShare.value
  const a = map.get(provA.value) ?? new Map<string, number>()
  const b = map.get(provB.value) ?? new Map<string, number>()
  const ta = total.get(provA.value) ?? 1
  const tb = total.get(provB.value) ?? 1
  const option: EChartsOption = {
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
    },
    legend: {
      textStyle: { color: '#b9ad96' },
      top: 0,
      data: [provA.value, provB.value],
    },
    radar: {
      indicator: CATEGORY_ORDER.map((c) => ({ name: c, max: 100 })),
      radius: '62%',
      splitArea: { areaStyle: { color: ['rgba(217,184,119,0.03)', 'rgba(217,184,119,0.06)'] } },
      axisName: { color: '#b9ad96', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.15)' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            name: provA.value,
            value: CATEGORY_ORDER.map((c) => Math.round(((a.get(c) ?? 0) / ta) * 1000) / 10),
            itemStyle: { color: '#d9b877' },
            lineStyle: { color: '#d9b877', width: 2 },
            areaStyle: { color: 'rgba(217,184,119,0.12)' },
          },
          {
            name: provB.value,
            value: CATEGORY_ORDER.map((c) => Math.round(((b.get(c) ?? 0) / tb) * 1000) / 10),
            itemStyle: { color: '#5a9e8b' },
            lineStyle: { color: '#5a9e8b', width: 2 },
            areaStyle: { color: 'rgba(90,158,139,0.12)' },
          },
        ],
      },
    ],
  }
  return option
})

const batchChart = useLazyChart(batchEl, () => {
  const labels = store.dataset?.batches.map((b) => `第${b.batch_no}批`) ?? []
  const option: EChartsOption = {
    animation: true,
    animationDuration: 900,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
    },
    legend: {
      textStyle: { color: '#b9ad96' },
      top: 0,
      data: [provA.value, provB.value],
    },
    grid: { left: 46, right: 20, top: 46, bottom: 30 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#8a7f6a' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8a7f6a' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    series: [
      {
        name: provA.value,
        type: 'bar',
        data: batchCounts.value.a,
        itemStyle: { color: '#d9b877', borderRadius: [4, 4, 0, 0] },
      },
      {
        name: provB.value,
        type: 'bar',
        data: batchCounts.value.b,
        itemStyle: { color: '#5a9e8b', borderRadius: [4, 4, 0, 0] },
      },
    ],
  }
  return option
})

watch(
  () => [provA.value, provB.value, store.dataset],
  () => {
    radarChart.render()
    batchChart.render()
  },
  { deep: false },
)

const summary = computed(() => {
  const a = rowOf(provA.value)
  const b = rowOf(provB.value)
  if (!a || !b) return []
  const lines: string[] = []
  lines.push(
    `${a.province}的地区子项 ${a.subitem_count} 个、独立项目 ${a.project_count} 个；` +
      `${b.province}为 ${b.subitem_count} 个、${b.project_count} 个。`,
  )
  const { map, total } = catShare.value
  const share = (prov: string, cat: string) =>
    ((map.get(prov)?.get(cat) ?? 0) / (total.get(prov) ?? 1)) * 100
  let topA: string = CATEGORY_ORDER[0]
  let topB: string = CATEGORY_ORDER[0]
  for (const c of CATEGORY_ORDER) {
    if (share(provA.value, c) > share(provA.value, topA)) topA = c
    if (share(provB.value, c) > share(provB.value, topB)) topB = c
  }
  lines.push(
    `${a.province}类别占比最高的是「${topA}」（${share(provA.value, topA).toFixed(1)}%），` +
      `${b.province}为「${topB}」（${share(provB.value, topB).toFixed(1)}%）。`,
  )
  lines.push(
    `传承人公开记录 ${a.province} ${a.inheritor_count} 人、每百子项 ${a.inheritors_per_100_subitems?.toFixed(1) ?? '—'}、` +
      `覆盖率 ${a.inheritor_coverage ? (a.inheritor_coverage * 100).toFixed(1) : 0}%；` +
      `${b.province} ${b.inheritor_count} 人、每百子项 ${b.inheritors_per_100_subitems?.toFixed(1) ?? '—'}、` +
      `覆盖率 ${b.inheritor_coverage ? (b.inheritor_coverage * 100).toFixed(1) : 0}%。`,
  )
  lines.push('以上差异基于公开名录数据描述，不代表传承状况优劣或保护成效评价。')
  return lines
})
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">COMPARE</p>
          <h2 class="section-title">省份对比实验室</h2>
          <p class="section-sub">
            任选两个省级地区，对比子项、项目、批次结构、类别结构与传承资源公开配置。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <div class="compare-selects">
          <label class="field">
            <span class="field-label">省份 A</span>
            <select v-model="provA" class="select">
              <option v-for="p in provinceOptions" :key="p.province" :value="p.province">
                {{ p.province }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">省份 B</span>
            <select v-model="provB" class="select">
              <option v-for="p in provinceOptions" :key="p.province" :value="p.province">
                {{ p.province }}
              </option>
            </select>
          </label>
        </div>
      </Reveal>

      <Reveal>
        <div class="compare-cards">
          <Reveal :delay="0" v-for="(p, i) in [rowOf(provA), rowOf(provB)]" :key="p?.province ?? i">
            <div v-if="p" class="card compare-card hoverable">
              <h3>{{ p.province }}</h3>
              <div class="compare-grid">
                <div class="c-stat"><b>{{ p.subitem_count }}</b><span>地区子项</span></div>
                <div class="c-stat"><b>{{ p.project_count }}</b><span>独立项目</span></div>
                <div class="c-stat"><b>{{ p.protection_unit_count }}</b><span>保护单位</span></div>
                <div class="c-stat"><b>{{ p.inheritor_count }}</b><span>传承人</span></div>
                <div class="c-stat"><b>{{ p.inheritors_per_100_subitems?.toFixed(1) ?? '—' }}</b><span>每百子项</span></div>
                <div class="c-stat">
                  <b>{{ p.inheritor_coverage ? (p.inheritor_coverage * 100).toFixed(1) : 0 }}%</b>
                  <span>覆盖率</span>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </Reveal>

      <div class="grid-2">
        <Reveal direction="left">
          <div class="card chart-card hoverable">
            <h3>类别结构雷达（占比 %）</h3>
            <div ref="radarEl" class="chart chart-lg"></div>
          </div>
        </Reveal>
        <Reveal direction="right" :delay="140">
          <div class="card chart-card hoverable">
            <h3>批次子项对比</h3>
            <div ref="batchEl" class="chart chart-lg"></div>
          </div>
        </Reveal>
      </div>

      <Reveal>
        <div class="card">
          <h3>数据差异摘要</h3>
          <ul class="summary-list">
            <li v-for="(line, i) in summary" :key="i">{{ line }}</li>
          </ul>
        </div>
      </Reveal>
    </div>
  </section>
</template>

<style scoped>
.compare-selects {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 220px;
}
.field-label {
  font-size: 12px;
  color: var(--ink-2);
}
.compare-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 16px;
}
@media (max-width: 720px) {
  .compare-cards {
    grid-template-columns: 1fr;
  }
}
.compare-card h3 {
  margin: 0 0 12px;
  font-size: 17px;
  color: var(--gold);
}
.compare-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.c-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-0);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 4px;
}
.c-stat b {
  color: var(--ink-0);
  font-size: 17px;
}
.c-stat span {
  font-size: 11px;
  color: var(--ink-2);
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}
@media (max-width: 900px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
.chart-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}
.chart-lg {
  height: 420px;
  width: 100%;
}
.summary-list {
  margin: 0;
  padding-left: 18px;
  color: var(--ink-1);
}
.summary-list li {
  margin-bottom: 8px;
}
</style>
