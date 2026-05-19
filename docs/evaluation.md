# Avaluació de models

## Objectiu

L'etapa d'avaluació mesura el rendiment real de cada model sobre el **conjunt de test** —
74 mostres que cap model ha vist mai durant l'entrenament. L'objectiu és respondre:

> Quin model generalitza millor la classificació CMS en dades noves?

A diferència de l'etapa anterior, aquí **no s'entrena res**. Els models es carreguen
des de `data/models/` i s'avaluen sobre `data/processed/X_test.csv`.

## Artefactes generats

| Fitxer | Descripció |
|--------|-----------|
| `results/evaluation_report.json` | Mètriques numèriques per a tots els models |
| `figures/confusion_matrix_logistic_regression.png` | Matriu de confusió — Logistic Regression |
| `figures/confusion_matrix_random_forest.png` | Matriu de confusió — Random Forest |
| `figures/confusion_matrix_svm.png` | Matriu de confusió — SVM (linear) |
| `figures/metrics_comparison.png` | Accuracy i F1 macro comparats en barres |
| `figures/f1_per_class.png` | F1-score per subtipus CMS i model |

## Per què el test set?

Durant l'entrenament, tots els models assoleixen una **accuracy del 100%** sobre les
dades de train. Això és esperat i no és overfitting: amb 15.625 dimensions i 296
mostres, els tres models (especialment RF i SVM) troben separadors perfectes.

El que importa és si aquest aprenentatge **generalitza** a mostres noves. Per saber-ho,
cal un conjunt de dades que el model mai hagi vist: el **test set** (74 mostres, 20%).

| Mesura | Train | Test |
|--------|-------|------|
| Accuracy esperada | ~100% | 70–90% (rang típic per CMS) |
| Significat | El model ha après les dades | El model pot classificar casos nous |

> **Regla fonamental:** mai prenguis decisions de model (hiperparàmetres, selecció de
> característiques, arquitectura) basant-te en el test set. Si ho fas, el test set
> deixa de ser una estimació honest del rendiment real.

## Mètriques

### Accuracy

La fracció de mostres classificades correctament:

```
Accuracy = Encerts / Total mostres
```

És intuitiva però pot ser enganyosa amb classes desbalancejades. Si CMS3 és el 15%
del test i el model sempre prediu CMS2, l'accuracy seria alta però el model seria inútil.

### Precision, Recall i F1-score (per classe)

Per a cada subtipus CMS:

| Mètrica | Fórmula | Interpretació |
|---------|---------|---------------|
| **Precision** | TP / (TP + FP) | Dels que el model diu "és CMS1", quants ho són realment? |
| **Recall** | TP / (TP + FN) | Dels CMS1 reals, quants ha detectat el model? |
| **F1-score** | 2 × (P × R) / (P + R) | Mitjana harmònica de precision i recall |

On TP = True Positives, FP = False Positives, FN = False Negatives.

### F1 macro vs F1 weighted

| Variant | Càlcul | Quan usar-la |
|---------|--------|-------------|
| **F1 macro** | Mitjana aritmètica dels F1 per classe | Quan totes les classes importan igual (p. ex. CMS3 = 11 mostres val tant com CMS2 = 29) |
| **F1 weighted** | Mitjana ponderada per support | Quan les classes majoritàries importan més proporcionalment |

Per a l'objectiu clínic del TFG (classificar correctament tots els subtipus, inclòs
el minoritari CMS3), el **F1 macro** és la mètrica principal.

## Confusion matrix

La matriu de confusió mostra per a cada subtipus real (eix Y) quantes mostres s'han
classificat en cada subtipus predit (eix X):

```
            Predicció
            CMS1  CMS2  CMS3  CMS4
Real  CMS1  [ 12    1     0     1 ]
      CMS2  [  0   27     1     1 ]
      CMS3  [  1    2     6     2 ]
      CMS4  [  0    1     0    19 ]
```

- La **diagonal** conté els encerts (valors alts → bon rendiment)
- Les **cel·les fora de la diagonal** són errors (quins subtipus es confonen entre si)
- **CMS3** sol tenir els valors de recall més baixos per ser la classe minoritària (11 mostres al test)

## Benchmark table

El script imprimeix una taula comparativa amb totes les mètriques per a cada model:

```
                      Accuracy  F1 macro  F1 weighted  F1 CMS1  F1 CMS2  F1 CMS3  F1 CMS4
Model
Logistic Regression   0.8378    0.7920    0.8305       0.8571   0.9032   0.5455   0.8421
Random Forest         0.8243    0.7745    0.8142       0.8000   0.8966   0.5333   0.8649
SVM (linear)          0.8378    0.7920    0.8305       0.8571   0.9032   0.5455   0.8421
```

*(Valors orientatius — els resultats exactes depenen del dataset i la seed)*

## Estructura de sortida

```
results/
└── evaluation_report.json

figures/
├── confusion_matrix_logistic_regression.png
├── confusion_matrix_random_forest.png
├── confusion_matrix_svm.png
├── metrics_comparison.png
└── f1_per_class.png
```

> **Nota:** la carpeta `results/` no s'inclou al repositori git (`.gitignore`).
> Les figures de `figures/` sí que es versionan per documentar els resultats.

## Com executar

Prerequisit: haver executat `scripts/train.py` per generar els fitxers `.joblib`.

```bash
# Avaluació completa (recomanat)
python scripts/evaluate.py

# Veure configuració sense executar
python scripts/evaluate.py --dry-run

# Rutes personalitzades
python scripts/evaluate.py \
    --processed-dir data/processed \
    --models-dir data/models \
    --output-dir results \
    --figures-dir figures
```

## `evaluation_report.json` — estructura

```json
{
  "logistic_regression": {
    "accuracy": 0.8378,
    "f1_macro": 0.7920,
    "f1_weighted": 0.8305,
    "per_class": {
      "CMS1": {"precision": 0.8571, "recall": 0.8571, "f1": 0.8571, "support": 14},
      "CMS2": {"precision": 0.8750, "recall": 0.9310, "f1": 0.9032, "support": 29},
      "CMS3": {"precision": 0.7500, "recall": 0.4545, "f1": 0.5652, "support": 11},
      "CMS4": {"precision": 0.8421, "recall": 0.8421, "f1": 0.8421, "support": 19}
    }
  },
  "random_forest": { ... },
  "svm": { ... }
}
```

*(Les matrius `y_pred` no es persisten al JSON — massa grans i derivables dels models)*

## Interpretació dels resultats

### Per què CMS3 té F1 baix?

CMS3 és el subtipus **menys representat** (43/296 mostres al train, 11/74 al test).
Tot i usar `class_weight='balanced'` per compensar el desbalanceig, el model
té menys exemples d'on aprendre els patrons de CMS3.

A més, CMS3 és biològicament el subtipus **menys diferenciat** — el seu perfil
d'expressió gènica se solapa parcialment amb CMS1 i CMS2, cosa que dificulta
la classificació.

### Per què els tres models donen resultats similars?

Tots els models reben exactament les mateixes 15.625 dimensions. Amb tants features
(n_features >> n_samples), tots troben separadors lineals o quasi-lineals efectius.
Les diferències principals apareixeran en l'etapa de cerca d'hiperparàmetres.

### Reproducibilitat

Donat `random_seed=42` i el mateix conjunt de test, executar el pipeline dues vegades
produeix exactament les mateixes mètriques. Qualsevol pot reproduir els resultats:

```bash
# Primera vegada
python scripts/train.py && python scripts/evaluate.py

# Segona vegada (mateixos resultats)
python scripts/train.py && python scripts/evaluate.py
```
