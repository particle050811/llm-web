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
    <audio v-if="showAudioPlayer" ref="mainAudio" :src="audioFileUrl" controls style="width:100%; margin:10px 0;"></audio>
    <div class="chat-container">
      <SentenceBubble
        v-for="(sentence, index) in parsedSentences"
        :key="index"
        :rawText="sentence"
        :audioUrl="audioFileUrl"
        @update:rawText="(newVal) => updateSentence(index, newVal)"
      />
    </div>
    <ReportInfo
      v-if="showReportInfo"
      v-model:school="reportSchool"
      v-model:method="reportMethod"
      v-model:phone="reportPhone"
      v-model:time="reportTime"
    />
    <div class="submit-btn-row" style="margin-top: 20px;" v-if="showSubmitButton">
      <button @click="submitReportData" :disabled="isSubmitButtonDisabled" class="submit-btn">
        {{ isSubmitButtonDisabled ? '提交中...' : '提交举报信息' }}
      </button>
    </div>
  </div>
  <br><br><br><br><br>
</template>

<script setup>
import { ref, watch, provide, computed } from 'vue'; // Import computed
import CryptoJS from 'crypto-js';
import SentenceBubble from '@/components/SentenceBubble.vue';
import ReportInfo from '@/components/ReportInfo.vue';
const mainAudio = ref(null);
provide('mainAudio', mainAudio);

const showAudioPlayer = ref(false);

const selectedFile = ref(null);
const originalFileName = ref('');
const savedModel = localStorage.getItem('selectedModel');
const selectedModel = ref(savedModel || 'gemini-2.0-flash-thinking');

watch(selectedModel, (newVal) => {
  localStorage.setItem('selectedModel', newVal);
});
const uploadStatus = ref('');
const transcriptionResult = ref('');
const isLoadingTranscription = ref(false);
const parsedSentences = ref([]); // 还原为简单字符串数组
const audioFileUrl = ref(''); // 用于存储Blob URL
const showReportInfo = ref(false);
const currentObjectName = ref(''); // 新增：存储当前文件的 object_name
const isSubmitButtonDisabled = ref(false); // 新增：控制提交按钮的禁用状态
const showSubmitButton = ref(false); // 新增：控制提交按钮的显示状态

watch(transcriptionResult, (newVal) => {
  // 按行分割并过滤可能的空行
  parsedSentences.value = newVal ? newVal.split('\n').filter(line => line.trim() !== '') : [];
});

const updateSentence = (index, newVal) => {
  // 更新数组中的特定句子
  if (parsedSentences.value && parsedSentences.value.length > index) {
      parsedSentences.value[index] = newVal;
      // 重新构建完整的转录字符串
      transcriptionResult.value = parsedSentences.value.join('\n');
  }
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
  const file = event.target.files[0];
  selectedFile.value = file;
  originalFileName.value = file.name;

  // 选择新文件时立即显示播放器
  showAudioPlayer.value = true;
  showSubmitButton.value = false;
  showReportInfo.value = false;
  if (file) {
    // 如果存在先前的Blob URL则撤销它，防止内存泄漏
    if (audioFileUrl.value) {
      URL.revokeObjectURL(audioFileUrl.value);
    }
    // 为选中的文件创建新的Blob URL
    audioFileUrl.value = URL.createObjectURL(file);
    // 当选择新文件时重置转录结果
    transcriptionResult.value = '';
    parsedSentences.value = [];
    uploadStatus.value = '文件已选择，等待上传。';
  } else {
    // 如果没有选择文件则清除URL
    if (audioFileUrl.value) {
      URL.revokeObjectURL(audioFileUrl.value);
    }
    audioFileUrl.value = '';
    uploadStatus.value = '请选择一个音频文件。';
  }
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

    // 这里不再需要设置audioFileUrl，它由handleFileChange处理

    if (urlData.status === 'exists') {
      uploadStatus.value = '文件已存在(服务器已有相同文件)，开始识别...';
      // 我们仍然需要object_name用于转录API调用
      currentObjectName.value = urlData.object_name; // 存储 object_name
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
        // 我们仍然需要object_name用于转录API调用
        currentObjectName.value = uploadResult.object_name; // 存储 object_name
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
    
    try {
      await fetchReportInfo(originalFileName.value, transcriptionResult.value);
    } catch (e) {
      console.error('调用举报信息接口失败', e);
    }
  } catch (error) {
    console.error('识别错误:', error);
    uploadStatus.value = '识别失败: ' + error.message;
    transcriptionResult.value = '识别出错';
  } finally {
    isLoadingTranscription.value = false;
  }
};
const reportSchool = ref('');
const reportMethod = ref('');
const reportPhone = ref('');
const reportTime = ref('');

