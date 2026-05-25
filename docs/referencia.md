# Reproductibilitat i referència

Aquesta pàgina agrupa els criteris de reproductibilitat, els requisits del projecte, els criteris d’acceptació i un glossari breu. Serveix com a pàgina de consulta final.

## Reproductibilitat

Un projecte és reproduïble quan una altra persona pot obtenir els mateixos resultats utilitzant les mateixes dades, el mateix codi i el mateix entorn.

En aquest projecte, la reproductibilitat es controla amb cinc elements:

| Element | Com es controla |
|---|---|
| Entorn | Dependències definides a `environment.yml` |
| Dades | Manifests i metadades versionats a `data/metadata/` |
| Codi | Repositori Git amb scripts i mòduls separats |
| Aleatorietat | Seed fixa en split i models |
| Artefactes | Logs, models, mètriques i figures regenerables |

## Entorn

L’entorn es crea amb:

```bash
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .
```

La verificació mínima és:

```bash
python -c "import numpy, pandas, sklearn, matplotlib; print('Ok')"
```

## Dades regenerables

Les dades grans no es guarden al repositori. Es regeneren amb:

```bash
python scripts/download.py
python scripts/preprocess.py
```

El manifest del GDC permet descarregar els mateixos fitxers. Els fitxers processats es generen sempre a partir de les mateixes dades raw i de les mateixes metadades.

## Aleatorietat

El pipeline fixa la seed per obtenir particions i resultats consistents.

| Procés | Control |
|---|---|
| Split train/test | `random_seed=42` |
| Models amb aleatorietat | `random_state=42` quan aplica |
| Reexecució | Mateix codi, mateixes dades i mateixa seed |

Si canvien les versions de llibreries, les dades o la seed, els resultats poden variar.

## Què no es versiona

| Ruta | Motiu | Com es reprodueix |
|---|---|---|
| `data/raw/` | Fitxers grans descarregats del GDC | `python scripts/download.py` |
| `data/processed/` | Derivat de les dades raw | `python scripts/preprocess.py` |
| `data/models/` | Models regenerables | `python scripts/train.py` |
| `results/` | Resultats regenerables | `python scripts/evaluate.py` |
| `tools/gdc-client/` | Eina externa descarregable | `scripts/download.py` la prepara si cal |

## Verificació de la reproductibilitat

Per comprovar la reproductibilitat del projecte:

```bash
# 1. Crear entorn
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .

# 2. Executar pipeline complet
python scripts/download.py
python scripts/preprocess.py
python scripts/train.py
python scripts/evaluate.py

# 3. Revisar resultats
cat results/evaluation_report.json
```

La sortida esperada és la generació de les mateixes matrius processades, els mateixos models i les mateixes mètriques, sempre que no canviïn les dades, el codi, les versions o la seed.

## Requisits funcionals

| Codi | Requisit |
|---|---|
| RF1 | El sistema ha de descarregar les dades RNA-seq a partir d’un manifest GDC |
| RF2 | El sistema ha de construir una matriu d’expressió gènica a partir dels fitxers descarregats |
| RF3 | El sistema ha d’unir les mostres amb les etiquetes CMS disponibles |
| RF4 | El sistema ha de separar les dades en train i test de manera estratificada |
| RF5 | El sistema ha d’entrenar Logistic Regression, Random Forest i SVM sota el mateix protocol |
| RF6 | El sistema ha d’avaluar els models amb mètriques comparables |
| RF7 | El sistema ha de generar figures d’avaluació i un informe de resultats |

## Requisits no funcionals

| Codi | Requisit |
|---|---|
| RNF1 | El projecte ha de ser reproduïble amb instruccions d’execució documentades |
| RNF2 | Les dades grans no s’han d’incloure al repositori |
| RNF3 | Les etapes han d’estar separades en scripts executables |
| RNF4 | La lògica reutilitzable ha d’estar encapsulada en mòduls de `src/` |
| RNF5 | Els resultats han de ser traçables mitjançant logs i fitxers de sortida |
| RNF6 | La documentació tècnica ha d’explicar el funcionament del pipeline i les decisions principals |

## Criteris d’acceptació

| Criteri | Verificació |
|---|---|
| Es pot crear l’entorn | `conda env create -f environment.yml` finalitza correctament |
| Es poden descarregar les dades | `python scripts/download.py` genera `data/raw/gdc/` |
| Es poden processar les dades | `python scripts/preprocess.py` genera `data/processed/` |
| Es poden entrenar els models | `python scripts/train.py` genera fitxers `.joblib` |
| Es poden avaluar els models | `python scripts/evaluate.py` genera `evaluation_report.json` |
| La documentació explica el pipeline | La pàgina “Dades i pipeline” inclou diagrames C4 i flux de fitxers |
| Els resultats són consultables | La pàgina “Experiments i resultats” resumeix mètriques i figures |

## Glossari breu

| Terme | Definició |
|---|---|
| CMS | Consensus Molecular Subtypes, classificació molecular del càncer colorectal en quatre subtipus principals |
| TCGA-COAD | Cohort de càncer de còlon del projecte The Cancer Genome Atlas |
| RNA-seq | Tècnica de seqüenciació per quantificar expressió gènica |
| STAR-Counts | Fitxers de comptatge d’expressió generats amb el workflow STAR |
| GDC | Genomic Data Commons, portal de dades genòmiques del National Cancer Institute |
| Synapse | Plataforma externa utilitzada per compartir dades i recursos científics |
| Pipeline | Seqüència automatitzada de passos de processament i anàlisi |
| Preprocessament | Transformació de dades raw en dades preparades per als models |
| Train/test split | Separació de dades en conjunt d’entrenament i conjunt de test |
| Data leakage | Ús indirecte d’informació del test durant l’entrenament o preprocessament |
| Logistic Regression | Model lineal de classificació |
| Random Forest | Conjunt d’arbres de decisió entrenats de manera agregada |
| SVM | Support Vector Machine, model que separa classes maximitzant el marge |
| Accuracy | Proporció total de prediccions correctes |
| Precision | Proporció de prediccions positives que són correctes |
| Recall | Proporció de mostres reals d’una classe que el model detecta |
| F1-score | Mitjana harmònica entre precision i recall |
| F1 macro | Mitjana del F1 de totes les classes amb el mateix pes |
| Matriu de confusió | Taula que mostra encerts i errors per classe real i classe predita |
| Seed | Llavor aleatòria utilitzada per obtenir resultats deterministes |
| `.joblib` | Format de serialització utilitzat per guardar models entrenats |

## Referències tècniques

- C4 Model: <https://c4model.com/>
- The Turing Way — Guide for Reproducible Research: <https://book.the-turing-way.org/reproducible-research/reproducible-research/>
- The Turing Way — Reproducible Environments: <https://book.the-turing-way.org/reproducible-research/renv/>
