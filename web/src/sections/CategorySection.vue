<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { computed, ref, watch } from 'vue'
import Reveal from '@/components/Reveal.vue'
import CategoryGalaxy from '@/components/CategoryGalaxy.vue'
import { useAppStore } from '@/stores/appStore'
import { CATEGORY_COLORS, CATEGORY_ORDER } from '@/types'
import { useLazyChart } from '@/utils/lazyChart'

defineProps<{ id: string }>()

const store = useAppStore()
const barEl = ref<HTMLDivElement | null>(null)
const covEl = ref<HTMLDivElement | null>(null)

const catRows = computed(() => {
  const d = store.dataset
  if (!d) return []
  const byName = new Map(d.categories.map((c) => [c.category, c]))
  return CATEGORY_ORDER.map((name) => byName.get(name)).filter(
    (c): c is NonNullable<typeof c> => Boolean(c),
  )
})

const maxSubitems = computed(() =>
  Math.max(1, ...catRows.value.map((c) => c.subitem_count)),
)

const distChart = useLazyChart(barEl, () => {
  const rows = catRows.value
  const option: EChartsOption = {
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
      formatter: (params: unknown) => {
        const p = params as Array<{ name: string; value: number }>
        const row = rows.find((r) => r.category === p[0]?.name)
        return `${p[0]?.name}<br/>子项：${p[0]?.value} · 项目：${row?.project_count ?? 0} · 传承人：${row?.inheritor_count ?? 0}`
      },
    },
    grid: { left: 140, right: 40, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#8a7f6a' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.category),
      axisLabel: { color: '#b9ad96', fontSize: 12 },
    },
    series: [
      {
        name: '地区子项',
        type: 'bar',
        data: rows.map((r) => ({
          value: r.subitem_count,
          itemStyle: { color: CATEGORY_COLORS[r.category] ?? '#d9b877', borderRadius: [0, 4, 4, 0] },
        })),
        label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11 },
      },
    ],
  }
  return option
})

const covChart = useLazyChart(covEl, () => {
  const rows = catRows.value
  return {
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5' },
      formatter: (params: unknown) => {
        const p = params as Array<{ name: string; value: number }>
        const row = rows.find((r) => r.category === p[0]?.name)
        return `${p[0]?.name}<br/>覆盖率：${(p[0]?.value ?? 0).toFixed(1)}%<br/>匹配子项/子项：${row?.matched_subitem_count ?? 0}/${row?.subitem_count ?? 0}`
      },
    },
    grid: { left: 140, right: 60, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#8a7f6a', formatter: '{value}%' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.category),
      axisLabel: { color: '#b9ad96', fontSize: 12 },
    },
    series: [
      {
        name: '传承人覆盖率',
        type: 'bar',
        data: rows.map((r) => ({
          value: Math.round((r.inheritor_coverage ?? 0) * 1000) / 10,
          itemStyle: { color: '#5a9e8b', borderRadius: [0, 4, 4, 0] },
        })),
        label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11, formatter: '{c}%' },
      },
    ],
  }
})

watch(
  () => store.dataset,
  () => {
    distChart.render()
    covChart.render()
  },
  { deep: false },
)
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">GALAXY</p>
          <h2 class="section-title">十类非遗星系</h2>
          <p class="section-sub">
            十大类别如同十组星系：每个类别展示项目数、地区覆盖、传承人公开配置与代表性构成。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <CategoryGalaxy />
      </Reveal>

      <Reveal>
        <div class="cat-grid">
          <Reveal v-for="(c, i) in catRows" :key="c.category" :delay="i * 55">
            <div
              class="card cat-card hoverable"
              :style="{ '--cat': CATEGORY_COLORS[c.category] }"
            >
              <h3 class="cat-name">{{ c.category }}</h3>
              <div class="cat-stats">
                <span><b>{{ c.subitem_count }}</b> 子项</span>
                <span><b>{{ c.project_count }}</b> 项目</span>
                <span><b>{{ c.inheritor_count }}</b> 传承人</span>
              </div>
              <div class="cat-bar">
                <div
                  class="cat-bar-fill"
                  :style="{
                    width: `${Math.round((c.subitem_count / maxSubitems) * 100)}%`,
                    background: CATEGORY_COLORS[c.category],
                  }"
                ></div>
              </div>
              <div class="cat-foot small muted">
                覆盖 {{ c.province_count }} 省 · {{ c.batch_count }} 批次 ·
                覆盖率 {{ c.inheritor_coverage ? (c.inheritor_coverage * 100).toFixed(1) : 0 }}%
              </div>
            </div>
          </Reveal>
        </div>
      </Reveal>

      <Reveal>
        <div class="grid-2">
          <Reveal direction="left">
            <div class="card chart-card hoverable">
              <h3>类别规模分布</h3>
              <div ref="barEl" class="chart chart-lg"></div>
            </div>
          </Reveal>
          <Reveal direction="right" :delay="140">
            <div class="card chart-card hoverable">
              <h3>传承人覆盖率（按类别）</h3>
              <div ref="covEl" class="chart chart-lg"></div>
            </div>
          </Reveal>
        </div>
      </Reveal>
    </div>
  </section>
</template>

<style scoped>
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 16px;
}
.cat-card {
  border-left: 3px solid var(--cat, var(--gold));
}
.cat-name {
  margin: 0 0 10px;
  font-size: 16px;
}
.cat-stats {
  display: flex;
  gap: 14px;
  font-size: 13px;
  color: var(--ink-1);
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.cat-stats b {
  color: var(--ink-0);
}
.cat-bar {
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.cat-bar-fill {
  height: 100%;
  transition: width 1s ease;
}
.cat-foot {
  margin-top: 8px;
}
.grid-2 {
  margin-top: 16px;
}
.chart-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}
.chart-lg {
  height: 420px;
  width: 100%;
}
@media (max-width: 860px) {
  .chart-lg {
    height: 340px;
  }
}
</style>
