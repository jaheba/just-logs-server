<template>
  <div class="log-table-container">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>Loading logs...</span>
    </div>
    
    <div v-else-if="logs.length === 0" class="no-data">
      <font-awesome-icon icon="inbox" class="icon" />
      <p>No logs found</p>
      <span class="hint">Try adjusting your filters or time range</span>
    </div>
    
    <table v-else class="log-table">
      <thead>
        <tr>
          <th class="col-expand"></th>
          <th class="col-timestamp" @click="$emit('sort', 'timestamp')">
            Timestamp
            <span class="sort-indicator">↕</span>
          </th>
          <th class="col-level" @click="$emit('sort', 'level')">
            Level
            <span class="sort-indicator">↕</span>
          </th>
          <th class="col-app" @click="$emit('sort', 'app_name')">
            Application
            <span class="sort-indicator">↕</span>
          </th>
          <th class="col-message">Message</th>
          <th class="col-actions">Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="log in logs" :key="log.id">
          <!-- Main row -->
          <tr
            class="log-row"
            :class="{
              expanded: expandedRows.has(log.id),
              [`level-${log.level.toLowerCase()}`]: true
            }"
            @click="toggleRow(log.id)"
          >
            <td class="col-expand">
              <button class="expand-btn">
                <font-awesome-icon :icon="expandedRows.has(log.id) ? 'chevron-down' : 'chevron-right'" />
              </button>
            </td>
            <td class="col-timestamp">
              <span class="timestamp">{{ formatTimestamp(log.timestamp) }}</span>
            </td>
            <td class="col-level">
              <span class="level-badge" :class="`level-${log.level.toLowerCase()}`">
                {{ log.level }}
              </span>
            </td>
            <td class="col-app">
              <span class="app-name">{{ log.app_name }}</span>
            </td>
            <td class="col-message">
              <span class="message-text">{{ truncateMessage(log.message) }}</span>
            </td>
            <td class="col-actions">
              <button
                @click.stop="copyLog(log)"
                class="action-btn"
                title="Copy log entry"
              >
                <font-awesome-icon icon="copy" />
              </button>
            </td>
          </tr>
          
          <!-- Expanded row -->
          <tr v-if="expandedRows.has(log.id)" class="expanded-row">
            <td colspan="6" class="expanded-content">
              <div class="expanded-inner">
                <div class="detail-section">
                  <h4>Full Message</h4>
                  <pre class="message-full">{{ log.message }}</pre>
                </div>
                
                <div v-if="log.structured_data" class="detail-section">
                  <h4>Structured Data</h4>
                  <pre class="structured-data">{{ formatJSON(log.structured_data) }}</pre>
                </div>
                
                <div v-if="log.parsed_fields" class="detail-section">
                  <h4>Parsed Fields</h4>
                  <pre class="parsed-fields">{{ formatJSON(log.parsed_fields) }}</pre>
                </div>
                
                <div class="detail-section metadata">
                  <h4>Metadata</h4>
                  <div class="metadata-grid">
                    <div class="metadata-item">
                      <span class="label">Log ID:</span>
                      <span class="value">{{ log.id }}</span>
                    </div>
                    <div class="metadata-item">
                      <span class="label">Client Timestamp:</span>
                      <span class="value">{{ new Date(log.timestamp).toISOString() }}</span>
                    </div>
                    <div v-if="log.server_timestamp" class="metadata-item">
                      <span class="label">Server Timestamp:</span>
                      <span class="value">{{ new Date(log.server_timestamp).toISOString() }}</span>
                    </div>
                    <div v-if="log.parser_rule_id" class="metadata-item">
                      <span class="label">Parser Rule ID:</span>
                      <span class="value">{{ log.parser_rule_id }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
import { ref, onUnmounted } from 'vue'

export default {
  name: 'LogTable',
  props: {
    logs: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['sort', 'expand'],
  setup(props, { emit }) {
    const expandedRows = ref(new Set())
    const currentTime = ref(Date.now())
    
    // Update current time every 30 seconds (not every render)
    const timeInterval = setInterval(() => {
      currentTime.value = Date.now()
    }, 30000)
    
    // Clean up interval on unmount
    onUnmounted(() => {
      clearInterval(timeInterval)
    })
    
    const toggleRow = (logId) => {
      if (expandedRows.value.has(logId)) {
        expandedRows.value.delete(logId)
      } else {
        expandedRows.value.add(logId)
      }
      emit('expand', logId, expandedRows.value.has(logId))
    }
    
    const formatTimestamp = (timestamp) => {
      const date = new Date(timestamp)
      const diffMs = currentTime.value - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    }
    
    const truncateMessage = (message, maxLength = 100) => {
      if (!message) return ''
      if (message.length <= maxLength) return message
      return message.substring(0, maxLength) + '...'
    }
    
    const formatJSON = (data) => {
      try {
        return JSON.stringify(data, null, 2)
      } catch (e) {
        return String(data)
      }
    }
    
    const copyLog = (log) => {
      const text = JSON.stringify(log, null, 2)
      navigator.clipboard.writeText(text).then(() => {
        // Could show a toast notification here
        console.log('Log copied to clipboard')
      })
    }
    
    return {
      expandedRows,
      toggleRow,
      formatTimestamp,
      truncateMessage,
      formatJSON,
      copyLog
    }
  }
}
</script>

<style scoped>
.log-table-container {
  position: relative;
  height: 100%;
  overflow: auto;
  background: var(--bg-secondary, #ffffff);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem;
  color: var(--text-muted, #888);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #ddd);
  border-top-color: var(--color-primary, #667eea);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem;
  color: var(--text-muted, #888);
}

.no-data .icon {
  font-size: 3rem;
}

.no-data p {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.no-data .hint {
  font-size: 0.875rem;
  opacity: 0.7;
}

.log-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.875rem;
}

thead {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-tertiary, #f5f5f5);
}

th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary, #555);
  border-bottom: 2px solid var(--border-color, #ddd);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

th:hover {
  background: var(--bg-secondary, #e9ecef);
}

.sort-indicator {
  opacity: 0.3;
  margin-left: 0.25rem;
  font-size: 0.75rem;
}

th:hover .sort-indicator {
  opacity: 0.6;
}

.col-expand {
  width: 40px;
  cursor: default;
}

.col-expand:hover {
  background: var(--bg-tertiary, #f5f5f5);
}

.col-timestamp {
  width: 140px;
}

.col-level {
  width: 100px;
}

.col-app {
  width: 150px;
}

.col-actions {
  width: 60px;
  text-align: center;
}

.log-row {
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  transition: background 0.15s;
  cursor: pointer;
}

.log-row:hover {
  background: var(--bg-tertiary, #f8f9fa);
}

.log-row.level-fatal {
  background: rgba(220, 53, 69, 0.05);
}

td {
  padding: 0.75rem 1rem;
  vertical-align: middle;
}

.expand-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-secondary, #555);
  display: flex;
  align-items: center;
  justify-content: center;
}

.timestamp {
  color: var(--text-muted, #888);
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.8125rem;
}

.level-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.level-badge.level-debug {
  background: rgba(108, 117, 125, 0.15);
  color: var(--level-debug, #6c757d);
}

.level-badge.level-info {
  background: rgba(23, 162, 184, 0.15);
  color: var(--level-info, #17a2b8);
}

.level-badge.level-warn {
  background: rgba(255, 193, 7, 0.15);
  color: var(--level-warn, #ffc107);
}

.level-badge.level-error {
  background: rgba(220, 53, 69, 0.15);
  color: var(--level-error, #dc3545);
}

.level-badge.level-fatal {
  background: rgba(111, 0, 0, 0.15);
  color: var(--level-fatal, #6f0000);
}

.app-name {
  color: var(--color-primary, #667eea);
  font-weight: 500;
}

.message-text {
  color: var(--text-primary, #333);
  word-break: break-word;
}

.action-btn {
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 1rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--bg-tertiary, #f5f5f5);
  border-color: var(--border-color, #ddd);
}

.expanded-row {
  background: var(--bg-primary, #fafafa);
}

.expanded-content {
  padding: 0;
}

.expanded-inner {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  border-left: 3px solid var(--color-primary, #667eea);
}

.detail-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary, #555);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-section pre {
  margin: 0;
  padding: 1rem;
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  overflow-x: auto;
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--text-primary, #333);
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metadata-item .label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metadata-item .value {
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.8125rem;
  color: var(--text-primary, #333);
}

/* Responsive */
@media (max-width: 1024px) {
  .col-timestamp {
    width: 100px;
  }
  
  .col-app {
    width: 100px;
  }
  
  .message-text {
    font-size: 0.8125rem;
  }
}

@media (max-width: 768px) {
  .log-table {
    font-size: 0.8125rem;
  }
  
  th, td {
    padding: 0.5rem;
  }
  
  .col-timestamp,
  .col-app {
    display: none;
  }
  
  .metadata-grid {
    grid-template-columns: 1fr;
  }
}
</style>
