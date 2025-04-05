<template>
  <div class="sentence-bubble-wrapper" :class="speakerClass">
    <button v-if="!isEditing" v-show="speaker === 's'" class="edit-button-left" @click.stop="startEdit">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.06 9L15 9.94L5.92 19H5V18.08L14.06 9ZM17.66 3C17.41 3 17.15 3.1 16.96 3.29L15.13 5.12L18.88 8.87L20.71 7.04C21.1 6.65 21.1 6 20.71 5.63L18.37 3.29C18.17 3.09 17.92 3 17.66 3ZM14.06 6.19L3 17.25V21H6.75L17.81 9.94L14.06 6.19Z" fill="currentColor"/>
      </svg>
    </button>
    <div v-if="!isEditing" class="sentence-bubble" @click="toggleEdit" ref="bubbleElement">
      <span>{{ displayText }}</span>
    </div>
    <textarea
      v-else
      v-model="editText"
      @input="autoResizeTextarea"
      @blur="saveEdit"
      @keydown.enter="handleTextareaEnter"
      @keyup.esc="cancelEdit"
      class="edit-textarea-standalone"
      ref="editInput"
      rows="1"
    ></textarea>
    <button v-if="!isEditing" v-show="speaker === 'o'" class="edit-button-right" @click.stop="startEdit">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.06 9L15 9.94L5.92 19H5V18.08L14.06 9ZM17.66 3C17.41 3 17.15 3.1 16.96 3.29L15.13 5.12L18.88 8.87L20.71 7.04C21.1 6.65 21.1 6 20.71 5.63L18.37 3.29C18.17 3.09 17.92 3 17.66 3ZM14.06 6.19L3 17.25V21H6.75L17.81 9.94L14.06 6.19Z" fill="currentColor"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue';
const emit = defineEmits(['update:rawText']);

const props = defineProps({
  rawText: {
    type: String,
    required: true,
  },
});

// 从 rawText 计算 speaker
const speaker = computed(() => {
  return props.rawText.startsWith('<s>') ? 's' : 'o';
});

// 从 rawText 计算要显示的文本
const displayText = computed(() => {
  // 检查格式是否有效
  const isValid = (props.rawText.startsWith('<s>') && props.rawText.endsWith('</s>')) ||
                 (props.rawText.startsWith('<o>') && props.rawText.endsWith('</o>'));
  
  if (!isValid) {
    bubbleElement.value?.classList.add('red-text');
    // 即使格式无效，也应用一个默认的气泡样式，避免空白
    bubbleElement.value?.classList.remove('speaker-s', 'speaker-o');
    bubbleElement.value?.classList.add('speaker-default');
    return props.rawText; // 返回原始文本
  }
  
  bubbleElement.value?.classList.remove('red-text', 'speaker-default');
  bubbleElement.value?.classList.add(`speaker-${speaker.value}`);
  // 格式有效时移除前缀和后缀，保留换行符
  const content = props.rawText.slice(3, -4);
  // 保留原始换行符，只去除首尾空白
  return content.trimStart();
});

const speakerClass = computed(() => {
  return speaker.value === 's' ? 'speaker-s' : 'speaker-o';
});

const isEditing = ref(false);
const editText = ref('');
const editInput = ref(null);
const bubbleElement = ref(null);

const startEdit = () => {
  isEditing.value = true;
  editText.value = props.rawText; // 编辑原始文本（包含<s>标签）
  nextTick(() => {
    editInput.value.focus();
    autoResizeTextarea();
  });
};

const saveEdit = () => {
  console.log('saveEdit triggered');
  if (editText.value.trim()) {
    // 允许保存任何文本，显示逻辑由 displayText 处理
    const newRawText = editText.value.trim();
    console.log('Emitting update:rawText with:', newRawText);
    emit('update:rawText', newRawText);
  }
  console.log('Setting isEditing to false');
  isEditing.value = false;
};
const cancelEdit = () => {
  isEditing.value = false;
};

const toggleEdit = () => {
  if (!isEditing.value) {
    startEdit();
  }
};

const autoResizeTextarea = () => {
  const textarea = editInput.value;
  textarea.style.height = 'auto';
  textarea.style.height = `${textarea.scrollHeight}px`;
};

const handleTextareaEnter = (e) => {
  if (e.ctrlKey || e.metaKey) {
    saveEdit();
  }
};

</script>

<style scoped>
:root {
  --bubble-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  --bubble-font-size: 1rem;
  --bubble-line-height: 1.5;
  --bubble-color: inherit;
}

.sentence-bubble-wrapper {
  display: flex;
  margin-bottom: 10px;
  max-width: 80%; /* 限制气泡最大宽度 */
  width: fit-content; /* 使宽度适应内容 */
  font-family: var(--bubble-font-family);
  font-size: var(--bubble-font-size);
  line-height: var(--bubble-line-height);
  align-items: center; /* 确保内容垂直居中 */
}



.edit-textarea-standalone {
  margin-bottom: 10px;
  padding: 10px 15px;
  border-radius: 15px;
  border: 1px solid #ccc;
  resize: none;
  overflow: hidden;
  box-sizing: border-box;
  font-family: var(--bubble-font-family);
  font-size: var(--bubble-font-size);
  line-height: var(--bubble-line-height);
  color: var(--bubble-color);
  background: transparent;
  width: 450px; /* 设置一个合理的宽度 */
}

.sentence-bubble {
  padding: 10px 15px;
  border-radius: 15px;
  overflow-wrap: break-word; /* 使用标准属性替换word-wrap */
  white-space: pre-wrap; /* 保留空格和换行符 */
  background-color: #f0f0f0; /* 默认背景色，确保所有气泡都有背景 */
  color: #333;
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

.red-text {
  color: #ff000085 !important;
  font-weight: bold !important;
}

.speaker-default .sentence-bubble {
  background-color: #f0f0f0; /* 默认背景色 */
  color: #333;
  border-radius: 15px;
}

.edit-button-left,
.edit-button-right {
  margin-right: 8px;
  padding: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
}




</style>