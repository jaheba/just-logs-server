import { ref, onMounted } from 'vue'

const sidebarCollapsed = ref(false)
const STORAGE_KEY = 'jlo-sidebar-collapsed'

export function useSidebar() {
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sidebarCollapsed.value))
  }
  
  const collapseSidebar = () => {
    sidebarCollapsed.value = true
    localStorage.setItem(STORAGE_KEY, JSON.stringify(true))
  }
  
  const expandSidebar = () => {
    sidebarCollapsed.value = false
    localStorage.setItem(STORAGE_KEY, JSON.stringify(false))
  }
  
  const initializeSidebar = () => {
    // Check localStorage first
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored !== null) {
      sidebarCollapsed.value = JSON.parse(stored)
      return
    }
    
    // Default based on screen size
    const isMobile = window.innerWidth < 768
    sidebarCollapsed.value = isMobile
  }
  
  return {
    sidebarCollapsed,
    toggleSidebar,
    collapseSidebar,
    expandSidebar,
    initializeSidebar
  }
}
