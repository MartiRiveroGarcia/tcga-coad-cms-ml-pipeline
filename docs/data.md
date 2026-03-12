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

## Instal·lació de l’eina de descàrrega (GDC Data Transfer Tool)

Per descarregar fitxers del GDC a partir d’un manifest, el projecte utilitza el **GDC Data Transfer Tool (gdc-client)**, instal·lat des de binaris oficials (cross-platform). ([GDC Data Transfer Tool](https://gdc.cancer.gov/access-data/gdc-data-transfer-tool))

### Instal·lar gdc-client (Linux/Windows/macOS)
Aquest repositori inclou un script que:
- detecta el sistema operatiu,
- descarrega el binari oficial corresponent,
- verifica el **MD5** publicat pel GDC,
- i el descomprimeix a `tools/gdc-client/<versió>/<plataforma>/`.

Comanda (NO descarrega res si no poses `--install`):
```bash
python scripts/setup_gdc_client.py

Instal·lació real:
```bash
python scripts/setup_gdc_client.py --install

> Nota: Els binaris dins tools/gdc-client/ no es versionen (estan al .gitignore).

### Descàrrega de dades amb manifest

El manifest de descàrrega del GDC és:

data/metadata/gdc_manifest.2026-03-09.191818.txt

Un cop tens gdc-client instal·lat, la descàrrega (quan toqui) es fa amb:

tools/gdc-client/2.3.0/linux_x64/gdc-client download -m data/metadata/gdc_manifest.2026-03-09.191818.txt -d data/raw/gdc

(A Windows i macOS, canvia la ruta segons la plataforma que hagi instal·lat el script.)