# Pipeline

## 1. Objectiu del pipeline
Aquest projecte defineix i documenta un **flux de treball reproduïble** per a la classificació dels subtipus CMS del càncer colorectal a partir de **matrius d’expressió RNA-seq ja processades**, amb l’objectiu de poder executar i comparar models sota condicions homogènies i transparents. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

## 2. Dades d’entrada (què entra al pipeline)
### 2.1 Font
Les dades s’obtenen del **GDC Data Portal** (TCGA), i s’utilitza la cohort **TCGA-COAD**. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

### 2.2 Tipus de dades i format esperat
Per al pipeline és imprescindible treballar amb:
- **Matriu d’expressió gènica** (valors numèrics homogènics).
- **Metadades** per filtrar i seleccionar mostres. :contentReference[oaicite:4]{index=4}

No es treballa amb dades crues **FASTQ**, perquè això implicaria fases fora d’abast (QC, alineament, quantificació, etc.). :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}

### 2.3 Criteris de selecció (per garantir homogeneïtat i reproductibilitat)
Per assegurar un conjunt de dades homogeni i reproduïble, s’apliquen aquests criteris:
- Cohort: **TCGA-COAD**
- Dades transcriptòmiques: **RNA-seq**
- Fitxers quantificats amb **STAR-Counts** (comptatges a nivell de gen)
- Només dades **d’accés obert**
- Mostres de **teixit tumoral** per minimitzar variabilitat biològica :contentReference[oaicite:7]{index=7}

## 3. Sortida d’aquesta fase (què ha de quedar generat)
Al final de la fase “dades”, el projecte ha de conservar:
- Un **manifest** i **metadades** suficients per reconstruir la descàrrega i el dataset (traçabilitat). :contentReference[oaicite:8]{index=8}
- La matriu d’expressió (format tabular) ja llesta per entrar al preprocessament.

> Nota de qualitat: per evitar biaixos i “leakage”, les transformacions s’han d’ajustar al conjunt d’entrenament i aplicar-se al conjunt de prova amb els paràmetres obtinguts. :contentReference[oaicite:9]{index=9}
