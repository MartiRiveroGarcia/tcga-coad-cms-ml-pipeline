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
| Logistic Regression | 0.8378 | 0.7920 | 0.8305 | 0.8571 | 0.9032 | 0.5455 | 0.8421 |
| Random Forest | 0.8243 | 0.7745 | 0.8142 | 0.8000 | 0.8966 | 0.5333 | 0.8649 |
| SVM lineal | 0.8378 | 0.7920 | 0.8305 | 0.8571 | 0.9032 | 0.5455 | 0.8421 |

Segons aquests resultats, Logistic Regression i SVM lineal obtenen el mateix rendiment global en accuracy i F1 macro. Random Forest queda lleugerament per sota en F1 macro, però manté un rendiment similar.

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

La interpretació principal és que CMS3 és el subtipus més difícil de classificar. Això és coherent amb el fet que és la classe menys representada en el dataset.

### Comparació de mètriques

El gràfic `metrics_comparison.png` resumeix el rendiment global dels models. El gràfic `f1_per_class.png` mostra el rendiment per subtipus CMS i permet detectar si un model funciona bé globalment però falla en classes minoritàries.

## Interpretació tècnica

Els tres models obtenen resultats similars perquè treballen amb una matriu d’alta dimensionalitat: hi ha molts més gens que mostres. En aquest context, models lineals com Logistic Regression i SVM poden trobar separadors efectius.

El rendiment inferior en CMS3 s’explica per dos factors:

1. CMS3 és el subtipus amb menys mostres.
2. Els seus patrons d’expressió poden solapar-se parcialment amb altres subtipus.

Aquesta limitació no invalida el pipeline, però indica que l’avaluació per classe és imprescindible. Una accuracy alta no és suficient si el model falla en un subtipus minoritari.

## Sortida de l’avaluació

El fitxer principal és:

```text
results/evaluation_report.json
```

Exemple d’estructura:

```json
{
  "logistic_regression": {
    "accuracy": 0.8378,
    "f1_macro": 0.7920,
    "f1_weighted": 0.8305,
    "per_class": {
      "CMS1": {"precision": 0.8571, "recall": 0.8571, "f1": 0.8571, "support": 14},
      "CMS2": {"precision": 0.8750, "recall": 0.9310, "f1": 0.9032, "support": 29},
      "CMS3": {"precision": 0.7500, "recall": 0.4545, "f1": 0.5455, "support": 11},
      "CMS4": {"precision": 0.8421, "recall": 0.8421, "f1": 0.8421, "support": 20}
    }
  }
}
```

## Conclusió dels experiments

El pipeline permet entrenar i avaluar models de classificació CMS de manera homogènia. Logistic Regression i SVM lineal actuen com els models amb millor rendiment global en aquesta configuració, mentre que Random Forest ofereix resultats propers. La principal limitació observada és el rendiment menor en CMS3, associat al desbalanceig i a la dificultat pròpia del subtipus.
