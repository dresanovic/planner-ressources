import { describe, expect, it } from 'vitest'

import { draftScheduleFixture } from '../test/draftScheduleFixtures'
import { filterSessions, groupSessionsByWeek } from './scheduleReviewUtils'

describe('scheduleReviewUtils', () => {
  it('groups sessions by week and day', () => {
    const groups = groupSessionsByWeek(draftScheduleFixture.sessions)

    expect(groups).toEqual([
      {
        weekStart: '2026-09-07',
        days: [
          {
            date: '2026-09-07',
            sessions: [draftScheduleFixture.sessions[1]],
          },
        ],
      },
      {
        weekStart: '2026-09-14',
        days: [
          {
            date: '2026-09-14',
            sessions: [draftScheduleFixture.sessions[0]],
          },
        ],
      },
    ])
  })

  it('keeps all sessions when filters are empty', () => {
    expect(filterSessions(draftScheduleFixture.sessions, {})).toHaveLength(2)
  })

  it('applies match-all filters', () => {
    const sessions = [
      draftScheduleFixture.sessions[0],
      {
        ...draftScheduleFixture.sessions[1],
        cohortId: 2,
        roomId: 2,
      },
    ]

    expect(filterSessions(sessions, { cohortId: 1, roomId: 1 })).toEqual([
      draftScheduleFixture.sessions[0],
    ])
    expect(filterSessions(sessions, { cohortId: 1, roomId: 2 })).toEqual([])
  })

  it('clears filters by using an empty filter object', () => {
    const filtered = filterSessions(draftScheduleFixture.sessions, { courseId: 1 })
    const cleared = filterSessions(filtered, {})

    expect(cleared).toHaveLength(2)
  })
})
