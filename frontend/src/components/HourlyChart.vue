<template>
  <div class="chart-container">
    <h3>Hourly Temperature &amp; Wind</h3>
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const props = defineProps({ hourly: { type: Array, required: true } })

const chartData = computed(() => ({
  labels: props.hourly.map(h => h.hour.slice(11, 16)),
  datasets: [
    {
      label: 'Temperature (°C)',
      data: props.hourly.map(h => h.temperature_c),
      borderColor: '#e74c3c',
      backgroundColor: 'rgba(231,76,60,0.1)',
      yAxisID: 'y',
      tension: 0.3,
    },
    {
      label: 'Wind Speed (km/h)',
      data: props.hourly.map(h => h.wind_speed_kmh),
      borderColor: '#3498db',
      backgroundColor: 'rgba(52,152,219,0.1)',
      yAxisID: 'y1',
      tension: 0.3,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  interaction: { mode: 'index', intersect: false },
  scales: {
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: { display: true, text: '°C' },
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: { display: true, text: 'km/h' },
      grid: { drawOnChartArea: false },
    },
  },
}
</script>

<style scoped>
.chart-container {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}
h3 { margin: 0 0 16px; }
</style>
