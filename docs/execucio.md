# Execució

Aquesta pàgina descriu com preparar l’entorn Conda i executar el projecte. El pipeline està pensat per executar-se des de l’arrel del repositori i es divideix en quatre scripts principals: descàrrega, preprocessament, entrenament i avaluació.

## Requisits previs

Abans de començar cal tenir instal·lat:

- Git.
- Conda, mitjançant Anaconda o Miniconda.
- Connexió a internet per descarregar els fitxers del GDC.
- Espai suficient en disc per guardar les dades RNA-seq descarregades.

El repositori no inclou les dades grans. Les dades es reprodueixen a partir dels manifests guardats a `data/metadata/`.

## Clonar el repositori

```bash
git clone https://github.com/martiriverogarcia/tcga-coad-cms-ml-pipeline.git
cd tcga-coad-cms-ml-pipeline
```

## Instal·lació amb Conda

L’entorn del projecte es crea amb Conda a partir del fitxer `environment.yml`.

### Linux, macOS o Windows amb Anaconda Prompt

```bash
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .
```

La instal·lació editable (`pip install -e .`) permet importar els mòduls de `src/` des dels scripts i notebooks sense reinstal·lar el paquet cada vegada que es modifica el codi.

## Verificar la instal·lació

Es pot comprovar que les dependències principals s’han instal·lat correctament amb la comanda següent:

```bash
python -c "import numpy, pandas, sklearn, matplotlib; print('Imports correctes')"
```

També és recomanable comprovar que els scripts són accessibles des de l’arrel del projecte:

```bash
python scripts/preprocess.py --help
python scripts/train.py --help
python scripts/evaluate.py --help
```

## Execució completa del pipeline

L’execució completa segueix aquest ordre:

```bash
python scripts/download.py
python scripts/preprocess.py
python scripts/train.py
python scripts/evaluate.py
```

Cada script genera els fitxers necessaris per a l’etapa següent. Per tant, no es recomana executar `train.py` abans de `preprocess.py`, ni `evaluate.py` abans de `train.py`.

## Execució per etapes

| Etapa | Comanda | Sortida esperada |
|---|---|---|
| Descàrrega | `python scripts/download.py` | Fitxers RNA-seq a `data/raw/gdc/` |
| Preprocessament | `python scripts/preprocess.py` | Fitxers processats a `data/processed/` |
| Entrenament | `python scripts/train.py` | Models `.joblib` a `data/models/` |
| Avaluació | `python scripts/evaluate.py` | Informe JSON a `results/` i figures a `figures/` |

## Descàrrega de dades

```bash
python scripts/download.py
```

Aquest script llegeix el manifest del GDC guardat a `data/metadata/`, instal·la l’eina `gdc-client` si cal i descarrega els fitxers RNA-seq a `data/raw/gdc/`.

Opcions útils:

```bash
python scripts/download.py --dry-run
python scripts/download.py --manifest data/metadata/gdc_manifest.2026-03-09.191818.txt
python scripts/download.py --out data/raw/gdc
```

## Preprocessament

```bash
python scripts/preprocess.py
```

Aquesta etapa construeix la matriu d’expressió, filtra les mostres i gens, associa les etiquetes CMS, separa train/test i aplica la transformació logarítmica.

Opcions útils:

```bash
python scripts/preprocess.py --dry-run
python scripts/preprocess.py --seed 42 --test-size 0.2
```

## Entrenament

```bash
python scripts/train.py
```

Aquesta etapa entrena els models Logistic Regression, Random Forest i SVM lineal amb les mateixes dades d’entrenament.

Opcions útils:

```bash
python scripts/train.py --dry-run
python scripts/train.py --model logistic_regression
python scripts/train.py --model random_forest
python scripts/train.py --model svm
python scripts/train.py --processed-dir data/processed --output-dir data/models
```

## Avaluació

```bash
python scripts/evaluate.py
```

Aquesta etapa carrega els models entrenats i els avalua sobre el conjunt de test. Genera mètriques, matrius de confusió i gràfics comparatius.

Opcions útils:

```bash
python scripts/evaluate.py --dry-run
python scripts/evaluate.py \
  --processed-dir data/processed \
  --models-dir data/models \
  --output-dir results \
  --figures-dir figures
```

## Execució dels notebooks

Els notebooks complementen l’execució del pipeline i permeten revisar l’exploració de dades, l’anàlisi dels models i els resultats finals.

```bash
jupyter lab notebooks/data_exploration.ipynb
```

```bash
jupyter lab notebooks/model_analysis.ipynb
```

```bash
jupyter lab notebooks/results_exploration.ipynb
```

L’ordre recomanat és executar primer `data_exploration.ipynb` després del preprocessament, `model_analysis.ipynb` després de l’entrenament i `results_exploration.ipynb` després de l’avaluació.

## Errors comuns

| Problema | Possible causa | Solució |
|---|---|---|
| `ModuleNotFoundError: src` | El paquet local no està instal·lat | Executar `pip install -e .` des de l’arrel del repositori |
| No existeix `data/raw/gdc/` | Encara no s’han descarregat les dades | Executar `python scripts/download.py` |
| No existeix `data/processed/` | Encara no s’ha fet el preprocessament | Executar `python scripts/preprocess.py` |
| No existeix `data/models/` | Encara no s’han entrenat els models | Executar `python scripts/train.py` |
| `evaluate.py` no troba models | Ruta de models incorrecta o models no generats | Revisar `--models-dir` o tornar a entrenar |
| Canvien les mètriques | Seed, dades o versions diferents | Revisar `environment.yml`, `random_seed` i manifests |