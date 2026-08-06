<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
</script>

<template>
  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="muted small">
        非遗星图 · 国家级非物质文化遗产项目传承观察
        <span v-if="store.dataset">
          数据版本 {{ store.dataset.metadata.data_version }} · 更新于
          {{ store.dataset.metadata.updated_at }}
        </span>
      </div>
      <div class="small muted">
        数据来源：中国非物质文化遗产网（ihchina.cn）公开接口；本项目为大学生竞赛学术研究作品。
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  border-top: 1px solid var(--line);
  padding: 18px 0 30px;
}
.footer-inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
