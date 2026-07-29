import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LECTURER_REVIEW_COMMENT_CANARY,
  LECTURER_REVIEW_SECRET_CANARY,
  lecturerReviewFeedbackResultFixture,
  lecturerReviewPublicErrorFixtures,
  publicLecturerReviewFixture,
} from '../test/lecturerReviewFixtures'

const api = vi.hoisted(() => ({
  getPublicLecturerReview: vi.fn(),
  submitPublicLecturerFeedback: vi.fn(),
}))

vi.mock('../api/lecturerReview', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/lecturerReview')>()),
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

function deferred<Value>() {
  let resolve!: (value: Value) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function sectionWithHeading(heading: string) {
  const target = [...document.querySelectorAll('h1, h2, h3, h4')].find(
    (candidate) => candidate.textContent?.trim() === heading,
  )
  return target?.closest<HTMLElement>('section, article, li') ?? null
}

function sessionItem(sessionType: string) {
  return (
    [...document.querySelectorAll<HTMLElement>('li')].find((candidate) =>
      candidate.textContent?.includes(sessionType),
    ) ?? null
  )
}

function labelledControl<T extends HTMLElement>(
  scope: ParentNode,
  labelText: string,
) {
  const label = [...scope.querySelectorAll<HTMLLabelElement>('label')].find(
    (candidate) => candidate.textContent?.includes(labelText),
  )
  if (!label) return null
  if (label.htmlFor) return document.getElementById(label.htmlFor) as T | null
  return label.querySelector<T>('input, textarea, select')
}

function scopedButton(scope: ParentNode, label: string) {
  return [...scope.querySelectorAll<HTMLButtonElement>('button')].find(
    (candidate) => candidate.textContent?.trim() === label,
  )
}

async function typeIn(control: HTMLTextAreaElement, value: string) {
  await act(async () => {
    control.value = value
    control.dispatchEvent(new Event('input', { bubbles: true }))
    await Promise.resolve()
  })
}

async function clickAndFlush(control: HTMLButtonElement | undefined) {
  await act(async () => {
    control?.click()
    await Promise.resolve()
  })
  await act(async () => {
    await Promise.resolve()
  })
}

afterEach(() => {
  if (root) {
    act(() => root?.unmount())
    root = null
  }
})

beforeEach(() => {
  vi.clearAllMocks()
  api.getPublicLecturerReview.mockResolvedValue(publicLecturerReviewFixture())
  api.submitPublicLecturerFeedback.mockResolvedValue(
    lecturerReviewFeedbackResultFixture(),
  )
})

describe('LecturerReviewPage read-only schedule', () => {
  it('renders the complete intended-lecturer scope across teaching and exam courses', async () => {
    await renderPage()

    expect(api.getPublicLecturerReview).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).toContain(
      'does not authenticate the person using it',
    )
    expect(document.body.textContent).toContain('Winter semester 2026')
    expect(document.body.textContent).toContain('Working R2')
    expect(document.body.textContent).toMatch(/Ready for review/i)
    expect(document.body.textContent).toMatch(/Access expires/i)
    expect(document.body.textContent).toContain('Europe/Vienna')
    expect(document.body.textContent).toContain('COURSE-42')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain('Lecture')
    expect(document.body.textContent).toContain('Room A-101')
    expect(document.body.textContent).toContain('COURSE-43')
    expect(document.body.textContent).toContain('Data Structures')
    expect(document.body.textContent).toContain('Written exam')
    expect(document.body.textContent).toContain('Auditorium B')
    expect(document.body.textContent).toMatch(/read.?only/i)
    expect(document.body.textContent).toMatch(/advisory/i)

    expect(document.body.textContent).not.toContain('Resource Planner')
    expect(document.body.textContent).not.toContain('Planner administration')
    expect(document.body.textContent).not.toContain('Prof Grace Lecturer')
    expect(document.body.textContent).not.toContain('Validation findings')
    expect(document.querySelector('nav')).toBeNull()
  })

  it('keeps a complete empty assignment projection valid and reviewable', async () => {
    api.getPublicLecturerReview.mockResolvedValue({
      ...publicLecturerReviewFixture(),
      courses: [],
      submittedFeedback: [],
    })

    await renderPage()

    expect(document.body.textContent).toMatch(
      /no (assigned )?(courses|sessions)|schedule is empty/i,
    )
    expect(document.body.textContent).toMatch(/Revision comment/i)
    expect(button('Refresh schedule')).toBeDefined()
    expect(document.body.textContent).not.toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
  })

  it('refreshes the authoritative schedule without changing the in-memory credential', async () => {
    await renderPage()

    await act(async () => {
      button('Refresh schedule')?.click()
      await Promise.resolve()
    })

    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(2)
    expect(api.getPublicLecturerReview).toHaveBeenLastCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })

  it('renders markup-looking retained feedback literally and never creates executable DOM', async () => {
    await renderPage()

    expect(document.body.textContent).toContain(LECTURER_REVIEW_COMMENT_CANARY)
    expect(
      document.querySelector(
        'script, iframe, object, embed, img, svg, [onerror], [onclick]',
      ),
    ).toBeNull()
  })

  it('renders the one identical non-disclosing state for unusable credentials', async () => {
    api.getPublicLecturerReview.mockRejectedValue(
      lecturerReviewPublicErrorFixtures.unavailable,
    )

    await renderPage()

    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Working R2')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).not.toContain('2026-10-01')
    expect(document.body.textContent).not.toContain('expired')
    expect(document.body.textContent).not.toContain('revoked')
  })

  it('fails safely without making a request when bootstrap supplies no valid secret', async () => {
    await renderPage(null)

    expect(api.getPublicLecturerReview).not.toHaveBeenCalled()
    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
  })

  it('never writes the bearer secret or protected review to browser storage', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')

    await renderPage()

    expect(storageWrite).not.toHaveBeenCalled()
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('does not disclose a bearer copied into a transport error', async () => {
    api.getPublicLecturerReview.mockRejectedValue(
      new Error(
        `Unsafe network detail for ${LECTURER_REVIEW_SECRET_CANARY}`,
      ),
    )

    await renderPage()

    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /could not be reached/i,
    )
    expect(button('Retry review')).toBeDefined()
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('recovers from a temporary throttle without losing the in-memory credential', async () => {
    api.getPublicLecturerReview
      .mockRejectedValueOnce(
        new LecturerReviewApiError(
          429,
          lecturerReviewPublicErrorFixtures.throttled.message,
          true,
        ),
      )
      .mockResolvedValueOnce(publicLecturerReviewFixture())

    await renderPage()

    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(button('Retry review')).toBeDefined()
    await clickAndFlush(button('Retry review'))
    expect(api.getPublicLecturerReview).toHaveBeenLastCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
  })

  it('ignores an older successful load after a newer terminal response', async () => {
    const older = deferred<ReturnType<typeof publicLecturerReviewFixture>>()
    await renderPage()
    api.getPublicLecturerReview
      .mockReturnValueOnce(older.promise)
      .mockRejectedValueOnce(
        new LecturerReviewApiError(404, 'Ended.', false),
      )
    const refresh = button('Refresh schedule')!
    await act(async () => {
      refresh.click()
      refresh.click()
      await Promise.resolve()
    })
    await act(async () => {
      await Promise.resolve()
    })
    expect(document.body.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )

    await act(async () => {
      older.resolve(publicLecturerReviewFixture())
      await older.promise
      await Promise.resolve()
    })

    expect(document.body.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
  })

  it('formats protected timestamps in their declared time zone', async () => {
    const formatter = vi.spyOn(Date.prototype, 'toLocaleString')
    await renderPage()

    expect(formatter).toHaveBeenCalledWith(
      undefined,
      expect.objectContaining({ timeZone: 'Europe/Vienna' }),
    )
    formatter.mockRestore()
  })
})

describe('LecturerReviewPage security and accessibility regression', () => {
  it('offers no link, form action, or script-controlled external navigation', async () => {
    const open = vi.spyOn(window, 'open')
    const address = window.location.href
    await renderPage()

    expect(document.querySelector('a[href]')).toBeNull()
    expect(document.querySelector('form[action]')).toBeNull()
    expect(
      [...document.querySelectorAll<HTMLButtonElement>('button')].every(
        (control) => control.type === 'button',
      ),
    ).toBe(true)

    await clickAndFlush(button('Refresh schedule'))

    expect(open).not.toHaveBeenCalled()
    expect(window.location.href).toBe(address)
  })

  it('uses named native keyboard controls, visible focus targets, and assistive loading/status/error semantics', async () => {
    const loading = deferred<ReturnType<typeof publicLecturerReviewFixture>>()
    api.getPublicLecturerReview.mockReturnValueOnce(loading.promise)
    await renderPage()

    const busy = document.querySelector<HTMLElement>('main[aria-busy="true"]')
    expect(busy).not.toBeNull()
    expect(busy?.querySelector('[role="status"]')?.textContent).toMatch(
      /loading|please wait/i,
    )

    await act(async () => {
      loading.resolve(publicLecturerReviewFixture())
      await loading.promise
      await Promise.resolve()
    })

    const revision = sectionWithHeading('Revision comment')!
    const comment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    const submit = scopedButton(revision, 'Submit revision comment')!
    const visibleLabel = document.querySelector<HTMLLabelElement>(
      `label[for="${comment.id}"]`,
    )
    expect(comment.tagName).toBe('TEXTAREA')
    expect(visibleLabel?.textContent).toMatch(/Revision comment/i)
    expect(submit.tagName).toBe('BUTTON')
    expect(submit.type).toBe('button')
    expect(comment.tabIndex).toBeGreaterThanOrEqual(0)
    expect(submit.tabIndex).toBeGreaterThanOrEqual(0)

    await typeIn(comment, 'A keyboard-submitted recommendation.')
    submit.focus()
    expect(document.activeElement).toBe(submit)
    const pending = deferred<
      ReturnType<typeof lecturerReviewFeedbackResultFixture>
    >()
    api.submitPublicLecturerFeedback.mockReturnValueOnce(pending.promise)
    await act(async () => {
      submit.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }),
      )
      submit.click()
      submit.dispatchEvent(
        new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }),
      )
      await Promise.resolve()
    })

    expect(
      document.querySelector('[role="status"]')?.textContent,
    ).toMatch(/submitting|pending/i)
    expect(submit.disabled).toBe(true)

    await act(async () => {
      pending.resolve(lecturerReviewFeedbackResultFixture())
      await pending.promise
      await Promise.resolve()
    })

    expect(
      [...document.querySelectorAll('[role="status"]')].some((status) =>
        /feedback accepted/i.test(status.textContent ?? ''),
      ),
    ).toBe(true)

    api.submitPublicLecturerFeedback.mockRejectedValueOnce(
      new LecturerReviewApiError(422, 'Feedback was not accepted.', false),
    )
    const currentRevision = sectionWithHeading('Revision comment')!
    const currentComment = labelledControl<HTMLTextAreaElement>(
      currentRevision,
      'Revision comment',
    )!
    await typeIn(currentComment, 'Keep keyboard focus on rejection.')
    const currentSubmit =
      scopedButton(currentRevision, 'Submit revision comment')!
    currentSubmit.focus()
    await clickAndFlush(currentSubmit)

    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /not accepted/i,
    )
    expect(document.activeElement).toBe(currentSubmit)
  })
})

