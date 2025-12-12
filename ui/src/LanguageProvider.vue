<script setup lang="ts">
import { provideLanguage } from './composables/useLanguage';
import App from './App.vue';

provideLanguage();
</script>

<template>
  <App />
</template>