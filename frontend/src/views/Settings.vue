<template>
  <div class="settings-page">
    <Toast />
    
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <h2>Settings</h2>
          <p class="subtitle">Manage system-wide configuration and retention policies</p>
        </div>
      </div>

      <!-- Retention Policies Section -->
      <div class="section">
        <h3 class="section-title">Global Retention Policies</h3>
        <p class="section-description">
          Default policies applied to all apps unless overridden. Logs are automatically deleted based on these rules.
        </p>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Loading policies...</p>
        </div>

        <div v-else class="policies-grid">
          <!-- High Priority Policy -->
          <div class="policy-card high">
            <div class="policy-header">
              <h4>High Priority</h4>
              <span class="policy-levels">FATAL, ERROR</span>
            </div>
            <div class="policy-body">
              <div class="policy-field">
                <label>Time-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="highPolicy.retention_days" 
                    type="number" 
                    min="1"
                    :disabled="saving"
                  />
                  <span class="input-suffix">days</span>
                </div>
              </div>
              <div class="policy-field">
                <label>Count-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="highPolicy.retention_count" 
                    type="number" 
                    min="0"
                    placeholder="Optional"
                    :disabled="saving"
                  />
                  <span class="input-suffix">logs</span>
                </div>
              </div>
              <div class="policy-actions">
                <label class="checkbox-label">
                  <input v-model="highPolicy.enabled" type="checkbox" :disabled="saving" />
                  Enabled
                </label>
                <button @click="savePolicy(highPolicy)" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Saving...' : 'Save' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Medium Priority Policy -->
          <div class="policy-card medium">
            <div class="policy-header">
              <h4>Medium Priority</h4>
              <span class="policy-levels">WARN, INFO</span>
            </div>
            <div class="policy-body">
              <div class="policy-field">
                <label>Time-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="mediumPolicy.retention_days" 
                    type="number" 
                    min="1"
                    :disabled="saving"
                  />
                  <span class="input-suffix">days</span>
                </div>
              </div>
              <div class="policy-field">
                <label>Count-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="mediumPolicy.retention_count" 
                    type="number" 
                    min="0"
                    placeholder="Optional"
                    :disabled="saving"
                  />
                  <span class="input-suffix">logs</span>
                </div>
              </div>
              <div class="policy-actions">
                <label class="checkbox-label">
                  <input v-model="mediumPolicy.enabled" type="checkbox" :disabled="saving" />
                  Enabled
                </label>
                <button @click="savePolicy(mediumPolicy)" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Saving...' : 'Save' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Low Priority Policy -->
          <div class="policy-card low">
            <div class="policy-header">
              <h4>Low Priority</h4>
              <span class="policy-levels">DEBUG, TRACE</span>
            </div>
            <div class="policy-body">
              <div class="policy-field">
                <label>Time-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="lowPolicy.retention_days" 
                    type="number" 
                    min="1"
                    :disabled="saving"
                  />
                  <span class="input-suffix">days</span>
                </div>
              </div>
              <div class="policy-field">
                <label>Count-based Retention</label>
                <div class="input-group">
                  <input 
                    v-model.number="lowPolicy.retention_count" 
                    type="number" 
                    min="0"
                    placeholder="Optional"
                    :disabled="saving"
                  />
                  <span class="input-suffix">logs</span>
                </div>
              </div>
              <div class="policy-actions">
                <label class="checkbox-label">
                  <input v-model="lowPolicy.enabled" type="checkbox" :disabled="saving" />
                  Enabled
                </label>
                <button @click="savePolicy(lowPolicy)" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Saving...' : 'Save' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cleanup Actions Section -->
      <div class="section">
        <h3 class="section-title">Cleanup Actions</h3>
        <p class="section-description">
          Manually trigger cleanup or preview what would be deleted. Automatic cleanup runs hourly.
        </p>

        <div class="cleanup-actions">
          <button @click="previewCleanup" class="btn-secondary" :disabled="previewing || running">
            {{ previewing ? 'Loading...' : 'Preview Changes' }}
          </button>
          <button @click="runCleanup" class="btn-danger" :disabled="previewing || running">
            {{ running ? 'Running...' : 'Run Cleanup Now' }}
          </button>
        </div>

        <div v-if="previewResults" class="preview-results">
          <h4>Preview Results</h4>
          <p class="preview-total">Would delete <strong>{{ previewResults.total_logs_to_delete.toLocaleString() }}</strong> logs</p>
          <div v-if="previewResults.previews.length > 0" class="preview-list">
            <div v-for="preview in previewResults.previews" :key="preview.policy_id" class="preview-item">
              <span class="preview-tier">{{ formatTier(preview.priority_tier) }}</span>
              <span class="preview-count">{{ preview.log_count.toLocaleString() }} logs</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Cleanup History Section -->
      <div class="section">
        <h3 class="section-title">Recent Cleanup Runs</h3>
        
        <div v-if="loadingRuns" class="loading">
          <div class="spinner-small"></div>
          <span>Loading history...</span>
        </div>

        <div v-else-if="runs.length === 0" class="no-data">
          <p>No cleanup runs yet</p>
        </div>

        <div v-else class="runs-table">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Status</th>
                <th>Logs Deleted</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in runs" :key="run.id">
                <td>{{ formatDateTime(run.started_at) }}</td>
                <td>
                  <span class="run-type" :class="`run-type-${run.trigger_type}`">
                    {{ run.trigger_type }}
                  </span>
                </td>
                <td>
                  <span class="run-status" :class="`run-status-${run.status}`">
                    {{ run.status }}
                  </span>
                </td>
                <td>{{ run.logs_deleted.toLocaleString() }}</td>
                <td>{{ formatDuration(run.started_at, run.completed_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import {
  getRetentionPolicies,
  updateRetentionPolicy,
  previewRetentionCleanup,
  runRetentionCleanup,
  getRetentionRuns
} from '../services/api'
import { useToast } from '../composables/useToast'
import Toast from '../components/Toast.vue'

export default {
  name: 'Settings',
  components: {
    Toast
  },
  setup() {
    const { success, error: showError } = useToast()
    
    const loading = ref(false)
    const saving = ref(false)
    const previewing = ref(false)
    const running = ref(false)
    const loadingRuns = ref(false)
    
    const highPolicy = ref({ priority_tier: 'high', retention_days: 90, retention_count: null, enabled: true })
    const mediumPolicy = ref({ priority_tier: 'medium', retention_days: 30, retention_count: null, enabled: true })
    const lowPolicy = ref({ priority_tier: 'low', retention_days: 7, retention_count: null, enabled: true })
    
    const previewResults = ref(null)
    const runs = ref([])

    const fetchPolicies = async () => {
      loading.value = true
      try {
        const response = await getRetentionPolicies()
        const policies = response.data.policies
        
        policies.forEach(policy => {
          if (policy.app_id === null) {
            if (policy.priority_tier === 'high') {
              highPolicy.value = { ...policy }
            } else if (policy.priority_tier === 'medium') {
              mediumPolicy.value = { ...policy }
            } else if (policy.priority_tier === 'low') {
              lowPolicy.value = { ...policy }
            }
          }
        })
      } catch (err) {
        console.error('Failed to fetch policies:', err)
        showError('Failed to load retention policies')
      } finally {
        loading.value = false
      }
    }

    const savePolicy = async (policy) => {
      saving.value = true
      try {
        const updates = {
          retention_type: 'time_based',
          retention_days: policy.retention_days || null,
          retention_count: policy.retention_count || null,
          enabled: policy.enabled
        }
        
        await updateRetentionPolicy(policy.id, updates)
        success(`${formatTier(policy.priority_tier)} priority policy updated`)
        await fetchPolicies()
      } catch (err) {
        console.error('Failed to save policy:', err)
        showError('Failed to save retention policy')
      } finally {
        saving.value = false
      }
    }

    const previewCleanup = async () => {
      previewing.value = true
      try {
        const response = await previewRetentionCleanup()
        previewResults.value = response.data
        success(`Preview loaded: ${response.data.total_logs_to_delete.toLocaleString()} logs would be deleted`)
      } catch (err) {
        console.error('Failed to preview cleanup:', err)
        showError('Failed to preview cleanup')
      } finally {
        previewing.value = false
      }
    }

    const runCleanup = async () => {
      if (!confirm('Are you sure you want to run cleanup now? This will permanently delete old logs.')) {
        return
      }
      
      running.value = true
      try {
        const response = await runRetentionCleanup()
        success(`Cleanup completed: ${response.data.logs_deleted.toLocaleString()} logs deleted`)
        previewResults.value = null
        await fetchRuns()
      } catch (err) {
        console.error('Failed to run cleanup:', err)
        showError('Failed to run cleanup')
      } finally {
        running.value = false
      }
    }

    const fetchRuns = async () => {
      loadingRuns.value = true
      try {
        const response = await getRetentionRuns(10)
        runs.value = response.data.runs
      } catch (err) {
        console.error('Failed to fetch runs:', err)
      } finally {
        loadingRuns.value = false
      }
    }

    const formatTier = (tier) => {
      const tiers = {
        high: 'High Priority',
        medium: 'Medium Priority',
        low: 'Low Priority'
      }
      return tiers[tier] || tier
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    const formatDuration = (start, end) => {
      if (!start || !end) return '-'
      const duration = new Date(end) - new Date(start)
      const seconds = Math.floor(duration / 1000)
      if (seconds < 60) return `${seconds}s`
      const minutes = Math.floor(seconds / 60)
      return `${minutes}m ${seconds % 60}s`
    }

    onMounted(() => {
      fetchPolicies()
      fetchRuns()
    })

    return {
      loading,
      saving,
      previewing,
      running,
      loadingRuns,
      highPolicy,
      mediumPolicy,
      lowPolicy,
      previewResults,
      runs,
      savePolicy,
      previewCleanup,
      runCleanup,
      formatTier,
      formatDateTime,
      formatDuration
    }
  }
}
</script>

<style scoped>
.settings-page {
  padding: 2rem;
  max-width: 1200px;
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

.section {
  margin-bottom: 3rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: var(--text-secondary, #666);
  font-size: 0.9375rem;
  margin: 0 0 1.5rem 0;
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

.policies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.policy-card {
  border: 2px solid var(--border-color, #e0e0e0);
  border-radius: 12px;
  overflow: hidden;
  background: var(--bg-secondary, #f8f9fa);
}

.policy-card.high { border-color: var(--level-fatal, #dc3545); }
.policy-card.medium { border-color: var(--level-warn, #ffc107); }
.policy-card.low { border-color: var(--level-info, #17a2b8); }

.policy-header {
  padding: 1rem 1.25rem;
  background: var(--bg-tertiary, #e9ecef);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.policy-card.high .policy-header { background: var(--level-fatal, #dc3545); color: var(--text-on-danger, #ffffff); }
.policy-card.medium .policy-header { background: var(--level-warn, #f39c12); color: var(--text-on-warning, #ffffff); }
.policy-card.low .policy-header { background: var(--level-info, #17a2b8); color: var(--text-on-info, #ffffff); }

.policy-header h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.policy-levels {
  font-size: 0.8125rem;
  opacity: 0.9;
}

.policy-body {
  padding: 1.25rem;
}

.policy-field {
  margin-bottom: 1rem;
}

.policy-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary, #333);
  font-size: 0.875rem;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.input-group input {
  flex: 1;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 0.9375rem;
  background: var(--bg-input, white);
  color: var(--text-primary, #333);
}

.input-group input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-suffix {
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
  min-width: 40px;
}

.policy-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color, #e0e0e0);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--text-primary, #333);
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--btn-secondary-bg);
  color: var(--btn-secondary-text);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--btn-secondary-hover);
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-danger {
  background: var(--btn-danger-bg);
  color: var(--btn-danger-text);
}

.btn-danger:hover:not(:disabled) {
  background: var(--btn-danger-hover, var(--btn-danger-bg));
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cleanup-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.preview-results {
  margin-top: 1.5rem;
  padding: 1.25rem;
  background: var(--bg-secondary, #f8f9fa);
  border-radius: 8px;
  border: 1px solid var(--border-color, #e0e0e0);
}

.preview-results h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.preview-total {
  margin: 0 0 1rem 0;
  font-size: 0.9375rem;
  color: var(--text-secondary, #666);
}

.preview-total strong {
  color: var(--color-primary, #667eea);
  font-size: 1.125rem;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: 0.625rem 0.875rem;
  background: var(--bg-card, white);
  border-radius: 6px;
  font-size: 0.875rem;
}

.preview-tier {
  font-weight: 500;
  color: var(--text-primary, #333);
}

.preview-count {
  color: var(--text-secondary, #666);
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary, #666);
}

.runs-table {
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
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  color: var(--text-primary, #333);
  font-size: 0.9375rem;
}

tr:hover {
  background: var(--bg-hover, #f8f9fa);
}

.run-type,
.run-status {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.run-type-automatic {
  background: var(--color-info);
  color: var(--text-on-info, #ffffff);
}

.run-type-manual {
  background: var(--color-primary);
  color: var(--text-on-primary, #ffffff);
}

.run-status-completed {
  background: var(--color-success);
  color: var(--text-on-success, #ffffff);
}

.run-status-running {
  background: var(--color-warning);
  color: var(--text-on-warning, #ffffff);
}

.run-status-failed {
  background: var(--color-danger);
  color: var(--text-on-danger, #ffffff);
}

@media (max-width: 768px) {
  .settings-page {
    padding: 1rem;
  }

  .container {
    padding: 1.5rem;
  }

  .policies-grid {
    grid-template-columns: 1fr;
  }

  .cleanup-actions {
    flex-direction: column;
  }

  .cleanup-actions button {
    width: 100%;
  }
}
</style>
