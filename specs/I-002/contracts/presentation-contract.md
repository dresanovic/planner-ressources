# Contract: German Labels, European Dates, and Actionable Problems

## Scope

This contract governs human-visible presentation in every current planner and accountless lecturer surface. It does not govern API payloads, persistence, comparison keys, URLs, logs, source fixtures, standards-based exports, or user-entered names/descriptions.

## Terminology consumption

1. Each approved configurable occurrence requests exactly one stable key from the effective terminology catalog.
2. Complete context values are used directly. No singular/plural derivation, grammatical inflection, or substitution into fixed German sentences occurs.
3. Application logic continues to use existing stable category IDs and domain values. A customer label can never change control flow, filtering, routing, API input, or stored data.
4. User-entered course/resource names and contextual values are rendered unchanged.
5. No UI renders before the full catalog is initialized. No missing value becomes blank or a raw key.
6. `client/index.html` declares German document language; ordinary UI copy, instructions, warnings, and errors are German and are not customer-overridable.

## Calendar date presentation

### Date-only values

- A valid machine value `2026-09-11` is displayed as `11.09.2026`.
- Every day/month is two digits and every year four digits.
- A range formats both available endpoints. For example: `11.09.2026–02.10.2026` with nearby German text that makes direction clear.
- An open-ended range states the known endpoint and does not manufacture the missing endpoint.
- Date-only formatting does not apply a timezone and cannot change the represented day.
- German weekday or month names, where retained in addition to the numeric date, use an explicit German locale.

### Timestamps

- A user-visible timestamp uses `DD.MM.YYYY` for its date part and preserves the established 24-hour time and `Europe/Vienna` meaning.
- The underlying instant remains in the existing machine value and in `<time dateTime>` where applicable.
- Device-default locale/timezone output is not used for required presentation.

### Date entry

- The visible field is a text input with `inputMode="numeric"`, a persistent `TT.MM.JJJJ` instruction, and normal keyboard/paste editing.
- The accepted complete form is exactly two day digits, dot, two month digits, dot, four year digits. Incomplete input is retained for correction but is not submitted.
- Impossible dates, non-zero-padded values, swapped/ambiguous forms, and values outside current min/max or range rules are rejected without normalization.
- A valid value converts to the same ISO calendar day before the existing API function is called.
- While visible text is invalid, the previous valid ISO value is not retained as a submittable value.
- Button-driven actions and form submission both block on invalid dates, focus the first affected date field, and show a German field-specific correction.
- A placeholder may repeat the format but never replaces the persistent label/help text.
- No calendar picker is required in FS-022.

### Machine-boundary exclusions

ISO values remain unchanged in:

- every existing API request/response and client domain type;
- database and snapshot content;
- comparisons and sorting;
- URL/query values;
- logs and technical diagnostics;
- source fixtures;
- iCalendar and other standards-based exports.

## User problem content

Every known warning or failure produces one or more separately readable problem items. Each item contains every safely known applicable element:

1. what condition occurred or which action failed;
2. the affected record, field, or attempted action;
3. the known reason, rule, expected value, or relevant boundary values;
4. whether the action is blocked or the condition is non-blocking;
5. whether entered work or the existing record remains saved/available, when known;
6. a correction, Retry, Refresh, Review, Edit, or intentional-retain path that the current user can actually perform.

Unknown facts are omitted or explicitly described as unavailable; they are never inferred from arbitrary error text. A raw status, code, or exception message is never the primary explanation.

## Problem taxonomy and recovery

| Category | Required user guidance | Direct action rule |
|---|---|---|
| Field validation | Name field and expected correction; preserve other valid input where possible | Focus/link to field; no generic Retry |
| Known rule warning | Name item, values/rule, non-blocking or blocking state, saved state, valid correction/retention | Use adjacent Edit when available; otherwise point to exact control |
| Failed safe read | Name load and context; distinguish connectivity/service/permission when known | Retry may be adjacent because the read is safe |
| Stale mutation | Name attempted action/item; explain it changed; state draft status | Refresh/review current state before repeat |
| Connectivity during mutation | Name attempted action and known draft state; outcome may be unknown | Refresh/verify before retry; never automatic retry |
| Permission failure | Name unavailable action and user-visible permission boundary without inventing cause | Point to an available alternate/review path only when real |
| Unexpected service failure | Name attempted action and known input state; do not claim a cause | Safest real retry/refresh guidance only |

