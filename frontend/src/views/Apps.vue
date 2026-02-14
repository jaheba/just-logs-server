<template>
  <div class="apps-page">
    <Toast />
    
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <h2>Applications</h2>
          <p class="subtitle">Manage your applications and their retention policies</p>
        </div>
        <button @click="openCreateDialog" class="btn-primary">
          Create App
        </button>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading applications...</p>
      </div>

      <div v-else-if="apps.length === 0" class="no-data">
        <p>No applications yet</p>
        <button @click="openCreateDialog" class="btn-secondary">
          Create Your First App
        </button>
      </div>

      <div v-else class="apps-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>Created</th>
              <th>Retention</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="app in apps" :key="app.id">
              <td>
                <span class="app-name">{{ app.name }}</span>
              </td>
              <td>{{ app.id }}</td>
              <td>{{ formatDate(app.created_at) }}</td>
              <td>
                <span class="retention-badge" :class="getRetentionClass(app.id)">
                  {{ getRetentionLabel(app.id) }}
                </span>
              </td>
              <td class="actions">
                <button @click="openEditDialog(app)" class="btn-icon" title="Edit Retention">
                  Edit
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create App Dialog -->
    <div v-if="showCreateDialog" class="modal-overlay" @click.self="closeCreateDialog">
      <div class="modal modal-small">
        <div class="modal-header">
          <h3>Create New Application</h3>
          <button @click="closeCreateDialog" class="close-btn">&times;</button>
        </div>
        
        <form @submit.prevent="handleCreate">
          <div class="modal-body">
            <div class="form-group">
              <label>Application Name *</label>
              <input
                v-model="newAppName"
                type="text"
                required
                placeholder="e.g., web-api, worker-service"
                minlength="1"
                maxlength="100"
              />
              <span class="field-hint">Unique name for your application</span>
            </div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div class="modal-footer">
            <button type="button" @click="closeCreateDialog" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="creating">
              <span v-if="creating" class="spinner-small"></span>
              {{ creating ? 'Creating...' : 'Create App' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit App Retention Dialog -->
    <div v-if="showEditDialog" class="modal-overlay" @click.self="closeEditDialog">
      <div class="modal">
        <div class="modal-header">
          <h3>Edit Retention: {{ editingApp?.name }}</h3>
          <button @click="closeEditDialog" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="retention-mode">
            <label class="radio-label">
              <input v-model="retentionMode" type="radio" value="default" />
              Use Global Defaults
            </label>
            <label class="radio-label">
              <input v-model="retentionMode" type="radio" value="custom" />
              Custom Retention Policies
            </label>
          </div>

          <div v-if="retentionMode === 'custom'" class="custom-policies">
            <p class="section-note">Configure custom retention for each priority tier</p>
            
            <!-- High Priority -->
            <div class="policy-section">
              <h4 class="policy-title high">High Priority (FATAL, ERROR)</h4>
              <div class="policy-fields">
                <div class="form-group">
                  <label>Time-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.high.retention_days" 
                      type="number" 
                      min="1"
                      placeholder="90"
                    />
                    <span class="input-suffix">days</span>
                  </div>
                </div>
                <div class="form-group">
                  <label>Count-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.high.retention_count" 
                      type="number" 
                      min="0"
                      placeholder="Optional"
                    />
                    <span class="input-suffix">logs</span>
                  </div>
                </div>
                <div class="form-group-checkbox">
                  <label class="checkbox-label">
                    <input v-model="customPolicies.high.enabled" type="checkbox" />
                    Enabled
                  </label>
                </div>
              </div>
            </div>

            <!-- Medium Priority -->
            <div class="policy-section">
              <h4 class="policy-title medium">Medium Priority (WARN, INFO)</h4>
              <div class="policy-fields">
                <div class="form-group">
                  <label>Time-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.medium.retention_days" 
                      type="number" 
                      min="1"
                      placeholder="30"
                    />
                    <span class="input-suffix">days</span>
                  </div>
                </div>
                <div class="form-group">
                  <label>Count-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.medium.retention_count" 
                      type="number" 
                      min="0"
                      placeholder="Optional"
                    />
                    <span class="input-suffix">logs</span>
                  </div>
                </div>
                <div class="form-group-checkbox">
                  <label class="checkbox-label">
                    <input v-model="customPolicies.medium.enabled" type="checkbox" />
                    Enabled
                  </label>
                </div>
              </div>
            </div>

            <!-- Low Priority -->
            <div class="policy-section">
              <h4 class="policy-title low">Low Priority (DEBUG, TRACE)</h4>
              <div class="policy-fields">
                <div class="form-group">
                  <label>Time-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.low.retention_days" 
                      type="number" 
                      min="1"
                      placeholder="7"
                    />
                    <span class="input-suffix">days</span>
                  </div>
                </div>
                <div class="form-group">
                  <label>Count-based</label>
                  <div class="input-group">
                    <input 
                      v-model.number="customPolicies.low.retention_count" 
                      type="number" 
                      min="0"
                      placeholder="Optional"
                    />
                    <span class="input-suffix">logs</span>
                  </div>
                </div>
                <div class="form-group-checkbox">
                  <label class="checkbox-label">
                    <input v-model="customPolicies.low.enabled" type="checkbox" />
                    Enabled
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="default-info">
            <p>This app will use the global retention policies configured in Settings:</p>
            <ul>
              <li>High Priority (FATAL, ERROR): 90 days</li>
              <li>Medium Priority (WARN, INFO): 30 days</li>
              <li>Low Priority (DEBUG, TRACE): 7 days</li>
            </ul>
          </div>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="modal-footer">
          <button type="button" @click="closeEditDialog" class="btn-secondary">
            Cancel
          </button>
          <button type="button" @click="handleSaveRetention" class="btn-primary" :disabled="saving">
            <span v-if="saving" class="spinner-small"></span>
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import {
  getApps,
  createApp,
  getAppRetentionPolicies,
  createRetentionPolicy,
  updateRetentionPolicy,
  deleteRetentionPolicy
} from '../services/api'
import { useToast } from '../composables/useToast'
import Toast from '../components/Toast.vue'

export default {
  name: 'Apps',
  components: {
    Toast
  },
  setup() {
    const { success, error: showError } = useToast()
    
    const apps = ref([])
    const appPolicies = ref({}) // Map of app_id -> policies
    const loading = ref(false)
    const creating = ref(false)
    const saving = ref(false)
    const error = ref('')
    
    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const newAppName = ref('')
    const editingApp = ref(null)
    const retentionMode = ref('default')
    
    const customPolicies = ref({
      high: { priority_tier: 'high', retention_days: 90, retention_count: null, enabled: true },
      medium: { priority_tier: 'medium', retention_days: 30, retention_count: null, enabled: true },
      low: { priority_tier: 'low', retention_days: 7, retention_count: null, enabled: true }
    })

    const fetchApps = async () => {
      loading.value = true
      try {
        const response = await getApps()
        apps.value = response.data
        
        // Fetch retention policies for each app
        for (const app of apps.value) {
          await fetchAppPolicies(app.id)
        }
      } catch (err) {
        console.error('Failed to fetch apps:', err)
        showError('Failed to load applications')
      } finally {
        loading.value = false
      }
    }

    const fetchAppPolicies = async (appId) => {
      try {
        const response = await getAppRetentionPolicies(appId)
        appPolicies.value[appId] = response.data.policies
      } catch (err) {
        console.error(`Failed to fetch policies for app ${appId}:`, err)
      }
    }

    const openCreateDialog = () => {
      newAppName.value = ''
      error.value = ''
      showCreateDialog.value = true
    }

    const closeCreateDialog = () => {
      showCreateDialog.value = false
      newAppName.value = ''
      error.value = ''
    }

    const handleCreate = async () => {
      creating.value = true
      error.value = ''

      try {
        await createApp(newAppName.value)
        success(`App "${newAppName.value}" created successfully`)
        closeCreateDialog()
        await fetchApps()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to create app'
        showError(error.value)
      } finally {
        creating.value = false
      }
    }

    const openEditDialog = async (app) => {
      editingApp.value = app
      error.value = ''
      
      // Load existing policies
      const policies = appPolicies.value[app.id] || []
      
      if (policies.length > 0) {
        retentionMode.value = 'custom'
        // Populate custom policies
        policies.forEach(policy => {
          if (customPolicies.value[policy.priority_tier]) {
            customPolicies.value[policy.priority_tier] = { ...policy }
          }
        })
      } else {
        retentionMode.value = 'default'
        // Reset to defaults
        customPolicies.value = {
          high: { priority_tier: 'high', retention_days: 90, retention_count: null, enabled: true },
          medium: { priority_tier: 'medium', retention_days: 30, retention_count: null, enabled: true },
          low: { priority_tier: 'low', retention_days: 7, retention_count: null, enabled: true }
        }
      }
      
      showEditDialog.value = true
    }

    const closeEditDialog = () => {
      showEditDialog.value = false
      editingApp.value = null
      error.value = ''
    }

    const handleSaveRetention = async () => {
      saving.value = true
      error.value = ''

      try {
        const appId = editingApp.value.id
        const existingPolicies = appPolicies.value[appId] || []

        if (retentionMode.value === 'default') {
          // Delete all app-specific policies (revert to global)
          for (const policy of existingPolicies) {
            await deleteRetentionPolicy(policy.id)
          }
          success(`${editingApp.value.name} now uses global retention policies`)
        } else {
          // Save custom policies
          const tiers = ['high', 'medium', 'low']
          
          for (const tier of tiers) {
            const policyData = customPolicies.value[tier]
            const existing = existingPolicies.find(p => p.priority_tier === tier)
            
            if (existing) {
              // Update existing policy
              await updateRetentionPolicy(existing.id, {
                retention_type: 'time_based',
                retention_days: policyData.retention_days || null,
                retention_count: policyData.retention_count || null,
                enabled: policyData.enabled
              })
            } else {
              // Create new policy
              await createRetentionPolicy({
                app_id: appId,
                priority_tier: tier,
                retention_type: 'time_based',
                retention_days: policyData.retention_days || null,
                retention_count: policyData.retention_count || null,
                enabled: policyData.enabled
              })
            }
          }
          success(`Custom retention policies saved for ${editingApp.value.name}`)
        }
        
        closeEditDialog()
        await fetchApps()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to save retention policies'
        showError(error.value)
      } finally {
        saving.value = false
      }
    }

    const getRetentionLabel = (appId) => {
      const policies = appPolicies.value[appId] || []
      return policies.length > 0 ? 'Custom' : 'Global Default'
    }

    const getRetentionClass = (appId) => {
      const policies = appPolicies.value[appId] || []
      return policies.length > 0 ? 'retention-custom' : 'retention-default'
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }

    onMounted(() => {
      fetchApps()
    })

    return {
      apps,
      loading,
      creating,
      saving,
      error,
      showCreateDialog,
      showEditDialog,
      newAppName,
      editingApp,
      retentionMode,
      customPolicies,
      openCreateDialog,
      closeCreateDialog,
      handleCreate,
      openEditDialog,
      closeEditDialog,
      handleSaveRetention,
      getRetentionLabel,
      getRetentionClass,
      formatDate
    }
  }
}
</script>

<style scoped>
.apps-page {
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

.loading {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  justify-content: center;
  color: var(--text-secondary, #666);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color, #e0e0e0);
  border-top-color: var(--color-primary, #667eea);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-data {
  text-align: center;
  padding: 4rem 2rem;
}

.no-data p {
  color: var(--text-secondary, #666);
  font-size: 1.125rem;
  margin-bottom: 1.5rem;
}

.apps-table {
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

.app-name {
  font-weight: 600;
  color: var(--color-primary, #667eea);
}

.retention-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.retention-default {
  background: var(--bg-secondary, #e9ecef);
  color: var(--text-secondary, #666);
}

.retention-custom {
  background: var(--color-primary);
  color: var(--text-on-primary);
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

.btn-icon:hover {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border-color: var(--btn-primary-bg);
}

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
  padding: 1rem;
}

.modal {
  background: var(--bg-card, white);
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
  justify-content: flex-end;
}

.form-group {
  margin-bottom: 1.5rem;
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

.retention-mode {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-primary, #333);
}

.radio-label input[type="radio"] {
  width: auto;
  cursor: pointer;
}

.section-note {
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
  margin: 0 0 1rem 0;
}

.custom-policies {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.policy-section {
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  overflow: hidden;
}

.policy-title {
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  font-weight: 600;
}

.policy-title.high {
  background: var(--level-fatal);
  color: var(--text-on-danger, #ffffff);
}

.policy-title.medium {
  background: var(--level-warn);
  color: var(--text-on-warning, #ffffff);
}

.policy-title.low {
  background: var(--level-info);
  color: var(--text-on-info, #ffffff);
}

.policy-fields {
  padding: 1rem;
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 1rem;
  align-items: end;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.input-group input {
  flex: 1;
  min-width: 0;
}

.input-suffix {
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
  white-space: nowrap;
}

.form-group-checkbox {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-primary, #333);
  margin: 0;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.default-info {
  padding: 1.5rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
  border: 1px solid var(--border-color, #e0e0e0);
}

.default-info p {
  margin: 0 0 1rem 0;
  color: var(--text-primary, #333);
  font-weight: 500;
}

.default-info ul {
  margin: 0;
  padding-left: 1.5rem;
  color: var(--text-secondary, #666);
}

.default-info li {
  margin-bottom: 0.5rem;
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

@media (max-width: 768px) {
  .apps-page {
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

  .policy-fields {
    grid-template-columns: 1fr;
  }

  th, td {
    padding: 0.625rem 0.5rem;
    font-size: 0.875rem;
  }
}
</style>
