import { useEffect, useMemo, useRef, useState } from 'react'

import {
  buildLecturerReviewUrl,
  type IssueLecturerReviewInput,
  type IssuedLecturerReviewLink,
  type LecturerReviewOverview,
  type ReplaceLecturerReviewInput,
} from '../api/lecturerReview'
import { formatCalendarDate, formatViennaDateTime } from '../utils/datePresentation'
import { label } from '../config/terminology'


type LecturerReviewManagementProps = {
  overview: LecturerReviewOverview
  busy: boolean
  onIssue: (
    input: Required<IssueLecturerReviewInput>,
  ) => Promise<IssuedLecturerReviewLink>
  onRevoke?: (linkId: number) => Promise<LecturerReviewOverview>
  onReplace?: (
    linkId: number,
    input: Required<ReplaceLecturerReviewInput>,
  ) => Promise<IssuedLecturerReviewLink>
  onOpenCurrentSession?: (navigation: {
    revisionId: number
    occurrenceRef: string
  }) => void
}

type CoordinationFilters = {
  lecturerId?: number
  courseSourceId?: number
  sessionKind?: 'revision' | 'teaching' | 'exam'
  feedbackKind?: 'revision_comment' | 'session_comment' | 'impossible_session'
}

export function LecturerReviewManagement({
  overview,
  busy,
  onIssue,
  onRevoke = () => Promise.reject(new Error('Revoke is unavailable.')),
  onReplace = () => Promise.reject(new Error('Replacement is unavailable.')),
  onOpenCurrentSession,
}: LecturerReviewManagementProps) {
  const [resultOverview, setResultOverview] =
    useState<LecturerReviewOverview | null>(null)
  const [lecturerId, setLecturerId] = useState('')
  const [durationDays, setDurationDays] = useState<1 | 2 | 3>(3)
  const [replacementDurationDays, setReplacementDurationDays] =
    useState<1 | 2 | 3>(3)
  const [issued, setIssued] = useState<IssuedLecturerReviewLink | null>(null)
  const [transientUrl, setTransientUrl] = useState<string | null>(null)
  const [uncertainLinkIds, setUncertainLinkIds] = useState<Set<number>>(
    () => new Set(),
  )
  const [feedbackFilters, setFeedbackFilters] =
    useState<CoordinationFilters>({})
  const [notPossibleOnly, setNotPossibleOnly] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const previousRevision = useRef(overview.revision.id)
  const feedbackHeadingRef = useRef<HTMLHeadingElement>(null)
  const currentOverview =
    resultOverview?.revision.id === overview.revision.id
      ? resultOverview
      : overview

  useEffect(() => {
    if (previousRevision.current !== overview.revision.id) {
      previousRevision.current = overview.revision.id
      setResultOverview(null)
      setIssued(null)
      setTransientUrl(null)
      setLecturerId('')
      setStatus('')
      setError('')
      setUncertainLinkIds(new Set())
      setFeedbackFilters({})
      setNotPossibleOnly(false)
    }
  }, [overview])

  const selectedLecturer = useMemo(
    () =>
      currentOverview.lecturers.find(
        (lecturer) => lecturer.lecturerId === Number(lecturerId),
      ) ?? null,
    [lecturerId, currentOverview.lecturers],
  )
  const working = ['draft', 'ready_for_review'].includes(
    currentOverview.revision.state,
  )
  const canIssue =
    !busy &&
    working &&
    selectedLecturer !== null &&
    selectedLecturer.initialIssueAllowed
  const feedbackComplete =
    currentOverview.feedbackAvailability === 'complete'
  const feedbackRows = currentOverview.feedbackGroups.flatMap((group) =>
    group.items.map((item) => ({ group, item })),
  )
  const isOpenImpossible = (item: (typeof feedbackRows)[number]['item']) =>
    item.kind === 'impossible_session' && item.sessionStatus === 'current'
  const itemFilteredRows = feedbackRows.filter(({ group, item }) => (
    (feedbackFilters.lecturerId === undefined ||
      item.intendedLecturerId === feedbackFilters.lecturerId) &&
    (feedbackFilters.courseSourceId === undefined ||
      item.sessionContext?.courseSourceId === feedbackFilters.courseSourceId) &&
    (feedbackFilters.sessionKind === undefined ||
      (feedbackFilters.sessionKind === 'revision'
        ? group.level === 'revision'
        : item.sessionContext?.sessionKind === feedbackFilters.sessionKind)) &&
    (feedbackFilters.feedbackKind === undefined ||
      item.kind === feedbackFilters.feedbackKind)
  ))
  const flaggedGroupRefs = new Set(
    itemFilteredRows
      .filter(({ item }) => isOpenImpossible(item))
      .map(({ group }) => group.groupRef),
  )
  const filteredRows = notPossibleOnly
    ? itemFilteredRows.filter(({ group }) => flaggedGroupRefs.has(group.groupRef))
    : itemFilteredRows
  const visibleFeedbackGroups = currentOverview.feedbackGroups
    .map((group) => {
      const items = filteredRows
        .filter((row) => row.group.groupRef === group.groupRef)
        .map((row) => row.item)
      return {
        ...group,
        items,
        impossibleFlagCount: items.filter(
          (item) => isOpenImpossible(item),
        ).length,
      }
    })
    .filter((group) => group.items.length > 0)
  const activeFeedbackFilterCount = Object.values(feedbackFilters).filter(
    (value) => value !== undefined,
  ).length + (notPossibleOnly ? 1 : 0)
  const prominentImpossibleCount = itemFilteredRows.filter(
    ({ item }) => isOpenImpossible(item),
  ).length
  const filteredCommentCount = filteredRows.filter(
    ({ item }) =>
      item.kind === 'revision_comment' || item.kind === 'session_comment',
  ).length
  const filteredImpossibleCount = filteredRows.filter(
    ({ item }) => isOpenImpossible(item),
  ).length
  const filteredAffectedSessions = new Set(
    filteredRows
      .map(({ item }) => item.sessionContext?.sessionRef)
      .filter((value): value is string => value !== undefined),
  ).size
  const feedbackLecturers = [
    ...new Map(
      feedbackRows.map(({ item }) => [
        item.intendedLecturerId,
        item.intendedLecturerName,
      ]),
    ),
  ]
  const feedbackCourses = [
    ...new Map(
      feedbackRows
        .filter(({ item }) => item.sessionContext !== null)
        .map(({ item }) => [
          item.sessionContext!.courseSourceId,
          `${item.sessionContext!.courseCode} · ${item.sessionContext!.courseTitle}`,
        ]),
    ),
  ]

  async function issue() {
    if (!canIssue || selectedLecturer === null) return
    setError('')
    setStatus('Zugangslink wird erstellt…')
    try {
      const result = await onIssue({
        lecturerId: selectedLecturer.lecturerId,
        durationDays,
      })
      setIssued(result)
      setResultOverview(result.overview)
      setTransientUrl(buildLecturerReviewUrl(result.secret))
      setStatus(
        'Der Zugangslink wurde erstellt. Kopieren Sie ihn jetzt; der geheime Anteil wird nur in diesem Ergebnis angezeigt.',
      )
    } catch {
      setIssued(null)
      setTransientUrl(null)
      setStatus('')
      setError('Der Zugangslink konnte nicht erstellt werden. Prüfen Sie den aktuellen Revisionsstand und versuchen Sie es erneut.')
    }
  }

  async function revoke(linkId: number) {
    setError('')
    setStatus('Zugangslink wird widerrufen…')
    try {
      const result = await onRevoke(linkId)
      setResultOverview(result)
      setIssued(null)
      setTransientUrl(null)
      setUncertainLinkIds((current) => {
        const next = new Set(current)
        next.delete(linkId)
        return next
      })
      setStatus('Der Zugangslink wurde widerrufen.')
    } catch {
      setStatus('')
      setError(
        'Der Zugangslink konnte nicht widerrufen werden. Laden Sie den aktuellen Stand und prüfen Sie seinen Status.',
      )
    }
  }

  async function replace(linkId: number) {
    setError('')
    setStatus('Zugangslink wird ersetzt…')
    setIssued(null)
    setTransientUrl(null)
    try {
      const result = await onReplace(linkId, {
        durationDays: replacementDurationDays,
      })
      setResultOverview(result.overview)
      setIssued(result)
      setTransientUrl(buildLecturerReviewUrl(result.secret))
      setUncertainLinkIds((current) => {
        const next = new Set(current)
        next.delete(linkId)
        return next
      })
      setStatus(
        'Der Ersatzlink wurde erstellt. Der frühere Zugang ist nicht mehr verfügbar; kopieren Sie jetzt den neuen Link.',
      )
    } catch {
      setUncertainLinkIds((current) => new Set(current).add(linkId))
      setStatus('')
      setError(
        'Das Ergebnis der Ersetzung ist unbekannt, weil die Antwort verloren ging. Laden Sie den aktuellen Status; erstellen Sie nur bei Bedarf danach einen neuen Ersatzlink.',
      )
    }
  }

  async function copy() {
    if (transientUrl === null) return
    try {
      await navigator.clipboard.writeText(transientUrl)
      setError('')
      setStatus('Der Link wurde kopiert.')
    } catch {
      setStatus('')
      setError(
        'Der Link konnte nicht kopiert werden. Markieren und kopieren Sie die einmalig angezeigte URL manuell.',
      )
    }
  }

  function dismiss() {
    setIssued(null)
    setTransientUrl(null)
    setStatus('Die einmalig angezeigten Linkdetails wurden geschlossen.')
    setError('')
  }

  const detailLecturer =
    issued?.overview.lecturers.find(
      (lecturer) => lecturer.lecturerId === issued.issuedLink.lecturerId,
    ) ?? selectedLecturer

  return (
    <section className="lecturer-review-management">
      <header>
        <p className="eyebrow">Kontolose Rückmeldung der {label('lecturer.plural')}</p>
        <h2>{currentOverview.revision.label}</h2>
        <p>
          {humanize(currentOverview.revision.state)}
          {currentOverview.revision.state === 'ready_for_review' &&
            ' · Empfohlener Zeitpunkt für die Rückmeldungsanfrage'}
        </p>
      </header>

      <section
        className="review-feedback-area"
        aria-labelledby="review-feedback-heading"
      >
        {feedbackComplete && prominentImpossibleCount === 0 ? (
          <p className="review-feedback-clear-status">
            Keine offenen Rückmeldungen „Nicht möglich“.
          </p>
        ) : (
          <button
            type="button"
            className="review-feedback-filter"
            aria-pressed={notPossibleOnly}
            disabled={!feedbackComplete}
            onClick={() => {
              const next = !notPossibleOnly
              setNotPossibleOnly(next)
              if (next) {
                queueMicrotask(() => feedbackHeadingRef.current?.focus())
              }
            }}
          >
            <span aria-hidden="true">!</span>{' '}
            {feedbackComplete
              ? `Nicht möglich ${prominentImpossibleCount}`
              : currentOverview.feedbackAvailability === 'partial'
                ? 'Anzahl „Nicht möglich“ unvollständig'
                : 'Anzahl „Nicht möglich“ nicht verfügbar'}
          </button>
        )}
        <div className="coordination-counters" aria-label="Rückmeldungszähler">
          {feedbackComplete ? (
            <>
              <span><strong>{filteredRows.length}</strong> Einträge</span>
              <span><strong>{filteredCommentCount}</strong> Kommentare</span>
              <span><strong>{filteredImpossibleCount}</strong> offen nicht möglich</span>
              <span><strong>{filteredAffectedSessions}</strong> betroffene Termine</span>
            </>
          ) : (
            <span>
              Genaue Zähler sind {currentOverview.feedbackAvailability === 'partial'
                ? 'unvollständig'
                : 'nicht verfügbar'}.
            </span>
          )}
        </div>
        <div className="coordination-filters" aria-label={`Filter für Rückmeldungen der ${label('lecturer.plural')}`}>
          <label>
            <span>Rückmeldung von {label('lecturer.singular')}</span>
            <select
              value={feedbackFilters.lecturerId ?? ''}
              onChange={(event) =>
                setFeedbackFilters((current) => ({
                  ...current,
                  lecturerId: event.target.value
                    ? Number(event.target.value)
                    : undefined,
                }))
              }
            >
              <option value="">Alle</option>
              {feedbackLecturers.map(([id, name]) => (
                <option value={id} key={id}>{name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>{label('course.singular')}</span>
            <select
              value={feedbackFilters.courseSourceId ?? ''}
              onChange={(event) =>
                setFeedbackFilters((current) => ({
                  ...current,
                  courseSourceId: event.target.value
                    ? Number(event.target.value)
                    : undefined,
                }))
              }
            >
              <option value="">Alle</option>
              {feedbackCourses.map(([id, name]) => (
                <option value={id} key={id}>{name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Terminart</span>
            <select
              value={feedbackFilters.sessionKind ?? ''}
              onChange={(event) =>
                setFeedbackFilters((current) => ({
                  ...current,
                  sessionKind: (event.target.value || undefined) as
                    CoordinationFilters['sessionKind'],
                }))
              }
            >
              <option value="">Alle</option>
              <option value="revision">Revision</option>
              <option value="teaching">Lehrtermin</option>
              <option value="exam">Prüfung</option>
            </select>
          </label>
          <label>
            <span>Art der Rückmeldung</span>
            <select
              value={feedbackFilters.feedbackKind ?? ''}
              onChange={(event) =>
                setFeedbackFilters((current) => ({
                  ...current,
                  feedbackKind: (event.target.value || undefined) as
                    CoordinationFilters['feedbackKind'],
                }))
              }
            >
              <option value="">Alle</option>
              <option value="revision_comment">Revisionskommentar</option>
              <option value="session_comment">Terminkommentar</option>
              <option value="impossible_session">Nicht möglich</option>
            </select>
          </label>
          <button
            type="button"
            disabled={activeFeedbackFilterCount === 0}
            onClick={() => {
              setFeedbackFilters({})
              setNotPossibleOnly(false)
              queueMicrotask(() => feedbackHeadingRef.current?.focus())
            }}
          >
            Rückmeldungsfilter zurücksetzen
          </button>
        </div>
        {!feedbackComplete && (
          <p role="status">
            {currentOverview.feedbackAvailability === 'partial'
              ? 'Die Rückmeldungen sind unvollständig; die Anzahl „Nicht möglich“ ist nicht vollständig.'
              : 'Die Rückmeldungen sind nicht verfügbar; es kann keine vollständige Anzahl angezeigt werden.'}
          </p>
        )}
        <h3
          id="review-feedback-heading"
          ref={feedbackHeadingRef}
          tabIndex={-1}
        >
          {notPossibleOnly ? 'Rückmeldungen „Nicht möglich“' : `Rückmeldungen der ${label('lecturer.plural')}`}
        </h3>
        <p className="review-feedback-announcement" aria-live="polite">
          {feedbackComplete
            ? `${filteredRows.length} ${filteredRows.length === 1 ? 'Rückmeldung' : 'Rückmeldungen'} in ${visibleFeedbackGroups.length} ${visibleFeedbackGroups.length === 1 ? 'Gruppe' : 'Gruppen'} werden angezeigt.`
            : currentOverview.feedbackAvailability === 'partial'
              ? 'Die angezeigten Rückmeldungen sind unvollständig; genaue Eintrags- und Gruppenzahlen sind nicht verfügbar.'
              : 'Die Rückmeldungsergebnisse sind nicht verfügbar; Eintrags- und Gruppenzahlen können nicht bestätigt werden.'}
        </p>
        {visibleFeedbackGroups.length === 0 ? (
          <p>
            {!feedbackComplete
              ? currentOverview.feedbackAvailability === 'partial'
                ? 'Die Rückmeldungsergebnisse sind unvollständig; ein leeres Ergebnis kann nicht bestätigt werden.'
                : 'Die Rückmeldungsergebnisse sind nicht verfügbar; ein leeres Ergebnis kann nicht bestätigt werden.'
              : notPossibleOnly
                ? 'Für keinen Termin liegt eine Rückmeldung „Nicht möglich“ vor.'
                : 'Für diese Revision wurde noch keine Rückmeldung abgegeben.'}
          </p>
        ) : (
          <div className="review-feedback-groups">
            {visibleFeedbackGroups.map((group) => (
              <article className="review-feedback-group" key={group.groupRef}>
                <h4>
                  {group.level === 'revision'
                    ? 'Revisionsrückmeldung'
                    : group.sessionContext?.courseTitle ??
                      'Historische Terminrückmeldung'}
                </h4>
                {group.sessionContext !== null && (
                  <dl className="review-feedback-context">
                    <div>
                      <dt>{label('course.singular')}</dt>
                      <dd>
                        {group.sessionContext.courseCode} ·{' '}
                        {group.sessionContext.courseTitle}
                      </dd>
                    </div>
                    <div>
                      <dt>Termin</dt>
                      <dd>{group.sessionContext.sessionType}</dd>
                    </div>
                    <div>
                      <dt>Datum und Uhrzeit</dt>
                      <dd>
                        {formatCalendarDate(group.sessionContext.date)},{' '}
                        {group.sessionContext.startTime}–
                        {group.sessionContext.endTime} (
                        {group.sessionContext.timeZone})
                      </dd>
                    </div>
                    <div>
                      <dt>{label('room.singular')}</dt>
                      <dd>{group.sessionContext.roomName}</dd>
                    </div>
                    <div>
                      <dt>{label('cohort.singular')}</dt>
                      <dd>{group.sessionContext.cohortName}</dd>
                    </div>
                    <div>
                      <dt>Offene Markierungen „Nicht möglich“</dt>
                      <dd>{group.impossibleFlagCount}</dd>
                    </div>
                  </dl>
                )}
                <ul>
                  {group.items.map((item) => (
                    <li
                      key={item.id}
                      className={
                        item.sessionStatus === 'changed' ||
                        item.sessionStatus === 'unavailable'
                          ? 'review-feedback-item-historical'
                          : undefined
                      }
                    >
                      {item.sessionStatus === 'changed' && (
                        <p className="review-feedback-resolution">
                          Erledigt durch Terminänderung · Diese Rückmeldung zählt nicht mehr als offen.
                        </p>
                      )}
                      {item.sessionStatus === 'unavailable' && (
                        <p className="review-feedback-resolution">
                          Historisch · Der erfasste Termin ist nicht mehr in dieser Zuordnung verfügbar.
                        </p>
                      )}
                      <strong>{feedbackKindLabel(item.kind)}</strong>
                      {item.comment !== null && <p>{item.comment}</p>}
                      <p>{feedbackAttribution(item.attribution)}</p>
                      <time dateTime={item.submittedAt}>
                        {formatTimestamp(item.submittedAt, item.timeZone)} ({item.timeZone})
                      </time>
                      {item.sessionContext != null && (
                        <dl className="review-feedback-item-context">
                          <div><dt>Erfasste {label('course.singular')}</dt><dd>{item.sessionContext.courseCode} · {item.sessionContext.courseTitle}</dd></div>
                          <div><dt>Erfasster Termin</dt><dd>{humanize(item.sessionContext.sessionKind)} · {item.sessionContext.sessionType}</dd></div>
                          <div><dt>Erfasstes Datum und Uhrzeit</dt><dd>{formatCalendarDate(item.sessionContext.date)}, {item.sessionContext.startTime}–{item.sessionContext.endTime} ({item.sessionContext.timeZone})</dd></div>
                          <div><dt>Erfasster {label('room.singular')}</dt><dd>{item.sessionContext.roomName}</dd></div>
                          <div><dt>Erfasste {label('cohort.singular')}</dt><dd>{item.sessionContext.cohortName}</dd></div>
                          <div><dt>Erfasste Studienart</dt><dd>{item.sessionContext.studyType ?? 'Nicht verfügbar'}</dd></div>
                          {item.sessionContext.sessionKind === 'teaching' ? (
                            <div><dt>Lehreinheiten</dt><dd>{item.sessionContext.teachingUnits ?? 'Nicht verfügbar'}</dd></div>
                          ) : (
                            <div><dt>Dauer</dt><dd>{item.sessionContext.examDurationMinutes == null ? 'Nicht verfügbar' : `${item.sessionContext.examDurationMinutes} Minuten`}</dd></div>
                          )}
                        </dl>
                      )}
                    </li>
                  ))}
                </ul>
                {group.currentNavigation !== null ? (
                  <button
                    type="button"
                    onClick={() =>
                      onOpenCurrentSession?.(group.currentNavigation!)
                    }
                  >
                    Aktuellen Termin öffnen
                  </button>
                ) : (
                  group.level === 'session' && (
                    <p>Der Ablauf für den aktuellen Termin ist nicht verfügbar.</p>
                  )
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="review-issue-controls">
        <label htmlFor="lecturer-review-lecturer">{label('lecturer.singular')}</label>
        <select
          id="lecturer-review-lecturer"
          value={lecturerId}
          onChange={(event) => setLecturerId(event.target.value)}
          disabled={!working || busy}
        >
          <option value="">{label('lecturer.singular')} auswählen</option>
          {currentOverview.lecturers.map((lecturer) => (
            <option
              value={lecturer.lecturerId}
              disabled={!lecturer.initialIssueAllowed}
              key={lecturer.lecturerId}
            >
              {lecturer.lecturerName}
            </option>
          ))}
        </select>

        <label htmlFor="lecturer-review-duration">Dauer</label>
        <select
          id="lecturer-review-duration"
          value={durationDays}
          onChange={(event) =>
            setDurationDays(Number(event.target.value) as 1 | 2 | 3)
          }
          disabled={!working || busy}
        >
          <option value="1">1 Tag</option>
          <option value="2">2 Tage</option>
          <option value="3">3 Tage</option>
        </select>

        <button type="button" disabled={!canIssue} onClick={() => void issue()}>
          Zugangslink erstellen
        </button>
      </div>

      {!working && (
        <p role="note">
          Erste Zugangslinks können nur aus einer Arbeitsrevision im Entwurf oder im Status „Bereit zur Prüfung“ erstellt werden.
        </p>
      )}

      <aside className="review-warning">
        <strong>Manuelle Zustellung</strong>
        <p>
          Senden Sie den Link selbst über einen privaten Kanal. Wer den Link besitzt, kann die zugeordnete Planung lesen und bis zum Zugangsende beratende Rückmeldungen abgeben.
        </p>
      </aside>

      {currentOverview.links.length > 0 && (
        <section
          className="review-link-history"
          aria-labelledby="review-link-history"
        >
          <h3 id="review-link-history">Linkverlauf</h3>
          <ul>
            {currentOverview.links.map((link) => {
              const uncertain = uncertainLinkIds.has(link.id)
              const active = link.status === 'active' && !uncertain
              return (
                <li key={link.id}>
                  <strong>{link.intendedLecturerName}</strong>
                  <span>
                    {uncertain ? 'Status unbekannt' : humanize(link.status)}
                  </span>
                  <span>
                    Erstellt {formatTimestamp(link.issuedAt, link.timeZone)} · endet{' '}
                    {formatTimestamp(link.expiresAt, link.timeZone)}
                  </span>
                  {link.endedAt !== null && (
                    <span>Beendet {formatTimestamp(link.endedAt, link.timeZone)}</span>
                  )}
                  {active && (
                    <div className="review-link-actions">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void revoke(link.id)}
                      >
                        Link widerrufen
                      </button>
                      {link.replaceAllowed && (
                        <>
                          <label htmlFor={`replacement-duration-${link.id}`}>
                            Dauer des Ersatzlinks
                          </label>
                          <select
                            id={`replacement-duration-${link.id}`}
                            value={replacementDurationDays}
                            disabled={busy}
                            onChange={(event) =>
                              setReplacementDurationDays(
                                Number(event.target.value) as 1 | 2 | 3,
                              )
                            }
                          >
                            <option value="1">1 Tag</option>
                            <option value="2">2 Tage</option>
                            <option value="3">3 Tage</option>
                          </select>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void replace(link.id)}
                          >
                            Link ersetzen
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </section>
      )}

      {issued !== null && transientUrl !== null && (
        <section className="review-one-time-result" aria-labelledby="review-url">
          <h3 id="review-url">Einmalig angezeigte Rückmeldungs-URL</h3>
          <p className="review-secret-url">{transientUrl}</p>
          <dl className="review-metadata">
            <div>
              <dt>{label('lecturer.singular')}</dt>
              <dd>{issued.issuedLink.intendedLecturerName}</dd>
            </div>
            <div>
              <dt>Revision</dt>
              <dd>{issued.overview.revision.label}</dd>
            </div>
            <div>
              <dt>{label('course.plural')}</dt>
              <dd>
                {detailLecturer?.courses
                  .map((course) => course.title)
                  .join(', ') || `Keine zugeordneten ${label('course.plural')}`}
              </dd>
            </div>
            <div>
              <dt>Erstellt</dt>
              <dd>{formatTimestamp(issued.issuedLink.issuedAt, issued.issuedLink.timeZone)}</dd>
            </div>
            <div>
              <dt>Zugang endet</dt>
              <dd>
                {formatTimestamp(issued.issuedLink.expiresAt, issued.issuedLink.timeZone)} (
                {issued.issuedLink.timeZone})
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{humanize(issued.issuedLink.status)}</dd>
            </div>
          </dl>
          <div className="review-result-actions">
            <button type="button" onClick={() => void copy()}>
              Link kopieren
            </button>
            <button type="button" onClick={dismiss}>
              Schließen
            </button>
          </div>
        </section>
      )}

      {status && <p role="status">{status}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  )
}

function humanize(value: string) {
  return ({
    draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung', published: 'Veröffentlicht',
    active: 'Aktiv', revoked: 'Widerrufen', expired: 'Abgelaufen', replaced: 'Ersetzt', revision_ended: 'Revision beendet',
    revision: 'Revision', teaching: 'Lehrtermin', exam: 'Prüfung',
  } as Record<string, string>)[value] ?? 'Unbekannter Status'
}

function feedbackKindLabel(value: string) {
  if (value === 'impossible_session') return 'Nicht möglich'
  if (value === 'session_comment') return 'Terminkommentar'
  return 'Revisionskommentar'
}

function feedbackAttribution(value: string) {
  const match = /^Submitted through the review link intended for (.+); identity was not authenticated\.$/.exec(value)
  return match
    ? `Über den Rückmeldungslink für ${match[1]} eingereicht; die Identität wurde nicht authentifiziert.`
    : 'Über einen kontolosen Rückmeldungslink eingereicht; die Identität wurde nicht authentifiziert.'
}

function formatTimestamp(value: string, _timeZone: string) {
  void _timeZone
  return formatViennaDateTime(value)
}
