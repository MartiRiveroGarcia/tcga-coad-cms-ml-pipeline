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

Transforma 483 fitxers de comptatge en un dataset net llest per entrenar models.
S'executa amb una sola comanda:

```bash
python scripts/preprocess.py
```

**Entrada:** fitxers RNA-seq a `data/raw/gdc/` + metadades a `data/metadata/`
**Sortida:** 6 fitxers a `data/processed/` (veure [sortida](#sortida-de-letapa-2))

### Visió general dels passos

El preprocessament es divideix en **dos blocs** separats pel train/test split.
Aquesta divisió és fonamental per evitar **data leakage** (veure nota més avall).

```
483 fitxers raw
      │
      ▼
  BLOC 1: Neteja segura (no mira valors d'expressió)
  ├── Pas 1: Construir matriu (60.664 gens × 483 fitxers)
  ├── Pas 2: Eliminar files QC — 4 files de metadades d'alineament
  ├── Pas 3: Filtrar gens protein-coding (60.660 → 19.962)
  ├── Pas 4: Deduplicar mostres (483 → 458)
  └── Pas 5: Unir amb etiquetes CMS (458 → 370)
      │
      ▼
  Pas 6: TRAIN/TEST SPLIT (296 train / 74 test, seed=42)
      │
      ▼
  BLOC 2: Transformacions (fit on train, apply to both)
  ├── Pas 7: Filtrar gens amb baix comptatge (19.962 → 15.625)
  └── Pas 8: Transformació log2(x + 1)
      │
      ▼
  Pas 9: Guardar tot a data/processed/
```

### Bloc 1: Neteja segura (abans del split)

Aquests passos **no generen data leakage** perquè les decisions es basen en
metadades o anotacions externes, no en la distribució dels valors d'expressió.

**Pas 1 — Construir matriu d'expressió.** Llegeix cada fitxer TSV dins de
`data/raw/gdc/<UUID>/`, n'extreu la columna `unstranded` (comptatges raw),
i els combina en una matriu única on cada fila és un gen i cada columna és un fitxer.

**Pas 2 — Eliminar files QC.** Els fitxers STAR-Counts inclouen 4 files de control
de qualitat (`N_unmapped`, `N_multimapping`, `N_noFeature`, `N_ambiguous`) que
no són gens reals sinó estadístiques de l'alineament. S'eliminen.

**Pas 3 — Filtrar gens protein-coding.** De ~60.660 gens, només es retenen els
~19.962 de tipus `protein_coding` segons l'anotació GENCODE v36.
Gens no codificants (lncRNA, pseudogens, etc.) s'eliminen perquè introdueixen
soroll sense aportar informació rellevant per a la classificació CMS.

**Pas 4 — Deduplicar mostres.** El dataset conté 483 fitxers però només 458 pacients
únics. Les duplicitats provenen de:

| Tipus | Quantes | Criteri d'eliminació |
|-------|---------|---------------------|
| Mostres FFPE | 13 | Perfil d'expressió alterat pel fixat en formalina |
| Mostres no primàries (metàstasi, recurrència) | 2 | Només treballem amb tumor primari |
| Fitxers duplicats per pacient | 10 | Es reté el fitxer amb més profunditat de seqüenciació |

**Pas 5 — Unir amb etiquetes CMS.** Es fa un inner join entre la matriu i les etiquetes
CMS de Guinney et al. 2015 (veure [Dades — Etiquetes CMS](data.md#etiquetes-cms-consensus-molecular-subtypes)).
Les mostres sense etiqueta es descarten. Resultat: **370 mostres**.

Distribució:

| Subtipus | Mostres | % |
|----------|---------|---|
| CMS2 | 145 | 39% |
| CMS4 | 100 | 27% |
| CMS1 | 71 | 19% |
| CMS3 | 54 | 15% |

### Pas 6: Train/test split

Dividim les 370 mostres en **296 entrenament** i **74 test** (80/20).
El split és **estratificat**: les proporcions de CMS1-4 es mantenen en ambdós conjunts.

La **seed=42** fixa l'aleatorietat. Executar el pipeline dos cops amb la mateixa seed
produeix exactament la mateixa partició.

### Bloc 2: Transformacions (després del split)

Aquí sí que mirem els valors d'expressió per prendre decisions. Per evitar data leakage,
els criteris es calculen **només sobre el conjunt d'entrenament** i s'apliquen
idènticament al de test.

> **Data leakage**: si normalitzes o filtres amb informació del conjunt de test,
> el model "veu" indirectament dades que no hauria de veure durant l'entrenament.
> Això produeix mètriques massa optimistes que no reflecteixen el rendiment real.

**Pas 7 — Filtrar gens amb baix comptatge.** Un gen es reté si almenys el 20% de
les mostres d'entrenament tenen un comptatge ≥ 10. Si un gen gairebé no s'expressa,
no aporta senyal útil per discriminar subtipus. Resultat: 19.962 → **15.625 gens**.

**Pas 8 — Transformació log2(x + 1).** Aplica `log2(x + 1)` a tots els comptatges.
Això comprimeix el rang de valors (de 0–1.700.000 a 0–20.7) i redueix l'efecte
dels gens molt expressats, fent les dades més adequades per als algorismes de ML.
El `+1` evita `log(0) = -infinit`.

### Sortida de l'etapa 2

Tots els fitxers es guarden a `data/processed/`:

| Fitxer | Contingut | Format |
|--------|-----------|--------|
| `X_train.csv` | 296 mostres × 15.625 gens (log2) | Mostres com a files, gens com a columnes |
| `X_test.csv` | 74 mostres × 15.625 gens (log2) | Idem |
| `y_train.csv` | Etiqueta CMS per cada mostra train | case_id, cms_label |
| `y_test.csv` | Etiqueta CMS per cada mostra test | case_id, cms_label |
| `gene_names.csv` | Mapatge gene_id → gene_name | Per interpretar resultats |
| `preprocessing_log.json` | Tots els paràmetres i comptadors | Per auditoria |

### Opcions del script

```bash
# Veure què faria sense processar
python scripts/preprocess.py --dry-run

# Canviar seed o proporció de test
python scripts/preprocess.py --seed 123 --test-size 0.3
```

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
