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
  color: #a1a1aa;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.selector-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #3a3a4a;
  border-radius: 8px;
  background: #2a2a3a;
  color: #e0e0e0;
  font-size: 14px;
}

.selector-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.18);
}
</style>
