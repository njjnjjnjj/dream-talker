<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { SleepRecord } from '../types';
import { useLanguage } from '../composables/useLanguage';
import { useRecordsApi } from '../api/records';
import WaveSurfer from 'wavesurfer.js';

interface RecordCardProps {
  record: SleepRecord;
  onUpdateRecord?: (id: string, updates: Partial<SleepRecord>) => void;
}

const props = defineProps<RecordCardProps>();
const emit = defineEmits(['updateRecord']);

const { t, language } = useLanguage();
const { updateRecordFavoriteStatus } = useRecordsApi();
const isPlaying = ref(false);
const isAudioLoaded = ref(false); // Track audio loading state
const isAudioError = ref(false); // Track audio error state
const isLoadingOnDemand = ref(false); // New state for on-demand loading
const currentTime = ref(0);
const audioPlayer = ref<HTMLAudioElement | null>(null); // Kept for potential future use, but not for playback control
const cardElement = ref<HTMLDivElement | null>(null);
const waveformContainer = ref<HTMLDivElement | null>(null);
const wavesurfer = ref<WaveSurfer | null>(null);
const duration = ref(props.record.duration);
const isIntersecting = ref(false); // Used for pre-loading

onMounted(() => {
  if (!waveformContainer.value || !cardElement.value) return;

  // Initialize WaveSurfer
  const token = sessionStorage.getItem('access_token');
  const headers = new Headers();
  if (token) {
    headers.append('Authorization', `Bearer ${token}`);
  }

  wavesurfer.value = WaveSurfer.create({
    container: waveformContainer.value,
    waveColor: 'rgb(51 65 85)', // slate-700
    progressColor: 'rgb(99 102 241)', // indigo-500
    barWidth: 3,
    barRadius: 3,
    barGap: 2,
    height: 32,
    cursorWidth: 0,
    normalize: true,
    fetchParams: {
      headers: headers
    }
  });

  const ws = wavesurfer.value;

  // WaveSurfer event listeners
  ws.on('ready', (newDuration: number) => {
    duration.value = newDuration;
    isLoadingOnDemand.value = false;
    isAudioLoaded.value = true;
    isAudioError.value = false;
  });
  ws.on('audioprocess', (time: number) => { currentTime.value = time; });
  ws.on('play', () => {
    isPlaying.value = true;
    document.dispatchEvent(new CustomEvent('wavesurfer-play', { detail: { instance: ws } }));
  });
  ws.on('pause', () => { isPlaying.value = false; });
  ws.on('finish', () => { isPlaying.value = false; });
  ws.on('error', (err: Error) => {
    console.error('WaveSurfer error:', err);
    isAudioError.value = true;
    isLoadingOnDemand.value = false;
  });

  // Listener to pause other instances
  const handleOtherPlayers = (e: Event) => {
    if ((e as CustomEvent).detail.instance !== ws) ws.pause();
  };
  document.addEventListener('wavesurfer-play', handleOtherPlayers);

  // Setup Intersection Observer for preloading
  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0];
      if (entry && entry.isIntersecting) {
        isIntersecting.value = true;
        // Load audio when card is about to be visible, if not already loaded
        if (!isAudioLoaded.value && !isLoadingOnDemand.value) {
          isLoadingOnDemand.value = true;
          const token = sessionStorage.getItem('access_token');
          const headers = new Headers();
          if (token) {
            headers.append('Authorization', `Bearer ${token}`);
          }
          ws.load(`/api/audio/${props.record.id}`);
        }
        // No need to unobserve, as loading should only happen once.
      }
    },
    { rootMargin: "200px" } // Trigger when 200px away from viewport
  );
  observer.observe(cardElement.value);

  // Cleanup on unmount
  onUnmounted(() => {
    ws.destroy();
    document.removeEventListener('wavesurfer-play', handleOtherPlayers);
    if (cardElement.value) {
      observer.unobserve(cardElement.value);
    }
  });
});

const togglePlay = () => {
  const ws = wavesurfer.value;
  if (!ws || isAudioError.value) return;

  // If audio is not loaded yet, clicking play will just wait
  // for the pre-loading to finish. The user can click play, and it will
  // start as soon as it's ready.
  if (!isAudioLoaded.value) {
      // If for some reason observer didn't trigger, trigger load now.
      if (!isLoadingOnDemand.value) {
          isLoadingOnDemand.value = true;
          const token = sessionStorage.getItem('access_token');
          const headers = new Headers();
          if (token) {
            headers.append('Authorization', `Bearer ${token}`);
          }
          ws.load(`/api/audio/${props.record.id}`);
      }
      // Play once ready
      ws.once('ready', () => {
          ws.play();
      });
      return;
  }
  
  ws.playPause();
};

