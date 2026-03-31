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
      class="fixed z-50 max-w-md rounded-md border border-brand-200/50 bg-white p-3 shadow-lg"
      :style="{
        left: `${jsonTooltip.left}px`,
        top: `${jsonTooltip.top}px`,
        width: `${jsonTooltip.width}px`,
      }"
      @mouseenter="keepJsonTooltipOpen"
      @mouseleave="hideJsonTooltip"
    >
      <pre class="max-h-64 overflow-auto whitespace-pre-wrap break-words text-xs text-gray-700">{{ jsonTooltip.content }}</pre>
    </div>
  </Teleport>
</template>
