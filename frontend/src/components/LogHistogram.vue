<template>
  <div class="histogram">
    <div class="histogram-title">Event Frequency</div>
    <div class="histogram-chart">
      <div
        v-for="(bar, index) in histogramData"
        :key="index"
        class="histogram-bar"
        :class="bar.level"
        :style="{ height: `${bar.height}%` }"
        :title="`${bar.count} events at ${bar.time}`"
        @click="$emit('select-time', bar.time)"
      ></div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'LogHistogram',
  props: {
    logs: {
      type: Array,
      default: () => []
    },
    buckets: {
      type: Number,
      default: 20
    }
  },
  emits: ['select-time'],
  setup(props) {
    const histogramData = computed(() => {
      if (!props.logs.length) return []
      
      // Group logs into time buckets
      const now = Date.now()
      const timeRange = 24 * 60 * 60 * 1000 // 24 hours
      const bucketSize = timeRange / props.buckets
      
      const buckets = Array(props.buckets).fill(null).map((_, i) => ({
        time: new Date(now - timeRange + (i * bucketSize)),
        count: 0,
        errors: 0,
        warnings: 0,
        height: 0,
        level: 'info'
      }))
      
      // Count logs in each bucket
      props.logs.forEach(log => {
        const logTime = new Date(log.timestamp).getTime()
        const bucketIndex = Math.floor((logTime - (now - timeRange)) / bucketSize)
        
        if (bucketIndex >= 0 && bucketIndex < props.buckets) {
          buckets[bucketIndex].count++
          
          if (log.level === 'ERROR' || log.level === 'FATAL') {
            buckets[bucketIndex].errors++
          } else if (log.level === 'WARN') {
            buckets[bucketIndex].warnings++
          }
        }
      })
      
      // Calculate heights and determine level
      const maxCount = Math.max(...buckets.map(b => b.count), 1)
      
      buckets.forEach(bucket => {
        bucket.height = (bucket.count / maxCount) * 100
        
        if (bucket.errors > 0) {
          bucket.level = 'error'
        } else if (bucket.warnings > 0) {
          bucket.level = 'warn'
        } else {
          bucket.level = 'info'
        }
      })
      
      return buckets
    })
    
    return {
      histogramData
    }
  }
}
</script>

<style scoped>
.histogram {
  background: var(--bg-secondary, #1a1a1a);
  border-bottom: 1px solid var(--border-color, #333);
  padding: 0.5rem 0.75rem;
  height: 80px;
}

.histogram-title {
  font-size: 0.625rem;
  color: var(--text-muted, #999);
  margin-bottom: 0.375rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.histogram-chart {
  display: flex;
  align-items: flex-end;
  gap: 1px;
  height: 50px;
}

.histogram-bar {
  flex: 1;
  background: var(--level-info, #17a2b8);
  border-radius: 2px 2px 0 0;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  min-height: 2px;
}

.histogram-bar:hover {
  opacity: 0.8;
  transform: translateY(-2px);
}

.histogram-bar.error {
  background: var(--level-error, #dc3545);
}

.histogram-bar.warn {
  background: var(--level-warn, #ffc107);
}

.histogram-bar.info {
  background: var(--level-info, #17a2b8);
}
</style>
