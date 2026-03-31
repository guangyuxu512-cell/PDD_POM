<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'

interface Props {
  show: boolean
  title?: string
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  width: '500px'
})

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <TransitionRoot :show="props.show" as="template">
    <Dialog class="relative z-50" @close="emit('close')">
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
              class="modal-container flex max-h-[90vh] w-full flex-col overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg"
              :style="{ maxWidth: props.width || '500px' }"
            >
              <div
                v-if="props.title"
                class="modal-header flex items-center justify-between border-b border-gray-100 px-5 py-4"
              >
                <DialogTitle class="text-lg font-semibold text-gray-900">
                  {{ props.title }}
                </DialogTitle>
                <button
                  type="button"
                  class="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                  @click="emit('close')"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div class="modal-body flex-1 overflow-y-auto px-5 py-4 text-sm text-gray-600">
                <slot />
              </div>

              <div
                v-if="$slots.footer"
                class="modal-footer flex items-center justify-end gap-2 border-t border-gray-100 px-5 py-3"
              >
                <slot name="footer" />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