/**
 * 发送识别结果和文件名到服务器，获取举报信息
 */
const fetchReportInfo = async (fileName, transcriptionText) => {
  try {
    const response = await fetch('/api/analyze-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        object_name: fileName,
        transcription_text: transcriptionText
      })
    });
    if (!response.ok) {
      throw new Error('举报信息请求失败: ' + response.status);
    }
    const data = await response.json();
    console.log('举报信息返回数据', data);

    // 格式化时间字符串
    let formattedTime = '';
    if (data.time && /^\d{14}$/.test(data.time)) {
      const t = data.time;
      formattedTime = `${t.slice(0,4)}-${t.slice(4,6)}-${t.slice(6,8)} ${t.slice(8,10)}:${t.slice(10,12)}`;
    } else {
      formattedTime = data.time || '';
    }

    // 避免用空字符串覆盖已有值
    if (data.school) reportSchool.value = data.school;
    if (data.method) reportMethod.value = data.method;
    if (data.phone) reportPhone.value = data.phone;
    if (formattedTime) reportTime.value = formattedTime;
    showReportInfo.value = true;
    showSubmitButton.value = true;
  } catch (error) {
    console.error('获取举报信息失败:', error);
  }
};

// 新增：提交举报信息的函数
const submitReportData = async () => {
  if (!currentObjectName.value) {
    alert('无法提交，缺少文件标识 (object_name)。请先上传并识别音频。');
    return;
  }

  // 验证必填字段
  const requiredFields = {
    '学校': reportSchool.value,
    '举报方式': reportMethod.value,
    '联系电话': reportPhone.value,
    '时间': reportTime.value
  };

  for (const [field, value] of Object.entries(requiredFields)) {
    if (!value || !value.trim()) {
      alert(`请填写${field}信息`);
      return;
    }
  }


  // 验证时间格式 (YYYY-MM-DD HH:mm)
  if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(reportTime.value.trim())) {
    alert('时间格式应为 YYYY-MM-DD HH:mm');
    return;
  }

  isSubmitButtonDisabled.value = true; // 禁用按钮

  const reportData = {
    object_name: currentObjectName.value,
    school: reportSchool.value.trim(),
    method: reportMethod.value.trim(),
    phone: reportPhone.value.trim(),
    time: reportTime.value.trim(),
    transcription_text: transcriptionResult.value // 包含语音识别内容
  };

  console.log('准备提交举报数据:', reportData);

  try {
    const response = await fetch('/api/submit-final-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(reportData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`提交失败: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log('提交成功:', result);
    alert('举报信息提交成功！');

  } catch (error) {
    console.error('提交举报信息时出错:', error);
    alert(`提交失败: ${error.message}`);
  } finally {
    // 设置5秒后解除禁用
    setTimeout(() => {
      isSubmitButtonDisabled.value = false;
    }, 5000);
  }
};

</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 10px;
}

.file-upload-row, .model-select-row, .upload-btn-row {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-select {
  width: 260px;
  font-size: 18px;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #ddd;
}

.file-input {
  flex: 1;
  max-width: 260px;
  font-size: 18px;
  padding: 8px;
}

.upload-btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  min-width: 100px;
  height: 40px;
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
.report-info {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.report-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 10px;
}

.report-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.report-label {
  width: 80px;
  font-size: 14px;
  color: #333;
}

.report-input {
  flex: 1;
  padding: 4px 6px;
  font-size: 13px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.submit-btn-row {
  display: flex;
  justify-content: center;
}

.submit-btn {
  padding: 10px 20px;
  background-color: #007bff; /* 蓝色背景 */
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: #0056b3; /* 深蓝色悬停效果 */
}

.submit-btn:disabled {
  background-color: #cccccc; /* 灰色禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}
</style>