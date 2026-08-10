import { afterEach } from 'vitest'
import { initializeTerminology } from '../config/terminology'
import { terminologyDefaults } from './terminologyDefaults'

try {
  initializeTerminology({ labels: terminologyDefaults })
} catch {
  // Vitest may keep the setup module while reusing an already initialized module.
}

;(globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
  .IS_REACT_ACT_ENVIRONMENT = true

function memoryStorage(): Storage {
  const values = new Map<string, string>()
  return {
    get length() {
      return values.size
    },
    clear() {
      values.clear()
    },
    getItem(key: string) {
      return values.get(key) ?? null
    },
    key(index: number) {
      return [...values.keys()][index] ?? null
    },
    removeItem(key: string) {
      values.delete(key)
    },
    setItem(key: string, value: string) {
      values.set(key, String(value))
    },
  }
}

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: memoryStorage(),
})
Object.defineProperty(globalThis, 'sessionStorage', {
  configurable: true,
  value: memoryStorage(),
})

afterEach(() => {
  document.body.innerHTML = ''
})
