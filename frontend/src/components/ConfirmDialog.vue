<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { computed } from 'vue'

interface Props {
  show: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  confirmText: '确认',
  cancelText: '取消',
  type: 'warning'
})

const emit = defineEmits<{
  close: []
  confirm: []
  cancel: []
}>()

const iconToneClasses = computed(() => {
  if (props.type === 'danger') {
    return 'border-rose-200 bg-rose-50 text-rose-600'
  }

  if (props.type === 'warning') {
    return 'border-amber-200 bg-amber-50 text-amber-600'
  }

  return 'border-brand-200/50 bg-gray-50 text-gray-600'
})

const confirmButtonClasses = computed(() => {
  const baseClasses =
    'rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none'

  if (props.type === 'danger') {
    return `${baseClasses} bg-rose-600 text-white hover:bg-rose-700`
  }

  return `${baseClasses} bg-brand-900 text-white hover:bg-brand-700`
})

function handleClose() {
  emit('close')
  emit('cancel')
}
</script>

<template>
  <TransitionRoot :show="props.show" as="template">
    <Dialog class="relative z-50" @close="handleClose">
      <TransitionChild
        as="template"
        enter="ease-out duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-150"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="ease-out duration-200"
            enter-from="scale-95 opacity-0"
            enter-to="scale-100 opacity-100"
            leave="ease-in duration-150"
            leave-from="scale-100 opacity-100"
            leave-to="scale-95 opacity-0"
          >
            <DialogPanel
              class="confirm-container w-full max-w-md rounded-md border border-brand-200/50 bg-white shadow-lg"
            >
              <div class="flex flex-col gap-4 px-5 py-5">
                <div
                  :class="[
                    'mx-auto flex h-12 w-12 items-center justify-center rounded-full border text-lg font-semibold',
                    iconToneClasses,
                  ]"
                >
                  <span>{{ props.type === 'info' ? 'i' : '!' }}</span>
                </div>

                <div class="space-y-2 text-center">
                  <DialogTitle class="text-lg font-semibold text-gray-900">
                    {{ props.title }}
                  </DialogTitle>
                  <p class="text-sm leading-6 text-gray-600">
                    {{ props.message }}
                  </p>
                </div>
              </div>

              <div class="flex items-center justify-center gap-2 border-t border-gray-100 px-5 py-3">
                <button
                  type="button"
                  class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                  @click="handleClose"
                >
                  {{ props.cancelText }}
                </button>
                <button type="button" :class="confirmButtonClasses" @click="emit('confirm')">
                  {{ props.confirmText }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
