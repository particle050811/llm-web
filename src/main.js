import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router' // 导入路由配置
import App from './App.vue'   // 导入根组件

// 不再需要旧的路由逻辑

const app = createApp(App) // 使用根组件 App.vue

app.use(router)       // 使用路由
app.use(ElementPlus)  // 继续使用 ElementPlus
app.mount('#app')     // 挂载到 #app 元素