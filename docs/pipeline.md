# Pipeline

## Visió general

El pipeline transforma dades d'expressió gènica en una comparativa de models de classificació.
Cada etapa és un script independent que es pot executar per separat.

```
Dades RNA-seq (TCGA-COAD)
        │
        ▼
   DESCÀRREGA ────────── scripts/download.py
   Descarrega fitxers       src/gdc_utils.py
   del GDC Portal
        │
        ▼
   PREPROCESSAMENT ───── scripts/preprocess.py
   Filtra gens sorollosos,   src/preprocessing.py
   normalitza, split
   train/test
        │
        ▼
   ENTRENAMENT ────────── scripts/train.py
   Entrena 3 models            src/models.py
   amb les mateixes dades
   i la mateixa seed
        │
        ▼
   AVALUACIÓ ──────────── scripts/evaluate.py
   Mètriques, gràfics,        src/evaluation.py
   taula comparativa
```

## Etapa 1: Descàrrega de dades

**Script:** `scripts/download.py`
**Mòdul:** `src/gdc_utils.py`

Descarrega les dades RNA-seq del GDC Data Portal usant el manifest que hi ha a `data/metadata/`.
Si l'eina `gdc-client` no està instal·lada, la descarrega i instal·la automàticament.

**Entrada:** manifest GDC (`data/metadata/gdc_manifest*.txt`)
**Sortida:** fitxers RNA-seq a `data/raw/gdc/`

Veure [Dades](data.md) per a més detalls sobre el dataset i els criteris de selecció.

## Etapa 2: Preprocessament

**Script:** `scripts/preprocess.py`
**Mòdul:** `src/preprocessing.py`

Transforma les dades brutes en un dataset net i llest per entrenar models:

1. **Càrrega** — llegeix tots els fitxers de comptatge i els unifica en una matriu (gens × mostres)
2. **Filtratge de gens** — elimina gens amb poca variabilitat o expressió molt baixa (soroll)
3. **Normalització** — ajusta els valors perquè siguin comparables entre mostres
4. **Split train/test** — separa les dades en conjunt d'entrenament i de prova **abans** de cap transformació que pugui generar data leakage

**Entrada:** fitxers RNA-seq a `data/raw/gdc/`
**Sortida:** matriu neta a `data/processed/`

> **Data leakage**: si normalitzes amb informació del conjunt de test, el model "veu"
> dades que no hauria de veure. Per evitar-ho, les transformacions s'ajusten (fit)
> al train i s'apliquen (transform) al test amb els paràmetres del train.

## Etapa 3: Entrenament

**Script:** `scripts/train.py`
**Mòdul:** `src/models.py`

Entrena 3 models de classificació amb les mateixes dades d'entrenament i la mateixa seed:

| Model | Tipus | Per què? |
|-------|-------|----------|
| Logistic Regression | Lineal | Baseline simple i interpretable |
| Random Forest | Ensemble (arbres) | Robust, bon rendiment general |
| SVM | Kernel | Bon rendiment en espais d'alta dimensió |

Cada model rep la mateixa matriu d'entrenament i la mateixa partició.
Això garanteix que la comparativa sigui justa.

**Entrada:** dades processades de `data/processed/`
**Sortida:** models entrenats (en memòria, passats a l'etapa d'avaluació)

> **Nota:** els models entrenats NO es guarden al repositori. Qualsevol persona
> pot regenerar-los executant el pipeline amb la mateixa seed.

## Etapa 4: Avaluació

**Script:** `scripts/evaluate.py`
**Mòdul:** `src/evaluation.py`

Mesura el rendiment de cada model amb dades que **mai ha vist** (test set) i genera
visualitzacions comparatives:

- **Mètriques per model:** accuracy, precision, recall, F1-score
- **Confusion matrix:** taula que mostra encerts i errors per cada subtipus CMS
- **Taula comparativa (benchmark):** els 3 models costat a costat

**Entrada:** models entrenats + dades de test de `data/processed/`
**Sortida:** mètriques i gràfics

## Dades d'entrada

### Què és RNA-seq?

RNA-seq mesura quant s'expressa cada gen en una mostra de teixit. El resultat és una taula on:
- Cada **fila** és un gen (~60.000 gens)
- Cada **columna** és una mostra (un pacient)
- Cada **valor** és un comptatge (quantes vegades s'ha detectat aquell gen)

### Què són els subtipus CMS?

El càncer colorectal es classifica en 4 subtipus moleculars (Consensus Molecular Subtypes):

| Subtipus | Nom | Característiques principals |
|----------|-----|----------------------------|
| CMS1 | MSI Immune | Hipermutació, activació immune |
| CMS2 | Canonical | Activació WNT i MYC |
| CMS3 | Metabolic | Desregulació metabòlica |
| CMS4 | Mesenchymal | Activació TGF-β, pitjor pronòstic |

L'objectiu del pipeline és entrenar models que, donada l'expressió gènica d'una mostra,
prediguin a quin subtipus CMS pertany.
