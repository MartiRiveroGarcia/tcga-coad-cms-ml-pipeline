# TFG – Pipeline reproduïble per a classificació CMS (TCGA-COAD)

Pipeline de machine learning per classificar subtipus moleculars (CMS) de càncer colorectal
a partir de dades RNA-seq del projecte TCGA-COAD. Compara 3 models amb reproducibilitat completa.

## Quickstart

```bash
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .

python scripts/download.py      # Descarrega dades GDC
python scripts/preprocess.py    # Neteja i normalitza
python scripts/train.py         # Entrena els 3 models
python scripts/evaluate.py      # Genera mètriques i gràfics
```

## Estructura

```
scripts/          Punts d'entrada del pipeline (un per etapa)
src/              Mòduls reutilitzables (paquet Python)
notebooks/        Exploració interactiva i validació visual
docs/             Documentació tècnica (MkDocs)
data/metadata/    Manifests GDC (al repo)
data/raw/         Dades descarregades (.gitignore)
data/processed/   Dades netes (.gitignore)
tools/            Binaris externs (.gitignore)
```

## Documentació (GitHub Pages)

Web: https://martiriverogarcia.github.io/tcga-coad-cms-ml-pipeline/

- Edita fitxers a `docs/` o `mkdocs.yml`
- Fes `git commit` + `git push` a `main`
- GitHub Actions desplega automàticament a `gh-pages`

