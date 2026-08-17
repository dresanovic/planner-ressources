import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LECTURER_REVIEW_COMMENT_CANARY,
  LECTURER_REVIEW_SECRET_CANARY,
  lecturerCalendarDownloadFixture,
  lecturerReviewFeedbackResultFixture,
  longLabelPublicLecturerReviewFixture,
  publicLecturerReviewFixture,
} from '../test/lecturerReviewFixtures'

const api = vi.hoisted(() => ({
  downloadPublicLecturerCalendar: vi.fn(),
  getPublicLecturerReview: vi.fn(),
  submitPublicLecturerFeedback: vi.fn(),
}))

vi.mock('../api/lecturerReview', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/lecturerReview')>()),
  downloadPublicLecturerCalendar: api.downloadPublicLecturerCalendar,
  getPublicLecturerReview: api.getPublicLecturerReview,
  submitPublicLecturerFeedback: api.submitPublicLecturerFeedback,
}))

import { LecturerReviewApiError } from '../api/lecturerReview'
import { LecturerReviewPage } from './LecturerReviewPage'

let root: Root | null = null

async function renderPage(secret: string | null = LECTURER_REVIEW_SECRET_CANARY) {
  root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => {
    root?.render(<LecturerReviewPage secret={secret} />)
    await Promise.resolve()
  })
  await act(async () => {
    await Promise.resolve()
  })
}

function button(label: string) {
  return [...document.querySelectorAll<HTMLButtonElement>('button')].find(
    (candidate) => candidate.textContent?.trim() === label,
  )
}

async function click(control: HTMLElement | undefined | null) {
  await act(async () => {
    control?.click()
    await Promise.resolve()
  })
}

async function typeIn(control: HTMLTextAreaElement, value: string) {
  await act(async () => {
    control.value = value
    control.dispatchEvent(new Event('input', { bubbles: true }))
    await Promise.resolve()
  })
}

function labelledControl<T extends HTMLElement>(labelText: string) {
  const label = [...document.querySelectorAll<HTMLLabelElement>('label')].find(
    (candidate) => candidate.textContent?.includes(labelText),
  )
  return label?.querySelector<T>('input, select, textarea') ?? null
}

async function change(control: HTMLSelectElement, value: string) {
  await act(async () => {
    control.value = value
    control.dispatchEvent(new Event('change', { bubbles: true }))
    await Promise.resolve()
  })
}

function feedbackItem(comment: string) {
  return [...document.querySelectorAll<HTMLLIElement>('.review-feedback-list li')]
    .find((item) => item.textContent?.includes(comment))
}

