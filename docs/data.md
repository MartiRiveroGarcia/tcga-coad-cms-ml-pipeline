# Dades i manifest

Aquest projecte NO puja dades grans al repositori. El que versionem és la **traçabilitat**:
- criteris de selecció
- consulta (o descripció) per reconstruir la descàrrega
- estructura/format dels fitxers d’entrada

## Què guardem a `data/metadata/`
1) `dataset_manifest.json`
   - Cohort (ex: TCGA-COAD)
   - Tipus de dades (RNA-seq)
   - Workflow/format (ex: STAR-Counts)
   - Accés (open)
   - Tipus de mostra (tumoral, etc.)
   - Data de creació i notes

2) `samples.tsv` (opcional però recomanat)
   - Taula amb les mostres/fitxers seleccionats (IDs, nom fitxer, etc.)
   - Serveix per reconstruir exactament el dataset i auditar canvis

> Objectiu: que qualsevol persona pugui reconstruir el mateix dataset només amb aquests fitxers.

## Carpetes de dades i política de git

| Carpeta | Contingut | Versionat? |
|---------|-----------|------------|
| `data/raw/` | Fitxers descarregats (RNA-seq counts, etc.) | **No** — gitignored |
| `data/processed/` | Sortides de preprocessament | **No** — gitignored |
| `data/metadata/` | Metadades | **Sí** |

- Les carpetes `data/raw/` i `data/processed/` estan al `.gitignore`.

## Fitxers de traçabilitat (export GDC)

Aquesta carpeta conté fitxers **petits** (manifest i metadades) que permeten reproduir la selecció i la descàrrega sense pujar dades grans al repositori.

### Ubicació
- `data/metadata/` (versionat)
- `data/raw/` (NO versionat; només descàrregues)

### Fitxers

**1) `gdc_manifest.<data>.txt`**
- Manifest oficial del GDC per descarregar fitxers amb el Data Transfer Tool.
- Conté els identificadors dels fitxers (`id`) i informació per validar la descàrrega (`md5`, `size`, `state`).
- És l’entrada principal del pas de descàrrega (futur): `gdc-client download -m <manifest>`.

**2) `metadata.repository.<data>.json`**
- JSON amb metadades completes dels fitxers del dataset (nom, mida, md5, tipus de dada).
- Inclou informació del workflow d’anàlisi (p. ex. `STAR - Counts`) i permet justificar/reproduir el dataset seleccionat.
- Pot referenciar fitxers d’entrada (p. ex. BAM) que poden ser d’accés controlat: el projecte treballa amb els fitxers de sortida oberts (counts) i NO descarrega els inputs controlats.

**3) `gdc_sample_sheet.<data>.tsv`**
- Taula “humana” exportada del GDC per fer mapeig entre fitxers i casos/mostres.
- La capçalera exacta es pot veure amb: `head -n 1 data/metadata/gdc_sample_sheet.<data>.tsv`.