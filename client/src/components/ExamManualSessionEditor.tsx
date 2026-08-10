import { createElement, useEffect, useMemo, useState } from 'react'
import type { ExamConfiguration, ExamSession } from '../api/examScheduling'
import {
  createExamPlacementDraft,
  examPlacementDraftsEqual,
  type ExamPlacementDraft,
  type ExamPlacementInput,
} from './examPlacementModel'
import { EuropeanDateField } from './EuropeanDateField'
import { label } from '../config/terminology'
import { ActionableProblemList } from './ActionableProblemList'
import type { UserProblem } from '../utils/userProblems'

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
  const problems: UserProblem[] = [
    ...(error ? [{
      key: 'exam-placement-fields',
      tone: 'blocking' as const,
      title: 'Prüfungstermin vervollständigen',
      details: [error],
    }] : []),
    ...(serverError ? [{
      key: 'exam-placement-save',
      tone: 'blocking' as const,
      title: 'Prüfungstermin konnte nicht gespeichert werden',
      details: [serverError],
    }] : []),
  ]

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
      setError('Füllen Sie alle Felder für den Prüfungstermin aus. Ihre Eingaben bleiben erhalten.')
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
    <form className="exam-manual-editor" aria-labelledby={headingId} onSubmit={(event) => { event.preventDefault(); void submit() }}>
      {createElement(headingLevel, { id: headingId }, mode === 'create' ? 'Prüfung manuell einplanen' : 'Prüfungstermin korrigieren')}
      <p className="constraint-note">Die Dauer beträgt fest {retainedDuration} Minuten. Der empfohlene Zeitraum ist eine nicht blockierende Orientierung.</p>
      <div className="exam-form-grid">
        <EuropeanDateField id="exam-placement-date" label="Datum" value={draft.day} disabled={busy} onChange={(value) => change({ ...draft, day: value ?? '' })} required />
        <label className="constraint-field"><span>Beginn</span><input type="time" value={draft.startTime} disabled={busy} onChange={(event) => change({ ...draft, startTime: event.target.value })} /></label>
        <label className="constraint-field"><span>{label('lecturer.fieldLabel')}</span><select value={draft.lecturerId} disabled={busy} onChange={(event) => change({ ...draft, lecturerId: Number(event.target.value) })}>{lecturers.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label>
        <label className="constraint-field"><span>{label('room.fieldLabel')}</span><select value={draft.roomId} disabled={busy} onChange={(event) => change({ ...draft, roomId: Number(event.target.value) })}>{rooms.map((option) => <option key={option.id} value={option.id}>{option.name}{option.capacity ? ` (${option.capacity})` : ''}</option>)}</select></label>
      </div>
      <ActionableProblemList problems={problems} className="exam-placement-problems" />
      <div className={actionsClassName}>
        <button type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Abbrechen</button>
        <button type="submit" disabled={busy}>{busy ? 'Speichern…' : 'Prüfungstermin speichern'}</button>
      </div>
    </form>
  )
}
