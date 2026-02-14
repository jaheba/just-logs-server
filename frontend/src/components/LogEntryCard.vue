<template>
  <div class="log-entry" :class="[`level-${log.level.toLowerCase()}`, { expanded, 'log-even': index % 2 === 0, 'log-odd': index % 2 !== 0 }]" @click="toggleExpand">
    <div class="log-header">
      <div class="log-dot"></div>
      <div class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</div>
      <div class="log-level" :class="`level-${log.level.toLowerCase()}`">
        {{ log.level }}
      </div>
      <div class="log-message">
        {{ log.message }}
      </div>
      <div v-if="log.tags && Object.keys(log.tags).length > 0" class="log-tags">
        <span 
          v-for="(value, key) in getVisibleTags(log.tags)" 
          :key="key" 
          class="tag-badge tag-clickable"
          @click.stop="$emit('select-tag', key, value)"
          :title="`Filter by ${key}=${value}`"
        >
          {{ key }}={{ value }}
        </span>
        <span 
          v-if="getHiddenTagCount(log.tags) > 0" 
          class="tag-badge tag-more"
          @click.stop="toggleExpand"
          title="Click to see all tags"
        >
          +{{ getHiddenTagCount(log.tags) }} more
        </span>
      </div>
      <div class="log-expand-icon">
        <font-awesome-icon :icon="expanded ? 'chevron-down' : 'chevron-right'" />
      </div>
    </div>
    
    <div v-if="expanded" class="log-details">
      <div class="property-section">
        <div class="property-title">Full Message</div>
        <pre class="property-grid">{{ log.message }}</pre>
      </div>
      
      <div v-if="log.structured_data" class="property-section">
        <div class="property-title">Structured Data</div>
        <div class="property-grid">
          <div
            v-for="(value, key) in log.structured_data"
            :key="key"
            class="property-row"
          >
            <span class="property-key">{{ key }}:</span>
            <span class="property-value">{{ formatValue(value) }}</span>
            <span class="property-actions">
              <span class="action-icon" title="Include in filter" @click.stop="$emit('filter-add', key, value)">
                <font-awesome-icon icon="check" />
              </span>
              <span class="action-icon" title="Exclude from filter" @click.stop="$emit('filter-exclude', key, value)">
                <font-awesome-icon icon="times" />
              </span>
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="log.parsed_fields" class="property-section">
        <div class="property-title">Parsed Fields</div>
        <div class="property-grid">
          <div
            v-for="(value, key) in log.parsed_fields"
            :key="key"
            class="property-row"
          >
            <span class="property-key">{{ key }}:</span>
            <span class="property-value">{{ formatValue(value) }}</span>
          </div>
        </div>
      </div>
      
      <div v-if="log.tags && Object.keys(log.tags).length > 0" class="property-section">
        <div class="property-title">Tags</div>
        <div class="property-grid">
          <div
            v-for="(value, key) in log.tags"
            :key="key"
            class="property-row"
          >
            <span class="property-key">{{ key }}:</span>
            <span class="property-value">{{ value }}</span>
            <span class="property-actions">
              <span class="action-icon" title="Filter by this tag" @click.stop="$emit('filter-add', key, value)">
                <font-awesome-icon icon="check" />
              </span>
              <span class="action-icon" title="Exclude this tag" @click.stop="$emit('filter-exclude', key, value)">
                <font-awesome-icon icon="times" />
              </span>
            </span>
          </div>
        </div>
      </div>
      
      <div class="property-section">
        <div class="property-title">Metadata</div>
        <div class="property-grid">
          <div class="property-row">
            <span class="property-key">ID:</span>
            <span class="property-value">{{ log.id }}</span>
          </div>
          <div class="property-row">
            <span class="property-key">Application:</span>
            <span class="property-value">{{ log.app_name }}</span>
          </div>
          <div class="property-row">
            <span class="property-key">Client Timestamp:</span>
            <span class="property-value">{{ new Date(log.timestamp).toISOString() }}</span>
          </div>
          <div v-if="log.server_timestamp" class="property-row">
            <span class="property-key">Server Timestamp:</span>
            <span class="property-value">{{ new Date(log.server_timestamp).toISOString() }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onUnmounted } from 'vue'

export default {
  name: 'LogEntryCard',
  props: {
    log: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    }
  },
  emits: ['filter-add', 'filter-exclude', 'select-tag'],
  setup() {
    const expanded = ref(false)
    const currentTime = ref(Date.now())
    
    const timeInterval = setInterval(() => {
      currentTime.value = Date.now()
    }, 30000)
    
    onUnmounted(() => {
      clearInterval(timeInterval)
    })
    
    const toggleExpand = () => {
      expanded.value = !expanded.value
    }
    
    const formatTimestamp = (timestamp) => {
      const date = new Date(timestamp)
      const diffMs = currentTime.value - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)
      
      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    }
    
    const formatValue = (value) => {
      if (typeof value === 'object') {
        return JSON.stringify(value)
      }
      return String(value)
    }
    
    const MAX_VISIBLE_TAGS = 2
    
    const getVisibleTags = (tags) => {
      if (!tags) return {}
      const entries = Object.entries(tags)
      return Object.fromEntries(entries.slice(0, MAX_VISIBLE_TAGS))
    }
    
    const getHiddenTagCount = (tags) => {
      if (!tags) return 0
      return Math.max(0, Object.keys(tags).length - MAX_VISIBLE_TAGS)
    }
    
    return {
      expanded,
      toggleExpand,
      formatTimestamp,
      formatValue,
      getVisibleTags,
      getHiddenTagCount
    }
  }
}
</script>

