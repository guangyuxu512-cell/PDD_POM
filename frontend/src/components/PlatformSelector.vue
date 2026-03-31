<script setup lang="ts">
import { onMounted } from 'vue'

import { usePlatformStore } from '../stores/platform'

const store = usePlatformStore()

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement
  store.setPlatform(target.value)
}

onMounted(() => {
  void store.loadPlatforms()
})
</script>

<template>
  <div class="platform-selector">
    <label class="selector-label" for="platform-selector">当前平台</label>
    <select
      id="platform-selector"
      class="selector-input"
      :value="store.currentPlatform"
      @change="handleChange"
    >
      <option
        v-for="platform in store.platforms"
        :key="platform.id"
        :value="platform.id"
      >
        {{ platform.icon }} {{ platform.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.platform-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-label {
  font-size: 12px;
  color: #9fb3c8;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.selector-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #1a4d7a;
  border-radius: 8px;
  background: #0f3460;
  color: #e0e0e0;
  font-size: 14px;
}

.selector-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
}
</style>
