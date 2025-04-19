<template>
  <div class="edit-report-container">
    <p v-if="object_name">正在编辑举报: <strong>{{ object_name }}</strong></p>
    <p v-else>未指定举报信息。</p>

    <!-- 时间戳选择 -->
    <div v-if="submissionTimestamps.length > 0" class="timestamp-select-row">
      <label for="timestampSelect">选择编辑版本:</label>
      <select id="timestampSelect" v-model="selectedTimestamp" class="timestamp-select">
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
import { ref, onMounted, watch, provide, computed, toRef } from 'vue'; // 导入 ref, onMounted, watch, provide, computed, toRef
import { useRoute } from 'vue-router'; // useRoute 可能不再需要，除非用于其他参数
import SentenceBubble from '../components/SentenceBubble.vue'; // 修正路径
import ReportInfo from '../components/ReportInfo.vue';       // 修正路径
import SubmitButton from '../components/SubmitButton.vue';   // 修正路径

// 将 object_name 定义为 prop
const props = defineProps({
  object_name: {
    type: String,
    default: '' // 提供一个默认值是个好习惯
  }
});

// const route = useRoute(); // 如果不再需要 route 对象，可以注释或移除
// const object_name = ref(route.params.object_name); // 移除这行，使用 props.object_name

const mainAudio = ref(null);
provide('mainAudio', mainAudio);

const submissionTimestamps = ref([]);
const selectedTimestamp = ref('');
const isLoading = ref(false);
const error = ref('');

const parsedSentences = ref([]);
const transcriptionResult = ref(''); // 存储完整的转录文本
const audioFileUrl = ref('');
const reportSchool = ref('');
const reportMethod = ref('');
const reportPhone = ref('');
const reportTime = ref('');

const showReportInfo = ref(false);
const showSubmitButton = ref(false);
const isSubmitButtonDisabled = ref(false);

// --- 数据获取 ---

const fetchTimestamps = async () => {
  // 使用 props.object_name
  if (!props.object_name) return;
  isLoading.value = true;
  error.value = '';
  try {
    // 使用 props.object_name
    const response = await fetch(`/api/get-timestamps?object_name=${encodeURIComponent(props.object_name)}`);
    if (!response.ok) {
      throw new Error(`获取时间戳失败: ${response.status}`);
    }
    const data = await response.json();
    submissionTimestamps.value = data.timestamps || [];
    // 只获取时间戳，不在 fetchTimestamps 中设置 selectedTimestamp
  } catch (err) {
    console.error('获取时间戳错误:', err);
    error.value = `加载历史版本列表失败: ${err.message}`;
    submissionTimestamps.value = []; // 出错时清除时间戳
  } finally {
    isLoading.value = false;
  }
};

// 获取音频文件
const fetchAudioFile = async () => {
  if (!props.object_name) return;
  // 注意：这里不设置 isLoading，让主加载流程控制
  // error.value = ''; // 错误由主流程处理

  try {
    const response = await fetch(`/api/get-audio-file?object_name=${encodeURIComponent(props.object_name)}`);
    if (!response.ok) {
      console.warn(`获取音频文件失败: ${response.status}`);
      throw new Error(`获取音频文件失败: ${response.status}`); // 抛出错误以便 Promise.allSettled 捕获
    }
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.startsWith('audio/')) {
      console.warn('无效的音频格式');
       throw new Error('无效的音频格式'); // 抛出错误
    }
    const audioBlob = await response.blob();
    audioFileUrl.value = URL.createObjectURL(audioBlob);
    return true; // 表示成功
  } catch (audioErr) {
    console.error("获取音频文件时出错:", audioErr);
    audioFileUrl.value = ''; // 清除可能存在的旧 URL
    // 将错误向上抛出，由 Promise.allSettled 处理
    throw audioErr; // 让调用者知道失败了
  }
};


// 根据时间戳获取举报详情（仅文本）
// timestamp 为 null 或 undefined 时获取最新版本
const fetchReportDetails = async (timestamp, isInitialLoad = false) => {
  if (!props.object_name) return;
  // 如果不是初始加载，则设置加载状态并重置
  if (!isInitialLoad) {
      isLoading.value = true;
      error.value = '';
      resetReportData(); // 获取新详情前重置数据 (保留音频)
  }

  try {
    // 构造请求 URL，如果 timestamp 为空，则不传递该参数
    let url = `/api/get-report-details?object_name=${encodeURIComponent(props.object_name)}`;
    if (timestamp) {
        url += `&timestamp=${encodeURIComponent(timestamp)}`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`获取举报详情失败: ${response.status}`);
    }
    const reportData = await response.json();

    if (reportData) {
      reportSchool.value = reportData.school || '';
      reportMethod.value = reportData.method || '';
      reportPhone.value = reportData.phone || '';
      reportTime.value = formatInputTime(reportData.time);
      transcriptionResult.value = reportData.transcription_text || '';
      parsedSentences.value = reportData.transcription_text ? reportData.transcription_text.split('\n').filter(line => line.trim() !== '') : [];
      showReportInfo.value = true;
      showSubmitButton.value = true;
      return true; // 表示成功
    } else {
      throw new Error('未获取到有效的举报数据');
    }
  } catch (err) {
    console.error('加载举报详情时出错:', err);
    // 如果是初始加载，错误由 onMounted 统一处理，否则直接设置
    if (!isInitialLoad) {
        error.value = `加载举报详情失败: ${err.message}`;
        resetReportData(); // 确保在出错时重置所有相关数据状态
    }
    // 将错误向上抛出，由调用者 (onMounted 或 watch) 处理
    throw err;
  } finally {
    // 如果不是初始加载，在这里结束加载状态
    if (!isInitialLoad) {
        isLoading.value = false;
    }
  }
};

