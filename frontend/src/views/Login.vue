<template>
  <div class="login-container">
    <div class="login-card">
      <h1>jlo - Just Logs</h1>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Enter username"
            required
          />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter password"
            required
          />
        </div>
        <button type="submit" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
      <div class="default-creds">
        <small>Default credentials: admin / admin</small>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../services/api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const username = ref('')
    const password = ref('')
    const loading = ref(false)
    const error = ref('')

    const handleLogin = async () => {
      loading.value = true
      error.value = ''

      try {
        await login(username.value, password.value)
        router.push('/')
      } catch (err) {
        error.value = err.response?.data?.detail || 'Login failed'
      } finally {
        loading.value = false
      }
    }

    return {
      username,
      password,
      loading,
      error,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-primary);
}

.login-card {
  background: var(--bg-card);
  padding: 2rem;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border-color);
}

h1 {
  text-align: center;
  color: var(--text-primary);
  margin-bottom: 2rem;
  font-size: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--input-border);
  border-radius: 5px;
  font-size: 1rem;
  transition: border-color 0.3s;
  background: var(--input-bg);
  color: var(--text-primary);
}

input:focus {
  outline: none;
  border-color: var(--input-focus);
}

button {
  width: 100%;
  padding: 0.75rem;
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

button:hover:not(:disabled) {
  background: var(--btn-primary-hover);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: var(--color-danger);
  color: var(--text-on-danger);
  border-radius: 5px;
  text-align: center;
  opacity: 0.9;
}

.default-creds {
  margin-top: 1rem;
  text-align: center;
  color: var(--text-muted);
}
</style>
