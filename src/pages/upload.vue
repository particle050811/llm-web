<template>
  <div class="upload-container">
    <div class="file-upload-row">
      <input
        type="file"
        id="audioInput"
        accept="audio/*"
        @change="handleFileChange"
        class="file-input"
      />
    </div>
    <div class="model-select-row">
      <select v-model="selectedModel" class="model-select">
        <option value="gemini-2.5-pro">gemini-2.5-pro</option>
        <option value="gemini-2.0-flash-thinking">gemini-2.0-flash-thinking</option>
        <option value="gemini-2.0-flash">gemini-2.0-flash</option>
      </select>
    </div>
    <div class="upload-btn-row">
      <button @click="uploadAudio" class="upload-btn">上传并识别音频</button>
    </div>
    <p v-if="uploadStatus" class="status-text">{{ uploadStatus }}</p>
    <div class="chat-container">
      <SentenceBubble
        v-for="(sentence, index) in parsedSentences"
        :key="index"
        :rawText="sentence"
        @update:rawText="(newVal) => updateSentence(index, newVal)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import CryptoJS from 'crypto-js';
import SentenceBubble from '@/components/SentenceBubble.vue';

const selectedFile = ref(null);
const selectedModel = ref('gemini-2.0-flash-thinking');
const uploadStatus = ref('');
const transcriptionResult = ref('');
const isLoadingTranscription = ref(false);
const parsedSentences = ref([]);

watch(transcriptionResult, (newVal) => {
  parsedSentences.value = newVal ? newVal.split('\n') : [];
});

const updateSentence = (index, newVal) => {
  parsedSentences.value[index] = newVal;
  transcriptionResult.value = parsedSentences.value.join('\n');
};

const calculateFileHash = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const wordArray = CryptoJS.lib.WordArray.create(e.target.result);
      const md5 = CryptoJS.MD5(wordArray).toString();
      resolve(md5);
    };
    reader.readAsArrayBuffer(file);
  });
};

const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0];
};

const uploadAudio = async () => {
  if (!selectedFile.value) {
    uploadStatus.value = '请先选择音频文件';
    return;
  }

  try {
    uploadStatus.value = '正在计算文件校验...';
    const fileHash = await calculateFileHash(selectedFile.value);

    uploadStatus.value = '正在检查服务器...';
    const urlResponse = await fetch(`/api/generate-audio-url?contentType=${encodeURIComponent(selectedFile.value.type)}&fileHash=${fileHash}`);
    if (!urlResponse.ok) {
      throw new Error(`获取上传链接失败，状态码: ${urlResponse.status}`);
    }
    const urlData = await urlResponse.json();

    if (urlData.status === 'exists') {
      uploadStatus.value = '文件已存在(服务器已有相同文件)，开始识别...';
      await transcribeAudio(urlData.object_name, selectedModel.value);
    } else if (urlData.status === 'new') {
      uploadStatus.value = '准备上传文件...';
      const formData = new FormData();
      formData.append('file', selectedFile.value);
      formData.append('object_name', urlData.object_name);

      uploadStatus.value = '正在上传文件...';
      const uploadResponse = await fetch('/api/upload-audio', {
        method: 'POST',
        body: formData
      });

      if (uploadResponse.ok) {
        const uploadResult = await uploadResponse.json();
        uploadStatus.value = '文件上传成功! 开始识别...';
        await transcribeAudio(uploadResult.object_name, selectedModel.value);
      } else {
        const errorText = await uploadResponse.text();
        throw new Error(`上传失败，状态码: ${uploadResponse.status}, 错误: ${errorText}`);
      }
    } else {
      throw new Error(`未知的服务器响应状态: ${urlData.status}`);
    }
  } catch (error) {
    console.error('上传或识别错误:', error);
    uploadStatus.value = '处理失败: ' + error.message;
    isLoadingTranscription.value = false;
  }
};

const transcribeAudio = async (objectName, model) => {
  isLoadingTranscription.value = true;
  transcriptionResult.value = '';
  uploadStatus.value = '正在识别中...';

  try {
    const response = await fetch('/api/transcribe-audio', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        object_name: objectName,
        model: model
      })
    });

    if (!response.ok) {
      throw new Error(`识别请求失败: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value);
        transcriptionResult.value += chunk;
      }
    }

    uploadStatus.value = '识别完成!';
  } catch (error) {
    console.error('识别错误:', error);
    uploadStatus.value = '识别失败: ' + error.message;
    transcriptionResult.value = '识别出错';
  } finally {
    isLoadingTranscription.value = false;
  }
};
</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 5px;
}

.file-upload-row, .model-select-row, .upload-btn-row {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.model-select {
  width: 220px;
  font-size: 13px;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.file-input {
  flex: 1;
  max-width: 220px;
  font-size: 13px;
}

.upload-btn {
  padding: 4px 8px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
  min-width: 70px;
  height: 28px;
  line-height: 1;
}

.upload-btn:hover {
  background-color: #3aa876;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-text {
  margin: 10px 0;
  font-size: 14px;
  color: #666;
}

.chat-container {
  margin-top: 0;
  border-radius: 8px;
  background-color: #fff;
  overflow-y: auto;
}
</style>