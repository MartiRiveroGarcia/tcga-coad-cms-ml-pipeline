# Reproductibilitat

## Per què és important?

Un projecte de machine learning és **reproduïble** quan qualsevol persona pot obtenir
els mateixos resultats seguint les mateixes instruccions. Això implica controlar:

- **Entorn** — les mateixes versions de Python i llibreries
- **Dades** — el mateix dataset exacte
- **Aleatorietat** — la mateixa seed per als processos estocàstics
- **Codi** — el mateix codi font (versionat amb Git)

## Entorn (Conda)

L'entorn es defineix a `environment.yml` amb versions fixades de totes les dependències.

### Crear l'entorn

```bash
conda env create -f environment.yml
conda activate tcga-coad-cms-ml-pipeline
```

### Instal·lar el paquet local

Per poder importar els mòduls de `src/` des de qualsevol lloc (scripts, notebooks):

```bash
pip install -e .
```

### Verificar que tot funciona

```bash
python -c "import numpy, pandas, sklearn, matplotlib; print('Ok imports')"
```

## Dades

Les dades no es pugen al repositori perquè són massa grans. En canvi, guardem el
**manifest** (llista de fitxers amb els seus IDs i checksums) que permet reconstruir
exactament el mateix dataset:

```bash
python scripts/download.py
```

Veure [Dades](data.md) per a més detalls.

## Aleatorietat (seeds)

Els algorismes de ML tenen components aleatoris (partició train/test, inicialització de pesos, etc.).
Per garantir resultats idèntics entre execucions, fixem una **seed** (llavor aleatòria)
a tots els punts del pipeline que usen aleatorietat.

## Estructura del pipeline

El pipeline s'executa en 4 etapes seqüencials. Cada etapa és un script independent
que es pot executar per separat:

```bash
python scripts/download.py      # 1. Descarrega dades del GDC
python scripts/preprocess.py    # 2. Neteja i normalitza
python scripts/train.py         # 3. Entrena els 3 models
python scripts/evaluate.py      # 4. Genera mètriques i gràfics
```

## Què NO es versiona

| Què | Per què | Com reproduir-ho |
|-----|---------|------------------|
| `data/raw/` | Fitxers massa grans | `python scripts/download.py` |
| `data/processed/` | Es genera a partir de raw | `python scripts/preprocess.py` |
| `tools/gdc-client/` | Binari extern | S'instal·la automàticament |

## Verificació

Per comprovar que el pipeline és reproduïble:

1. Clona el repositori en un directori net
2. Crea l'entorn Conda des de zero
3. Executa les 4 etapes
4. Compara els resultats amb els obtinguts anteriorment

Les mètriques haurien de ser idèntiques si la seed és la mateixa.
