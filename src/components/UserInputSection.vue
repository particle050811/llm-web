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
  modelValue: String // Corresponds to the 'msg' ref in App.vue
});

const emit = defineEmits(['update:modelValue']);

const msgShow = ref(true); // Local state for visibility

// Method to update the msg value via emit
const setMsg = (value) => {
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