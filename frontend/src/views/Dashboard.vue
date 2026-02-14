<template>
  <div class="discover-page">
    <div class="main-layout">
      <!-- Main Content -->
      <main class="content">
        <FilterBar
          v-model:filters="filters"
          :apps="apps"
          :sidebar-collapsed="sidebarCollapsed"
          :sidebar-header-hovered="sidebarHeaderHovered"
          :new-log-received="newLogCounter"
          @apply="applyFilters"
          @export="handleExport"
          @save-query="handleSaveQuery"
          @toggle-sidebar="toggleSidebar"
          @sidebar-hover="sidebarHeaderHovered = $event"
        />
        
        <!-- Histogram -->
        <LogHistogram
          :logs="logs"
          @select-time="handleSelectTime"
        />
        
        <!-- Stats Bar -->
        <div class="stats-bar">
          <div class="stat">
            <span class="stat-value">{{ totalLogs.toLocaleString() }}</span> events
          </div>
          <div class="stat">
            showing <span class="stat-value">{{ logs.length }}</span> of <span class="stat-value">{{ totalLogs.toLocaleString() }}</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ errorCount }}</span> errors
          </div>
          <div class="stat">
            <span class="stat-value">{{ warningCount }}</span> warnings
          </div>
        </div>
        
        <!-- Logs Container -->
        <div class="logs-container" @scroll="handleScroll">
          <div v-if="loading" class="loading-overlay">
            <div class="spinner"></div>
            <span>Loading logs...</span>
          </div>
          
          <div v-else-if="logs.length === 0" class="no-data">
            <font-awesome-icon icon="inbox" class="icon" />
            <p>No logs found</p>
            <span class="hint">Try adjusting your filters or time range</span>
          </div>
          
          <template v-else>
            <LogEntryCard
              v-for="(log, index) in logs"
              :key="log.id"
              :log="log"
              :index="index"
              @filter-add="handleFilterAdd"
              @filter-exclude="handleFilterExclude"
              @select-tag="handleSelectTag"
            />
            
            <!-- Loading more indicator -->
            <div v-if="loadingMore" class="loading-more">
              <div class="spinner-small"></div>
              <span>Loading more logs...</span>
            </div>
            
            <!-- End of logs indicator -->
            <div v-else-if="!hasMoreLogs && logs.length > 0" class="end-of-logs">
              <span>No more logs to load</span>
            </div>
          </template>
        </div>
      </main>
      
      <!-- Right Sidebar (Signals) -->
      <SignalsSidebar
        :collapsed="sidebarCollapsed"
        :hovered="sidebarHeaderHovered"
        :apps="apps"
        :selected-app="filters.app_id"
        :active-levels="activeLevels"
        :available-tags="availableTags"
        :selected-tags="filters.tags"
        @select-signal="handleSelectSignal"
        @select-app="handleSelectApp"
        @select-tag="handleSelectTag"
        @load-query="handleLoadQuery"
        @toggle="toggleSidebar"
        @header-hover="sidebarHeaderHovered = $event"
      />
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import {
  getLogs,
  getLogsCount,
  getApps,
  exportLogs,
  createLogStream,
  getLogTags
} from '../services/api'
import { useSidebar } from '../composables/useSidebar'
import FilterBar from '../components/FilterBar.vue'
import LogHistogram from '../components/LogHistogram.vue'
import LogEntryCard from '../components/LogEntryCard.vue'
import SignalsSidebar from '../components/SignalsSidebar.vue'

