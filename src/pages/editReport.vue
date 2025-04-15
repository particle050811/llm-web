<template>
  <div class="edit-report-container">
    <p v-if="object_name">正在编辑举报: <strong>{{ object_name }}</strong></p>
    <p v-else>未指定举报信息。</p>

    <!-- 时间戳选择 -->
    <div v-if="submissionTimestamps.length > 0" class="timestamp-select-row">
      <label for="timestampSelect">选择编辑版本:</label>
      <select id="timestampSelect" v-model="selectedTimestamp" @change="fetchReportDetails" class="timestamp-select">
        <option disabled value="">请选择一个时间戳</option>
        <option v-for="ts in submissionTimestamps" :key="ts" :value="ts">
          {{ formatTimestamp(ts) }}
        </option>
      </select>
    </div>
    <p v-else-if="!isLoading && object_name">没有找到该举报的历史版本。</p>
    <p v-if="isLoading">正在加载数据...</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <!-- 主要内容区域 -->
    <div v-if="selectedTimestamp && !isLoading && !error">
      <ReportInfo
        v-if="showReportInfo"
        v-model:school="reportSchool"
        v-model:method="reportMethod"
        v-model:phone="reportPhone"
        v-model:time="reportTime"
      />
      <audio v-if="audioFileUrl" ref="mainAudio" :src="audioFileUrl" controls style="width:100%; margin:10px 0;"></audio>
      <div class="chat-container">
        <SentenceBubble
          v-for="(sentence, index) in parsedSentences"
          :key="index"
          :rawText="sentence"
          :audioUrl="audioFileUrl"
          @update:rawText="(newVal) => updateSentence(index, newVal)"
        />
      </div>
      <SubmitButton
        :isDisabled="isSubmitButtonDisabled"
        :showButton="showSubmitButton"
        @submit="handleSubmitReport"
        buttonText="更新举报信息"
      />
    </div>
  </div>
   <br><br><br><br><br>
</template>

<script setup>
import { ref, onMounted, watch, provide, computed } from 'vue';
import { useRoute } from 'vue-router';
import SentenceBubble from '../components/SentenceBubble.vue'; // Corrected path
import ReportInfo from '../components/ReportInfo.vue';       // Corrected path
import SubmitButton from '../components/SubmitButton.vue';   // Corrected path

const route = useRoute();
const object_name = ref(route.params.object_name);

const mainAudio = ref(null);
provide('mainAudio', mainAudio);

const submissionTimestamps = ref([]);
const selectedTimestamp = ref('');
const isLoading = ref(false);
const error = ref('');

const parsedSentences = ref([]);
const transcriptionResult = ref(''); // Store the full transcription text
const audioFileUrl = ref('');
const reportSchool = ref('');
const reportMethod = ref('');
const reportPhone = ref('');
const reportTime = ref('');

const showReportInfo = ref(false);
const showSubmitButton = ref(false);
const isSubmitButtonDisabled = ref(false);

// --- Data Fetching ---

const fetchTimestamps = async () => {
  if (!object_name.value) return;
  isLoading.value = true;
  error.value = '';
  try {
    const response = await fetch(`/api/get-timestamps?object_name=${encodeURIComponent(object_name.value)}`);
    if (!response.ok) {
      throw new Error(`获取时间戳失败: ${response.status}`);
    }
    const data = await response.json();
    submissionTimestamps.value = data.timestamps || [];
    // Optionally select the latest timestamp by default
    if (submissionTimestamps.value.length > 0) {
      selectedTimestamp.value = submissionTimestamps.value[0];
      await fetchReportDetails();
    }
  } catch (err) {
    console.error('获取时间戳错误:', err);
    error.value = `加载历史版本列表失败: ${err.message}`;
    submissionTimestamps.value = []; // Clear timestamps on error
  } finally {
    isLoading.value = false;
  }
};

const fetchReportDetails = async () => {
  if (!object_name.value || !selectedTimestamp.value) return;
  isLoading.value = true;
  error.value = '';
  resetReportData(); // Reset data before fetching new details

  try {
    // Fetch report details
    const reportResponse = await fetch(`/api/get-report-details?object_name=${encodeURIComponent(object_name.value)}&timestamp=${encodeURIComponent(selectedTimestamp.value)}`);
    if (!reportResponse.ok) {
      throw new Error(`获取举报详情失败: ${reportResponse.status}`);
    }
    const reportData = await reportResponse.json();

    if (reportData) {
      reportSchool.value = reportData.school || '';
      reportMethod.value = reportData.method || '';
      reportPhone.value = reportData.phone || '';
      reportTime.value = formatInputTime(reportData.time); // Format for input if needed
      transcriptionResult.value = reportData.transcription_text || '';
      parsedSentences.value = reportData.transcription_text ? reportData.transcription_text.split('\n').filter(line => line.trim() !== '') : [];
      showReportInfo.value = true;
      showSubmitButton.value = true;

      // Fetch audio URL (assuming object_name corresponds to the audio file)
      // Note: This might need adjustment based on how audio is stored/retrieved
      try {
          const audioResponse = await fetch(`/api/get-audio-file?object_name=${encodeURIComponent(object_name.value)}`);
          if (!audioResponse.ok) {
              throw new Error(`HTTP错误: ${audioResponse.status}`);
          }
          
          const contentType = audioResponse.headers.get('content-type');
          if (!contentType || !contentType.startsWith('audio/')) {
              throw new Error('无效的音频格式');
          }
          
          const audioBlob = await audioResponse.blob();
          audioFileUrl.value = URL.createObjectURL(audioBlob);
      } catch (audioErr) {
          console.error("获取音频文件时出错:", audioErr);
          error.value = `获取音频文件失败: ${audioErr.message}`;
          audioFileUrl.value = '';
      }

    } else {
      throw new Error('未找到指定版本的举报数据');
    }

  } catch (err) {
    console.error('获取举报详情错误:', err);
    error.value = `加载举报详情失败: ${err.message}`;
    resetReportData();
  } finally {
    isLoading.value = false;
  }
};

