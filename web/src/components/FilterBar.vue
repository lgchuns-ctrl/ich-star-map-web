<script setup lang="ts">
import { computed } from 'vue'
import type { BatchRow, EntryType, FilterState } from '@/types'
import { BATCH_LABELS, ENTRY_TYPE_LABELS } from '@/types'

const props = defineProps<{
  categories: string[]
  batches: BatchRow[]
  provinces: string[]
  modelValue: FilterState
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: FilterState): void
  (e: 'reset'): void
}>()

const f = computed({
  get: () => props.modelValue,
  set: (v: FilterState) => emit('update:modelValue', v),
})

function patch(p: Partial<FilterState>) {
  emit('update:modelValue', { ...props.modelValue, ...p })
}

function reset() {
  emit('reset')
}

const entryTypes: Array<{ value: EntryType | ''; label: string }> = [
  { value: '', label: '全部类型' },
  { value: 'new', label: ENTRY_TYPE_LABELS['new'] },
  { value: 'extension', label: ENTRY_TYPE_LABELS['extension'] },
]

const activeSummary = computed(() => {
  const parts: string[] = []
  if (f.value.category) parts.push(`类别：${f.value.category}`)
  if (f.value.batch !== null && f.value.batch !== undefined) {
    parts.push(`批次：${BATCH_LABELS[f.value.batch]?.label ?? f.value.batch}`)
  }
  if (f.value.entryType) parts.push(`类型：${ENTRY_TYPE_LABELS[f.value.entryType]}`)
  if (f.value.province) parts.push(`地区：${f.value.province}`)
  return parts
})
</script>

<template>
  <div class="filter-bar card">
    <div class="filter-grid">
      <label class="field">
        <span class="field-label">类别</span>
        <select v-model="f.category" class="select">
          <option value="">全部类别</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">批次</span>
        <select :value="f.batch ?? ''" class="select" @change="patch({ batch: ($event.target as HTMLSelectElement).value ? Number(($event.target as HTMLSelectElement).value) : null })">
          <option value="">全部批次</option>
          <option v-for="b in batches" :key="b.batch_no" :value="b.batch_no">
            {{ BATCH_LABELS[b.batch_no]?.label ?? b.batch_no }}
          </option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">类型</span>
        <select :value="f.entryType" class="select" @change="patch({ entryType: ($event.target as HTMLSelectElement).value as EntryType | '' })">
          <option v-for="t in entryTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">地区</span>
        <select :value="f.province" class="select" @change="patch({ province: ($event.target as HTMLSelectElement).value })">
          <option value="">全部地区</option>
          <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
        </select>
      </label>
      <div class="field field-action">
        <button type="button" class="btn btn-sm" @click="reset">重置筛选</button>
      </div>
    </div>
    <div v-if="activeSummary.length" class="active-summary small">
      当前筛选条件：{{ activeSummary.join(' · ') }}
    </div>
    <div v-else class="active-summary small">当前筛选条件：无（展示全部数据）</div>
  </div>
</template>

<style scoped>
.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  align-items: end;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field-label {
  font-size: 12px;
  color: var(--ink-2);
}
.field-action {
  justify-content: flex-end;
  flex-direction: row;
  align-items: center;
}
.active-summary {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
}
</style>
