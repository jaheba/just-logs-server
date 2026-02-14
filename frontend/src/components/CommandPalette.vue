<template>
  <teleport to="body">
    <div v-if="isOpen" class="command-palette-overlay" @click="close">
      <div class="command-palette" @click.stop>
        <div class="search-section">
          <div class="search-input-wrapper">
            <font-awesome-icon icon="search" class="search-icon" />
            <input
              ref="searchInput"
              v-model="searchQuery"
              type="text"
              class="search-input"
              :placeholder="currentView === 'main' ? 'Type a command or search...' : 'Search themes...'"
              @keydown.down.prevent="selectNext"
              @keydown.up.prevent="selectPrevious"
              @keydown.enter.prevent="executeSelected"
              @keydown.esc="close"
            />
          </div>
        </div>
        
        <div class="results-section">
          <div v-if="currentView === 'main'" class="results-list">
            <div
              v-for="(command, index) in filteredCommands"
              :key="command.id"
              class="result-item"
              :class="{ selected: index === selectedIndex }"
              @click="executeCommand(command)"
              @mouseenter="selectedIndex = index"
            >
              <div class="result-icon">
                <font-awesome-icon :icon="command.icon" />
              </div>
              <div class="result-content">
                <div class="result-title">{{ command.title }}</div>
                <div class="result-description">{{ command.description }}</div>
              </div>
              <div v-if="command.action === 'submenu'" class="result-arrow">
                <font-awesome-icon icon="chevron-right" />
              </div>
            </div>
            
            <div v-if="filteredCommands.length === 0" class="no-results">
              No commands found
            </div>
          </div>
          
          <div v-else-if="currentView === 'themes'" class="results-list">
            <div class="theme-mode-selector">
              <button
                v-for="mode in themeModes"
                :key="mode.value"
                class="mode-btn"
                :class="{ active: themeMode === mode.value }"
                @click="setThemeMode(mode.value)"
              >
                <font-awesome-icon :icon="mode.icon" />
                <span>{{ mode.label }}</span>
              </button>
            </div>
            
            <div class="theme-divider"></div>
            
            <div
              v-for="(theme, index) in filteredThemes"
              :key="theme.id"
              class="result-item"
              :class="{ selected: index === selectedIndex }"
              @click="selectTheme(theme)"
              @mouseenter="selectedIndex = index"
            >
              <div class="result-icon">
                <font-awesome-icon icon="palette" />
              </div>
              <div class="result-content">
                <div class="result-title">{{ theme.name }}</div>
                <div class="result-description">{{ theme.description }}</div>
              </div>
              <div v-if="isCurrentTheme(theme)" class="result-check">
                <font-awesome-icon icon="check" />
              </div>
            </div>
            
            <div v-if="filteredThemes.length === 0" class="no-results">
              No themes found
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useTheme } from '../composables/useTheme'
import { useRouter } from 'vue-router'

