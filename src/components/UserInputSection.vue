<template>
  <el-row align="middle">
    <el-col :xs="8" :lg="6" justify="center">
      <strong>用户输入</strong>
    </el-col>
    <el-col :span="4" justify="center">
      <el-switch
        v-model="msgShow"
        :active-action-icon="View"
        :inactive-action-icon="Hide"
      />
    </el-col>
    <el-col :span="24" justify="center" v-if="msgShow" style="margin-bottom: 5px;">
      <el-row>
        <el-col :span="6"><el-button @click="setMsg(exam1)">考核表1</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(exam2)">考核表2</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(exam3)">考核表3</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(exam4)">考核表4</el-button></el-col>
      </el-row>
    </el-col>
    <el-col :span="24" justify="center" v-if="msgShow">
      <el-row>
        <el-col :span="6"><el-button @click="setMsg(question1)">提问1</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(question2)">提问2</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(question3)">提问3</el-button></el-col>
        <el-col :span="6"><el-button @click="setMsg(question4)">提问4</el-button></el-col>
      </el-row>
    </el-col>
  </el-row>
  <llm-put :modelValue="modelValue" @update:modelValue="emitUpdate" v-if="msgShow"/>
</template>

<script setup>
import { ref } from 'vue';
import llmPut from './llm-put.vue';
import {
  exam1,
  exam2,
  exam3,
  exam4,
  question1,
  question2,
  question3,
  question4,
} from '../assets/prompts';
import { Hide, View } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: String // 对应于 App.vue 中的 'msg' 响应式引用
});

const emit = defineEmits(['update:modelValue']);

const msgShow = ref(true); // 控制可见性的本地状态

// 通过 emit 更新 msg 值的方法
const setMsg = (value) => {
  emit('update:modelValue', value);
};

// 处理来自 llm-put 的更新并向上传递的方法
const emitUpdate = (value) => {
  emit('update:modelValue', value);
};

// 将导入的提示词暴露给模板使用
// 在模板事件处理器中直接使用导入的变量更为合适
// 这里无需使用 defineExpose 来访问这些变量
</script>