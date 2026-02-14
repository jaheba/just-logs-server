<template>
  <transition-group name="toast" tag="div" class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast"
      :class="`toast-${toast.type}`"
      @click="removeToast(toast.id)"
    >
      <div class="toast-icon">
        <span v-if="toast.type === 'success'">✓</span>
        <span v-else-if="toast.type === 'error'">✕</span>
        <span v-else-if="toast.type === 'warning'">⚠</span>
        <span v-else>ℹ</span>
      </div>
      <div class="toast-content">
        <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
        <div class="toast-message">{{ toast.message }}</div>
      </div>
      <button class="toast-close" @click.stop="removeToast(toast.id)">
        &times;
      </button>
    </div>
  </transition-group>
</template>

<script>
import { useToast } from '../composables/useToast'

export default {
  name: 'Toast',
  setup() {
    const { toasts, removeToast } = useToast()

    return {
      toasts,
      removeToast
    }
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 300px;
  max-width: 400px;
  pointer-events: auto;
  cursor: pointer;
  border-left: 4px solid;
}

.toast-success {
  border-left-color: var(--color-success);
}

.toast-error {
  border-left-color: var(--color-danger);
}

.toast-warning {
  border-left-color: var(--color-warning);
}

.toast-info {
  border-left-color: var(--color-info);
}

.toast-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.875rem;
}

.toast-success .toast-icon {
  background: var(--color-success);
  color: var(--text-on-success);
}

.toast-error .toast-icon {
  background: var(--color-danger);
  color: var(--text-on-danger);
}

.toast-warning .toast-icon {
  background: var(--color-warning);
  color: var(--text-on-warning);
}

.toast-info .toast-icon {
  background: var(--color-info);
  color: var(--text-on-info);
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  color: var(--text-primary, #333);
  margin-bottom: 0.25rem;
  font-size: 0.9375rem;
}

.toast-message {
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
  line-height: 1.4;
}

.toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary, #999);
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.toast-close:hover {
  background: var(--bg-hover, #f0f0f0);
  color: var(--text-primary, #333);
}

/* Animations */
.toast-enter-active {
  animation: slideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: slideOut 0.3s ease-in;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

@media (max-width: 640px) {
  .toast-container {
    left: 1rem;
    right: 1rem;
  }

  .toast {
    min-width: 0;
    max-width: none;
  }
}
</style>