describe('LecturerReviewPage advisory feedback', () => {
  it('applies the 2000-character limit after trimming for every comment control', async () => {
    await renderPage()
    const revision = sectionWithHeading('Revision comment')!
    const revisionComment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    const lecture = sessionItem('Lecture')!
    const sessionComment = labelledControl<HTMLTextAreaElement>(
      lecture,
      'Session comment',
    )!
    const flagComment = labelledControl<HTMLTextAreaElement>(
      lecture,
      'Not possible explanation',
    )!

    expect(revisionComment.maxLength).toBe(-1)
    expect(sessionComment.maxLength).toBe(-1)
    expect(flagComment.maxLength).toBe(-1)

    await typeIn(
      revisionComment,
      `${' '.repeat(20)}${'x'.repeat(2000)}${' '.repeat(20)}`,
    )
    expect(revision.textContent).toMatch(/2000\s*\/\s*2000/)
    expect(
      scopedButton(revision, 'Submit revision comment')?.disabled,
    ).toBe(false)

    await clickAndFlush(scopedButton(revision, 'Submit revision comment'))

    expect(api.submitPublicLecturerFeedback).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
      expect.objectContaining({ comment: 'x'.repeat(2000) }),
    )
  })

  it('submits a revision comment with a pending state, stable attribution, and accepted announcement', async () => {
    const pending = deferred<
      ReturnType<typeof lecturerReviewFeedbackResultFixture>
    >()
    api.submitPublicLecturerFeedback.mockReturnValue(pending.promise)
    await renderPage()
    const revision = sectionWithHeading('Revision comment')!
    const comment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    const submit = scopedButton(revision, 'Submit revision comment')!

    await typeIn(comment, '  Tuesday afternoon would be preferable.  ')
    expect(revision.textContent).toMatch(/38\s*\/\s*2000/)
    await act(async () => {
      submit.click()
      await Promise.resolve()
    })

    expect(submit.disabled).toBe(true)
    expect(revision.textContent).toMatch(/submitting|pending/i)
    expect(api.submitPublicLecturerFeedback).toHaveBeenCalledTimes(1)
    expect(api.submitPublicLecturerFeedback).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
      expect.objectContaining({
        kind: 'revision_comment',
        comment: 'Tuesday afternoon would be preferable.',
        clientSubmissionId: expect.stringMatching(
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
        ),
      }),
    )

    await act(async () => {
      pending.resolve(lecturerReviewFeedbackResultFixture())
      await pending.promise
      await Promise.resolve()
    })

    expect(document.body.textContent).toMatch(/feedback accepted/i)
    expect(comment.value).toBe('')
    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(2)
  })

  it('submits an ordinary comment against the selected current session', async () => {
    await renderPage()
    const lecture = sessionItem('Lecture')!
    const comment = labelledControl<HTMLTextAreaElement>(
      lecture,
      'Session comment',
    )!

    await typeIn(comment, 'Could this start at 10:00?')
    await clickAndFlush(scopedButton(lecture, 'Submit session comment'))

    expect(api.submitPublicLecturerFeedback).toHaveBeenCalledWith(
      LECTURER_REVIEW_SECRET_CANARY,
      expect.objectContaining({
        kind: 'session_comment',
        sessionRef: 'teaching:101',
        comment: 'Could this start at 10:00?',
        clientSubmissionId: expect.any(String),
      }),
    )
    expect(document.body.textContent).toMatch(/feedback accepted/i)
  })

  it('accepts Not possible without text and a later separate flag with an optional recommendation', async () => {
    const initial = publicLecturerReviewFixture()
    const firstFlag = {
      id: 704,
      kind: 'impossible_session' as const,
      sessionRef: 'exam:202',
      comment: null,
      submittedAt: '2026-09-28T10:00:00Z',
      timeZone: 'Europe/Vienna',
    }
    const secondFlag = {
      ...firstFlag,
      id: 705,
      comment: 'Available on 15 December after 14:00.',
      submittedAt: '2026-09-28T10:05:00Z',
    }
    api.getPublicLecturerReview
      .mockResolvedValueOnce(initial)
      .mockResolvedValueOnce({
        ...initial,
        submittedFeedback: [...initial.submittedFeedback, firstFlag],
      })
      .mockResolvedValueOnce({
        ...initial,
        submittedFeedback: [
          ...initial.submittedFeedback,
          firstFlag,
          secondFlag,
        ],
      })
    api.submitPublicLecturerFeedback
      .mockResolvedValueOnce({
        outcome: 'created',
        item: firstFlag,
      })
      .mockResolvedValueOnce({
        outcome: 'created',
        item: secondFlag,
      })
    await renderPage()
    let exam = sessionItem('Written exam')!

    await clickAndFlush(scopedButton(exam, 'Not possible'))

    expect(api.submitPublicLecturerFeedback).toHaveBeenNthCalledWith(
      1,
      LECTURER_REVIEW_SECRET_CANARY,
      expect.objectContaining({
        kind: 'impossible_session',
        sessionRef: 'exam:202',
        clientSubmissionId: expect.any(String),
      }),
    )
    expect(
      api.submitPublicLecturerFeedback.mock.calls[0][1],
    ).not.toHaveProperty('comment')

    exam = sessionItem('Written exam')!
    const recommendation = labelledControl<HTMLTextAreaElement>(
      exam,
      'Not possible explanation',
    )!
    await typeIn(recommendation, 'Available on 15 December after 14:00.')
    await clickAndFlush(scopedButton(exam, 'Not possible'))

    const firstSubmission = api.submitPublicLecturerFeedback.mock.calls[0][1]
    const secondSubmission = api.submitPublicLecturerFeedback.mock.calls[1][1]
    expect(secondSubmission).toEqual(
      expect.objectContaining({
        kind: 'impossible_session',
        sessionRef: 'exam:202',
        comment: 'Available on 15 December after 14:00.',
      }),
    )
    expect(secondSubmission.clientSubmissionId).not.toBe(
      firstSubmission.clientSubmissionId,
    )
    expect(document.body.textContent).toContain(
      'Available on 15 December after 14:00.',
    )
  })

  it('preserves a rejected draft, announces the reason, and creates no false success', async () => {
    api.submitPublicLecturerFeedback.mockRejectedValue(
      new LecturerReviewApiError(
        422,
        lecturerReviewPublicErrorFixtures.invalidFeedback.message,
        false,
      ),
    )
    await renderPage()
    const revision = sectionWithHeading('Revision comment')!
    const comment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    await typeIn(comment, 'Keep this draft after rejection.')

    await clickAndFlush(scopedButton(revision, 'Submit revision comment'))

    expect(comment.value).toBe('Keep this draft after rejection.')
    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      lecturerReviewPublicErrorFixtures.invalidFeedback.message,
    )
    expect(revision.textContent).not.toMatch(/feedback accepted/i)
    expect(
      scopedButton(revision, 'Submit revision comment')?.disabled,
    ).toBe(false)
    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(1)
  })

  it('fails closed and refreshes before allowing feedback after a scope conflict', async () => {
    const refreshed = publicLecturerReviewFixture()
    const refresh = deferred<typeof refreshed>()
    api.submitPublicLecturerFeedback.mockRejectedValueOnce(
      new LecturerReviewApiError(
        409,
        lecturerReviewPublicErrorFixtures.refreshRequired.message,
        false,
        'REVIEW_REFRESH_REQUIRED',
      ),
    )
    api.getPublicLecturerReview
      .mockResolvedValueOnce(publicLecturerReviewFixture())
      .mockReturnValueOnce(refresh.promise)
    await renderPage()
    const lecture = sessionItem('Lecture')!
    const comment = labelledControl<HTMLTextAreaElement>(
      lecture,
      'Session comment',
    )!
    await typeIn(comment, 'This session has just left scope.')

    await clickAndFlush(scopedButton(lecture, 'Submit session comment'))

    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.querySelector('main[aria-busy="true"]')).not.toBeNull()

    await act(async () => {
      refresh.resolve({
        ...refreshed,
        courses: refreshed.courses.filter(
          (course) => course.sourceCourseId !== 42,
        ),
      })
      await refresh.promise
      await Promise.resolve()
    })

    expect(api.getPublicLecturerReview).toHaveBeenCalledTimes(2)
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).toContain('Data Structures')
  })

  it('reuses one logical submission identity when an ambiguous retry preserves the draft', async () => {
    api.submitPublicLecturerFeedback
      .mockRejectedValueOnce(
        new LecturerReviewApiError(
          0,
          'The feedback result is unknown. Retry this same submission.',
          true,
        ),
      )
      .mockResolvedValueOnce(lecturerReviewFeedbackResultFixture())
    await renderPage()
    const revision = sectionWithHeading('Revision comment')!
    const comment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    await typeIn(comment, 'Preserve me for a safe retry.')

    await clickAndFlush(scopedButton(revision, 'Submit revision comment'))

    expect(comment.value).toBe('Preserve me for a safe retry.')
    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /unknown|retry/i,
    )
    const firstSubmission =
      api.submitPublicLecturerFeedback.mock.calls[0][1]

    await clickAndFlush(
      scopedButton(revision, 'Retry revision comment') ??
        scopedButton(revision, 'Submit revision comment'),
    )

    const secondSubmission =
      api.submitPublicLecturerFeedback.mock.calls[1][1]
    expect(secondSubmission.clientSubmissionId).toBe(
      firstSubmission.clientSubmissionId,
    )
    expect(secondSubmission.comment).toBe(firstSubmission.comment)
    expect(comment.value).toBe('')
    expect(document.body.textContent).toMatch(/feedback accepted/i)
  })

  it('shows immutable same-link history with distinct kinds and literal markup', async () => {
    await renderPage()
    const history = sectionWithHeading('Revision comment')!

    expect(history.textContent).toMatch(/Revision comment/i)
    expect(history.textContent).toMatch(/Session comment/i)
    expect(history.textContent).toMatch(/Impossible session|Not possible/i)
    expect(history.textContent).toContain(
      'Tuesday and Thursday are generally preferable.',
    )
    expect(history.textContent).toContain(LECTURER_REVIEW_COMMENT_CANARY)
    expect(history.querySelector('script')).toBeNull()
    expect(
      [...history.querySelectorAll('button')].some((candidate) =>
        /edit|delete/i.test(candidate.textContent ?? ''),
      ),
    ).toBe(false)
  })
})

