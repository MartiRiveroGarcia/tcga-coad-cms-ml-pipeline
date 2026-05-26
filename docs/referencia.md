# Reproductibilitat

Aquesta pàgina descriu com es controla la reproductibilitat del projecte. L’objectiu és que una altra persona pugui executar el pipeline amb les mateixes dades, el mateix codi i el mateix entorn per obtenir els mateixos resultats.

## Elements de reproductibilitat

La reproductibilitat del projecte es controla amb cinc elements principals:

| Element | Com es controla |
|---|---|
| Entorn | Dependències definides a `environment.yml` |
| Dades | Manifests, sample sheets i etiquetes CMS guardats a `data/metadata/` |
| Codi | Scripts executables a `scripts/` i mòduls reutilitzables a `src/` |
| Aleatorietat | Seed fixa en el split i en els models que incorporen aleatorietat |
| Sortides | Fitxers processats, models, resultats i figures generats pel pipeline |

## Entorn d’execució

L’entorn del projecte es crea amb Conda a partir del fitxer `environment.yml`.

```bash
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .
```

La instal·lació editable permet que els scripts i notebooks importin correctament els mòduls locals de `src/`.

Es pot comprovar la instal·lació mínima amb:

```bash
python -c "import numpy, pandas, sklearn, matplotlib; print('Imports correctes')"
```

## Dades i artefactes generats

Les dades grans i els artefactes generats no es guarden al repositori. Es poden tornar a crear executant les etapes corresponents del pipeline.

```bash
python scripts/download.py
python scripts/preprocess.py
python scripts/train.py
python scripts/evaluate.py
```

El manifest del GDC i les metadades guardades a `data/metadata/` permeten reconstruir el conjunt de dades utilitzat pel projecte. Els fitxers processats, els models i els resultats es generen sempre a partir d’aquestes entrades.

## Control de l’aleatorietat

El pipeline fixa una seed per reduir la variabilitat entre execucions.

| Procés | Control aplicat |
|---|---|
| Separació train/test | `random_seed=42` |
| Models amb aleatorietat | `random_state=42` quan aplica |
| Reexecució del pipeline | Mateix codi, mateixes dades, mateix entorn i mateixa seed |

Si canvien les versions de les llibreries, les dades descarregades, el codi o la seed, els resultats poden variar.

## Fitxers no versionats

El repositori evita incloure dades grans i sortides regenerables. Això manté el projecte més lleuger i permet reconstruir els resultats a partir dels scripts.

| Ruta | Motiu | Com es reprodueix |
|---|---|---|
| `data/raw/gdc/` | Fitxers RNA-seq descarregats del GDC | `python scripts/download.py` |
| `data/processed/` | Dades derivades del preprocessament | `python scripts/preprocess.py` |
| `data/models/` | Models entrenats | `python scripts/train.py` |
| `results/` | Informes i mètriques d’avaluació | `python scripts/evaluate.py` |
| `figures/` | Figures i gràfics generats | `python scripts/evaluate.py` o notebooks |
| `tools/gdc-client/` | Eina externa descarregable | `scripts/download.py` la prepara si cal |

Els fitxers de `data/metadata/` sí que es versionen perquè són necessaris per reconstruir el dataset.

## Execució reproduïble del pipeline

Per reproduir el projecte des de zero, cal executar els passos següents des de l’arrel del repositori:

```bash
# 1. Crear i activar l'entorn
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
pip install -e .

# 2. Descarregar les dades
python scripts/download.py

# 3. Preprocessar les dades
python scripts/preprocess.py

# 4. Entrenar els models
python scripts/train.py

# 5. Avaluar els models
python scripts/evaluate.py
```

Després de l’execució, les sortides principals són:

```text
data/processed/
data/models/
results/evaluation_report.json
figures/
```

## Resultats esperats

L’execució completa ha de generar les matrius processades, els models entrenats i l’informe d’avaluació.

El fitxer principal de resultats és:

```text
results/evaluation_report.json
```

Aquest fitxer conté les mètriques globals i per classe de cada model. Els valors esperats poden variar si canvien les dades, les versions de les dependències, la seed o el codi del projecte.

## Limitacions de reproductibilitat

La reproductibilitat depèn de factors que poden canviar fora del repositori:

- Disponibilitat dels fitxers al GDC.
- Canvis en versions futures de llibreries.
- Diferències entre sistemes operatius.
- Canvis manuals en manifests, metadades o etiquetes.
- Modificacions del codi del pipeline.

Per reduir aquests riscos, el projecte versiona els manifests i metadades necessaris, fixa la seed i defineix l’entorn amb `environment.yml`.

## Resum

El projecte és reproduïble perquè separa clarament les dades d’entrada, el codi executable, l’entorn de dependències i les sortides generades. Les dades grans i els resultats no es versionen, però es poden reconstruir executant el pipeline complet amb les metadades i manifests inclosos al repositori.