function deferred<Value>() {
  let resolve!: (value: Value) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

afterEach(() => {
  if (root) {
    act(() => root?.unmount())
    root = null
  }
  document.body.innerHTML = ''
  Object.defineProperty(window, 'innerWidth', {
    value: 1024,
    configurable: true,
  })
  vi.unstubAllGlobals()
})

beforeEach(() => {
  vi.clearAllMocks()
  api.getPublicLecturerReview.mockResolvedValue(publicLecturerReviewFixture())
  api.downloadPublicLecturerCalendar.mockResolvedValue(
    lecturerCalendarDownloadFixture(),
  )
  api.submitPublicLecturerFeedback.mockResolvedValue(
    lecturerReviewFeedbackResultFixture(),
  )
})

describe('LecturerReviewPage shared restricted workspace', () => {
  it('gates one complete-schedule browser handoff behind explicit confirmation', async () => {
    const createObjectURL = vi.fn(() => 'blob:fs020-calendar')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined)
    await renderPage()
    const sessionType = labelledControl<HTMLSelectElement>('Terminart')!
    await change(sessionType, 'exam')
    await click(button('Liste'))

    const opener = button('Kalender herunterladen')!
    await click(opener)

    expect(api.downloadPublicLecturerCalendar).not.toHaveBeenCalled()
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('2')
    await click(button('Download fortsetzen'))

    expect(api.downloadPublicLecturerCalendar).toHaveBeenCalledOnce()
    expect(api.downloadPublicLecturerCalendar).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(anchorClick).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:fs020-calendar')
    expect(sessionType.value).toBe('exam')
    expect(button('Liste')?.getAttribute('aria-pressed')).toBe('true')
    const statusText = document.querySelector('[role="status"][aria-live="polite"]')?.textContent ?? ''
    expect(statusText).not.toMatch(/Outlook.*aktualisiert|Dubletten|synchronisiert/i)
  })

  it('cancels without a request and preserves mode, revision draft, and opener focus', async () => {
    await renderPage()
    await click(button('Liste'))
    const revisionDraft = document.querySelector<HTMLTextAreaElement>('#lecturer-review-revision-comment')!
    await typeIn(revisionDraft, 'Ungesendeter Kalender-Kontext.')
    const opener = button('Kalender herunterladen')!
    await click(opener)
    await click(button('Abbrechen'))

    expect(api.downloadPublicLecturerCalendar).not.toHaveBeenCalled()
    expect(button('Liste')?.getAttribute('aria-pressed')).toBe('true')
    expect(revisionDraft.value).toBe('Ungesendeter Kalender-Kontext.')
    expect(document.activeElement).toBe(opener)
  })

  it('keeps a retryable failure in the dialog and retries once per confirmation', async () => {
    const createObjectURL = vi.fn(() => 'blob:fs020-calendar-retry')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
    api.downloadPublicLecturerCalendar
      .mockRejectedValueOnce(new LecturerReviewApiError(503, 'raw hidden', true))
      .mockResolvedValueOnce(lecturerCalendarDownloadFixture())
    await renderPage()
    await click(button('Kalender herunterladen'))

    await click(button('Download fortsetzen'))
    expect(api.downloadPublicLecturerCalendar).toHaveBeenCalledTimes(1)
    expect(document.querySelector('[role="alert"]')?.textContent).toContain('vorübergehend')
    expect(document.body.textContent).not.toContain('raw hidden')

    await click(button('Download fortsetzen'))
    expect(api.downloadPublicLecturerCalendar).toHaveBeenCalledTimes(2)
    expect(document.querySelector('.lecturer-calendar-download-dialog')).toBeNull()
    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledOnce()
  })

  it('clears protected DOM on a terminal calendar result', async () => {
    api.downloadPublicLecturerCalendar.mockRejectedValueOnce(
      new LecturerReviewApiError(404, 'This review is unavailable.', false, 'REVIEW_UNAVAILABLE'),
    )
    await renderPage()
    const revisionDraft = document.querySelector<HTMLTextAreaElement>('#lecturer-review-revision-comment')!
    await typeIn(revisionDraft, 'Protected calendar draft.')
    await click(button('Kalender herunterladen'))
    await click(button('Download fortsetzen'))

    expect(document.body.textContent).toContain('nicht verfügbar')
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Protected calendar draft.')
    expect(document.querySelector('.calendar-workspace')).toBeNull()
  })

  it('shows zero as the informational count for an authoritative empty review', async () => {
    const empty = publicLecturerReviewFixture()
    empty.courses = []
    api.getPublicLecturerReview.mockResolvedValueOnce(empty)
    await renderPage()
    await click(button('Kalender herunterladen'))

    expect(document.querySelector('.lecturer-calendar-download-dialog')?.textContent).toContain('0 Termine')
    expect(api.downloadPublicLecturerCalendar).not.toHaveBeenCalled()
  })

  it('shows complete fixed-context teaching and exam scope in all established modes', async () => {
    await renderPage()

    expect(api.getPublicLecturerReview).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(document.body.textContent).toContain('Durch diesen Prüfungslink festgelegt')
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain('Data Structures')
    for (const mode of ['Woche', 'Tag', 'Monat', 'Liste']) {
      expect(button(mode)).toBeDefined()
    }
    expect(
      [...document.querySelectorAll('label')].some(
        (label) => label.textContent?.trim() === 'Lecturer',
      ),
    ).toBe(false)
    expect(document.body.textContent).not.toMatch(
      /edit session|delete with confirmation|planning failures|start draft/i,
    )
  })

  it('distinguishes an authoritative empty projection from a filter-empty result', async () => {
    const empty = publicLecturerReviewFixture()
    empty.courses = []
    empty.validationFindings = []
    empty.filterFacets = {
      courses: [],
      cohorts: [],
      rooms: [],
      studyTypes: [],
      sessionTypes: [],
      lifecycleContexts: empty.filterFacets.lifecycleContexts,
      validationCategories: [],
    }
    api.getPublicLecturerReview.mockResolvedValueOnce(empty)
    await renderPage()

    expect(document.body.textContent).toContain(
      'derzeit keine Lehr- oder Prüfungstermine',
    )
  })

  it('uses reload-only projection semantics without polling or a refresh action', async () => {
    vi.useFakeTimers()
    await renderPage()
    await act(async () => {
      vi.advanceTimersByTime(120_000)
      await Promise.resolve()
    })

    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(1)
    expect(button('Refresh schedule')).toBeUndefined()
    vi.useRealTimers()
  })

  it('opens exact teaching and exam occurrences in the reused restricted pane', async () => {
    await renderPage()

    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      'Lehreinheiten',
    )
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      'Terminkommentar senden',
    )
    expect(document.querySelector('.session-pane')?.textContent).not.toContain(
      'Termin bearbeiten',
    )

    await click(document.querySelector('[data-occurrence-ref="exam:202"]'))
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      'Written exam',
    )
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      '120 Minuten',
    )
  })

  it('keeps unsent occurrence drafts behind the shared discard decision', async () => {
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    const draft = document.querySelector<HTMLTextAreaElement>(
      '#session-comment-teaching-101',
    )!
    await typeIn(draft, 'Please move this.')

    await click(document.querySelector('[data-occurrence-ref="exam:202"]'))

    expect(document.querySelector('[role="dialog"]')?.textContent).toContain(
      'Nicht gesendete Rückmeldung verwerfen?',
    )
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      'Algorithms',
    )
    await click(button('Weiter schreiben'))
    expect(draft.value).toBe('Please move this.')
  })

  it('commits a target-hiding filter only after the unsent-feedback decision', async () => {
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    const draft = document.querySelector<HTMLTextAreaElement>(
      '#session-comment-teaching-101',
    )!
    await typeIn(draft, 'Keep this until I decide.')
    const sessionType = labelledControl<HTMLSelectElement>('Terminart')!

    await change(sessionType, 'exam')

    expect(document.querySelector('[role="dialog"]')?.textContent).toContain(
      'Nicht gesendete Rückmeldung verwerfen?',
    )
    expect(sessionType.value).toBe('')
    expect(document.querySelector('.session-pane')?.textContent).toContain(
      'Algorithms',
    )
    await click(button('Weiter schreiben'))
    expect(draft.value).toBe('Keep this until I decide.')
    expect(sessionType.value).toBe('')

    await change(sessionType, 'exam')
    await click(button('Rückmeldung verwerfen'))

    expect(sessionType.value).toBe('exam')
    expect(document.querySelector('.session-pane')).toBeNull()
    expect(document.body.textContent).toContain('1 aktive Filterbedingung')
  })

  it('does not compose the calendar notice over an existing discard decision', async () => {
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    const draft = document.querySelector<HTMLTextAreaElement>(
      '#session-comment-teaching-101',
    )!
    await typeIn(draft, 'Keep one modal only.')
    await change(labelledControl<HTMLSelectElement>('Terminart')!, 'exam')

    const download = button('Kalender herunterladen')!
    expect(download.disabled).toBe(true)
    await click(download)
    expect(document.querySelectorAll('[role="dialog"]')).toHaveLength(1)
    expect(api.downloadPublicLecturerCalendar).not.toHaveBeenCalled()
  })

  it('appends accepted feedback locally and performs no projection GET', async () => {
    const review = publicLecturerReviewFixture()
    review.submittedFeedback = []
    api.getPublicLecturerReview.mockResolvedValueOnce(review)
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    const draft = document.querySelector<HTMLTextAreaElement>(
      '#session-comment-teaching-101',
    )!
    await typeIn(draft, 'Could this start later?')

    await click(button('Terminkommentar senden'))

    expect(api.submitPublicLecturerFeedback).toHaveBeenCalledOnce()
    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(1)
    expect(document.body.textContent).toContain(
      LECTURER_REVIEW_COMMENT_CANARY,
    )
    expect(draft.value).toBe('')
  })

  it('keeps a stable retry UUID and preserves the draft after an ambiguous failure', async () => {
    api.submitPublicLecturerFeedback
      .mockRejectedValueOnce(new LecturerReviewApiError(0, 'Uncertain.', true))
      .mockResolvedValueOnce(lecturerReviewFeedbackResultFixture())
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    const draft = document.querySelector<HTMLTextAreaElement>(
      '#session-comment-teaching-101',
    )!
    await typeIn(draft, 'Retry me.')
    await click(button('Terminkommentar senden'))
    expect(draft.value).toBe('Retry me.')
    await click(button('Terminkommentar senden'))

    const first = api.submitPublicLecturerFeedback.mock.calls[0][1]
    const second = api.submitPublicLecturerFeedback.mock.calls[1][1]
    expect(second.clientSubmissionId).toBe(first.clientSubmissionId)
  })

  it('preserves an unrelated revision retry UUID when a session target becomes stale', async () => {
    api.submitPublicLecturerFeedback
      .mockRejectedValueOnce(new LecturerReviewApiError(0, 'Uncertain.', true))
      .mockRejectedValueOnce(
        new LecturerReviewApiError(
          409,
          'The schedule changed.',
          false,
          'REVIEW_REFRESH_REQUIRED',
        ),
      )
      .mockResolvedValueOnce(lecturerReviewFeedbackResultFixture())
    await renderPage()

    const revisionDraft = document.querySelector<HTMLTextAreaElement>(
      '#lecturer-review-revision-comment',
    )!
    await typeIn(revisionDraft, 'Keep this revision retry stable.')
    await click(button('Revisionskommentar senden'))
    const firstRevisionSubmission =
      api.submitPublicLecturerFeedback.mock.calls[0][1]

    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    await typeIn(
      document.querySelector<HTMLTextAreaElement>(
        '#session-comment-teaching-101',
      )!,
      'This assignment is stale.',
    )
    await click(button('Terminkommentar senden'))
    expect(revisionDraft.value).toBe('Keep this revision retry stable.')

    await click(button('Revisionskommentar senden'))
    const retriedRevisionSubmission =
      api.submitPublicLecturerFeedback.mock.calls[2][1]
    expect(retriedRevisionSubmission.clientSubmissionId).toBe(
      firstRevisionSubmission.clientSubmissionId,
    )
  })

  it('clears selected scope and directs reload without an automatic GET on stale target', async () => {
    api.submitPublicLecturerFeedback.mockRejectedValueOnce(
      new LecturerReviewApiError(
        409,
        'The schedule changed.',
        false,
        'REVIEW_REFRESH_REQUIRED',
      ),
    )
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    await typeIn(
      document.querySelector<HTMLTextAreaElement>(
        '#session-comment-teaching-101',
      )!,
      'Stale draft.',
    )
    await typeIn(
      document.querySelector<HTMLTextAreaElement>(
        '#flag-comment-teaching-101',
      )!,
      'Stale flag draft.',
    )
    await click(button('Terminkommentar senden'))

    expect(document.querySelector('.session-pane')).toBeNull()
    expect(document.body.textContent).toContain('noch nicht gesendete Rückmeldung bleibt')
    expect(document.body.textContent).toContain('Öffnen Sie den Termin erneut')
    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(1)
    expect(document.activeElement?.hasAttribute('data-workspace-results-heading')).toBe(true)

    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    expect(document.querySelector<HTMLTextAreaElement>('#session-comment-teaching-101')?.value).toBe('Stale draft.')
    expect(document.querySelector<HTMLTextAreaElement>('#flag-comment-teaching-101')?.value).toBe('Stale flag draft.')
  })

  it('preserves a revision draft when its submission becomes stale', async () => {
    api.submitPublicLecturerFeedback.mockRejectedValueOnce(
      new LecturerReviewApiError(409, 'The schedule changed.', false, 'REVIEW_REFRESH_REQUIRED'),
    )
    await renderPage()
    const revisionDraft = document.querySelector<HTMLTextAreaElement>('#lecturer-review-revision-comment')!
    await typeIn(revisionDraft, 'Stale revision draft.')

    await click(button('Revisionskommentar senden'))

    expect(revisionDraft.value).toBe('Stale revision draft.')
    expect(document.body.textContent).toContain('Revisionskommentar bleibt im Eingabefeld erhalten')
    expect(document.body.textContent).not.toContain('Öffnen Sie den Termin erneut')
  })

  it('announces and focuses results when a newly loaded projection removes the selected assignment', async () => {
    const reduced = publicLecturerReviewFixture()
    reduced.courses = reduced.courses.filter(
      (course) => course.courseRef !== 'course:42',
    )
    reduced.filterFacets.courses = reduced.filterFacets.courses.filter(
      (course) => course.value !== 'course:42',
    )
    reduced.filterFacets.rooms = reduced.filterFacets.rooms.filter(
      (room) => room.value !== 'room:101',
    )
    api.getPublicLecturerReview
      .mockResolvedValueOnce(publicLecturerReviewFixture())
      .mockResolvedValueOnce(reduced)
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    await typeIn(
      document.querySelector<HTMLTextAreaElement>('#session-comment-teaching-101')!,
      'This draft loses its assignment.',
    )

    await act(async () => {
      root?.render(<LecturerReviewPage secret="FS015ChangedSecretCanary22222222222222222" />)
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(document.querySelector('.session-pane')).toBeNull()
    expect(document.body.textContent).toMatch(/ausgewählte Termin.*nicht mehr enthalten/i)
    expect(document.body.textContent).not.toContain(
      'This draft loses its assignment.',
    )
    expect(document.activeElement?.hasAttribute('data-workspace-results-heading')).toBe(true)
  })

  it('associates same-link feedback history with safe current or historical session identity', async () => {
    const review = publicLecturerReviewFixture()
    review.submittedFeedback.push({
      id: 704,
      kind: 'session_comment',
      sessionRef: 'teaching:999',
      comment: 'Historical assignment comment.',
      submittedAt: '2026-09-28T10:00:00Z',
      timeZone: 'Europe/Vienna',
    })
    api.getPublicLecturerReview.mockResolvedValueOnce(review)
    await renderPage()

    const current = feedbackItem('Could this session start at 10:00?')!
    expect(current.textContent).toMatch(/Lehrtermin.*COURSE-42.*Algorithms/i)
    expect(current.textContent).toContain('05.10.2026')
    const historical = feedbackItem('Historical assignment comment.')!
    expect(historical.textContent).toContain('Lehrtermin 999')
    expect(historical.textContent).toMatch(/nicht mehr.*aktuellen Zuordnung/i)
    expect(historical.textContent).not.toMatch(/planner|capacity|configuration/i)
  })

  it('clears every protected workspace field on a terminal feedback result', async () => {
    api.submitPublicLecturerFeedback.mockRejectedValueOnce(
      new LecturerReviewApiError(404, 'Unavailable.', false, 'REVIEW_UNAVAILABLE'),
    )
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))
    await typeIn(
      document.querySelector<HTMLTextAreaElement>(
        '#session-comment-teaching-101',
      )!,
      'Protected draft.',
    )
    await click(button('Terminkommentar senden'))

    expect(document.body.textContent).toContain('Terminprüfung nicht verfügbar')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).not.toContain('Protected draft.')
  })

  it('does not let an older in-flight success restore a terminal state', async () => {
    const pending = deferred<ReturnType<typeof publicLecturerReviewFixture>>()
    api.getPublicLecturerReview.mockReturnValueOnce(pending.promise)
    await renderPage()
    root?.render(<LecturerReviewPage secret={null} />)
    await act(async () => {
      await Promise.resolve()
    })
    pending.resolve(publicLecturerReviewFixture())
    await act(async () => {
      await Promise.resolve()
    })

    expect(document.body.textContent).toContain('Terminprüfung nicht verfügbar')
    expect(document.body.textContent).not.toContain('Algorithms')
  })

  it('uses full-screen focus-contained restricted pane composition at narrow width', async () => {
    Object.defineProperty(window, 'innerWidth', {
      value: 320,
      configurable: true,
    })
    api.getPublicLecturerReview.mockResolvedValueOnce(
      longLabelPublicLecturerReviewFixture(),
    )
    await renderPage()
    await click(document.querySelector('[data-occurrence-ref="teaching:101"]'))

    const pane = document.querySelector('.session-pane')
    expect(pane?.classList.contains('session-pane-fullscreen')).toBe(true)
    expect(pane?.getAttribute('role')).toBe('dialog')
    expect(pane?.getAttribute('aria-modal')).toBe('true')
    expect(pane?.textContent).toContain(
      'Building North, fourth floor, seminar room with a deliberately long name',
    )
    expect(pane?.textContent).toContain('Working R2')
    expect(pane?.textContent).toContain('Bereit zur Prüfung')
    expect(pane?.textContent).toContain('COURSE-42')
  })
})
