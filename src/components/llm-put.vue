<template>
  <el-input
    v-model="localValue"
    type="textarea"
    :rows="rows"
    :placeholder="placeholder"
    :resize="resize"
    :style="{ width: '100%' }"
  />
</template>

<script>
export default {
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    rows: {
      type: Number,
      default: 13
    },
    placeholder: {
      type: String,
      default: ''
    },
    resize: {
      type: String,
      default: 'none' 
    }
  },
  computed: {
    localValue: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  }
};
</script>
