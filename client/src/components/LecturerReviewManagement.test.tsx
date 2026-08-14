import { act, type ComponentType, type ComponentProps } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LECTURER_REVIEW_COMMENT_CANARY,
  LECTURER_REVIEW_SECRET_CANARY,
  LECTURER_REVIEW_REPLACEMENT_SECRET_CANARY,
  issuedLecturerReviewLinkFixture,
  lecturerReviewLinkFixture,
  plannerLecturerReviewOverviewFixture,
} from '../test/lecturerReviewFixtures'
import type {
  IssueLecturerReviewInput,
  IssuedLecturerReviewLink,
  LecturerReviewOverview,
} from '../api/lecturerReview'
import { LecturerReviewManagement } from './LecturerReviewManagement'

let root: Root | null = null

type ReplacementInput = { durationDays: 1 | 2 | 3 }
type Us3ManagementProps = ComponentProps<typeof LecturerReviewManagement> & {
  onRevoke: (linkId: number) => Promise<LecturerReviewOverview>
  onReplace: (
    linkId: number,
    input: ReplacementInput,
  ) => Promise<IssuedLecturerReviewLink>
  onOpenCurrentSession: (navigation: {
    revisionId: number
    occurrenceRef: string
  }) => void
}
const Us3LecturerReviewManagement =
  LecturerReviewManagement as ComponentType<Us3ManagementProps>

function overview(
  state: 'draft' | 'ready_for_review' | 'published' = 'ready_for_review',
): LecturerReviewOverview {
  const fixture = plannerLecturerReviewOverviewFixture()
  return {
    ...fixture,
    revision: { ...fixture.revision, state },
    links: [],
    lecturers: [
      ...fixture.lecturers.map((lecturer) => ({
        ...lecturer,
        initialIssueAllowed: state !== 'published',
      })),
      {
        lecturerId: 9,
        lecturerName: 'Unassigned Lecturer',
        sessionCount: 0,
        courses: [],
        initialIssueAllowed: false,
      },
    ],
    feedbackGroups: [],
    totalFeedbackCount: 0,
    impossibleFlagCount: 0,
  }
}

function activeOverview(
  state: 'draft' | 'ready_for_review' | 'published' = 'ready_for_review',
): LecturerReviewOverview {
  const fixture = plannerLecturerReviewOverviewFixture()
  return {
    ...fixture,
    revision: { ...fixture.revision, state },
    links: [lecturerReviewLinkFixture()],
  }
}

function replacementResult(durationDays: 1 | 2 | 3 = 3) {
  const current = lecturerReviewLinkFixture()
  const issued = issuedLecturerReviewLinkFixture(
    LECTURER_REVIEW_REPLACEMENT_SECRET_CANARY,
  )
  const oldLink = {
    ...current,
    status: 'replaced' as const,
    endedAt: '2026-09-29T08:00:00Z',
    replaceAllowed: false,
  }
  const replacement = {
    ...current,
    id: 502,
    durationDays,
    issuedAt: '2026-09-29T08:00:00Z',
    expiresAt:
      durationDays === 1
        ? '2026-09-30T08:00:00Z'
        : durationDays === 2
          ? '2026-10-01T08:00:00Z'
          : '2026-10-02T08:00:00Z',
  }
  const replacementOverview = {
    ...issued.overview,
    links: [oldLink, replacement],
  }
  return {
    ...issued,
    issuedLink: replacement,
    overview: replacementOverview,
  }
}

