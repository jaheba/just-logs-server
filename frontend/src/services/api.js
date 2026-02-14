import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Authentication
export const login = (username, password) => {
  return api.post('/auth/login', { username, password })
}

export const logout = () => {
  return api.post('/auth/logout')
}

export const getCurrentUser = () => {
  return api.get('/auth/me')
}

// Applications
export const getApps = () => {
  return api.get('/apps')
}

export const createApp = (name) => {
  return api.post('/apps', { name })
}

// API Keys
export const getApiKeys = () => {
  return api.get('/api-keys')
}

export const createApiKey = (appId, tags = null) => {
  return api.post('/api-keys', { app_id: appId, tags })
}

export const revokeApiKey = (keyId) => {
  return api.delete(`/api-keys/${keyId}`)
}

export const updateApiKeyTags = (keyId, tags) => {
  return api.put(`/api-keys/${keyId}/tags`, tags)
}

// Logs
export const getLogs = (params) => {
  return api.get('/logs', { params })
}

export const getLogsCount = (params) => {
  return api.get('/logs/count', { params })
}

export const getLogTags = () => {
  return api.get('/logs/tags')
}

export const exportLogs = (format, params) => {
  return api.get('/logs/export', {
    params: { ...params, format },
    responseType: format === 'csv' ? 'blob' : 'json'
  })
}

// SSE for real-time logs
export const createLogStream = (onMessage, onError) => {
  const eventSource = new EventSource('/api/logs/stream', {
    withCredentials: true
  })
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (error) {
      console.error('Failed to parse SSE message:', error)
    }
  }
  
  eventSource.onerror = (error) => {
    if (onError) {
      onError(error)
    }
    eventSource.close()
  }
  
  return eventSource
}

// User Management
export const getUsers = () => {
  return api.get('/users')
}

export const getUser = (userId) => {
  return api.get(`/users/${userId}`)
}

export const createUser = (userData) => {
  return api.post('/users', userData)
}

export const updateUser = (userId, userData) => {
  return api.put(`/users/${userId}`, userData)
}

export const deleteUser = (userId) => {
  return api.delete(`/users/${userId}`)
}

export const changePassword = (passwordData) => {
  return api.post('/auth/change-password', passwordData)
}

export const resetUserPassword = (userId, passwordData) => {
  return api.post(`/users/${userId}/reset-password`, passwordData)
}

// Retention Policies
export const getRetentionPolicies = (appId = null) => {
  const params = appId !== null ? { app_id: appId } : {}
  return api.get('/retention-policies', { params })
}

export const getAppRetentionPolicies = (appId) => {
  return api.get(`/apps/${appId}/retention-policies`)
}

export const createRetentionPolicy = (policy) => {
  return api.post('/retention-policies', policy)
}

export const updateRetentionPolicy = (policyId, updates) => {
  return api.put(`/retention-policies/${policyId}`, updates)
}

export const deleteRetentionPolicy = (policyId) => {
  return api.delete(`/retention-policies/${policyId}`)
}

// Retention Cleanup Operations
export const runRetentionCleanup = (appId = null) => {
  const params = appId !== null ? { app_id: appId } : {}
  return api.post('/retention/run-cleanup', null, { params })
}

export const previewRetentionCleanup = (appId = null) => {
  const params = appId !== null ? { app_id: appId } : {}
  return api.get('/retention/preview', { params })
}

export const getRetentionRuns = (limit = 20, offset = 0) => {
  return api.get('/retention/runs', { params: { limit, offset } })
}

export const getRetentionRun = (runId) => {
  return api.get(`/retention/runs/${runId}`)
}

export default api
