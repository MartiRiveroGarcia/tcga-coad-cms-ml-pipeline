# Projecte

## Objectiu del TFG
Construir un pipeline reproduïble i documentat per classificar subtipus CMS a TCGA-COAD a partir d’expressió gènica, i comparar models sota condicions homogènies.

## Abast
- Pipeline de preparació de dades (matriu + metadades → dataset llest per ML)
- Entrenament i comparació de models ML
- Avaluació amb mètriques i matrius de confusió
- Documentació didàctica i reproduïbilitat (entorn, configs, seeds)

## Fora d’abast
- Processament de dades crues (FASTQ), QC, alineament, quantificació.

## Resum del pipeline (alt nivell)
1) Definició de cohort i criteris (manifest)
2) Construcció matriu d’expressió + metadades
3) Split train/test (abans de transformacions)
4) Preprocessament (fit al train → apply al test)
5) Entrenament models + tuning
6) Avaluació final al test
7) Export de resultats + traçabilitat (configs, versions)

## Models previstos
- Random Forest
- SVM
- Logistic Regression (baseline)

## Decisions clau
- Split train/test abans de qualsevol transformació.
- No es treballa amb FASTQ (fora d’abast).
- No es pugen dades grans al repo; només manifests/metadades.
- Reproduïbilitat: entorn conda + seeds + config per run.

## KPIs
Veure: [KPI checklist](KPI_CHECKLIST.md)
