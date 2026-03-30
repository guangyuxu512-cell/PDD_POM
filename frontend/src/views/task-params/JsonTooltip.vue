<script setup lang="ts">
import { computed } from 'vue'

import { useTaskParamsContext } from './useTaskParamsStore'

function useJsonTooltip() {
  const store = useTaskParamsContext()

  return {
    jsonTooltip: computed(() => store.jsonTooltip),
    keepJsonTooltipOpen: store.keepJsonTooltipOpen,
    hideJsonTooltip: store.hideJsonTooltip,
  }
}

const { jsonTooltip, keepJsonTooltipOpen, hideJsonTooltip } = useJsonTooltip()
</script>

<template>
  <Teleport to="body">
    <div
      v-if="jsonTooltip.visible"
      class="json-tooltip-panel"
      :style="{
        left: `${jsonTooltip.left}px`,
        top: `${jsonTooltip.top}px`,
        width: `${jsonTooltip.width}px`,
      }"
      @mouseenter="keepJsonTooltipOpen"
      @mouseleave="hideJsonTooltip"
    >
      <pre>{{ jsonTooltip.content }}</pre>
    </div>
  </Teleport>
</template>

<style scoped>
.json-tooltip-panel {
  position: fixed;
  z-index: 3000;
  max-width: 500px;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: rgba(15, 23, 42, 0.96);
  color: #e5eefc;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: var(--shadow-md);
}

.json-tooltip-panel pre {
  margin: 0;
  max-height: min(60vh, 420px);
  overflow: auto;
  font-size: var(--font-size-sm);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