<style scoped>
.log-entry {
  cursor: pointer;
  transition: all 0.15s;
  border: none;
  margin: 0;
}

.log-entry.log-even {
  background: var(--log-bg-even, rgba(30, 30, 30, 0.6));
}

.log-entry.log-odd {
  background: var(--log-bg-odd, rgba(13, 13, 13, 0.3));
}

.log-entry.log-even:hover {
  background: var(--log-bg-even-hover, rgba(42, 42, 42, 0.8));
}

.log-entry.log-odd:hover {
  background: var(--log-bg-odd-hover, rgba(26, 26, 26, 0.6));
}

.log-header {
  padding: 0.25rem 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.log-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
}

.log-entry.level-error .log-dot {
  background: var(--level-error, #dc3545);
}

.log-entry.level-warn .log-dot {
  background: var(--level-warn, #ffc107);
}

.log-entry.level-info .log-dot {
  background: var(--level-info, #17a2b8);
}

.log-entry.level-debug .log-dot {
  background: var(--level-debug, #6c757d);
}

.log-entry.level-fatal .log-dot {
  background: var(--level-fatal, #6f0000);
}

.log-timestamp {
  color: var(--text-muted, #666);
  font-size: 0.65rem;
  font-family: var(--theme-font-mono, monospace);
  min-width: 55px;
  flex-shrink: 0;
}

.log-level {
  padding: 0.1rem 0.3rem;
  border-radius: 2px;
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  min-width: 42px;
  text-align: center;
  flex-shrink: 0;
  line-height: 1;
}

.log-level.level-error {
  background: rgba(220, 53, 69, 0.2);
  color: var(--level-error, #dc3545);
}

.log-level.level-warn {
  background: rgba(255, 193, 7, 0.2);
  color: var(--level-warn, #ffc107);
}

.log-level.level-info {
  background: rgba(23, 162, 184, 0.2);
  color: var(--level-info, #17a2b8);
}

.log-level.level-debug {
  background: rgba(108, 117, 125, 0.2);
  color: var(--level-debug, #6c757d);
}

.log-level.level-fatal {
  background: rgba(111, 0, 0, 0.2);
  color: var(--level-fatal, #6f0000);
}

.log-message {
  flex: 1;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.8rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.log-tags {
  display: flex;
  gap: 0.3rem;
  flex-wrap: nowrap;
  align-items: center;
  flex-shrink: 0;
}

.tag-badge {
  display: inline-block;
  padding: 0.1rem 0.3rem;
  background: var(--color-primary, #667eea);
  color: white;
  border-radius: 2px;
  font-size: 0.6rem;
  font-weight: 500;
  white-space: nowrap;
  font-family: var(--theme-font-mono, monospace);
  line-height: 1;
}

.tag-badge.tag-clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.tag-badge.tag-clickable:hover {
  background: var(--color-primary-dark, #5568d3);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.tag-badge.tag-more {
  background: var(--bg-tertiary, #2a2a2a);
  color: var(--text-muted, #999);
  cursor: pointer;
  border: 1px dashed var(--border-color, #444);
  transition: all 0.2s;
}

.tag-badge.tag-more:hover {
  background: var(--color-primary, #667eea);
  color: white;
  border-color: var(--color-primary, #667eea);
  border-style: solid;
}

.log-expand-icon {
  color: var(--text-muted, #666);
  font-size: 0.7rem;
  margin-left: 0.25rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

/* Expanded Details */
.log-details {
  padding: 0.5rem 0.5rem 0.5rem 1.5rem;
  border-top: 1px solid var(--border-color, #333);
  background: var(--bg-primary, #0d0d0d);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.property-section {
  margin-bottom: 0.4rem;
}

.property-section:last-child {
  margin-bottom: 0;
}

.property-title {
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--color-primary, #667eea);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.3rem;
}

.property-grid {
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.675rem;
  line-height: 1.4;
  color: var(--text-primary, #e0e0e0);
}

.property-grid pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.property-row {
  display: flex;
  padding: 0.1rem 0;
  gap: 0.5rem;
  align-items: center;
}

.property-row:hover {
  background: var(--bg-tertiary, #1a1a1a);
}

.property-key {
  color: var(--level-info, #17a2b8);
  min-width: 100px;
  flex-shrink: 0;
  font-size: 0.65rem;
}

.property-value {
  color: var(--text-primary, #e0e0e0);
  flex: 1;
  word-break: break-word;
  font-size: 0.65rem;
}

.property-actions {
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.2s;
  display: flex;
  gap: 0.2rem;
}

.property-row:hover .property-actions {
  opacity: 1;
}

.action-icon {
  padding: 0.05rem 0.2rem;
  background: var(--bg-tertiary, #2a2a2a);
  border-radius: 2px;
  cursor: pointer;
  font-size: 0.65rem;
  transition: background 0.2s;
}

.action-icon:hover {
  background: var(--color-primary, #667eea);
  color: #ffffff;
}
</style>
