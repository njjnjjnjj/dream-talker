<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import { useLanguage } from '../composables/useLanguage';
import { getMonthlyActivity } from '../services/mockData';
import { type MonthlyActivity } from '../types';

interface CalendarWidgetProps {
  selectedDate: Date;
}

const props = defineProps<CalendarWidgetProps>();
const emit = defineEmits(['selectDate']);

const { t, language } = useLanguage();
const currentMonth = ref(new Date(props.selectedDate));
const activityData = ref<MonthlyActivity>({});

// Reset to selected date's month when opened or changed externally
onMounted(() => {
  currentMonth.value = new Date(props.selectedDate);
});

// Fetch mock data when month changes
watch(currentMonth, () => {
  const year = currentMonth.value.getFullYear();
  const month = currentMonth.value.getMonth();
  const data = getMonthlyActivity(year, month);
  activityData.value = data;
}, { immediate: true });

const handlePrevMonth = () => {
  const newDate = new Date(currentMonth.value);
  newDate.setMonth(currentMonth.value.getMonth() - 1);
  currentMonth.value = newDate;
};

const handleNextMonth = () => {
  const newDate = new Date(currentMonth.value);
  newDate.setMonth(currentMonth.value.getMonth() + 1);
  currentMonth.value = newDate;
};

const handleDateClick = (day: number) => {
  const newDate = new Date(currentMonth.value);
  newDate.setDate(day);
  emit('selectDate', newDate);
};

const getDaysInMonth = (date: Date) => {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
};

const getFirstDayOfMonth = (date: Date) => {
  return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
};

const daysInMonth = computed(() => getDaysInMonth(currentMonth.value));
const firstDay = computed(() => getFirstDayOfMonth(currentMonth.value));
const daysArray = computed(() => Array.from({ length: daysInMonth.value }, (_, i) => i + 1));
const blanksArray = computed(() => Array.from({ length: firstDay.value }, (_, i) => i));

const monthYearString = computed(() => currentMonth.value.toLocaleDateString(language.value === 'zh' ? 'zh-CN' : 'en-US', {
  month: 'long',
  year: 'numeric'
}));

const isSelected = (day: number) => {
  return props.selectedDate.getDate() === day &&
         props.selectedDate.getMonth() === currentMonth.value.getMonth() &&
         props.selectedDate.getFullYear() === currentMonth.value.getFullYear();
};

const isToday = (day: number) => {
  const today = new Date();
  return today.getDate() === day &&
         today.getMonth() === currentMonth.value.getMonth() &&
         today.getFullYear() === currentMonth.value.getFullYear();
};

</script>

<template>
  <div class="bg-slate-800 rounded-b-xl border-x border-b border-slate-700 p-4 animate-in slide-in-from-top-2 duration-200">
    
    <!-- Calendar Header -->
    <div class="flex justify-between items-center mb-4">
      <button @click="handlePrevMonth" class="p-1 hover:bg-slate-700 rounded text-slate-400">
        <!-- ChevronLeft size={20} -->
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-left"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <span class="font-bold text-slate-200">{{ monthYearString }}</span>
      <button @click="handleNextMonth" class="p-1 hover:bg-slate-700 rounded text-slate-400">
        <!-- ChevronRight size={20} -->
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-right"><path d="m9 18 6-6-6-6"/></svg>
      </button>
    </div>

    <!-- Weekdays -->
    <div class="grid grid-cols-7 mb-2">
      <div v-for="day in t.date.weekdays" :key="day" class="text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">
        {{ day }}
      </div>
    </div>

    <!-- Days Grid -->
    <div class="grid grid-cols-7 gap-1">
      <div v-for="i in blanksArray" :key="`blank-${i}`" class="h-10"></div>
      
      <button
        v-for="day in daysArray"
        :key="day"
        @click="handleDateClick(day)"
        :class="`h-10 md:h-12 rounded-lg flex flex-col items-center justify-center relative transition-all border border-transparent
          ${isSelected(day) 
            ? 'bg-indigo-600 text-white shadow-lg border-indigo-500' 
            : 'hover:bg-slate-700 text-slate-300 hover:border-slate-600'}
          ${isToday(day) && !isSelected(day) ? 'bg-slate-700/50 text-indigo-300 border-slate-600' : ''}
        `"
      >
        <span :class="`text-sm ${isSelected(day) ? 'font-bold' : ''}`">{{ day }}</span>
        
        <div v-if="(activityData[`${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`] || 0) > 0" class="flex items-center justify-center mt-0.5">
           <!-- Badge for count -->
           <span :class="`text-[10px] px-1.5 rounded-full font-medium ${
             isSelected(day)
               ? 'bg-white/20 text-white'
               : 'bg-indigo-500/20 text-indigo-400'
           }`">
             {{ activityData[`${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`] || 0 }}
           </span>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>