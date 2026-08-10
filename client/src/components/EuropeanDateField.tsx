import { useEffect, useId, useRef, useState } from 'react'

import {
  formatCalendarDate,
  isIsoCalendarDate,
  parseEuropeanDate,
} from '../utils/datePresentation'

type Props = {
  id?: string
  name?: string
  label: string
  value: string | null | undefined
  onChange: (isoValue: string | null) => void
  required?: boolean
  min?: string
  max?: string
  disabled?: boolean
  autoFocus?: boolean
  className?: string
  error?: string
  describedBy?: string
  invalid?: boolean
}

function initialText(value: string | null | undefined): string {
  return value && isIsoCalendarDate(value) ? formatCalendarDate(value) : ''
}

function validationError(
  raw: string,
  required: boolean,
  min?: string,
  max?: string,
): string | null {
  if (raw === '') return required ? 'Geben Sie ein Datum im Format TT.MM.JJJJ ein.' : null
  const iso = parseEuropeanDate(raw)
  if (!iso) return 'Geben Sie ein gültiges Datum im Format TT.MM.JJJJ ein.'
  if (min && iso < min) return `Das Datum darf nicht vor dem ${formatCalendarDate(min)} liegen.`
  if (max && iso > max) return `Das Datum darf nicht nach dem ${formatCalendarDate(max)} liegen.`
  return null
}

export function EuropeanDateField({
  id,
  name,
  label,
  value,
  onChange,
  required = false,
  min,
  max,
  disabled = false,
  autoFocus = false,
  className = 'constraint-field',
  error,
  describedBy,
  invalid = false,
}: Props) {
  const generatedId = useId()
  const inputId = id ?? `date-${generatedId.replace(/:/g, '')}`
  const hintId = `${inputId}-hint`
  const errorId = `${inputId}-error`
  const [raw, setRaw] = useState(() => initialText(value))
  const [touched, setTouched] = useState(false)
  const lastExternalValue = useRef(value)
  const lastEmittedValue = useRef<string | null | undefined>(undefined)
  const inputRef = useRef<HTMLInputElement>(null)
  const localError = validationError(raw, required, min, max)
  const activeError = error ?? (touched ? localError : null)

  useEffect(() => {
    if (Object.is(value, lastExternalValue.current)) return
    lastExternalValue.current = value
    const normalizedValue = value && isIsoCalendarDate(value) ? value : null
    if (normalizedValue === lastEmittedValue.current) {
      lastEmittedValue.current = undefined
      return
    }
    lastEmittedValue.current = undefined
    setRaw(initialText(value))
    setTouched(false)
  }, [value])

  useEffect(() => {
    inputRef.current?.setCustomValidity(error ?? localError ?? '')
  }, [error, localError])

  return (
    <label className={className} htmlFor={inputId}>
      <span>{label}</span>
      <input
        ref={inputRef}
        id={inputId}
        name={name}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        placeholder="TT.MM.JJJJ"
        value={raw}
        required={required}
        disabled={disabled}
        autoFocus={autoFocus}
        aria-invalid={activeError || invalid ? 'true' : undefined}
        aria-describedby={`${hintId}${activeError ? ` ${errorId}` : ''}${describedBy ? ` ${describedBy}` : ''}`}
        onChange={(event) => {
          const nextRaw = event.target.value
          const nextError = validationError(nextRaw, required, min, max)
          setRaw(nextRaw)
          event.currentTarget.setCustomValidity(error ?? nextError ?? '')
          const nextValue = nextError ? null : parseEuropeanDate(nextRaw)
          lastEmittedValue.current = nextValue
          onChange(nextValue)
        }}
        onBlur={() => setTouched(true)}
        onInvalid={() => {
          setTouched(true)
          inputRef.current?.focus()
        }}
      />
      <small id={hintId} className="field-hint">Format: TT.MM.JJJJ</small>
      {activeError && <small id={errorId} className="field-error">{activeError}</small>}
    </label>
  )
}
