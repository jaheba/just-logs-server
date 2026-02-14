<template>
  <div class="dashboards-page">
    <div class="page-header">
      <div>
        <h1>Dashboards</h1>
        <p class="subtitle">Create and manage custom dashboards for log analytics</p>
      </div>
      <button class="btn-primary" @click="showCreateDialog = true">
        <font-awesome-icon icon="plus" />
        Create Dashboard
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Loading dashboards...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="dashboards.length === 0" class="empty-state">
      <font-awesome-icon icon="chart-line" class="icon" />
      <h2>No dashboards yet</h2>
      <p>Create your first dashboard to visualize log data and metrics</p>
      <button class="btn-primary" @click="showCreateDialog = true">
        <font-awesome-icon icon="plus" />
        Create Dashboard
      </button>
    </div>

    <!-- Dashboards Grid -->
    <div v-else class="dashboards-grid">
      <div
        v-for="dashboard in dashboards"
        :key="dashboard.id"
        class="dashboard-card"
        @click="openDashboard(dashboard.id)"
      >
        <div class="card-header">
          <h3>{{ dashboard.name }}</h3>
          <div class="card-actions">
            <button
              class="icon-btn"
              @click.stop="duplicateDashboard(dashboard)"
              title="Duplicate"
            >
              <font-awesome-icon icon="copy" />
            </button>
            <button
              class="icon-btn"
              @click.stop="editDashboard(dashboard)"
              title="Edit"
              v-if="dashboard.owner_id === currentUser?.id"
            >
              <font-awesome-icon icon="edit" />
            </button>
            <button
              class="icon-btn danger"
              @click.stop="confirmDelete(dashboard)"
              title="Delete"
              v-if="dashboard.owner_id === currentUser?.id"
            >
              <font-awesome-icon icon="trash" />
            </button>
          </div>
        </div>
        
        <p v-if="dashboard.description" class="card-description">
          {{ dashboard.description }}
        </p>
        
        <div class="card-footer">
          <div class="card-meta">
            <span class="badge" v-if="dashboard.is_public">
              <font-awesome-icon icon="globe" />
              Public
            </span>
            <span class="badge" v-else>
              <font-awesome-icon icon="lock" />
              Private
            </span>
            <span class="meta-text">
              by {{ dashboard.owner_username || 'Unknown' }}
            </span>
          </div>
          <div class="card-stats">
            <span class="meta-text">
              Updated {{ formatDate(dashboard.updated_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <div v-if="showCreateDialog || showEditDialog" class="modal-overlay" @click="closeDialogs">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ showEditDialog ? 'Edit Dashboard' : 'Create Dashboard' }}</h2>
          <button class="icon-btn" @click="closeDialogs">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Name *</label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="e.g., System Overview"
              maxlength="100"
              required
            />
          </div>
          
          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="formData.description"
              placeholder="Describe what this dashboard shows..."
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="formData.is_public" />
              Make this dashboard public
            </label>
            <p class="hint">Public dashboards can be viewed by all users</p>
          </div>
          
          <div class="form-group">
            <label>Auto-refresh interval (seconds)</label>
            <input
              v-model.number="formData.refresh_interval"
              type="number"
              min="0"
              placeholder="60"
            />
            <p class="hint">Set to 0 to disable auto-refresh</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeDialogs">Cancel</button>
          <button class="btn-primary" @click="saveDashboard" :disabled="!formData.name">
            {{ showEditDialog ? 'Save Changes' : 'Create Dashboard' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="showDeleteDialog" class="modal-overlay" @click="showDeleteDialog = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>Delete Dashboard</h2>
          <button class="icon-btn" @click="showDeleteDialog = false">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        
        <div class="modal-body">
          <p>Are you sure you want to delete <strong>{{ dashboardToDelete?.name }}</strong>?</p>
          <p class="warning">This action cannot be undone. All widgets will be deleted.</p>
        </div>
        
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteDialog = false">Cancel</button>
          <button class="btn-danger" @click="performDelete">Delete Dashboard</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getDashboards,
  createDashboard as apiCreateDashboard,
  updateDashboard as apiUpdateDashboard,
  deleteDashboard as apiDeleteDashboard,
  duplicateDashboard as apiDuplicateDashboard,
  getCurrentUser
} from '../services/api'
import { useToast } from '../composables/useToast'

export default {
  name: 'DashboardsList',
  setup() {
    const router = useRouter()
    const { showToast } = useToast()
    
    const loading = ref(true)
    const dashboards = ref([])
    const currentUser = ref(null)
    
    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const showDeleteDialog = ref(false)
    const dashboardToDelete = ref(null)
    const editingDashboard = ref(null)
    
    const formData = ref({
      name: '',
      description: '',
      is_public: false,
      refresh_interval: 60
    })
    
    const loadDashboards = async () => {
      loading.value = true
      try {
        const response = await getDashboards()
        dashboards.value = response.data
      } catch (error) {
        console.error('Failed to load dashboards:', error)
        showToast('Failed to load dashboards', 'error')
      } finally {
        loading.value = false
      }
    }
    
    const loadCurrentUser = async () => {
      try {
        const response = await getCurrentUser()
        currentUser.value = response.data
      } catch (error) {
        console.error('Failed to load current user:', error)
      }
    }
    
    const openDashboard = (dashboardId) => {
      router.push(`/dashboards/${dashboardId}`)
    }
    
    const editDashboard = (dashboard) => {
      editingDashboard.value = dashboard
      formData.value = {
        name: dashboard.name,
        description: dashboard.description || '',
        is_public: dashboard.is_public,
        refresh_interval: dashboard.refresh_interval
      }
      showEditDialog.value = true
    }
    
    const confirmDelete = (dashboard) => {
      dashboardToDelete.value = dashboard
      showDeleteDialog.value = true
    }
    
    const duplicateDashboard = async (dashboard) => {
      const newName = prompt('Enter a name for the duplicated dashboard:', `${dashboard.name} (Copy)`)
      if (!newName) return
      
      try {
        await apiDuplicateDashboard(dashboard.id, newName)
        showToast('Dashboard duplicated successfully', 'success')
        await loadDashboards()
      } catch (error) {
        console.error('Failed to duplicate dashboard:', error)
        showToast('Failed to duplicate dashboard', 'error')
      }
    }
    
    const saveDashboard = async () => {
      try {
        if (showEditDialog.value && editingDashboard.value) {
          await apiUpdateDashboard(editingDashboard.value.id, formData.value)
          showToast('Dashboard updated successfully', 'success')
        } else {
          await apiCreateDashboard(formData.value)
          showToast('Dashboard created successfully', 'success')
        }
        
        closeDialogs()
        await loadDashboards()
      } catch (error) {
        console.error('Failed to save dashboard:', error)
        showToast('Failed to save dashboard', 'error')
      }
    }
    
    const performDelete = async () => {
      try {
        await apiDeleteDashboard(dashboardToDelete.value.id)
        showToast('Dashboard deleted successfully', 'success')
        showDeleteDialog.value = false
        dashboardToDelete.value = null
        await loadDashboards()
      } catch (error) {
        console.error('Failed to delete dashboard:', error)
        showToast('Failed to delete dashboard', 'error')
      }
    }
    
    const closeDialogs = () => {
      showCreateDialog.value = false
      showEditDialog.value = false
      editingDashboard.value = null
      formData.value = {
        name: '',
        description: '',
        is_public: false,
        refresh_interval: 60
      }
    }
    
    const formatDate = (dateStr) => {
      const date = new Date(dateStr)
      const now = new Date()
      const diff = now - date
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)
      const days = Math.floor(hours / 24)
      
      if (days > 0) return `${days}d ago`
      if (hours > 0) return `${hours}h ago`
      if (minutes > 0) return `${minutes}m ago`
      return 'just now'
    }
    
    onMounted(() => {
      loadDashboards()
      loadCurrentUser()
    })
    
    return {
      loading,
      dashboards,
      currentUser,
      showCreateDialog,
      showEditDialog,
      showDeleteDialog,
      dashboardToDelete,
      formData,
      openDashboard,
      editDashboard,
      confirmDelete,
      duplicateDashboard,
      saveDashboard,
      performDelete,
      closeDialogs,
      formatDate
    }
  }
}
</script>

<style scoped>
.dashboards-page {
  padding: 2.5rem 3rem;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid var(--border-color);
}

.page-header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-secondary);
  margin: 0.75rem 0 0 0;
  font-size: 1.05rem;
  font-weight: 400;
}

