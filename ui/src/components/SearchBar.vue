<script setup lang="ts">
import { useLanguage } from '../composables/useLanguage';

interface SearchBarProps {
  searchTerm: string;
  showFavoritesOnly: boolean;
}

const props = defineProps<SearchBarProps>();
const emit = defineEmits(['searchChange', 'toggleFavorites']);

const { t } = useLanguage();

const handleSearchChange = (event: Event) => {
  emit('searchChange', (event.target as HTMLInputElement).value);
};

const handleToggleFavorites = () => {
  emit('toggleFavorites');
};

</script>

<template>
  <div class="flex gap-3 mb-6 bg-slate-900/50 p-2 rounded-xl border border-slate-800">
    <div class="relative flex-1">
      <!-- Search size={18} -->
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      <input 
        type="text" 
        :value="props.searchTerm"
        @input="handleSearchChange"
        :placeholder="t.search.placeholder"
        class="w-full bg-slate-800 text-slate-200 pl-10 pr-4 py-2 rounded-lg border border-transparent focus:border-indigo-500 focus:outline-none transition-all placeholder:text-slate-600"
      />
    </div>
    <button 
      @click="handleToggleFavorites"
      :class="`flex items-center gap-2 px-3 py-2 rounded-lg transition-all border ${
        props.showFavoritesOnly 
          ? 'bg-amber-500/10 text-amber-400 border-amber-500/50' 
          : 'bg-slate-800 text-slate-400 border-transparent hover:text-slate-200'
      }`"
      :title="t.search.onlyFavorites"
    >
      <!-- Star size={18} fill={showFavoritesOnly ? "currentColor" : "none"} -->
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" :fill="props.showFavoritesOnly ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      <span class="hidden sm:inline text-sm font-medium">{{ t.search.onlyFavorites }}</span>
    </button>
  </div>
</template>

<style scoped>
/* Add any scoped styles here if necessary */
</style>