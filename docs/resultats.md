# Experiments i resultats

Aquesta pàgina resumeix l’exploració de dades, l’entrenament dels models i l’avaluació final. L’objectiu és documentar què s’ha comprovat, quins models s’han entrenat i com s’ha comparat el seu rendiment.

## Objectiu dels experiments

Els experiments responen a tres preguntes:

1. Les dades preprocessades tenen una estructura coherent?
2. Els subtipus CMS mostren separació en l’espai d’expressió gènica?
3. Quin model supervisat generalitza millor sobre el conjunt de test?

La comparació es fa amb un únic protocol: tots els models utilitzen el mateix preprocessament, el mateix split train/test i la mateixa seed.

## Exploració de dades

L’exploració es fa amb el notebook:

```text
notebooks/data_exploration.ipynb
```

Aquesta etapa és analítica. No modifica les dades que entren als models. Serveix per comprovar la qualitat del preprocessament i obtenir una primera lectura visual de la separabilitat dels subtipus CMS.

### Dades utilitzades

| Element | Valor |
|---|---|
| Mostres totals amb etiqueta CMS | 370 |
| Mostres train | 296 |
| Mostres test | 74 |
| Nombre de gens després del preprocessament | 15.625 |
| Subtipus | CMS1, CMS2, CMS3, CMS4 |

### Distribució de classes

| Subtipus | Mostres totals | Percentatge aproximat |
|---|---:|---:|
| CMS1 | 71 | 19% |
| CMS2 | 145 | 39% |
| CMS3 | 54 | 15% |
| CMS4 | 100 | 27% |

El dataset està desbalancejat. CMS2 és la classe majoritària i CMS3 és la classe menys representada. Per aquest motiu, l’avaluació no es pot basar només en accuracy i s’utilitza F1 macro com a mètrica principal.

## PCA i UMAP

Les dades processades tenen 15.625 dimensions, una per gen. Per visualitzar-les, es fan servir tècniques de reducció de dimensionalitat.

| Tècnica | Tipus | Ús en el projecte |
|---|---|---|
| PCA | Lineal | Analitzar direccions principals de variació |
| UMAP | No lineal | Visualitzar agrupacions locals i possibles clústers |

PCA i UMAP només s’utilitzen per exploració. Els models no s’entrenen amb les components reduïdes, sinó amb la matriu completa de gens preprocessats.

## Entrenament dels models

L’entrenament es fa amb:

```bash
python scripts/train.py
```

Els models entrenats són:

| Model | Configuració principal | Justificació |
|---|---|---|
| Logistic Regression | `solver='lbfgs'`, `max_iter=5000`, `class_weight='balanced'` | Baseline lineal i interpretable |
| Random Forest | `n_estimators=500`, `max_features='sqrt'`, `class_weight='balanced'` | Model robust i capaç de capturar relacions no lineals |
| SVM lineal | `kernel='linear'`, `class_weight='balanced'` | Adequat quan hi ha moltes més variables que mostres |

Tots els models es guarden a:

```text
data/models/
├── logistic_regression.joblib
├── random_forest.joblib
├── svm.joblib
└── training_log.json
```

El fitxer `training_log.json` documenta els hiperparàmetres, la seed i informació bàsica de l’entrenament.

## Avaluació

L’avaluació es fa amb:

```bash
python scripts/evaluate.py
```

Aquesta etapa carrega els models entrenats i els avalua sobre el conjunt de test. El conjunt de test no s’utilitza durant l’entrenament i serveix per estimar la capacitat de generalització dels models.

### Mètriques utilitzades

| Mètrica | Funció |
|---|---|
| Accuracy | Proporció global de mostres classificades correctament |
| Precision | Fiabilitat de les prediccions positives d’una classe |
| Recall | Capacitat de detectar totes les mostres reals d’una classe |
| F1-score | Mitjana harmònica entre precision i recall |
| F1 macro | Mitjana del F1 de totes les classes amb el mateix pes |
| F1 weighted | Mitjana del F1 ponderada pel nombre de mostres de cada classe |

