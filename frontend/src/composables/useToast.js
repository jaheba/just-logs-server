import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

export function useToast() {
  const addToast = ({ message, title, type = 'info', duration = 3000 }) => {
    const id = ++toastId
    toasts.value.push({ id, message, title, type })

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  const removeToast = (id) => {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const success = (message, title = '', duration = 3000) =>
    addToast({ message, title, type: 'success', duration })

  const error = (message, title = '', duration = 5000) =>
    addToast({ message, title, type: 'error', duration })

  const warning = (message, title = '', duration = 4000) =>
    addToast({ message, title, type: 'warning', duration })

  const info = (message, title = '', duration = 3000) =>
    addToast({ message, title, type: 'info', duration })

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info
  }
}
