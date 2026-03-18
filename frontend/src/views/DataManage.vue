<script setup lang="ts">
import TaskParamsManage from './TaskParamsManage.vue'
</script>

<template>
  <div class="manage-page">
    <h1>数据管理</h1>
    <TaskParamsManage :show-title="false" />
  </div>
</template>

<style scoped>
.manage-page h1 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #1a1a2e;
}
</style>
