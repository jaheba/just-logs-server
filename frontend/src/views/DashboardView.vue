<template>
  <div class="dashboard-view">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Loading dashboard...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <font-awesome-icon icon="exclamation-triangle" class="icon" />
      <h2>Dashboard not found</h2>
      <p>{{ error }}</p>
      <router-link to="/dashboards" class="btn-primary">
        <font-awesome-icon icon="arrow-left" />
        Back to Dashboards
      </router-link>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="dashboard-content">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="header-left">
          <router-link to="/dashboards" class="back-link">
            <font-awesome-icon icon="arrow-left" />
          </router-link>
          <div>
            <h1>{{ dashboard.name }}</h1>
            <p v-if="dashboard.description" class="description">
              {{ dashboard.description }}
            </p>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn-secondary" @click="toggleEditMode">
            <font-awesome-icon :icon="editMode ? 'check' : 'edit'" />
            {{ editMode ? 'Done' : 'Edit' }}
          </button>
          <button class="btn-secondary" @click="refreshDashboard">
            <font-awesome-icon icon="sync" :class="{ 'fa-spin': refreshing }" />
            Refresh
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="dashboard.widgets && dashboard.widgets.length === 0" class="empty-widgets">
        <font-awesome-icon icon="chart-line" class="icon" />
        <h2>No widgets yet</h2>
        <p>Add widgets to visualize your log data</p>
        <button class="btn-primary" @click="showAddWidgetDialog = true">
          <font-awesome-icon icon="plus" />
          Add Widget
        </button>
      </div>

      <!-- Widgets Grid -->
      <div v-else class="widgets-grid">
        <div
          v-for="widget in dashboard.widgets"
          :key="widget.id"
          class="widget-container"
          :style="{
            gridColumn: `span ${widget.width}`,
            gridRow: `span ${widget.height}`
          }"
        >
          <div class="widget-card">
            <div class="widget-header">
              <h3>{{ widget.title }}</h3>
              <div class="widget-actions" v-if="editMode">
                <button class="icon-btn" @click="editWidget(widget)">
                  <font-awesome-icon icon="edit" />
                </button>
                <button class="icon-btn danger" @click="deleteWidget(widget)">
                  <font-awesome-icon icon="trash" />
                </button>
              </div>
            </div>
            <div class="widget-body">
              <!-- Placeholder content -->
              <div class="widget-placeholder">
                <font-awesome-icon :icon="getWidgetIcon(widget.widget_type)" class="icon" />
                <p>{{ widget.widget_type }} widget</p>
                <small>Coming soon...</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Widget Button (floating) -->
      <button
        v-if="editMode"
        class="fab"
        @click="showAddWidgetDialog = true"
        title="Add Widget"
      >
        <font-awesome-icon icon="plus" />
      </button>
    </div>

    <!-- Add Widget Dialog -->
    <div v-if="showAddWidgetDialog" class="modal-overlay" @click="showAddWidgetDialog = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>Add Widget</h2>
          <button class="icon-btn" @click="showAddWidgetDialog = false">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <p class="hint">Widget configuration coming soon in the next phase...</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddWidgetDialog = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDashboard } from '../services/api'
import { useToast } from '../composables/useToast'