function feedbackOverview(): LecturerReviewOverview {
  const fixture = plannerLecturerReviewOverviewFixture()
  const [revision, teaching, exam] = fixture.feedbackGroups
  return {
    ...fixture,
    totalFeedbackCount: 6,
    impossibleFlagCount: 3,
    feedbackGroups: [
      revision,
      {
        ...teaching,
        impossibleFlagCount: 1,
        items: [
          ...teaching.items,
          {
            id: 704,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'impossible_session',
            comment: 'Monday morning cannot work.',
            sessionContext: teaching.sessionContext,
            sessionStatus: 'current',
            submittedAt: '2026-09-28T09:50:00Z',
            timeZone: 'Europe/Vienna',
          },
        ],
      },
      {
        ...exam,
        impossibleFlagCount: 2,
        items: [
          ...exam.items,
          {
            id: 705,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'impossible_session',
            comment: 'Could take this exam on 15 December.',
            sessionContext: exam.sessionContext,
            sessionStatus: 'current',
            submittedAt: '2026-09-28T09:55:00Z',
            timeZone: 'Europe/Vienna',
          },
        ],
      },
      {
        groupRef: 'teaching:303',
        level: 'session',
        sessionContext: {
          sessionRef: 'teaching:303',
          sessionKind: 'teaching',
          sourceSessionId: 303,
          sessionType: 'Lecture',
          courseSourceId: 45,
          courseCode: 'COURSE-45',
          courseTitle: 'Computer Networks',
          date: '2026-11-09',
          startTime: '15:00',
          endTime: '17:25',
          timeZone: 'Europe/Vienna',
          roomName: 'Historical Room C',
          cohortName: 'CS-26',
        },
        currentNavigation: null,
        impossibleFlagCount: 0,
        items: [
          {
            id: 706,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'impossible_session',
            comment: 'I am away on that date.',
            sessionContext: {
              sessionRef: 'teaching:303',
              sessionKind: 'teaching',
              sourceSessionId: 303,
              sessionType: 'Lecture',
              courseSourceId: 45,
              courseCode: 'COURSE-45',
              courseTitle: 'Computer Networks',
              date: '2026-11-09',
              startTime: '15:00',
              endTime: '17:25',
              timeZone: 'Europe/Vienna',
              roomName: 'Historical Room C',
              cohortName: 'CS-26',
            },
            sessionStatus: 'unavailable',
            submittedAt: '2026-09-28T10:00:00Z',
            timeZone: 'Europe/Vienna',
          },
        ],
      },
    ],
  }
}

async function renderManagement({
  currentOverview = overview(),
  issue = vi.fn().mockResolvedValue(issuedLecturerReviewLinkFixture()),
  revoke = vi.fn(),
  replace = vi.fn(),
  openCurrentSession = vi.fn(),
}: {
  currentOverview?: LecturerReviewOverview
  issue?: ReturnType<typeof vi.fn>
  revoke?: ReturnType<typeof vi.fn>
  replace?: ReturnType<typeof vi.fn>
  openCurrentSession?: ReturnType<typeof vi.fn>
} = {}) {
  root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => {
    root?.render(
      <Us3LecturerReviewManagement
        overview={currentOverview}
        busy={false}
        onIssue={
          issue as unknown as (
            input: Required<IssueLecturerReviewInput>,
          ) => Promise<IssuedLecturerReviewLink>
        }
        onRevoke={
          revoke as unknown as (
            linkId: number,
          ) => Promise<LecturerReviewOverview>
        }
        onReplace={
          replace as unknown as (
            linkId: number,
            input: ReplacementInput,
          ) => Promise<IssuedLecturerReviewLink>
        }
        onOpenCurrentSession={
          openCurrentSession as unknown as (navigation: {
            revisionId: number
            occurrenceRef: string
          }) => void
        }
      />,
    )
    await Promise.resolve()
  })
  return { issue, revoke, replace, openCurrentSession }
}

function labelledControl<T extends HTMLElement>(labelText: string) {
  const label = [...document.querySelectorAll<HTMLLabelElement>('label')].find(
    (candidate) => candidate.textContent?.includes(labelText),
  )
  if (!label) return null
  if (label.htmlFor) {
    return document.getElementById(label.htmlFor) as T | null
  }
  return label.querySelector<T>('input, select, textarea')
}

function button(label: string) {
  return [...document.querySelectorAll<HTMLButtonElement>('button')].find(
    (candidate) => candidate.textContent?.trim() === label,
  )
}

function notPossibleFilter() {
  return [...document.querySelectorAll<HTMLButtonElement>('button')].find(
    (candidate) =>
      candidate.textContent?.includes('Nicht möglich') &&
      candidate.hasAttribute('aria-pressed'),
  )
}

function feedbackGroup(title: string) {
  const heading = [...document.querySelectorAll<HTMLHeadingElement>('h3, h4')].find(
    (candidate) => candidate.textContent?.includes(title),
  )
  return heading?.closest<HTMLElement>('article') ?? null
}

function scopedButton(scope: ParentNode, label: string) {
  return [...scope.querySelectorAll<HTMLButtonElement>('button')].find(
    (candidate) => candidate.textContent?.trim() === label,
  )
}

async function change(control: HTMLSelectElement, value: string) {
  await act(async () => {
    control.value = value
    control.dispatchEvent(new Event('change', { bubbles: true }))
    await Promise.resolve()
  })
}

