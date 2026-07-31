import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  buildLecturerReviewUrl,
  getLecturerReviewOverview,
  getPublicLecturerReview,
  issueLecturerReviewLink,
  LecturerReviewApiError,
  submitPublicLecturerFeedback,
} from './lecturerReview'
import {
  issuedLecturerReviewLinkFixture,
  LECTURER_REVIEW_SECRET_CANARY,
  lecturerReviewFeedbackInputFixtures,
  lecturerReviewLinkFixture,
  lecturerReviewPublicErrorFixtures,
  plannerLecturerReviewOverviewFixture,
  publicLecturerFeedbackFixture,
  publicLecturerReviewFixture,
} from '../test/lecturerReviewFixtures'


afterEach(() => vi.unstubAllGlobals())


describe('lecturer review API', () => {
  it('uses planner paths and applies the three-day issue default', async () => {
    const overview = plannerLecturerReviewOverviewFixture()
    const issued = issuedLecturerReviewLinkFixture()
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(overview), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(issued), { status: 201 }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getLecturerReviewOverview(15)).resolves.toEqual(overview)
    await expect(
      issueLecturerReviewLink(15, { lecturerId: 7 }),
    ).resolves.toEqual(issued)

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/schedule-revisions/15/lecturer-review',
    )
    expect(fetchMock.mock.calls[1][0]).toBe(
      '/api/schedule-revisions/15/lecturer-review-links',
    )
    expect(fetchMock.mock.calls[1][1]).toEqual(
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      }),
    )
    expect(JSON.parse(String(fetchMock.mock.calls[1][1].body))).toEqual({
      lecturerId: 7,
      durationDays: 3,
    })
    expect(issued.secret).toBe(LECTURER_REVIEW_SECRET_CANARY)
    expect(JSON.stringify(overview)).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
  })

  it('uses the exact relative public path with omitted credentials and an in-memory bearer', async () => {
    const review = publicLecturerReviewFixture()
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(review), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
    ).resolves.toEqual(review)

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [path, options] = fetchMock.mock.calls[0]
    expect(path).toBe('/api/public/lecturer-review')
    expect(path).not.toContain(LECTURER_REVIEW_SECRET_CANARY)
    expect(options).toEqual(
      expect.objectContaining({
        method: 'GET',
        credentials: 'omit',
        headers: expect.objectContaining({
          Authorization: `Bearer ${LECTURER_REVIEW_SECRET_CANARY}`,
        }),
      }),
    )
    expect(options.body).toBeUndefined()
  })

  it('constructs the public fragment URL on the client from an explicit origin', () => {
    expect(
      buildLecturerReviewUrl(
        LECTURER_REVIEW_SECRET_CANARY,
        'https://planner.example.edu',
      ),
    ).toBe(
      `https://planner.example.edu/lecturer-review/#/${LECTURER_REVIEW_SECRET_CANARY}`,
    )
    expect(
      buildLecturerReviewUrl(
        LECTURER_REVIEW_SECRET_CANARY,
        'https://planner.example.edu/',
      ),
    ).toBe(
      `https://planner.example.edu/lecturer-review/#/${LECTURER_REVIEW_SECRET_CANARY}`,
    )
  })

  it('rejects malformed planner, issue, and minimum public DTOs at runtime', async () => {
    const overviewWithSecret = {
      ...plannerLecturerReviewOverviewFixture(),
      secret: LECTURER_REVIEW_SECRET_CANARY,
    }
    const issuedWithMalformedSecret = {
      ...issuedLecturerReviewLinkFixture(),
      secret: 'too-short',
    }
    const publicReviewWithPlannerData = {
      ...publicLecturerReviewFixture(),
      plannerNotes: ['Do not expose this field.'],
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(overviewWithSecret), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(issuedWithMalformedSecret), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(publicReviewWithPlannerData), {
          status: 200,
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    const overviewError = await captureError(() =>
      getLecturerReviewOverview(15),
    )
    const issuedError = await captureError(() =>
      issueLecturerReviewLink(15, { lecturerId: 7, durationDays: 1 }),
    )
    const publicError = await captureError(() =>
      getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
    )

    for (const error of [overviewError, issuedError, publicError]) {
      expect(error).toBeInstanceOf(LecturerReviewApiError)
      expect(error).toMatchObject({ status: 502 })
    }
  })

  it('rejects nested public privacy canaries while accepting nullable historical context', async () => {
    const unsafeCourse = structuredClone(publicLecturerReviewFixture())
    Object.assign(unsafeCourse.courses[0], {
      lecturerIds: [7],
      plannerNotes: ['private'],
    })
    const historical = structuredClone(plannerLecturerReviewOverviewFixture())
    const context = historical.feedbackGroups.find(
      (group) => group.sessionContext !== null,
    )?.sessionContext
    if (context) {
      Object.assign(
        context as unknown as Record<string, unknown>,
        {
          studyType: null,
          teachingUnits: null,
          examDurationMinutes: null,
        },
      )
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(unsafeCourse), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(historical), { status: 200 }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
    ).rejects.toMatchObject({ status: 502 })
    await expect(getLecturerReviewOverview(15)).resolves.toEqual(historical)
  })

  it('rejects internally inconsistent public projection references and kind metadata', async () => {
    const mismatchedCourse = structuredClone(publicLecturerReviewFixture())
    mismatchedCourse.courses[0].sessions[0].courseRef = 'course:999'
    const invalidKindMetadata = structuredClone(publicLecturerReviewFixture())
    invalidKindMetadata.courses[0].sessions[0].teachingUnits = null
    const missingFinding = structuredClone(publicLecturerReviewFixture())
    missingFinding.courses[0].sessions[0].validationFindingRefs = [
      'public-finding:missing',
    ]
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mismatchedCourse), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(invalidKindMetadata), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(missingFinding), { status: 200 }),
      )
    vi.stubGlobal('fetch', fetchMock)

    for (let attempt = 0; attempt < 3; attempt += 1) {
      await expect(
        getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
      ).rejects.toMatchObject({ status: 502 })
    }
  })

  it('never copies a bearer secret or unsafe server detail into routine errors', async () => {
    const unsafeServerMessage =
      `Unexpected failure for ${LECTURER_REVIEW_SECRET_CANARY}`
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            code: 'UNEXPECTED_FAILURE',
            message: unsafeServerMessage,
          }),
          { status: 500 },
        ),
      )
      .mockRejectedValueOnce(new TypeError(unsafeServerMessage))
    vi.stubGlobal('fetch', fetchMock)

    const httpError = await captureError(() =>
      getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
    )
    const transportError = await captureError(() =>
      getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY),
    )

    expect(httpError).toBeInstanceOf(LecturerReviewApiError)
    expect(transportError).toBeInstanceOf(LecturerReviewApiError)
    expect(serializeError(httpError)).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(serializeError(transportError)).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(serializeError(httpError)).not.toContain(unsafeServerMessage)
    expect(serializeError(transportError)).not.toContain(unsafeServerMessage)
  })

  it('does not expose the one-time secret in a routine link summary', () => {
    const routineSummary = lecturerReviewLinkFixture()

    expect(routineSummary).not.toHaveProperty('secret')
    expect(routineSummary).not.toHaveProperty('reviewUrl')
  })

  it('submits every feedback payload and keeps one logical retry UUID stable', async () => {
    const inputs = lecturerReviewFeedbackInputFixtures()
    const items = publicLecturerFeedbackFixture()
    const createdResults = items.map((item) => ({
      outcome: 'created' as const,
      item,
    }))
    const alreadyAcceptedResult = {
      outcome: 'already_accepted' as const,
      item: items[2],
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(createdResults[0]), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(createdResults[1]), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(createdResults[2]), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(alreadyAcceptedResult), { status: 200 }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        inputs.revisionComment,
      ),
    ).resolves.toEqual(createdResults[0])
    await expect(
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        inputs.sessionComment,
      ),
    ).resolves.toEqual(createdResults[1])
    await expect(
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        inputs.impossibleSession,
      ),
    ).resolves.toEqual(createdResults[2])
    await expect(
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        inputs.impossibleSession,
      ),
    ).resolves.toEqual(alreadyAcceptedResult)

    expect(fetchMock).toHaveBeenCalledTimes(4)
    for (const [path, options] of fetchMock.mock.calls) {
      expect(path).toBe('/api/public/lecturer-review/feedback')
      expect(path).not.toContain(LECTURER_REVIEW_SECRET_CANARY)
      expect(options).toEqual(
        expect.objectContaining({
          method: 'POST',
          credentials: 'omit',
          headers: expect.objectContaining({
            Authorization: `Bearer ${LECTURER_REVIEW_SECRET_CANARY}`,
            'Content-Type': 'application/json',
          }),
        }),
      )
    }
    expect(
      fetchMock.mock.calls.map(([, options]) =>
        JSON.parse(String(options.body)),
      ),
    ).toEqual([
      inputs.revisionComment,
      inputs.sessionComment,
      inputs.impossibleSession,
      inputs.impossibleSession,
    ])
    const firstAttempt = JSON.parse(
      String(fetchMock.mock.calls[2][1].body),
    )
    const ambiguousRetry = JSON.parse(
      String(fetchMock.mock.calls[3][1].body),
    )
    expect(ambiguousRetry.clientSubmissionId).toBe(
      firstAttempt.clientSubmissionId,
    )
  })

  it('preserves validation, refresh-required, and throttle outcomes without protected data', async () => {
    const input = lecturerReviewFeedbackInputFixtures().sessionComment
    const errors = lecturerReviewPublicErrorFixtures
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(errors.invalidFeedback), { status: 422 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(errors.refreshRequired), { status: 409 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(errors.throttled), {
          status: 429,
          headers: { 'Retry-After': '60' },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    const validationError = await captureError(() =>
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        input,
      ),
    )
    const refreshError = await captureError(() =>
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        input,
      ),
    )
    const throttleError = await captureError(() =>
      submitPublicLecturerFeedback(
        LECTURER_REVIEW_SECRET_CANARY,
        input,
      ),
    )

    expect(validationError).toBeInstanceOf(LecturerReviewApiError)
    expect(validationError).toMatchObject({
      status: 422,
      code: 'INVALID_FEEDBACK',
      message: errors.invalidFeedback.message,
    })
    expect(refreshError).toBeInstanceOf(LecturerReviewApiError)
    expect(refreshError).toMatchObject({
      status: 409,
      code: 'REVIEW_REFRESH_REQUIRED',
      message: errors.refreshRequired.message,
    })
    expect(throttleError).toBeInstanceOf(LecturerReviewApiError)
    expect(throttleError).toMatchObject({
      status: 429,
      code: 'REVIEW_TEMPORARILY_UNAVAILABLE',
      message: errors.throttled.message,
      retryable: true,
    })
    for (const error of [
      validationError,
      refreshError,
      throttleError,
    ]) {
      expect(serializeError(error)).not.toContain(
        LECTURER_REVIEW_SECRET_CANARY,
      )
      expect(serializeError(error)).not.toContain('Dr Ada Lecturer')
      expect(serializeError(error)).not.toContain('teaching:101')
    }
  })
})


async function captureError(action: () => Promise<unknown>) {
  try {
    await action()
  } catch (error) {
    return error
  }
  throw new Error('Expected the lecturer review request to fail.')
}


function serializeError(error: unknown) {
  if (!(error instanceof Error)) return JSON.stringify(error)
  return JSON.stringify({
    ...error,
    name: error.name,
    message: error.message,
  })
}
