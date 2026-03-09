# Reproductibilitat (placeholder)

## Entorn (Conda)
Aquest projecte utilitza un entorn Conda definit a `environment.yml`.

### Crear l’entorn
```bash
conda env create -f environment.yml

### Activa l'entorn
```bash
conda activate tcga-coad-cms-ml-pipeline

### Comprovació ràpida
```bash
python -c "import numpy, pandas, sklearn, matplotlib; print('Ok imports')"

- Entorn conda (`environment.yml`)
- Seeds
- Com reproduir un run
