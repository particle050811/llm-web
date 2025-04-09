<template>
  <el-row align="middle">
    <el-col :xs="8" :lg="6" justify="center">
      <strong>系统预设提示词</strong>
    </el-col>
    <el-col :span="4" justify="center">
      <el-switch
        v-model="promptShow"
        :active-action-icon="View"
        :inactive-action-icon="Hide"
      />
    </el-col>
    <el-col :span="24" justify="center" v-if="promptShow" style="margin-bottom: 5px;">
      <el-row>
        <el-col :span="6"><el-button @click="setPrompt(audit1)">基础审核</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(audit2)">推理审核</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(audit3)">审核3</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(audit4)">审核4</el-button></el-col>
      </el-row>
      <el-row>
        <el-col :span="6"><el-button @click="setPrompt(answer1)">答疑</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(answer2)">答疑2</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(answer3)">答疑3</el-button></el-col>
        <el-col :span="6"><el-button @click="setPrompt(answer4)">答疑4</el-button></el-col>
      </el-row>
    </el-col>
  </el-row>
  <llm-put :modelValue="modelValue" @update:modelValue="emitUpdate" v-if="promptShow" style="margin-top: auto;"/>
</template>

<script setup>
import { ref, watch } from 'vue';
import llmPut from './llm-put.vue';
import {
  audit1,
  audit2,
  audit3,
  audit4,
  answer1,
  answer2,
  answer3,
  answer4,
} from '../assets/prompts';
import { Hide, View } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: String // 对应于 App.vue 中的 'prompt' 响应式引用
});

const emit = defineEmits(['update:modelValue']);

const promptShow = ref(true); // 控制显示切换的本地状态

// 通过 emit 更新 prompt 值的方法
const setPrompt = (value) => {
  emit('update:modelValue', value);
};

// 处理来自 llm-put 的更新并向上传递的方法
const emitUpdate = (value) => {
  emit('update:modelValue', value);
};

// 将导入的提示词暴露给模板使用
// 在模板事件处理器中直接使用导入的变量更为合适
// 这里不需要使用 defineExpose 来访问这些变量
</script>