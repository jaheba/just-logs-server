<template>
  <div class="time-range-picker">
    <button @click="toggleDropdown" class="picker-button" ref="buttonRef">
      <span class="icon">🕒</span>
      <span class="label">{{ displayLabel }}</span>
      <span class="arrow">{{ isOpen ? '▲' : '▼' }}</span>
    </button>
    
    <div v-if="isOpen" class="dropdown" ref="dropdownRef">
      <div class="quick-ranges">
        <h4>Quick ranges</h4>
        <button
          v-for="range in quickRanges"
          :key="range.value"
          @click="selectQuickRange(range)"
          class="range-option"
          :class="{ active: selectedRange === range.value }"
        >
          {{ range.label }}
        </button>
      </div>
      
      <div class="custom-range">
        <h4>Custom range</h4>
        <div class="date-inputs">
          <div class="input-group">
            <label>From</label>
            <input
              type="datetime-local"
              v-model="customFrom"
              @change="onCustomRangeChange"
            />
          </div>
          <div class="input-group">
            <label>To</label>
            <input
              type="datetime-local"
              v-model="customTo"
              @change="onCustomRangeChange"
            />
          </div>
        </div>
        <button @click="applyCustomRange" class="apply-btn">Apply</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

export default {
  name: 'TimeRangePicker',
  props: {
    modelValue: {
      type: Object,
      default: () => ({ from: null, to: null, label: 'Last 24 hours' })
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const isOpen = ref(false)
    const buttonRef = ref(null)
    const dropdownRef = ref(null)
    const selectedRange = ref('24h')
    const customFrom = ref('')
    const customTo = ref('')
    
    const quickRanges = [
      { label: 'Last 15 minutes', value: '15m', minutes: 15 },
      { label: 'Last 1 hour', value: '1h', minutes: 60 },
      { label: 'Last 24 hours', value: '24h', minutes: 1440 },
      { label: 'Last 7 days', value: '7d', minutes: 10080 },
      { label: 'Last 30 days', value: '30d', minutes: 43200 },
      { label: 'Last 90 days', value: '90d', minutes: 129600 }
    ]
    
    const displayLabel = computed(() => {
      return props.modelValue.label || 'Last 24 hours'
    })
    
    const toggleDropdown = () => {
      isOpen.value = !isOpen.value
    }
    
    const selectQuickRange = (range) => {
      selectedRange.value = range.value
      const now = new Date()
      const from = new Date(now.getTime() - range.minutes * 60 * 1000)
      
      emit('update:modelValue', {
        from: from.toISOString(),
        to: now.toISOString(),
        label: range.label
      })
      
      isOpen.value = false
    }
    
    const onCustomRangeChange = () => {
      selectedRange.value = 'custom'
    }
    
    const applyCustomRange = () => {
      if (!customFrom.value || !customTo.value) {
        alert('Please select both start and end dates')
        return
      }
      
      const from = new Date(customFrom.value)
      const to = new Date(customTo.value)
      
      if (from >= to) {
        alert('Start date must be before end date')
        return
      }
      
      const label = `${from.toLocaleString()} - ${to.toLocaleString()}`
      
      emit('update:modelValue', {
        from: from.toISOString(),
        to: to.toISOString(),
        label: 'Custom range'
      })
      
      isOpen.value = false
    }
    
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (
        buttonRef.value &&
        dropdownRef.value &&
        !buttonRef.value.contains(event.target) &&
        !dropdownRef.value.contains(event.target)
      ) {
        isOpen.value = false
      }
    }
    
    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
      
      // Initialize with default range if not set
      if (!props.modelValue.from) {
        selectQuickRange(quickRanges[2]) // Default to 24 hours
      }
    })
    
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })
    
    return {
      isOpen,
      buttonRef,
      dropdownRef,
      selectedRange,
      customFrom,
      customTo,
      quickRanges,
      displayLabel,
      toggleDropdown,
      selectQuickRange,
      onCustomRangeChange,
      applyCustomRange
    }
  }
}
</script>

<style scoped>
.time-range-picker {
  position: relative;
  display: inline-block;
}

.picker-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
  color: var(--text-primary, #333);
}

.picker-button:hover {
  border-color: var(--color-primary, #667eea);
  background: var(--bg-tertiary, #f5f5f5);
}

.picker-button .icon {
  font-size: 1rem;
}

.picker-button .label {
  font-weight: 500;
}

.picker-button .arrow {
  font-size: 0.7rem;
  opacity: 0.7;
}

.dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  min-width: 300px;
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.quick-ranges h4,
.custom-range h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary, #555);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quick-ranges {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color, #ddd);
}

.range-option {
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  font-size: 0.875rem;
  color: var(--text-primary, #333);
  transition: all 0.2s;
}

.range-option:hover {
  background: var(--bg-tertiary, #f5f5f5);
  border-color: var(--border-color, #ddd);
}

.range-option.active {
  background: var(--color-primary, #667eea);
  color: white;
  border-color: var(--color-primary, #667eea);
}

.custom-range {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.date-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.input-group label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary, #555);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-group input {
  padding: 0.5rem;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  font-size: 0.875rem;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #333);
}

.input-group input:focus {
  outline: none;
  border-color: var(--color-primary, #667eea);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.apply-btn {
  padding: 0.5rem 1rem;
  background: var(--color-primary, #667eea);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.apply-btn:hover {
  background: var(--color-secondary, #5a67d8);
}
</style>
