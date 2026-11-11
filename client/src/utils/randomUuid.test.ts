import { afterEach, expect, it, vi } from 'vitest'
import { randomUuid } from './randomUuid'

afterEach(() => vi.unstubAllGlobals())

it('uses the native UUID generator when available', () => {
  const native = vi.fn(() => '12345678-1234-4123-8123-123456789abc')
  vi.stubGlobal('crypto', { randomUUID: native })
  expect(randomUuid()).toBe('12345678-1234-4123-8123-123456789abc')
  expect(native).toHaveBeenCalledOnce()
})

it('creates a UUID v4 from cryptographic bytes when HTTP hides randomUUID', () => {
  const getRandomValues = vi.fn((bytes: Uint8Array) => bytes.fill(255))
  vi.stubGlobal('crypto', { getRandomValues })
  expect(randomUuid()).toBe('ffffffff-ffff-4fff-bfff-ffffffffffff')
  expect(getRandomValues).toHaveBeenCalledOnce()
})

it('fails when cryptographic randomness is unavailable', () => {
  vi.stubGlobal('crypto', undefined)
  expect(() => randomUuid()).toThrow('Sichere Zufallswerte')
})
