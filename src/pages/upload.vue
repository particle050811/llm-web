<template>
  <div class="upload-container">
    <h1>音频上传</h1>
    <input 
      type="file" 
      id="audioInput" 
      accept="audio/*" 
      @change="handleFileChange" 
    />
    <button @click="uploadAudio">上传音频</button>
    <p v-if="uploadStatus">{{ uploadStatus }}</p>
    <div v-if="isLoadingTranscription" class="loading">正在识别中...</div>
    <div v-if="transcriptionResult" class="transcription-result">
      <h2>识别结果:</h2>
      <p>{{ transcriptionResult }}</p>
    </div>
  </div>
</template>

<script>
import CryptoJS from 'crypto-js'

export default {
  data() {
    return {
      selectedFile: null,
      uploadStatus: '',
      transcriptionResult: '', // 新增：存储识别结果
      isLoadingTranscription: false // 新增：识别加载状态
    }
  },
  // 移除 created 钩子中的预签名URL获取逻辑
  // 改为在 uploadAudio 方法中获取
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
          await this.transcribeAudio(urlData.object_name)
        } else {
          if (!urlData.url) {
            throw new Error('无效的预签名URL')
          }

          this.uploadStatus = '正在上传文件...'
          const response = await fetch(urlData.url, {
            method: 'PUT',
            body: this.selectedFile,
            headers: {
              'Content-Type': this.selectedFile.type
            }
          })

          if (response.ok) {
            this.uploadStatus = '文件上传成功! 开始识别...'
            await this.transcribeAudio(urlData.object_name)
          } else {
            const errorText = await response.text()
            throw new Error(`上传失败，状态码: ${response.status}, 错误: ${errorText}`)
          }
        }
      } catch (error) {
        console.error('上传或识别错误:', error)
        this.uploadStatus = '处理失败: ' + error.message
        this.isLoadingTranscription = false // 出错时停止加载
      }
    }, // 在 uploadAudio 方法后添加逗号
    async transcribeAudio(objectName) {
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
            model: 'gemini-2.0-flash-thinking'
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
            this.transcriptionResult += chunk
          }
        }

        this.uploadStatus = '识别完成!'
      } catch (error) {
        console.error('识别错误:', error)
        this.uploadStatus = '识别失败: ' + error.message
        this.transcriptionResult = '识别出错'
      } finally {
        this.isLoadingTranscription = false
      }
    } // transcribeAudio 方法结束
  }, // methods 对象结束
// 这部分代码已被移入上面的 REPLACE 块中，此处删除
}
</script>

<style scoped>
.upload-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}

input[type="file"] {
  margin: 20px 0;
  display: block;
}

button {
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #3aa876;
}

.loading {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.transcription-result {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.transcription-result h2 {
  margin-top: 0;
  font-size: 1.1em;
  color: #333;
}

.transcription-result p {
  white-space: pre-wrap; /* 保留换行和空格 */
  word-wrap: break-word;
}
</style>