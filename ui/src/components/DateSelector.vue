<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLanguage } from '../composables/useLanguage';
import CalendarWidget from './CalendarWidget.vue';

interface DateSelectorProps {
  selectedDate: Date;
}

const props = defineProps<DateSelectorProps>();
const emit = defineEmits(['change']);

const { t, language } = useLanguage();
const isCalendarOpen = ref(false);

const handlePrevDay = () => {
  const newDate = new Date(props.selectedDate);
  newDate.setDate(props.selectedDate.getDate() - 1);
  emit('change', newDate);
};

const handleNextDay = () => {
  const newDate = new Date(props.selectedDate);
  newDate.setDate(props.selectedDate.getDate() + 1);
  emit('change', newDate);
};

const toggleCalendar = () => {
  isCalendarOpen.value = !isCalendarOpen.value;
};

const isToday = computed(() => new Date().toDateString() === props.selectedDate.toDateString());
const locale = computed(() => language.value === 'zh' ? 'zh-CN' : 'en-US');

const handleSelectDate = (date: Date) => {
  emit('change', date);
  // Optional: close on select, but keeping open is often better for exploration
  // isCalendarOpen.value = false;
};

</script>

<template>
  <div class="mb-6 relative z-10">
    <!-- Main Bar -->
    <div 
      :class="`flex items-center justify-between bg-slate-800/80 backdrop-blur rounded-xl p-4 border border-slate-700 shadow-lg transition-all cursor-pointer hover:border-slate-600 ${isCalendarOpen ? 'rounded-b-none border-b-0' : ''}`"
      @click="toggleCalendar"
    >
      <div class="flex items-center gap-4">
        <div :class="`p-2 rounded-lg transition-colors ${isCalendarOpen ? 'bg-indigo-500 text-white' : 'bg-indigo-500/20 text-indigo-400'}`">
          <!-- CalendarIcon size={24} -->
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-calendar"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>
        </div>
        <div>
          <h2 class="text-lg font-semibold text-slate-100 flex items-center gap-2">
            {{ selectedDate.toLocaleDateString(locale, { month: 'long', day: 'numeric', year: 'numeric' }) }}
            <svg v-if="isCalendarOpen" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-up text-slate-500"><path d="m18 15-6-6-6 6"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down text-slate-500"><path d="m6 9 6 6 6-6"/></svg>
          </h2>
          <p class="text-sm text-slate-400">
            {{ isToday ? t.date.tonight : selectedDate.toLocaleDateString(locale, { weekday: 'long' }) }}
          </p>
        </div>
      </div>

      <!-- Mini Navigation (only show if calendar is closed for quick access) -->
      <div v-if="!isCalendarOpen" class="flex items-center gap-2">
        <button 
          @click.stop="handlePrevDay"
          class="p-2 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
        >
          <!-- ChevronLeft size={20} -->
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-left"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <button 
          @click.stop="handleNextDay"
          :disabled="isToday"
          :class="`p-2 rounded-lg transition-colors ${
            isToday 
              ? 'text-slate-600 cursor-not-allowed' 
              : 'hover:bg-slate-700 text-slate-300'
          }`"
        >
          <!-- ChevronRight size={20} -->
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-right"><path d="m9 18 6-6-6-6"/></svg>
        </button>
      </div>
    </div>

    <!-- Expanded Calendar -->
    <CalendarWidget 
      v-if="isCalendarOpen"
      :selected-date="selectedDate" 
      @select-date="handleSelectDate" 
    />
  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>