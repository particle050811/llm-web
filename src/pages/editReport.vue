<template>
  <div class="edit-report-container">
    <h1>编辑举报信息</h1>
    <p v-if="object_name">正在编辑举报: <strong>{{ object_name }}</strong></p>
    <p v-else>未指定举报信息。</p>
    <!-- 在这里添加编辑表单等内容 -->
    <router-link to="/">返回列表</router-link>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

// 接收来自路由的 object_name 参数
const props = defineProps({
  object_name: {
    type: String,
    required: true,
  },
});

console.log('编辑页面接收到的 object_name:', props.object_name);

// 在这里可以添加加载和保存举报详情的逻辑
</script>

<style scoped>
.edit-report-container {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #fff;
  text-align: center;
}

h1 {
  color: #333;
  margin-bottom: 20px;
}

p {
  font-size: 16px;
  margin-bottom: 20px;
}

strong {
  color: #007bff;
}

a {
  display: inline-block;
  margin-top: 20px;
  padding: 8px 15px;
  background-color: #6c757d;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
}

a:hover {
  background-color: #5a6268;
}
</style>