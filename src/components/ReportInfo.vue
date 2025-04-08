<template>
  <div class="report-info">
    <div class="report-row">
      <label class="report-label">举报学校</label>
      <input class="report-input" v-model="schoolValue" placeholder="无法识别" />
    </div>
    <div class="report-row">
      <label class="report-label">举报途径</label>
      <input class="report-input" v-model="methodValue" placeholder="无法识别" />
    </div>
    <div class="report-row">
      <label class="report-label">举报电话</label>
      <input class="report-input" v-model="phoneValue" placeholder="无法识别" />
    </div>
    <div class="report-row">
      <label class="report-label">举报时间</label>
      <input class="report-input" v-model="timeValue" placeholder="无法识别" />
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue';

const props = defineProps({
  school: String,
  method: String,
  phone: String,
  time: String
});

const emits = defineEmits(['update:school', 'update:method', 'update:phone', 'update:time']);

const schoolValue = computed({
  get: () => props.school,
  set: (val) => emits('update:school', val)
});
const methodValue = computed({
  get: () => props.method,
  set: (val) => emits('update:method', val)
});
const phoneValue = computed({
  get: () => props.phone,
  set: (val) => emits('update:phone', val)
});
const timeValue = computed({
  get: () => props.time,
  set: (val) => emits('update:time', val)
});
</script>

<style scoped>
.report-info {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 12px;
  background-color: #f9f9f9;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: 1rem;
  line-height: 1.5;
}

.report-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.report-label {
  width: 80px;
  font-size: 1rem;
  color: #333;
}

.report-input {
  flex: 1;
  padding: 10px 15px;
  font-size: 1rem;
  line-height: 1.5;
  border: 1px solid #ccc;
  border-radius: 15px;
  box-sizing: border-box;
}
</style>