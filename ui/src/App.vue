<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import { useLanguage } from './composables/useLanguage';
import { Moon, Mic, BarChart2, Settings, Globe, ArrowUp, LogOut } from 'lucide-vue-next';

const { t, language, setLanguage } = useLanguage();
const route = useRoute();
const router = useRouter();
const showBackToTop = ref(false);

const isLoginPage = computed(() => route.name === 'login');

const handleScroll = () => {
  showBackToTop.value = window.scrollY > window.innerHeight;
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});

const toggleLanguage = () => {
  setLanguage(language.value === 'en' ? 'zh' : 'en');
};

const handleLogout = () => {
  sessionStorage.removeItem('access_token');
  router.push('/login');
};

const smoothScrollTo = (y: number, duration = 300) => {
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

const scrollToTop = () => {
  smoothScrollTo(0);
};
</script>

<template>
  <div v-if="!isLoginPage" class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/20">
    
    <!-- Header -->
    <header class="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
      <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="bg-indigo-600 p-2 rounded-lg text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
            <Moon :size="20" fill="currentColor" />
          </div>
          <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-slate-100">
            {{ t.appTitle }}
          </h1>
        </div>
        
        <div class="flex items-center gap-2 sm:gap-4"> <!-- Adjusted gap for mobile -->
          <nav class="flex bg-slate-900/50 p-1 rounded-lg border border-slate-800">
            <RouterLink
              to="/"
              class="nav-link"
            >
              <Mic :size="16" />
              <span class="hidden sm:inline">{{ t.tabs.recordings }}</span>
            </RouterLink>
            <RouterLink
              to="/stats"
              class="nav-link"
            >
              <BarChart2 :size="16" />
              <span class="hidden sm:inline">{{ t.tabs.insights }}</span>
            </RouterLink>
          </nav>
          
          <RouterLink
            to="/settings"
            class="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
            title="Settings"
          >
            <Settings :size="20" />
          </RouterLink>

          <button
            @click="toggleLanguage"
            class="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
            title="Switch Language"
          >
            <Globe :size="20" />
          </button>
          
          <button
            @click="handleLogout"
            class="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
            title="Logout"
          >
            <LogOut :size="20" />
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-5xl mx-auto px-4 py-8">
      <RouterView />
    </main>

    <!-- Back to Top Button -->
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-300"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <button
        v-if="showBackToTop"
        @click="scrollToTop"
        class="fixed bottom-6 right-6 sm:bottom-8 sm:right-8 z-50 w-12 h-12 bg-indigo-600/80 backdrop-blur-sm text-white rounded-full flex items-center justify-center shadow-lg hover:bg-indigo-500 transition-all duration-300 transform hover:-translate-y-1"
        title="Back to top"
      >
        <ArrowUp :size="24" />
      </button>
    </Transition>
  </div>
  <RouterView v-else />
</template>

<style>
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
  font-weight: 500;
  transition: all 0.2s;
  color: #94a3b8; /* slate-400 */
}
.nav-link:hover {
  color: #e2e8f0; /* slate-200 */
}
.router-link-exact-active {
  background-color: #4f46e5; /* indigo-600 */
  color: white;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
</style>
