import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentUser } from '../services/api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/apps',
    name: 'Apps',
    component: () => import('../views/Apps.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/api-keys',
    name: 'ApiKeys',
    component: () => import('../views/ApiKeys.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication and authorization
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  
  if (requiresAuth) {
    try {
      const response = await getCurrentUser()
      const user = response.data
      
      // Check admin requirement
      if (requiresAdmin && user.role !== 'admin') {
        // Redirect non-admin users away from admin pages
        next('/')
        return
      }
      
      next()
    } catch (error) {
      next('/login')
    }
  } else {
    next()
  }
})

export default router
