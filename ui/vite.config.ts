import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // vueDevTools(),
    tailwindcss()
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  esbuild: {
    sourcemap: false, // 开发模式不生成 sourcemap
  },
  server: {
    host: true, // Make Vite accessible on the local network
    allowedHosts: [
      "dream.nimou.space"
    ],
    proxy: {
      // 代理 /api 请求
      '/api': {
        target: 'http://localhost:8569',
        changeOrigin: true,
      },
      // 代理 /vad WebSocket 请求
      '/vad': {
        target: 'ws://localhost:8569',
        ws: true,
      },
    },
  },
})
