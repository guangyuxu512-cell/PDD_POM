<script setup lang="ts">
import {
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { toasts } from '../utils/toast'

const toneClasses = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  error: 'border-rose-200 bg-rose-50 text-rose-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  info: 'border-gray-200 bg-gray-50 text-gray-800',
} as const

const iconLabels = {
  success: '✓',
  error: '✕',
  warning: '!',
  info: 'i',
} as const
</script>

<template>
  <Teleport to="body">
    <div class="fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3" aria-live="polite">
      <TransitionRoot
        v-for="t in toasts"
        :key="t.id"
        appear
        :show="true"
        as="template"
      >
        <TransitionChild
          as="template"
          enter="transform ease-out duration-200"
          enter-from="translate-x-4 opacity-0"
          enter-to="translate-x-0 opacity-100"
          leave="transform ease-in duration-150"
          leave-from="translate-x-0 opacity-100"
          leave-to="translate-x-4 opacity-0"
        >
          <div
            :class="[
              'pointer-events-auto flex items-start gap-3 rounded-md border px-4 py-3 shadow-lg',
              toneClasses[t.type],
            ]"
            role="status"
          >
            <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full text-sm font-semibold">
              {{ iconLabels[t.type] }}
            </span>
            <span class="text-sm leading-6">{{ t.message }}</span>
          </div>
        </TransitionChild>
      </TransitionRoot>
    </div>
  </Teleport>
</template>
