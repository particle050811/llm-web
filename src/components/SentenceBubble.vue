<template>
  <div class="sentence-bubble-wrapper" :class="speakerClass">
    <div class="sentence-bubble">
      {{ text }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
  speaker: {
    type: String, // 's' for self (right), 'o' for other (left)
    required: true,
    validator: (value) => ['s', 'o'].includes(value),
  },
});

const speakerClass = computed(() => {
  return props.speaker === 's' ? 'speaker-s' : 'speaker-o';
});
</script>

<style scoped>
.sentence-bubble-wrapper {
  display: flex;
  margin-bottom: 10px;
  max-width: 80%; /* 限制气泡最大宽度 */
}

.sentence-bubble {
  padding: 10px 15px;
  border-radius: 15px;
  word-wrap: break-word; /* 允许长单词换行 */
  white-space: pre-wrap; /* 保留空格和换行符 */
}

.speaker-s {
  margin-left: auto; /* 靠右对齐 */
  justify-content: flex-end; /* 内容靠右 */
}

.speaker-s .sentence-bubble {
  background-color: #0084ff; /* 蓝色背景 */
  color: white;
  border-bottom-right-radius: 5px; /* 右下角调整为直角 */
}

.speaker-o {
  margin-right: auto; /* 靠左对齐 */
  justify-content: flex-start; /* 内容靠左 */
}

.speaker-o .sentence-bubble {
  background-color: #e5e5ea; /* 灰色背景 */
  color: black;
  border-bottom-left-radius: 5px; /* 左下角调整为直角 */
}
</style>