// --- 组件逻辑 ---

const updateSentence = (index, newVal) => {
  if (parsedSentences.value && parsedSentences.value.length > index) {
    parsedSentences.value[index] = newVal;
    transcriptionResult.value = parsedSentences.value.join('\n');
  }
};

const handleSubmitReport = async (reportData) => {
  // SubmitButton 组件现在发出完整的 reportData 对象
  isSubmitButtonDisabled.value = true;
  error.value = ''; // 清除之前的错误

  // 确保包含当前的转录文本
  const finalReportData = {
      ...reportData, // 包含来自 ReportInfo 的学校、方式、电话、时间
      object_name: props.object_name, // 使用 props.object_name
      transcription_text: transcriptionResult.value, // 使用可能已编辑的文本
      submission_timestamp: selectedTimestamp.value // 包含正在编辑的时间戳？还是生成新的？假设我们更新现有的，或者后端处理版本控制。为简单起见，我们发送它。
      // 如果后端需要在编辑时创建*新*版本，请在此处移除 submission_timestamp。
  };


  console.log("Submitting updated report:", finalReportData);


  try {
    // 使用与上传相同的端点，或专用的更新端点
    // 假设如果提供了时间戳，'/api/submit-final-report' 可以处理更新
    const response = await fetch('/api/submit-final-report', {
      method: 'POST', // 或者如果你的 API 使用 PUT 进行更新
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
    // 可选地，刷新时间戳或导航离开
    await fetchTimestamps(); // 刷新时间戳列表以防创建了新的时间戳
    // 或许重置选择或导航？
    // selectedTimestamp.value = ''; // 重置选择
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
  // audioFileUrl.value = ''; // 重置时不应清除音频，除非 object_name 改变
  reportSchool.value = '';
  reportMethod.value = '';
  reportPhone.value = '';
  reportTime.value = '';
  showReportInfo.value = false;
  showSubmitButton.value = false;
  error.value = ''; // 重置时也清除错误
};

const formatTimestamp = (isoTimestamp) => {
  if (!isoTimestamp) return 'N/A';
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleString('zh-CN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch (e) {
    return isoTimestamp; // 如果格式化失败则返回原始值
  }
};

// 如果需要，格式化时间以便在 ReportInfo 中显示/编辑
const formatInputTime = (timeString) => {
    // 假设 timeString 可能是 YYYYMMDDHHMMSS 或已格式化
    if (timeString && /^\d{14}$/.test(timeString)) {
      const t = timeString;
      return `${t.slice(0,4)}-${t.slice(4,6)}-${t.slice(6,8)}T${t.slice(8,10)}:${t.slice(10,12)}`; // 格式化为 datetime-local 输入
    }
    // 如果已经是合适的格式（如 ISO 或 YYYY-MM-DD HH:MM），则根据需要调整
    // 为简单起见，如果不是特定的 14 位数字格式，则按原样返回
    return timeString || '';
};


// --- 生命周期钩子 ---

// 标记是否为首次加载数据
const isInitialLoading = ref(false);

onMounted(async () => {
  if (!props.object_name) {
    error.value = "未提供举报标识 (object_name)。";
    return;
  }

  isLoading.value = true;
  isInitialLoading.value = true; // 标记开始初始加载
  error.value = '';
  resetReportData(); // 初始加载前清空所有数据

  console.log("开始并发获取初始数据...");

  const results = await Promise.allSettled([
    fetchTimestamps(),
    fetchReportDetails(null, true), // 获取最新详情，标记为初始加载
    fetchAudioFile()
  ]);

  console.log("并发获取结果:", results);

  let timestampsResult, detailsResult, audioResult;
  let fetchError = null;

  // 处理时间戳结果
  if (results[0].status === 'fulfilled') {
    timestampsResult = results[0].value; // fetchTimestamps 不返回值，但成功即表示列表已更新
    if (submissionTimestamps.value.length > 0) {
      // 设置初始选中的时间戳，但不触发 watch 中的 fetch
      selectedTimestamp.value = submissionTimestamps.value[0];
      console.log("初始时间戳设置为:", selectedTimestamp.value);
    } else {
        console.log("没有找到历史版本。");
        // 如果没有时间戳，可能需要显示提示信息，而不是错误
        // error.value = "没有找到该举报的历史版本。";
    }
  } else {
    console.error("获取时间戳失败:", results[0].reason);
    fetchError = results[0].reason; // 记录第一个错误
  }

  // 处理详情结果 (fetchReportDetails 内部已更新 refs)
  if (results[1].status === 'fulfilled') {
    detailsResult = results[1].value; // 成功时返回 true
    console.log("获取最新详情成功。");
  } else {
    console.error("获取最新详情失败:", results[1].reason);
    if (!fetchError) fetchError = results[1].reason; // 记录错误
  }

  // 处理音频结果 (fetchAudioFile 内部已更新 ref)
  if (results[2].status === 'fulfilled') {
    audioResult = results[2].value; // 成功时返回 true
    console.log("获取音频成功。");
  } else {
    console.error("获取音频失败:", results[2].reason);
     // 音频失败通常不阻止显示文本，可以只记录警告或次要错误
     // if (!fetchError) fetchError = results[2].reason;
     console.warn("音频文件加载失败，但不阻塞页面。");
  }

  // 如果有任何关键请求失败，设置错误状态
  if (fetchError) {
      error.value = `加载初始数据失败: ${fetchError.message || fetchError}`;
      // 根据失败情况决定是否重置数据
      if (results[1].status !== 'fulfilled') { // 如果详情获取失败，则重置
          resetReportData();
      }
  } else if (!selectedTimestamp.value) {
      // 如果时间戳和详情都成功，但时间戳列表为空
      error.value = "没有找到该举报的任何版本。";
      resetReportData(); // 清空界面
  }


  isLoading.value = false;
  // 延迟一点重置 initialLoading 标志，确保 watch 不会误触发
  setTimeout(() => {
      isInitialLoading.value = false;
      console.log("初始加载完成。");
  }, 0);
});

// 监视 prop object_name 的变化
watch(() => props.object_name, (newName, oldName) => {
  // 当 prop 变化时，重置状态并重新获取数据
  // 当 prop 变化时，重新执行 onMounted 的逻辑来并发获取新数据
  if (newName && newName !== oldName) {
      console.log(`Object Name 改变: ${oldName} -> ${newName}，重新加载数据...`);
      // 触发 onMounted 逻辑 (或者将其提取到一个可重用函数中)
      // 为了简单起见，这里直接调用 onMounted 内部的逻辑
      // 注意：这会重置所有状态，包括 selectedTimestamp
      onMounted(); // 重新执行挂载逻辑
  } else if (!newName && oldName) {
      // 如果 object_name 变为空，则清空数据
      console.log("Object Name 变为空，清空数据。");
      selectedTimestamp.value = '';
      resetReportData();
      submissionTimestamps.value = [];
      error.value = "未提供举报标识 (object_name)。";
  }
}, { immediate: false }); // immediate: false 因为 onMounted 已经处理了初始加载

// 监听 selectedTimestamp 的变化，自动获取详情
watch(selectedTimestamp, (newTimestamp, oldTimestamp) => {
  // 仅当时间戳实际改变、不为空，并且不是在初始加载期间设置时才触发获取
  if (newTimestamp && newTimestamp !== oldTimestamp && !isInitialLoading.value) {
    console.log(`用户选择时间戳: ${newTimestamp}，获取对应详情...`);
    fetchReportDetails(newTimestamp, false); // 获取指定版本详情，标记为非初始加载
  } else if (!newTimestamp && !isInitialLoading.value) {
    // 如果时间戳被用户清空（理论上不会发生，除非有清空选项）
    console.log("时间戳被清空，重置报告数据。");
    resetReportData();
  } else if (newTimestamp && newTimestamp !== oldTimestamp && isInitialLoading.value) {
      console.log("初始加载设置 selectedTimestamp，跳过 watch fetch。");
  }
});

// 提供 SubmitButton 所需的响应式引用
provide('reportSchool', reportSchool);
provide('reportMethod', reportMethod);
provide('reportPhone', reportPhone);
provide('reportTime', reportTime);
provide('currentObjectName', toRef(props, 'object_name')); // 提供 prop 的 ref
provide('transcriptionResult', transcriptionResult); // SubmitButton 需要最终文本

</script>

<style scoped>
.edit-report-container {
  max-width: 600px; /* 增加最大宽度 */
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
  margin-bottom: 15px; /* 调整边距 */
  text-align: center;
}

strong {
  color: #0056b3; /* 深蓝色 */
}

.timestamp-select-row {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px; /* 在标签和选择框之间添加间隙 */
}

.timestamp-select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 16px;
  min-width: 250px; /* 确保选择框有足够的宽度 */
}


.error-text {
  color: #dc3545; /* Bootstrap 危险色 */
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
  text-align: center; /* 如果需要，居中链接 */
}

a:hover {
  background-color: #5a6268;
}


</style>