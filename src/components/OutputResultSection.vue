<template>
  <el-row justify="center" v-if="output && output.length > 0" :gutter="20">
    <el-col :xs="24" :sm="12" :md="12" :lg="8" v-for="(result, index) in output" :key="index">
      <div>
        <strong>{{ result.model }}:</strong>
        <el-collapse v-if="result.reasoning && result.reasoning.length > 0">
          <el-collapse-item>
            <template #title>
              <strong>深度思考</strong>
            </template>
            <div class="reasoning-content" v-html="renderMarkdown(result.reasoning)"></div>
          </el-collapse-item>
        </el-collapse>
        <!-- Use :modelValue and @update:modelValue for llm-put if it needs two-way binding -->
        <!-- Assuming llm-put is primarily for display here, pass content as a prop -->
        <llm-put :modelValue="result.content" readonly /> 
        <el-row>
          <el-col :span="8">
            耗时：<span v-if="result.duration !== null">{{ result.duration }} 秒</span>
            <span v-else>计算中...</span>
          </el-col>
          <el-col :span="8">
            字数：<span v-if="result.charCount !== undefined">{{ result.charCount }} 字</span>
            <span v-else>计算中...</span>
          </el-col>
          <el-col :span="8">
            速率：<span v-if="result.duration !== null && result.charCount !== undefined && result.duration > 0">
              {{ (result.charCount / result.duration).toFixed(2) }} 字/秒
            </span>
            <span v-else-if="result.duration === 0 && result.charCount > 0">无限</span>
            <span v-else>计算中...</span>
          </el-col>
        </el-row>
      </div>
    </el-col>
  </el-row>
</template>

<script setup>
import { defineProps } from 'vue';
import llmPut from './llm-put.vue'; // Assuming llm-put is in the same directory
import { marked } from 'marked';

const props = defineProps({
  output: Array // Array of result objects from App.vue
});

const renderMarkdown = (content) => {
  return marked(content || '');
};
</script>

<style scoped>
.reasoning-content {
  /* Add any specific styling for reasoning content if needed */
  white-space: pre-wrap; /* Preserve whitespace and wrap text */
  word-wrap: break-word;
}
/* Add other styles if necessary */
</style>