<template>
  <el-row justify="center">
    <el-col :xs="20" :sm="20" :md="20" :lg="10">
      <el-checkbox-group :modelValue="modelValue" @update:modelValue="emitModelUpdate">
        <el-row>
          <el-col :xs="12" :sm="8" :md="6" :lg="6" v-for="model in models" :key="model.value">
            <el-checkbox :label="model.label" :value="model.value">
            </el-checkbox>
          </el-col>
        </el-row>
      </el-checkbox-group>
    </el-col>
    <el-col :xs="4" :sm="4" :md="2" :lg="2" class="button-container">
      <el-button @click="emitExecute">执行</el-button>
      <el-switch
        :modelValue="isSixTests"
        @update:modelValue="emitSixTestsUpdate"
        inline-prompt
        active-text="6次测试"
        inactive-text="单次测试"
      />
    </el-col>
  </el-row>
</template>

<script setup>
const props = defineProps({
  models: Array, // 可用模型列表 [{ label: '...', value: '...' }]
  modelValue: Array, // 对应 App.vue 中的 modelList (v-model)
  isSixTests: Boolean // 对应 App.vue 中的 isSixTests (v-model)
});

const emit = defineEmits(['update:modelValue', 'update:isSixTests', 'execute']);

const emitModelUpdate = (value) => {
  emit('update:modelValue', value);
};

const emitSixTestsUpdate = (value) => {
  emit('update:isSixTests', value);
};

const emitExecute = () => {
  emit('execute');
};
</script>

<style scoped>
.button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px; /* 在按钮和开关之间添加一些间距 */
}
</style>