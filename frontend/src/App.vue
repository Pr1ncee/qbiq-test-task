<template>
  <div class="app">
    <h1>Weather Dashboard</h1>
    <SearchBar @search="handleSearch" />
    <div v-if="loading" class="spinner">Loading...</div>
    <ErrorBanner v-if="error" :message="error" @dismiss="clearError" />
    <WeatherCard v-if="weatherData" :data="weatherData" />
    <HourlyChart v-if="weatherData?.hourly?.length" :hourly="weatherData.hourly" />
    <RecentSearches :searches="recentSearches" @select="handleSearch" />
  </div>
</template>

<script setup>
import { useWeather } from './composables/useWeather.js'
import SearchBar from './components/SearchBar.vue'
import WeatherCard from './components/WeatherCard.vue'
import HourlyChart from './components/HourlyChart.vue'
import RecentSearches from './components/RecentSearches.vue'
import ErrorBanner from './components/ErrorBanner.vue'

const { loading, error, weatherData, recentSearches, fetchWeather } = useWeather()

function handleSearch(city) {
  fetchWeather(city)
}

function clearError() {
  error.value = null
}
</script>

<style>
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f5f7fa;
  margin: 0;
  padding: 0;
}
.app {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}
h1 {
  font-size: 28px;
  color: #2c3e50;
  margin-bottom: 24px;
}
.spinner {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 18px;
}
</style>
