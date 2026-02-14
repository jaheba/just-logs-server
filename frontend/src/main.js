import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './themes.css'

// Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { 
  faSearch,
  faPalette,
  faSun,
  faMoon,
  faCircleHalfStroke,
  faChartBar,
  faBox,
  faCog,
  faChevronRight,
  faChevronLeft,
  faCheck,
  faFilter,
  faTimes,
  faPlay,
  faEye,
  faEyeSlash,
  faChevronDown,
  faChevronUp,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faBug,
  faSkullCrossbones,
  faCopy,
  faFileExport,
  faSave,
  faPlus,
  faTrash,
  faKey,
  faInbox,
  faUser,
  faUserCircle,
  faUsers,
  faUserShield,
  faUserEdit,
  faLock,
  faSignOutAlt,
  faEdit,
  faPen,
  faCheckCircle,
  faTimesCircle
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faSearch,
  faPalette,
  faSun,
  faMoon,
  faCircleHalfStroke,
  faChartBar,
  faBox,
  faCog,
  faChevronRight,
  faChevronLeft,
  faCheck,
  faFilter,
  faTimes,
  faPlay,
  faEye,
  faEyeSlash,
  faChevronDown,
  faChevronUp,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faBug,
  faSkullCrossbones,
  faCopy,
  faFileExport,
  faSave,
  faPlus,
  faTrash,
  faKey,
  faInbox,
  faUser,
  faUserCircle,
  faUsers,
  faUserShield,
  faUserEdit,
  faLock,
  faSignOutAlt,
  faEdit,
  faPen,
  faCheckCircle,
  faTimesCircle
)

const app = createApp(App)
app.component('font-awesome-icon', FontAwesomeIcon)
app.use(router)
app.mount('#app')