export default {
  name: 'CommandPalette',
  setup() {
    const isOpen = ref(false)
    const searchQuery = ref('')
    const currentView = ref('main')
    const selectedIndex = ref(0)
    const searchInput = ref(null)
    const router = useRouter()
    
    const { currentTheme, setTheme } = useTheme()
    const themeMode = ref('auto')
    
    const themeModes = [
      { value: 'light', label: 'Light', icon: 'sun' },
      { value: 'dark', label: 'Dark', icon: 'moon' },
      { value: 'auto', label: 'Auto', icon: 'circle-half-stroke' }
    ]
    
    const themeList = [
      { id: 'logs', name: 'Logs', description: 'Clean, professional log viewing theme' },
      { id: 'terminal', name: 'Terminal', description: 'Classic terminal aesthetic with green accent' },
      { id: 'paper', name: 'Paper', description: 'Document/paper-like aesthetic with warm tones' },
      { id: 'sap', name: 'SAP Fiori', description: 'SAP design system with blue accent' },
      { id: 'agent-47', name: 'Agent 47', description: 'Hitman-inspired dark theme (dark only)' }
    ]
    
    const commands = [
      {
        id: 'themes',
        title: 'Change Theme...',
        description: 'Switch between light, dark, and color themes',
        icon: 'palette',
        action: 'submenu',
        keywords: ['theme', 'color', 'appearance', 'dark', 'light']
      },
      {
        id: 'events',
        title: 'Go to Events',
        description: 'View all log events',
        icon: 'chart-bar',
        action: 'navigate',
        path: '/',
        keywords: ['events', 'logs', 'discover', 'home']
      },
      {
        id: 'apps',
        title: 'Go to Apps',
        description: 'Manage applications',
        icon: 'box',
        action: 'navigate',
        path: '/apps',
        keywords: ['apps', 'applications', 'manage']
      },
      {
        id: 'settings',
        title: 'Go to Settings',
        description: 'API keys and configuration',
        icon: 'cog',
        action: 'navigate',
        path: '/api-keys',
        keywords: ['settings', 'api', 'keys', 'config', 'configuration']
      }
    ]
    
    const filteredCommands = computed(() => {
      if (!searchQuery.value) return commands
      
      const query = searchQuery.value.toLowerCase()
      return commands.filter(cmd => {
        return cmd.title.toLowerCase().includes(query) ||
               cmd.description.toLowerCase().includes(query) ||
               cmd.keywords.some(k => k.includes(query))
      })
    })
    
    const filteredThemes = computed(() => {
      if (!searchQuery.value) return themeList
      
      const query = searchQuery.value.toLowerCase()
      return themeList.filter(theme => {
        return theme.name.toLowerCase().includes(query) ||
               theme.description.toLowerCase().includes(query)
      })
    })
    
    const open = () => {
      isOpen.value = true
      currentView.value = 'main'
      searchQuery.value = ''
      selectedIndex.value = 0
      
      nextTick(() => {
        searchInput.value?.focus()
      })
    }
    
    const close = () => {
      isOpen.value = false
      searchQuery.value = ''
      currentView.value = 'main'
      selectedIndex.value = 0
    }
    
    const selectNext = () => {
      const maxIndex = currentView.value === 'main' 
        ? filteredCommands.value.length - 1
        : filteredThemes.value.length - 1
      
      if (selectedIndex.value < maxIndex) {
        selectedIndex.value++
      }
    }
    
    const selectPrevious = () => {
      if (selectedIndex.value > 0) {
        selectedIndex.value--
      }
    }
    
    const executeCommand = (command) => {
      if (command.action === 'submenu') {
        if (command.id === 'themes') {
          currentView.value = 'themes'
          selectedIndex.value = 0
          searchQuery.value = ''
        }
      } else if (command.action === 'navigate') {
        router.push(command.path)
        close()
      }
    }
    
    const executeSelected = () => {
      if (currentView.value === 'main') {
        if (filteredCommands.value.length > 0) {
          executeCommand(filteredCommands.value[selectedIndex.value])
        }
      } else if (currentView.value === 'themes') {
        if (filteredThemes.value.length > 0) {
          selectTheme(filteredThemes.value[selectedIndex.value])
        }
      }
    }
    
    const setThemeMode = (mode) => {
      themeMode.value = mode
    }
    
    const getThemeIdForMode = (baseTheme) => {
      if (themeMode.value === 'light') {
        // Agent-47 has -light suffix, others don't
        if (baseTheme.id === 'agent-47') {
          return 'agent-47-light'
        }
        return baseTheme.id
      } else if (themeMode.value === 'dark') {
        // Agent-47 dark has no suffix, others have -dark
        if (baseTheme.id === 'agent-47') {
          return 'agent-47'
        }
        return `${baseTheme.id}-dark`
      } else { // auto
        // Detect system preference
        const prefersDark = window.matchMedia && 
                           window.matchMedia('(prefers-color-scheme: dark)').matches
        if (baseTheme.id === 'agent-47') {
          return prefersDark ? 'agent-47' : 'agent-47-light'
        }
        return prefersDark ? `${baseTheme.id}-dark` : baseTheme.id
      }
    }
    
    const selectTheme = (theme) => {
      const themeId = getThemeIdForMode(theme)
      setTheme(themeId)
      close()
    }
    
    const isCurrentTheme = (theme) => {
      const themeId = getThemeIdForMode(theme)
      return currentTheme.value === themeId
    }
    
    const handleKeyDown = (e) => {
      // Ctrl + P
      if (e.ctrlKey && !e.shiftKey && !e.metaKey && !e.altKey && e.key === 'p') {
        e.preventDefault()
        if (isOpen.value) {
          close()
        } else {
          open()
        }
      }
      
      // Escape to close
      if (e.key === 'Escape' && isOpen.value) {
        close()
      }
    }
    
    watch(searchQuery, () => {
      selectedIndex.value = 0
    })
    
    onMounted(() => {
      window.addEventListener('keydown', handleKeyDown)
    })
    
    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeyDown)
    })
    
    return {
      isOpen,
      searchQuery,
      currentView,
      selectedIndex,
      searchInput,
      filteredCommands,
      filteredThemes,
      themeModes,
      themeMode,
      themeList,
      open,
      close,
      selectNext,
      selectPrevious,
      executeCommand,
      executeSelected,
      setThemeMode,
      selectTheme,
      isCurrentTheme
    }
  }
}
</script>

