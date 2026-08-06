<script setup lang="ts">
import { computed, ref } from 'vue'
import ChinaMap from '@/charts/ChinaMap.vue'
import FilterBar from '@/components/FilterBar.vue'
import ProjectDetailDrawer from '@/components/ProjectDetailDrawer.vue'
import DataDisclaimer from '@/components/DataDisclaimer.vue'
import { useAppStore } from '@/stores/appStore'
import type { ProvinceRow, Subitem } from '@/types'
import { BATCH_LABELS, ENTRY_TYPE_LABELS } from '@/types'

const store = useAppStore()

const mapNameOf = computed(
  () =>
    new Map(store.dataset?.provinces.map((p) => [p.province, p.map_name]) ?? []),
)

const provinceAgg = computed<ProvinceRow[]>(() => {
  const map = new Map<string, ProvinceRow>()
  for (const it of store.filteredSubitems) {
    let row = map.get(it.province)
    if (!row) {
      row = {
        province: it.province,
        map_name: mapNameOf.value.get(it.province) ?? '',
        subitem_count: 0,
        project_count: 0,
        categories_covered: 0,
        new_count: 0,
        extension_count: 0,
      }
      map.set(it.province, row)
    }
    row.subitem_count += 1
    if (it.entry_type === 'new') row.new_count += 1
    if (it.entry_type === 'extension') row.extension_count += 1
  }
  for (const row of map.values()) {
    const items = store.filteredSubitems.filter((i) => i.province === row.province)
    row.project_count = new Set(items.map((i) => i.project_code)).size
    row.categories_covered = new Set(items.map((i) => i.category)).size
  }
  return [...map.values()].sort((a, b) => b.subitem_count - a.subitem_count)
})

const selectedItems = computed<Subitem[]>(() =>
  store.filters.province
    ? store.filteredSubitems.filter((i) => i.province === store.filters.province)
    : [],
)

const selectedRow = computed(() =>
  provinceAgg.value.find((p) => p.province === store.filters.province),
)

const drawer = ref<{ visible: boolean; subitem: Subitem | null }>({
  visible: false,
  subitem: null,
})

function openDetail(it: Subitem) {
  drawer.value = { visible: true, subitem: it }
}

function onSelectProvince(province: string) {
  store.setFilter({ province: store.filters.province === province ? '' : province })
}

function onReset() {
  store.resetFilters()
}

const activeFilterNote = computed(() => {
  const parts: string[] = []
  if (store.filters.category) parts.push(store.filters.category)
  if (store.filters.batch !== null && store.filters.batch !== undefined) {
    parts.push(BATCH_LABELS[store.filters.batch]?.label ?? String(store.filters.batch))
  }
  if (store.filters.entryType) parts.push(ENTRY_TYPE_LABELS[store.filters.entryType])
  if (store.filters.province) parts.push(store.filters.province)
  return parts.join(' · ') || '全部数据'
})
</script>

<template>
  <div class="container">
    <h1 class="page-title">全国分布</h1>
    <p class="page-sub">
      国家级非遗项目与地区子项的省级分布。悬浮查看数据，点击地图或右侧列表选择省份；支持类别、批次与新增/扩展筛选。
    </p>

    <FilterBar
      :model-value="store.filters"
      :categories="store.distinctCategories"
      :batches="store.dataset?.batches ?? []"
      :provinces="store.distinctProvinces"
      @update:model-value="(v) => store.setFilter(v)"
      @reset="onReset"
    />

    <div class="map-layout">
      <div class="card map-card">
        <ChinaMap
          v-if="store.dataset"
          :geo-json="store.dataset.geoJson"
          :province-data="provinceAgg"
          :selected="store.filters.province"
          :loading="store.loading"
          :error="store.error"
          @select="onSelectProvince"
        />
        <div v-else-if="store.loading" class="loading-box">数据加载中…</div>
        <div v-else class="empty-state">数据未加载。</div>
      </div>

      <div class="card side-panel">
        <h3 class="panel-title">
          {{ store.filters.province ? store.filters.province : '省份列表' }}
          <span class="muted small">（当前范围：{{ activeFilterNote }}）</span>
        </h3>

        <div v-if="selectedRow" class="province-stats">
          <div class="stat">
            <b>{{ selectedRow.subitem_count }}</b>
            <span>地区子项</span>
          </div>
          <div class="stat">
            <b>{{ selectedRow.project_count }}</b>
            <span>独立项目</span>
          </div>
          <div class="stat">
            <b>{{ selectedRow.categories_covered }}</b>
            <span>类别覆盖</span>
          </div>
          <div class="stat">
            <b>{{ selectedRow.new_count }}/{{ selectedRow.extension_count }}</b>
            <span>新增/扩展</span>
          </div>
        </div>

        <div v-if="selectedItems.length" class="item-list">
          <button
            v-for="it in selectedItems"
            :key="it.subitem_id"
            type="button"
            class="item-row"
            @click="openDetail(it)"
          >
            <span class="item-code">{{ it.project_code }}</span>
            <span class="item-name">{{ it.project_name }}</span>
            <span class="item-meta small">
              {{ BATCH_LABELS[it.batch_no]?.year ?? it.batch_no }} ·
              {{ ENTRY_TYPE_LABELS[it.entry_type] }}
            </span>
          </button>
        </div>

        <div v-if="!store.filters.province" class="province-list">
          <button
            v-for="p in provinceAgg"
            :key="p.province"
            type="button"
            class="item-row"
            @click="onSelectProvince(p.province)"
          >
            <span class="item-name">{{ p.province }}</span>
            <span class="item-meta small">{{ p.subitem_count }} 子项 · {{ p.project_count }} 项目</span>
          </button>
        </div>
        <div v-if="provinceAgg.length === 0" class="empty-state">当前筛选条件下暂无数据。</div>
      </div>
    </div>

    <div class="map-note">
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
.map-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  margin-top: 16px;
}
@media (max-width: 980px) {
  .map-layout {
    grid-template-columns: 1fr;
  }
}
.map-card {
  overflow: hidden;
}
.side-panel {
  max-height: 640px;
  overflow-y: auto;
}
.panel-title {
  margin: 0 0 12px;
  font-size: 17px;
}
.province-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-0);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 4px;
}
.stat b {
  color: var(--gold);
  font-size: 17px;
}
.stat span {
  font-size: 11px;
  color: var(--ink-2);
}
.item-list,
.province-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.item-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  width: 100%;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 10px;
  color: var(--ink-0);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.item-row:hover {
  background: rgba(217, 184, 119, 0.08);
  border-color: var(--gold-dim);
}
.item-code {
  color: var(--gold);
  font-family: var(--font-serif);
  flex: none;
  font-size: 12px;
}
.item-name {
  flex: 1;
}
.item-meta {
  flex: none;
}
.map-note {
  margin-top: 16px;
}
</style>
