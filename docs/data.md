# Dades

## Què són les dades d'aquest projecte?

Aquest projecte treballa amb dades d'**expressió gènica** (RNA-seq) de pacients amb càncer colorectal,
obtingudes del projecte públic [TCGA-COAD](https://portal.gdc.cancer.gov/) (The Cancer Genome Atlas — Colon Adenocarcinoma).

En termes simples: cada fitxer conté una llista de **gens** i quant s'expressa cadascun en una mostra de teixit tumoral.
Aquestes dades serveixen per entrenar models que classifiquin les mostres en **subtipus moleculars (CMS)**.

## D'on venen?

Les dades provenen del **GDC Data Portal** (Genomic Data Commons), el repositori oficial del NIH
per a dades genòmiques de càncer. No treballem amb dades crues (FASTQ) sinó amb
**comptatges ja quantificats** (STAR-Counts), que són taules numèriques llestes per analitzar.

### Criteris de selecció

| Criteri | Valor |
|---------|-------|
| Cohort | TCGA-COAD |
| Tipus de dada | RNA-seq (transcriptòmica) |
| Workflow | STAR-Counts (comptatges a nivell de gen) |
| Accés | Obert (open access) |
| Tipus de mostra | Teixit tumoral (Primary Tumor) |

Aquests criteris garanteixen un dataset **homogeni i reproduïble**.

## Què guardem al repositori?

El repositori **NO conté les dades grans** (fitxers RNA-seq). Només guardem fitxers petits
que permeten **reconstruir exactament el mateix dataset**:

| Carpeta | Contingut | Al repositori? |
|---------|-----------|----------------|
| `data/metadata/` | Manifests i metadades | Sí |
| `data/raw/` | Fitxers RNA-seq descarregats | No (.gitignore) |
| `data/processed/` | Dades netes i normalitzades | No (.gitignore) |

### Fitxers de metadades

**`gdc_manifest.<data>.txt`**
Manifest oficial del GDC. Conté els identificadors únics de cada fitxer, el seu MD5 i mida.
És l'entrada principal per a la descàrrega automatitzada.

**`metadata.repository.<data>.json`** (si existeix)
JSON amb metadades completes dels fitxers (nom, workflow, tipus de dada).
Permet justificar i auditar el dataset seleccionat.

**`gdc_sample_sheet.<data>.tsv`** (si existeix)
Taula que mapeja fitxers a casos/mostres del TCGA. Útil per associar
cada fitxer d'expressió amb el seu pacient i mostra d'origen.

## Com es descarreguen les dades?

La descàrrega és completament automatitzada amb una sola comanda:

```bash
python scripts/download.py
```

### Què fa aquest script?

1. **Busca el manifest** — detecta automàticament el fitxer `gdc_manifest*.txt` més recent a `data/metadata/`
2. **Instal·la gdc-client si cal** — el [GDC Data Transfer Tool](https://gdc.cancer.gov/access-data/gdc-data-transfer-tool) és l'eina oficial per descarregar dades del GDC. Si no la tens instal·lada, el script la descarrega, en verifica el MD5, i l'extreu a `tools/gdc-client/`
3. **Descarrega els fitxers** — usa gdc-client amb el manifest per baixar tots els fitxers a `data/raw/gdc/`

### Opcions disponibles

```bash
# Veure què faria sense descarregar res
python scripts/download.py --dry-run

# Usar un manifest concret
python scripts/download.py --manifest data/metadata/gdc_manifest.2026-03-09.191818.txt

# Canviar el directori de sortida
python scripts/download.py --out data/raw/custom_dir
```

### Estructura interna

El script `scripts/download.py` és un punt d'entrada lleuger. Tota la lògica reutilitzable
(detecció de plataforma, instal·lació, cerca de l'executable) viu a `src/gdc_utils.py`.

```
scripts/download.py          ← punt d'entrada (parseig d'arguments, orquestració)
    ↓ importa
src/gdc_utils.py             ← lògica compartida (instal·lació, detecció, cerca)
    ↓ usa
tools/gdc-client/            ← binari descarregat (.gitignore)
    ↓ descarrega
data/raw/gdc/                ← fitxers RNA-seq (.gitignore)
```

## Principi de reproductibilitat

Qualsevol persona que cloni el repositori pot obtenir exactament les mateixes dades executant
`python scripts/download.py`. El manifest és determinista: conté els IDs exactes dels fitxers
i els seus checksums per verificar la integritat.
