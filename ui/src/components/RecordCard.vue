<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { type SleepRecord } from '../types';
import { useLanguage } from '../composables/useLanguage';

interface RecordCardProps {
  record: SleepRecord;
  onUpdateRecord?: (id: string, updates: Partial<SleepRecord>) => void;
}

const props = defineProps<RecordCardProps>();
const emit = defineEmits(['updateRecord']);

const { t, language } = useLanguage();
const isPlaying = ref(false);
const currentTime = ref(0);

// Create a static, consistent waveform pattern based on the record ID
const waveformData = computed(() => {
  const bars = 60;
  // Simple pseudo-random generator seeded by id string length + index
  return Array.from({ length: bars }, (_, i) => {
      const seed = props.record.id.charCodeAt(props.record.id.length - 1) + i;
      // Generate values between 20% and 100% height
      return 20 + (Math.sin(seed) * 40 + 40); 
  });
});

let animationFrameId: number | null = null;
let lastTime = performance.now();

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});

const togglePlay = () => {
  if (isPlaying.value) {
    isPlaying.value = false;
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
  } else {
    isPlaying.value = true;
    lastTime = performance.now();
    animationFrameId = requestAnimationFrame(animatePlay);
    
    // If we are at the end, restart
    if (currentTime.value >= props.record.duration) {
      currentTime.value = 0;
    }
  }
};

const animatePlay = (time: number) => {
  const deltaTime = (time - lastTime) / 1000;
  lastTime = time;

  currentTime.value += deltaTime;
  if (currentTime.value >= props.record.duration) {
    isPlaying.value = false;
    currentTime.value = props.record.duration;
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
  } else {
    animationFrameId = requestAnimationFrame(animatePlay);
  }
};

const handleSeek = (event: MouseEvent) => {
  const target = event.currentTarget as HTMLDivElement;
  const rect = target.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const percentage = Math.min(Math.max(x / rect.width, 0), 1);
  const newTime = percentage * props.record.duration;
  
  currentTime.value = newTime;
  
  // Optional: If we want to auto-play on seek, uncomment:
  // if (!isPlaying.value) togglePlay();
};

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const toggleFavorite = () => {
  if (props.onUpdateRecord) {
    props.onUpdateRecord(props.record.id, { isFavorite: !props.record.isFavorite });
  }
  emit('updateRecord', props.record.id, { isFavorite: !props.record.isFavorite });
};

const timeString = computed(() => new Date(props.record.timestamp).toLocaleTimeString(language.value === 'zh' ? 'zh-CN' : 'en-US', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: true
}));

</script>

<template>
  <div class="bg-slate-800 rounded-xl p-5 border border-slate-700/50 hover:border-slate-600 transition-all shadow-md group">
    
    <!-- Header Info -->
    <div class="flex justify-between items-start mb-4">
      <div class="flex items-center gap-3">
          <div :class="`p-2.5 rounded-full ${isPlaying ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-700/50 text-slate-400'}`">
              <!-- Clock size={18} -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clock"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <div>
              <div class="flex items-center gap-2">
                  <span class="text-lg font-bold font-mono tracking-tight text-white">{{ timeString }}</span>
                  <span v-if="record.confidence > 0.85" class="text-[10px] uppercase font-bold bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      High Quality
                  </span>
              </div>
              <div class="text-xs text-slate-400 mt-0.5">
                  {{ new Date(record.timestamp).toLocaleDateString() }}
              </div>
          </div>
      </div>
      
      <button 
        @click="toggleFavorite"
        :class="`p-2 rounded-full transition-all ${
          record.isFavorite 
            ? 'text-amber-400 bg-amber-400/10 hover:bg-amber-400/20' 
            : 'text-slate-600 hover:text-slate-400 hover:bg-slate-700'
        }`"
        title="Toggle Favorite"
      >
        <!-- Star size={20} fill={record.isFavorite ? "currentColor" : "none"} -->
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" :fill="record.isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      </button>
    </div>

    <!-- Audio Player Container -->
    <div class="bg-slate-900/50 rounded-lg p-3 mb-4 border border-slate-700/50 flex items-center gap-4">
        <!-- Play/Pause Button -->
        <button 
           @click="togglePlay"
           :class="`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
             isPlaying 
             ? 'bg-indigo-500 text-white shadow-[0_0_10px_rgba(99,102,241,0.4)]' 
             : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
           }`"
        >
          <template v-if="isPlaying">
            <!-- Pause size={18} fill="currentColor" -->
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pause"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          </template>
          <template v-else>
            <!-- Play size={18} fill="currentColor" className="ml-1" -->
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-play ml-1"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </template>
        </button>

        <!-- Interactive Waveform / Progress Bar -->
        <div class="flex-1 h-full flex flex-col justify-center cursor-pointer group/waveform" @click="handleSeek">
           <!-- Visual Bars -->
           <div class="flex items-center justify-between h-8 gap-[2px]">
              <div 
                 v-for="(height, i) in waveformData"
                 :key="i" 
                 :class="`w-1 rounded-full transition-colors duration-150 ${
                     (i / waveformData.length) <= (currentTime / record.duration) ? 'bg-indigo-500' : 'bg-slate-700 group-hover/waveform:bg-slate-600'
                 }`"
                 :style="{ height: `${height}%` }"
              />
           </div>
        </div>

        <!-- Time Display -->
        <div class="flex-shrink-0 font-mono text-xs text-slate-400 w-20 text-right">
            <span :class="isPlaying ? 'text-indigo-400 font-bold' : ''">{{ formatTime(currentTime) }}</span>
            <span class="mx-1 opacity-50">/</span>
            <span>{{ formatTime(record.duration) }}</span>
        </div>
    </div>
    
    <!-- Transcript -->
    <div class="relative mb-3 pl-1">
      <p class="text-lg text-slate-200 font-medium italic leading-relaxed">
        "{{ record.transcription }}"
      </p>
    </div>

    <!-- Tags -->
    <div v-if="record.tags && record.tags.length > 0" class="flex gap-2 flex-wrap">
        <span v-for="tag in record.tags" :key="tag" class="flex items-center gap-1 text-xs font-medium text-slate-400 bg-slate-700/50 px-2 py-1 rounded-md border border-slate-700 hover:bg-slate-700 hover:text-slate-200 transition-colors cursor-default">
            <!-- Tag size={10} -->
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-tag"><path d="M12.586 1.586A2 2 0 0 0 11.172 1H3a2 2 0 0 0-2 2v8.172a2 2 0 0 0 .586 1.414L12 22l10-10L12.586 1.586z"/><circle cx="7" cy="7" r="2"/></svg>
            {{ tag }}
        </span>
        <span :class="record.confidence > 0.8 ? 'text-xs px-2 py-1 text-emerald-500 ml-auto' : 'text-xs px-2 py-1 text-amber-500 ml-auto'">
            {{ Math.round(record.confidence * 100) }}% {{ t.card.match }}
        </span>
    </div>

  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>