La mètrica principal és **F1 macro**, perquè dona el mateix pes a tots els subtipus CMS i evita que les classes majoritàries dominin la interpretació.

## Resultats del benchmark

| Model | Accuracy | F1 macro | F1 weighted | F1 CMS1 | F1 CMS2 | F1 CMS3 | F1 CMS4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.959459 | 0.954033 | 0.959442 | 0.9333 | 0.9831 | 0.9524 | 0.9474 |
| Random Forest | 0.851351 | 0.824548 | 0.843806 | 0.8667 | 0.8923 | 0.7059 | 0.8333 |
| SVM lineal | 0.959459 | 0.954033 | 0.959442 | 0.9333 | 0.9831 | 0.9524 | 0.9474 |

Segons aquests resultats, Logistic Regression i SVM lineal obtenen el mateix rendiment global en accuracy, F1 macro i F1 weighted. Random Forest queda per sota en totes les mètriques globals, especialment en F1 macro.

## Figures generades

L’avaluació genera les figures següents:

```text
figures/
├── confusion_matrix_logistic_regression.png
├── confusion_matrix_random_forest.png
├── confusion_matrix_svm.png
├── metrics_comparison.png
└── f1_per_class.png
```

### Matrius de confusió

Les matrius de confusió permeten veure quins subtipus es classifiquen correctament i quins es confonen entre si. La diagonal representa encerts i les cel·les fora de la diagonal representen errors.

La interpretació principal és que Logistic Regression i SVM classifiquen correctament la majoria de mostres del conjunt de test. En canvi, Random Forest mostra més dificultats, especialment en CMS3, on obté un recall de 0.5455.

### Comparació de mètriques

El gràfic `metrics_comparison.png` resumeix el rendiment global dels models. El gràfic `f1_per_class.png` mostra el rendiment per subtipus CMS i permet detectar si un model funciona bé globalment però falla en classes minoritàries.

## Interpretació tècnica

Logistic Regression i SVM obtenen els millors resultats globals i presenten el mateix rendiment en aquest experiment. Tots dos models aconsegueixen una accuracy de 0.959459 i un F1 macro de 0.954033.

Random Forest obté un rendiment inferior. La diferència principal es troba en CMS3, on el model presenta una precision de 1.0000 però un recall de 0.5455. Això indica que, quan Random Forest prediu CMS3, ho fa correctament, però no recupera totes les mostres reals d’aquest subtipus.

Aquesta limitació no invalida el pipeline, però mostra la importància d’avaluar el rendiment per classe. Una accuracy global pot ocultar diferències rellevants entre subtipus, especialment quan el dataset està desbalancejat.

## Sortida de l’avaluació

El fitxer principal és:

```text
results/evaluation_report.json
```

Exemple d’estructura:

```json
{
  "logistic_regression": {
    "accuracy": 0.959459,
    "f1_macro": 0.954033,
    "f1_weighted": 0.959442,
    "per_class": {
      "CMS1": {"precision": 0.875, "recall": 1.0, "f1": 0.9333, "support": 14},
      "CMS2": {"precision": 0.9667, "recall": 1.0, "f1": 0.9831, "support": 29},
      "CMS3": {"precision": 1.0, "recall": 0.9091, "f1": 0.9524, "support": 11},
      "CMS4": {"precision": 1.0, "recall": 0.9, "f1": 0.9474, "support": 20}
    }
  }
}
```

## Conclusió dels experiments

El pipeline permet entrenar i avaluar models de classificació CMS de manera homogènia. Logistic Regression i SVM lineal són els models amb millor rendiment global en aquesta configuració, amb una accuracy de 0.959459 i un F1 macro de 0.954033. Random Forest obté un rendiment inferior, principalment per la seva menor capacitat de recuperar mostres CMS3.