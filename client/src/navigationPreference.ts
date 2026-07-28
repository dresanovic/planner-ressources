export const NAVIGATION_PINNED_STORAGE_KEY = 'resource-planner.navigation.pinned.v1'

export function readNavigationPinned(): boolean {
  try {
    const stored = globalThis.localStorage?.getItem(NAVIGATION_PINNED_STORAGE_KEY)
    if (stored == null) return true
    if (stored === 'true') return true
    if (stored === 'false') return false
    return true
  } catch {
    return true
  }
}

export function writeNavigationPinned(pinned: boolean) {
  try {
    globalThis.localStorage?.setItem(NAVIGATION_PINNED_STORAGE_KEY, String(pinned))
  } catch {
    // The preference is optional; blocked storage must never block navigation.
  }
}
