<template>
  <div style="margin: 10px;">
    <el-row justify="center" :gutter="20">
      <!-- System Prompt Section -->
      <el-col :xs="24" :sm="14" :md="14" :lg="8" justify="center" style="display: flex; flex-direction: column;">
        <SystemPromptSection v-model="prompt" />
      </el-col>

      <!-- User Input Section -->
      <el-col :xs="24" :sm="10" :md="10" :lg="6" justify="center">
        <UserInputSection v-model="msg" />
      </el-col>
    </el-row>

    <!-- Model Execution Section -->
    <ModelExecutionSection
      :models="models"
      v-model="modelList"
      v-model:isSixTests="isSixTests"
      @execute="execute"
    />

    <!-- Output Result Section -->
    <OutputResultSection :output="output" />

    <br><br><br><br><br>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { check_prompt, user_prompt } from '../assets/prompts'; // Keep defaults

// Import the new components
import SystemPromptSection from '../components/SystemPromptSection.vue';
import UserInputSection from '../components/UserInputSection.vue';
import ModelExecutionSection from '../components/ModelExecutionSection.vue';
import OutputResultSection from '../components/OutputResultSection.vue';

// State remains in the parent component
const prompt = ref(localStorage.getItem('prompt') || check_prompt);
const msg = ref(localStorage.getItem('msg') || user_prompt);
const output = ref([]);
const modelList = ref([]); // Selected models
const models = ref([]);    // Available models
const isSixTests = ref(false); // Six tests mode flag
const testCount = ref(0); // Current test count (used internally by execute)

const host = window.location.hostname;

// Watch for changes and save to localStorage (remains the same)
watch(prompt, (newVal) => {
  localStorage.setItem('prompt', newVal);
});

watch(msg, (newVal) => {
  localStorage.setItem('msg', newVal);
});

// Fetch models function (remains the same)
const fetchModels = async () => {
  try {
    const url = `http://${host}:5000/fetchModels`;
    const response = await fetch(url);
    const data = await response.json();
    models.value = data.map(model => ({
      label: model,
      value: model
    }));
    console.log('Models fetched:', models.value);
  } catch (error) {
    console.error('Error fetching model list:', error);
    ElMessage.error('获取模型列表失败'); // Notify user
  }
};

// Execute function (remains largely the same, triggered by child component event)
const execute = async () => {
  if (isSixTests.value && modelList.value.length !== 1) {
    ElMessage.warning('6次测试模式下只能选择一个模型');
    return;
  }

  output.value = []; // Clear previous results
  if (isSixTests.value) {
    testCount.value = 0;
    const promises = Array.from({ length: 6 }, (_, i) => {
      return new Promise(resolve => {
        setTimeout(async () => {
          testCount.value = i + 1; // Keep track for display if needed
          await executeSingleTest(modelList.value[0], i + 1);
          resolve();
        }, i * 400); // Stagger requests
      });
    });
    await Promise.all(promises);
  } else {
    const testPromises = modelList.value.map(model => executeSingleTest(model));
    await Promise.all(testPromises);
  }
};

// Execute single test function (remains the same)
const executeSingleTest = async (modelValue, testNumber) => {
  const outputIndex = output.value.length; // Get index before adding
  const newOutputEntry = {
    model: modelValue + (isSixTests.value ? ` (测试 ${testNumber}/6)` : ''),
    content: '',
    reasoning: '',
    startTime: Date.now(),
    duration: null,
    charCount: 0
  };
  output.value.push(newOutputEntry); // Add new entry placeholder

  try {
    const url = `http://${host}:5000/query_stream`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelValue,
        prompt: prompt.value, // Use the ref directly
        msg: msg.value       // Use the ref directly
      })
    });

    const currentOutput = output.value[outputIndex]; // Reference the correct entry

    if (!response.ok) {
      let errorMsg = '请求失败，请重试';
      try {
        const errorData = await response.json();
        errorMsg = errorData.error || errorMsg;
      } catch (e) {
        try { errorMsg = await response.text(); } catch (err) { /* ignore secondary error */ }
      }
      currentOutput.content = errorMsg;
      currentOutput.charCount = errorMsg.length;
      currentOutput.duration = ((Date.now() - currentOutput.startTime) / 1000).toFixed(2);
      return; // Stop processing for this test
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        const jsonStrings = chunk.split('\n').filter(str => str.trim() !== '');
        for (const jsonStr of jsonStrings) {
          try {
            const delta = JSON.parse(jsonStr);
            if (delta.content) {
              currentOutput.content += delta.content;
            }
            if (delta.reasoning_content) {
              currentOutput.reasoning += delta.reasoning_content;
            }
            currentOutput.charCount = (currentOutput.content?.length || 0) + (currentOutput.reasoning?.length || 0);
          } catch (jsonError) {
            console.error('Error parsing JSON stream chunk:', jsonError, jsonStr);
            // Append raw chunk if parsing fails, might be plain text error
            currentOutput.content += jsonStr;
             currentOutput.charCount = (currentOutput.content?.length || 0) + (currentOutput.reasoning?.length || 0);
          }
        }
      }
    }
    currentOutput.duration = ((Date.now() - currentOutput.startTime) / 1000).toFixed(2);

  } catch (error) {
    console.error('Error during fetch/stream processing:', error);
    const currentOutput = output.value[outputIndex]; // Ensure reference
    currentOutput.content = error.message || '请求处理时发生错误';
    currentOutput.charCount = currentOutput.content.length;
    currentOutput.duration = ((Date.now() - currentOutput.startTime) / 1000).toFixed(2);
  }
};

// Fetch models on mount (remains the same)
onMounted(() => {
  fetchModels();
});

// Removed: promptShow, msgShow refs (managed within child components)
// Removed: Hide, View imports (managed within child components)
// Removed: specific prompt imports like audit1, exam1 etc. (managed within child components)
// Removed: marked, renderMarkdown (managed within OutputResultSection)
// Removed: isLargeScreen function (no longer used)
</script>

<style>
/* Keep global styles or move them if appropriate */
/* .button-container { Style moved to ModelExecutionSection.vue */
  /* display: flex; */
  /* flex-direction: column; */
  /* align-items: center; */
  /* gap: 10px; */
/* } */
/* .reasoning-content { Style moved to OutputResultSection.vue */
 /* white-space: pre-wrap; */
 /* word-wrap: break-word; */
/* } */
</style>