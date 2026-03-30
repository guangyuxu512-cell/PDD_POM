<script setup lang="ts">
interface Props {
  show: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}

withDefaults(defineProps<Props>(), {
  confirmText: '确认',
  cancelText: '取消',
  type: 'warning'
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click="emit('cancel')">
      <div class="confirm-container" @click.stop>
        <div class="confirm-icon" :class="type">
          <span v-if="type === 'danger'">⚠️</span>
          <span v-else-if="type === 'warning'">⚠️</span>
          <span v-else>ℹ️</span>
        </div>
        <h3>{{ title }}</h3>
        <p>{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn btn-secondary" @click="emit('cancel')">
            {{ cancelText }}
          </button>
          <button class="btn" :class="`btn-${type}`" @click="emit('confirm')">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-container {
  background: #16213e;
  border-radius: 8px;
  padding: 32px;
  width: 400px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-container h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #e0e0e0;
}

.confirm-container p {
  margin: 0 0 24px 0;
  color: #a0a0a0;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #0f3460;
  color: #e0e0e0;
}

.btn-secondary:hover {
  background: #1a4d7a;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover {
  background: #d97706;
}

.btn-info {
  background: #3b82f6;
  color: white;
}

.btn-info:hover {
  background: #2563eb;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .confirm-container,
.modal-leave-active .confirm-container {
  transition: transform 0.3s ease;
}

.modal-enter-from .confirm-container,
.modal-leave-to .confirm-container {
  transform: scale(0.9);
}
</style>
