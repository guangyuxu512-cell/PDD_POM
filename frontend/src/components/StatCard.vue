<script setup lang="ts">
interface Props {
  icon: string
  label: string
  value: number
  color: string
}

defineProps<Props>()
</script>

<template>
  <div class="rounded-md border border-brand-200/50 bg-white p-4 shadow-sm">
    <div class="flex items-start justify-between gap-3">
      <div class="space-y-2">
        <p class="text-xs font-medium uppercase tracking-wider text-gray-500">
          {{ label }}
        </p>
        <p class="font-mono text-2xl font-semibold text-gray-900">
          {{ value }}
        </p>
      </div>
      <span class="flex h-10 w-10 items-center justify-center rounded-md bg-gray-100 text-lg text-gray-500">
        {{ icon }}
      </span>
    </div>
  </div>
</template>
