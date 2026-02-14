<template>
  <div class="app-layout">
    <!-- Top Navigation Bar -->
    <header class="navbar">
      <div class="navbar-left">
        <div class="logo">
          <span class="logo-j">j</span><span class="logo-l">l</span><span class="logo-o">o</span>
        </div>
        
        <nav class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
            Events
          </router-link>
          
          <router-link to="/dashboards" class="nav-link" :class="{ active: $route.path.startsWith('/dashboards') }">
            Dashboards
          </router-link>
          
          <router-link to="/apps" class="nav-link" :class="{ active: $route.path === '/apps' }">
            Apps
          </router-link>
          
          <router-link to="/api-keys" class="nav-link" :class="{ active: $route.path === '/api-keys' }">
            API Keys
          </router-link>
          
          <router-link v-if="isAdmin" to="/users" class="nav-link" :class="{ active: $route.path === '/users' }">
            Users
          </router-link>
          
          <router-link v-if="isAdmin" to="/settings" class="nav-link" :class="{ active: $route.path === '/settings' }">
            Settings
          </router-link>
        </nav>
      </div>
      
      <div class="navbar-right">
        <ThemeSwitcher />
        <div class="user-menu-wrapper" ref="menuWrapper">
          <div class="user-menu" @click="toggleMenu">
            <div class="user-avatar-small">
              {{ getUserInitials() }}
            </div>
            <span class="user-name-text">{{ displayName }}</span>
            <span class="menu-arrow" :class="{ open: showMenu }">▼</span>
          </div>
          
          <transition name="dropdown">
            <div v-if="showMenu" class="dropdown-menu">
              <div class="dropdown-header">
                <div class="dropdown-user-info">
                  <div class="dropdown-avatar">
                    {{ getUserInitials() }}
                  </div>
                  <div class="dropdown-user-details">
                    <div class="dropdown-user-name">{{ displayName }}</div>
                    <div class="dropdown-user-email">{{ currentUser?.email || currentUser?.username }}</div>
                  </div>
                </div>
                <div class="dropdown-role-badge" :class="`role-${currentUser?.role}`">
                  {{ formatRole(currentUser?.role) }}
                </div>
              </div>
              
              <div class="dropdown-divider"></div>
              
              <button @click="goToProfile" class="dropdown-item">
                <font-awesome-icon icon="user" class="dropdown-icon" />
                My Profile
              </button>
              
              <button @click="openChangePassword" class="dropdown-item">
                <font-awesome-icon icon="key" class="dropdown-icon" />
                Change Password
              </button>
              
              <div class="dropdown-divider"></div>
              
              <button @click="handleLogout" class="dropdown-item dropdown-item-danger">
                <font-awesome-icon icon="sign-out-alt" class="dropdown-icon" />
                Logout
              </button>
            </div>
          </transition>
        </div>
      </div>
    </header>
    
    <!-- Content Area -->
    <main class="content">
      <slot />
    </main>
    
    <!-- Change Password Dialog -->
    <ChangePasswordDialog 
      :show="showChangePasswordDialog" 
      @close="showChangePasswordDialog = false"
      @success="handlePasswordChanged"
    />
    
    <!-- Toast Notifications -->
    <Toast />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { logout, getCurrentUser } from '../services/api'
import { useToast } from '../composables/useToast'
import ThemeSwitcher from './ThemeSwitcher.vue'
import ChangePasswordDialog from './ChangePasswordDialog.vue'
import Toast from './Toast.vue'

export default {
  name: 'AppLayout',
  components: {
    ThemeSwitcher,
    ChangePasswordDialog,
    Toast
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { success } = useToast()
    
    const currentUser = ref(null)
    const showMenu = ref(false)
    const showChangePasswordDialog = ref(false)
    const menuWrapper = ref(null)
    
    const fetchCurrentUser = async () => {
      try {
        const response = await getCurrentUser()
        currentUser.value = response.data
      } catch (error) {
        console.error('Failed to fetch current user:', error)
      }
    }
    
    const isAdmin = computed(() => {
      return currentUser.value?.role === 'admin'
    })
    
    const displayName = computed(() => {
      if (!currentUser.value) return 'User'
      return currentUser.value.full_name || currentUser.value.username
    })
    
    const getUserInitials = () => {
      if (!currentUser.value) return 'U'
      
      const name = currentUser.value.full_name || currentUser.value.username
      const parts = name.split(' ')
      
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      }
      
      return name.substring(0, 2).toUpperCase()
    }
    
    const formatRole = (role) => {
      const roles = {
        admin: 'Admin',
        editor: 'Editor',
        viewer: 'Viewer'
      }
      return roles[role] || role
    }
    
    const toggleMenu = () => {
      showMenu.value = !showMenu.value
    }
    
    const goToProfile = () => {
      showMenu.value = false
      router.push('/profile')
    }
    
    const openChangePassword = () => {
      showMenu.value = false
      showChangePasswordDialog.value = true
    }
    
    const handlePasswordChanged = () => {
      success('Password changed successfully')
    }
    
    const handleLogout = async () => {
      showMenu.value = false
      try {
        await logout()
        router.push('/login')
      } catch (error) {
        console.error('Logout failed:', error)
      }
    }
    
    // Close menu when clicking outside
    const handleClickOutside = (event) => {
      if (menuWrapper.value && !menuWrapper.value.contains(event.target)) {
        showMenu.value = false
      }
    }
    
    onMounted(() => {
      fetchCurrentUser()
      document.addEventListener('click', handleClickOutside)
    })
    
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })
    
    return {
      currentUser,
      isAdmin,
      displayName,
      showMenu,
      showChangePasswordDialog,
      menuWrapper,
      getUserInitials,
      formatRole,
      toggleMenu,
      goToProfile,
      openChangePassword,
      handlePasswordChanged,
      handleLogout
    }
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary, #f5f5f5);
}

