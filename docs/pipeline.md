# Dades i pipeline

Aquesta pàgina descriu l’origen de les dades, l’estructura del repositori i el funcionament intern del pipeline. També inclou els diagrames C4 que expliquen el sistema en diferents nivells de detall.

## Origen de les dades

El projecte utilitza dades d’expressió gènica RNA-seq de la cohort TCGA-COAD. Els fitxers provenen del Genomic Data Commons i es descarreguen mitjançant un manifest versionat dins de `data/metadata/`.

El pipeline no treballa amb fitxers FASTQ ni fa alineament de seqüències. Parteix de fitxers STAR-Counts ja quantificats, que contenen comptatges d’expressió gènica per mostra.

| Element | Valor |
|---|---|
| Cohort | TCGA-COAD |
| Tipus de dada | RNA-seq |
| Workflow | STAR-Counts |
| Tipus de mostra | Tumor primari |
| Accés | Dades públiques del GDC |
| Etiquetes | Subtipus CMS provinents de metadades externes |

## Què es versiona i què no?

El repositori només versiona fitxers petits o necessaris per reconstruir el projecte. Les dades grans i els artefactes regenerables queden exclosos del control de versions.

| Ruta | Contingut | Es versiona? | Motiu |
|---|---|---|---|
| `data/metadata/` | Manifests, sample sheets i etiquetes CMS | Sí | Permeten reconstruir el dataset |
| `data/raw/gdc/` | Fitxers RNA-seq descarregats | No | Són grans i es poden descarregar de nou |
| `data/processed/` | Matrius processades | No | Es generen amb `preprocess.py` |
| `data/models/` | Models entrenats | No | Es generen amb `train.py` |
| `results/` | Informes d’avaluació | No | Es generen amb `evaluate.py` |
| `figures/` | Figures finals i gràfics | Depèn del criteri del projecte | Poden servir per documentar resultats |

## Estructura del repositori

```text
tcga-coad-cms-ml-pipeline/
├── data/
│   ├── metadata/       # manifests, sample sheets i etiquetes CMS
│   ├── raw/gdc/        # fitxers RNA-seq descarregats
│   ├── processed/      # dades transformades per als models
│   └── models/         # models entrenats
├── docs/               # documentació MkDocs
├── figures/            # figures generades
├── notebooks/          # exploració i anàlisi interactiva
├── results/            # mètriques i informes d’avaluació
├── scripts/            # punts d’entrada executables
├── src/                # mòduls reutilitzables
├── tools/              # eines externes, com gdc-client
├── environment.yml
└── README.md
```

La separació entre `scripts/` i `src/` és una decisió arquitectònica important. Els scripts actuen com a punts d’entrada executables i orquestren cada etapa. Els mòduls de `src/` contenen la lògica reutilitzable que pot ser cridada per scripts, notebooks o tests.

## Visió general del pipeline

El pipeline s’executa en quatre etapes productives:

```text
1. Descàrrega       scripts/download.py      src/gdc_utils.py
2. Preprocessament  scripts/preprocess.py    src/preprocessing.py
3. Entrenament      scripts/train.py         src/models.py
4. Avaluació        scripts/evaluate.py      src/evaluation.py
```

L’exploració amb notebooks no es considera una etapa productiva del pipeline. És una etapa d’anàlisi que ajuda a validar les dades i interpretar resultats, però no modifica els fitxers que entren als models.

## Contracte de les etapes

| Etapa | Entrada | Procés | Sortida |
|---|---|---|---|
| Descàrrega | Manifest GDC a `data/metadata/` | Instal·la o localitza `gdc-client` i descarrega els fitxers | Fitxers RNA-seq a `data/raw/gdc/` |
| Preprocessament | Fitxers raw i metadades | Construeix matriu, filtra, uneix etiquetes, separa train/test i transforma | `X_train`, `X_test`, `y_train`, `y_test` i logs |
| Entrenament | Dades processades de train | Entrena Logistic Regression, Random Forest i SVM | Models `.joblib` i `training_log.json` |
| Avaluació | Models entrenats i dades de test | Calcula mètriques i figures | `evaluation_report.json` i gràfics |

