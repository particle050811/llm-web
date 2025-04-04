import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: { // 新增：添加 resolve.alias 配置
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '') // 保留 /api 前缀
      }
    }
  },
  build: {
    rollupOptions: {
      input: {
        test: fileURLToPath(new URL('./src/pages/test.vue', import.meta.url)),
        upload: fileURLToPath(new URL('./src/pages/upload.vue', import.meta.url))
      }
    }
  }
})
