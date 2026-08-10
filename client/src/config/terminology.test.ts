import { describe, expect, it, vi } from 'vitest'

const expectedKeys = [
  'course.singular', 'course.plural', 'course.navigation', 'course.heading', 'course.fieldLabel', 'course.tableHeading',
  'lecturer.singular', 'lecturer.plural', 'lecturer.navigation', 'lecturer.heading', 'lecturer.fieldLabel', 'lecturer.tableHeading',
  'cohort.singular', 'cohort.plural', 'cohort.navigation', 'cohort.heading', 'cohort.fieldLabel', 'cohort.tableHeading',
  'room.singular', 'room.plural', 'room.navigation', 'room.heading', 'room.fieldLabel', 'room.tableHeading',
  'schedule.navigation', 'schedule.heading', 'academicData.navigation', 'academicData.heading',
] as const

function catalog(value = 'Wert') {
  return Object.fromEntries(expectedKeys.map((key) => [key, `${value} ${key}`]))
}

describe('terminology catalog', () => {
  it('accepts exactly the published keys and provides typed set-once access', async () => {
    vi.resetModules()
    const module = await import('./terminology')
    expect(module.TERMINOLOGY_KEYS).toEqual(expectedKeys)
    const labels = catalog()
    module.initializeTerminology({ labels })
    expect(module.label('course.singular')).toBe('Wert course.singular')
    expect(() => module.initializeTerminology({ labels })).toThrow(/bereits initialisiert/)
  })

  it.each([
    { labels: { ...catalog(), unknown: 'x' } },
    { labels: Object.fromEntries(Object.entries(catalog()).slice(1)) },
    { labels: { ...catalog(), 'course.singular': '' } },
    { labels: { ...catalog(), 'course.singular': 12 } },
    { labels: { ...catalog(), 'course.singular': 'A\nB' } },
    { labels: null },
    catalog(),
  ])('rejects an incomplete or malformed response without partial initialization', async (payload) => {
    vi.resetModules()
    const module = await import('./terminology')
    expect(() => module.initializeTerminology(payload)).toThrow()
    expect(() => module.label('course.singular')).toThrow(/nicht geladen/)
  })

  it('fetches once with omitted credentials and validates before returning', async () => {
    vi.resetModules()
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ labels: catalog('Kunde') }), { status: 200 }),
    )
    const { fetchAndInitializeTerminology, label } = await import('./terminology')
    await fetchAndInitializeTerminology()
    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledWith('/api/public/ui-terminology', {
      credentials: 'omit',
      headers: { Accept: 'application/json' },
    })
    expect(label('room.plural')).toBe('Kunde room.plural')
  })
})