export default {
  name: 'DashboardView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { showToast } = useToast()
    
    const loading = ref(true)
    const error = ref(null)
    const dashboard = ref(null)
    const editMode = ref(false)
    const refreshing = ref(false)
    const showAddWidgetDialog = ref(false)
    
    let refreshInterval = null
    
    const loadDashboard = async () => {
      loading.value = true
      error.value = null
      
      try {
        const response = await getDashboard(route.params.id)
        dashboard.value = response.data
      } catch (err) {
        console.error('Failed to load dashboard:', err)
        error.value = err.response?.data?.detail || 'Failed to load dashboard'
        showToast('Failed to load dashboard', 'error')
      } finally {
        loading.value = false
      }
    }
    
    const refreshDashboard = async () => {
      if (refreshing.value) return
      
      refreshing.value = true
      try {
        await loadDashboard()
      } finally {
        refreshing.value = false
      }
    }
    
    const toggleEditMode = () => {
      editMode.value = !editMode.value
      if (editMode.value) {
        showToast('Edit mode enabled', 'info')
      }
    }
    
    const editWidget = (widget) => {
      showToast('Widget editing coming soon...', 'info')
    }
    
    const deleteWidget = (widget) => {
      showToast('Widget deletion coming soon...', 'info')
    }
    
    const getWidgetIcon = (type) => {
      const icons = {
        metric: 'chart-line',
        chart: 'chart-bar',
        table: 'table',
        log_stream: 'stream'
      }
      return icons[type] || 'chart-line'
    }
    
    const setupAutoRefresh = () => {
      if (dashboard.value && dashboard.value.refresh_interval > 0) {
        refreshInterval = setInterval(() => {
          refreshDashboard()
        }, dashboard.value.refresh_interval * 1000)
      }
    }
    
    onMounted(async () => {
      await loadDashboard()
      setupAutoRefresh()
    })
    
    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })
    
    return {
      loading,
      error,
      dashboard,
      editMode,
      refreshing,
      showAddWidgetDialog,
      refreshDashboard,
      toggleEditMode,
      editWidget,
      deleteWidget,
      getWidgetIcon
    }
  }
}
</script>

<style scoped>
.dashboard-view {
  height: 100%;
  overflow: auto;
  background: var(--bg-primary);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 1.5rem;
}

.loading-container span {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 3rem;
}

.error-state .icon {
  font-size: 5rem;
  color: #ff9800;
  margin-bottom: 1.5rem;
  opacity: 0.8;
}

.error-state h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.dashboard-content {
  padding: 2.5rem 3rem;
  max-width: 1800px;
  margin: 0 auto;
  position: relative;
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
}

.back-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  color: var(--text-primary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
}

.back-link:hover {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
  transform: translateX(-4px);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.description {
  color: var(--text-secondary);
  margin: 0.75rem 0 0 0;
  font-size: 1rem;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.empty-widgets {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
  text-align: center;
  padding: 4rem 3rem;
  background: var(--bg-secondary);
  border: 3px dashed var(--border-color);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.empty-widgets:hover {
  border-color: var(--accent-color);
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-primary));
}

.empty-widgets .icon {
  font-size: 5rem;
  color: var(--accent-color);
  opacity: 0.4;
  margin-bottom: 1.5rem;
}

.empty-widgets h2 {
  margin: 0 0 0.75rem 0;
  font-weight: 700;
  font-size: 1.75rem;
}

.empty-widgets p {
  color: var(--text-secondary);
  margin: 0 0 2rem 0;
  font-size: 1.05rem;
}

.widgets-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 2rem;
  grid-auto-rows: 120px;
}

.widget-container {
  min-height: 120px;
}

.widget-card {
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.widget-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent-color), #667eea);
}

.widget-card:hover {
  border-color: var(--accent-color);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(to bottom, var(--bg-secondary), transparent);
}

.widget-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.widget-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.widget-card:hover .widget-actions {
  opacity: 1;
}

.widget-body {
  flex: 1;
  padding: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.widget-placeholder {
  text-align: center;
  color: var(--text-secondary);
}

.widget-placeholder .icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  opacity: 0.4;
  color: var(--accent-color);
}

.widget-placeholder p {
  margin: 0 0 0.35rem 0;
  font-weight: 600;
  font-size: 1rem;
}

.widget-placeholder small {
  font-size: 0.85rem;
  opacity: 0.6;
}

.fab {
  position: fixed;
  right: 3rem;
  bottom: 3rem;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #667eea);
  color: white;
  border: none;
  font-size: 1.75rem;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
}

.fab:hover {
  transform: scale(1.15) rotate(90deg);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.fab:active {
  transform: scale(1.05) rotate(90deg);
}

.btn-secondary {
  padding: 0.65rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary:hover {
  border-color: var(--accent-color);
  background: var(--bg-tertiary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  padding: 0.65rem 1.25rem;
  font-size: 0.95rem;
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

.fa-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
