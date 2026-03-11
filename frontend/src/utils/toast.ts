import { ref } from 'vue'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface ToastItem {
  id: number
  message: string
  type: ToastType
}

export const toasts = ref<ToastItem[]>([])
let nextId = 0

export const toast = {
  show(message: string, type: ToastType = 'info') {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 3000)
  },
  success(message: string) {
    this.show(message, 'success')
  },
  error(message: string) {
    this.show(message, 'error')
  },
  warning(message: string) {
    this.show(message, 'warning')
  },
  info(message: string) {
    this.show(message, 'info')
  }
}
