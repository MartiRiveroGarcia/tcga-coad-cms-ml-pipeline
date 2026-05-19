# Glossari

Aquest glossari recull els termes biològics, estadístics i d'aprenentatge automàtic emprats
al llarg del projecte. Cada entrada inclou una definició formal, el seu significat concret
en el context TCGA-COAD, i, quan és útil, una il·lustració conceptual.

---

## Dades i biologia

### RNA-seq (RNA sequencing)
Tecnologia experimental que mesura el nivell d'expressió de cada gen en una mostra de teixit.
El resultat és una matriu de comptatges on cada fila és un gen i cada columna és un pacient.
**Al nostre projecte:** 370 pacients × ~60.000 gens (comptatges *STAR-Counts unstranded*);
reduïts a 15.625 gens proteics i normalitzats en log₂ per al modelatge.

### Expressió gènica
Mesura de quant s'activa un gen en una cèl·lula o teixit. Un gen "molt expressat" produeix
moltes còpies de proteïna; un gen "poc expressat" en produeix poques o cap.
**Al nostre projecte:** representada com a valors log₂(comptatge + 1), rang [0, 20.71].

### Gen / Feature
En biologia: segment d'ADN que codifica per a una proteïna.
En aprenentatge automàtic: variable d'entrada (*feature*) del model. Cada gen és una dimensió
de l'espai de característiques.
**Al nostre projecte:** 15.625 gens proteics = 15.625 dimensions per mostra.

### CMS (Consensus Molecular Subtypes)
Classificació del càncer colorectal en quatre subtipus moleculars definits per Guinney et al.
(2015, *Nature Medicine*) a partir de l'expressió gènica de 4.151 tumors.

| Subtipus | Nom | Característiques principals | Freqüència (TCGA-COAD) |
|:--------:|-----|---------------------------|:----------------------:|
| **CMS1** | MSI Immune | Hipermutació, alta activitat immune | 19% |
| **CMS2** | Canonical | Activació WNT i MYC | 39% |
| **CMS3** | Metabolic | Desregulació metabòlica, perfil mixt | 15% |
| **CMS4** | Mesenchymal | Activació TGF-β, pitjor pronòstic | 27% |

**Al nostre projecte:** etiquetes de supervisió per als 370 pacients del dataset.

### TCGA (The Cancer Genome Atlas)
Projecte de recerca dels NIH (National Institutes of Health) que ha recollit i seqüenciat dades
genòmiques de milers de tumors de 33 tipus de càncer. Les dades son d'accés públic.
**Al nostre projecte:** TCGA-COAD conté dades RNA-seq de càncer colorectal (*colon adenocarcinoma*).

### GDC (Genomic Data Commons)
Portal web del NCI (*National Cancer Institute*) des d'on es descarreguen les dades de TCGA.
**Al nostre projecte:** font de descàrrega dels 483 fitxers RNA-seq originals.

### GENCODE
Base de dades d'anotació del genoma humà que classifica cada gen per tipus
(proteic, lncRNA, pseudogen, etc.). Versió 36 usada en aquest projecte.
**Al nostre projecte:** font per al filtratge de gens protein-coding (19.962 de 60.660 totals).

### FFPE (Formalin-Fixed Paraffin-Embedded)
Mètode de preservació de teixit tumoral que usa formalina. Produeix una degradació parcial
del RNA, generant biaixos tècnics incompatibles amb teixit congelat fresc.
**Al nostre projecte:** 13 mostres FFPE eliminades durant el preprocessament.

### Data leakage
Situació en la qual informació del conjunt de test influeix (directament o indirecta)
en les decisions de preprocessament o entrenament. Produeix mètriques d'avaluació
artificalment optimistes que no reflecteixen el rendiment real.
**Al nostre projecte:** per evitar-ho, el filtratge de gens i la transformació log₂ es
calculen exclusivament sobre les 296 mostres d'entrenament i s'apliquen posteriorment al test.

---

## Preparació de dades

### Preprocessament
Conjunt de transformacions que converteixen les dades brutes en un format adequat per al
modelatge. Inclou neteja, normalització i selecció de variables.
**Al nostre projecte:** 9 passos documentats a `scripts/preprocess.py` i `docs/pipeline.md`.

