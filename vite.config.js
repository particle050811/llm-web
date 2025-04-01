import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      input: {
        test: fileURLToPath(new URL('./src/pages/test.vue', import.meta.url)),
        upload: fileURLToPath(new URL('./src/pages/upload.vue', import.meta.url))
      }
    }
  }
})