describe('LecturerReviewPage ended-link safety', () => {
  it('clears every protected field when a later refresh reports expiry, revoke, replacement, or revision end', async () => {
    api.getPublicLecturerReview
      .mockResolvedValueOnce(publicLecturerReviewFixture())
      .mockRejectedValueOnce(
        new LecturerReviewApiError(
          404,
          'The credential was revoked after the page loaded.',
          false,
        ),
      )
    await renderPage()
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain(
      'Tuesday and Thursday are generally preferable.',
    )

    await clickAndFlush(button('Refresh schedule'))

    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Working R2')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).not.toContain('Room A-101')
    expect(document.body.textContent).not.toContain(
      'Tuesday and Thursday are generally preferable.',
    )
    expect(document.body.textContent).not.toMatch(
      /expired|revoked|replaced|abandoned|superseded/i,
    )
  })

  it('clears protected data when feedback submission discovers that the link ended', async () => {
    api.submitPublicLecturerFeedback.mockRejectedValue(
      new LecturerReviewApiError(
        404,
        lecturerReviewPublicErrorFixtures.unavailable.message,
        false,
      ),
    )
    await renderPage()
    const revision = sectionWithHeading('Revision comment')!
    const comment = labelledControl<HTMLTextAreaElement>(
      revision,
      'Revision comment',
    )!
    await typeIn(comment, 'This draft must not survive ended access.')

    await clickAndFlush(scopedButton(revision, 'Submit revision comment'))

    expect(document.querySelector('[role="alert"]')?.textContent).toContain(
      lecturerReviewPublicErrorFixtures.unavailable.message,
    )
    expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).not.toContain(
      'This draft must not survive ended access.',
    )
  })

  it('renders byte-for-byte identical safe UI for every unusable-link reason', async () => {
    const reasons = [
      'malformed',
      'unknown',
      'expired',
      'revoked',
      'replaced',
      'abandoned',
      'superseded',
      'source throttled',
    ]
    const rendered: string[] = []

    for (const reason of reasons) {
      api.getPublicLecturerReview.mockRejectedValueOnce(
        new LecturerReviewApiError(
          404,
          `Unsafe internal detail: ${reason}.`,
          false,
        ),
      )
      await renderPage()
      rendered.push(document.body.innerHTML)
      expect(document.querySelector('[role="alert"]')?.textContent).toContain(
        lecturerReviewPublicErrorFixtures.unavailable.message,
      )
      expect(document.body.textContent).not.toContain(reason)
      expect(document.body.textContent).not.toContain('Dr Ada Lecturer')
      await act(async () => {
        root?.unmount()
        root = null
        await Promise.resolve()
      })
      document.body.innerHTML = ''
    }

    expect(new Set(rendered).size).toBe(1)
  })
})

describe('LecturerReviewPage FS-015 slice exclusions', () => {
  it('offers read-only schedule review and append-only feedback without account, approval, editing, attachment, or thread controls', async () => {
    await renderPage()

    expect(document.querySelector('input[type="file"]')).toBeNull()
    expect(document.querySelector('input[type="password"]')).toBeNull()
    expect(document.querySelector('input[type="email"]')).toBeNull()
    expect(document.querySelector('input[type="date"]')).toBeNull()
    expect(document.querySelector('input[type="time"]')).toBeNull()

    const actionLabels = [
      ...document.querySelectorAll<HTMLButtonElement>('button'),
    ].map((candidate) => candidate.textContent?.trim() ?? '')
    expect(actionLabels.some((label) =>
      /approve|accept schedule|publish|edit schedule|delete feedback|reply|attach|sign in|create account/i.test(
        label,
      ),
    )).toBe(false)
    expect(document.body.textContent).toMatch(/read-only/i)
    expect(document.body.textContent).toMatch(/advisory/i)
  })
})
