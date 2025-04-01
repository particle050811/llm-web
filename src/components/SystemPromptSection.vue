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
  modelValue: String // Corresponds to the 'prompt' ref in App.vue
});

const emit = defineEmits(['update:modelValue']);

const promptShow = ref(true); // Keep local state for visibility toggle

// Method to update the prompt value via emit
const setPrompt = (value) => {
  emit('update:modelValue', value);
};

// Method to handle updates from llm-put and emit them upwards
const emitUpdate = (value) => {
  emit('update:modelValue', value);
};

// Expose imported prompts to the template
// It's better to directly use imported variables in the template event handlers
// defineExpose is not needed here for accessing these variables in the template.
</script>