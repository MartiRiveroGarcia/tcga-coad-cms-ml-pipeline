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
