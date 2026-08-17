import { useEffect, useRef } from 'react'

type Props = {
  eventCount: number
  busy: boolean
  error: string | null
  restoreFocusTo: HTMLElement | null
  onCancel: () => void
  onConfirm: () => void
}

export function LecturerCalendarDownloadDialog({
  eventCount,
  busy,
  error,
  restoreFocusTo,
  onCancel,
  onConfirm,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    cancelRef.current?.focus()
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !busy) {
        event.preventDefault()
        onCancel()
        return
      }
      if (event.key === 'Tab') trapFocus(event, dialogRef.current)
    }
    document.addEventListener('keydown', keydown)
    return () => document.removeEventListener('keydown', keydown)
  }, [busy, onCancel])

  useEffect(() => () => restoreFocusTo?.focus(), [restoreFocusTo])

  return (
    <div className="dialog-backdrop">
      <div
        ref={dialogRef}
        className="replacement-dialog lecturer-calendar-download-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lecturer-calendar-download-title"
        aria-describedby="lecturer-calendar-download-description lecturer-calendar-download-privacy"
      >
        <h2 id="lecturer-calendar-download-title">Kalender herunterladen</h2>
        <div id="lecturer-calendar-download-description">
          <p>
            Die aktuell geöffnete Planung zeigt den vollständigen, ungefilterten
            Terminstand mit{' '}
            <strong>{eventCount} Termine</strong>.
          </p>
          <p>
            Beim Fortsetzen werden Berechtigung und vollständiger Terminstand erneut
            geprüft. Die Zahl im Download kann deshalb von dieser Anzeige abweichen.
          </p>
        </div>
        <div id="lecturer-calendar-download-privacy" className="calendar-download-notice">
          <p>
            Die Datei ist eine statische Momentaufnahme. Änderungen im Produkt oder das
            Ende dieses Links aktualisieren oder löschen bereits heruntergeladene Dateien
            nicht.
          </p>
          <p>
            Die Datei enthält Ihren persönlichen Terminplan. Kopieren oder teilen Sie sie
            nur geschützt, weil dadurch Ihr Terminplan offengelegt werden kann. Speichern
            und löschen Sie die Datei geschützt auf Ihrem Gerät. Ein wiederholter manueller
            Import kann im Kalenderprogramm doppelte Termine erzeugen; das Produkt gleicht
            importierte Termine nicht ab und entfernt sie nicht.
          </p>
        </div>
        {error && <p className="refresh-error" role="alert">{error}</p>}
        <div className="dialog-actions">
          <button
            ref={cancelRef}
            type="button"
            className="secondary-button"
            disabled={busy}
            onClick={onCancel}
          >
            Abbrechen
          </button>
          <button type="button" disabled={busy} onClick={onConfirm}>
            {busy ? 'Kalender wird erstellt …' : 'Download fortsetzen'}
          </button>
        </div>
      </div>
    </div>
  )
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null) {
  if (!container) return
  const focusable = [...container.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )]
  if (focusable.length === 0) {
    event.preventDefault()
    return
  }
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
