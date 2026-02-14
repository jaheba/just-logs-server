import { ref, onMounted } from 'vue'

const THEME_STORAGE_KEY = 'jlo-theme'
const DEFAULT_THEME = 'logs'

// Available themes
export const themes = [
  { id: 'logs', name: 'Logs Light', dark: false },
  { id: 'logs-dark', name: 'Logs Dark', dark: true },
  { id: 'terminal', name: 'Terminal Light', dark: false },
  { id: 'terminal-dark', name: 'Terminal Dark', dark: true },
  { id: 'paper', name: 'Paper Light', dark: false },
  { id: 'paper-dark', name: 'Paper Dark', dark: true },
  { id: 'sap', name: 'SAP Fiori Light', dark: false },
  { id: 'sap-dark', name: 'SAP Fiori Dark', dark: true },
  { id: 'agent-47-light', name: 'Agent 47 Light', dark: false },
  { id: 'agent-47', name: 'Agent 47 Dark', dark: true }
]

// Shared reactive theme state
const currentTheme = ref(DEFAULT_THEME)

// Setup system theme listener (only once)
let systemThemeListenerInitialized = false

export function useTheme() {
  const loadTheme = () => {
    try {
      const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
      if (savedTheme && themes.find(t => t.id === savedTheme)) {
        currentTheme.value = savedTheme
      } else {
        // Try to detect system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
          currentTheme.value = 'logs-dark'
        } else {
          currentTheme.value = DEFAULT_THEME
        }
      }
    } catch (e) {
      console.error('Failed to load theme:', e)
      currentTheme.value = DEFAULT_THEME
    }
    applyTheme(currentTheme.value)
  }

  const applyTheme = (themeId) => {
    // Remove all theme classes
    themes.forEach(theme => {
      document.body.classList.remove(`theme-${theme.id}`)
    })
    
    // Add the selected theme class
    document.body.classList.add(`theme-${themeId}`)
  }

  const setTheme = (themeId) => {
    if (!themes.find(t => t.id === themeId)) {
      console.warn(`Theme ${themeId} not found, using default`)
      themeId = DEFAULT_THEME
    }
    
    currentTheme.value = themeId
    applyTheme(themeId)
    
    try {
      localStorage.setItem(THEME_STORAGE_KEY, themeId)
    } catch (e) {
      console.error('Failed to save theme:', e)
    }
  }

  const toggleDarkMode = () => {
    const current = themes.find(t => t.id === currentTheme.value)
    if (!current) return

    // Find the opposite theme (light <-> dark) in the same family
    const baseFamily = current.id.replace('-dark', '')
    const targetTheme = current.dark 
      ? baseFamily 
      : `${baseFamily}-dark`
    
    setTheme(targetTheme)
  }

  const isDark = () => {
    const theme = themes.find(t => t.id === currentTheme.value)
    return theme ? theme.dark : false
  }

  const getThemeName = () => {
    const theme = themes.find(t => t.id === currentTheme.value)
    return theme ? theme.name : 'Unknown'
  }

  const initSystemThemeListener = () => {
    if (systemThemeListenerInitialized) return
    
    if (typeof window !== 'undefined' && window.matchMedia) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')
      darkModeQuery.addEventListener('change', (e) => {
        // Only auto-switch if user hasn't set a preference
        try {
          const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
          if (!savedTheme) {
            currentTheme.value = e.matches ? 'logs-dark' : 'logs'
            applyTheme(currentTheme.value)
          }
        } catch (err) {
          console.error('Failed to handle system theme change:', err)
        }
      })
      systemThemeListenerInitialized = true
    }
  }

  // Initialize listener when composable is used
  if (typeof window !== 'undefined') {
    initSystemThemeListener()
  }

  return {
    currentTheme,
    themes,
    loadTheme,
    setTheme,
    toggleDarkMode,
    isDark,
    getThemeName
  }
}
