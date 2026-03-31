import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listPlatforms } from '../api/platforms'
import type { Platform } from '../api/types'

const defaultPlatform: Platform = {
  id: 'pdd',
  name: '拼多多',
  icon: '🟠',
}

function getInitialPlatform() {
  if (typeof window === 'undefined') {
    return defaultPlatform.id
  }

  return window.localStorage.getItem('selectedPlatform') || defaultPlatform.id
}

export const usePlatformStore = defineStore('platform', () => {
  const platforms = ref<Platform[]>([defaultPlatform])
  const currentPlatform = ref<string>(getInitialPlatform())

  async function loadPlatforms() {
    try {
      const data = await listPlatforms()
      platforms.value = data.list.length > 0 ? data.list : [defaultPlatform]
    } catch {
      platforms.value = [defaultPlatform]
    }

    if (!platforms.value.some((platform) => platform.id === currentPlatform.value)) {
      const fallbackPlatform = platforms.value[0] ?? defaultPlatform
      setPlatform(fallbackPlatform.id)
    }
  }

  function setPlatform(id: string) {
    currentPlatform.value = id
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('selectedPlatform', id)
    }
  }

  return { platforms, currentPlatform, loadPlatforms, setPlatform }
})
