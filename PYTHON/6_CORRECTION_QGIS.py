# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 09:02:30 2026

@author: ASUS
"""
import os
import glob
import numpy as np

# =========================================================
# CONFIGURATION DES CHEMINS
# =========================================================
data_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee"

dossiers_resultats = [
    os.path.join(data_dir, "resultats_normal"),
    os.path.join(data_dir, "resultats_humide")
]

def nettoyer_raster_natif(chemin_fichier):
    """Lit l'en-tête natif de Fortran (749x695), nettoie les données et reformate pour QGIS."""
    try:
        with open(chemin_fichier, 'r') as f:
            lignes = f.readlines()
            
        if len(lignes) < 6:
            print(f"  [ERREUR] Fichier trop court : {os.path.basename(chemin_fichier)}")
            return

        # 1. Extraction dynamique et nettoyage de l'en-tête Fortran
        entete = {}
        for i in range(6):
            # Remplace les virgules éventuelles et sépare la clé de la valeur
            parts = lignes[i].replace(',', '.').strip().split()
            if len(parts) >= 2:
                entete[parts[0].lower()] = float(parts[1])

        ncols = int(entete.get('ncols', 749))
        nrows = int(entete.get('nrows', 695))
        
        # 2. Nettoyage des données (virgules, notations scientifiques D de Fortran)
        lignes_donnees = lignes[6:]
        lignes_propres = [
            ligne.replace(',', '.').replace('D', 'e').replace('d', 'e') 
            for ligne in lignes_donnees
        ]
        
        # 3. Chargement plat (1D) pour contourner les sauts de ligne aléatoires
        data = np.loadtxt(lignes_propres).flatten()
        taille_attendue = nrows * ncols
        
        # Ajustement des trous si le modèle s'est arrêté brutalement
        if data.size < taille_attendue:
            manquant = taille_attendue - data.size
            data = np.append(data, np.full(manquant, -9999.0))
        elif data.size > taille_attendue:
            data = data[:taille_attendue]
            
        # Reformage 2D sur la vraie géométrie calculée
        data_2d = data.reshape((nrows, ncols))
        
        # 4. Écriture du fichier au format QGIS strict
        with open(chemin_fichier, 'w') as f:
            f.writelines([
                f"ncols         {ncols}\n",
                f"nrows         {nrows}\n",
                f"xllcorner     {entete['xllcorner']:.6f}\n",
                f"yllcorner     {entete['yllcorner']:.6f}\n",
                f"cellsize      {int(entete['cellsize'])}\n",
                f"NODATA_value  -9999\n"
            ])
            np.savetxt(f, data_2d, fmt="%.3f")
            
        print(f"  [OK] Rognage préservé et corrigé : {os.path.basename(chemin_fichier):<25} ({ncols} col x {nrows} lig)")
        
    except Exception as e:
        print(f"  [ERREUR] Impossible de traiter {os.path.basename(chemin_fichier)} : {e}")

# =========================================================
# LANCEMENT
# =========================================================
print("Début du formatage QGIS (basé sur la grille interne recadrée par Fortran)...")
for dossier in dossiers_resultats:
    if os.path.exists(dossier):
        print(f"\nTraitement du dossier : {os.path.basename(dossier)}")
        for fichier in glob.glob(os.path.join(dossier, "*.asc")):
            nettoyer_raster_natif(fichier)

print("\nNettoyage terminé. Les dimensions natives ont été respectées.")