A duplicated direct action is omitted when a clear adjacent control already performs it; the message identifies that control precisely.

## Multiple problems

- Preserve one item per distinct issue, including multiple field errors or warnings from one operation.
- Do not use `join`, punctuation concatenation, or a single paragraph to flatten an array of problems.
- Items have stable keys and list semantics so repeated categories remain distinguishable visually and to assistive technology.
- Long record names/details wrap without covering actions or causing horizontal page loss at supported sizes.

## Outside-recommended-window wording contract

The German wording may be refined, but it must communicate the following facts as one non-blocking warning item:

```text
Prüfung für „KI Grundlagen“: Der Termin am 11.09.2026 liegt außerhalb des empfohlenen Zeitraums 15.09.2026–30.09.2026. Die Planung bleibt gespeichert und kann beibehalten werden. Verwenden Sie „Bearbeiten“, um den Termin zu ändern.
```

- Use the actual course/exam label and actual scheduled/recommended dates.
- If the placement is not yet saved, say so; never copy the sample saved-state statement blindly.
- On an editable planner row, identify the adjacent `Bearbeiten` control rather than adding a duplicate button.
- On a read-only planner or lecturer view, give only the review/feedback/retain route actually available there.
- Do not change the existing rule, recommendation calculation, non-blocking severity, or placement.

## Safe unknown fallback

The fallback is fixed German copy populated only with caller-known safe context. It must:

- identify the attempted action and affected item when known;
- say that the exact cause is unavailable rather than fabricate one;
- state whether entered data remains in the form only when the component still holds it;
- distinguish a known connectivity failure from an unknown service failure;
- avoid direct mutation retry when the server outcome is ambiguous;
- never include stack traces, raw exception/backend message text, bearer values, URL fragments, database details, host names, private tokens, or infrastructure identifiers.

Optional diagnostic reference identifiers are not part of FS-022.

## Accessibility behavior

- `html[lang]` is `de`.
- Each field error has a stable ID, the input sets `aria-invalid="true"`, and the input references the message through `aria-describedby` while the error is active.
- Newly presented blocking/urgent failures use one appropriate alert announcement container per update; each child problem is not redundantly announced as a separate alert.
- Non-blocking warnings use a labelled warning/status list and polite semantics, not `role="alert"` and not color alone.
- Recovery buttons/links are native keyboard-operable controls with visible focus and a label that makes the action/context clear.
- Focus moves to the first invalid field after an attempted submit. Background refreshes do not repeatedly steal focus.
- Text and controls remain readable and operable at 200% text zoom, 320 CSS pixels, and with long customer terms/record names/messages.
- Date entry accepts typing and paste without a caret-moving mask; its format instruction and error are programmatically available.
- Human-readable dates in accessible names, descriptions, live regions, and error text follow `DD.MM.YYYY` too.

## Accountless privacy boundary

- The lecturer secret fragment is removed before terminology or domain requests begin and never appears in display text or logs.
- Public validation projection uses only allowlisted categories, public occurrence/course context, and validated safe supporting values.
- Existing `findingRef`, `category`, `message`, and `affectedSessionRefs` response fields remain; no internal finding object or arbitrary service message is exposed.
- A missing safe fact produces restrained review guidance, not disclosure of the internal value.

## Regression contract

FS-022 changes presentation only. Tests must demonstrate no change to:

- validation/business outcomes and warning severity;
- successful, failed, stale, and partial-save semantics;
- authorization and accountless privacy;
- API/status/schema behavior other than the additive terminology read endpoint;
- ISO transport/storage/order/URL/log/export behavior;
- existing 24-hour time, duration, and timezone rules;
- stored course, lecturer, cohort, room, and user-entered names.
