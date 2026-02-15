<template>
  <div class="filter-bar">
    <div class="filter-container">
      <!-- Search Row -->
      <div class="search-row">
        <div class="search-container">
          <font-awesome-icon icon="search" class="search-icon" />
          <input
            v-model="localFilters.search"
            type="text"
            class="search-input"
            placeholder='@Level = "Error" or @Message contains "timeout"'
            @keyup.enter="$emit('apply')"
          />
        </div>
        <div class="query-actions">
          <button
            @click="handleLiveToggle"
            class="live-btn"
            :class="{ active: localFilters.realtime, 'new-log': showNewLogAnimation }"
            :title="localFilters.realtime ? 'Live updates ON - Click to pause' : 'Click to refresh and enable live updates'"
          >
            <font-awesome-icon :icon="localFilters.realtime ? 'bolt' : 'play'" class="live-icon" />
            <span>{{ localFilters.realtime ? 'LIVE' : 'Run' }}</span>
          </button>
          <button
            @click="toggleSidebar"
            @mouseenter="$emit('sidebar-hover', true)"
            @mouseleave="$emit('sidebar-hover', false)"
            class="sidebar-toggle-btn"
            :class="{ collapsed: sidebarCollapsed, hovered: sidebarHeaderHovered }"
            :title="sidebarCollapsed ? 'Show filters' : 'Hide filters'"
          >
            <font-awesome-icon :icon="sidebarCollapsed ? 'chevron-left' : 'chevron-right'" />
          </button>
        </div>
      </div>
      
      <!-- Filter Row -->
      <div class="filter-row">
        <div class="filter-chips">
          <div v-if="localFilters.level" class="filter-chip">
            <span class="chip-label">Level:</span>
            <span class="chip-value">{{ localFilters.level }}</span>
            <span class="chip-remove" @click="localFilters.level = null">
              <font-awesome-icon icon="times" />
            </span>
          </div>
          <div v-if="localFilters.app_id" class="filter-chip">
            <span class="chip-label">App:</span>
            <span class="chip-value">{{ getAppName(localFilters.app_id) }}</span>
            <span class="chip-remove" @click="localFilters.app_id = null">
              <font-awesome-icon icon="times" />
            </span>
          </div>
          <div 
            v-for="(value, key) in localFilters.tags" 
            :key="`tag-${key}`" 
            class="filter-chip tag-chip"
          >
            <span class="chip-label">{{ key }}:</span>
            <span class="chip-value">{{ value }}</span>
            <span class="chip-remove" @click="removeTagFilter(key)">
              <font-awesome-icon icon="times" />
            </span>
          </div>
        </div>
        
        <select v-model="localFilters.timeRange.label" class="time-selector">
          <option>All</option>
          <option>Last 15 minutes</option>
          <option>Last hour</option>
          <option selected>Last 24 hours</option>
          <option>Last 7 days</option>
          <option>Custom range...</option>
        </select>
      </div>
    </div>
    
    <!-- Custom Date Range Modal -->
    <div v-if="showCustomDateModal" class="modal-overlay" @click="closeCustomDateModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Custom Date Range</h3>
          <button @click="closeCustomDateModal" class="modal-close">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <div class="date-input-group">
            <label>From</label>
            <input 
              v-model="customDateFrom" 
              type="datetime-local" 
              class="date-input"
            />
          </div>
          <div class="date-input-group">
            <label>To</label>
            <input 
              v-model="customDateTo" 
              type="datetime-local" 
              class="date-input"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCustomDateModal" class="btn-secondary">Cancel</button>
          <button @click="applyCustomDateRange" class="btn-primary">Apply</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import TimeRangePicker from './TimeRangePicker.vue'

