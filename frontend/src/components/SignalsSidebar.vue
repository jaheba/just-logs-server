<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- Header -->
    <div 
      class="sidebar-header" 
      :class="{ hovered }" 
      @click="$emit('toggle')"
      @mouseenter="$emit('header-hover', true)"
      @mouseleave="$emit('header-hover', false)"
    >
      <span class="sidebar-title">Signals</span>
    </div>
    
    <div class="sidebar-content">
      <div class="signal-group">
        <div class="signal-group-title">By Level</div>
        <div
          v-for="signal in levelSignals"
          :key="signal.id"
          class="signal-item"
          :class="{ active: signal.id === 'all-levels' ? activeLevels.length === 0 : activeLevels.includes(signal.filter.level) }"
          @click="$emit('select-signal', signal)"
        >
          <span v-if="signal.color" class="level-dot" :style="{ backgroundColor: signal.color }"></span>
          {{ signal.name }}
        </div>
      </div>

      <div class="signal-group">
        <div class="signal-group-title">By Application</div>
        <div
          v-for="app in apps"
          :key="app.id"
          class="signal-item"
          :class="{ active: selectedApp === app.id }"
          @click="$emit('select-app', app)"
        >
          {{ app.name }}
        </div>
      </div>

      <div v-if="Object.keys(availableTags).length > 0" class="signal-group">
        <div class="signal-group-title">By Tags</div>
        <div
          v-for="(values, key) in availableTags"
          :key="key"
          class="tag-group"
        >
          <div class="tag-key">{{ key }}</div>
          <div
            v-for="value in values"
            :key="value"
            class="signal-item tag-item"
            :class="{ active: selectedTags[key] === value }"
            @click="$emit('select-tag', key, value)"
          >
            <span class="tag-display">{{ key }}={{ value }}</span>
          </div>
        </div>
      </div>

      <div v-if="savedQueries.length > 0" class="signal-group">
        <div class="signal-group-title">Saved Queries</div>
        <div
          v-for="query in savedQueries"
          :key="query.id"
          class="signal-item"
          @click="$emit('load-query', query)"
        >
          {{ query.name }}
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'SignalsSidebar',
  props: {
    collapsed: {
      type: Boolean,
      default: false
    },
    apps: {
      type: Array,
      default: () => []
    },
    selectedApp: {
      type: Number,
      default: null
    },
    activeLevels: {
      type: Array,
      default: () => []
    },
    availableTags: {
      type: Object,
      default: () => ({})
    },
    selectedTags: {
      type: Object,
      default: () => ({})
    },
    hovered: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select-signal', 'select-app', 'select-tag', 'load-query', 'toggle', 'header-hover'],
  setup() {
    const savedQueries = ref([])
    
    const levelSignals = [
      { id: 'all-levels', name: 'All Levels', filter: { level: null }, color: null },
      { id: 'fatal', name: 'Fatal', filter: { level: 'FATAL' }, color: 'var(--level-fatal, #8b0000)' },
      { id: 'error', name: 'Error', filter: { level: 'ERROR' }, color: 'var(--level-error, #dc3545)' },
      { id: 'warn', name: 'Warning', filter: { level: 'WARN' }, color: 'var(--level-warn, #ffc107)' },
      { id: 'info', name: 'Info', filter: { level: 'INFO' }, color: 'var(--level-info, #17a2b8)' },
      { id: 'debug', name: 'Debug', filter: { level: 'DEBUG' }, color: 'var(--level-debug, #6c757d)' }
    ]
    
    // Load saved queries from localStorage
    try {
      const saved = localStorage.getItem('jlo-saved-queries')
      if (saved) {
        savedQueries.value = JSON.parse(saved)
      }
    } catch (e) {
      console.error('Failed to load saved queries:', e)
    }
    
    return {
      levelSignals,
      savedQueries
    }
  }
}
</script>

<style scoped>
/* Sidebar container - slides with transform */
.sidebar {
  width: 220px;
  background: transparent;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  order: 2;
  position: relative;
  transform: translateX(0);
  transition: transform 0.3s ease, margin-left 0.3s ease;
  z-index: 100;
}

.sidebar.collapsed {
  transform: translateX(220px); /* Slides off-screen to the right */
  margin-left: -220px; /* Gives space back to main content */
}

/* Sidebar header */
.sidebar-header {
  width: 100%;
  height: 44px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-tertiary, #e9ecef);
  border-bottom: 1px solid var(--border-color, #333);
  flex-shrink: 0;
  transition: background 0.2s ease;
  cursor: pointer;
}

/* Hover effect - ONLY when button or header itself is hovered (via .hovered class) */
.sidebar-header.hovered {
  background: var(--bg-secondary, #f5f5f5);
}

.sidebar-title {
  font-weight: 600;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary, #666);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  background: var(--bg-tertiary, #e9ecef);
}

.signal-group {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border-color, #222);
}

.signal-group-title {
  font-size: 0.625rem;
  font-weight: 600;
  color: var(--color-primary, #667eea);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.375rem;
}

.signal-item {
  padding: 0.375rem 0.5rem;
  margin: 0.125rem 0;
  border-radius: 3px;
  font-size: 0.75rem;
  color: var(--text-primary, #333);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.level-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.signal-item:hover {
  background: var(--bg-secondary, #f5f5f5);
  color: var(--text-primary, #333);
}

.signal-item.active {
  background: var(--color-primary, #667eea);
  color: #ffffff;
}

.tag-group {
  margin-top: 0.5rem;
}

.tag-key {
  font-size: 0.625rem;
  font-weight: 600;
  color: var(--text-secondary, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
  padding-left: 0.5rem;
}

.tag-item {
  padding-left: 1rem;
}

.tag-display {
  font-family: var(--theme-font-mono, monospace);
  font-size: 0.7rem;
}

/* Scrollbar styling */
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: var(--bg-tertiary, #e9ecef);
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--border-color, #ddd);
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-secondary, #ccc);
}
</style>
