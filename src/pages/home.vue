<template>
  <div class="home-container">
    <h1>举报列表</h1>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!loading && !error" class="report-list">
      <div
        v-for="report in reports"
        :key="report.object_name"
        class="report-card"
        @click="goToEditPage(report.object_name)"
      >
        <p><strong>学校:</strong> {{ report.school || 'N/A' }}</p>
        <p><strong>电话:</strong> {{ report.phone || 'N/A' }}</p>
        <p><strong>时间:</strong> {{ report.time || 'N/A' }}</p>
        <small>ID: {{ report.object_name }}</small>
      </div>
      <div v-if="reports.length === 0 && !loading" class="no-reports">
        暂无举报信息。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const reports = ref([]);
const loading = ref(true);
const error = ref(null);
const router = useRouter();

const fetchReports = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch('/api/reports'); // 假设后端接口路径为 /api/reports
    if (!response.ok) {
      throw new Error(`获取举报列表失败: ${response.status}`);
    }
    const data = await response.json();
    reports.value = data; // 假设返回的数据是报告数组
    console.log('获取到的举报列表:', data);
  } catch (err) {
    console.error('获取举报列表时出错:', err);
    error.value = err.message || '无法加载举报列表。';
  } finally {
    loading.value = false;
  }
};

const goToEditPage = (objectName) => {
  if (objectName) {
    router.push({ name: 'EditReport', params: { object_name: objectName } });
  } else {
    console.warn('无法跳转，缺少 object_name');
  }
};

onMounted(() => {
  fetchReports();
});
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  font-family: sans-serif;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.loading, .error, .no-reports {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.error {
  color: red;
}

.report-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.report-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.report-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.report-card p {
  margin: 5px 0;
  font-size: 14px;
  color: #555;
}

.report-card p strong {
  color: #333;
}

.report-card small {
    display: block;
    margin-top: 10px;
    font-size: 12px;
    color: #999;
    word-break: break-all; /* 防止长 ID 溢出 */
}
</style>