async function click(control: HTMLButtonElement | undefined) {
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
  vi.restoreAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  })
})

describe('LecturerReviewManagement initial link issuance', () => {
  it('identifies Ready for review as recommended and limits selection to eligible lecturers', async () => {
    await renderManagement()

    expect(document.body.textContent).toContain('Working R2')
    expect(document.body.textContent).toMatch(/Bereit zur Prüfung/i)
    expect(document.body.textContent).toMatch(/Empfohlener Zeitpunkt/i)

    const lecturer = document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')
    expect(lecturer).not.toBeNull()
    expect(
      [...(lecturer?.options ?? [])].map((option) => option.textContent),
    ).toEqual(
      expect.arrayContaining(['Dr Ada Lecturer', 'Prof Grace Lecturer']),
    )
    const unassigned = [...(lecturer?.options ?? [])].find(
      (option) => option.textContent === 'Unassigned Lecturer',
    )
    expect(unassigned == null || unassigned.disabled).toBe(true)
  })

  it('issues from Draft without confirmation using the three-day default', async () => {
    const confirm = vi.spyOn(window, 'confirm')
    const issue = vi.fn().mockResolvedValue(issuedLecturerReviewLinkFixture())
    await renderManagement({ currentOverview: overview('draft'), issue })
    const lecturer = document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!
    const duration = labelledControl<HTMLSelectElement>('Dauer')!

    await change(lecturer, '7')

    expect(duration.value).toBe('3')
    expect([...duration.options].map((option) => option.textContent)).toEqual([
      '1 Tag',
      '2 Tage',
      '3 Tage',
    ])
    await click(button('Zugangslink erstellen'))

    expect(issue).toHaveBeenCalledWith({
      lecturerId: 7,
      durationDays: 3,
    })
    expect(confirm).not.toHaveBeenCalled()
  })

  it('submits a configured one- or two-day duration instead of the default', async () => {
    const issue = vi.fn().mockResolvedValue(issuedLecturerReviewLinkFixture())
    await renderManagement({ issue })
    const lecturer = document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!
    const duration = labelledControl<HTMLSelectElement>('Dauer')!

    await change(lecturer, '8')
    await change(duration, '1')
    await click(button('Zugangslink erstellen'))

    expect(issue).toHaveBeenLastCalledWith({
      lecturerId: 8,
      durationDays: 1,
    })
    expect([...duration.options].some((option) => option.value === '2')).toBe(
      true,
    )
  })

  it('does not enable initial issuance for a Published or ineligible selection', async () => {
    await renderManagement({ currentOverview: overview('published') })

    const lecturer = document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!
    await change(lecturer, '7')

    expect(button('Zugangslink erstellen')?.disabled).toBe(true)
    expect(document.body.textContent).toMatch(/Arbeitsrevision|Bereit zur Prüfung/i)
  })

  it('shows the one-time client-built URL, scope, expiry, and manual-delivery warning', async () => {
    await renderManagement()
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))

    const expectedUrl =
      `${window.location.origin}/lecturer-review/#/` +
      LECTURER_REVIEW_SECRET_CANARY
    expect(document.body.textContent).toContain(expectedUrl)
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).toContain('Working R2')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain('Data Structures')
    expect(document.body.textContent).toMatch(/Erstellt/i)
    expect(document.body.textContent).toMatch(/Zugang endet/i)
    expect(document.body.textContent).toContain('Europe/Vienna')
    expect(document.body.textContent).toMatch(/Aktiv/i)
    expect(document.body.textContent).toMatch(/Manuelle Zustellung|selbst/i)
    expect(document.body.textContent).toMatch(/privaten Kanal/i)
    expect(document.body.textContent).toMatch(/Wer den Link besitzt/i)
  })

  it('formats planner timestamps in the declared review time zone', async () => {
    await renderManagement({ currentOverview: activeOverview() })
    expect(document.body.textContent).toContain('28.09.2026')
    expect(document.body.textContent).toContain('Europe/Vienna')
  })

  it('does not restore a one-time URL after the management view is unmounted', async () => {
    await renderManagement()
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))
    expect(document.body.textContent).toContain(LECTURER_REVIEW_SECRET_CANARY)

    await act(async () => {
      root?.render(<div>Outside lecturer reviews</div>)
      await Promise.resolve()
    })
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )

    await act(async () => {
      root?.render(
        <LecturerReviewManagement
          overview={overview()}
          busy={false}
          onIssue={vi.fn()}
        />,
      )
      await Promise.resolve()
    })
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })

  it('copies exactly the transient URL and announces success without persistence', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')
    await renderManagement()
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))
    const expectedUrl =
      `${window.location.origin}/lecturer-review/#/` +
      LECTURER_REVIEW_SECRET_CANARY

    await click(button('Link kopieren'))

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expectedUrl)
    expect(document.querySelector('[role="status"]')?.textContent).toMatch(
      /kopiert/i,
    )
    expect(storageWrite).not.toHaveBeenCalled()
  })

  it('announces clipboard denial without losing or regenerating the one-time URL', async () => {
    const issue = vi.fn().mockResolvedValue(issuedLecturerReviewLinkFixture())
    vi.mocked(navigator.clipboard.writeText).mockRejectedValue(
      new DOMException('Denied', 'NotAllowedError'),
    )
    await renderManagement({ issue })
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))

    await click(button('Link kopieren'))

    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /konnte nicht kopiert werden/i,
    )
    expect(document.body.textContent).toContain(LECTURER_REVIEW_SECRET_CANARY)
    expect(issue).toHaveBeenCalledTimes(1)
  })

  it('dismisses and clears the secret when the selected revision changes', async () => {
    await renderManagement()
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))
    expect(document.body.textContent).toContain(LECTURER_REVIEW_SECRET_CANARY)

    await click(button('Schließen'))
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )

    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')
    await click(button('Zugangslink erstellen'))
    const changedOverview = {
      ...overview(),
      revision: {
        ...overview().revision,
        id: 16,
        label: 'Working R3',
      },
    }
    await act(async () => {
      root?.render(
        <LecturerReviewManagement
          overview={changedOverview}
          busy={false}
          onIssue={vi.fn()}
        />,
      )
      await Promise.resolve()
    })

    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })

  it('keeps callback error details and bearer values out of the alert and browser storage', async () => {
    const storageWrite = vi.spyOn(Storage.prototype, 'setItem')
    const issue = vi.fn().mockRejectedValue(
      new Error(
        `Unsafe issue detail for ${LECTURER_REVIEW_SECRET_CANARY}`,
      ),
    )
    await renderManagement({ issue })
    await change(document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!, '7')

    await click(button('Zugangslink erstellen'))

    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /konnte nicht erstellt werden/i,
    )
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(storageWrite).not.toHaveBeenCalled()
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('keeps the one-time URL non-navigating and exposes keyboard focus and assistive copy status', async () => {
    const open = vi.spyOn(window, 'open')
    const address = window.location.href
    await renderManagement()
    const lecturer = document.querySelector<HTMLSelectElement>('#lecturer-review-lecturer')!
    await change(lecturer, '7')
    const issue = button('Zugangslink erstellen')!

    issue.focus()
    expect(document.activeElement).toBe(issue)
    await act(async () => {
      issue.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }),
      )
      issue.click()
      issue.dispatchEvent(
        new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }),
      )
      await Promise.resolve()
    })

    const transientUrl =
      document.querySelector<HTMLElement>('.review-secret-url')!
    expect(transientUrl.tagName).toBe('P')
    expect(transientUrl.closest('a[href]')).toBeNull()
    expect(document.querySelector('a[href]')).toBeNull()
    expect(document.querySelector('form[action]')).toBeNull()
    const copy = button('Link kopieren')!
    copy.focus()
    await click(copy)

    expect(document.activeElement).toBe(copy)
    expect(document.querySelector('[role="status"]')?.textContent).toMatch(
      /kopiert/i,
    )
    expect(open).not.toHaveBeenCalled()
    expect(window.location.href).toBe(address)
    expect(
      [...document.querySelectorAll<HTMLButtonElement>('button')].every(
        (control) => control.type === 'button',
      ),
    ).toBe(true)
  })
})