### Filtratge de gens
Eliminació dels gens amb nivells d'expressió massa baixos o massa variables per ser
informatius. Redueix el soroll i la dimensionalitat.
**Al nostre projecte:** criteri — gen retingut si ≥20% de les mostres de train (≥60/296)
tenen comptatge ≥10. Resultat: 15.625 de 19.962 gens proteics.

### Normalització log₂
Transformació $x' = \log_2(x + 1)$ aplicada als comptatges RNA-seq. Comprima el rang de valors
(evita que gens molt expressats dominin el model) i aproxima una distribució normal.
El +1 evita $\log_2(0) = -\infty$.
**Al nostre projecte:** rang resultant [0.00, 20.71].

### Train/test split (divisió entrenament/test)
Partició del dataset en dos subconjunts mutament excloents:
- **Conjunt d'entrenament (train):** usat per ajustar els paràmetres del model.
- **Conjunt de test:** usat exclusivament per avaluar el rendiment final; cap model
  el veu durant l'entrenament.
**Al nostre projecte:** 296 mostres train / 74 test (80/20), divisió estratificada, seed=42.

### Divisió estratificada (stratified split)
Variant del train/test split que garanteix que la proporció de cada classe es manté
en ambdós conjunts. Essencial quan hi ha classes minoritàries.
**Al nostre projecte:** garanteix que CMS3 apareix tant al train (43/296=15%) com al test
(11/74=15%), evitant que el test set no contingui mostres d'un subtipus.

### Desbalanceig de classes (class imbalance)
Situació en la qual les classes no estan representades de manera equitativa al dataset.
Pot fer que el model ignori les classes minoritàries.
**Al nostre projecte:** CMS2=39%, CMS4=27%, CMS1=19%, CMS3=15%.
Mitigat amb `class_weight='balanced'`.

### Bootstrap
Tècnica de mostratge amb reemplaçament: donat un conjunt de N elements, es seleccionen
N elements aleatòriament permetent repeticions. Alguns elements apareixeran múltiples
vegades; d'altres no apareixeran.
**Al nostre projecte:** cada arbre del Random Forest s'entrena sobre un bootstrap del
conjunt de train (296 mostres amb reemplaçament → ~63% úniques per arbre).

---

## Mètriques d'avaluació

### Accuracy (precisió global)
Fracció de mostres classificades correctament: $\text{Accuracy} = \frac{\text{encerts}}{\text{total}}$.
**Limitació:** pot ser enganyosa amb classes desbalancejades. Un model que sempre prediu
CMS2 (majoritari) obtindria 39% d'accuracy sense aprendre res.
**Al nostre projecte:** LR=0.9595, RF=0.8514, SVM=0.9595 (sobre 74 mostres de test).

### True Positive (TP), False Positive (FP), False Negative (FN)
Per a una classe $k$ (p. ex. CMS3):
- **TP**: mostres CMS3 reals classificades com CMS3 → encerts
- **FP**: mostres d'altres subtipus classificades com CMS3 → falsos alarmes
- **FN**: mostres CMS3 reals classificades com un altre subtipus → casos perduts

### Precision (valor predictiu positiu)
$\text{Precision}_k = \frac{TP_k}{TP_k + FP_k}$

Dels casos que el model prediu com a classe $k$, quants ho son realment.
Alta precision → poques falses alarmes.
**Al nostre projecte (LR, CMS3):** Precision=1.0 — el model no dona cap fals positiu CMS3.

### Recall (sensibilitat)
$\text{Recall}_k = \frac{TP_k}{TP_k + FN_k}$

Dels casos reals de classe $k$, quants detecta el model.
Alt recall → poques deteccions perdudes.
**Al nostre projecte (LR, CMS3):** Recall=0.909 — el model detecta 10 de 11 casos CMS3 reals.

### F1-score
Mitjana harmònica de precision i recall: $F1_k = \frac{2 \cdot P_k \cdot R_k}{P_k + R_k}$.
Rang [0, 1]; valor 1 = classificació perfecta.
La mitjana harmònica penalitza desequilibris entre P i R: un F1 alt requereix ambdós
valors elevats simultàniament.

