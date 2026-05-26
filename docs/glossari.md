# Glossari

## Bioinformàtica i dades genòmiques

### RNA-seq

Tècnica de seqüenciació utilitzada per quantificar l’expressió gènica. En aquest projecte, les dades RNA-seq s’utilitzen per representar l’activitat dels gens en mostres de càncer colorectal.

### Expressió gènica

Mesura de l’activitat d’un gen en una mostra biològica. En el pipeline, cada mostra es representa mitjançant un conjunt de valors d’expressió gènica.

### Matriu d’expressió

Taula on les files o columnes representen mostres i gens. En aquest projecte, aquesta matriu és l’entrada principal dels models d’aprenentatge automàtic.

### Gen

Unitat d’informació genètica que pot estar associada a la producció d’ARN o proteïnes. En el projecte, els gens actuen com a variables d’entrada dels models.

### Gen protein-coding

Gen que codifica una proteïna. El preprocessament filtra els gens per conservar els gens codificants i reduir soroll en les dades.

### Comptatge gènic

Valor numèric que representa el nombre de lectures associades a un gen en una mostra RNA-seq.

### STAR-Counts

Fitxers de comptatge generats a partir del workflow STAR. Aquests fitxers contenen valors d’expressió gènica ja quantificats i són l’entrada inicial del pipeline.

### FASTQ

Format de fitxer que conté lectures crues de seqüenciació. Aquest projecte no treballa amb FASTQ perquè parteix de dades RNA-seq ja quantificades.

### Alineament

Procés bioinformàtic que assigna lectures de seqüenciació a una regió del genoma o transcriptoma de referència. Aquest pas queda fora de l’abast del pipeline.

### Normalització

Procés que redueix diferències tècniques entre mostres per fer-les més comparables. En aquest projecte, el pipeline parteix de dades ja quantificades i aplica transformacions posteriors durant el preprocessament.

### Transformació logarítmica

Transformació numèrica aplicada per reduir l’escala dels comptatges i suavitzar valors molt grans. En el projecte s’utilitza `log2(x + 1)`.

### Batch effect

Variabilitat tècnica no desitjada produïda per diferències entre lots, laboratoris, protocols o plataformes. Pot afectar l’anàlisi si no es controla adequadament.

---

## Càncer colorectal i subtipus CMS

### Càncer colorectal

Tipus de càncer que afecta el còlon o el recte. En aquest projecte, s’estudien mostres de càncer de còlon de la cohort TCGA-COAD.

### TCGA-COAD

Cohort de The Cancer Genome Atlas corresponent a mostres de colon adenocarcinoma. És la cohort utilitzada com a font de dades principal del projecte.

### CMS

Sigla de Consensus Molecular Subtypes. És una classificació molecular del càncer colorectal basada en perfils transcriptòmics.

### Subtipus molecular

Grup de mostres que comparteixen patrons moleculars similars. En el projecte, els subtipus moleculars corresponen a CMS1, CMS2, CMS3 i CMS4.

### CMS1

Subtipus CMS associat habitualment a característiques immunes i inestabilitat de microsatèl·lits. En el pipeline, CMS1 és una de les classes de classificació.

### CMS2

Subtipus CMS sovint descrit com a canònic o epitelial. En el pipeline, CMS2 és una de les classes de classificació.

### CMS3

Subtipus CMS associat a signatures metabòliques. En el pipeline, CMS3 és una de les classes de classificació i és la classe amb menys mostres en el conjunt utilitzat.

### CMS4

Subtipus CMS associat a característiques mesenquimals i estromals. En el pipeline, CMS4 és una de les classes de classificació.

### Etiqueta CMS

Classe assignada a una mostra segons el seu subtipus CMS. Aquestes etiquetes s’utilitzen com a variable objectiu durant l’entrenament supervisat.

---

## Fonts de dades i repositori

### GDC

Sigla de Genomic Data Commons. És el portal des d’on es descarreguen els fitxers RNA-seq utilitzats en el projecte.

### Manifest GDC

Fitxer que conté els identificadors dels fitxers que cal descarregar del GDC. El pipeline utilitza aquest manifest per reproduir la descàrrega de dades.

### Sample sheet

Fitxer de metadades que descriu les mostres i els fitxers associats. S’utilitza per relacionar fitxers descarregats amb informació de mostra.