describe('LecturerReviewManagement link ending and replacement', () => {
  it('revokes the selected active link and renders the authoritative ended status', async () => {
    const current = activeOverview()
    const revokedOverview: LecturerReviewOverview = {
      ...current,
      links: current.links.map((link) => ({
        ...link,
        status: 'revoked' as const,
        endedAt: '2026-09-29T08:00:00Z',
        replaceAllowed: false,
      })),
    }
    const revoke = vi.fn().mockResolvedValue(revokedOverview)
    await renderManagement({ currentOverview: current, revoke })

    expect(document.body.textContent).toContain('Aktiv')
    await click(button('Link widerrufen'))

    expect(revoke).toHaveBeenCalledWith(501)
    expect(document.body.textContent).toMatch(/Link wurde widerrufen/i)
    expect(document.body.textContent).toContain('Widerrufen')
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })

  it('replaces an active link with a new duration and reveals only the new one-time URL', async () => {
    const replace = vi.fn().mockResolvedValue(replacementResult(1))
    await renderManagement({
      currentOverview: activeOverview(),
      replace,
    })
    const duration =
      labelledControl<HTMLSelectElement>('Dauer des Ersatzlinks')!

    expect(duration.value).toBe('3')
    expect([...duration.options].map((option) => option.textContent)).toEqual([
      '1 Tag',
      '2 Tage',
      '3 Tage',
    ])
    await change(duration, '1')
    await click(button('Link ersetzen'))

    expect(replace).toHaveBeenCalledWith(501, { durationDays: 1 })
    expect(document.body.textContent).toContain(
      `${window.location.origin}/lecturer-review/#/${LECTURER_REVIEW_REPLACEMENT_SECRET_CANARY}`,
    )
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(document.body.textContent).toMatch(/frühere/i)
    expect(document.body.textContent).toMatch(/nicht mehr verfügbar|beendet/i)
  })

  it('allows replacement for an active current-Published link while initial issue stays disabled', async () => {
    await renderManagement({
      currentOverview: activeOverview('published'),
      replace: vi.fn().mockResolvedValue(replacementResult()),
    })

    expect(button('Zugangslink erstellen')?.disabled).toBe(true)
    expect(button('Link ersetzen')?.disabled).toBe(false)
    expect(document.body.textContent).toMatch(/Veröffentlicht/i)
  })

  it('handles a lost replacement response without inventing a secret or presenting the old link as usable', async () => {
    const replace = vi
      .fn()
      .mockRejectedValue(new TypeError('Connection ended after commit'))
    await renderManagement({
      currentOverview: activeOverview(),
      replace,
    })

    await click(button('Link ersetzen'))

    expect(replace).toHaveBeenCalledWith(501, { durationDays: 3 })
    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /Ergebnis.*unbekannt|Antwort verloren/i,
    )
    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /Laden Sie den aktuellen Status/i,
    )
    expect(document.querySelector('[role="alert"]')?.textContent).toMatch(
      /neuen Ersatzlink/i,
    )
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_REPLACEMENT_SECRET_CANARY,
    )
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(button('Link kopieren')).toBeUndefined()
  })

  it('keeps expired, revoked, replaced, and revision-ended links as non-secret history', async () => {
    const base = lecturerReviewLinkFixture()
    const ended: LecturerReviewOverview = {
      ...activeOverview(),
      links: (
        [
          ['expired', 501],
          ['revoked', 502],
          ['replaced', 503],
          ['revision_ended', 504],
        ] as const
      ).map(([status, id], index) => ({
        ...base,
        id,
        status,
        endedAt: `2026-09-${26 + index}T08:00:00Z`,
        replaceAllowed: false,
      })),
    }
    await renderManagement({ currentOverview: ended })

    expect(document.body.textContent).toContain('Abgelaufen')
    expect(document.body.textContent).toContain('Widerrufen')
    expect(document.body.textContent).toContain('Ersetzt')
    expect(document.body.textContent).toContain('Revision beendet')
    expect(button('Link widerrufen')).toBeUndefined()
    expect(button('Link ersetzen')).toBeUndefined()
    expect(button('Link kopieren')).toBeUndefined()
    expect(document.body.textContent).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })
})

