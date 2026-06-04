<template>
  <div v-if="searches.length" class="recent-searches">
    <span class="label">Recent:</span>
    <button
      v-for="city in searches"
      :key="city"
      class="chip"
      @click="$emit('select', city)"
    >
      {{ city }}
    </button>
  </div>
</template>

<script setup>
defineProps({ searches: { type: Array, default: () => [] } })
defineEmits(['select'])
</script>

<style scoped>
.recent-searches {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 16px;
}
.label { color: #666; font-size: 14px; }
.chip {
  padding: 4px 12px;
  background: #f0f4ff;
  border: 1px solid #c5d3f0;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  color: #3a5fc8;
}
.chip:hover { background: #dce6ff; }
</style>
