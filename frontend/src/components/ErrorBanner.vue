<template>
  <div class="error-banner">
    <span>{{ message }}</span>
    <button class="dismiss" @click="$emit('dismiss')">✕</button>
  </div>
</template>

<script setup>
defineProps({ message: { type: String, required: true } })
defineEmits(['dismiss'])
</script>

<style scoped>
.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.dismiss {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #721c24;
  padding: 0 4px;
}
</style>