const handleSeek = (event: MouseEvent) => {
  const ws = wavesurfer.value;
  if (!ws || !isAudioLoaded.value) return;

  const target = event.currentTarget as HTMLDivElement;
  const rect = target.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const progress = x / rect.width;
  ws.seekTo(progress);
};

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const toggleFavorite = async () => {
  const newFavoriteStatus = !props.record.is_favorite;
  try {
    await updateRecordFavoriteStatus(props.record.id, newFavoriteStatus);
    // Optimistically update the local state
    if (props.onUpdateRecord) {
      props.onUpdateRecord(props.record.id, { is_favorite: newFavoriteStatus });
    }
    emit('updateRecord', props.record.id, { is_favorite: newFavoriteStatus });
  } catch (error) {
    console.error('Failed to update favorite status:', error);
    // Revert UI if API call fails
    // You might want to show a toast notification here
  }
};

const timeString = computed(() => new Date(props.record.timestamp).toLocaleTimeString(language.value === 'zh' ? 'zh-CN' : 'en-US', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: true
}));

</script>

<template>
  <div
    ref="cardElement"
    :class="`bg-slate-800 rounded-xl p-5 border transition-all shadow-md group ${
      record.is_favorite
        ? 'border-amber-500/30 hover:border-amber-500/50 shadow-amber-900/10'
        : 'border-slate-700/50 hover:border-slate-600'
    }`"
  >
    
    <!-- Header Info -->
    <div class="flex justify-between items-start mb-4">
      <div class="flex items-center gap-3">
          <div :class="`p-2.5 rounded-full ${isPlaying ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-700/50 text-slate-400'}`">
              <!-- Clock size={18} -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clock"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <div>
              <div class="flex items-center gap-2">
                  <span class="text-sm sm:text-base md:text-lg font-bold font-mono tracking-tight text-white">{{ timeString }}</span> <!-- Even smaller text on tiny mobile -->
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
          record.is_favorite
            ? 'text-amber-400 bg-amber-400/10 hover:bg-amber-400/20'
            : 'text-slate-600 hover:text-slate-400 hover:bg-slate-700'
        }`"
        title="Toggle Favorite"
      >
        <!-- Star size={20} fill={record.is_favorite ? "currentColor" : "none"} -->
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" :fill="record.is_favorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      </button>
    </div>

    <!-- Audio Player Container -->
    <div class="bg-slate-900/50 rounded-lg p-3 mb-4 border border-slate-700/50 flex items-center gap-2 sm:gap-4"> <!-- Reverted flex-wrap, adjusted gap -->
        <!-- Play/Pause Button -->
        <button
           @click="togglePlay"
           :disabled="isLoadingOnDemand || isAudioError"
           :class="`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all ${
              isAudioError
              ? 'bg-red-500/10 text-red-500 cursor-not-allowed border border-red-500/20'
              : isLoadingOnDemand
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'
                : isPlaying
                  ? 'bg-indigo-500 text-white shadow-[0_0_10px_rgba(99,102,241,0.4)]'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
            }`"
        >
          <template v-if="isAudioError">
             <!-- Alert Triangle size={18} -->
             <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-alert-triangle"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>
          </template>
          <template v-else-if="isLoadingOnDemand">
             <!-- Loading Spinner -->
             <svg class="animate-spin h-5 w-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
          </template>
          <template v-else-if="isPlaying">
            <!-- Pause size={18} fill="currentColor" -->
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pause"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          </template>
          <template v-else>
            <!-- Play size={18} fill="currentColor" className="ml-1" -->
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-play ml-1"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </template>
        </button>

        <!-- Interactive Waveform / Progress Bar -->
        <div
          ref="waveformContainer"
          class="flex-1 h-full flex flex-col justify-center cursor-pointer min-w-[100px]"
          @click="handleSeek"
        >
          <!-- wavesurfer.js will mount here -->
        </div>

        <!-- Time Display -->
        <div class="flex-shrink-0 font-mono text-[9px] xs:text-xs sm:text-sm text-slate-400 min-w-[4.5rem] text-right whitespace-nowrap"> <!-- Smallest possible font, always visible -->
            <span :class="isPlaying ? 'text-indigo-400 font-bold' : ''">{{ formatTime(currentTime) }}</span>
            <span class="mx-0.5 opacity-50">/</span> <!-- Reduced mx -->
            <span>{{ formatTime(duration) }}</span>
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
/* Removed content-visibility as we are now using a more robust IntersectionObserver approach */
</style>