<template>
  <div class="search-bar">
    <input
      v-model="query"
      type="text"
      placeholder="Enter city name..."
      @keyup.enter="handleSearch"
    />
    <button @click="handleSearch" :disabled="!query.trim()">Search</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['search'])
const query = ref('')

function handleSearch() {
  if (query.value.trim()) {
    emit('search', query.value.trim())
  }
}
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}
.search-bar input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  outline: none;
}
.search-bar input:focus {
  border-color: #4a90e2;
}
.search-bar button {
  padding: 10px 20px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
}
.search-bar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