describe('LecturerReviewManagement planner feedback filter', () => {
  it('separates feedback from access-link management while showing the open count', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })

    const feedbackTab = button('Rückmeldungen (5 offen)')!
    const linksTab = button('Zugangslinks')!
    const feedbackPanel = document.querySelector<HTMLElement>('#review-workflow-panel-feedback')!
    const linksPanel = document.querySelector<HTMLElement>('#review-workflow-panel-links')!

    expect(feedbackTab.getAttribute('aria-selected')).toBe('true')
    expect(feedbackPanel.hidden).toBe(false)
    expect(linksPanel.hidden).toBe(true)

    await click(linksTab)

    expect(linksTab.getAttribute('aria-selected')).toBe('true')
    expect(feedbackPanel.hidden).toBe(true)
    expect(linksPanel.hidden).toBe(false)
  })

  it('filters immutable items before regrouping and derives all four counters from the same scope', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    const counters = document.querySelector('.coordination-counters')!

    expect(counters.textContent).toMatch(/5.*Einträge/i)
    expect(counters.textContent).toMatch(/2.*Kommentare/i)
    expect(counters.textContent).toMatch(/3.*offen nicht möglich/i)
    expect(counters.textContent).toMatch(/2.*betroffene Termine/i)

    await change(
      labelledControl<HTMLSelectElement>('Art der Rückmeldung')!,
      'session_comment',
    )
    expect(counters.textContent).toMatch(/1.*Einträge/i)
    expect(counters.textContent).toMatch(/1.*Kommentare/i)
    expect(counters.textContent).toMatch(/0.*nicht möglich/i)
    expect(counters.textContent).toMatch(/1.*betroffene Termine/i)
    expect(document.body.textContent).not.toContain(
      'Tuesday and Thursday are generally preferable.',
    )

    await change(
      labelledControl<HTMLSelectElement>('Lehrveranstaltung')!,
      '42',
    )
    expect(document.querySelectorAll('.review-feedback-group')).toHaveLength(1)

    await click(button('Rückmeldungsfilter zurücksetzen'))
    expect(counters.textContent).toMatch(/5.*Einträge/i)
    expect(document.body.textContent).toContain(
      'Tuesday and Thursday are generally preferable.',
    )
  })

  it('counts repeated impossible items separately and affected sessions distinctly', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    await change(
      labelledControl<HTMLSelectElement>('Art der Rückmeldung')!,
      'impossible_session',
    )
    const counters = document.querySelector('.coordination-counters')!

    expect(counters.textContent).toMatch(/3.*Einträge/i)
    expect(counters.textContent).toMatch(/3.*offen nicht möglich/i)
    expect(counters.textContent).toMatch(/2.*betroffene Termine/i)
    expect(document.body.textContent).not.toContain(
      'Could this session start at 10:00?',
    )
  })

  it('places a native keyboard-focusable Not possible filter above management with the exact flag-item count', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    const filter = notPossibleFilter()!
    const lecturer = labelledControl<HTMLSelectElement>('Rückmeldung von Lehrende Person')!

    expect(filter.tagName).toBe('BUTTON')
    expect(filter.type).toBe('button')
    expect(filter.tabIndex).toBeGreaterThanOrEqual(0)
    expect(filter.textContent).toMatch(/Nicht möglich.*3|3.*Nicht möglich/)
    expect(filter.getAttribute('aria-pressed')).toBe('false')
    expect(
      filter.compareDocumentPosition(lecturer) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()

    filter.focus()
    expect(document.activeElement).toBe(filter)
    await act(async () => {
      filter.dispatchEvent(
        new KeyboardEvent('keydown', { key: ' ', bubbles: true }),
      )
      filter.click()
      filter.dispatchEvent(
        new KeyboardEvent('keyup', { key: ' ', bubbles: true }),
      )
      await Promise.resolve()
    })

    expect(filter.getAttribute('aria-pressed')).toBe('true')
    expect(document.activeElement?.textContent).toMatch(
      /Rückmeldungen.*Nicht möglich/i,
    )
  })

  it('filters to each currently affected session exactly once while retaining every item in each group', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    await click(notPossibleFilter())

    const algorithms = feedbackGroup('Algorithms')!
    const structures = feedbackGroup('Data Structures')!
    const networks = feedbackGroup('Computer Networks')
    const affected = [algorithms, structures]

    expect(affected.every((group) => group !== null)).toBe(true)
    expect(new Set(affected).size).toBe(2)
    expect(algorithms.textContent).toContain(
      'Could this session start at 10:00?',
    )
    expect(algorithms.textContent).toContain('Monday morning cannot work.')
    expect(structures.textContent).toContain(
      LECTURER_REVIEW_COMMENT_CANARY,
    )
    expect(
      document.querySelector(
        'script, iframe, object, embed, img, svg, [onerror], [onclick]',
      ),
    ).toBeNull()
    expect(structures.textContent).toContain(
      'Could take this exam on 15 December.',
    )
    expect(networks).toBeNull()
    expect(document.body.textContent).not.toContain(
      'Tuesday and Thursday are generally preferable.',
    )

    expect(
      [...document.querySelectorAll('h3, h4')].filter((heading) =>
        heading.textContent?.includes('Data Structures'),
      ),
    ).toHaveLength(1)
  })

  it('intersects the Not possible toggle with item filters and clears both scopes together', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    await change(labelledControl<HTMLSelectElement>('Lehrveranstaltung')!, '42')

    expect(notPossibleFilter()?.textContent).toMatch(/Nicht möglich.*1|1.*Nicht möglich/)
    await click(notPossibleFilter())

    const counters = document.querySelector('.coordination-counters')!
    expect(counters.textContent).toMatch(/2.*Einträge/i)
    expect(counters.textContent).toMatch(/1.*Kommentare/i)
    expect(counters.textContent).toMatch(/1.*nicht möglich/i)
    expect(counters.textContent).toMatch(/1.*betroffene Termine/i)
    expect(document.querySelectorAll('.review-feedback-group')).toHaveLength(1)

    await click(button('Rückmeldungsfilter zurücksetzen'))

    expect(notPossibleFilter()?.getAttribute('aria-pressed')).toBe('false')
    expect(labelledControl<HTMLSelectElement>('Lehrveranstaltung')?.value).toBe('')
    expect(counters.textContent).toMatch(/5.*Einträge/i)
  })

  it('uses visible non-color kind labels and retains historical session context without a guessed action', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })
    await change(labelledControl<HTMLSelectElement>('Status')!, 'resolved')
    const historical = feedbackGroup('Computer Networks')!

    expect(historical.textContent).toContain('Nicht möglich')
    expect(historical.textContent).toContain('COURSE-45')
    expect(historical.textContent).toContain('09.11.2026')
    expect(historical.textContent).toContain('15:00')
    expect(historical.textContent).toContain('17:25')
    expect(historical.textContent).toContain('Europe/Vienna')
    expect(historical.textContent).toContain('Historical Room C')
    expect(historical.textContent).toContain('CS-26')
    expect(historical.textContent).toContain('Dr Ada Lecturer')
    expect(historical.textContent).toMatch(
      /Identität wurde nicht authentifiziert|Rückmeldungslink für/i,
    )
    expect(historical.textContent).toMatch(
      /aktuellen Termin.*nicht verfügbar|kann nicht geöffnet werden/i,
    )
    expect(historical.textContent).toContain('Historisch')
    expect(
      [...historical.querySelectorAll('button')].some(
        (candidate) => candidate.textContent?.trim() === 'Aktuellen Termin öffnen',
      ),
    ).toBe(false)
  })

  it('renders every item from its own complete captured session context', async () => {
    const captured = feedbackOverview()
    const teaching = captured.feedbackGroups.find(
      (group) => group.groupRef === 'teaching:101',
    )!
    teaching.items[1] = {
      ...teaching.items[1],
      sessionContext: {
        ...teaching.items[1].sessionContext!,
        sessionType: 'Workshop before revision',
        courseCode: 'HIST-42',
        courseTitle: 'Algorithms before revision',
        date: '2026-10-04',
        roomName: 'Historical Lab',
        cohortName: 'CS-25',
        studyType: 'Part-time',
        teachingUnits: 2,
      },
    }
    await renderManagement({ currentOverview: captured })

    const teachingItem = [...document.querySelectorAll<HTMLLIElement>(
      '.review-feedback-group li',
    )].find((item) => item.textContent?.includes('Monday morning cannot work.'))!
    expect(teachingItem.textContent).toContain('HIST-42')
    expect(teachingItem.textContent).toContain('Algorithms before revision')
    expect(teachingItem.textContent).toContain('Workshop before revision')
    expect(teachingItem.textContent).toContain('Historical Lab')
    expect(teachingItem.textContent).toContain('Part-time')
    expect(teachingItem.textContent).toMatch(/Lehreinheiten.*2/i)

    const examItem = [...document.querySelectorAll<HTMLLIElement>(
      '.review-feedback-group li',
    )].find((item) => item.textContent?.includes(LECTURER_REVIEW_COMMENT_CANARY))!
    expect(examItem.textContent).toContain('COURSE-43')
    expect(examItem.textContent).toContain('Written exam')
    expect(examItem.textContent).toMatch(/Dauer.*120 Minuten/i)
  })

  it('invokes the authoritative current-session action only for a supplied navigation target', async () => {
    const openCurrentSession = vi.fn()
    await renderManagement({
      currentOverview: feedbackOverview(),
      openCurrentSession,
    })
    await click(notPossibleFilter())
    const algorithms = feedbackGroup('Algorithms')!

    await click(scopedButton(algorithms, 'Aktuellen Termin öffnen'))

    expect(openCurrentSession).toHaveBeenCalledWith({
      revisionId: 15,
      occurrenceRef: 'teaching:101',
    })
    expect(openCurrentSession).toHaveBeenCalledTimes(1)
  })

  it('clears the filter without changing links, feedback, or any mutation callback', async () => {
    const issue = vi.fn()
    const revoke = vi.fn()
    const replace = vi.fn()
    await renderManagement({
      currentOverview: feedbackOverview(),
      issue,
      revoke,
      replace,
    })
    const filter = notPossibleFilter()!
    await click(filter)
    expect(document.body.textContent).not.toContain(
      'Tuesday and Thursday are generally preferable.',
    )

    await click(filter)

    expect(filter.getAttribute('aria-pressed')).toBe('false')
    expect(document.body.textContent).toContain(
      'Tuesday and Thursday are generally preferable.',
    )
    expect(filter.textContent).toMatch(/3/)
    expect(issue).not.toHaveBeenCalled()
    expect(revoke).not.toHaveBeenCalled()
    expect(replace).not.toHaveBeenCalled()
  })

  it('shows an exact complete zero without rendering an alert control', async () => {
    const empty: LecturerReviewOverview = {
      ...feedbackOverview(),
      totalFeedbackCount: 0,
      impossibleFlagCount: 0,
      feedbackGroups: [],
    }
    await renderManagement({ currentOverview: empty })
    expect(notPossibleFilter()).toBeUndefined()
    expect(document.body.textContent).toContain(
      'Keine offenen Rückmeldungen „Nicht möglich“.',
    )
    expect(document.body.textContent).not.toMatch(/unvollständig|nicht verfügbar/i)
    expect(document.querySelectorAll('article')).toHaveLength(0)
  })

  it('clears changed impossible feedback from the alert while retaining it as resolved history', async () => {
    const changed: LecturerReviewOverview = plannerLecturerReviewOverviewFixture()
    const impossible = changed.feedbackGroups[2].items[0]
    impossible.sessionStatus = 'changed'
    changed.feedbackGroups[2].impossibleFlagCount = 0
    changed.impossibleFlagCount = 0

    await renderManagement({ currentOverview: changed })

    expect(notPossibleFilter()).toBeUndefined()
    expect(document.querySelector('.coordination-counters')?.textContent)
      .toMatch(/0.*offen nicht möglich/i)
    expect(document.body.textContent).not.toContain('Erledigt durch Terminänderung')

    await change(labelledControl<HTMLSelectElement>('Status')!, 'resolved')

    expect(document.body.textContent).toContain('Erledigt durch Terminänderung')
    expect(document.body.textContent).toContain(LECTURER_REVIEW_COMMENT_CANARY)
  })

  it.each([
    ['partial', /unvollständig/i],
    ['unavailable', /nicht verfügbar/i],
  ] as const)(
    'does not misrepresent %s feedback as a numeric zero',
    async (availability, message) => {
      const incomplete: LecturerReviewOverview = {
        ...feedbackOverview(),
        feedbackAvailability: availability,
        totalFeedbackCount: null,
        impossibleFlagCount: null,
        feedbackGroups: [],
      }
      await renderManagement({ currentOverview: incomplete })
      const filter = notPossibleFilter()!

      expect(filter.textContent).not.toMatch(/\b0\b/)
      expect(document.body.textContent).toMatch(message)
      expect(filter.disabled).toBe(true)
      expect(document.querySelector('.review-feedback-announcement')?.textContent)
        .not.toMatch(/\b0\b/)
      expect(document.body.textContent).not.toContain(
        'Für diese Revision wurde noch keine Rückmeldung abgegeben.',
      )
    },
  )
})

describe('LecturerReviewManagement FS-015 slice exclusions', () => {
  it('keeps delivery manual and exposes no multi-lecturer credential, automated messaging, approval, resolution, or publication gate', async () => {
    await renderManagement({ currentOverview: feedbackOverview() })

    expect(document.body.textContent).toMatch(/selbst über einen privaten Kanal/i)
    const actionLabels = [
      ...document.querySelectorAll<HTMLButtonElement>('button'),
    ].map((candidate) => candidate.textContent?.trim() ?? '')
    expect(actionLabels.some((label) =>
      /send email|send invite|send to all|approve|accept feedback|resolve|block publication|publish/i.test(
        label,
      ),
    )).toBe(false)
    expect(document.querySelector('input[type="email"]')).toBeNull()
    expect(document.querySelector('input[type="file"]')).toBeNull()
  })
})
