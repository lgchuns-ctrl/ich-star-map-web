<script setup lang="ts">
import { computed } from 'vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import { useAppStore } from '@/stores/appStore'

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
  <div class="container">
    <h1 class="page-title">数据与方法</h1>
    <p class="page-sub">本作品的数据来源、处理流程、指标定义与研究限制，全部可追溯。</p>

    <template v-if="store.loading">
      <div class="loading-box">数据加载中…</div>
    </template>

    <template v-else-if="meta">
      <section class="section">
        <h2>数据版本</h2>
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
                <th>原始记录 / 清洗子项 / 独立项目</th>
                <td>
                  {{ meta.raw_record_count }} / {{ meta.cleaned_subitem_count }} /
                  {{ meta.distinct_project_count }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="section">
        <h2>数据来源</h2>
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
      </section>

      <section class="section">
        <h2>处理流程与指标</h2>
        <div class="grid-2">
          <div class="card">
            <h3>采集</h3>
            <p class="muted">{{ method?.collection }}</p>
          </div>
          <div class="card">
            <h3>清洗</h3>
            <p class="muted">{{ method?.cleaning }}</p>
          </div>
          <div class="card">
            <h3>指标定义</h3>
            <ul class="muted indicator-list">
              <li v-for="(v, k) in meta.indicators" :key="k">
                <b>{{ k }}</b>：{{ v }}
              </li>
            </ul>
          </div>
          <div class="card">
            <h3>数据伦理</h3>
            <p class="muted">{{ method?.ethics }}</p>
          </div>
        </div>
      </section>

      <section class="section">
        <h2>研究限制</h2>
        <div class="card">
          <ul class="limitation-list">
            <li v-for="(n, i) in meta.notes" :key="i">{{ n }}</li>
            <li v-for="(n, i) in method?.limitations ?? []" :key="`m-${i}`">{{ n }}</li>
            <li>
              缺失值不做“不存在”解释；未纳入传承人数据（全量阶段补充国家级代表性传承人公开名单）。
            </li>
            <li>
              本项目不发布未经论证的综合“濒危分数”，传承资源相关表述统一为“公开配置/覆盖情况”。
            </li>
          </ul>
        </div>
      </section>

      <section class="section">
        <h2>项目文档</h2>
        <div class="card">
          <ul class="limitation-list">
            <li v-for="d in docs" :key="d">{{ d }}</li>
          </ul>
          <p class="small muted">
            完整代码、原始数据与文档位于项目仓库，构建产物可部署到 GitHub Pages。
          </p>
        </div>
      </section>

      <section class="section">
        <DataDisclaimer />
      </section>
    </template>

    <div v-else-if="store.error" class="error-box">{{ store.error }}</div>
  </div>
</template>

<style scoped>
.section {
  margin-bottom: 28px;
}
.section h2 {
  font-size: 19px;
  margin: 0 0 12px;
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
