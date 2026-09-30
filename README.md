#  Modélisation Hydrologique et Analyse des Risques de Ruissellement (Bassin du Hohrain, Rouffach)

![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Leaflet](https://img.shields.io/badge/Leaflet-199900?style=for-the-badge&logo=Leaflet&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)
![QGIS](https://img.shields.io/badge/QGIS-589632?style=for-the-badge&logo=QGIS&logoColor=white)

Ce dépôt GitHub regroupe les scripts et les chaînes de traitement géomatique et numérique développés dans le cadre de l'étude hydrologique du **bassin versant viticole du Hohrain (Rouffach, Haut-Rhin)**. L'objectif est d'évaluer la vulnérabilité du bassin face aux crues torrentielles, de tester la robustesse du bassin de rétention aval (1 500 m³) et de proposer des mesures d'aménagement par Solutions Fondées sur la Nature (SFN).

---

##  Architecture de la Chaîne de Traitement

Le projet repose sur un couplage d'outils rigoureux :
* **QGIS / PyQGIS :** Traitements géomatiques, intersection spatiale et automatisation de l'implantation des SFN.
* **GRASS GIS :** Modélisation géomorphologique (MNT 2m), conditionnement topographique (*Road Burning*) et routage D8.
* **Python :** Automatisation des flux, transcodage matriciel et standardisation des formats d'entrée/sortie.
* **Fortran 95 :** Moteur de calcul hydrodynamique distribué (`volume.exe`) résolvant la fonction de production SCS-CN et le routage maille à maille.
* **Excel :** Modèle matriciel semi-distribué (SCS-CN + hydrogramme de Nash) pour la validation des bilans massiques globaux.

---

##  Structure du Dépôt et Annexes Méthodologiques

Les scripts autonomes documentés dans le rapport sont organisés et nommés de la manière suivante :

### 1. Prétraitement et Préparation des Données Géographiques
* **`1_CODE_EXTRACTION_CHEMIN_ROUTE_PARCELLE.py`**  
  Filtre les entités correspondant aux voies de circulation et fossés à partir de la couche parcellaire source pour produire la couche vectorielle `route_chemin`.
* **`2_CODE_EXTENTION_COUCHE_SOL_BV.py`**  
  Assure le comblement des vides (lacunes spatiales) de la couche pédologique en s'appuyant sur des diagrammes de Voronoï le long des frontières de sol.
* **`4_CODE_JOINTURE_SOL_PARCELLE_UNITE_HYDRO.py`**  
  Réalise l'intersection spatiale rigoureuse entre les polygones de sol et d'occupation du sol pour générer la couche vectorielle des Unités Hydrologiques Homogènes (`unitehydro`).

### 2. Exécution et Pilotage du Modèle Numérique (Fortran)
* **`5_CODE_APPLICATION_MODEL_FORTRAN.py`**  
  Orchestre l'exécution séquentielle du binaire Fortran `volume.exe` à travers l'ensemble des périodes de retour (de $T_2$ à $T_{100}$) et des scénarios d'humidité antécédente des sols (AMC II / AMC III).
* **`6_CORRECTION_QGIS.py`**  
  Assure la mise en conformité stricte des en-têtes et des formats des rasters ASCII Grid générés par le moteur Fortran pour permettre leur exploitation sans erreur sous QGIS.

### 3. Analyse Spatiale et Aménagements (SFN)
* **`7_EXTRACTION_AXE_RUISSELLEMENT.py`**  
  Filtre les rasters de volume cumulé selon un seuil d'eau minimal pour isoler et vectoriser les réseaux de drainage et les axes de ruissellement principaux.
* **`8_SNF.py`**  
  Script PyQGIS combinant l'analyse de la pente ($\ge 15\%$) et la topologie du réseau hydrographique pour positionner automatiquement 31 sites d'intervention prioritaires (fascines, noues d'infiltration).

---

##  Utilisation / Prérequis

1. **Environnement SIG :** QGIS (version 3.x) et GRASS GIS configurés avec le système de projection local (Lambert II étendu / EPSG:27572).
2. **Interpréteur Python :** Modules requis : `os`, `sys`, `processing` (PyQGIS), `numpy`.
3. **Moteur de Calcul :** Le binaire compilé `volume.exe` doit être placé dans le répertoire racine des scripts Fortran pour exécuter les simulations matricielles.

---

## Licence
Ce projet est mis à disposition à des fins académiques et d'ingénierie dans le cadre de la gestion des risques hydrologiques en milieu viticole.
