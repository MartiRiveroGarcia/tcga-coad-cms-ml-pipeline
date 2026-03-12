# Dades i manifest

Aquest projecte NO puja dades grans al repositori. El que versionem és la **traçabilitat**:
- criteris de selecció
- consulta (o descripció) per reconstruir la descàrrega
- estructura/format dels fitxers d’entrada

## Què guardem a `data/manifests/`
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
| `data/manifests/` | Metadades i instruccions de descàrrega | **Sí** |

- Les carpetes `data/raw/` i `data/processed/` estan al `.gitignore`.
- Per reconstruir les dades, seguiu les instruccions del manifest (`data/manifests/`).
