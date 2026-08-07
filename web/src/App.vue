<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import MouseGlow from '@/components/MouseGlow.vue'
import Starfield from '@/components/Starfield.vue'
import HomeHero from '@/sections/HomeHero.vue'
import MapSection from '@/sections/MapSection.vue'
import TimelineSection from '@/sections/TimelineSection.vue'
import CategorySection from '@/sections/CategorySection.vue'
import InheritorSection from '@/sections/InheritorSection.vue'
import ComparisonSection from '@/sections/ComparisonSection.vue'
import SearchSection from '@/sections/SearchSection.vue'
import DataSection from '@/sections/DataSection.vue'
import NoticeSection from '@/sections/NoticeSection.vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()

onMounted(() => {
  void store.load()
})
</script>

<template>
  <AppHeader />
  <MouseGlow />
  <Starfield />
  <main>
    <div v-if="store.error" class="container">
      <div class="error-box">
        数据加载失败：{{ store.error }}。请检查 web/public/data 下的 JSON 文件是否完整。
      </div>
    </div>
    <template v-else>
      <HomeHero id="hero" />
      <MapSection id="map" />
      <TimelineSection id="timeline" />
      <CategorySection id="categories" />
      <InheritorSection id="inheritors" />
      <ComparisonSection id="comparison" />
      <SearchSection id="search" />
      <DataSection id="data" />
      <NoticeSection id="notes" />
    </template>
  </main>
  <AppFooter />
</template>
