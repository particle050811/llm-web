<template>
  <div class="submit-btn-row" style="margin-top: 20px;" v-if="showButton">
    <button @click="handleSubmit" :disabled="isDisabled" class="submit-btn">
      {{ isDisabled ? '提交中...' : '提交举报信息' }}
    </button>
  </div>
</template>

<script setup>
import { inject } from 'vue';

const emit = defineEmits(['submit']);

const props = defineProps({
  isDisabled: {
    type: Boolean,
    default: false
  },
  showButton: {
    type: Boolean,
    default: false
  }
});

// 从父组件注入的表单数据
const reportSchool = inject('reportSchool');
const reportMethod = inject('reportMethod'); 
const reportPhone = inject('reportPhone');
const reportTime = inject('reportTime');
const currentObjectName = inject('currentObjectName');
const transcriptionResult = inject('transcriptionResult');

const handleSubmit = async () => {
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

  emit('submit', {
    object_name: currentObjectName.value,
    school: reportSchool.value.trim(),
    method: reportMethod.value.trim(),
    phone: reportPhone.value.trim(),
    time: reportTime.value.trim(),
    transcription_text: transcriptionResult.value
  });
};
</script>

<style scoped>
.submit-btn-row {
  display: flex;
  justify-content: center;
}

.submit-btn {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  opacity: 0.7;
}
</style>