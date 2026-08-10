import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EuropeanDateField } from './EuropeanDateField'

afterEach(() => { document.body.innerHTML = '' })

function change(input: HTMLInputElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

describe('EuropeanDateField', () => {
  it('shows an ISO value as European text and emits the same ISO day', () => {
    const onChange = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<EuropeanDateField id="exam-date" label="Prüfungstermin" value="2026-09-11" onChange={onChange} />))
    const input = document.querySelector('input')!
    expect(input.value).toBe('11.09.2026')
    expect(input.type).toBe('text')
    expect(input.inputMode).toBe('numeric')
    act(() => change(input, '29.02.2028'))
    expect(onChange).toHaveBeenLastCalledWith('2028-02-29')
  })

  it('does not retain a stale ISO value while visible text is invalid', () => {
    const onChange = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<EuropeanDateField id="date" label="Datum" value="2026-09-11" onChange={onChange} required />))
    const input = document.querySelector('input')!
    act(() => change(input, '31.04.2026'))
    expect(onChange).toHaveBeenLastCalledWith(null)
    act(() => input.dispatchEvent(new FocusEvent('focusout', { bubbles: true })))
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(input.getAttribute('aria-describedby')).toContain('date-error')
    expect(document.body.textContent).toContain('TT.MM.JJJJ')
  })

  it('preserves partial corrections when a controlled parent clears its machine value', () => {
    function ControlledDate() {
      const [value, setValue] = useState('2026-09-11')
      return <>
        <EuropeanDateField id="controlled-date" label="Datum" value={value} required onChange={(next) => setValue(next ?? '')} />
        <output data-machine-value>{value}</output>
      </>
    }
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ControlledDate />))
    const input = document.querySelector<HTMLInputElement>('#controlled-date')!

    act(() => change(input, '1.09.2026'))
    expect(input.value).toBe('1.09.2026')
    expect(document.querySelector('[data-machine-value]')?.textContent).toBe('')

    act(() => change(input, '12.09.2026'))
    expect(input.value).toBe('12.09.2026')
    expect(document.querySelector('[data-machine-value]')?.textContent).toBe('2026-09-12')
  })

  it('supports optional empty values, required correction, min/max, and external reset', () => {
    const onChange = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<EuropeanDateField id="date" label="Datum" value={null} onChange={onChange} min="2026-09-01" max="2026-09-30" />))
    const input = document.querySelector('input')!
    act(() => change(input, '01.09.2026'))
    act(() => change(input, ''))
    expect(onChange).toHaveBeenLastCalledWith(null)
    act(() => change(input, '31.08.2026'))
    expect(input.validationMessage).toContain('01.09.2026')
    act(() => root.render(<EuropeanDateField id="date" label="Datum" value="2026-09-30" onChange={onChange} />))
    expect(input.value).toBe('30.09.2026')
  })
})