### F1 macro
Mitjana aritmètica dels F1-scores de totes les classes, sense ponderar pel nombre de mostres.
Tractament equitatiu per a totes les classes, independentment de la seva freqüència.
**Recomanat** quan totes les classes son igualment importants (cas del nostre projecte).
**Al nostre projecte (LR):** F1 macro = 0.9540.

### F1 weighted
Mitjana ponderada dels F1-scores, on el pes de cada classe és proporcional al seu
nombre de mostres (*support*). Classes majoritàries contribueixen més.
**Al nostre projecte (LR):** F1 weighted = 0.9594 (lleugerament superior al macro perquè
les classes majoritàries, CMS2 i CMS4, ten un F1 molt elevat).

### Support
Nombre de mostres de cada classe al conjunt d'avaluació.
**Al nostre projecte (test set):** CMS1=14, CMS2=29, CMS3=11, CMS4=20.

### Matriu de confusió
Taula quadrada $K \times K$ (on $K$ és el nombre de classes) que mostra, per a cada classe
real (files), com s'han distribuït les prediccions del model (columnes).
- **Diagonal:** encerts (TP per a cada classe).
- **Fora de la diagonal:** errors (indica quins subtipus es confonen).
**Al nostre projecte:** matriu 4×4 (CMS1–CMS4). Disponible a `figures/confusion_matrix_*.png`.

### ROC / AUC
**ROC** (*Receiver Operating Characteristic*): corba que representa la taxa de vertaders
positius (recall) vs. la taxa de falsos positius per a tots els llindars possibles.
**AUC** (*Area Under the Curve*): àrea sota la corba ROC. Rang [0.5, 1]; valor 1 = perfect.
**Al nostre projecte:** no calculat en l'etapa actual; `probability=True` als models
ho deixa preparat per a una anàlisi futura.

---

## Models d'aprenentatge automàtic

### Classificació supervisada
Tasca d'aprenentatge automàtic on el model aprèn a assignar etiquetes predefinides
a partir d'exemples etiquetats (parells entrada–etiqueta).
**Al nostre projecte:** entrada = vector de 15.625 valors d'expressió gènica; etiqueta = CMS1–4.

### Hiperplà
En un espai de $d$ dimensions, un hiperplà és un subespai de $d-1$ dimensions que
el divideix en dos semiesais. En 2D és una recta; en 3D és un plà; en 15.625D és un
objecte abstracte equivalent.
La Regressió Logística i el SVM troben hiperplans que separen les classes en $\mathbb{R}^{15625}$.

### Regressió Logística (Logistic Regression, LR)
Model lineal de classificació que assigna pesos $w_{kj}$ a cada feature (gen) per a cada classe $k$.
La predicció és la classe amb la puntuació ponderada més alta, convertida en probabilitats
per la funció softmax.
**Al nostre projecte:** solver=lbfgs, max_iter=5000, class_weight='balanced', random_state=42.
Accuracy test = 0.9595, F1 macro = 0.9540.

### Softmax
Funció que converteix un vector de puntuacions reals en una distribució de probabilitats
sumant 1: $\text{softmax}(\mathbf{z})_k = e^{z_k} / \sum_m e^{z_m}$.
Assegura que les probabilitats predites per a les 4 classes sumen exactament 1.

### Regularització L2 (Ridge)
Terme de penalització $\lambda \|\mathbf{w}\|^2$ afegit a la funció de pèrdua durant l'entrenament.
Evita que els pesos creixin massa (sobreajustament). La Regressió Logística d'sklearn usa L2
per defecte (paràmetre $C=1.0$, on $C = 1/\lambda$).

### Random Forest (RF)
Mètode d'*ensemble* que construeix múltiples arbres de decisió, cadascun entrenat sobre
un bootstrap del dataset i usant un subconjunt aleatori de features en cada divisió.
La predicció final és per majoria de vots.
**Al nostre projecte:** 500 arbres, max_features='sqrt' (~125 gens/divisió), n_jobs=-1.
Accuracy test = 0.8514, F1 macro = 0.8245.

### Arbre de decisió (Decision Tree)
Model que aplica successions de decisions binàries (gen $j$ > llindar?) per classificar
una mostra. Cada nus interior és una decisió; cada fulla és una predicció.

