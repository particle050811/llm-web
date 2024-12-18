<template>
  <el-row justify="center">
    <el-col :span="8" justify="center">
      <llm-put v-model="prompt"/>
    </el-col>
    <el-col :span="6" justify="center" style="margin-left: 20px;">
      <llm-put v-model="msg" />
    </el-col>
  </el-row>
  <el-row justify="center">
    <el-checkbox-group v-model="modelList">
      <el-checkbox
        v-for="model in models"
        :key="model.value"
        :label="model.label"
        :value="model.value"
      >
      </el-checkbox>
    </el-checkbox-group>
    <el-button style="margin-left: 20px;" @click="execute">执行</el-button>
  </el-row>
  <el-row justify="center" v-if="output.length > 0">
    <el-col :span="7" v-for="(result, index) in output" :key="index" style="margin-left: 20px;">
      <div>
        <strong>{{ result.model }}:</strong>
        <llm-put v-model="output[index].response" />
      </div>
    </el-col>
  </el-row>
</template>

<script setup>
  import { ref, onMounted } from 'vue';
  import llmPut from './components/llm-put.vue';
  import { check_prompt, user_prompt } from './assets/prompts';
  // 导入 axios
  import axios from 'axios';

  const prompt = ref(check_prompt);
  const msg = ref(user_prompt);
  const output = ref([]);
  const modelList = ref([]); // 选中的模型列表
  const models = ref([]);    // 模型列表

  // 获取模型列表的函数
  const fetchModels = async () => {
    try {
      const response = await axios.get('http://localhost:5000/fetchModels');
      // 将字符串数组转换为对象数组
      models.value = response.data.map(model => ({
        label: model, // 使用模型名称作为 label
        value: model  // 使用模型名称作为 value
      }));
      console.log('Model=', models.value);
    } catch (error) {
      console.error('Error fetching model list:', error);
    }
  };

  // 在组件挂载时获取模型列表
  onMounted(() => {
    fetchModels();
  });

  const execute = async () => {
  try {
    const selectedModels = modelList.value;

    // 自定义 Base64 编码函数，支持 UTF-8 字符
    const encodeBase64 = (str) => {
      const encoder = new TextEncoder();
      const data = encoder.encode(str);
      return btoa(String.fromCharCode.apply(null, data));
    };

    // 只编码一次 prompt 和 msg
    const encodedPrompt = encodeBase64(prompt.value);
    const encodedMsg = encodeBase64(msg.value);

    // 创建请求数组
    const requests = selectedModels.map(async (model) => {
      const response = await axios.post('http://localhost:5000/query', {
        model: model,
        prompt: encodedPrompt, // 复用编码后的 prompt
        msg: encodedMsg // 复用编码后的 msg
      });

      // 确保 response.data 是字符串类型
      let responseData = response.data;
      if (typeof responseData !== 'string') {
        responseData = JSON.stringify(responseData); // 将对象转换为字符串
      }

      console.log(responseData); // 打印响应数据
      return { model: model, response: responseData };
    });

    // 等待所有请求完成
    const results = await Promise.all(requests);
    output.value = results;
  } catch (error) {
    console.error('Error sending POST request:', error);
    output.value = [{ model: '错误', response: '请求失败，请重试' }];
  }
};
</script>