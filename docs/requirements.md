# Requisits i criteris d’acceptació

## Requisits funcionals
RF1. El projecte ha de definir un flux complet (pipeline) des de dades tabulars fins a resultats d’avaluació.  
RF2. Ha de permetre executar i comparar diversos models sota el mateix split i preprocessament.  
RF3. Ha de generar mètriques i matrius de confusió per model.  
RF4. Ha de guardar resultats de cada execució en una estructura consistent (runs).

## Requisits no funcionals
RNF1. Reproduïbilitat: entorn definit (Conda) i instruccions d’execució clares.  
RNF2. Traçabilitat: guardar config/seed/versions o metadades mínimes per reconstruir un run.  
RNF3. Transparència: documentació didàctica a GitHub Pages (MkDocs).  
RNF4. Repo net: no incloure datasets grans; només manifests/metadades.

## Criteris d’acceptació (checks)
Veure la llista completa i marcable a: [KPI checklist](KPI_CHECKLIST.md)

Checks mínims:
- CA1. Es pot crear l’entorn des de `environment.yml` i fer imports bàsics.
- CA2. La documentació es construeix amb MkDocs i es publica a GitHub Pages.
- CA3. Existeix un manifest de dades versionat a `data/manifests/`.
- CA4. Existeix una estructura de resultats per “runs” (quan s’implementi el pipeline).
