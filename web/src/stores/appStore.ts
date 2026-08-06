import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { FilterState, Subitem } from '@/types'
import type { Dataset } from '@/services/dataService'
import { emptyFilter, filterSubitems, loadDataset } from '@/services/dataService'

export const useAppStore = defineStore('app', () => {
  const dataset = ref<Dataset | null>(null)
  const loading = ref(false)
  const error = ref('')
  const filters = ref<FilterState>(emptyFilter())

  async function load() {
    if (dataset.value) return
    loading.value = true
    error.value = ''
    try {
      dataset.value = await loadDataset()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  function resetFilters() {
    filters.value = emptyFilter()
  }

  function setFilter(patch: Partial<FilterState>) {
    filters.value = { ...filters.value, ...patch }
  }

  const filteredSubitems = computed<Subitem[]>(() =>
    dataset.value ? filterSubitems(dataset.value.subitems, filters.value) : [],
  )

  const distinctCategories = computed<string[]>(() => {
    const s = new Set(dataset.value?.categories.map((c) => c.category) ?? [])
    return [...s]
  })

  const distinctProvinces = computed<string[]>(() =>
    dataset.value
      ? [...new Set(dataset.value.provinces.map((p) => p.province))].sort(
          (a, b) => a.localeCompare(b, 'zh-CN'),
        )
      : [],
  )

  return {
    dataset,
    loading,
    error,
    filters,
    load,
    resetFilters,
    setFilter,
    filteredSubitems,
    distinctCategories,
    distinctProvinces,
  }
})
