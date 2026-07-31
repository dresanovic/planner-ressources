import { useEffect, useRef } from 'react'

type Props = {
  destinationLabel: string
  title?: string
  description?: string
  keepLabel?: string
  discardLabel?: string
  restoreFocusTo?: HTMLElement | null
  onKeepEditing: () => void
  onDiscard: () => void
}

export function DiscardChangesDialog({
  destinationLabel,
  title = 'Discard unsaved changes?',
  description,
  keepLabel = 'Keep editing',
  discardLabel = 'Discard changes',
  restoreFocusTo,
  onKeepEditing,
  onDiscard,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const keepRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    keepRef.current?.focus()
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        keep()
        return
      }
      if (event.key === 'Tab') trapFocus(event, dialogRef.current)
    }
    document.addEventListener('keydown', keydown)
    return () => document.removeEventListener('keydown', keydown)
  })

  function restoreFocus() {
    restoreFocusTo?.focus()
  }

  function keep() {
    onKeepEditing()
    window.setTimeout(restoreFocus, 0)
  }

  function discard() {
    onDiscard()
  }

  return (
    <div className="dialog-backdrop">
      <div ref={dialogRef} className="replacement-dialog discard-changes-dialog" role="dialog" aria-modal="true" aria-labelledby="discard-changes-title" aria-describedby="discard-changes-description">
        <h2 id="discard-changes-title">{title}</h2>
        <p id="discard-changes-description">{description ?? `Your session changes have not been saved. Discard them to continue to ${destinationLabel}.`}</p>
        <div className="dialog-actions">
          <button ref={keepRef} type="button" className="secondary-button" onClick={keep}>{keepLabel}</button>
          <button type="button" className="destructive-button" onClick={discard}>{discardLabel}</button>
        </div>
      </div>
    </div>
  )
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null) {
  if (!container) return
  const focusable = [...container.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}
