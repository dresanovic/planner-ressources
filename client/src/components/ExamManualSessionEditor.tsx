import { createElement, useEffect, useMemo, useState } from 'react'
import type { ExamConfiguration, ExamSession } from '../api/examScheduling'
import {
  createExamPlacementDraft,
  examPlacementDraftsEqual,
  type ExamPlacementDraft,
  type ExamPlacementInput,
} from './examPlacementModel'

type Option = { id: number; name: string; capacity?: number }

type Props = {
  mode: 'create' | 'edit'
  configuration?: ExamConfiguration
  exam?: ExamSession
  snapshotToken: string
  semesterId: number
  lecturers: Option[]
  rooms: Option[]
  busy: boolean
  serverError?: string
  onCancel: () => void
  onSubmit: (request: ExamPlacementInput) => Promise<void>
  draft?: ExamPlacementDraft
  baseline?: ExamPlacementDraft
  onDraftChange?: (draft: ExamPlacementDraft) => void
  onDirtyChange?: (dirty: boolean) => void
  headingLevel?: 'h2' | 'h3'
  headingId?: string
  actionsClassName?: string
}

export function ExamManualSessionEditor({
  mode,
  configuration,
  exam,
  snapshotToken,
  semesterId,
  lecturers,
  rooms,
  busy,
  serverError,
  onCancel,
  onSubmit,
  draft: controlledDraft,
  baseline: controlledBaseline,
  onDraftChange,
  onDirtyChange,
  headingLevel = 'h3',
  headingId = 'exam-manual-title',
  actionsClassName = 'dialog-actions',
}: Props) {
  const initialDraft = useMemo(
    () => createExamPlacementDraft({ exam, configuration, lecturers, rooms }),
    [configuration, exam, lecturers, rooms],
  )
  const [internalDraft, setInternalDraft] = useState(initialDraft)
  const [internalBaseline] = useState(initialDraft)
  const [error, setError] = useState('')
  const draft = controlledDraft ?? internalDraft
  const baseline = controlledBaseline ?? internalBaseline
  const retainedDuration = mode === 'edit' && exam ? exam.durationMinutes : configuration?.durationMinutes

  useEffect(() => {
    onDirtyChange?.(!examPlacementDraftsEqual(draft, baseline))
  }, [baseline, draft, onDirtyChange])

  function change(next: ExamPlacementDraft) {
    setError('')
    if (controlledDraft == null) setInternalDraft(next)
    onDraftChange?.(next)
  }

  async function submit() {
    if (!draft.day || !draft.startTime || !draft.lecturerId || !draft.roomId || (mode === 'create' && !configuration)) {
      setError('Complete every placement field.')
      return
    }
    setError('')
    if (mode === 'create') {
      await onSubmit({
        semesterId,
        date: draft.day,
        startTime: draft.startTime,
        lecturerId: draft.lecturerId,
        roomId: draft.roomId,
        expectedConfigurationRevision: configuration!.revision,
        inputSnapshotToken: snapshotToken,
      })
    } else {
      await onSubmit({
        date: draft.day,
        startTime: draft.startTime,
        lecturerId: draft.lecturerId,
        roomId: draft.roomId,
        expectedExamRevision: exam!.revision,
        inputSnapshotToken: snapshotToken,
      })
    }
  }

  return (
    <section className="exam-manual-editor" aria-labelledby={headingId}>
      {createElement(headingLevel, { id: headingId }, mode === 'create' ? 'Place exam manually' : `Correct ${exam?.lifecycleStatus} exam`)}
      <p className="constraint-note">Duration is fixed at {retainedDuration} minutes. Any start time is allowed when all hard constraints pass; the recommended range remains optional.</p>
      <div className="exam-form-grid">
        <label className="constraint-field"><span>Date</span><input type="date" value={draft.day} disabled={busy} onChange={(event) => change({ ...draft, day: event.target.value })} /></label>
        <label className="constraint-field"><span>Start time</span><input type="time" value={draft.startTime} disabled={busy} onChange={(event) => change({ ...draft, startTime: event.target.value })} /></label>
        <label className="constraint-field"><span>Lecturer</span><select value={draft.lecturerId} disabled={busy} onChange={(event) => change({ ...draft, lecturerId: Number(event.target.value) })}>{lecturers.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label>
        <label className="constraint-field"><span>Room</span><select value={draft.roomId} disabled={busy} onChange={(event) => change({ ...draft, roomId: Number(event.target.value) })}>{rooms.map((option) => <option key={option.id} value={option.id}>{option.name}{option.capacity ? ` (${option.capacity})` : ''}</option>)}</select></label>
      </div>
      {(error || serverError) && <div role="alert" className="alert-item">{[error, serverError].filter(Boolean).join(' ')}</div>}
      <div className={actionsClassName}>
        <button type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Cancel</button>
        <button type="button" disabled={busy} onClick={() => void submit()}>{busy ? 'Saving…' : 'Save exam placement'}</button>
      </div>
    </section>
  )
}
