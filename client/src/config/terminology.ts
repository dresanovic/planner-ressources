export const TERMINOLOGY_KEYS = [
  'course.singular', 'course.plural', 'course.navigation', 'course.heading', 'course.fieldLabel', 'course.tableHeading',
  'lecturer.singular', 'lecturer.plural', 'lecturer.navigation', 'lecturer.heading', 'lecturer.fieldLabel', 'lecturer.tableHeading',
  'cohort.singular', 'cohort.plural', 'cohort.navigation', 'cohort.heading', 'cohort.fieldLabel', 'cohort.tableHeading',
  'room.singular', 'room.plural', 'room.navigation', 'room.heading', 'room.fieldLabel', 'room.tableHeading',
  'schedule.navigation', 'schedule.heading', 'academicData.navigation', 'academicData.heading',
] as const

export type TerminologyKey = typeof TERMINOLOGY_KEYS[number]
export type TerminologyCatalog = Readonly<Record<TerminologyKey, string>>

const expectedKeys = new Set<string>(TERMINOLOGY_KEYS)
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
let activeCatalog: TerminologyCatalog | null = null

function invalidCatalog(): never {
  throw new Error('Ungültiger Terminologiekatalog.')
}

function validateResponse(value: unknown): TerminologyCatalog {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalidCatalog()
  const response = value as Record<string, unknown>
  if (Object.keys(response).length !== 1 || !('labels' in response)) invalidCatalog()
  const labels = response.labels
  if (!labels || typeof labels !== 'object' || Array.isArray(labels)) invalidCatalog()
  const record = labels as Record<string, unknown>
  const keys = Object.keys(record)
  if (keys.length !== TERMINOLOGY_KEYS.length || keys.some((key) => !expectedKeys.has(key))) invalidCatalog()
  const validated = {} as Record<TerminologyKey, string>
  for (const key of TERMINOLOGY_KEYS) {
    const labelValue = record[key]
    if (
      typeof labelValue !== 'string'
      || !labelValue.trim()
      || [...labelValue].some((character) => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127)
    ) invalidCatalog()
    validated[key] = labelValue
  }
  return Object.freeze(validated)
}

export function initializeTerminology(response: unknown): void {
  if (activeCatalog) throw new Error('Der Terminologiekatalog wurde bereits initialisiert.')
  activeCatalog = validateResponse(response)
}

export function label(key: TerminologyKey): string {
  if (!activeCatalog) throw new Error('Der Terminologiekatalog wurde nicht geladen.')
  return activeCatalog[key]
}

export async function fetchAndInitializeTerminology(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/public/ui-terminology`, {
    credentials: 'omit',
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error('Terminologiekatalog konnte nicht geladen werden.')
  initializeTerminology(await response.json())
}