### Synapse

Plataforma utilitzada com a font externa de recursos relacionats amb les etiquetes CMS. En el projecte, la informació procedent de Synapse s’utilitza durant el preprocessament.

### Metadades

Informació descriptiva sobre mostres, fitxers o etiquetes. En el repositori, les metadades es guarden a `data/metadata/`.

### Dades raw

Dades originals descarregades abans del preprocessament. En el projecte es guarden a `data/raw/gdc/` i no es versionen.

### Dades processades

Dades generades després del preprocessament i preparades per entrenar models. Es guarden a `data/processed/`.

### Artefacte

Fitxer generat durant l’execució del pipeline, com ara una matriu processada, un model entrenat, un informe de mètriques o una figura.

### Fitxer versionat

Fitxer inclòs al control de versions del repositori. En aquest projecte es versionen fitxers petits i necessaris per reconstruir el procés, com manifests i metadades.

### Fitxer no versionat

Fitxer exclòs del control de versions perquè és gran o regenerable. Inclou dades raw, dades processades, models, resultats i figures generades.

---

## Pipeline i execució

### Pipeline

Seqüència ordenada d’etapes que transforma les dades inicials en resultats finals. En aquest projecte, el pipeline inclou descàrrega, preprocessament, entrenament i avaluació.

### Etapa productiva

Etapa que genera fitxers utilitzats per una etapa posterior del pipeline. En aquest projecte, les etapes productives són descàrrega, preprocessament, entrenament i avaluació.

### Notebook

Document interactiu que combina codi, resultats i explicacions. En el projecte, els notebooks s’utilitzen per exploració i anàlisi, però no substitueixen els scripts productius.

### Script

Fitxer executable que actua com a punt d’entrada d’una etapa del pipeline. Els scripts es troben al directori `scripts/`.

### Mòdul

Fitxer de codi reutilitzable que conté funcions utilitzades pels scripts o notebooks. Els mòduls es troben al directori `src/`.

### Descàrrega

Primera etapa del pipeline. Obté els fitxers RNA-seq del GDC a partir del manifest guardat a `data/metadata/`.

### Preprocessament

Etapa que transforma els fitxers descarregats en matrius preparades per a l’entrenament. Inclou filtratge, unió amb etiquetes CMS, separació train/test i transformació de valors.

### Entrenament

Etapa que ajusta els models d’aprenentatge automàtic amb les dades d’entrenament.

### Avaluació

Etapa que calcula el rendiment dels models sobre el conjunt de test.

### `gdc-client`

Eina de línia de comandes utilitzada per descarregar fitxers del Genomic Data Commons.

### `environment.yml`

Fitxer que defineix l’entorn Conda del projecte i les dependències necessàries.

### Conda

Gestor d’entorns i paquets utilitzat per crear un entorn d’execució reproduïble.

### `joblib`

Llibreria utilitzada per guardar i carregar models entrenats en format `.joblib`.

---

## Preprocessament i partició de dades

### Train

Conjunt de dades utilitzat per entrenar els models.

### Test

Conjunt de dades reservat per avaluar els models després de l’entrenament.

### Split train/test

Separació del dataset en conjunt d’entrenament i conjunt de test.

### Split estratificat

Separació train/test que manté proporcions similars de cada classe en els dos conjunts.

### Data leakage

Problema que es produeix quan informació del conjunt de test influeix en l’entrenament o el preprocessament. Pot provocar una estimació massa optimista del rendiment.

### Seed

Valor fix utilitzat per controlar processos aleatoris i facilitar que els resultats siguin reproduïbles.

### `random_state`

Paràmetre utilitzat en algunes llibreries per fixar la seed d’un procés aleatori.

### Deduplicació

Procés d’eliminar mostres duplicades o repetides per evitar inconsistències en el dataset.

### Files QC

Files de control de qualitat presents en alguns fitxers d’expressió. S’eliminen durant el preprocessament perquè no representen gens utilitzables com a variables del model.

### Filtratge de gens

Procés d’eliminar gens que no compleixen determinats criteris, com ara tenir comptatges massa baixos.

---

## Aprenentatge automàtic

### Aprenentatge automàtic

Conjunt de tècniques que permeten entrenar models perquè aprenguin patrons a partir de dades.

### Aprenentatge supervisat

