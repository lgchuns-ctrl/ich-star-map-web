<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()

onMounted(() => {
  void store.load()
})
</script>

<template>
  <AppHeader />
  <div v-if="store.error" class="container page">
    <div class="error-box">
      数据加载失败：{{ store.error }}。请检查 web/public/data 下的 JSON 文件是否完整。
    </div>
  </div>
  <main class="page" v-else>
    <router-view />
  </main>
  <AppFooter />
</template>
