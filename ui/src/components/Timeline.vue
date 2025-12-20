<script setup lang="ts">
import { computed } from 'vue';
import { type SleepRecord } from '../types';

interface TimelineProps {
  records: SleepRecord[];
}

const props = defineProps<TimelineProps>();
const emit = defineEmits(['scrollToRecord']);

const timeRange = computed(() => {
  if (props.records.length === 0) {
    return { startHour: 0, endHour: 0, totalMinutes: 0 };
  }

  const timestamps = props.records.map(r => new Date(r.timestamp).getTime());
  const minDate = new Date(Math.min(...timestamps));
  const maxDate = new Date(Math.max(...timestamps));

  let startHour = minDate.getHours() - 1;
  let endHour = maxDate.getHours() + 2; // +2 to make the range inclusive of the last hour block

  // Clamp to 0-24 range
  startHour = Math.max(0, startHour);
  endHour = Math.min(24, endHour);
  
  // Handle edge case where records span across midnight, causing start > end
  if (startHour > endHour && props.records.some(r => new Date(r.timestamp).getHours() < 12)) {
      startHour = 0;
  }
  if (startHour > endHour && props.records.some(r => new Date(r.timestamp).getHours() > 12)) {
      endHour = 24;
  }

  const totalMinutes = (endHour - startHour) * 60;

  return { startHour, endHour, totalMinutes };
});

const getPosition = (timestamp: string) => {
  const { startHour, totalMinutes } = timeRange.value;
  if (totalMinutes === 0) return 0;
  
  const date = new Date(timestamp);
  const eventTotalMinutes = (date.getHours() * 60) + date.getMinutes();
  const relativeMinutes = eventTotalMinutes - (startHour * 60);

  return (relativeMinutes / totalMinutes) * 100;
};

const timelineEvents = computed(() => {
  if (!props.records || props.records.length === 0) return [];
  return props.records.map(record => ({
    id: record.id,
    timestamp: record.timestamp,
    position: getPosition(record.timestamp),
    is_favorite: record.is_favorite,
  }));
});

const hourMarkers = computed(() => {
  const { startHour, endHour, totalMinutes } = timeRange.value;
  if (totalMinutes === 0) return [];
  
  const markers = [];
  for (let hour = Math.ceil(startHour); hour < endHour; hour++) {
      const relativeMinutes = (hour - startHour) * 60;
      markers.push({
          hour,
          position: (relativeMinutes / totalMinutes) * 100,
      });
  }
  return markers;
});

const handleEventClick = (recordId: string) => {
  emit('scrollToRecord', recordId);
};
</script>

<template>
  <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-800">
    <div v-if="records.length > 0" class="relative w-full h-12">
      <!-- Timeline Background Track -->
      <div class="absolute top-1/2 -translate-y-1/2 w-full h-1 bg-slate-800 rounded-full z-0"></div>

      <!-- Hour Markers -->
      <div v-for="marker in hourMarkers" :key="marker.hour" class="absolute h-full top-0 flex flex-col items-center justify-start -translate-x-1/2 z-10" :style="{ left: `${marker.position}%` }">
        <span class="text-[10px] text-slate-500 mb-1">{{ marker.hour.toString().padStart(2, '0') }}</span>
        <div class="w-px h-2 bg-slate-700"></div>
      </div>

      <!-- Record Events -->
      <div
        v-for="event in timelineEvents"
        :key="event.id"
        class="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full cursor-pointer transition-all duration-200 transform hover:scale-150 z-20 border-2 border-slate-900/50"
        :class="event.is_favorite ? 'bg-amber-400 hover:bg-amber-300' : 'bg-indigo-500 hover:bg-indigo-400'"
        :style="{ left: `calc(${event.position}% - 6px)` }"
        :title="new Date(event.timestamp).toLocaleTimeString()"
        @click="handleEventClick(event.id)"
      >
      </div>
    </div>
    <div v-else class="text-center text-sm text-slate-500">
      No recordings on this day to build a timeline.
    </div>
  </div>
</template>
