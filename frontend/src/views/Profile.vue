<template>
  <div class="profile-page">
    <Toast />
    
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <h2>My Profile</h2>
          <p class="subtitle">Manage your account settings</p>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading profile...</p>
      </div>

      <div v-else class="profile-content">
        <!-- Profile Card -->
        <div class="profile-card">
          <div class="profile-header">
            <div class="profile-avatar-large">
              {{ getUserInitials() }}
            </div>
            <div class="profile-info">
              <h3>{{ user.full_name || user.username }}</h3>
              <p class="profile-username">@{{ user.username }}</p>
              <span class="role-badge" :class="`role-${user.role}`">
                {{ formatRole(user.role) }}
              </span>
            </div>
          </div>

          <div class="profile-stats">
            <div class="stat-item">
              <div class="stat-label">Role</div>
              <div class="stat-value">{{ formatRole(user.role) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Status</div>
              <div class="stat-value" :class="user.is_active ? 'text-success' : 'text-danger'">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Last Login</div>
              <div class="stat-value">{{ formatDate(user.last_login) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">Member Since</div>
              <div class="stat-value">{{ formatShortDate(user.created_at) }}</div>
            </div>
          </div>
        </div>

        <!-- Edit Profile Section -->
        <div class="section-card">
          <div class="section-header">
            <h3>Personal Information</h3>
            <button v-if="!editing" @click="startEditing" class="btn-secondary btn-small">
              <span class="btn-icon">✏️</span>
              Edit
            </button>
          </div>

          <form v-if="editing" @submit.prevent="handleSave" class="profile-form">
            <div class="form-row">
              <div class="form-group">
                <label>Username</label>
                <input
                  v-model="form.username"
                  type="text"
                  disabled
                  class="input-disabled"
                />
                <span class="field-hint">Username cannot be changed</span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input
                  v-model="form.full_name"
                  type="text"
                  placeholder="Enter your full name"
                  maxlength="100"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Email</label>
                <input
                  v-model="form.email"
                  type="email"
                  placeholder="your.email@example.com"
                  maxlength="255"
                />
              </div>
            </div>

            <div v-if="error" class="error-message">
              <span class="error-icon">⚠️</span>
              {{ error }}
            </div>

            <div class="form-actions">
              <button type="submit" class="btn-primary" :disabled="saving">
                <span v-if="saving" class="spinner-small"></span>
                {{ saving ? 'Saving...' : 'Save Changes' }}
              </button>
              <button type="button" @click="cancelEditing" class="btn-secondary">
                Cancel
              </button>
            </div>
          </form>

          <div v-else class="profile-details">
            <div class="detail-row">
              <span class="detail-label">Username</span>
              <span class="detail-value">{{ user.username }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Full Name</span>
              <span class="detail-value">{{ user.full_name || 'Not set' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Email</span>
              <span class="detail-value">{{ user.email || 'Not set' }}</span>
            </div>
          </div>
        </div>

        <!-- Security Section -->
        <div class="section-card">
          <div class="section-header">
            <h3>Security</h3>
          </div>

          <div class="security-content">
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">Password</div>
                <div class="security-description">
                  Last changed: {{ user.last_login ? formatDate(user.last_login) : 'Never' }}
                </div>
              </div>
              <button @click="showChangePasswordDialog = true" class="btn-secondary btn-small">
                Change Password
              </button>
            </div>
          </div>
        </div>

        <!-- Account Information -->
        <div class="section-card">
          <div class="section-header">
            <h3>Account Information</h3>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <div class="info-label">Account ID</div>
              <div class="info-value">#{{ user.id }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">Role</div>
              <div class="info-value">{{ formatRole(user.role) }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">Account Status</div>
              <div class="info-value">
                <span class="status-badge" :class="user.is_active ? 'status-active' : 'status-inactive'">
                  <span class="status-dot"></span>
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
            <div class="info-item">
              <div class="info-label">Created</div>
              <div class="info-value">{{ new Date(user.created_at).toLocaleString() }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Change Password Dialog -->
    <ChangePasswordDialog 
      :show="showChangePasswordDialog" 
      @close="showChangePasswordDialog = false"
      @success="handlePasswordChanged"
    />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getCurrentUser, updateUser } from '../services/api'
import { useToast } from '../composables/useToast'
import { useRouter } from 'vue-router'
import Toast from '../components/Toast.vue'
import ChangePasswordDialog from '../components/ChangePasswordDialog.vue'

export default {
  name: 'Profile',
  components: {
    Toast,
    ChangePasswordDialog
  },
  setup() {
    const router = useRouter()
    const { success, error: showError } = useToast()
    
    const user = ref({})
    const loading = ref(false)
    const editing = ref(false)
    const saving = ref(false)
    const error = ref('')
    const showChangePasswordDialog = ref(false)

    const form = ref({
      username: '',
      full_name: '',
      email: ''
    })

    const fetchUser = async () => {
      loading.value = true
      try {
        const response = await getCurrentUser()
        user.value = response.data
      } catch (err) {
        console.error('Failed to fetch user:', err)
        showError('Failed to load profile')
        router.push('/')
      } finally {
        loading.value = false
      }
    }

    const getUserInitials = () => {
      if (!user.value) return 'U'
      
      const name = user.value.full_name || user.value.username
      const parts = name.split(' ')
      
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      }
      
      return name.substring(0, 2).toUpperCase()
    }

    const formatRole = (role) => {
      const roles = {
        admin: 'Administrator',
        editor: 'Editor',
        viewer: 'Viewer'
      }
      return roles[role] || role
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
      if (days === 0) return 'Today'
      if (days === 1) return 'Yesterday'
      if (days < 7) return `${days} days ago`
      if (days < 30) return `${Math.floor(days / 7)} weeks ago`
      if (days < 365) return `${Math.floor(days / 30)} months ago`
      return date.toLocaleDateString()
    }

    const formatShortDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }

    const startEditing = () => {
      form.value = {
        username: user.value.username,
        full_name: user.value.full_name || '',
        email: user.value.email || ''
      }
      editing.value = true
      error.value = ''
    }

    const cancelEditing = () => {
      editing.value = false
      error.value = ''
    }

    const handleSave = async () => {
      saving.value = true
      error.value = ''

      try {
        const updateData = {
          full_name: form.value.full_name || null,
          email: form.value.email || null
        }
        
        await updateUser(user.value.id, updateData)
        await fetchUser()
        editing.value = false
        success('Profile updated successfully')
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to update profile'
        showError(error.value)
      } finally {
        saving.value = false
      }
    }

    const handlePasswordChanged = () => {
      success('Password changed successfully')
    }

    onMounted(() => {
      fetchUser()
    })

    return {
      user,
      loading,
      editing,
      saving,
      error,
      form,
      showChangePasswordDialog,
      getUserInitials,
      formatRole,
      formatDate,
      formatShortDate,
      startEditing,
      cancelEditing,
      handleSave,
      handlePasswordChanged
    }
  }
}
</script>

<style scoped>
.profile-page {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  min-height: 100vh;
}

.container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  margin-bottom: 1rem;
}

.page-header h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.75rem;
  color: var(--text-primary, #333);
  font-weight: 700;
}

.subtitle {
  margin: 0;
  color: var(--text-secondary, #666);
  font-size: 0.9375rem;
}

/* Loading */
.loading {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color, #e0e0e0);
  border-top-color: var(--color-primary, #667eea);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--text-secondary, #666);
}

/* Profile Content */
.profile-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Profile Card */
.profile-card {
  background: var(--color-primary);
  border-radius: 16px;
  padding: 2rem;
  color: var(--text-on-primary);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.profile-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-accent);
  color: var(--text-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  flex-shrink: 0;
  border: 3px solid var(--border-color);
}

.profile-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.profile-username {
  margin: 0 0 0.75rem 0;
  opacity: 0.9;
  font-size: 0.9375rem;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.8125rem;
  opacity: 0.8;
  font-weight: 500;
}

.stat-value {
  font-size: 1.125rem;
  font-weight: 600;
}

/* Section Cards */
.section-card {
  background: var(--bg-card, white);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--border-color, #e0e0e0);
}

.section-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary, #333);
  font-weight: 600;
}

/* Profile Details */
.profile-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
}

.detail-label {
  font-weight: 600;
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
}

.detail-value {
  color: var(--text-primary, #333);
  font-size: 0.9375rem;
}

/* Form */
.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--text-primary, #333);
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-disabled {
  background: var(--bg-secondary, #f0f0f0);
  cursor: not-allowed;
  opacity: 0.6;
}

.field-hint {
  margin-top: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary, #999);
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

/* Security Section */
.security-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
}

.security-info {
  flex: 1;
}

.security-title {
  font-weight: 600;
  color: var(--text-primary, #333);
  margin-bottom: 0.25rem;
}

.security-description {
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
}

.info-label {
  font-size: 0.8125rem;
  color: var(--text-secondary, #666);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.info-value {
  font-size: 0.9375rem;
  color: var(--text-primary, #333);
  font-weight: 600;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.8125rem;
}

.btn-primary {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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

.btn-icon {
  font-size: 1rem;
}

/* Role Badge */
.role-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.role-admin {
  background: var(--bg-tertiary);
  color: var(--text-on-primary);
  font-weight: 600;
}

.role-editor {
  background: var(--bg-tertiary);
  color: var(--text-on-primary);
  font-weight: 600;
}

.role-viewer {
  background: var(--bg-tertiary);
  color: var(--text-on-primary);
  font-weight: 600;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.status-badge.status-active {
  background: var(--color-success);
  color: var(--text-on-success);
}

.status-badge.status-inactive {
  background: var(--color-danger);
  color: var(--text-on-danger);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.text-success {
  color: #2e7d32;
}

.text-danger {
  color: #c62828;
}

/* Error Message */
.error-message {
  padding: 1rem 1.5rem;
  background: var(--color-danger);
  color: var(--text-on-danger);
  border-radius: 8px;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  opacity: 0.9;
}

.error-icon {
  font-size: 1.25rem;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-page {
    padding: 1rem;
  }

  .profile-header {
    flex-direction: column;
    text-align: center;
    align-items: center;
  }

  .profile-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .form-actions {
    flex-direction: column;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
