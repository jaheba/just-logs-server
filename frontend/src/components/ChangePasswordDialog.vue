<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal">
      <div class="modal-header">
        <h3>Change Password</h3>
        <button @click="handleClose" class="close-btn">&times;</button>
      </div>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="currentPassword">Current Password *</label>
          <div class="password-input">
            <input
              id="currentPassword"
              v-model="form.currentPassword"
              :type="showCurrentPassword ? 'text' : 'password'"
              required
              placeholder="Enter current password"
              autocomplete="current-password"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showCurrentPassword = !showCurrentPassword"
              tabindex="-1"
            >
              <font-awesome-icon :icon="showCurrentPassword ? 'eye-slash' : 'eye'" />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="newPassword">New Password *</label>
          <div class="password-input">
            <input
              id="newPassword"
              v-model="form.newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Enter new password (min 6 characters)"
              autocomplete="new-password"
              @input="validatePassword"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showNewPassword = !showNewPassword"
              tabindex="-1"
            >
              <font-awesome-icon :icon="showNewPassword ? 'eye-slash' : 'eye'" />
            </button>
          </div>
          <div v-if="passwordStrength" class="password-strength">
            <div class="strength-bar">
              <div
                class="strength-fill"
                :class="`strength-${passwordStrength.level}`"
                :style="{ width: `${passwordStrength.percent}%` }"
              ></div>
            </div>
            <span class="strength-label" :class="`strength-${passwordStrength.level}`">
              {{ passwordStrength.text }}
            </span>
          </div>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm New Password *</label>
          <div class="password-input">
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="Confirm new password"
              autocomplete="new-password"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showConfirmPassword = !showConfirmPassword"
              tabindex="-1"
            >
              <font-awesome-icon :icon="showConfirmPassword ? 'eye-slash' : 'eye'" />
            </button>
          </div>
          <div v-if="form.confirmPassword && form.newPassword !== form.confirmPassword" class="error-hint">
            Passwords do not match
          </div>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-actions">
          <button
            type="submit"
            class="btn-primary"
            :disabled="saving || !isFormValid"
          >
            {{ saving ? 'Changing...' : 'Change Password' }}
          </button>
          <button type="button" @click="handleClose" class="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { changePassword } from '../services/api'

export default {
  name: 'ChangePasswordDialog',
  props: {
    show: {
      type: Boolean,
      required: true
    }
  },
  emits: ['close', 'success'],
  setup(props, { emit }) {
    const form = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    const showCurrentPassword = ref(false)
    const showNewPassword = ref(false)
    const showConfirmPassword = ref(false)
    const saving = ref(false)
    const error = ref('')
    const passwordStrength = ref(null)

    const isFormValid = computed(() => {
      return (
        form.value.currentPassword &&
        form.value.newPassword &&
        form.value.confirmPassword &&
        form.value.newPassword === form.value.confirmPassword &&
        form.value.newPassword.length >= 6
      )
    })

    const validatePassword = () => {
      const password = form.value.newPassword
      if (!password) {
        passwordStrength.value = null
        return
      }

      let strength = 0
      let text = ''
      let level = ''

      // Length check
      if (password.length >= 8) strength += 20
      if (password.length >= 12) strength += 10

      // Character variety
      if (/[a-z]/.test(password)) strength += 15
      if (/[A-Z]/.test(password)) strength += 15
      if (/[0-9]/.test(password)) strength += 20
      if (/[^a-zA-Z0-9]/.test(password)) strength += 20

      if (strength < 40) {
        text = 'Weak'
        level = 'weak'
      } else if (strength < 70) {
        text = 'Fair'
        level = 'fair'
      } else if (strength < 90) {
        text = 'Good'
        level = 'good'
      } else {
        text = 'Strong'
        level = 'strong'
      }

      passwordStrength.value = { percent: strength, text, level }
    }

    const handleSubmit = async () => {
      if (!isFormValid.value) return

      saving.value = true
      error.value = ''

      try {
        await changePassword({
          current_password: form.value.currentPassword,
          new_password: form.value.newPassword
        })

        emit('success')
        handleClose()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to change password'
      } finally {
        saving.value = false
      }
    }

    const handleClose = () => {
      form.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      showCurrentPassword.value = false
      showNewPassword.value = false
      showConfirmPassword.value = false
      error.value = ''
      passwordStrength.value = null
      emit('close')
    }

    return {
      form,
      showCurrentPassword,
      showNewPassword,
      showConfirmPassword,
      saving,
      error,
      passwordStrength,
      isFormValid,
      validatePassword,
      handleSubmit,
      handleClose
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal {
  background: var(--bg-card, white);
  border-radius: 12px;
  padding: 0;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary, #333);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.75rem;
  color: var(--text-secondary, #666);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--bg-hover, #f0f0f0);
  color: var(--text-primary, #333);
}

form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary, #333);
  font-size: 0.875rem;
}

.password-input {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input input {
  width: 100%;
  padding: 0.625rem 2.5rem 0.625rem 0.75rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
  transition: all 0.2s;
}

.password-input input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.toggle-password {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  opacity: 0.6;
  transition: opacity 0.2s;
  color: var(--color-primary, #667eea);
  font-weight: 600;
}

.toggle-password:hover {
  opacity: 1;
}

.password-strength {
  margin-top: 0.5rem;
}

.strength-bar {
  height: 4px;
  background: var(--bg-secondary, #f0f0f0);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
}

.strength-fill.strength-weak {
  background: var(--color-danger);
}

.strength-fill.strength-fair {
  background: var(--color-warning);
}

.strength-fill.strength-good {
  background: var(--color-success);
}

.strength-fill.strength-strong {
  background: var(--color-info);
}

.strength-label {
  font-size: 0.75rem;
  font-weight: 600;
}

.strength-label.strength-weak {
  color: var(--color-danger);
}

.strength-label.strength-fair {
  color: var(--color-warning);
}

.strength-label.strength-good {
  color: var(--color-success);
}

.strength-label.strength-strong {
  color: var(--color-info);
}

.error-hint {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-danger);
}

.error-message {
  padding: 0.75rem;
  background: var(--color-danger);
  color: #ffffff;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  opacity: 0.9;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9375rem;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--btn-secondary-bg);
  color: var(--btn-secondary-text);
}

.btn-secondary:hover {
  background: var(--btn-secondary-hover);
}

@media (max-width: 640px) {
  .modal {
    width: 95%;
    max-height: 95vh;
  }

  .modal-header {
    padding: 1rem;
  }

  form {
    padding: 1rem;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
