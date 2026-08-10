# Contract: Effective UI Terminology

## Purpose

Provide the one startup-validated effective terminology catalog to the planner and accountless lecturer clients before either interface renders. This endpoint contains presentation configuration only and does not alter existing business API, storage, or authorization contracts.

## Request

```text
GET /api/public/ui-terminology
Accept: application/json
```

- Public. Production uses the same origin; local development resolves the fixed
  path through the existing `VITE_API_BASE_URL` convention.
- Requires no planner identity, lecturer bearer value, cookie, query token, or URL fragment.
- The bootstrap client sends no `Authorization` header and uses `credentials: "omit"`.
- On the accountless route, the lecturer secret fragment is removed from the address before this request is started.

## Successful response

```text
200 OK
Content-Type: application/json
Cache-Control: no-store
```

```json
{
  "labels": {
    "course.singular": "Lehrveranstaltung",
    "course.plural": "Lehrveranstaltungen",
    "course.navigation": "Lehrveranstaltungen",
    "course.heading": "Lehrveranstaltungen",
    "course.fieldLabel": "Lehrveranstaltung",
    "course.tableHeading": "Lehrveranstaltung",
    "lecturer.singular": "Lehrende Person",
    "lecturer.plural": "Lehrende",
    "lecturer.navigation": "Lehrende",
    "lecturer.heading": "Lehrende",
    "lecturer.fieldLabel": "Lehrende Person",
    "lecturer.tableHeading": "Lehrende Person",
    "cohort.singular": "Kohorte",
    "cohort.plural": "Kohorten",
    "cohort.navigation": "Kohorten",
    "cohort.heading": "Kohorten",
    "cohort.fieldLabel": "Kohorte",
    "cohort.tableHeading": "Kohorte",
    "room.singular": "Raum",
    "room.plural": "Räume",
    "room.navigation": "Räume",
    "room.heading": "Räume",
    "room.fieldLabel": "Raum",
    "room.tableHeading": "Raum",
    "schedule.navigation": "Planung",
    "schedule.heading": "Terminplanung",
    "academicData.navigation": "Stammdaten",
    "academicData.heading": "Akademische Stammdaten"
  }
}
```

The values above establish the planned shipped German defaults. Implementation may correct a German default during product review, but any key-set change requires the specification and schema to be updated first.

## Response invariants

- `labels` contains every property enumerated by [terminology-overrides.schema.json](terminology-overrides.schema.json), including entries not overridden by the customer.
- `labels` contains no additional property and every value satisfies the schema's label constraints.
- Response ordering has no semantic meaning.
- Values are plain text. The client never interprets HTML, Markdown, placeholders, or interpolation tokens.
- No raw file path, customer override source, secret, diagnostic, user record, or language metadata is returned.
- A catalog is immutable for one running service process.
- The endpoint reads the immutable application-state catalog and performs no database query.
- One browser bootstrap attempt issues one request. Normal application interaction issues no additional terminology request; the explicit bootstrap Retry issues exactly one new request.

## Startup and failure behavior

- The endpoint cannot return a partially merged or invalid catalog. Default validation and configured override validation finish before the FastAPI lifespan yields.
- If `CUSTOMER_TERMINOLOGY_FILE` is unset, the response contains the shipped defaults.
- If the variable is set and the file is missing, unreadable, malformed, has duplicate/unknown properties, or contains an invalid value, service startup fails and the application is not marked ready.
- Operator diagnostics name the configuration file and invalid key/category when safe; they do not log customer values.
- If a running client cannot fetch or validate the response, neither application surface imports/renders. It displays fixed German bootstrap copy explaining that interface terminology could not be loaded and a Retry control that repeats only this safe GET.
- The bootstrap copy must not include raw parser/network errors, raw catalog keys, URL fragments, or authorization data.

## Client validation

The client accepts only an object with one `labels` object containing the exact expected key set and valid string values. Missing, additional, blank, non-string, control-character, or malformed content is a bootstrap failure. It does not merge locally with a second default map and never returns a key as display fallback.

Automated contract tests compare the property set in `terminology-overrides.schema.json`, the backend default JSON, and the client's expected-key set. Direct component tests initialize deterministic defaults through the shared Vitest setup; override/bootstrap tests isolate module state while production initialization remains set once.

## Security and caching

- Endpoint output is non-sensitive deployment presentation data.
- `Cache-Control: no-store` prevents an old customer catalog being reused after a restart.
- The endpoint remains accessible on both normal planner and `/lecturer-review/` entry paths without receiving the lecturer secret.
- Existing middleware must classify the operation as public or otherwise ensure no lecturer credential is necessary.

## Compatibility

This is one additive public read endpoint for FS-022. All existing domain endpoints, request/response fields, status codes, ISO date fields, and accountless lecturer response shape remain unchanged.
