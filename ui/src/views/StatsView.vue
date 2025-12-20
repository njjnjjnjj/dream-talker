<script setup lang="ts">
import { computed, watch } from 'vue';
import { useRecordsApi } from '../api/records';
import StatisticsPanel from '../components/StatisticsPanel.vue';

const { statistics, fetchStatistics } = useRecordsApi();

// Stats Data State (Computed from API response)
const keywordData = computed(() => statistics.value?.keywordData || []);
const dailyStats = computed(() => statistics.value?.dailyStats || []);
const hourlyStats = computed(() => statistics.value?.hourlyStats || []);
const tagStats = computed(() => statistics.value?.tagStats || []);

// Fetch stats on component mount
fetchStatistics();

const handleStatsRangeChange = (range: { startDate: Date; endDate: Date }) => {
  fetchStatistics({ startDate: range.startDate, endDate: range.endDate });
};
</script>

<template>
  <div class="animate-in slide-in-from-bottom-4 duration-500">
    <StatisticsPanel
      :daily-stats="dailyStats"
      :hourly-stats="hourlyStats"
      :tag-stats="tagStats"
      :keyword-data="keywordData"
      @range-change="handleStatsRangeChange"
    />
  </div>
</template>