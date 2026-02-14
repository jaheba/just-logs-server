<template>
  <AppLayout v-if="isAuthenticated">
    <router-view />
  </AppLayout>
  <router-view v-else />
  
  <!-- Command Palette - always available -->
  <CommandPalette />
</template>

<script>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from './composables/useTheme'
import AppLayout from './components/AppLayout.vue'
import CommandPalette from './components/CommandPalette.vue'

export default {
  name: 'App',
  components: {
    AppLayout,
    CommandPalette
  },
  setup() {
    const route = useRoute()
    const { loadTheme } = useTheme()
    
    const isAuthenticated = computed(() => {
      return route.path !== '/login'
    })
    
    onMounted(() => {
      loadTheme()
    })
    
    return {
      isAuthenticated
    }
  }
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>