## Arquitectura C4

El model C4 permet documentar arquitectura amb diferents nivells de zoom. En aquesta documentació s’utilitzen tres nivells: context, contenidors i components. El nivell de context mostra el sistema i els actors externs; el nivell de contenidors mostra les parts principals del sistema; i el nivell de components mostra l’estructura interna de cada etapa.

### Nivell 1: context del sistema

![Diagrama C4 de context](assets/diagrames/c4-context.png)

El diagrama de context mostra el pipeline com un sistema de software complet. L’actor principal és l’investigador o investigadora, que executa el pipeline i consulta la documentació.

El sistema interactua amb tres elements externs:

| Element extern | Funció dins del projecte |
|---|---|
| Genomic Data Commons | Proporciona els fitxers RNA-seq i les metadades de descàrrega |
| Synapse | Proporciona recursos externs relacionats amb les etiquetes CMS |
| GitHub Pages | Publica la documentació tècnica generada amb MkDocs |

Aquest nivell respon a la pregunta: **qui utilitza el sistema i amb quines fonts externes es relaciona?**

### Nivell 2: contenidors

![Diagrama C4 de contenidors](assets/diagrames/c4-containers.png)

El diagrama de contenidors amplia el sistema i mostra les parts principals del projecte. Dins del pipeline apareixen quatre etapes productives: obtenció de dades, preprocessament, entrenament i avaluació.

També s’hi mostra la documentació com un bloc separat. Aquesta documentació es construeix amb MkDocs i es publica a GitHub Pages. Els notebooks apareixen com a suport tècnic per entendre decisions, paràmetres i resultats, però no substitueixen els scripts del pipeline.

La lectura del diagrama és la següent:

1. L’investigador o investigadora executa les etapes del pipeline.
2. La primera etapa obté dades del GDC.
3. Les metadades i etiquetes externes es guarden a `data/metadata/`.
4. El preprocessament genera dades netes a `data/processed/`.
5. L’entrenament genera models a `data/models/`.
6. L’avaluació genera resultats i figures.
7. La documentació explica el procés i es publica a GitHub Pages.

Aquest nivell respon a la pregunta: **quines parts formen el sistema i com flueixen les dades?**

## Components de cada etapa

### Etapa 1: obtenció de dades

![Components de l’etapa d’obtenció de dades](assets/diagrames/c4-components-download.png)

L’etapa d’obtenció de dades té com a punt d’entrada `scripts/download.py`. Aquest script no concentra tota la lògica, sinó que delega les funcions reutilitzables a `src/gdc_utils.py`.

| Component | Responsabilitat |
|---|---|
| `scripts/download.py` | Punt d’entrada executable de la descàrrega |
| `src/gdc_utils.py` | Funcions per localitzar, descarregar i executar `gdc-client` |
| `tools/gdc-client/` | Directori on es guarda l’eina externa de descàrrega |
| `data/metadata/` | Directori amb manifests i metadades |
| `data/raw/gdc/` | Directori on es guarden els fitxers descarregats |

El flux principal és:

```text
scripts/download.py
        │
        ▼
src/gdc_utils.py
        │
        ├── llegeix manifest a data/metadata/
        ├── comprova o descarrega gdc-client
        └── desa els fitxers a data/raw/gdc/
```

Aquesta separació facilita la reutilització del codi. Si en el futur cal canviar la manera de descarregar dades, el canvi es pot concentrar a `src/gdc_utils.py`.

### Etapa 2: preprocessament

![Components de l’etapa de preprocessament](assets/diagrames/c4-components-preprocess.png)

L’etapa de preprocessament transforma els fitxers RNA-seq descarregats en una matriu apta per entrenar models. El punt d’entrada és `scripts/preprocess.py`, mentre que la lògica principal viu a `src/preprocessing.py`.