export default {
  name: 'Dashboard',
  components: {
    FilterBar,
    LogHistogram,
    LogEntryCard,
    SignalsSidebar
  },
  setup() {
    const { sidebarCollapsed, initializeSidebar, toggleSidebar } = useSidebar()
    
    const logs = ref([])
    const apps = ref([])
    const loading = ref(false)
    const loadingMore = ref(false)
    const totalLogs = ref(0)
    const limit = ref(100)
    const offset = ref(0)
    const activeLevels = ref([])
    const hasMoreLogs = ref(true)
    const newLogCounter = ref(0)
    const sidebarHeaderHovered = ref(false)
    let eventSource = null
    let autoRefreshInterval = null
    
    const filters = ref({
      app_id: null,
      level: null, // Can be null, a string, or an array of strings
      search: null,
      tags: {}, // Tag filters: { env: 'prod', region: 'us-east' }
      timeRange: {
        from: null,
        to: null,
        label: 'Last 24 hours'
      },
      realtime: false,
      autoRefresh: 'off'
    })
    
    const availableTags = ref({})
    
    const currentPage = computed(() => Math.floor(offset.value / limit.value) + 1)
    
    const errorCount = computed(() => {
      return logs.value.filter(log => log.level === 'ERROR' || log.level === 'FATAL').length
    })
    
    const warningCount = computed(() => {
      return logs.value.filter(log => log.level === 'WARN').length
    })
    
    const fetchLogs = async (append = false) => {
      if (append) {
        loadingMore.value = true
      } else {
        loading.value = true
      }
      
      try {
        const params = {
          app_id: filters.value.app_id,
          search: filters.value.search,
          limit: limit.value,
          offset: offset.value
        }
        
        // Handle level/levels parameter
        if (filters.value.level) {
          if (Array.isArray(filters.value.level)) {
            params.levels = filters.value.level.join(',')
          } else {
            params.level = filters.value.level
          }
        }
        
        // Handle tags parameter
        if (Object.keys(filters.value.tags).length > 0) {
          params.tags = Object.entries(filters.value.tags)
            .map(([k, v]) => `${k}=${v}`)
            .join(',')
        }
        
        // Add time range if set
        if (filters.value.timeRange.from) {
          params.start_time = filters.value.timeRange.from
          params.end_time = filters.value.timeRange.to
        }
        
        const response = await getLogs(params)
        
        if (append) {
          // Append new logs for infinite scroll
          logs.value = [...logs.value, ...response.data]
          hasMoreLogs.value = response.data.length === limit.value
        } else {
          // Replace logs for new search/filter
          logs.value = response.data
          hasMoreLogs.value = response.data.length === limit.value
          
          // Fetch total count only on initial load
          const countParams = {
            app_id: filters.value.app_id,
            search: filters.value.search,
            start_time: filters.value.timeRange.from,
            end_time: filters.value.timeRange.to
          }
          
          // Handle level/levels parameter for count
          if (filters.value.level) {
            if (Array.isArray(filters.value.level)) {
              countParams.levels = filters.value.level.join(',')
            } else {
              countParams.level = filters.value.level
            }
          }
          
          // Handle tags parameter for count
          if (Object.keys(filters.value.tags).length > 0) {
            countParams.tags = Object.entries(filters.value.tags)
              .map(([k, v]) => `${k}=${v}`)
              .join(',')
          }
          
          const countResponse = await getLogsCount(countParams)
          totalLogs.value = countResponse.data.total
        }
      } catch (error) {
        console.error('Failed to fetch logs:', error)
      } finally {
        if (append) {
          loadingMore.value = false
        } else {
          loading.value = false
        }
      }
    }
    
    const fetchApps = async () => {
      try {
        const response = await getApps()
        apps.value = response.data
      } catch (error) {
        console.error('Failed to fetch apps:', error)
      }
    }
    
    const fetchAvailableTags = async () => {
      try {
        const response = await getLogTags()
        availableTags.value = response.data.tags || {}
      } catch (error) {
        console.error('Failed to fetch tags:', error)
      }
    }
    
    const loadMoreLogs = async () => {
      if (loadingMore.value || loading.value || !hasMoreLogs.value) {
        return
      }
      
      offset.value += limit.value
      await fetchLogs(true)
    }
    
    const handleScroll = (event) => {
      const container = event.target
      const scrollPosition = container.scrollTop + container.clientHeight
      const scrollHeight = container.scrollHeight
      
      // Load more when within 300px of bottom
      if (scrollHeight - scrollPosition < 300 && hasMoreLogs.value && !loadingMore.value && !loading.value) {
        loadMoreLogs()
      }
    }
    
    const applyFilters = () => {
      offset.value = 0
      hasMoreLogs.value = true
      updateURLHash()
      fetchLogs()
    }
    
    const handleSort = (field) => {
      console.log('Sort by:', field)
      // TODO: Implement sorting
    }
    
    const handleExpand = (logId, expanded) => {
      console.log('Expanded:', logId, expanded)
    }
    
    const prevPage = () => {
      if (offset.value >= limit.value) {
        offset.value -= limit.value
        fetchLogs()
      }
    }
    
    const nextPage = () => {
      if (offset.value + limit.value < totalLogs.value) {
        offset.value += limit.value
        fetchLogs()
      }
    }
    
    const handleExport = async (format) => {
      try {
        const params = {
          app_id: filters.value.app_id,
          level: filters.value.level,
          search: filters.value.search,
          start_time: filters.value.timeRange.from,
          end_time: filters.value.timeRange.to
        }
        
        const response = await exportLogs(format, params)
        
        if (format === 'csv') {
          const blob = new Blob([response.data], { type: 'text/csv' })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `logs-${Date.now()}.csv`
          a.click()
          window.URL.revokeObjectURL(url)
        } else {
          const blob = new Blob([JSON.stringify(response.data, null, 2)], {
            type: 'application/json'
          })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `logs-${Date.now()}.json`
          a.click()
          window.URL.revokeObjectURL(url)
        }
      } catch (error) {
        console.error('Export failed:', error)
      }
    }
    
    const handleSaveQuery = () => {
      const queryName = prompt('Enter a name for this query:')
      if (queryName) {
        const savedQueries = JSON.parse(localStorage.getItem('jlo-saved-queries') || '[]')
        savedQueries.push({
          id: Date.now(),
          name: queryName,
          filters: { ...filters.value },
          createdAt: new Date().toISOString()
        })
        localStorage.setItem('jlo-saved-queries', JSON.stringify(savedQueries))
        alert('Query saved!')
      }
    }
    
    const handleSelectTime = (time) => {
      // Handle time selection from histogram
      console.log('Selected time:', time)
      // TODO: Implement time-based filtering
    }
    
    const handleFilterAdd = (key, value) => {
      console.log('Add filter:', key, value)
      // TODO: Add to search query
    }
    
    const handleFilterExclude = (key, value) => {
      console.log('Exclude filter:', key, value)
      // TODO: Add exclusion to search query
    }
    
    const handleSelectSignal = (signal) => {
      console.log('Selected signal:', signal)
      
      if (signal.filter.level === null) {
        // "All Levels" selected - clear all level filters
        activeLevels.value = []
        filters.value.level = null
        window.location.hash = filters.value.app_id ? `app=${filters.value.app_id}` : ''
      } else {
        // Toggle the level
        const level = signal.filter.level
        const index = activeLevels.value.indexOf(level)
        
        if (index > -1) {
          // Level already selected, remove it
          activeLevels.value.splice(index, 1)
        } else {
          // Add the level
          activeLevels.value.push(level)
        }
        
        // Update filters based on active levels
        if (activeLevels.value.length === 0) {
          filters.value.level = null
        } else if (activeLevels.value.length === 1) {
          filters.value.level = activeLevels.value[0]
        } else {
          filters.value.level = activeLevels.value
        }
        
        // Update URL hash
        updateURLHash()
      }
      
      fetchLogs()
    }
    
    const handleSelectTag = (key, value) => {
      // Toggle tag filter
      if (filters.value.tags[key] === value) {
        delete filters.value.tags[key]  // Deselect
      } else {
        filters.value.tags[key] = value  // Select
      }
      updateURLHash()
      fetchLogs()
    }
    
    const updateURLHash = () => {
      const hashParams = []
      if (activeLevels.value.length > 0) {
        hashParams.push(`levels=${activeLevels.value.join(',')}`)
      }
      if (filters.value.app_id) {
        hashParams.push(`app=${filters.value.app_id}`)
      }
      if (Object.keys(filters.value.tags).length > 0) {
        const tagStr = Object.entries(filters.value.tags)
          .map(([k, v]) => `${k}:${v}`)
          .join(',')
        hashParams.push(`tags=${tagStr}`)
      }
      if (filters.value.search) {
        hashParams.push(`search=${encodeURIComponent(filters.value.search)}`)
      }
      window.location.hash = hashParams.length > 0 ? hashParams.join('&') : ''
    }
    
    const handleSelectApp = (app) => {
      // Toggle app selection - if already selected, unselect it
      if (filters.value.app_id === app.id) {
        filters.value.app_id = null
      } else {
        filters.value.app_id = app.id
      }
      updateURLHash()
      fetchLogs()
    }
    
    const handleLoadQuery = (query) => {
      filters.value = { ...query.filters }
      fetchLogs()
    }
    
    const startRealtimeStream = () => {
      if (eventSource) {
        eventSource.close()
      }
      
      eventSource = createLogStream(
        (newLog) => {
          logs.value.unshift(newLog)
          if (logs.value.length > limit.value) {
            logs.value.pop()
          }
          totalLogs.value++
          newLogCounter.value++ // Trigger animation
        },
        (error) => {
          console.error('SSE error:', error)
          filters.value.realtime = false
        }
      )
    }
    
    const stopRealtimeStream = () => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }
    
    const setupAutoRefresh = () => {
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval)
        autoRefreshInterval = null
      }
      
      if (filters.value.autoRefresh !== 'off' && !filters.value.realtime) {
        const intervals = {
          '5s': 5000,
          '10s': 10000,
          '30s': 30000,
          '1m': 60000,
          '5m': 300000
        }
        
        const interval = intervals[filters.value.autoRefresh]
        if (interval) {
          autoRefreshInterval = setInterval(() => {
            fetchLogs()
          }, interval)
        }
      }
    }
    
    // Watch for realtime toggle
    watch(() => filters.value.realtime, (newVal) => {
      if (newVal) {
        startRealtimeStream()
        setupAutoRefresh() // This will stop auto-refresh if realtime is on
      } else {
        stopRealtimeStream()
      }
    })
    
    // Watch for auto-refresh changes
    watch(() => filters.value.autoRefresh, () => {
      setupAutoRefresh()
    })
    
    const applyHashFilters = () => {
      const hash = window.location.hash.slice(1) // Remove the # character
      if (!hash) {
        activeLevels.value = [] // Clear active levels
        filters.value.level = null
        filters.value.app_id = null
        filters.value.search = null
        return
      }
      
      const params = new URLSearchParams(hash)
      
      // Handle multiple levels filter from hash
      const levelsParam = params.get('levels')
      if (levelsParam) {
        activeLevels.value = levelsParam.split(',').map(l => l.trim().toUpperCase())
        if (activeLevels.value.length === 1) {
          filters.value.level = activeLevels.value[0]
        } else {
          filters.value.level = activeLevels.value
        }
      } else {
        activeLevels.value = []
        filters.value.level = null
      }
      
      // Handle app filter from hash
      const app = params.get('app')
      if (app) {
        filters.value.app_id = parseInt(app)
      } else {
        filters.value.app_id = null
      }
      
      // Handle tags filter from hash
      const tagsParam = params.get('tags')
      if (tagsParam) {
        filters.value.tags = {}
        tagsParam.split(',').forEach(tag => {
          const [key, value] = tag.split(':')
          if (key && value) {
            filters.value.tags[key.trim()] = value.trim()
          }
        })
      } else {
        filters.value.tags = {}
      }
      
      // Handle search filter from hash
      const searchParam = params.get('search')
      if (searchParam) {
        filters.value.search = decodeURIComponent(searchParam)
      } else {
        filters.value.search = null
      }
    }
    
    // Handle browser back/forward button
    const handleHashChange = () => {
      applyHashFilters()
      fetchLogs()
    }
    
    onMounted(() => {
      initializeSidebar() // Initialize sidebar collapsed state
      applyHashFilters() // Apply filters from URL hash first
      fetchLogs()
      fetchApps()
      fetchAvailableTags()
      
      // Listen for hash changes (back/forward navigation)
      window.addEventListener('hashchange', handleHashChange)
    })
    
    onUnmounted(() => {
      stopRealtimeStream()
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval)
      }
      window.removeEventListener('hashchange', handleHashChange)
    })
    
    return {
      sidebarCollapsed,
      sidebarHeaderHovered,
      toggleSidebar,
      newLogCounter,
      logs,
      apps,
      loading,
      loadingMore,
      hasMoreLogs,
      totalLogs,
      limit,
      offset,
      filters,
      currentPage,
      errorCount,
      warningCount,
      activeLevels,
      availableTags,
      applyFilters,
      handleSort,
      handleExpand,
      handleScroll,
      prevPage,
      nextPage,
      handleExport,
      handleSaveQuery,
      handleSelectTime,
      handleFilterAdd,
      handleFilterExclude,
      handleSelectSignal,
      handleSelectApp,
      handleSelectTag,
      handleLoadQuery
    }
  }
}
</script>

