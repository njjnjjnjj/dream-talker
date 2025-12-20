<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useLanguage } from '../composables/useLanguage';

const { t } = useLanguage();

// --- Icon Generator Logic ---
const canvas = ref<HTMLCanvasElement | null>(null);
const iconSize = 180;
const backgroundColor = '#4f46e5'; // bg-indigo-600
const iconColor = 'white';

const svgString = `
  <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 24 24" fill="${iconColor}" stroke="${iconColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
  </svg>
`;

const renderIcon = () => {
  const ctx = canvas.value?.getContext('2d');
  if (!ctx || !canvas.value) return;

  canvas.value.width = iconSize;
  canvas.value.height = iconSize;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const cornerRadius = iconSize * 0.1;
  ctx.beginPath();
  ctx.moveTo(cornerRadius, 0);
  ctx.lineTo(iconSize - cornerRadius, 0);
  ctx.arcTo(iconSize, 0, iconSize, cornerRadius, cornerRadius);
  ctx.lineTo(iconSize, iconSize - cornerRadius);
  ctx.arcTo(iconSize, iconSize, iconSize - cornerRadius, iconSize, cornerRadius);
  ctx.lineTo(cornerRadius, iconSize);
  ctx.arcTo(0, iconSize, 0, iconSize - cornerRadius, cornerRadius);
  ctx.lineTo(0, cornerRadius);
  ctx.arcTo(0, 0, cornerRadius, 0, cornerRadius);
  ctx.closePath();

  ctx.fillStyle = backgroundColor;
  ctx.fill();

  const img = new Image();
  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  img.onload = () => {
    const padding = iconSize * 0.2;
    const finalIconSize = iconSize - padding * 2;
    ctx.drawImage(img, padding, padding, finalIconSize, finalIconSize);
    URL.revokeObjectURL(url);
  };

  img.src = url;
};

const downloadIcon = () => {
  if (!canvas.value) return;
  const link = document.createElement('a');
  link.download = 'apple-touch-icon.png';
  link.href = canvas.value.toDataURL('image/png');
  link.click();
};

onMounted(() => {
  renderIcon();
});
</script>

<template>
  <div class="animate-in slide-in-from-bottom-4 duration-500 text-white">
    <h1 class="text-3xl font-bold mb-8 text-slate-100">{{ t.settings.title }}</h1>

    <div class="space-y-12">
      <!-- Section: iOS App Icon -->
      <section>
        <h2 class="text-xl font-semibold mb-3 text-slate-200 border-b border-slate-700 pb-3">{{ t.settings.iconSectionTitle }}</h2>
        <div class="flex flex-col md:flex-row items-start gap-6 bg-slate-900/50 p-6 rounded-lg border border-slate-800">
          <div class="flex-shrink-0">
            <canvas ref="canvas" class="rounded-lg border border-slate-700 w-32 h-32 md:w-48 md:h-48"></canvas>
          </div>
          <div class="flex-grow">
            <p class="text-slate-300 mb-4"
              v-html="t.settings.iconSectionDesc.replace('{file}', '<code>apple-touch-icon.png</code>').replace('{folder}', '<code>public</code>')">
            </p>
            <button
              @click="downloadIcon"
              class="inline-flex items-center gap-2 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-500 transition-colors shadow-md"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
              {{ t.settings.iconDownloadBtn }}
            </button>
          </div>
        </div>
      </section>

      <!-- Placeholder for future settings -->
      <section>
        <h2 class="text-xl font-semibold mb-3 text-slate-200 border-b border-slate-700 pb-3">{{ t.settings.moreSettingsTitle }}</h2>
        <div class="bg-slate-900/50 p-6 rounded-lg border border-slate-800 text-center">
          <p class="text-slate-500">{{ t.settings.moreSettingsDesc }}</p>
        </div>
      </section>
    </div>
  </div>
</template>