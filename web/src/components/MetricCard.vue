<script setup lang="ts">
defineProps<{
  label: string
  value: number | string
  note?: string
}>()
</script>

<template>
  <div class="metric card">
    <div class="metric-value">{{ value }}</div>
    <div class="metric-label">{{ label }}</div>
    <div v-if="note" class="metric-note">{{ note }}</div>
  </div>
</template>

<style scoped>
.metric {
  text-align: center;
  padding: 18px 12px;
}
.metric-value {
  font-family: var(--font-serif);
  font-size: 34px;
  color: var(--gold);
  line-height: 1.2;
}
.metric-label {
  margin-top: 4px;
  color: var(--ink-0);
  font-size: 14px;
}
.metric-note {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ink-2);
}
</style>