export default {
  name: 'FilterBar',
  components: {
    TimeRangePicker
  },
  props: {
    filters: {
      type: Object,
      required: true
    },
    apps: {
      type: Array,
      default: () => []
    },
    sidebarCollapsed: {
      type: Boolean,
      default: true
    },
    sidebarHeaderHovered: {
      type: Boolean,
      default: false
    },
    newLogReceived: {
      type: Number,
      default: 0
    }
  },
  emits: ['update:filters', 'apply', 'export', 'save-query', 'toggle-sidebar', 'sidebar-hover'],
  setup(props, { emit }) {
    const showNewLogAnimation = ref(false)
    
    // Watch for new log notifications
    watch(() => props.newLogReceived, (newVal, oldVal) => {
      if (newVal > oldVal && props.filters.realtime) {
        showNewLogAnimation.value = true
        setTimeout(() => {
          showNewLogAnimation.value = false
        }, 800) // Animation duration
      }
    })
    
    // Initialize time range with actual dates
    const initTimeRange = () => {
      const now = new Date()
      const from = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
      const to = now.toISOString()
      return {
        from,
        to,
        label: props.filters.timeRange?.label || 'All'
      }
    }
    
    const localFilters = ref({
      app_id: props.filters.app_id,
      level: props.filters.level,
      search: props.filters.search,
      tags: props.filters.tags || {},
      timeRange: props.filters.timeRange?.from ? { ...props.filters.timeRange } : initTimeRange(),
      realtime: props.filters.realtime,
      autoRefresh: props.filters.autoRefresh
    })
    
    // Custom date range modal state
    const showCustomDateModal = ref(false)
    const customDateFrom = ref('')
    const customDateTo = ref('')
    
    const formatDateForInput = (isoString) => {
      if (!isoString) return ''
      const date = new Date(isoString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day}T${hours}:${minutes}`
    }
    
    const openCustomDateModal = () => {
      customDateFrom.value = formatDateForInput(localFilters.value.timeRange.from)
      customDateTo.value = formatDateForInput(localFilters.value.timeRange.to)
      showCustomDateModal.value = true
    }
    
    const closeCustomDateModal = () => {
      showCustomDateModal.value = false
      // Reset to previous label if user cancels
      if (localFilters.value.timeRange.label === 'Custom range...') {
        localFilters.value.timeRange.label = 'All'
      }
    }
    
    const applyCustomDateRange = () => {
      if (!customDateFrom.value || !customDateTo.value) {
        alert('Please select both start and end dates')
        return
      }
      
      const from = new Date(customDateFrom.value).toISOString()
      const to = new Date(customDateTo.value).toISOString()
      
      if (from >= to) {
        alert('Start date must be before end date')
        return
      }
      
      localFilters.value.timeRange.from = from
      localFilters.value.timeRange.to = to
      localFilters.value.timeRange.label = `${customDateFrom.value} to ${customDateTo.value}`
      
      showCustomDateModal.value = false
      emit('update:filters', { ...localFilters.value })
      emit('apply')
    }
    
    const handleLiveToggle = () => {
      if (localFilters.value.realtime) {
        // Currently live - pause it
        localFilters.value.realtime = false
        emit('update:filters', { ...localFilters.value })
      } else {
        // Currently paused - refresh and enable live
        emit('apply')
        localFilters.value.realtime = true
        emit('update:filters', { ...localFilters.value })
      }
    }
    
    const toggleSidebar = () => {
      emit('toggle-sidebar')
    }
    
    const getAppName = (appId) => {
      const app = props.apps.find(a => a.id === appId)
      return app ? app.name : 'Unknown'
    }
    
    const removeTagFilter = (key) => {
      delete localFilters.value.tags[key]
      emit('update:filters', { ...localFilters.value })
    }
    
    // Watch for changes that need immediate sync
    watch(() => localFilters.value.realtime, () => {
      emit('update:filters', { ...localFilters.value })
    })
    
    watch(() => localFilters.value.level, () => {
      emit('update:filters', { ...localFilters.value })
    })
    
    watch(() => localFilters.value.app_id, () => {
      emit('update:filters', { ...localFilters.value })
    })
    
    watch(() => localFilters.value.search, () => {
      emit('update:filters', { ...localFilters.value })
    })
    
    watch(() => localFilters.value.timeRange, () => {
      emit('update:filters', { ...localFilters.value })
    }, { deep: true })
    
    // Watch for time range label changes and calculate actual dates
    watch(() => localFilters.value.timeRange.label, (newLabel) => {
      if (newLabel === 'Custom range...') {
        openCustomDateModal()
        return
      }
      
      const now = new Date()
      let from = null
      let to = now.toISOString()
      
      switch (newLabel) {
        case 'All':
          from = null
          to = null
          break
        case 'Last 15 minutes':
          from = new Date(now.getTime() - 15 * 60 * 1000).toISOString()
          break
        case 'Last hour':
          from = new Date(now.getTime() - 60 * 60 * 1000).toISOString()
          break
        case 'Last 24 hours':
          from = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
          break
        case 'Last 7 days':
          from = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
          break
        default:
          from = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
      }
      
      localFilters.value.timeRange.from = from
      localFilters.value.timeRange.to = to
      emit('update:filters', { ...localFilters.value })
      emit('apply')
    })
    
    // Initialize time range on mount
    onMounted(() => {
      if (!props.filters.timeRange?.from) {
        emit('update:filters', { ...localFilters.value })
      }
    })
    
    return {
      localFilters,
      showNewLogAnimation,
      handleLiveToggle,
      toggleSidebar,
      getAppName,
      removeTagFilter,
      showCustomDateModal,
      customDateFrom,
      customDateTo,
      closeCustomDateModal,
      applyCustomDateRange
    }
  }
}
</script>

<style scoped>
.filter-bar {
  background: var(--bg-secondary, #1a1a1a);
  border-bottom: 1px solid var(--border-color, #333);
}

.filter-container {
  padding: 0.5rem 0.75rem;
  padding-right: 40px; /* Reserve space for fixed sidebar toggle button */
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Search Row */
.search-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.search-container {
  position: relative;
  flex: 1;
}

.search-input {
  width: 100%;
  padding: 0.625rem 0.75rem 0.625rem 2rem;
  background: var(--bg-primary, #0d0d0d);
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.8125rem;
  font-family: var(--theme-font-mono, monospace);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
}

.search-icon {
  position: absolute;
  left: 0.625rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #666);
  font-size: 0.875rem;
}

.query-actions {
  display: flex;
  gap: 0.375rem;
  flex-shrink: 0;
}

.live-btn {
  padding: 0.625rem 1rem;
  background: var(--color-primary, #667eea);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 0.8125rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  font-weight: 600;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.live-btn:hover {
  background: var(--color-secondary, #5a67d8);
  transform: translateY(-1px);
}

.live-btn.active {
  background: var(--color-danger, #dc3545);
  color: white;
  animation: pulse 2s ease-in-out infinite;
  position: relative;
}

.live-icon {
  font-size: 0.875rem;
}

.live-btn.active .live-icon {
  animation: bolt-flash 1.5s ease-in-out infinite;
}

/* New log received animation */
.live-btn.active.new-log {
  animation: pulse 2s ease-in-out infinite, border-sweep 0.8s ease-out;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(220, 53, 69, 0);
  }
}

@keyframes bolt-flash {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes border-sweep {
  0% {
    box-shadow: 
      0 0 0 0 rgba(220, 53, 69, 0.7),
      0 -2px 8px 2px rgba(255, 255, 255, 0.8),
      0 0 0 0 transparent,
      0 0 0 0 transparent,
      0 0 0 0 transparent;
  }
  25% {
    box-shadow: 
      0 0 0 0 rgba(220, 53, 69, 0.7),
      0 0 0 0 transparent,
      2px 0 8px 2px rgba(255, 255, 255, 0.8),
      0 0 0 0 transparent,
      0 0 0 0 transparent;
  }
  50% {
    box-shadow: 
      0 0 0 0 rgba(220, 53, 69, 0.7),
      0 0 0 0 transparent,
      0 0 0 0 transparent,
      0 2px 8px 2px rgba(255, 255, 255, 0.8),
      0 0 0 0 transparent;
  }
  75% {
    box-shadow: 
      0 0 0 0 rgba(220, 53, 69, 0.7),
      0 0 0 0 transparent,
      0 0 0 0 transparent,
      0 0 0 0 transparent,
      -2px 0 8px 2px rgba(255, 255, 255, 0.8);
  }
  100% {
    box-shadow: 
      0 0 0 0 rgba(220, 53, 69, 0.7),
      0 -2px 8px 2px rgba(255, 255, 255, 0),
      0 0 0 0 transparent,
      0 0 0 0 transparent,
      0 0 0 0 transparent;
  }
}

/* Sidebar Toggle Button */
.sidebar-toggle-btn {
  position: fixed;
  right: 220px; /* Positioned at left edge of sidebar when expanded */
  top: 44px; /* Aligned with sidebar header */
  width: 32px;
  height: 44px;
  padding: 0;
  background: var(--bg-tertiary, #e9ecef);
  border: 1px solid var(--border-color, #e0e0e0);
  border-right: none;
  border-top: 1px solid var(--border-color, #e0e0e0);
  border-bottom: 1px solid var(--border-color, #333);
  border-radius: 6px 0 0 0;
  color: var(--text-secondary, #666);
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: right 0.3s ease, background 0.2s ease;
  z-index: 102; /* Above sidebar so it's always clickable */
  box-shadow: -2px 0 4px rgba(0, 0, 0, 0.05);
}

/* When hovering button OR when sidebar header is hovered, both change background */
.sidebar-toggle-btn:not(.collapsed):hover,
.sidebar-toggle-btn:not(.collapsed).hovered {
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-primary, #333);
}

.sidebar-toggle-btn.collapsed {
  right: 0; /* Moves to right edge when sidebar collapses */
  border-radius: 6px 0 0 6px;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-toggle-btn.collapsed:hover {
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-primary, #333);
}

/* Filter Row */
.filter-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.filter-chips {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
  flex: 1;
}

.filter-chip {
  padding: 0.25rem 0.5rem;
  background: var(--bg-tertiary, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 12px;
  font-size: 0.6875rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.chip-label {
  color: var(--color-primary, #667eea);
  font-weight: 600;
}

.chip-value {
  color: var(--text-primary, #e0e0e0);
}

.chip-remove {
  color: var(--text-muted, #999);
  cursor: pointer;
  font-weight: bold;
  font-size: 0.875rem;
  padding: 0 0.125rem;
  transition: color 0.2s;
}

.chip-remove:hover {
  color: var(--level-error, #dc3545);
}

.tag-chip {
  background: var(--color-primary, #667eea);
  color: white;
}

.tag-chip .chip-label,
.tag-chip .chip-value {
  color: white;
  font-family: var(--theme-font-mono, monospace);
}

.time-selector {
  padding: 0.375rem 0.625rem;
  background: var(--bg-tertiary, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 3px;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.75rem;
  cursor: pointer;
  margin-left: auto;
  font-family: inherit;
}

.time-selector:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
}

/* Custom Date Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-secondary, #1a1a1a);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color, #333);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.125rem;
  color: var(--text-primary, #e0e0e0);
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted, #999);
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.modal-close:hover {
  color: var(--text-primary, #e0e0e0);
}

.modal-body {
  padding: 1.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.date-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.date-input-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary, #e0e0e0);
}

.date-input {
  padding: 0.625rem 0.75rem;
  background: var(--bg-primary, #0d0d0d);
  border: 1px solid var(--border-color, #444);
  border-radius: 4px;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.875rem;
  font-family: var(--theme-font-mono, monospace);
}

.date-input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
}

/* Chrome/Safari datetime-local styling */
.date-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-color, #333);
}

.btn-primary,
.btn-secondary {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--color-primary, #667eea);
  color: white;
}

.btn-primary:hover {
  background: var(--color-secondary, #5a67d8);
}

.btn-secondary {
  background: var(--bg-tertiary, #2a2a2a);
  color: var(--text-primary, #e0e0e0);
  border: 1px solid var(--border-color, #444);
}

.btn-secondary:hover {
  background: var(--bg-sidebar-hover, #333);
}
</style>
