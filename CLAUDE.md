# CLAUDE.md — Project instructions

## Project goal
Build a reproducible ML pipeline + didactic documentation (MkDocs/GitHub Pages) for TCGA-COAD CMS classification.

## Working style (important)
- Work step-by-step. Prefer small, incremental changes.
- Always propose a short plan before editing files.
- Prefer "Ask before edits" for code/document changes.
- Keep diffs small; one task per commit.

## Repository & branches
- main: source of truth (code + docs). Keep it stable.
- gh-pages: generated website output. Never edit manually.
- For new work: create a branch `docs/...` or `feat/...`.

## Reproducibility rules
- Use `environment.yml` as the primary environment definition.
- Deterministic runs: fixed seed + saved config per run.
- Do NOT commit large datasets; only manifests/metadata in `data/manifests/`.

## Docs rules
- Docs live in `docs/` and `mkdocs.yml`.
- Changes to docs should keep MkDocs build working.
- The GitHub Action deploys docs to gh-pages after pushes to main.

## Before you change anything
- Identify files affected.
- Define a clear “done” check (e.g., mkdocs builds, imports work).
- After changes: run the minimal verification command(s) and report results.

## Source of truth (read these first)
- docs/project.md (goal, scope, key decisions)
- docs/requirements.md (functional/non-functional requirements + acceptance)
- docs/pipeline.md (pipeline description)
- docs/data.md (data manifest approach)
- docs/KPI_CHECKLIST.md (KPIs to check off)
- docs/reproducibility.md (environment + reproducibility instructions)

## Schedule & current stage (IMPORTANT)
This section defines how to sequence work (project convention) and must be followed.

### Stage plan (from Avantprojecte dates + project convention titles)
| Stage | Start | End | Title (Stage = Task) |
|------:|:------|:----|:---------------------|
| 1 | 2026-02-19 | 2026-02-24 | Task A — Càrrega i gestió de dades d’expressió gènica |
| 2 | 2026-02-25 | 2026-03-10 | Task B — Preprocessament de dades |
| 3 | 2026-03-11 | 2026-03-20 | Task C — Reducció de dimensionalitat i exploració de dades |
| 4 | 2026-03-21 | 2026-04-07 | Task D — Entrenament de models d’aprenentatge automàtic |
| 5 | 2026-04-08 | 2026-05-06 | Task E — Optimització i validació dels models |
| 6 | 2026-05-07 | 2026-05-18 | Task F — Avaluació del rendiment dels models |
| 7 | 2026-05-19 | 2026-05-27 | Task G — Generació de visualitzacions i interpretació de resultats |

### Current status
- ACTUAL_START_DATE: 2026-03-09
- CURRENT_STAGE: 1
- NOTE: We are behind the original plan.

### Generic rule (always follow)
- Work strictly in stage order: 1 → 2 → 3 → 4 → 5 → 6 → 7.
- Do NOT propose or implement work from a later stage unless:
  1) the current stage has a written Definition of Done (DoD), AND
  2) the DoD is fully completed and verified with checks, AND
  3) changes are committed and pushed.

### How to work with me (every step)
1) Propose a plan (max 5 bullets) aligned with CURRENT_STAGE
2) Keep changes small (<30 minutes)
3) Define "done" checks (commands/observable outputs)
4) Use a feature branch (docs/* or feat/*)
5) One task per commit
