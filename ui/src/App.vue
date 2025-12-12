<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useLanguage } from './composables/useLanguage';
import { type SleepRecord, type KeywordStat, type DailyStats, type HourlyStat, type TagStat } from './types';
import DateSelector from './components/DateSelector.vue';
import RecordCard from './components/RecordCard.vue';
import StatisticsPanel from './components/StatisticsPanel.vue';
import SearchBar from './components/SearchBar.vue';
import { generateMockRecords, getKeywordStats, getWeeklyStats, getHourlyStats, getTagStats } from './services/mockData';

const { t, language, setLanguage } = useLanguage();

const selectedDate = ref<Date>(new Date());
const records = ref<SleepRecord[]>([]);
const activeTab = ref<'daily' | 'stats'>('daily');

// Stats Data State
const keywordData = ref<KeywordStat[]>([]);
const dailyStats = ref<DailyStats[]>([]);
const hourlyStats = ref<HourlyStat[]>([]);
const tagStats = ref<TagStat[]>([]);

// Search and Filter State
const searchTerm = ref('');
const showFavoritesOnly = ref(false);

// Load data on date or language change
watch([selectedDate, language], () => {
  // Simulate API fetch lag
  const timer = setTimeout(() => {
    records.value = generateMockRecords(selectedDate.value, language.value);
    searchTerm.value = ''; // Reset search on date change
  }, 300);
  return () => clearTimeout(timer);
}, { immediate: true });

// Load static stats data
onMounted(() => {
  keywordData.value = getKeywordStats(language.value);
  dailyStats.value = getWeeklyStats(language.value);
  hourlyStats.value = getHourlyStats();
  tagStats.value = getTagStats(language.value);
});

watch(language, () => {
  keywordData.value = getKeywordStats(language.value);
  dailyStats.value = getWeeklyStats(language.value);
  hourlyStats.value = getHourlyStats();
  tagStats.value = getTagStats(language.value);
});

const toggleLanguage = () => {
  setLanguage(language.value === 'en' ? 'zh' : 'en');
};

const handleUpdateRecord = (id: string, updates: Partial<SleepRecord>) => {
  records.value = records.value.map(rec => rec.id === id ? { ...rec, ...updates } : rec);
};

// Filter records based on search and favorites
const filteredRecords = computed(() => {
  return records.value.filter(record => {
    const matchesSearch = record.transcription.toLowerCase().includes(searchTerm.value.toLowerCase());
    const matchesFav = showFavoritesOnly.value ? record.isFavorite : true;
    return matchesSearch && matchesFav;
  });
});

</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/20">
    
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
      <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="bg-indigo-600 p-2 rounded-lg text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
            <!-- <Moon size={20} fill="currentColor" /> -->
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-moon"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
          </div>
          <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-slate-100">
            {{ t.appTitle }}
          </h1>
        </div>
        
        <div class="flex items-center gap-4">
          <nav class="flex bg-slate-900/50 p-1 rounded-lg border border-slate-800">
            <button 
              @click="activeTab = 'daily'"
              :class="`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'daily' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-slate-200'
              }`"
            >
              <!-- <Mic size={16} /> -->
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-mic"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
              <span class="hidden sm:inline">{{ t.tabs.recordings }}</span>
            </button>
            <button 
              @click="activeTab = 'stats'"
              :class="`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === 'stats' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-slate-200'
              }`"
            >
              <!-- <BarChart2 size={16} /> -->
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bar-chart-2"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>
              <span class="hidden sm:inline">{{ t.tabs.insights }}</span>
            </button>
          </nav>

          <button
            @click="toggleLanguage"
            class="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
            title="Switch Language"
          >
            <!-- <Globe size={20} /> -->
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-globe"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-5xl mx-auto px-4 py-8">
      
      <div v-if="activeTab === 'daily'" class="animate-in slide-in-from-bottom-4 duration-500">
        <DateSelector :selected-date="selectedDate" @change="selectedDate = $event" />
        
        <SearchBar
          :search-term="searchTerm"
          @search-change="searchTerm = $event"
          :show-favorites-only="showFavoritesOnly"
          @toggle-favorites="showFavoritesOnly = !showFavoritesOnly"
        />

        <div class="mb-6 flex items-center justify-between">
          <h3 class="text-slate-300 font-medium uppercase tracking-wider text-sm">
            {{ t.timeline.title }}
          </h3>
          <span class="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
            {{ filteredRecords.length }} / {{ records.length }} {{ t.timeline.eventsDetected }}
          </span>
        </div>

        <div class="grid gap-6">
          <template v-if="filteredRecords.length > 0">
            <RecordCard 
              v-for="record in filteredRecords"
              :key="record.id" 
              :record="record" 
              @update-record="handleUpdateRecord"
            />
          </template>
          <template v-else>
            <div class="text-center py-20 bg-slate-900/30 rounded-2xl border border-dashed border-slate-800">
              <!-- <Activity className="mx-auto text-slate-600 mb-4 opacity-50" size={48} /> -->
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-activity mx-auto text-slate-600 mb-4 opacity-50"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              <p class="text-slate-500 text-lg">
                {{ records.length === 0 ? t.timeline.noEvents : t.timeline.noResults }}
              </p>
              <p v-if="records.length === 0" class="text-slate-600 text-sm mt-1">{{ t.timeline.silence }}</p>
            </div>
          </template>
        </div>
      </div>

      <div v-if="activeTab === 'stats'" class="animate-in slide-in-from-bottom-4 duration-500">
        <StatisticsPanel 
          :daily-stats="dailyStats" 
          :hourly-stats="hourlyStats"
          :tag-stats="tagStats"
          :keyword-data="keywordData"
        />
      </div>

    </main>
  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>
