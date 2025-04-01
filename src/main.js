import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 根据URL路径动态加载不同页面
const path = window.location.pathname
let component

if (path === '/test') {
  component = (await import('./pages/test.vue')).default
} else if (path === '/upload') {
  component = (await import('./pages/upload.vue')).default
} else {
  // 默认加载test页面
  component = (await import('./pages/upload.vue')).default
}

const app = createApp(component)
app.use(ElementPlus)
app.mount('#app')