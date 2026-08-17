# FS-020 Public Gateway Boundary Delta

This contract extends the established FS-015 exact-path public boundary. All unspecified FS-015 rules continue to apply.

## Newly allowed operation

| Method | Exact path | Authorization | Request scope |
|---|---|---|---|
| `GET` | `/api/public/lecturer-review/calendar` | `Authorization: Bearer <opaque FS-015 secret>` | None; no query, body, cookie, lecturer, revision, filter, dates, selection, or filename |

The public allowlist contains the existing FS-015 review/feedback operations, public terminology read, and this exact new operation only. Route tests must intentionally update the expected lecturer-review operation count from two to three.

## Gateway invariants

- The fragment secret is removed from browser-visible URL/history before protected requests and remains in memory.
- The new route is reachable only through its exact method/path. Trailing or prefixed variants, alternate verbs, encoded separators, case changes, extra path segments, and near-miss public paths fail closed before protected logic.
- Authentication uses the header only. Cookies/credentials are omitted and do not authorize the request.
- Query parameters and request bodies are rejected or ignored only by failing closed; they never influence export scope.
- The gateway and application preserve `Cache-Control: no-store`, `Pragma: no-cache`, `Referrer-Policy: no-referrer`, and `X-Robots-Tag: noindex,nofollow`; successful calendar delivery also uses `X-Content-Type-Options: nosniff`.
- Error responses are JSON safe errors. A failed response never uses `text/calendar`, attachment disposition, event count, filename, or partial calendar bytes.
- Response compression/access logging, if present at the gateway, must not record bearer values, calendar bodies, or personalized filenames.

## Authorization timing

Opening the notice does not call the route. Confirmation creates a new request and the application re-resolves the bearer, locks/re-reads the relevant semester state, and re-evaluates link and revision access. A state change after page load or notice display wins.

## Non-integration boundary

The route returns a static HTTP attachment only. It does not call Outlook, Microsoft Graph, Exchange, another calendar provider, email delivery, a subscription endpoint, or a background synchronization service.
