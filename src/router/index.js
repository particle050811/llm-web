import { createRouter, createWebHistory } from 'vue-router';
import Home from '../pages/home.vue';
import EditReport from '../pages/editReport.vue';
import Test from '../pages/test.vue';     // 导入 test.vue
import Upload from '../pages/upload.vue'; // 导入 upload.vue

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '主页' } // 添加 meta title
  },
  {
    path: '/edit/:object_name', // 使用动态路由参数
    name: 'EditReport',
    component: EditReport,
    props: true, // 将路由参数作为 props 传递给组件
    meta: { title: '编辑报告' } // 添加 meta title
  },
  {
    path: '/test', // 添加 test 页面的路由
    name: 'Test',
    component: Test,
    meta: { title: 'LLM审核答疑测试' } // 添加 meta title
  },
  {
    path: '/upload', // 添加 upload 页面的路由
    name: 'Upload',
    component: Upload,
    meta: { title: '上传录音' } // 添加 meta title
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

// 全局后置守卫，用于更新页面标题
router.afterEach((to, from) => {
  // 如果目标路由有 meta.title，则更新 document.title
  if (to.meta && to.meta.title) {
    document.title = to.meta.title;
  } else {
    // 可选：如果没有设置标题，可以设置一个默认标题
    document.title = 'LLM审核答疑测试'; // 或者其他默认标题
  }
});