.dashboards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 2rem;
}

.dashboard-card {
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.dashboard-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--accent-color), #667eea);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.dashboard-card:hover {
  border-color: var(--accent-color);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
  transform: translateY(-4px);
}

.dashboard-card:hover::before {
  transform: scaleX(1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  flex: 1;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.dashboard-card:hover .card-actions {
  opacity: 1;
}

.card-description {
  color: var(--text-secondary);
  margin: 0 0 1.5rem 0;
  font-size: 0.95rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 3rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1.25rem;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.meta-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 6rem 2rem;
  background: var(--bg-secondary);
  border-radius: 16px;
  border: 2px dashed var(--border-color);
}

.empty-state .icon {
  font-size: 5rem;
  color: var(--accent-color);
  opacity: 0.3;
  margin-bottom: 1.5rem;
}

.empty-state h2 {
  margin: 0 0 0.75rem 0;
  font-weight: 700;
  font-size: 1.75rem;
}

.empty-state p {
  color: var(--text-secondary);
  margin: 0 0 2rem 0;
  font-size: 1.05rem;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6rem 2rem;
  gap: 1.5rem;
}

.loading-container span {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.icon-btn.danger:hover {
  color: #ff4444;
  background: rgba(255, 68, 68, 0.1);
}

.warning {
  color: #ff9800;
  font-size: 0.95rem;
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 152, 0, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

/* Button improvements */
.btn-primary {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent-color), #667eea);
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--accent-color);
  transform: scale(1.05);
}
</style>
