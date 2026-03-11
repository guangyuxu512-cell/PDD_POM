import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentShop = ref<string | null>(null)
  const theme = ref<'dark' | 'light'>('dark')

  function setCurrentShop(shopId: string | null) {
    currentShop.value = shopId
  }

  function setTheme(newTheme: 'dark' | 'light') {
    theme.value = newTheme
  }

  return {
    currentShop,
    theme,
    setCurrentShop,
    setTheme
  }
})
