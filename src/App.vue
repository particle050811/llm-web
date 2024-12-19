<template>
  <el-row justify="center">
    <el-col :span="8" justify="center">
      <strong>系统预设提示词</strong>
      <llm-put v-model="prompt" />
    </el-col>
    <el-col :span="6" justify="center" style="margin-left: 20px;">
      <strong>用户输入</strong>
      <llm-put v-model="msg" />
    </el-col>
  </el-row>
  <el-row justify="center">
    <el-col :span="10">
      <el-checkbox-group v-model="modelList">
        <el-row>
          <el-col :span="6" v-for="(model, index) in models" :key="model.value">
            <el-checkbox :label="model.label" :value="model.value">
            </el-checkbox>
          </el-col>
        </el-row>
      </el-checkbox-group>
    </el-col>
    <el-col :span="1" class="button-container">
      <el-button style="margin-left: 20px;" @click="execute">执行</el-button>
    </el-col>
  </el-row>
  <el-row justify="center" v-if="output.length > 0">
    <el-col :span="7" v-for="(result, index) in output" :key="index" style="margin-left: 20px;">
      <div>
        <strong>{{ result.model }}:</strong>
        <llm-put v-model="output[index].response" />
        <p v-if="result.duration !== null">耗时: {{ result.duration }} 秒</p>
      </div>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import llmPut from './components/llm-put.vue';
import { check_prompt, user_prompt } from './assets/prompts';

const prompt = ref(check_prompt);
const msg = ref(user_prompt);
const output = ref([]);
const modelList = ref([]); // 选中的模型列表
const models = ref([]);    // 模型列表

const host = window.location.hostname;

// 获取模型列表的函数
const fetchModels = async () => {
  try {
    const url = `http://${host}:5000/fetchModels`;
    const response = await fetch(url);
    const data = await response.json();
    // 将字符串数组转换为对象数组
    models.value = data.map(model => ({
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

    // 清空 output 数组，并为每个选定的模型创建一个初始输出对象，包含开始时间
    // 关键修改：使用 map 遍历 models，并根据 modelList 进行过滤和排序
    output.value = models.value
      .filter(model => selectedModels.includes(model.value))
      .map(model => ({
        model: model.value,
        response: '',
        startTime: Date.now(),
        duration: null
      }));

    // 自定义 Base64 编码函数，支持 UTF-8 字符
    const encodeBase64 = (str) => {
      const encoder = new TextEncoder();
      const data = encoder.encode(str);
      return btoa(String.fromCharCode.apply(null, data));
    };

    // 只编码一次 prompt 和 msg
    const encodedPrompt = encodeBase64(prompt.value);
    const encodedMsg = encodeBase64(msg.value);

    // 创建一个数组来保存每个请求的 Promise 及其索引
    // 关键修改：使用 map 遍历 output.value，并使用 index 作为请求的索引
    const promisesWithIndex = output.value.map(async (outputModel, index) => {
      const model = outputModel.model;
      try {
        const url = `http://${host}:5000/query_stream`;
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: model,
            prompt: encodedPrompt,
            msg: encodedMsg
          })
        });

        if (!response.ok) {
          // 尝试解析响应为 JSON
          let errorMsg = '请求失败，请重试'; // 默认错误信息
          try {
            const errorData = await response.json();
            errorMsg = errorData.error || errorMsg; // 如果有 error 字段，则使用它
          } catch (e) {
            // 如果解析 JSON 失败，可能响应不是 JSON 格式，使用 text() 方法
            try {
              errorMsg = await response.text();
            } catch (err) {
              console.error("Failed to parse error response as text:", err);
            }
          }
          // 在请求结束后计算持续时间
          output.value[index].duration = ((Date.now() - output.value[index].startTime) / 1000).toFixed(2);
          return { index, error: errorMsg };
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            // 根据索引找到 output 数组中对应的位置，并将数据块追加到 response 字段
            output.value[index].response += chunk;
          }
        }
        // 在请求结束后计算持续时间
        output.value[index].duration = ((Date.now() - output.value[index].startTime) / 1000).toFixed(2);
        return { index, response: output.value[index].response }; // 标记请求成功
      } catch (error) {
        // 在请求结束后计算持续时间
        output.value[index].duration = ((Date.now() - output.value[index].startTime) / 1000).toFixed(2);
        return { index, error: error.message || '请求失败，请重试' };
      }
    });

    // 使用 Promise.all 等待所有请求完成
    const results = await Promise.all(promisesWithIndex);

    // 处理结果，根据索引排序（虽然在流式处理中已经按索引更新，这里是最终的保障）
    results.forEach(result => {
      if (result.error) {
        output.value[result.index].response = result.error;
      } else {
        //这里实际上可以不用做任何操作，因为在上面的流处理中已经更新了 output.value[result.index].response
        //为了保持代码清晰和完整性，你可以选择保留这部分代码或者将其删除
        // output.value[result.index].response = result.response;
      }
    });
  } catch (error) {
    console.error('Error sending POST request:', error);
    output.value = [{ model: '错误', response: '请求失败，请重试', startTime: Date.now(), duration: 0 }];
  }
};
</script>

<style>
  /* 强制将页面宽度设置为 1024px */
  body {
    width: 1670px;
    margin: 0 auto; /* 居中显示 */
  }
</style>