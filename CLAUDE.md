# CLAUDE.md

## Projecte
Pipeline ML reproduïble per classificar subtipus CMS de càncer colorectal (TCGA-COAD).
TFG de bioinformàtica — l'objectiu és benchmark de models amb reproducibilitat completa.

## Mode de treball
- Claude actua com a editor de codi: llegeix, escriu i modifica fitxers.
- NO executa comandes (terminal, git, pip, tests, scripts).
- Per validar canvis, Claude indica com fer-ho manualment.

## Idioma
- Documentació i comunicació: català
- Codi (funcions, variables, docstrings, comments): anglès

## Tech stack
- Python 3.10+
- Conda (environment.yml)
- MkDocs per documentació (GitHub Pages)

## Convencions de codi
- Type hints obligatoris
- Funcions petites i modulars
- Noms descriptius (no abreviacions)
- Preferir logging sobre print (si existeix al projecte)
- Codi clar > codi intel·ligent

## Estructura del projecte
- `scripts/` — punts d'entrada executables (un per etapa del pipeline)
  - `download.py` — descarrega dades GDC
  - `preprocess.py` — filtra gens sorollosos, normalitza
  - `train.py` — entrena 3 models de classificació CMS
  - `evaluate.py` — mètriques, gràfics comparatius, benchmark
- `src/` — mòduls reutilitzables (paquet Python importable)
  - `gdc_utils.py` — utilitats GDC (download, setup, detecció plataforma)
  - `preprocessing.py` — funcions de neteja i filtratge
  - `models.py` — definició i entrenament de models
  - `evaluation.py` — mètriques, plots, interpretació
- `notebooks/` — exploració interactiva (importen des de `src/`)
  - `data_exploration.ipynb` — EDA de les dades RNA-seq
  - `model_comparison.ipynb` — comparació visual de resultats
- `docs/` — documentació tècnica (MkDocs → GitHub Pages)
- `data/`
  - `metadata/` — manifests GDC (al repo)
  - `raw/` — dades descarregades (.gitignore)
  - `processed/` — dades netes (.gitignore)
- `tools/` — binaris externs, gdc-client (.gitignore)

## Com executar
- Entorn: `conda env create -f environment.yml && pip install -e .`
- Docs: `mkdocs serve` (local) o push a main (GitHub Actions deploya)
- Pipeline:
  1. `python scripts/download.py`
  2. `python scripts/preprocess.py`
  3. `python scripts/train.py`
  4. `python scripts/evaluate.py`

## Git
- Claude NO fa commits, push ni cap operació git directament.
- Quan calgui fer commit, Claude indica les comandes exactes a executar.
- Commits freqüents i atòmics (cada pocs canvis).
- Quan s'hagi de fer un commit, demanar primer git status i en base a la sortida de la comanda fer el commit.
- Branques: `main` (principal), `feat/etapa{N}-*` (per etapa del TFG).
