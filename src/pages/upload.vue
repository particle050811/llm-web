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
        :text="sentence.text"
        :speaker="sentence.speaker"
      />
    </div>
  </div>
</template>

<script>
import CryptoJS from 'crypto-js';
import SentenceBubble from '@/components/SentenceBubble.vue'; // 新增：导入 SentenceBubble 组件

export default {
  components: { // 新增：注册组件
    SentenceBubble,
  },
  data() {
    return {
      selectedFile: null,
      selectedModel: 'gemini-2.0-flash-thinking',
      uploadStatus: '',
      transcriptionResult: '', // 新增：存储识别结果
      isLoadingTranscription: false // 新增：识别加载状态
    }
  },
  computed: { // 新增：计算属性来解析识别结果
    parsedSentences() {
      if (!this.transcriptionResult) {
        return [];
      }
      const sentences = [];
      // 使用正则表达式匹配 <s>...</s> 或 <o>...</o>
      const regex = /<(s|o)>(.*?)<\/\1>/g;
      let match;
      while ((match = regex.exec(this.transcriptionResult)) !== null) {
        sentences.push({
          speaker: match[1], // 's' or 'o'
          text: match[2].trim(), // 提取文本并去除首尾空格
        });
      }
      return sentences;
    },
  },
  methods: {
    async calculateFileHash(file) {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const wordArray = CryptoJS.lib.WordArray.create(e.target.result)
          const md5 = CryptoJS.MD5(wordArray).toString()
          resolve(md5)
        }
        reader.readAsArrayBuffer(file)
      })
    },
    handleFileChange(event) {
      this.selectedFile = event.target.files[0]
    },
    async uploadAudio() {
      if (!this.selectedFile) {
        this.uploadStatus = '请先选择音频文件'
        return
      }

      try {
        this.uploadStatus = '正在计算文件校验...'
        const fileHash = await this.calculateFileHash(this.selectedFile)

        this.uploadStatus = '正在检查服务器...'
        const urlResponse = await fetch(`/api/generate-audio-url?contentType=${encodeURIComponent(this.selectedFile.type)}&fileHash=${fileHash}`)
        if (!urlResponse.ok) {
          throw new Error(`获取上传链接失败，状态码: ${urlResponse.status}`)
        }
        const urlData = await urlResponse.json()

        if (urlData.status === 'exists') {
          this.uploadStatus = '文件已存在(服务器已有相同文件)，开始识别...'
          await this.transcribeAudio(urlData.object_name, this.selectedModel)
        } else if (urlData.status === 'new') {
          // 文件不存在，需要上传到新的 /api/upload-audio 接口
          this.uploadStatus = '准备上传文件...'
          const formData = new FormData()
          formData.append('file', this.selectedFile)
          formData.append('object_name', urlData.object_name) // 将 object_name 作为表单字段发送

          this.uploadStatus = '正在上传文件...'
          const uploadResponse = await fetch('/api/upload-audio', {
            method: 'POST',
            body: formData
            // 注意：发送 FormData 时不需要设置 Content-Type header
          })

          if (uploadResponse.ok) {
            const uploadResult = await uploadResponse.json() // 可以获取后端返回的信息
            this.uploadStatus = '文件上传成功! 开始识别...'
            await this.transcribeAudio(uploadResult.object_name) // 使用后端确认的 object_name
          } else {
            const errorText = await uploadResponse.text()
            throw new Error(`上传失败，状态码: ${uploadResponse.status}, 错误: ${errorText}`)
          }
        } else {
           // 处理未知的 status 或错误
           throw new Error(`未知的服务器响应状态: ${urlData.status}`)
        }
      } catch (error) {
        console.error('上传或识别错误:', error)
        this.uploadStatus = '处理失败: ' + error.message
        this.isLoadingTranscription = false // 出错时停止加载
      }
    }, // 在 uploadAudio 方法后添加逗号
    async transcribeAudio(objectName, model) {
      this.isLoadingTranscription = true
      this.transcriptionResult = ''
      this.uploadStatus = '正在识别中...'

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
        })

        if (!response.ok) {
          throw new Error(`识别请求失败: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let done = false

        while (!done) {
          const { value, done: readerDone } = await reader.read()
          done = readerDone
          if (value) {
            const chunk = decoder.decode(value)
            // 直接将原始带标签的文本追加
            this.transcriptionResult += chunk
          }
        }

        this.uploadStatus = '识别完成!'
      } catch (error) {
        console.error('识别错误:', error)
        this.uploadStatus = '识别失败: ' + error.message
        this.transcriptionResult = '识别出错' // 可以显示错误信息
      } finally {
        this.isLoadingTranscription = false
      }
    } // transcribeAudio 方法结束
  }, // methods 对象结束
}
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