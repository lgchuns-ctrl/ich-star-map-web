<script setup lang="ts">
import { onBeforeUnmount, onMounted, watch } from 'vue'
import type { Subitem } from '@/types'
import { BATCH_LABELS, ENTRY_TYPE_LABELS } from '@/types'

const props = defineProps<{
  subitem: Subitem | null
  visible: boolean
}>()

const emit = defineEmits<{ (e: 'close'): void }>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.visible) emit('close')
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

watch(
  () => props.visible,
  (v) => {
    document.body.style.overflow = v ? 'hidden' : ''
  },
)
</script>

<template>
  <teleport to="body">
    <div v-if="visible" class="overlay" @click.self="emit('close')">
      <aside class="drawer" role="dialog" aria-label="项目详情">
        <button type="button" class="close" aria-label="关闭" @click="emit('close')">×</button>
        <template v-if="subitem">
          <h3 class="drawer-title">{{ subitem.project_name }}</h3>
          <dl class="detail-list">
            <div class="detail-row">
              <dt>项目编号</dt>
              <dd>{{ subitem.project_code }}</dd>
            </div>
            <div class="detail-row">
              <dt>类别</dt>
              <dd>{{ subitem.category }}</dd>
            </div>
            <div class="detail-row">
              <dt>公布批次</dt>
              <dd>{{ BATCH_LABELS[subitem.batch_no]?.label ?? subitem.batch_no }}</dd>
            </div>
            <div class="detail-row">
              <dt>新增/扩展</dt>
              <dd>{{ ENTRY_TYPE_LABELS[subitem.entry_type] ?? subitem.entry_type }}</dd>
            </div>
            <div class="detail-row">
              <dt>申报地区</dt>
              <dd>{{ subitem.region_raw || subitem.province }}</dd>
            </div>
            <div class="detail-row">
              <dt>省级地区</dt>
              <dd>{{ subitem.province }}</dd>
            </div>
            <div class="detail-row">
              <dt>保护单位</dt>
              <dd>{{ subitem.protection_unit || '—' }}</dd>
            </div>
            <div class="detail-row">
              <dt>官方来源</dt>
              <dd>
                <a :href="subitem.source_url" target="_blank" rel="noopener noreferrer">
                  中国非物质文化遗产网项目记录
                </a>
              </dd>
            </div>
            <div class="detail-row">
              <dt>数据更新时间</dt>
              <dd>{{ new Date().toISOString().slice(0, 10) }}</dd>
            </div>
          </dl>
        </template>
        <p v-else class="muted">未找到该项目详情。</p>
      </aside>
    </div>
  </teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 14, 0.66);
  z-index: 100;
}
.drawer {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: min(440px, 94vw);
  background: var(--bg-1);
  border-left: 1px solid var(--gold-dim);
  padding: 26px 22px;
  overflow-y: auto;
  box-shadow: -16px 0 60px rgba(0, 0, 0, 0.5);
  animation: slide-in 0.25s ease;
}
@keyframes slide-in {
  from {
    transform: translateX(30px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
.close {
  position: absolute;
  top: 14px;
  right: 16px;
  background: none;
  border: none;
  color: var(--ink-1);
  font-size: 26px;
  cursor: pointer;
}
.close:hover {
  color: var(--gold);
}
.drawer-title {
  font-size: 22px;
  margin: 0 0 18px;
  padding-right: 30px;
}
.detail-list {
  margin: 0;
}
.detail-row {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--line);
}
.detail-row dt {
  width: 92px;
  flex: none;
  color: var(--ink-2);
  font-size: 13px;
}
.detail-row dd {
  margin: 0;
  color: var(--ink-0);
  font-size: 14px;
  word-break: break-all;
}
</style>
