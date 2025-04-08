<template>
  <div class="sentence-bubble-wrapper" :class="speakerClass">
    <button v-if="!isEditing" v-show="speaker === 's'" class="edit-button-left" @click.stop="startEdit">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.06 9L15 9.94L5.92 19H5V18.08L14.06 9ZM17.66 3C17.41 3 17.15 3.1 16.96 3.29L15.13 5.12L18.88 8.87L20.71 7.04C21.1 6.65 21.1 6 20.71 5.63L18.37 3.29C18.17 3.09 17.92 3 17.66 3ZM14.06 6.19L3 17.25V21H6.75L17.81 9.94L14.06 6.19Z" fill="currentColor"/>
      </svg>
    </button>
    <div v-if="!isEditing" class="sentence-bubble" ref="bubbleElement" @click="playAudio">
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
import { computed, ref, nextTick, watch } from 'vue';
const emit = defineEmits(['update:rawText']);

const props = defineProps({
  rawText: {
    type: String,
    required: true,
  },
  audioUrl: {
    type: String,
    required: true, // 仍然需要父组件提供音频 URL
  },
  // startTime 和 endTime 不再作为 props 传入
});

// 从 rawText 提取时间戳字符串
const timeRegex = /\[(\d{2}):(\d{2})-(\d{2}):(\d{2})\]/;


// 辅助函数：解析时间戳字符串 [MM:SS-MM:SS]
const parseTimestamp = (text) => {
  const match = text.match(timeRegex);
  let startTime = -1;
  let endTime = -1;

  if (match) {
    const startMinutes = parseInt(match[1], 10);
    const startSeconds = parseInt(match[2], 10);
    const endMinutes = parseInt(match[3], 10);
    const endSeconds = parseInt(match[4], 10);
    startTime = startMinutes * 60 + startSeconds;
    endTime = endMinutes * 60 + endSeconds;
  }
  // 返回解析结果，如果没匹配到，则 startTime 和 endTime 保持为 -1
  return { startTime, endTime };
};


// 计算属性，用于从 rawText 动态提取 startTime
const computedStartTime = computed(() => {
  return parseTimestamp(props.rawText).startTime;
});

// 计算属性，用于从 rawText 动态提取 endTime
const computedEndTime = computed(() => {
  return parseTimestamp(props.rawText).endTime;
});

// 从 rawText 计算 speaker
const speaker = computed(() => {
  return props.rawText.startsWith('[s]') ? 's' : 'o';
});

// 提取对话内容（不含时间戳和标签）
const content = computed(() => {
  // 检查是否以 <s> 或 <o> 开头，并且成功提取了时间戳
  const { startTime, endTime } = parseTimestamp(props.rawText);
  const isValid = (props.rawText.startsWith('[s]') || props.rawText.startsWith('[o]')) && startTime !== -1 && endTime !== -1;
  if (!isValid) {
    bubbleElement.value?.classList.add('red-text');
    bubbleElement.value?.classList.remove('speaker-s', 'speaker-o');
    bubbleElement.value?.classList.add('speaker-default');
    return props.rawText;
  }

  bubbleElement.value?.classList.remove('red-text', 'speaker-default');
  bubbleElement.value?.classList.add(`speaker-${speaker.value}`);
  
  return props.rawText
    .replace(timeRegex, '')
    .slice(3)
    .trim();
});

const displayText = computed(() => content.value);

const speakerClass = computed(() => {
  return speaker.value === 's' ? 'speaker-s' : 'speaker-o';
});

const isEditing = ref(false);
const editText = ref('');
const editInput = ref(null);
const bubbleElement = ref(null);

const startEdit = () => {
  isEditing.value = true;
  editText.value = props.rawText; // 编辑原始文本（包含[s]标签）
  nextTick(() => {
    editInput.value.focus();
    autoResizeTextarea();
  });
};

const saveEdit = () => {
  console.log('保存编辑触发');
  if (editText.value.trim()) {
    // 构建新的原始文本
    const newRawText = editText.value.replace(/\n/g, '').trim();
    console.log('触发update:rawText事件，内容:', newRawText);
    emit('update:rawText', newRawText);
  }
  console.log('设置isEditing为false');
  isEditing.value = false;
};
const cancelEdit = () => {
  isEditing.value = false;
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

const playAudio = () => {
  try {
    if (!props.audioUrl) {
      console.error('音频URL为空');
      return;
    }
    const audio = new Audio(props.audioUrl);
    // 使用计算属性获取开始和结束时间
    audio.currentTime = computedStartTime.value;
    audio.play().catch(e => console.error("播放音频失败:", e)); // 添加播放错误处理

    // 在到达结束时间时停止播放
    const stopAt = computedEndTime.value;
    const checkTime = () => {
      if (audio.currentTime >= stopAt) {
        audio.pause();
        audio.removeEventListener('timeupdate', checkTime);
      }
    };
    
    audio.addEventListener('timeupdate', checkTime);
  } catch (error) {
    console.error('播放音频时发生错误:', error);
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
  cursor: pointer;
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