<template>
  <div class="api-keys-page">
    <div class="container">
      <div class="page-header">
        <h2>API Keys</h2>
        <button @click="showCreateForm = true" class="btn-primary">
          Generate New Key
        </button>
      </div>

      <div v-if="showCreateForm" class="create-form">
        <h3>Generate API Key</h3>
        <form @submit.prevent="handleCreate">
          <div class="form-group">
            <label>Application</label>
            <select v-model="selectedAppId" required>
              <option :value="null" disabled>Select an application</option>
              <option v-for="app in apps" :key="app.id" :value="app.id">
                {{ app.name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Tags (optional)</label>
            <div class="tags-input">
              <div v-for="(tag, index) in newKeyTags" :key="index" class="tag-input-row">
                <input 
                  v-model="tag.key" 
                  placeholder="Key (e.g., env)" 
                  class="tag-key-input"
                />
                <input 
                  v-model="tag.value" 
                  placeholder="Value (e.g., prod)" 
                  class="tag-value-input"
                />
                <button 
                  type="button" 
                  @click="removeTag(index)" 
                  class="btn-remove-tag"
                  title="Remove tag"
                >
                  ×
                </button>
              </div>
              <button 
                type="button" 
                @click="addTag" 
                class="btn-add-tag"
              >
                + Add Tag
              </button>
            </div>
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn-primary" :disabled="creating">
              {{ creating ? 'Generating...' : 'Generate' }}
            </button>
            <button type="button" @click="cancelCreate" class="btn-secondary">
              Cancel
            </button>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
        </form>
      </div>

      <div v-if="newlyCreatedKey" class="new-key-alert">
        <h3>API Key Created!</h3>
        <p>Copy this key now. You won't be able to see it again.</p>
        <div class="key-display">
          <code>{{ newlyCreatedKey }}</code>
          <button @click="copyKey" class="btn-copy">Copy</button>
        </div>
        <button @click="newlyCreatedKey = null" class="btn-primary">Done</button>
      </div>

      <div v-if="editingKey" class="edit-tags-modal">
        <div class="modal-overlay" @click="editingKey = null"></div>
        <div class="modal-content">
          <h3>Edit Tags for {{ editingKey.app_name }}</h3>
          <div class="tags-input">
            <div v-for="(tag, index) in editKeyTags" :key="index" class="tag-input-row">
              <input 
                v-model="tag.key" 
                placeholder="Key" 
                class="tag-key-input"
              />
              <input 
                v-model="tag.value" 
                placeholder="Value" 
                class="tag-value-input"
              />
              <button 
                type="button" 
                @click="removeEditTag(index)" 
                class="btn-remove-tag"
              >
                ×
              </button>
            </div>
            <button type="button" @click="addEditTag" class="btn-add-tag">
              + Add Tag
            </button>
          </div>
          <div class="modal-actions">
            <button @click="saveTags" class="btn-primary" :disabled="savingTags">
              {{ savingTags ? 'Saving...' : 'Save' }}
            </button>
            <button @click="editingKey = null" class="btn-secondary">
              Cancel
            </button>
          </div>
          <div v-if="editError" class="error">{{ editError }}</div>
        </div>
      </div>

      <div v-if="loading" class="loading">Loading API keys...</div>

      <div v-else-if="apiKeys.length === 0" class="no-data">
        No API keys yet. Generate one to start sending logs.
      </div>

      <div v-else class="keys-table">
        <table>
          <thead>
            <tr>
              <th>Application</th>
              <th>Key (masked)</th>
              <th>Tags</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in apiKeys" :key="key.id">
              <td>{{ key.app_name }}</td>
              <td class="key-cell">{{ maskKey(key.key) }}</td>
              <td class="tags-cell">
                <span 
                  v-for="(value, tagKey) in key.tags" 
                  :key="tagKey" 
                  class="tag-badge"
                >
                  {{ tagKey }}={{ value }}
                </span>
                <button 
                  v-if="key.is_active"
                  @click="editTags(key)" 
                  class="btn-edit-tags"
                  title="Edit tags"
                >
                  ✎
                </button>
              </td>
              <td>
                <span class="status" :class="key.is_active ? 'active' : 'inactive'">
                  {{ key.is_active ? 'Active' : 'Revoked' }}
                </span>
              </td>
              <td>{{ formatDate(key.created_at) }}</td>
              <td>
                <button
                  v-if="key.is_active"
                  @click="handleRevoke(key.id)"
                  class="btn-revoke"
                >
                  Revoke
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import {
  getApiKeys,
  createApiKey,
  revokeApiKey,
  getApps,
  updateApiKeyTags
} from '../services/api'

export default {
  name: 'ApiKeys',
  setup() {
    const apiKeys = ref([])
    const apps = ref([])
    const loading = ref(false)
    const showCreateForm = ref(false)
    const selectedAppId = ref(null)
    const creating = ref(false)
    const error = ref('')
    const newlyCreatedKey = ref(null)
    const newKeyTags = ref([])
    const editingKey = ref(null)
    const editKeyTags = ref([])
    const savingTags = ref(false)
    const editError = ref('')

    const fetchApiKeys = async () => {
      loading.value = true
      try {
        const response = await getApiKeys()
        apiKeys.value = response.data
      } catch (err) {
        console.error('Failed to fetch API keys:', err)
      } finally {
        loading.value = false
      }
    }

    const fetchApps = async () => {
      try {
        const response = await getApps()
        apps.value = response.data
      } catch (err) {
        console.error('Failed to fetch apps:', err)
      }
    }

    const handleCreate = async () => {
      creating.value = true
      error.value = ''

      try {
        // Convert tags array to object
        const tagsObject = {}
        newKeyTags.value.forEach(tag => {
          if (tag.key && tag.value) {
            tagsObject[tag.key] = tag.value
          }
        })
        
        const response = await createApiKey(
          selectedAppId.value, 
          Object.keys(tagsObject).length > 0 ? tagsObject : null
        )
        newlyCreatedKey.value = response.data.key
        selectedAppId.value = null
        newKeyTags.value = []
        showCreateForm.value = false
        await fetchApiKeys()
      } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to create API key'
      } finally {
        creating.value = false
      }
    }

    const cancelCreate = () => {
      showCreateForm.value = false
      selectedAppId.value = null
      newKeyTags.value = []
      error.value = ''
    }

    const addTag = () => {
      newKeyTags.value.push({ key: '', value: '' })
    }

    const removeTag = (index) => {
      newKeyTags.value.splice(index, 1)
    }

    const editTags = (key) => {
      editingKey.value = key
      // Convert tags object to array
      editKeyTags.value = Object.entries(key.tags || {}).map(([k, v]) => ({
        key: k,
        value: v
      }))
      if (editKeyTags.value.length === 0) {
        editKeyTags.value.push({ key: '', value: '' })
      }
      editError.value = ''
    }

    const addEditTag = () => {
      editKeyTags.value.push({ key: '', value: '' })
    }

    const removeEditTag = (index) => {
      editKeyTags.value.splice(index, 1)
    }

    const saveTags = async () => {
      savingTags.value = true
      editError.value = ''

      try {
        // Convert tags array to object
        const tagsObject = {}
        editKeyTags.value.forEach(tag => {
          if (tag.key && tag.value) {
            tagsObject[tag.key] = tag.value
          }
        })

        await updateApiKeyTags(editingKey.value.id, tagsObject)
        editingKey.value = null
        editKeyTags.value = []
        await fetchApiKeys()
      } catch (err) {
        editError.value = err.response?.data?.detail || 'Failed to update tags'
      } finally {
        savingTags.value = false
      }
    }

    const handleRevoke = async (keyId) => {
      if (!confirm('Are you sure you want to revoke this API key?')) {
        return
      }

      try {
        await revokeApiKey(keyId)
        await fetchApiKeys()
      } catch (err) {
        alert('Failed to revoke API key')
      }
    }

    const maskKey = (key) => {
      if (!key) return ''
      const prefix = key.substring(0, 8)
      return `${prefix}${'*'.repeat(20)}`
    }

    const copyKey = () => {
      navigator.clipboard.writeText(newlyCreatedKey.value)
      alert('API key copied to clipboard!')
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString()
    }

    onMounted(() => {
      fetchApiKeys()
      fetchApps()
    })

    return {
      apiKeys,
      apps,
      loading,
      showCreateForm,
      selectedAppId,
      creating,
      error,
      newlyCreatedKey,
      newKeyTags,
      editingKey,
      editKeyTags,
      savingTags,
      editError,
      handleCreate,
      cancelCreate,
      addTag,
      removeTag,
      editTags,
      addEditTag,
      removeEditTag,
      saveTags,
      handleRevoke,
      maskKey,
      copyKey,
      formatDate
    }
  }
}
</script>

<style scoped>
.api-keys-page {
  height: 100%;
  overflow: auto;
  background: var(--bg-primary, #f5f5f5);
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary, #333);
}

.create-form {
  background: var(--bg-card, white);
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--header-shadow, rgba(0, 0, 0, 0.1));
  margin-bottom: 2rem;
  border: 1px solid var(--border-color, #e0e0e0);
}

.create-form h3 {
  margin-top: 0;
  color: var(--text-primary, #333);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary, #555);
  font-weight: 500;
}

.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--input-border, #ddd);
  border-radius: 5px;
  font-size: 1rem;
  background: var(--input-bg, #ffffff);
  color: var(--text-primary, #333);
}

.form-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  transition: opacity 0.3s;
}

.btn-primary {
  background: var(--btn-primary-bg, #667eea);
  color: var(--btn-primary-text, white);
}

.btn-primary:hover {
  background: var(--btn-primary-hover, #5a67d8);
}

.btn-secondary {
  background: var(--btn-secondary-bg, #6c757d);
  color: var(--btn-secondary-text, white);
}

.btn-secondary:hover {
  background: var(--btn-secondary-hover, #5a6268);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(220, 53, 69, 0.1);
  color: var(--color-failure, #dc3545);
  border-radius: 5px;
  border: 1px solid var(--color-failure, #dc3545);
}

.new-key-alert {
  background: rgba(40, 167, 69, 0.1);
  border: 1px solid var(--color-success, #28a745);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.new-key-alert h3 {
  margin-top: 0;
  color: var(--color-success, #28a745);
}

.new-key-alert p {
  color: var(--text-primary, #333);
  margin-bottom: 1rem;
}

.key-display {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.key-display code {
  flex: 1;
  padding: 0.75rem;
  background: var(--code-bg, #f8f9fa);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 5px;
  font-family: var(--theme-font-mono, monospace);
  word-break: break-all;
  color: var(--code-text, #333);
}

.btn-copy {
  padding: 0.75rem 1.5rem;
  background: var(--color-success, #28a745);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
}

.btn-copy:hover {
  opacity: 0.9;
}

.loading,
.no-data {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted, #888);
  background: var(--bg-card, white);
  border-radius: 8px;
  border: 1px solid var(--border-color, #e0e0e0);
}

.keys-table {
  background: var(--bg-card, white);
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--header-shadow, rgba(0, 0, 0, 0.1));
  overflow: hidden;
  border: 1px solid var(--border-color, #e0e0e0);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg-tertiary, #f8f9fa);
}

th {
  text-align: left;
  padding: 1rem;
  font-weight: 600;
  color: var(--text-secondary, #555);
  border-bottom: 2px solid var(--border-color, #dee2e6);
}

tbody {
  background: var(--bg-card, white);
}

td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color, #dee2e6);
  color: var(--text-primary, #333);
}

tr:last-child td {
  border-bottom: none;
}

.key-cell {
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.875rem;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status.active {
  background: rgba(40, 167, 69, 0.2);
  color: var(--color-success, #28a745);
}

.status.inactive {
  background: rgba(220, 53, 69, 0.2);
  color: var(--color-failure, #dc3545);
}

.btn-revoke {
  padding: 0.5rem 1rem;
  background: var(--btn-danger-bg, #dc3545);
  color: var(--btn-danger-text, white);
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
}

.btn-revoke:hover {
  background: var(--btn-danger-hover, #c82333);
}

/* Tags Input */
.tags-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tag-input-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tag-key-input,
.tag-value-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-color, #ccc);
  border-radius: 5px;
  background: var(--bg-card, white);
  color: var(--text-primary, #333);
  font-size: 0.875rem;
}

.tag-key-input {
  max-width: 200px;
}

.btn-remove-tag {
  width: 32px;
  height: 32px;
  padding: 0;
  background: var(--btn-danger-bg, #dc3545);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove-tag:hover {
  background: var(--btn-danger-hover, #c82333);
}

.btn-add-tag {
  align-self: flex-start;
  padding: 0.5rem 1rem;
  background: var(--bg-secondary, #e9ecef);
  color: var(--text-primary, #333);
  border: 1px solid var(--border-color, #ccc);
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-add-tag:hover {
  background: var(--bg-tertiary, #dee2e6);
}

/* Tags Display */
.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  align-items: center;
}

.tag-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--color-primary, #667eea);
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.btn-edit-tags {
  padding: 0.25rem 0.5rem;
  background: transparent;
  color: var(--text-secondary, #666);
  border: 1px solid var(--border-color, #ccc);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-edit-tags:hover {
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-primary, #333);
}

/* Edit Tags Modal */
.edit-tags-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  z-index: 1001;
  background: var(--bg-card, white);
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--text-primary, #333);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
</style>
