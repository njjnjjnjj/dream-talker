<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useLanguage } from '../composables/useLanguage';
import { type SleepRecord } from '../types';
import { useRecordsApi } from '../api/records';
import DateSelector from '../components/DateSelector.vue';
import RecordCard from '../components/RecordCard.vue';
import SearchBar from '../components/SearchBar.vue';
import Timeline from '../components/Timeline.vue';

const { t } = useLanguage();
const { records, isLoading, error, fetchRecordsByDate, getAudioUrl, fetchMonthlyActivity } = useRecordsApi();

const selectedDate = ref<Date>(new Date());
const searchTerm = ref('');
const showFavoritesOnly = ref(false);
const sortOrder = ref<'asc' | 'desc'>('asc');
const isTimelineExpanded = ref(false);
const isDeleteMode = ref(false);

// Load data on date change
onMounted(() => {
  fetchRecordsByDate(selectedDate.value);
  const now = new Date();
  fetchMonthlyActivity(now.getFullYear(), now.getMonth() + 1);
});


const handleDateChange = (newDate: Date) => {
  selectedDate.value = newDate;
  fetchRecordsByDate(newDate);
  searchTerm.value = ''; // Reset search on date change
};

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
};

const handleUpdateRecord = (id: string, updates: Partial<SleepRecord>) => {
  records.value = records.value.map(rec => rec.id === id ? { ...rec, ...updates } : rec);
};

const handleDeleteRecord = (id: string) => {
  records.value = records.value.filter(rec => rec.id !== id);
};

// Filter and sort records
const filteredRecords = computed(() => {
  const filtered = records.value.filter(record => {
    const matchesSearch = record.transcription.toLowerCase().includes(searchTerm.value.toLowerCase());
    const matchesFav = showFavoritesOnly.value ? record.is_favorite : true;
    return matchesSearch && matchesFav;
  });

  return filtered.sort((a, b) => {
    const dateA = new Date(a.timestamp).getTime();
    const dateB = new Date(b.timestamp).getTime();
    return sortOrder.value === 'asc' ? dateA - dateB : dateB - dateA;
  });
});

const getRecordWithAudioUrl = (record: SleepRecord) => {
  return {
    ...record,
    audioUrl: getAudioUrl(record.audio_url),
  };
};

const smoothScrollTo = (y: number, duration = 500) => {
  const start = window.scrollY;
  const distance = y - start;
  let startTime: number | null = null;

  const ease = (t: number) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

  const animation = (currentTime: number) => {
    if (startTime === null) startTime = currentTime;
    const timeElapsed = currentTime - startTime;
    const progress = Math.min(timeElapsed / duration, 1);
    
    window.scrollTo(0, start + distance * ease(progress));

    if (timeElapsed < duration) {
      requestAnimationFrame(animation);
    }
  };

  requestAnimationFrame(animation);
};

const scrollToRecord = (recordId: string) => {
  const element = document.getElementById(`record-${recordId}`);
  if (element) {
    const elementRect = element.getBoundingClientRect();
    const absoluteElementTop = elementRect.top + window.scrollY;
    const middle = absoluteElementTop - (window.innerHeight / 2) + (elementRect.height / 2);
    
    smoothScrollTo(middle, 300); // Scroll over 300ms

    // Highlight the card briefly
    element.classList.add('ring-2', 'ring-indigo-500', 'transition-all', 'duration-500');
    setTimeout(() => {
      element.classList.remove('ring-2', 'ring-indigo-500');
    }, 1500);
  }
};
</script>

<template>
  <div class="animate-in slide-in-from-bottom-4 duration-500">
    <DateSelector :selected-date="selectedDate" @change="handleDateChange" />
    
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
      <div class="flex items-center gap-2">
        <span class="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
          {{ filteredRecords.length }} / {{ records.length }} {{ t.timeline.eventsDetected }}
        </span>
          <button @click="isTimelineExpanded = !isTimelineExpanded" class="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800" :title="isTimelineExpanded ? 'Collapse Timeline' : 'Expand Timeline'">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-hourglass transition-transform duration-300" :class="{'rotate-90': isTimelineExpanded}"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></svg>
          </button>
          <button
            @click="toggleSortOrder"
            class="p-2 rounded-lg transition-all duration-200 border"
            :class="sortOrder === 'desc' ? 'bg-indigo-600/20 border-indigo-500/30 text-indigo-400' : 'text-slate-400 hover:text-indigo-400 bg-slate-900/50 hover:bg-slate-800 border-transparent hover:border-slate-700'"
            title="Toggle Sort Order"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-up-down transition-transform duration-300" :class="{'rotate-180': sortOrder === 'desc'}">
              <path d="m21 16-4 4-4-4"/>
              <path d="M17 20V4"/>
              <path d="m3 8 4-4 4 4"/>
              <path d="M7 4v16"/>
            </svg>
          </button>

          <button
            @click="isDeleteMode = !isDeleteMode"
            class="p-2 rounded-lg transition-all duration-200 border"
            :class="isDeleteMode ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'text-slate-400 hover:text-red-400 bg-slate-900/50 hover:bg-slate-800 border-transparent hover:border-slate-700'"
            title="Toggle Delete Mode"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash-2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
          </button>
      </div>
    </div>
    
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="transform -translate-y-4 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-4 opacity-0"
    >
      <div v-if="isTimelineExpanded" class="mb-6">
        <Timeline :records="filteredRecords" @scroll-to-record="scrollToRecord" />
      </div>
    </Transition>


    <div class="grid gap-6">
      <template v-if="filteredRecords.length > 0">
        <RecordCard
          v-for="record in filteredRecords"
          :key="record.id"
          :id="`record-${record.id}`"
          :record="getRecordWithAudioUrl(record)"
          :is-delete-mode="isDeleteMode"
          @update-record="handleUpdateRecord"
          @delete-record="handleDeleteRecord"
        />
      </template>
      <template v-else>
        <div class="text-center py-20 bg-slate-900/30 rounded-2xl border border-dashed border-slate-800">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-activity mx-auto text-slate-600 mb-4 opacity-50"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          <p class="text-slate-500 text-lg">
            {{ records.length === 0 ? t.timeline.noEvents : t.timeline.noResults }}
          </p>
          <p v-if="records.length === 0" class="text-slate-600 text-sm mt-1">{{ t.timeline.silence }}</p>
        </div>
      </template>
    </div>
  </div>
</template>