// --- Component Logic ---

const updateSentence = (index, newVal) => {
  if (parsedSentences.value && parsedSentences.value.length > index) {
    parsedSentences.value[index] = newVal;
    transcriptionResult.value = parsedSentences.value.join('\n');
  }
};

const handleSubmitReport = async (reportData) => {
  // The SubmitButton component now emits the full reportData object
  isSubmitButtonDisabled.value = true;
  error.value = ''; // Clear previous errors

  // Ensure the current transcription text is included
  const finalReportData = {
      ...reportData, // Contains school, method, phone, time from ReportInfo
      object_name: object_name.value,
      transcription_text: transcriptionResult.value, // Use the potentially edited text
      submission_timestamp: selectedTimestamp.value // Include the timestamp being edited? Or generate new? Let's assume we update the existing one or backend handles versioning. For simplicity, let's send it.
      // If backend needs to create a *new* version upon edit, remove submission_timestamp here.
  };


  console.log("Submitting updated report:", finalReportData);


  try {
    // Use the same endpoint as upload, or a dedicated update endpoint
    // Assuming '/api/submit-final-report' can handle updates if timestamp is provided
    const response = await fetch('/api/submit-final-report', {
      method: 'POST', // Or PUT if your API uses it for updates
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(finalReportData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`更新失败: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    console.log('更新成功:', result);
    alert('举报信息更新成功！');
    // Optionally, refresh timestamps or navigate away
    await fetchTimestamps(); // Refresh timestamp list in case a new one was created
    // Maybe reset selection or navigate?
    // selectedTimestamp.value = ''; // Reset selection
    // resetReportData();

  } catch (err) {
    console.error('更新举报信息时出错:', err);
    error.value = `更新失败: ${err.message}`;
    alert(`更新失败: ${err.message}`);
  } finally {
    isSubmitButtonDisabled.value = false;
  }
};

const resetReportData = () => {
  parsedSentences.value = [];
  transcriptionResult.value = '';
  audioFileUrl.value = '';
  reportSchool.value = '';
  reportMethod.value = '';
  reportPhone.value = '';
  reportTime.value = '';
  showReportInfo.value = false;
  showSubmitButton.value = false;
  error.value = ''; // Also clear errors when resetting
};

const formatTimestamp = (isoTimestamp) => {
  if (!isoTimestamp) return 'N/A';
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleString('zh-CN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch (e) {
    return isoTimestamp; // Return original if formatting fails
  }
};

// Format time for display/editing in ReportInfo if needed
const formatInputTime = (timeString) => {
    // Assuming timeString might be YYYYMMDDHHMMSS or already formatted
    if (timeString && /^\d{14}$/.test(timeString)) {
      const t = timeString;
      return `${t.slice(0,4)}-${t.slice(4,6)}-${t.slice(6,8)}T${t.slice(8,10)}:${t.slice(10,12)}`; // Format for datetime-local input
    }
    // If it's already in a suitable format (like ISO or YYYY-MM-DD HH:MM), adapt as needed
    // For simplicity, returning as is if not in the specific 14-digit format
    return timeString || '';
};


// --- Lifecycle Hooks ---

onMounted(() => {
  if (object_name.value) {
    fetchTimestamps();
  } else {
    error.value = "未提供举报标识 (object_name)。";
  }
});

// Watch for route changes if the component is reused for different reports
watch(() => route.params.object_name, (newName) => {
  object_name.value = newName;
  selectedTimestamp.value = ''; // Reset selection when object_name changes
  resetReportData();
  fetchTimestamps();
});

// Provide reactive refs needed by SubmitButton
provide('reportSchool', reportSchool);
provide('reportMethod', reportMethod);
provide('reportPhone', reportPhone);
provide('reportTime', reportTime);
provide('currentObjectName', object_name); // SubmitButton might need this
provide('transcriptionResult', transcriptionResult); // SubmitButton needs the final text

</script>

<style scoped>
.edit-report-container {
  max-width: 600px; /* Increased max-width */
  margin: 0 auto;
  padding: 10px;
  border-radius: 8px;
}

h1 {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

p {
  font-size: 16px;
  margin-top: 0;
  margin-bottom: 15px; /* Adjusted margin */
  text-align: center;
}

strong {
  color: #0056b3; /* Darker blue */
}

.timestamp-select-row {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px; /* Add gap between label and select */
}

.timestamp-select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 16px;
  min-width: 250px; /* Ensure select has enough width */
}


.error-text {
  color: #dc3545; /* Bootstrap danger color */
  font-weight: bold;
  text-align: center;
  margin-top: 15px;
}

a {
  display: inline-block;
  margin-top: 20px;
  padding: 8px 15px;
  background-color: #6c757d;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
  text-align: center; /* Center link if needed */
}

a:hover {
  background-color: #5a6268;
}


</style>