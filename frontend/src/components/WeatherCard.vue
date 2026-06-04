<template>
  <div class="weather-card">
    <div class="card-header">
      <h2>{{ data.city }}</h2>
      <span class="cache-badge" :class="data.cached ? 'hit' : 'miss'">
        Cache: {{ data.cached ? 'HIT ✓' : 'MISS' }}
      </span>
    </div>
    <div class="card-body">
      <span class="temperature">{{ data.current.temperature_c }}°C</span>
      <span class="description">{{ data.current.weather_description }}</span>
      <span class="wind">Wind: {{ data.current.wind_speed_kmh }} km/h</span>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Object, required: true } })
</script>

<style scoped>
.weather-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-header h2 { margin: 0; font-size: 24px; }
.cache-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.cache-badge.hit { background: #d4edda; color: #155724; }
.cache-badge.miss { background: #fff3cd; color: #856404; }
.card-body {
  display: flex;
  gap: 20px;
  align-items: center;
  font-size: 18px;
}
.temperature { font-size: 36px; font-weight: 700; }
</style>
