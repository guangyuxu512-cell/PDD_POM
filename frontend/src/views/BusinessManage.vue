<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BatchExecute from './BatchExecute.vue'
import FlowManage from './FlowManage.vue'
import ScheduleManage from './ScheduleManage.vue'

type TabKey = 'flow' | 'execute' | 'schedule'

const route = useRoute()
const router = useRouter()

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'flow', label: '流程管理' },
  { key: 'execute', label: '批量执行' },
  { key: 'schedule', label: '定时任务' },
]

function normalizeTabKey(value: unknown): TabKey {
  const text = String(value || '').trim()
  return tabs.some((tab) => tab.key === text) ? (text as TabKey) : 'flow'
}

const activeTab = computed<TabKey>(() => normalizeTabKey(route.query.tab))

function switchTab(tab: TabKey) {
  void router.replace({ path: '/business', query: { tab } })
}
</script>

<template>
  <div class="manage-page">
    <h1>业务管理</h1>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <FlowManage v-if="activeTab === 'flow'" :show-title="false" />
      <BatchExecute v-else-if="activeTab === 'execute'" :show-title="false" />
      <ScheduleManage v-else :show-title="false" />
    </div>
  </div>
</template>

<style scoped>
.manage-page h1 {
  font-size: 28px;
  margin-bottom: 20px;
  color: #1a1a2e;
}

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 24px;
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: none;
  font-size: 15px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #1a1a2e;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-content {
  min-height: 0;
}
</style>