### Impuresa de Gini (Gini Impurity)
Criteri usat per seleccionar la millor divisió en un nus d'un arbre de decisió:
$\text{Gini}(t) = 1 - \sum_k p_k^2$, on $p_k$ és la proporció de mostres de la classe $k$ al nus $t$.
Gini=0 indica un nus pur (totes les mostres de la mateixa classe).

### Feature importance (RF)
Mesura de la utilitat de cada gen en la classificació del Random Forest: promig de la
reducció d'impuresa Gini produïda per les divisions sobre aquell gen, als 500 arbres.
Rang [0, 1]; la suma de totes les importàncies és 1.

### SVM (Support Vector Machine)
Model que busca l'hiperplà de separació entre classes que maximitza el marge —
la distància entre l'hiperplà i els punts de train més propers (*vectors de suport*).
**Al nostre projecte:** kernel=linear, probability=True (Platt scaling), class_weight='balanced'.
Accuracy test = 0.9595, F1 macro = 0.9540 (idèntic a LR).

### Vectors de suport (Support Vectors)
Subconjunt de les mostres d'entrenament que es troben sobre o dins del marge de l'SVM.
Son els únics punts que defineixen l'hiperplà: eliminar qualsevol altra mostra no
modificaria el classificador.
En espais d'alta dimensió, la proporció de vectors de suport sol ser elevada.

### Kernel (SVM)
Funció que defineix la mesura de similitud entre dues mostres en l'espai de features.
**Kernel lineal:** $K(\mathbf{x}_i, \mathbf{x}_j) = \mathbf{x}_i \cdot \mathbf{x}_j$ (producte escalar).
Adequat quan les dades son linealment separables, com en el cas d'alta dimensió del nostre projecte.

### Platt scaling
Mètode de calibració que converteix les puntuacions de decisió del SVM
(distàncies a l'hiperplà) en probabilitats [0, 1] mitjançant una regressió logística
entrenada per cross-validació interna. Actiu amb `probability=True`.

### class_weight='balanced'
Paràmetre d'sklearn que ajusta el pes de cada mostra durant l'entrenament per compensar
el desbalanceig de classes: $w_k = \frac{N}{K \cdot N_k}$, on $N$ és el total de mostres,
$K$ el nombre de classes i $N_k$ el nombre de mostres de la classe $k$.
**Al nostre projecte:** pes(CMS3) ≈ 1.72 × pes(CMS2) ≈ 2.71 × pes normal.

### Sobreajustament (Overfitting)
Fenomen en el qual el model aprèn massa bé les dades d'entrenament (inclòs el soroll)
i perd capacitat de generalitzar a dades noves. Indicatiu: accuracy train >> accuracy test.
**Al nostre projecte:** tots tres models obtenen train accuracy=100% (esperat en alta dimensió);
els models lineals generalitzen bé (test~=96%) però el RF generalitza menys bé (test~=85%).

### Alta dimensió (n_features >> n_samples)
Règim en el qual el nombre de variables d'entrada supera el nombre de mostres.
Propietat clau: en alta dimensió, gairebé sempre existeix un hiperplà que separa
linealment qualsevol conjunt de classes, cosa que beneficia els models lineals.
**Al nostre projecte:** 15.625 gens > 296 mostres → règim d'alta dimensió.

### Coeficients del model (LR/SVM)
Pesos $w_{kj}$ apresos durant l'entrenament, un per a cada combinació gen–classe.
Indiquen la contribució de cada gen a la predicció d'un subtipus: coeficient positiu alt
→ el gen és evidència a favor d'aquell subtipus; coeficient negatiu → en contra.
**Al nostre projecte:** LR té 15.625 × 4 = 62.500 coeficients; SVM en té el mateix nombre
en mode One-vs-Rest.

### One-vs-Rest (OvR)
Estratègia de multiclasse que entrena un classificador binari per a cada classe
(classe $k$ vs. tota la resta). La predicció final és la classe amb la puntuació més alta.
**Al nostre projecte:** el SVM d'sklearn usa OvR per defecte per als 4 subtipus CMS.
