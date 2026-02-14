<template>
  <div class="users-page">
    <Toast />
    
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <h2>User Management</h2>
          <p class="subtitle">Manage users and their permissions</p>
        </div>
        <button @click="openCreateDialog" class="btn-primary">
          Create User
        </button>
      </div>

      <!-- Search and Filter -->
      <div class="controls">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by username, name, or email..."
            class="search-input"
          />
        </div>
        <div class="filters">
          <select v-model="filterRole" class="filter-select">
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="editor">Editor</option>
            <option value="viewer">Viewer</option>
          </select>
          <select v-model="filterStatus" class="filter-select">
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading users...</p>
      </div>

      <div v-else-if="filteredUsers.length === 0" class="no-data">
        <p>{{ searchQuery || filterRole || filterStatus ? 'No users match your filters' : 'No users found' }}</p>
        <button v-if="!searchQuery && !filterRole && !filterStatus" @click="openCreateDialog" class="btn-secondary">
          Create Your First User
        </button>
      </div>

      <div v-else class="users-table">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>
                <span class="username">{{ user.username }}</span>
              </td>
              <td>{{ user.full_name || '-' }}</td>
              <td>{{ user.email || '-' }}</td>
              <td>
                <span class="role-badge" :class="`role-${user.role}`">
                  {{ formatRole(user.role) }}
                </span>
              </td>
              <td>
                <span class="status-badge" :class="user.is_active ? 'status-active' : 'status-inactive'">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td>{{ formatDate(user.last_login) }}</td>
              <td>{{ formatShortDate(user.created_at) }}</td>
              <td class="actions">
                <button @click="openEditDialog(user)" class="btn-icon" title="Edit">
                  Edit
                </button>
                <button @click="openResetPasswordDialog(user)" class="btn-icon" title="Reset Password">
                  Reset
                </button>
                <button 
                  @click="handleDelete(user)" 
                  class="btn-icon btn-danger" 
                  :disabled="user.id === currentUserId"
                  :title="user.id === currentUserId ? 'Cannot delete yourself' : 'Delete'"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit User Dialog -->
    <div v-if="showUserDialog" class="modal-overlay" @click.self="closeUserDialog">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingUser ? 'Edit User' : 'Create New User' }}</h3>
          <button @click="closeUserDialog" class="close-btn">&times;</button>
        </div>
        
        <form @submit.prevent="handleSaveUser">
          <div class="modal-body">
            <div class="form-row" v-if="!editingUser">
              <div class="form-group">
                <label>Username *</label>
                <input
                  v-model="userForm.username"
                  type="text"
                  required
                  :disabled="editingUser"
                  placeholder="johndoe"
                  minlength="3"
                  maxlength="50"
                />
                <span class="field-hint">Unique identifier for login</span>
              </div>
            </div>

            <div class="form-row" v-if="!editingUser">
              <div class="form-group">
                <label>Password *</label>
                <input
                  v-model="userForm.password"
                  type="password"
                  required
                  minlength="6"
                  placeholder="Minimum 6 characters"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input
                  v-model="userForm.full_name"
                  type="text"
                  placeholder="John Doe"
                  maxlength="100"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Email</label>
                <input
                  v-model="userForm.email"
                  type="email"
                  placeholder="john@example.com"
                  maxlength="255"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Role *</label>
                <select v-model="userForm.role" required>
                  <option value="viewer">Viewer - Read-only access</option>
                  <option value="editor">Editor - Can manage apps and keys</option>
                  <option value="admin">Admin - Full system access</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group-checkbox">
                <label class="checkbox-label">
                  <input v-model="userForm.is_active" type="checkbox" />
                  Active account
                </label>
                <span class="field-hint">Inactive users cannot log in</span>
              </div>
            </div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div class="modal-footer">
            <button type="button" @click="closeUserDialog" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner-small"></span>
              {{ saving ? 'Saving...' : editingUser ? 'Update User' : 'Create User' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reset Password Dialog -->
    <div v-if="showResetPasswordDialog" class="modal-overlay" @click.self="closeResetPasswordDialog">
      <div class="modal modal-small">
        <div class="modal-header">
          <h3>Reset Password</h3>
          <button @click="closeResetPasswordDialog" class="close-btn">&times;</button>
        </div>
        
        <form @submit.prevent="handleResetPassword">
          <div class="modal-body">
            <p class="reset-info">
              Resetting password for <strong>{{ resetPasswordUser?.username }}</strong>
            </p>
            
            <div class="form-group">
              <label for="newPassword">New Password *</label>
              <input
                id="newPassword"
                v-model="resetPasswordForm.new_password"
                type="password"
                required
                minlength="6"
                placeholder="Enter new password (min 6 characters)"
              />
            </div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div class="modal-footer">
            <button type="button" @click="closeResetPasswordDialog" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner-small"></span>
              {{ saving ? 'Resetting...' : 'Reset Password' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  getCurrentUser
} from '../services/api'
import { useToast } from '../composables/useToast'
import Toast from '../components/Toast.vue'

export default {
  name: 'Users',
  components: {
    Toast
  },
  setup() {
    const { success, error: showError, warning } = useToast()
    
    const users = ref([])
    const loading = ref(false)
    const showUserDialog = ref(false)
    const showResetPasswordDialog = ref(false)
    const editingUser = ref(null)
    const resetPasswordUser = ref(null)
    const saving = ref(false)
    const error = ref('')
    const currentUserId = ref(null)
    const searchQuery = ref('')
    const filterRole = ref('')
    const filterStatus = ref('')

    const userForm = ref({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role: 'viewer',
      is_active: true
    })

    const resetPasswordForm = ref({
      new_password: ''
    })

    // Computed properties for statistics
    const activeUsers = computed(() => users.value.filter(u => u.is_active).length)
    const adminUsers = computed(() => users.value.filter(u => u.role === 'admin').length)
    const editorUsers = computed(() => users.value.filter(u => u.role === 'editor').length)

    // Filtered users based on search and filters
    const filteredUsers = computed(() => {
      return users.value.filter(user => {
        // Search filter
        if (searchQuery.value) {
          const query = searchQuery.value.toLowerCase()
          const matchesSearch = 
            user.username.toLowerCase().includes(query) ||
            (user.full_name && user.full_name.toLowerCase().includes(query)) ||
            (user.email && user.email.toLowerCase().includes(query))
          
          if (!matchesSearch) return false
        }

        // Role filter
        if (filterRole.value && user.role !== filterRole.value) {
          return false
        }

        // Status filter
        if (filterStatus.value) {
          const isActive = filterStatus.value === 'active'
          if (user.is_active !== isActive) return false
        }

        return true
      })
    })

    const fetchUsers = async () => {
      loading.value = true
      try {
        const response = await getUsers()
        users.value = response.data
      } catch (err) {
        console.error('Failed to fetch users:', err)
        showError('Failed to load users')
      } finally {
        loading.value = false
      }
    }

    const fetchCurrentUser = async () => {
      try {
        const response = await getCurrentUser()
        currentUserId.value = response.data.id
      } catch (err) {
        console.error('Failed to fetch current user:', err)
      }
    }

    const openCreateDialog = () => {
      editingUser.value = null
      userForm.value = {
        username: '',
        password: '',
        full_name: '',
        email: '',
        role: 'viewer',
        is_active: true
      }
      error.value = ''
      showUserDialog.value = true
    }

    const openEditDialog = (user) => {
      editingUser.value = user
      userForm.value = {
        username: user.username,
        full_name: user.full_name || '',
        email: user.email || '',
        role: user.role,
        is_active: user.is_active
      }
      error.value = ''
      showUserDialog.value = true
    }

    const closeUserDialog = () => {
      showUserDialog.value = false
      editingUser.value = null
      error.value = ''
    }

    const openResetPasswordDialog = (user) => {
      resetPasswordUser.value = user
      resetPasswordForm.value = { new_password: '' }
      error.value = ''
      showResetPasswordDialog.value = true
    }

    const closeResetPasswordDialog = () => {
      showResetPasswordDialog.value = false
      resetPasswordUser.value = null
      error.value = ''
    }

    const handleSaveUser = async () => {
      saving.value = true
      error.value = ''

      try {
        if (editingUser.value) {
          // Update existing user
          const updateData = {
            full_name: userForm.value.full_name || null,
            email: userForm.value.email || null,
            role: userForm.value.role,
            is_active: userForm.value.is_active
          }
          await updateUser(editingUser.value.id, updateData)
          success(`User ${editingUser.value.username} updated successfully`)
        } else {
          // Create new user
          await createUser(userForm.value)
          success(`User ${userForm.value.username} created successfully`)
        }
        await fetchUsers()
        closeUserDialog()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to save user'
        showError(error.value)
      } finally {
        saving.value = false
      }
    }

    const handleResetPassword = async () => {
      saving.value = true
      error.value = ''

      try {
        await resetUserPassword(resetPasswordUser.value.id, resetPasswordForm.value)
        success(`Password reset for ${resetPasswordUser.value.username}`)
        closeResetPasswordDialog()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to reset password'
        showError(error.value)
      } finally {
        saving.value = false
      }
    }

    const handleDelete = async (user) => {
      if (user.id === currentUserId.value) {
        warning('You cannot delete your own account')
        return
      }

      if (!confirm(`Are you sure you want to delete user "${user.username}"?\n\nThis action cannot be undone.`)) {
        return
      }

      try {
        await deleteUser(user.id)
        success(`User ${user.username} deleted successfully`)
        await fetchUsers()
      } catch (err) {
        showError(err.response?.data?.detail || 'Failed to delete user')
      }
    }

    const formatRole = (role) => {
      const roles = {
        admin: 'Admin',
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

    onMounted(() => {
      fetchUsers()
      fetchCurrentUser()
    })

    return {
      users,
      loading,
      showUserDialog,
      showResetPasswordDialog,
      editingUser,
      resetPasswordUser,
      userForm,
      resetPasswordForm,
      saving,
      error,
      currentUserId,
      searchQuery,
      filterRole,
      filterStatus,
      activeUsers,
      adminUsers,
      editorUsers,
      filteredUsers,
      openCreateDialog,
      openEditDialog,
      closeUserDialog,
      openResetPasswordDialog,
      closeResetPasswordDialog,
      handleSaveUser,
      handleResetPassword,
      handleDelete,
      formatRole,
      formatDate,
      formatShortDate
    }
  }
}
</script>

<style scoped>
.users-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.container {
  background: var(--bg-card, white);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--border-color, #e0e0e0);
}

.header-left h2 {
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

/* Controls */
.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 250px;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.filters {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
  cursor: pointer;
  transition: all 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
}

/* Loading State */
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
  font-size: 1rem;
}

/* No Data State */
.no-data {
  text-align: center;
  padding: 4rem 2rem;
}

.no-data p {
  color: var(--text-secondary, #666);
  font-size: 1.125rem;
  margin-bottom: 1.5rem;
}

/* Users Table */
.users-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 0.875rem 1rem;
  background: var(--bg-secondary, #f8f9fa);
  color: var(--text-primary, #333);
  font-weight: 600;
  font-size: 0.875rem;
  border-bottom: 2px solid var(--border-color, #e0e0e0);
  white-space: nowrap;
}

td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  color: var(--text-primary, #333);
  font-size: 0.9375rem;
}

tr:hover {
  background: var(--bg-hover, #f8f9fa);
}

.username {
  font-weight: 600;
  color: var(--color-primary, #667eea);
}

.actions {
  display: flex;
  gap: 0.5rem;
  white-space: nowrap;
}

.btn-icon {
  background: var(--btn-secondary-bg);
  color: var(--btn-secondary-text);
  border: 1px solid var(--border-color);
  padding: 0.375rem 0.75rem;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.8125rem;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-icon:hover:not(:disabled) {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border-color: var(--btn-primary-bg);
}

.btn-icon:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-icon.btn-danger:hover:not(:disabled) {
  background: var(--btn-danger-bg);
  color: var(--btn-danger-text);
  border-color: var(--btn-danger-bg);
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.role-admin {
  background: var(--color-primary);
  color: var(--text-on-primary);
}

.role-editor {
  background: var(--color-warning);
  color: var(--text-on-warning);
}

.role-viewer {
  background: var(--color-info);
  color: var(--text-on-info);
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.status-active {
  background: var(--color-success);
  color: var(--text-on-success);
}

.status-badge.status-inactive {
  background: var(--color-danger);
  color: var(--text-on-danger);
}

/* Buttons */
.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9375rem;
  transition: all 0.2s;
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

/* Modal */
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
  padding: 1rem;
}

.modal {
  background: var(--bg-card, white);
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
  display: flex;
  flex-direction: column;
}

.modal-small {
  max-width: 440px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.375rem;
  color: var(--text-primary, #333);
  font-weight: 700;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--text-secondary, #666);
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s;
  line-height: 1;
}

.close-btn:hover {
  background: var(--bg-hover, #f0f0f0);
  color: var(--text-primary, #333);
}

.modal-body {
  padding: 2rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--border-color, #e0e0e0);
  flex-shrink: 0;
  justify-content: flex-end;
}

.form-row {
  margin-bottom: 1.5rem;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: var(--text-primary, #333);
  font-size: 0.9375rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.field-hint {
  margin-top: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary, #999);
}

.form-group-checkbox {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-primary, #333);
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.reset-info {
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  color: var(--text-secondary, #666);
  font-size: 0.9375rem;
}

.reset-info strong {
  color: var(--text-primary, #333);
}

.error-message {
  padding: 1rem 1.5rem;
  background: var(--color-danger);
  color: var(--text-on-danger);
  border-radius: 8px;
  margin: 1.5rem 2rem;
  font-size: 0.9375rem;
  opacity: 0.9;
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

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
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

/* Responsive */
@media (max-width: 768px) {
  .users-page {
    padding: 1rem;
  }

  .container {
    padding: 1.5rem;
  }

  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .controls {
    flex-direction: column;
  }

  .filters {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .users-table {
    font-size: 0.875rem;
  }

  th, td {
    padding: 0.625rem 0.5rem;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 1.25rem;
  }
}
</style>
