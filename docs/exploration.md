# Etapa 3: Reducció de dimensionalitat i exploració de dades

## Objectiu

> **Important:** aquesta etapa és d'anàlisi, no de transformació. Les dades que
> entraran als models segueixen sent les **15.625 dimensions** de l'etapa 2.
> PCA i UMAP s'usen aquí exclusivament per visualitzar — no modifiquen res.

Abans d'entrenar qualsevol model, explorar les dades permet respondre tres preguntes:

1. **El preprocessament és correcte?** — Verificar que les dimensions, els valors i les distribucions
   coincideixen amb el que esperem.
2. **Els subtipus CMS es poden separar?** — Si l'expressió gènica discrimina bé els 4 subtipus,
   els models de ML tindran feina fàcil. Si se superposen molt, la tasca serà difícil.
3. **Hi ha problemes no detectats?** — Outliers, mostres amb perfils estranys, o biaixos
   tècnics que el preprocessament no hagi eliminat.

L'exploració es fa **abans** d'entrenar. Les decisions que es prenen aquí
(p.ex. quines mètriques usar per avaluar) influencien el disseny de les etapes següents.

---

## Artefactes d'aquesta etapa

| Artefacte | Funció |
|-----------|--------|
| `src/dimensionality_reduction.py` | Funcions reutilitzables de PCA i UMAP |
| `notebooks/data_exploration.ipynb` | EDA interactiu pas a pas |

---

## Reducció de dimensionalitat: per què?

Les dades processades tenen **15.625 dimensions** (una per gen). Cap humà pot visualitzar
15.625 dimensions directament. La reducció de dimensionalitat transforma les dades en 2 o 3
dimensions conservant la màxima informació possible, permetent visualitzar-les.

Aquí usem dues tècniques complementàries:

### PCA (Principal Component Analysis)

PCA és una transformació **lineal** que troba les direccions (components) on les dades
varien més. Cada component principal és una combinació de tots els gens.

**Per al nostre projecte:**
- Fixa PCA sobre les dades d'**entrenament** (fit on train)
- Aplica la mateixa transformació al **test** (transform on test)
- Visualitza PC1 vs PC2 acolorit per subtipus CMS

Si els 4 subtipus formen grups separats en l'espai PC1-PC2, significa que l'expressió
gènica és un bon discriminador i que els models de classificació tindran un senyal clar.

**Scree plot:** gràfic que mostra quanta variança del dataset original captura cada
component. Ens indica quants components fan falta per capturar el 80% de la informació.

**Loadings:** per a cada component, els gens amb loading alt en valor absolut
són els que més contribueixen a aquella direcció. Permeten interpretar biològicament
la separació (ex: si PC1 és dominat per gens del sistema immunitari, pot coincidir
amb la separació CMS1 — que és el subtipus immunoactiu).

### UMAP (Uniform Manifold Approximation and Projection)

UMAP és una tècnica **no lineal** especialment bona per visualitzar clústers.
A diferència de PCA, no intenta maximitzar la variança global sinó preservar
les relacions de veïnatge local entre mostres.

| | PCA | UMAP |
|-|-----|------|
| Tipus | Lineal | No lineal |
| Interpretable | Sí (loadings de gens) | No directament |
| Ràpid | Molt | Moderat |
| Bon per a... | Anàlisi + exploració | Visualització de clústers |

UMAP es fa sobre les dades de train, sense separar train/test, perquè és
exclusivament per a **visualització** — no s'usa com a input dels models.

---

## Implicació per als models

### Desbalanceig de classes

El dataset TCGA-COAD té un desbalanceig conegut:

| Subtipus | Mostres | % |
|----------|---------|---|
| CMS2 | 145 | 39% |
| CMS4 | 100 | 27% |
| CMS1 | 71 | 19% |
| CMS3 | 54 | 15% |

Un model que sempre predís CMS2 tindria un **39% d'accuracy sense aprendre res**.
Per aquest motiu, a l'avaluació (etapa 6) s'usa:

- **F1 macro** — mitjana del F1 de cada classe, independentment de la mida
- **Matriu de confusió** — per veure quins subtipus s'encerten i quins es confonen

### Separabilitat observada

La qualitat de la separació en PCA/UMAP anticipa la dificultat de la classificació:

- **Grups ben separats** → els models haurien d'obtenir F1 > 0.8
- **Grups solapats** → la tasca és difícil, especialment per als subtipus minoritaris

---

## Com executar l'exploració

```bash
# Assegurar-se que les dades processades existeixen
python scripts/preprocess.py

# Obrir el notebook (des de l'arrel del projecte)
jupyter lab notebooks/data_exploration.ipynb
```

El notebook guarda automàticament els gràfics generats a `figures/` per incloure'ls
a la memòria del TFG.

---

## Estructura del mòdul `src/dimensionality_reduction.py`

```python
fit_pca(X_train, n_components=50)          # Ajusta PCA sobre train
apply_pca(pca, X)                          # Projecta dades (train o test)
plot_explained_variance(pca)               # Scree plot
plot_pca_scatter(coords, labels)           # Scatter PC1 vs PC2
plot_top_genes(pca, gene_names, component) # Gens amb més loading
plot_umap_scatter(X, labels)               # Projecció UMAP
```

Totes les funcions de plot accepten un paràmetre opcional `output_path` per guardar
la figura directament a disc.
