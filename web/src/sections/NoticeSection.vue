<script setup lang="ts">
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import Reveal from '@/components/Reveal.vue'
import { useAppStore } from '@/stores/appStore'

defineProps<{ id: string }>()

const store = useAppStore()
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">NOTES</p>
          <h2 class="section-title">数据口径与研究限制</h2>
          <p class="section-sub">
            所有指标的口径定义、免责声明、使用范围与数据版本集中说明于此。
          </p>
        </div>
      </Reveal>

      <Reveal>
        <DataDisclaimer />
      </Reveal>

      <Reveal>
        <div class="grid-2">
          <div class="card hoverable">
            <h3>指标说明</h3>
            <ul class="list">
              <li><b>独立项目数</b>：按项目编号去重后的国家级非遗项目数量。</li>
              <li><b>地区子项数</b>：同一项目在不同申报地区形成的记录数。</li>
              <li><b>代表性传承人覆盖率</b> = 已匹配到代表性传承人的子项数 ÷ 地区子项总数（分子与分母均展示）。</li>
              <li><b>每百个子项对应传承人数</b> = 代表性传承人数 ÷ 地区子项数 × 100。</li>
              <li>所有指标基于公开数据构建，缺失不解释为不存在，相关不作因果。</li>
            </ul>
          </div>
          <div class="card hoverable">
            <h3>使用与版权</h3>
            <ul class="list">
              <li>仅使用公开数据，原始响应、清洗脚本与质量报告在仓库中可追溯。</li>
              <li>本项目为高校学生竞赛学术研究作品，不构成官方评价。</li>
              <li>地图底图与素材来源已登记，仅用于数据展示，不作地图出版。</li>
              <li>传承人接口含 2025 年第六批等全部批次（3995 条），与官方截至 2023 年汇总（3059 人）口径不同。</li>
            </ul>
          </div>
        </div>
      </Reveal>

      <Reveal>
        <div class="card">
          <h3>数据版本</h3>
          <p v-if="store.dataset" class="muted">
            {{ store.dataset.metadata.data_version }} · 更新于
            {{ store.dataset.metadata.updated_at }} · 子项
            {{ store.dataset.metadata.cleaned_subitem_count }} / 项目
            {{ store.dataset.metadata.distinct_project_count }} / 传承人
            {{ store.dataset.metadata.inheritor_count }}
          </p>
        </div>
      </Reveal>
    </div>
  </section>
</template>

<style scoped>
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
.card h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.list {
  margin: 0;
  padding-left: 18px;
  color: var(--ink-1);
}
.list li {
  margin-bottom: 8px;
}
</style>