<style scoped>
.command-palette-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  z-index: 10000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  animation: fadeIn 0.15s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.command-palette {
  width: 100%;
  max-width: 600px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.search-section {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.search-input-wrapper {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #999);
  font-size: 0.875rem;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.75rem 0.75rem 0.75rem 2.5rem;
  background: var(--input-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  color: var(--text-primary, #333);
  font-size: 1rem;
  font-family: var(--theme-font);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-input::placeholder {
  color: var(--text-muted, #999);
}

.results-section {
  max-height: 400px;
  overflow-y: auto;
}

.results-list {
  padding: 0.5rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.result-item:hover,
.result-item.selected {
  background: var(--bg-tertiary, #f5f5f5);
}

.result-icon {
  font-size: 1.25rem;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-primary, #333);
  margin-bottom: 0.125rem;
}

.result-description {
  font-size: 0.8125rem;
  color: var(--text-muted, #888);
}

.result-arrow {
  color: var(--text-muted, #999);
  font-size: 1rem;
  flex-shrink: 0;
}

.result-check {
  color: var(--color-primary, #667eea);
  font-size: 1.125rem;
  font-weight: 600;
  flex-shrink: 0;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted, #888);
  font-size: 0.875rem;
}

/* Theme Mode Selector */
.theme-mode-selector {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--bg-tertiary, #f5f5f5);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.mode-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  color: var(--text-primary, #333);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
}

.mode-btn:hover {
  background: var(--bg-secondary, #f9f9f9);
  border-color: var(--color-primary, #667eea);
}

.mode-btn.active {
  background: var(--color-primary, #667eea);
  border-color: var(--color-primary, #667eea);
  color: #ffffff;
}

.theme-divider {
  height: 1px;
  background: var(--border-color, #e0e0e0);
  margin: 0.5rem 0;
}

/* Scrollbar */
.results-section::-webkit-scrollbar {
  width: 8px;
}

.results-section::-webkit-scrollbar-track {
  background: var(--bg-tertiary, #f5f5f5);
}

.results-section::-webkit-scrollbar-thumb {
  background: var(--border-color, #ddd);
  border-radius: 4px;
}

.results-section::-webkit-scrollbar-thumb:hover {
  background: var(--border-secondary, #ccc);
}

/* Responsive */
@media (max-width: 768px) {
  .command-palette-overlay {
    padding-top: 10vh;
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  .results-section {
    max-height: 300px;
  }
  
  .theme-mode-selector {
    flex-direction: column;
  }
}
</style>
