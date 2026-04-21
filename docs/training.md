# Etapa 4: Entrenament de models

## Objectiu

Entrenar tres classificadors de machine learning sobre les mateixes dades d'entrenament
i amb la mateixa seed, per garantir una **comparativa justa**. Cada model rep exactament
la mateixa matriu d'expressió (296 mostres × 15.625 gens) i les mateixes etiquetes CMS.

L'avaluació del rendiment sobre el conjunt de test es fa a l'**etapa 6** — aquí
només s'entrena i es guarden els models.

---

## Artefactes d'aquesta etapa

| Artefacte | Funció |
|-----------|--------|
| `src/models.py` | Funcions reutilitzables de càrrega de dades i entrenament |
| `scripts/train.py` | Script d'orquestració (punt d'entrada) |
| `data/models/*.joblib` | Models entrenats — **no al repositori git** (regenerables) |
| `data/models/training_log.json` | Hiperparàmetres, temps d'entrenament i sanity check |

---

## Per què tres models?

Cada model representa una família d'algorismes diferent. Usar-los en paral·lel
permet comparar estratègies d'aprenentatge i veure quina s'adapta millor al problema.

| Model | Família | Justificació |
|-------|---------|-------------|
| **Logistic Regression** | Lineal | Baseline interpretable. Si un model lineal simple funciona bé, el problema té una estructura lineal clara. Ràpid d'entrenar i fàcil d'interpretar (els coeficients indiquen quins gens discriminen). |
| **Random Forest** | Ensemble d'arbres | Robust davant de dades amb moltes dimensions i interaccions no lineals. La importància de cada gen (feature importance) permet identificar gens discriminatius. |
| **SVM** | Kernel | Especialment eficaç quan el nombre de característiques supera el nombre de mostres (15.625 gens > 296 mostres). El kernel lineal troba l'hiperplà que maximitza el marge entre classes. |

---

## Disseny experimental

### Mateixa seed, mateixa partició

Els tres models usen `random_state=42`. Combinat amb el split estratificat de
l'etapa 2 (també seed=42), qualsevol persona que executi el pipeline obtindrà
exactament els mateixos models i resultats.

### `class_weight='balanced'`

El dataset té un desbalanceig conegut:

| Subtipus | Train | % |
|----------|-------|---|
| CMS2 | 116 | 39% |
| CMS4 | 80  | 27% |
| CMS1 | 57  | 19% |
| CMS3 | 43  | 15% |

Sense correcció, un model que sempre predigui CMS2 tindria un **39% d'accuracy
sense aprendre res**. L'opció `class_weight='balanced'` fa que sklearn pondera
automàticament cada classe inversament proporcional a la seva freqüència:

```
pes_CMS2 = 296 / (4 × 116) ≈ 0.64
pes_CMS3 = 296 / (4 × 43)  ≈ 1.72
```

Això força el model a prestar més atenció als subtipus minoritaris (CMS3, CMS1).

### Dades sense reducció de dimensionalitat

Els models reben les **15.625 dimensions** originals de l'etapa 2, no les components
PCA de l'etapa 3. La reducció de dimensionalitat de l'etapa 3 és exclusivament per
visualització. Entrenar directament sobre els gens permet:

- Calcular importància de gens (Random Forest)
- Interpretar coeficients (Logistic Regression)
- Aprofitar la geometria d'alta dimensió (SVM)

---

## Detalls per model

### Logistic Regression

| Hiperparàmetre | Valor | Justificació |
|---------------|-------|-------------|
| `solver` | `lbfgs` | Eficient per a multiclasse, estàndard per L2 |
| `multi_class` | `multinomial` | Distribució conjunta sobre les 4 classes (no one-vs-rest) |
| `max_iter` | `5000` | El default (100) no convergeix amb 15.625 features |
| `class_weight` | `balanced` | Corregeix el desbalanceig de classes |

### Random Forest

| Hiperparàmetre | Valor | Justificació |
|---------------|-------|-------------|
| `n_estimators` | `500` | Suficients arbres per a estimacions estables; més no millora significativament |
| `max_features` | `sqrt` | Estàndard per classificació: considera √15.625 ≈ 125 gens per split |
| `n_jobs` | `-1` | Paral·lelitza la construcció dels arbres (tots els nuclis). Determinista amb `random_state` fix |
| `class_weight` | `balanced` | Corregeix el desbalanceig |

### SVM (Support Vector Machine)

| Hiperparàmetre | Valor | Justificació |
|---------------|-------|-------------|
| `kernel` | `linear` | Quan n_features >> n_samples, el kernel lineal és suficient i molt més ràpid que RBF |
| `probability` | `True` | Activa Platt scaling per obtenir `predict_proba`, necessari per a corbes ROC a l'etapa 6 |
| `class_weight` | `balanced` | Corregeix el desbalanceig |
| `max_iter` | `-1` | Il·limitat (default SVC): deixa que l'optimitzador convergeixi |

---

## Estructura de sortida

Els models es guarden a `data/models/` (exclòs del repositori via `.gitignore`):

```
data/models/
├── logistic_regression.joblib   ← model serialitzat amb joblib
├── random_forest.joblib
├── svm.joblib
└── training_log.json            ← hiperparàmetres + temps + sanity check
```

El fitxer `training_log.json` documenta exactament com s'han entrenat els models:

```json
{
  "timestamp": "2026-04-02T...",
  "random_seed": 42,
  "train_samples": 296,
  "train_genes": 15625,
  "cms_distribution_train": {"CMS1": 57, "CMS2": 116, "CMS3": 43, "CMS4": 80},
  "models": {
    "logistic_regression": {
      "hyperparameters": {"solver": "lbfgs", "max_iter": 5000, ...},
      "train_accuracy": 0.9932,
      "training_time_seconds": 12.4,
      "output_file": "logistic_regression.joblib"
    }
  }
}
```

---

## Com executar

```bash
# Entrenar tots els models (mode per defecte)
python scripts/train.py

# Veure configuració sense entrenar
python scripts/train.py --dry-run

# Entrenar només un model
python scripts/train.py --model random_forest
python scripts/train.py --model logistic_regression
python scripts/train.py --model svm

# Especificar directoris manualment
python scripts/train.py --processed-dir data/processed --output-dir data/models
```

---

## Sanity check: precisió en entrenament

El log inclou la **precisió sobre el conjunt d'entrenament** per a cada model.
Valors típics esperats:

| Model | Train accuracy esperada |
|-------|------------------------|
| Logistic Regression | 0.85 – 0.95 |
| Random Forest | 0.98 – 1.00 |
| SVM | 0.90 – 0.98 |

Una train accuracy alta **no implica overfitting** per si sola — és esperable quan
el model ha après els patrons del conjunt d'entrenament. L'overfitting es detecta
comparant train accuracy amb **test accuracy** (etapa 6). Si la diferència és gran
(p.ex. train=0.99, test=0.60), el model no generalitza.

---

## Reproducibilitat

Els models **no es guarden al repositori** perquè es poden regenerar en minuts:

```bash
python scripts/preprocess.py   # genera data/processed/ (si no existeix)
python scripts/train.py        # genera data/models/
```

Dues execucions consecutives amb la mateixa seed produiran fitxers `.joblib`
idèntics byte per byte.
