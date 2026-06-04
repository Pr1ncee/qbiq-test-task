import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const RECENT_KEY = 'weather_recent_searches'

const loading = ref(false)
const error = ref(null)
const weatherData = ref(null)

function saveRecent(city) {
  const existing = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  const updated = [city, ...existing.filter(c => c.toLowerCase() !== city.toLowerCase())].slice(0, 5)
  localStorage.setItem(RECENT_KEY, JSON.stringify(updated))
}

export function useWeather() {
  const recentSearches = computed(() => {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  })

  async function fetchWeather(city) {
    if (!city.trim()) return
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API_BASE}/weather`, { params: { city } })
      weatherData.value = data
      saveRecent(data.city)
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch weather data'
      weatherData.value = null
    } finally {
      loading.value = false
    }
  }

  return { loading, error, weatherData, recentSearches, fetchWeather }
}
