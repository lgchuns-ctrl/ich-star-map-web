<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
</script>

<template>
  <div class="disclaimer-box">
    <strong>数据口径说明：</strong>
    相关指标基于公开国家级名录及国家级代表性传承人数据构建，仅反映公开数据中的资源配置与覆盖情况，
    不代表官方濒危等级或保护成效评价。
    <template v-if="store.dataset">
      当前数据版本 {{ store.dataset.metadata.data_version }}，更新于
      {{ store.dataset.metadata.updated_at }}。
    </template>
  </div>
</template>
