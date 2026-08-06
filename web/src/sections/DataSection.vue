<script setup lang="ts">
import { computed } from 'vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import Reveal from '@/components/Reveal.vue'
import { useAppStore } from '@/stores/appStore'

defineProps<{ id: string }>()

const store = useAppStore()

const meta = computed(() => store.dataset?.metadata)
const method = computed(() => store.dataset?.methodology)

const docs = [
  '项目背景与竞赛调研（docs/项目背景.md）',
  '数据源登记表（docs/数据源登记表.md）',
  '数据字典（docs/数据字典.md）',
  '数据采集说明、数据清洗说明、指标定义（docs/）',
  '数据质量报告（docs/数据质量报告.md）',
  '网页设计说明、部署说明（docs/）',
  '参赛作品说明书、答辩演示脚本（docs/）',
]
</script>

<template>
  <section :id="id" class="site-section">
    <div class="container">
      <Reveal>
        <div class="section-head">
          <p class="section-kicker">METHOD</p>
          <h2 class="section-title">数据与方法</h2>
          <p class="section-sub">本作品的数据来源、处理流程、指标定义与研究限制，全部可追溯。</p>
        </div>
      </Reveal>

      <template v-if="store.loading">
        <div class="loading-box">数据加载中…</div>
      </template>

      <template v-else-if="meta">
        <Reveal>
          <div class="section-subhead">
            <h3>数据版本</h3>
          </div>
          <div class="card">
            <table class="meta-table">
              <tbody>
                <tr>
                  <th>数据版本</th>
                  <td>{{ meta.data_version }}</td>
                </tr>
                <tr>
                  <th>数据更新时间</th>
                  <td>{{ meta.updated_at }}</td>
                </tr>
                <tr>
                  <th>采集范围</th>
                  <td>{{ meta.scope }}</td>
                </tr>
                <tr>
                  <th>子项 / 项目 / 传承人</th>
                  <td>
                    {{ meta.cleaned_subitem_count }} / {{ meta.distinct_project_count }} /
                    {{ meta.inheritor_count }}（匹配率 {{ (meta.inheritor_match_rate * 100).toFixed(2) }}%）
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Reveal>

        <Reveal>
          <div class="section-subhead">
            <h3>数据来源</h3>
          </div>
          <div class="card">
            <table class="meta-table">
              <thead>
                <tr>
                  <th>来源</th>
                  <th>角色</th>
                  <th>访问日期</th>
                  <th>格式</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in meta.sources" :key="s.url">
                  <td>
                    <a :href="s.url" target="_blank" rel="noopener noreferrer">{{ s.name }}</a>
                  </td>
                  <td>{{ s.role }}</td>
                  <td>{{ s.accessed_at }}</td>
                  <td>{{ s.type }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Reveal>

        <Reveal>
          <div class="section-subhead">
            <h3>处理流程与指标</h3>
          </div>
          <div class="grid-2">
            <div class="card hoverable">
              <h4>采集</h4>
              <p class="muted">{{ method?.collection }}</p>
            </div>
            <div class="card hoverable">
              <h4>清洗</h4>
              <p class="muted">{{ method?.cleaning }}</p>
            </div>
            <div class="card hoverable">
              <h4>指标定义</h4>
              <ul class="indicator-list muted">
                <li v-for="(v, k) in meta.indicators" :key="k">
                  <b>{{ k }}</b>：{{ v }}
                </li>
              </ul>
            </div>
            <div class="card hoverable">
              <h4>数据伦理</h4>
              <p class="muted">{{ method?.ethics }}</p>
            </div>
          </div>
        </Reveal>

        <Reveal>
          <div class="section-subhead">
            <h3>研究限制</h3>
          </div>
          <div class="card">
            <ul class="limitation-list">
              <li v-for="(n, i) in meta.notes" :key="i">{{ n }}</li>
              <li v-for="(n, i) in method?.limitations ?? []" :key="`m-${i}`">{{ n }}</li>
              <li>缺失值不做“不存在”解释；统计结果均可追溯到原始记录。</li>
              <li>本项目不发布未经论证的综合“濒危分数”。</li>
            </ul>
          </div>
        </Reveal>

        <Reveal>
          <div class="section-subhead">
            <h3>项目文档</h3>
          </div>
          <div class="card">
            <ul class="limitation-list">
              <li v-for="d in docs" :key="d">{{ d }}</li>
            </ul>
            <p class="small muted">完整代码、原始数据与文档位于项目仓库，构建产物可部署到 GitHub Pages。</p>
          </div>
        </Reveal>

        <Reveal>
          <DataDisclaimer />
        </Reveal>
      </template>

      <div v-else-if="store.error" class="error-box">{{ store.error }}</div>
    </div>
  </section>
</template>

<style scoped>
.section-subhead {
  margin: 20px 0 12px;
}
.section-subhead h3 {
  font-size: 18px;
  margin: 0;
  padding-left: 10px;
  border-left: 3px solid var(--gold);
}
.meta-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.meta-table th,
.meta-table td {
  text-align: left;
  padding: 9px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.meta-table th {
  width: 170px;
  color: var(--ink-2);
  font-weight: 500;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 900px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
.grid-2 h4 {
  margin: 0 0 8px;
  font-size: 15px;
}
.indicator-list,
.limitation-list {
  margin: 0;
  padding-left: 18px;
}
.indicator-list li,
.limitation-list li {
  margin-bottom: 6px;
}
</style>
