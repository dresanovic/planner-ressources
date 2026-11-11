# Resource Planner

The application uses a FastAPI backend and a React/TypeScript client. See
[backend setup](backend/README.md) and [container deployment](infrastructure/docker/README.md).

For Codex integration, the [local MCP bridge](mcp-server/README.md) runs beside
Codex and calls this application's HTTP API to retrieve cohorts and save draft
plan sessions. Its dependencies are separate from the application server.

New teaching planning runs require `config/optimization/policy.json`. For a new
installation copy `config/optimization/policy.example.json`; preserve existing
operator budgets. The normal path is independent of the working directory.
`TEACHING_OPTIMIZATION_POLICY_FILE` overrides the path. Containers mount the
policy directory so atomic replacement is visible. A missing or invalid policy
blocks new teaching runs without blocking unrelated health/startup.

I-011 provides three concrete strategies: `standard`, `cohort` and `lecturer`.
I-012 adds `standard_optimized` (“Standard optimiert”), a separate Standard-derived
search that reuses the same legality helpers and spreads teaching across feasible
weeks of each course's planning period. Standard's search remains unchanged.
See [activation and verification](specs/I-012-standard-optimized/quickstart.md).
Set `activeAlgorithm` in the operator policy; its omission retains Standard.
The planner sees the captured algorithm without a selector. Cohort and Lecturer
use bounded constructive search and repair; Lecturer uses fixed code-ordered,
nontransferable shares. Heuristic results require explicit acceptance, including
full-coverage results. Exam generation keeps its existing algorithm.

See the [comparison measurements](specs/I-011-policy-teaching-strategies/verification/performance-comparison.md)
and [validation evidence](specs/I-011-policy-teaching-strategies/validation.md).
The tests use isolated snapshots and disposable databases. Container mount,
screen-reader speech and true 200% zoom acceptance remain unverified here.
