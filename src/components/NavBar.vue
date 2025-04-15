<template>
  <nav class="navbar">
    <router-link to="/" class="nav-link">主页</router-link>
    <router-link to="/test" class="nav-link">LLM测试</router-link>
    <router-link to="/upload" class="nav-link">上传录音</router-link>
  </nav>
</template>

<script>
export default {
  name: 'NavBar'
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: center;
  gap: 1rem; /* 使用 gap 属性设置间距 */
  padding: 1rem;
  background-color: #f0f0f0;
  border-bottom: 1px solid #ddd;
  font-size: 18px;
}

.nav-link {
  text-decoration: none;
  color: #333;
}

.nav-link:hover {
  color: #42b983;
}

.router-link-exact-active {
  font-weight: bold;
  color: #42b983;
}
</style>