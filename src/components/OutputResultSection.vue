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
        <!-- 如果 llm-put 需要双向绑定，使用 :modelValue 和 @update:modelValue -->
        <!-- 假设 llm-put 主要用于展示，这里作为 prop 传递内容 -->
        <!-- 监听 update:modelValue 事件来更新 result.content -->
        <llm-put :modelValue="result.content" @update:modelValue="updateContent(result, $event)" />
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
import llmPut from './llm-put.vue'; // 假设 llm-put 位于同一目录
import { marked } from 'marked';

const props = defineProps({
  output: Array // 来自 App.vue 的结果对象数组
});

const renderMarkdown = (content) => {
  return marked(content || '');
};

// 更新 result 内容的方法
const updateContent = (result, newValue) => {
  // 尝试直接修改 props 中的对象属性。注意：这通常不推荐，但可能是最简单的临时解决方案。
  // 如果需要更规范的数据流管理，应考虑向上触发事件。
  result.content = newValue;
  // 如果需要更新字数等依赖 content 的计算值，也应在此处处理或触发相应更新
  // 例如：result.charCount = newValue.length;
};
</script>

<style scoped>
.reasoning-content {
  /* 如有需要，可为推理内容添加特定样式 */
  white-space: pre-wrap; /* Preserve whitespace and wrap text */
  word-wrap: break-word;
}
/* 如有必要，添加其他样式 */
</style>