Tipus d’aprenentatge automàtic en què el model s’entrena amb exemples que tenen una etiqueta coneguda.

### Classificació

Tasca d’aprenentatge supervisat en què el model assigna una classe a cada mostra.

### Variable d’entrada

Característica utilitzada pel model per fer una predicció. En aquest projecte, les variables d’entrada són valors d’expressió gènica.

### Variable objectiu

Classe que el model ha d’aprendre a predir. En aquest projecte, la variable objectiu és el subtipus CMS.

### Model

Algorisme entrenat per predir etiquetes CMS a partir de dades d’expressió gènica.

### Logistic Regression

Model lineal de classificació utilitzat com a baseline. En el projecte s’utilitza per predir subtipus CMS.

### Random Forest

Model d’ensemble format per múltiples arbres de decisió. En el projecte s’utilitza com a alternativa no lineal.

### SVM

Sigla de Support Vector Machine. Model de classificació basat en la separació de classes mitjançant un hiperplà.

### SVM lineal

Variant de SVM amb kernel lineal. És útil en contextos amb moltes variables i relativament poques mostres.

### Hiperparàmetre

Paràmetre del model definit abans de l’entrenament, com ara `class_weight`, `max_iter` o `n_estimators`.

### `class_weight='balanced'`

Configuració que ajusta el pes de les classes segons la seva freqüència. Ajuda a reduir l’efecte del desbalanceig de classes.

### Baseline

Model de referència utilitzat per comparar el rendiment d’altres models.

---

## Mètriques i resultats

### Accuracy

Proporció de mostres classificades correctament respecte al total de mostres avaluades.

### Precision

Proporció de prediccions positives d’una classe que són correctes.

### Recall

Proporció de mostres reals d’una classe que el model detecta correctament.

### F1-score

Mitjana harmònica entre precision i recall. Resumeix l’equilibri entre totes dues mètriques.

### F1 macro

Mitjana del F1-score de totes les classes donant el mateix pes a cada classe. És útil quan les classes estan desbalancejades.

### F1 weighted

Mitjana del F1-score ponderada pel nombre de mostres de cada classe.

### Support

Nombre de mostres reals d’una classe en el conjunt d’avaluació.

### Matriu de confusió

Taula que compara les classes reals amb les classes predites pel model. La diagonal representa encerts i les cel·les fora de la diagonal representen errors.

### Benchmark

Comparació sistemàtica entre models utilitzant el mateix conjunt de dades, el mateix protocol i les mateixes mètriques.

### Generalització

Capacitat d’un model per fer bones prediccions sobre dades no utilitzades durant l’entrenament.

---

## Exploració i visualització

### Anàlisi exploratòria

Procés d’examinar les dades abans o després del preprocessament per entendre’n l’estructura, possibles patrons i limitacions.

### Reducció de dimensionalitat

Conjunt de tècniques que projecten dades amb moltes variables en un espai de menys dimensions per facilitar-ne la visualització.

### PCA

Sigla de Principal Component Analysis. Tècnica lineal de reducció de dimensionalitat que identifica direccions principals de variació.

### UMAP

Tècnica no lineal de reducció de dimensionalitat utilitzada per visualitzar estructures locals i possibles agrupacions.

### Clúster

Grup de mostres que apareixen properes en un espai de característiques o en una visualització reduïda.

### Visualització

Representació gràfica de dades o resultats per facilitar-ne la interpretació.

---

## Documentació i reproductibilitat

### Reproductibilitat

Capacitat de tornar a executar una anàlisi amb les mateixes dades, el mateix codi i el mateix entorn per obtenir els mateixos resultats.

### MkDocs

Eina utilitzada per generar la documentació tècnica del projecte a partir de fitxers Markdown.

### GitHub Pages

Servei utilitzat per publicar la documentació tècnica del projecte com a pàgina web.

### Markdown

Llenguatge de marcatge lleuger utilitzat per escriure les pàgines de documentació.

### Repositori

Espai on es desa el codi, la documentació i els fitxers versionats del projecte.

### Control de versions

Sistema que permet registrar canvis en el codi i la documentació. En aquest projecte es fa servir Git.

### Git

Eina de control de versions utilitzada per gestionar l’evolució del projecte.

### GitHub

Plataforma on s’allotja el repositori del projecte i des d’on es publica la documentació amb GitHub Pages.