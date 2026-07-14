import type { BatchPreparation } from '../api/multiCourseDraftGeneration'

type Props = {
  preparation: BatchPreparation
  disabled?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ReplacementConfirmationDialog({ preparation, disabled = false, onConfirm, onCancel }: Props) {
  const replacements = preparation.courses.filter((course) => course.replacementRequired)
  return (
    <div className="dialog-backdrop" role="presentation">
      <section className="replacement-dialog" role="dialog" aria-modal="true" aria-labelledby="replacement-title">
        <h2 id="replacement-title">Replace existing Draft Schedules?</h2>
        <p className="replacement-warning">
          Regeneration replaces these schedules and all manual session edits. This cannot be undone from this screen.
        </p>
        <ul>
          {replacements.map((course) => <li key={course.courseId}>{course.courseName ?? `Course ${course.courseId}`}</li>)}
        </ul>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onCancel} disabled={disabled}>Cancel</button>
          <button type="button" onClick={onConfirm} disabled={disabled}>
            {disabled ? 'Replacing...' : 'Confirm replacement'}
          </button>
        </div>
      </section>
    </div>
  )
}
