<script setup lang="ts">
import { NAV_SECTIONS } from '@/config/nav'
import { useScrollSpy } from '@/utils/scroll'

const ids = NAV_SECTIONS.map((s) => s.id)
const { activeId } = useScrollSpy(ids)
</script>

<template>
  <header class="site-header">
    <div class="container header-inner">
      <a href="#hero" class="brand">
        <span class="brand-star">✦</span>
        <span>非遗星图</span>
      </a>
      <nav class="nav">
        <a
          v-for="s in NAV_SECTIONS"
          :key="s.id"
          :href="`#${s.id}`"
          class="nav-link"
          :class="{ active: activeId === s.id }"
        >
          {{ s.label }}
        </a>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(11, 16, 26, 0.82);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif);
  font-size: 20px;
  letter-spacing: 0.12em;
  color: var(--ink-0);
}
.brand-star {
  color: var(--gold);
  font-size: 18px;
}
.nav {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.nav-link {
  padding: 6px 12px;
  border-radius: 999px;
  color: var(--ink-1);
  font-size: 14px;
}
.nav-link:hover {
  color: var(--gold);
  text-decoration: none;
  background: rgba(217, 184, 119, 0.08);
}
.nav-link.router-link-exact-active {
  color: var(--gold);
  background: rgba(217, 184, 119, 0.14);
}
.nav-link.active {
  color: var(--gold);
  background: rgba(217, 184, 119, 0.14);
}
@media (max-width: 640px) {
  .brand {
    font-size: 16px;
  }
  .nav-link {
    font-size: 12px;
    padding: 5px 8px;
  }
  .nav {
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
