<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, ref, watch } from 'vue'
import MetricCard from '@/components/MetricCard.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import Reveal from '@/components/Reveal.vue'
import { useAppStore } from '@/stores/appStore'
import { useLazyChart } from '@/utils/lazyChart'

defineProps<{ id: string }>()

const store = useAppStore()
const chartEl = ref<HTMLDivElement | null>(null)

const totalInheritors = computed(() => store.dataset?.metadata.inheritor_count ?? 0)
const totalSubitems = computed(() => store.dataset?.metadata.cleaned_subitem_count ?? 0)
const matchRate = computed(() => store.dataset?.metadata.inheritor_match_rate ?? 0)
const nationalPer100 = computed(() =>
  totalSubitems.value > 0 ? (totalInheritors.value / totalSubitems.value) * 100 : 0,
)
const provincesWithInheritors = computed(
  () => store.dataset?.provinces.filter((p) => p.inheritor_count > 0).length ?? 0,
)

const provinceRows = computed(() =>
  [...(store.dataset?.provinces ?? [])].sort((a, b) => b.inheritor_count - a.inheritor_count),
)
const categoryRows = computed(() =>
  [...(store.dataset?.categories ?? [])].sort((a, b) => b.subitem_count - a.subitem_count),
)

const barChart = useLazyChart(chartEl, () => {
  const top = provinceRows.value.slice(0, 15)
  const option: EChartsOption = {
    grid: { left: 90, right: 40, top: 20, bottom: 30 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(16,24,38,0.92)',
      borderColor: 'rgba(217,184,119,0.4)',
      textStyle: { color: '#f2e8d5', fontSize: 12 },
      formatter: (params: unknown) => {
        const p = params as Array<{ name: string; value: number }>
        const row = provinceRows.value.find((r) => r.province === p[0]?.name)
        if (!row) return ''
        return `${row.province}<br/>传承人：${row.inheritor_count}<br/>每百子项：${row.inheritors_per_100_subitems?.toFixed(1) ?? '—'}<br/>覆盖率：${row.inheritor_coverage ? (row.inheritor_coverage * 100).toFixed(1) : 0}%`
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#8a7f6a' },
      splitLine: { lineStyle: { color: 'rgba(217,184,119,0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: top.map((p) => p.province),
      axisLabel: { color: '#b9ad96', fontSize: 12 },
    },
    series: [
      {
        name: '国家级代表性传承人（公开）',
        type: 'bar',
        data: top.map((p) => p.inheritor_count),
        itemStyle: { color: '#d9b877', borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', color: '#b9ad96', fontSize: 11 },
      },
    ],
  }
  return option
})

watch(
  () => store.dataset,
  () => barChart.render(),
  { deep: false },
)
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">INHERITORS</p>
          <h2 class="section-title">传承资源观察</h2>
          <p class="section-sub">
            基于国家级代表性传承人公开名单，观察各地区与类别的公开配置与覆盖情况。指标仅反映公开数据，不代表官方濒危等级。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <div class="grid-4">
          <MetricCard label="传承人公开记录" :value="totalInheritors" note="含第六批(2025)等全部批次">
            <template #value><AnimatedNumber :value="totalInheritors" /></template>
          </MetricCard>
          <MetricCard
            label="传承人-子项匹配率"
            :value="`${(matchRate * 100).toFixed(2)}%`"
            note="按公开编号+地区关联"
          />
          <MetricCard
            label="全国每百子项传承人数"
            :value="nationalPer100.toFixed(1)"
            note="传承人 ÷ 子项 × 100"
          >
            <template #value><AnimatedNumber :value="nationalPer100" :decimals="1" /></template>
          </MetricCard>
          <MetricCard label="有传承人公开记录的省份" :value="provincesWithInheritors" note="覆盖省级地区">
            <template #value><AnimatedNumber :value="provincesWithInheritors" /></template>
          </MetricCard>
        </div>
      </Reveal>

      <Reveal>
        <div class="section-subhead">
          <h3>传承人公开数量 TOP15（省级）</h3>
        </div>
        <div class="card chart-card hoverable">
          <div ref="chartEl" class="chart chart-lg"></div>
        </div>
      </Reveal>

      <Reveal>
        <div class="grid-2">
          <div class="card table-card">
            <h3>省级传承资源配置</h3>
            <table class="data-table">
              <thead>
                <tr>
                  <th>省份</th>
                  <th>子项</th>
                  <th>传承人</th>
                  <th>每百子项</th>
                  <th>覆盖率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in provinceRows" :key="p.province">
                  <td>{{ p.province }}</td>
                  <td>{{ p.subitem_count }}</td>
                  <td>{{ p.inheritor_count }}</td>
                  <td>{{ p.inheritors_per_100_subitems?.toFixed(1) ?? '—' }}</td>
                  <td>
                    {{ p.matched_subitem_count }}/{{ p.subitem_count }}
                    <span class="small muted">
                      （{{ p.inheritor_coverage ? (p.inheritor_coverage * 100).toFixed(1) : 0 }}%）
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="card table-card">
            <h3>类别传承资源对比</h3>
            <table class="data-table">
              <thead>
                <tr>
                  <th>类别</th>
                  <th>子项</th>
                  <th>传承人</th>
                  <th>覆盖率</th>
                  <th>每百子项</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in categoryRows" :key="c.category">
                  <td>{{ c.category }}</td>
                  <td>{{ c.subitem_count }}</td>
                  <td>{{ c.inheritor_count }}</td>
                  <td>
                    {{ c.matched_subitem_count }}/{{ c.subitem_count }}
                    <span class="small muted">
                      （{{ c.inheritor_coverage ? (c.inheritor_coverage * 100).toFixed(1) : 0 }}%）
                    </span>
                  </td>
                  <td>{{ c.inheritors_per_100_subitems?.toFixed(1) ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div class="card">
          <h3>指标解释</h3>
          <ul class="indicator-list">
            <li><b>代表性传承人覆盖率</b> = 已匹配到代表性传承人的子项数 ÷ 地区子项总数（分子与分母同时展示）。</li>
            <li><b>每百个子项对应传承人数</b> = 国家级代表性传承人数 ÷ 地区子项数量 × 100。</li>
            <li>传承人-子项关联优先按官方 child_num 精确匹配，回退到项目编号+省份；多候选记录（26 条）不计入匹配分子。</li>
            <li>这些指标只描述公开数据中的配置情况，缺失不解释为不存在，不作因果推断。</li>
          </ul>
        </div>
      </Reveal>

      <div class="note-block">
        <DataDisclaimer />
      </div>
    </div>
  </section>
</template>

<style scoped>
.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
@media (max-width: 900px) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}
.section-subhead {
  margin: 22px 0 10px;
}
.section-subhead h3,
.table-card h3,
.card h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.chart {
  width: 100%;
}
.chart-lg {
  height: 440px;
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
.table-card {
  overflow-x: auto;
  padding: 6px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th,
.data-table td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.data-table th {
  color: var(--ink-2);
  font-weight: 500;
  font-size: 12px;
}
.indicator-list {
  margin: 0;
  padding-left: 18px;
}
.indicator-list li {
  margin-bottom: 8px;
  color: var(--ink-1);
}
.note-block {
  margin-top: 18px;
}
</style>
