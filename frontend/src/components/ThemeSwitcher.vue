<template>
  <button @click="cycleMode" class="theme-mode-toggle" :title="`Theme mode: ${currentModeLabel}`">
    <font-awesome-icon :icon="currentModeIcon" />
  </button>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useTheme } from '../composables/useTheme'

export default {
  name: 'ThemeSwitcher',
  setup() {
    const { currentTheme, setTheme } = useTheme()
    const themeMode = ref('auto')
    
    const themeModes = [
      { value: 'auto', label: 'Auto', icon: 'circle-half-stroke' },
      { value: 'light', label: 'Light', icon: 'sun' },
      { value: 'dark', label: 'Dark', icon: 'moon' }
    ]
    
    const currentModeIcon = computed(() => {
      const mode = themeModes.find(m => m.value === themeMode.value)
      return mode ? mode.icon : 'circle-half-stroke'
    })
    
    const currentModeLabel = computed(() => {
      const mode = themeModes.find(m => m.value === themeMode.value)
      return mode ? mode.label : 'Auto'
    })
    
    const cycleMode = () => {
      const currentIndex = themeModes.findIndex(m => m.value === themeMode.value)
      const nextIndex = (currentIndex + 1) % themeModes.length
      themeMode.value = themeModes[nextIndex].value
      
      // Save to localStorage
      try {
        localStorage.setItem('jlo-theme-mode', themeMode.value)
      } catch (e) {
        console.error('Failed to save theme mode:', e)
      }
    }
    
    const getBaseTheme = (themeId) => {
      // Extract base theme name (remove -dark or -light suffix)
      return themeId.replace('-dark', '').replace('-light', '')
    }
    
    const applyThemeMode = () => {
      const baseTheme = getBaseTheme(currentTheme.value)
      let newThemeId = baseTheme
      
      if (themeMode.value === 'light') {
        // Agent-47 has -light suffix, others don't
        if (baseTheme === 'agent-47') {
          newThemeId = 'agent-47-light'
        } else {
          newThemeId = baseTheme
        }
      } else if (themeMode.value === 'dark') {
        // Agent-47 dark has no suffix, others have -dark
        if (baseTheme === 'agent-47') {
          newThemeId = 'agent-47'
        } else {
          newThemeId = `${baseTheme}-dark`
        }
      } else { // auto
        const prefersDark = window.matchMedia && 
                           window.matchMedia('(prefers-color-scheme: dark)').matches
        if (baseTheme === 'agent-47') {
          newThemeId = prefersDark ? 'agent-47' : 'agent-47-light'
        } else {
          newThemeId = prefersDark ? `${baseTheme}-dark` : baseTheme
        }
      }
      
      if (newThemeId !== currentTheme.value) {
        setTheme(newThemeId)
      }
    }
    
    // Load saved mode on mount
    try {
      const savedMode = localStorage.getItem('jlo-theme-mode')
      if (savedMode && themeModes.find(m => m.value === savedMode)) {
        themeMode.value = savedMode
      }
    } catch (e) {
      console.error('Failed to load theme mode:', e)
    }
    
    // Watch for mode changes and apply
    watch(themeMode, () => {
      applyThemeMode()
    })
    
    // Listen for system theme changes in auto mode
    if (window.matchMedia) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')
      darkModeQuery.addEventListener('change', () => {
        if (themeMode.value === 'auto') {
          applyThemeMode()
        }
      })
    }

    return {
      themeMode,
      currentModeIcon,
      currentModeLabel,
      cycleMode
    }
  }
}
</script>

<style scoped>
.theme-mode-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
  color: var(--text-sidebar-muted, #999);
}

.theme-mode-toggle:hover {
  background: var(--bg-sidebar-hover, #2a2a2a);
  color: var(--text-sidebar, #e0e0e0);
}
</style>