/* Navbar */
.navbar {
  height: 44px;
  background: var(--bg-sidebar, #1a1a1a);
  border-bottom: 1px solid var(--border-color, #333);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  flex-shrink: 0;
  box-shadow: none;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Logo */
.logo {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.logo-j {
  color: var(--level-fatal);
}

.logo-l {
  color: var(--level-warn);
}

.logo-o {
  color: var(--level-info);
}

/* Navigation Links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.nav-link {
  padding: 0.375rem 0.75rem;
  color: var(--text-sidebar-muted, #999);
  text-decoration: none;
  transition: all 0.2s;
  border-radius: 4px;
  font-weight: 500;
  font-size: 0.8125rem;
  white-space: nowrap;
}

.nav-link:hover {
  background: var(--bg-sidebar-hover, #2a2a2a);
  color: var(--text-sidebar, #e0e0e0);
}

.nav-link.active {
  background: var(--color-primary);
  color: var(--text-on-primary);
}

/* User Menu */
.user-menu-wrapper {
  position: relative;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  background: var(--bg-sidebar-hover, #2a2a2a);
  border-radius: 6px;
  color: var(--text-sidebar, #e0e0e0);
  cursor: pointer;
  font-size: 0.8125rem;
  transition: all 0.2s;
  font-weight: 500;
}

.user-menu:hover {
  background: var(--bg-sidebar-active, #333);
}

.user-avatar-small {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--text-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 700;
}

.user-name-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-arrow {
  font-size: 0.625rem;
  transition: transform 0.2s;
}

.menu-arrow.open {
  transform: rotate(180deg);
}

/* Dropdown Menu */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 280px;
  background: var(--bg-card, white);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  padding: 1rem;
  background: var(--bg-secondary, #f8f9fa);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.dropdown-user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.dropdown-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--text-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 700;
  flex-shrink: 0;
}

.dropdown-user-details {
  flex: 1;
  min-width: 0;
}

.dropdown-user-name {
  font-weight: 600;
  color: var(--text-primary, #333);
  font-size: 0.9375rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-user-email {
  font-size: 0.8125rem;
  color: var(--text-secondary, #666);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-role-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.dropdown-role-badge.role-admin {
  background: var(--color-primary);
  color: var(--text-on-primary);
}

.dropdown-role-badge.role-editor {
  background: var(--color-warning);
  color: var(--text-on-warning);
}

.dropdown-role-badge.role-viewer {
  background: var(--color-info);
  color: var(--text-on-info);
}

.dropdown-divider {
  height: 1px;
  background: var(--border-color, #e0e0e0);
  margin: 0.25rem 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  color: var(--text-primary, #333);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  font-weight: 500;
}

.dropdown-item:hover {
  background: var(--bg-hover, #f0f0f0);
}

.dropdown-item-danger {
  color: var(--color-danger);
}

.dropdown-item-danger:hover {
  background: var(--color-danger);
  color: var(--text-on-danger);
}

.dropdown-icon {
  width: 16px;
  margin-right: 0.5rem;
}



/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Content Area */
.content {
  flex: 1;
  overflow: auto;
  background: var(--bg-primary, #f5f5f5);
}

/* Responsive */
@media (max-width: 768px) {
  .navbar {
    padding: 0 0.75rem;
  }
  
  .navbar-left {
    gap: 1rem;
  }
  
  .nav-links {
    gap: 0.125rem;
  }
  
  .nav-link {
    padding: 0.375rem 0.5rem;
    font-size: 0.75rem;
  }
  
  .logo {
    font-size: 1.125rem;
  }
  
  .user-menu {
    font-size: 0.75rem;
    padding: 0.375rem 0.5rem;
  }
  
  .user-name-text {
    max-width: 80px;
  }
  
  .dropdown-menu {
    min-width: 260px;
  }
}
</style>
