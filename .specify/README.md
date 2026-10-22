# Spec Kit maintenance

This project uses Spec Kit CLI v1.2.2, the Codex integration, and ten project-local
skills in `.agents/skills/speckit-*/`. Keep the CLI installed through `uv`.
Global copies of these ten skills are redundant; independent global skills are
unaffected. Codex detects skill changes automatically; restart Codex only if the
skill selector still shows stale duplicates. See the official
[skill discovery guidance](https://learn.chatgpt.com/docs/build-skills).

## Ownership and customization

- `.specify/memory/constitution.md` owns permanent engineering rules: spec-first
  work, test-first delivery wherever practical, measurable Given/When/Then
  acceptance, KISS, incremental slices, FastAPI, React/TypeScript/Vite,
  `backend/app/`, `backend/tests/`, `client/`, and verification before commit.
  The approved clean, verified solo `main`/`master` exception remains in principle V.
- The ten skills, six PowerShell scripts, all five base templates, and integration
  manifests match the clean v1.2.2 reference. Do not customize those managed files.
- `templates/overrides/plan-template.md` retains the mandatory three-part
  Simplicity Check and concrete Verification Plan, using the actual repository layout.
- `templates/overrides/spec-template.md` adds explicit test requirements to the
  official scaffold and allows the constitution's working-branch exception.
- Tasks and checklists use the clean official base templates. The old checklist
  override obscured v1.2.2 reviewer ownership and checkbox semantics and was removed.
  Generated artifacts must replace sample paths/tasks with the selected plan.

The official tasks skill and base template say tests are optional unless the
specification explicitly requests them. The specification override makes that
request, and the constitution requires test-first work and explicit verification
tasks. Never treat the generic optional wording as a waiver. Existing features
also remain governed by the constitution; this migration does not rewrite them.

## Verified v1.2.2 resolution

The installed v1.2.2 implementation verifies this precedence:

1. `templates/overrides/<name>.md` (whole-file replacement).
2. Installed presets (enabled registry entries, priority then identifier).
3. Extension templates (priority then identifier).
4. `templates/<name>.md` (core fallback).

Sources: `.specify/scripts/powershell/common.ps1`, functions `Resolve-Template`
and `Resolve-TemplateContent`, and the installed `specify_cli/presets/_resolver.py`.
The standalone resolver emits JSON with `TEMPLATE_CONTENT`. Overrides cannot be
small append-only fragments; preset composition supports that use case but is
unnecessary for these two scaffolds and requires Python/PyYAML at runtime.

```powershell
specify preset resolve plan-template
pwsh -NoProfile -File .specify/scripts/powershell/resolve-template.ps1 spec-template -Json
specify integration status
```

Feature directories and Git branch names are independent in v1.2.2. The current
feature is selected by `SPECIFY_FEATURE_DIRECTORY` or the ignored
`.specify/feature.json`, rather than inferred from the current Git branch. To
inspect an existing feature without changing the pointer:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/<existing-feature>'
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
Remove-Item Env:SPECIFY_FEATURE_DIRECTORY
```

## Workflow exception

`workflows/speckit/workflow.yml` uses the official v1.0.1 workflow bundled with
Spec Kit v1.2.2, retaining the pre-existing `scope` input (`full`, `backend-only`,
`frontend-only`). This input remains descriptive metadata; it does not filter
steps. It is the only workflow source difference from the reference. v1.2.2
workflow overlays support step insert/replace/remove operations, not adding
top-level inputs (`specify_cli/workflows/overlay/schema.py`), so a small direct
workflow customization is retained. Registry installation time and project init
options remain project-specific. Review this exception when upgrading.

## Future upgrades

Back up `.specify`, project-local skills, and any global duplicates before an
upgrade. Compare against a clean installation of the target version. Preserve
the constitution and the two overrides, then verify managed hashes, both CLI and
PowerShell resolution, workflow loading, and an isolated smoke workflow before
removing any redundant skills. Keep migration backups out of commits.
