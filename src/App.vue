<template>
  <el-row justify="center" :gutter="20">
    <el-col :xs="24" :lg="8" justify="center" style="display: flex; flex-direction: column;">
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
            <el-col :span="6"><el-button @click="prompt = audit1">审核1</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = audit2">审核2</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = audit3">审核3</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = audit4">审核4</el-button></el-col>
          </el-row>
          <el-row>
            <el-col :span="6"><el-button @click="prompt = answer1">答疑1</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = answer2">答疑2</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = answer3">答疑3</el-button></el-col>
            <el-col :span="6"><el-button @click="prompt = answer4">答疑4</el-button></el-col>
          </el-row>
        </el-col>
      </el-row>
      <llm-put v-model="prompt" v-if="promptShow" style="margin-top: auto;"/>
    </el-col>
    <el-col :xs="24" :lg="6" justify="center">
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
            <el-col :span="6"><el-button @click="msg = exam1">考核表1</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = exam2">考核表2</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = exam3">考核表3</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = exam4">考核表4</el-button></el-col>
          </el-row>
        </el-col>
        <el-col :span="24" justify="center" v-if="msgShow">
          <el-row>
            <el-col :span="6"><el-button @click="msg = question1">提问1</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = question2">提问2</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = question3">提问3</el-button></el-col>
            <el-col :span="6"><el-button @click="msg = question4">提问4</el-button></el-col>
          </el-row>
        </el-col>
      </el-row>
      <llm-put v-model="msg" v-if="msgShow"/>
    </el-col>
  </el-row>
  <el-row justify="center">
    <el-col :xs="20" :lg="10">
      <el-checkbox-group v-model="modelList">
        <el-row>
          <el-col :xs="12" :lg="6" v-for="(model, index) in models" :key="model.value">
            <el-checkbox :label="model.label" :value="model.value">
            </el-checkbox>
          </el-col>
        </el-row>
      </el-checkbox-group>
    </el-col>
    <el-col :xs="4" :lg="1" class="button-container">
      <el-button @click="execute">执行</el-button>
      <el-switch
        v-model="isSixTests"
        inline-prompt
        active-text="6次测试"
        inactive-text="单次测试"
      />
    </el-col>
  </el-row>
  <el-row justify="center" v-if="output.length > 0" :gutter="20">
    <el-col :xs="24" :lg="8" v-for="(result, index) in output" :key="index">
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
import { 
  check_prompt, 
  user_prompt,
  audit1,
  audit2,
  audit3,
  audit4,
  answer1,
  answer2,
  answer3,
  answer4,
  exam1,
  exam2,
  exam3,
  exam4,
  question1,
  question2,
  question3,
  question4
} from './assets/prompts';
import { Hide, View } from '@element-plus/icons-vue'
import { watch } from 'vue';
import { ElMessage } from 'element-plus';

const promptShow = ref(false)
const msgShow = ref(true)

// Initialize from localStorage or use defaults
const prompt = ref(localStorage.getItem('prompt') || check_prompt);
const msg = ref(localStorage.getItem('msg') || user_prompt);

// Watch for changes and save to localStorage
watch(prompt, (newVal) => {
  localStorage.setItem('prompt', newVal);
});

watch(msg, (newVal) => {
  localStorage.setItem('msg', newVal);
});
const output = ref([]);
const modelList = ref([]); // 选中的模型列表
const models = ref([]);    // 模型列表
const isSixTests = ref(false); // 是否处于6次测试模式
const testCount = ref(0); // 当前测试次数

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

// 定义一个函数来检查是否为 lg 或更大的屏幕
const isLargeScreen = () => {
  return window.innerWidth >= 1200; // Element Plus 的 lg Breakpoint 是 1200px
};

// 在组件挂载时进行初始化设置
onMounted(() => {
  fetchModels();
  promptShow.value = isLargeScreen(); // 根据初始屏幕大小设置 promptShow
});

const execute = async () => {
  if (isSixTests.value && modelList.value.length !== 1) {
    ElMessage.warning('6次测试模式下只能选择一个模型');
    return;
  }
  
  output.value = []; // 清空之前的测试结果
  if (isSixTests.value) {
    testCount.value = 0;
    // 创建6个并发执行的promise，每个延迟n-1秒启动
    const promises = Array.from({length: 6}, (_, i) => {
      return new Promise(resolve => {
        setTimeout(async () => {
          testCount.value = i + 1;
          await executeSingleTest(modelList.value[0], i + 1);
          resolve();
        }, i * 400);
      });
    });
    await Promise.all(promises);
    return;
  }
  
  // 并发执行所有选中模型的测试
  const testPromises = modelList.value.map(async (model) => {
    await executeSingleTest(model);
  });
  
  await Promise.all(testPromises);
}

const executeSingleTest = async (modelValue, testNumber) => {
  try {
    // 为当前测试创建新的输出对象
    const newOutput = [{
      model: modelValue + (isSixTests.value ? ` (测试 ${testNumber}/6)` : ''),
      response: '',
      startTime: Date.now(),
      duration: null
    }];
    
    // 将新输出添加到现有输出数组中
    const outputIndex = output.value.length;
    output.value = [...output.value, ...newOutput];

    // 自定义 Base64 编码函数，支持 UTF-8 字符
    const encodeBase64 = (str) => {
      const encoder = new TextEncoder();
      const data = encoder.encode(str);
      return btoa(String.fromCharCode.apply(null, data));
    };

    // 只编码一次 prompt 和 msg
    const encodedPrompt = encodeBase64(prompt.value);
    const encodedMsg = encodeBase64(msg.value);

    // 执行单个测试
    const model = modelValue;
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
        let errorMsg = '请求失败，请重试';
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          try {
            errorMsg = await response.text();
          } catch (err) {
            console.error("Failed to parse error response as text:", err);
          }
        }
        output.value[outputIndex].duration = ((Date.now() - output.value[outputIndex].startTime) / 1000).toFixed(2);
        output.value[outputIndex].response = errorMsg;
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          output.value[outputIndex].response += chunk;
        }
      }
      
      output.value[outputIndex].duration = ((Date.now() - output.value[outputIndex].startTime) / 1000).toFixed(2);
    } catch (error) {
      console.error('Error sending POST request:', error);
      output.value[outputIndex].response = error.message || '请求失败，请重试';
      output.value[outputIndex].duration = ((Date.now() - output.value[outputIndex].startTime) / 1000).toFixed(2);
    }
  } catch (error) {
    console.error('Error sending POST request:', error);
    output.value = [{ model: '错误', response: '请求失败，请重试', startTime: Date.now(), duration: 0 }];
  }
}
</script>
