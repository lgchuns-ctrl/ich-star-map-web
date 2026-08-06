<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import FilterBar from '@/components/FilterBar.vue'
import ProjectDetailDrawer from '@/components/ProjectDetailDrawer.vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import { emptyFilter, filterSubitems } from '@/services/dataService'
import { useAppStore } from '@/stores/appStore'
import type { FilterState, Subitem } from '@/types'
import { BATCH_LABELS, ENTRY_TYPE_LABELS } from '@/types'

const store = useAppStore()

const filters = ref<FilterState>(emptyFilter())
const page = ref(1)
const pageSize = 20

const results = computed<Subitem[]>(() =>
  store.dataset ? filterSubitems(store.dataset.subitems, filters.value) : [],
)

const totalPages = computed(() => Math.max(1, Math.ceil(results.value.length / pageSize)))
const paged = computed(() =>
  results.value.slice((page.value - 1) * pageSize, page.value * pageSize),
)

watch(filters, () => {
  page.value = 1
})

const drawer = ref<{ visible: boolean; subitem: Subitem | null }>({
  visible: false,
  subitem: null,
})

function openDetail(it: Subitem) {
  drawer.value = { visible: true, subitem: it }
}

function onReset() {
  filters.value = emptyFilter()
  page.value = 1
}

const provinces = computed<string[]>(() =>
  store.dataset ? store.dataset.provinces.map((p) => p.province) : [],
)
</script>

<template>
  <div class="container">
    <h1 class="page-title">寻找一项非遗</h1>
    <p class="page-sub">
      按项目名称、编号、类别、批次、类型、地区或保护单位检索国家级非遗记录，点击条目查看详情。
    </p>

    <div class="search-row">
      <input
        v-model="filters.keyword"
        class="input search-input"
        type="search"
        placeholder="输入项目名称 / 编号 / 地区 / 保护单位关键词"
        aria-label="搜索关键词"
      />
      <button type="button" class="btn btn-sm" @click="onReset">清空</button>
    </div>

    <FilterBar
      :model-value="filters"
      :categories="store.distinctCategories"
      :batches="store.dataset?.batches ?? []"
      :provinces="provinces"
      @update:model-value="(v) => (filters = v)"
      @reset="onReset"
    />

    <div class="result-summary muted small">
      共 {{ results.length }} 条记录（全量数据集：十大门类 {{ store.dataset?.metadata.cleaned_subitem_count }} 条地区子项）
    </div>

    <div v-if="paged.length" class="card table-card">
      <table class="result-table">
        <thead>
          <tr>
            <th>编号</th>
            <th>名称</th>
            <th>类别</th>
            <th>批次</th>
            <th>类型</th>
            <th>地区</th>
            <th>保护单位</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="it in paged" :key="it.subitem_id" @click="openDetail(it)">
            <td class="mono">{{ it.project_code }}</td>
            <td>{{ it.project_name }}</td>
            <td>{{ it.category }}</td>
            <td>{{ BATCH_LABELS[it.batch_no]?.year ?? it.batch_no }}</td>
            <td>{{ ENTRY_TYPE_LABELS[it.entry_type] }}</td>
            <td>{{ it.province }}</td>
            <td class="small muted">{{ it.protection_unit || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="pagination">
        <button type="button" class="btn btn-sm" :disabled="page <= 1" @click="page--">
          上一页
        </button>
        <span class="small muted">
          第 {{ page }} / {{ totalPages }} 页
        </span>
        <button type="button" class="btn btn-sm" :disabled="page >= totalPages" @click="page++">
          下一页
        </button>
      </div>
    </div>

    <div v-else-if="store.loading" class="loading-box">数据加载中…</div>
    <div v-else class="empty-state">
      未找到符合条件的项目。可尝试清空筛选或更换关键词。
    </div>

    <div class="note-block">
      <DataDisclaimer />
    </div>
  </div>

  <ProjectDetailDrawer
    :subitem="drawer.subitem"
    :visible="drawer.visible"
    @close="drawer.visible = false"
  />
</template>

<style scoped>
.search-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}
.search-input {
  flex: 1;
  font-size: 15px;
}
.result-summary {
  margin: 14px 0 10px;
}
.table-card {
  overflow-x: auto;
  padding: 6px;
}
.result-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.result-table th,
.result-table td {
  text-align: left;
  padding: 9px 10px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.result-table th {
  color: var(--ink-2);
  font-weight: 500;
  font-size: 12px;
}
.result-table tbody tr {
  cursor: pointer;
  transition: background 0.15s ease;
}
.result-table tbody tr:hover {
  background: rgba(217, 184, 119, 0.08);
}
.mono {
  font-family: var(--font-serif);
  color: var(--gold);
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 14px 0 8px;
}
.pagination .btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.note-block {
  margin-top: 16px;
}
</style>