| Component | Responsabilitat |
|---|---|
| `scripts/preprocess.py` | Orquestra el preprocessament |
| `src/preprocessing.py` | Implementa neteja, filtratge, split i transformació |
| `data/raw/gdc/` | Entrada amb fitxers RNA-seq descarregats |
| `data/metadata/` | Entrada amb metadades i etiquetes |
| `data/processed/` | Sortida amb matrius i logs processats |

El preprocessament s’organitza en dos blocs:

```text
Bloc 1: neteja segura abans del split
  ├── construir matriu d’expressió
  ├── eliminar files QC
  ├── filtrar gens protein-coding
  ├── deduplicar mostres
  └── unir amb etiquetes CMS

Split train/test

Bloc 2: transformacions després del split
  ├── filtrar gens amb baix comptatge usant només train
  └── aplicar log2(x + 1)
```

La separació abans i després del split evita que el conjunt de test influeixi en decisions de preprocessament que haurien de calcular-se només amb les dades d’entrenament.

### Etapa 3: entrenament

![Components de l’etapa d’entrenament](assets/diagrames/c4-components-train.png)

L’etapa d’entrenament carrega les dades processades i entrena els classificadors. El punt d’entrada és `scripts/train.py` i la lògica dels models es troba a `src/models.py`.

| Component | Responsabilitat |
|---|---|
| `scripts/train.py` | Punt d’entrada de l’entrenament |
| `src/models.py` | Funcions de càrrega de dades i entrenament dels models |
| `data/processed/` | Entrada amb `X_train` i `y_train` |
| `data/models/` | Sortida amb models entrenats |

Els models entrenats són:

- Logistic Regression.
- Random Forest.
- SVM amb kernel lineal.

Tots els models reben la mateixa matriu d’entrenament i les mateixes etiquetes. Això permet comparar-los en condicions homogènies.

### Etapa 4: avaluació

![Components de l’etapa d’avaluació](assets/diagrames/c4-components-evaluate.png)

L’etapa d’avaluació carrega els models entrenats i les dades de test. El punt d’entrada és `scripts/evaluate.py`. Les funcions de càlcul de mètriques i generació de figures es troben a `src/evaluation.py`.

| Component | Responsabilitat |
|---|---|
| `scripts/evaluate.py` | Punt d’entrada de l’avaluació |
| `src/evaluation.py` | Càlcul de mètriques, matrius de confusió i gràfics |
| `src/models.py` | Funcions de càrrega de dades o models quan cal |
| `data/models/` | Entrada amb models entrenats |
| `data/processed/` | Entrada amb `X_test` i `y_test` |
| `results/` | Sortida amb informes numèrics |
| `figures/` | Sortida amb figures d’avaluació |

Aquesta etapa no entrena cap model. Només avalua models ja generats sobre dades que no s’han utilitzat durant l’entrenament.

## Flux de fitxers

```text
data/metadata/
   │
   ▼
scripts/download.py
   │
   ▼
data/raw/gdc/
   │
   ▼
scripts/preprocess.py
   │
   ▼
data/processed/
   │
   ▼
scripts/train.py
   │
   ▼
data/models/
   │
   ▼
scripts/evaluate.py
   │
   ├── results/evaluation_report.json
   └── figures/*.png
```

## Decisions tècniques principals

| Decisió | Justificació |
|---|---|
| Separar `scripts/` i `src/` | Manté punts d’entrada simples i lògica reutilitzable |
| No versionar dades raw | Evita pujar fitxers grans i regenerables |
| Guardar manifests | Permet reconstruir el mateix dataset |
| Fer split abans de transformacions dependents de dades | Redueix el risc de data leakage |
| Entrenar tots els models amb el mateix split | Permet una comparació justa |
| Guardar logs i artefactes | Facilita auditoria i reproducció |

## Resum

El pipeline està dissenyat com una seqüència modular. Cada etapa té un script executable, un o més mòduls reutilitzables i una sortida clara. Aquesta estructura facilita entendre el projecte, executar-lo per parts i reproduir els resultats finals.
