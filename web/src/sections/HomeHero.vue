<script setup lang="ts">
import { computed } from 'vue'
import MetricCard from '@/components/MetricCard.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import Reveal from '@/components/Reveal.vue'
import { useAppStore } from '@/stores/appStore'

defineProps<{ id: string }>()

const store = useAppStore()

const metrics = computed(() => {
  const d = store.dataset
  if (!d) return []
  return [
    {
      label: '地区子项记录',
      value: d.metadata.cleaned_subitem_count,
      note: '按申报地区展开',
    },
    {
      label: '独立项目',
      value: d.metadata.distinct_project_count,
      note: '按项目编号去重',
    },
    { label: '覆盖省级地区', value: d.provinces.length, note: '含中直单位等' },
    {
      label: '传承人公开记录',
      value: d.metadata.inheritor_count,
      note: '含第六批(2025)',
    },
  ]
})

const questions = [
  '国家级非遗项目与子项分布在哪些地区？',
  '省级地区之间类别结构有何差异？',
  '五批名录的新增与扩展如何变化？',
  '十大类别的空间与时间分布有何特点？',
  '代表性传承人的公开配置是否相对充足？',
  '项目数量、类别多样性与传承人配置有何关系？',
]
</script>

<template>
  <section :id="id" class="hero">
    <div class="container hero-inner">
      <p class="hero-kicker rise-1">数字人文 · 数据可视化 · 文化传承观察</p>
      <h1 class="hero-title rise-2">非遗星图</h1>
      <p class="hero-sub rise-3">
        国家级非物质文化遗产项目传承观察——以公开名录数据为星，铺开一幅地域与时间的文化星图。
      </p>
      <p v-if="store.dataset" class="hero-meta muted small rise-4">
        数据版本 {{ store.dataset.metadata.data_version }} · 更新于
        {{ store.dataset.metadata.updated_at }}
      </p>
      <div class="hero-actions rise-5">
        <a href="#map" class="btn btn-primary">进入全国分布</a>
        <a href="#search" class="btn">寻找一项非遗</a>
      </div>
      <div class="scroll-hint rise-6" aria-hidden="true">﹀</div>
    </div>
  </section>

  <div class="container metrics-section">
    <div class="grid-4">
      <Reveal v-for="(m, i) in metrics" :key="m.label" :delay="i * 110">
        <MetricCard :label="m.label" :note="m.note" class="hoverable">
          <template #value>
            <AnimatedNumber :value="m.value" />
          </template>
        </MetricCard>
      </Reveal>
    </div>
  </div>

  <section class="container site-section">
    <Reveal>
      <div class="section-head">
        <p class="section-kicker">QUESTIONS</p>
        <h2 class="section-title">本项目要回答的问题</h2>
      </div>
      <div class="question-grid">
        <Reveal v-for="(q, i) in questions" :key="q" :delay="i * 60">
          <div class="question-item hoverable">
            <span class="q-index">0{{ i + 1 }}</span>
            <span>{{ q }}</span>
          </div>
        </Reveal>
      </div>
    </Reveal>
  </section>

  <section class="container site-section">
    <Reveal>
      <div class="section-head">
        <p class="section-kicker">FEATURES</p>
        <h2 class="section-title">作品特点</h2>
      </div>
      <div class="grid-2">
        <Reveal :delay="0">
          <div class="card hoverable">
            <h3>真实数据 · 全程可溯</h3>
            <p class="muted">
              数据来自中国非物质文化遗产网公开接口，原始响应、请求日志、清洗脚本与质量报告全部归档于项目仓库，可逐条回溯。
            </p>
          </div>
        </Reveal>
        <Reveal :delay="140">
          <div class="card hoverable">
            <h3>双重统计口径</h3>
            <p class="muted">
              同时呈现“独立项目数”与“地区子项数”，避免把同一项目在不同地区的申报记录误算为多个项目。
            </p>
          </div>
        </Reveal>
        <Reveal :delay="280">
          <div class="card hoverable">
            <h3>透明的传承资源观察</h3>
            <p class="muted">
              使用可解释指标观察代表性传承人公开配置情况，明确声明不构成官方濒危等级或保护成效评价。
            </p>
          </div>
        </Reveal>
        <Reveal :delay="420">
          <div class="card hoverable">
            <h3>离线可用的静态站点</h3>
            <p class="muted">
              网页运行时不依赖在线接口，全部数据打包为本地 JSON；比赛现场断网时核心功能仍可运行。
            </p>
          </div>
        </Reveal>
      </div>
    </Reveal>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 72vh;
  display: flex;
  align-items: center;
  overflow: hidden;
  scroll-margin-top: 0;
  background: radial-gradient(1200px 600px at 70% 20%, rgba(217, 184, 119, 0.08), transparent 60%);
}
.hero-inner {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 60px 0;
}
.hero-kicker {
  color: var(--gold);
  letter-spacing: 0.35em;
  font-size: 13px;
  margin: 0 0 14px;
}
.rise-1,
.rise-2,
.rise-3,
.rise-4,
.rise-5,
.rise-6 {
  opacity: 0;
  animation: rise 0.9s ease forwards;
}
.rise-1 {
  animation-delay: 0.05s;
}
.rise-2 {
  animation-delay: 0.18s;
}
.rise-3 {
  animation-delay: 0.32s;
}
.rise-4 {
  animation-delay: 0.46s;
}
.rise-5 {
  animation-delay: 0.6s;
}
.rise-6 {
  animation-delay: 0.78s;
}
@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
.hero-title {
  font-size: clamp(46px, 9vw, 84px);
  margin: 0;
  letter-spacing: 0.18em;
  text-shadow: 0 0 40px rgba(217, 184, 119, 0.25);
}
.hero-sub {
  color: var(--ink-1);
  max-width: 620px;
  margin: 18px auto 10px;
  font-size: 16px;
}
.hero-meta {
  margin: 4px 0 26px;
}
.hero-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.scroll-hint {
  margin-top: 48px;
  color: var(--ink-2);
  font-size: 18px;
  animation: bounce 2s infinite;
}
@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(8px);
  }
}
.metrics-section {
  margin-top: -34px;
  position: relative;
  z-index: 2;
}
.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
@media (max-width: 900px) {
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}
.question-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 10px;
}
.question-item {
  display: flex;
  gap: 10px;
  align-items: baseline;
  padding: 10px 14px;
  border: 1px dashed var(--line);
  border-radius: 8px;
  color: var(--ink-1);
  font-size: 14px;
}
.q-index {
  color: var(--gold);
  font-family: var(--font-serif);
  flex: none;
}
</style>
