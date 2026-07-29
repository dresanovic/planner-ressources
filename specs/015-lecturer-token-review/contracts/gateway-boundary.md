# FS-015 Trusted Gateway Boundary

This is the deployment contract for the authorization and client-address
boundaries clarified for FS-015. It does not define a new application account,
login, role, or identity system.

## Security ownership

The trusted gateway is the only public network path to the frontend and
FastAPI backend.

- The gateway applies the existing planner authorization before serving a
  planner page or forwarding a planner API operation.
- The gateway permits anonymous traffic only for the exact public review
  surface below.
- The backend listener is private or loopback-bound and cannot be reached
  directly from the public network.
- Hidden UI controls are not authorization. A blocked planner API request must
  be rejected by the gateway before it reaches the application.

The concrete planner identity mechanism belongs to the existing gateway
deployment and is outside FS-015. Release evidence must nevertheless prove
that authorized planners pass and anonymous requests fail.

## Anonymous allowlist

The gateway uses a default-deny rule and permits anonymous requests only for:

| Method | Exact path | Purpose |
|---|---|---|
| `GET` or `HEAD` | `/lecturer-review/` | Public review shell |
| `GET` or `HEAD` | required built asset paths | JavaScript, CSS, fonts, or images referenced by the public shell |
| `GET` | `/api/public/lecturer-review` | Complete minimum-scope protected view |
| `POST` | `/api/public/lecturer-review/feedback` | Append one valid feedback item |

The copied URL is
`{planner-window-origin}/lecturer-review/#/{secret}`. The fragment is never
part of a gateway or server request. The backend returns only the one-time raw
secret; the planner client constructs this URL.

The gateway must protect or refuse anonymous access to:

- `/` and every planner page entry;
- `/health`, API documentation, and the OpenAPI document;
- every `/api/...` path not listed above;
- planner link-management and retained-feedback paths;
- unlisted methods on public paths;
- additional subpaths under `/api/public/lecturer-review`;
- the direct backend host or port.

A gateway may normalize `/lecturer-review` to `/lecturer-review/`, but the
normalization must preserve the browser fragment and must not log or receive
the secret.

## Public frontend boundary

`client/src/main.tsx` branches on the exact pathname `/lecturer-review/` before
loading either application surface:

- the public branch dynamically imports only `LecturerReviewPage`;
- the planner branch dynamically imports the normal `App`;
- the public branch never renders planner navigation or requests planner APIs;
- the fragment is removed while preserving `/lecturer-review/`;
- public API URLs are fixed, relative, and same-origin in production;
- public fetches use `credentials: "omit"`;
- production `VITE_API_BASE_URL` must be empty/same-origin so the browser cannot
  bypass the gateway.

Built assets contain no schedule or planner data. If the gateway exposes a
shared asset directory, authorization continues to be enforced at page and API
boundaries.

## Public response policy

The public shell and every public API success or error response use:

```text
Cache-Control: no-store
Pragma: no-cache
Referrer-Policy: no-referrer
X-Robots-Tag: noindex, nofollow
```

The shell loads no third-party analytics or assets. Production access is HTTPS
only.

## Authoritative client address

The gateway:

1. removes inbound `Forwarded`, `X-Forwarded-For`, `X-Real-IP`, and related
   forwarding values supplied by the caller;
2. writes the authoritative client address into the forwarding information
   passed to Uvicorn; and
3. connects from a known gateway address or bounded gateway network.

Uvicorn proxy-header processing is enabled only for that known peer, using an
exact `--forwarded-allow-ips` value or equivalent `FORWARDED_ALLOW_IPS`
configuration. A wildcard value is prohibited.

Feature code reads only `request.client.host` after this server boundary. It
does not parse a forwarding header. The invalid-token limiter derives its
short-lived HMAC fingerprint from that normalized address using a protected
configuration secret containing at least 256 bits of random key material that
remains stable across application restarts. The limiter state is stored
atomically in the existing database and physically removed within the specified
retention bound.

## Local development

Localhost may connect directly to a single Uvicorn worker for development and
automated application tests. Direct localhost behavior is not evidence that
the production gateway contract passes.

Tests may inject distinct `request.client.host` values to prove limiter bucket
behavior. Proxy-header integration tests must distinguish trusted gateway peers
from untrusted peers and must never configure wildcard proxy trust.

## Release evidence ownership

Before gateway acceptance begins, the release record must identify:

- the deployment environment being tested;
- the gateway configuration or runbook under review;
- the gateway peer address or bounded CIDR trusted by Uvicorn;
- the person or team responsible for the gateway; and
- the person recording the release decision.

Gateway configuration remains outside the FS-015 application repository, but
missing deployment ownership or evidence blocks production release.

## Release acceptance

Release evidence must demonstrate all of the following against the deployed
gateway:

1. An authorized planner can reach the planner page and representative planner
   link-management/history operations.
2. An anonymous request reaches `/lecturer-review/` and the exact two public
   API operations.
3. Anonymous `/`, planner APIs, `/health`, API documentation, unlisted public
   methods/subpaths, and direct backend access are rejected.
4. The gateway overwrites forged forwarding headers.
5. Repeated requests from one real source cannot evade the 20-attempt boundary
   by varying forwarding headers.
6. Two real sources receive independent invalid-token limiter buckets.
7. Proxy trust is restricted to the recorded gateway peer/CIDR, and restarting
   the application does not reset an active unusable-link rejection period.
8. Production public calls are same-origin, HTTPS, and use no credentials.

Failure of any item blocks production release of FS-015.
