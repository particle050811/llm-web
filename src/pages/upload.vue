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
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedFile: null,
      uploadStatus: ''
    }
  },
  // 移除 created 钩子中的预签名URL获取逻辑
  // 改为在 uploadAudio 方法中获取
  methods: {
    handleFileChange(event) {
      this.selectedFile = event.target.files[0]
    },
    async uploadAudio() {
      if (!this.selectedFile) {
        this.uploadStatus = '请先选择音频文件'
        return
      }

      try {
        // 1. 获取带Content-Type的预签名URL
        const urlResponse = await fetch(`/api/generate-audio-url?contentType=${encodeURIComponent(this.selectedFile.type)}`)
        if (!urlResponse.ok) {
          throw new Error(`获取上传链接失败，状态码: ${urlResponse.status}`)
        }
        const urlData = await urlResponse.json()
        if (!urlData.url) {
          throw new Error('无效的预签名URL')
        }

        // 2. 执行上传
        const response = await fetch(urlData.url, {
          method: 'PUT',
          body: this.selectedFile,
          headers: {
            'Content-Type': this.selectedFile.type
          }
        })

        if (response.ok) {
          this.uploadStatus = '音频上传成功!'
        } else {
          const errorText = await response.text()
          throw new Error(`上传失败，状态码: ${response.status}, 错误: ${errorText}`)
        }
      } catch (error) {
        console.error('上传错误:', error)
        this.uploadStatus = '上传失败: ' + error.message
      }
    }
  }
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
</style>