<style scoped>
.discover-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--bg-primary, #1a1a1a);
}

.main-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  order: 1;
}

/* Stats Bar */
.stats-bar {
  padding: 0.375rem 0.75rem;
  background: var(--bg-secondary, #1a1a1a);
  border-bottom: 1px solid var(--border-color, #333);
  display: flex;
  gap: 1.25rem;
  font-size: 0.6875rem;
}

.stat {
  color: var(--text-muted, #999);
}

.stat-value {
  color: var(--color-primary, #667eea);
  font-weight: 600;
}

/* Logs Container */
.logs-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.2rem 0.4rem;
  background: var(--bg-secondary, #1a1a1a);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem;
  color: var(--text-muted, #666);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #333);
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
  color: var(--text-muted, #666);
}

.no-data .icon {
  font-size: 3rem;
  color: var(--text-muted, #666);
}

.no-data p {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
  color: var(--text-primary, #e0e0e0);
}

.no-data .hint {
  font-size: 0.875rem;
  opacity: 0.7;
}

/* Scrollbar styling */
.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: var(--bg-primary, #1a1a1a);
}

.logs-container::-webkit-scrollbar-thumb {
  background: var(--border-color, #333);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: var(--border-secondary, #444);
}

/* Loading more indicator */
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.5rem;
  color: var(--text-muted, #666);
  font-size: 0.875rem;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color, #333);
  border-top-color: var(--color-primary, #667eea);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.end-of-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  color: var(--text-muted, #666);
  font-size: 0.875rem;
  opacity: 0.7;
}
</style>
