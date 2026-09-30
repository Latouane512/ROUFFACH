# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 08:22:27 2026

@author: ASUS
"""

import os
import numpy as np

# =========================================================
# CONFIGURATION
# =========================================================
model_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee"

# Définissez ici le volume minimum (en m³) pour qu'un pixel soit 
# considéré comme un axe de ruissellement.
# Mettez 0.1 si vous voulez juste enlever les pixels secs, 
# ou 100 pour ne voir que les rivières principales.
#2.0 trop elever 
SEUIL_VOLUME = 0.3

conditions = ["normal", "humide"]
periodes = ["T2", "T5", "T10", "T20", "T50", "T100"]
types_vol = ["volume_avec_inf", "volume_sans_inf"]

print(f"Extraction des axes de ruissellement (Seuil : {SEUIL_VOLUME} m³)...")

# =========================================================
# TRAITEMENT
# =========================================================
for cond in conditions:
    # Dossier d'entrée (vos résultats précédents)
    src_dir = os.path.join(model_dir, f"resultats_{cond}")
    
    # Nouveau dossier de sortie pour les axes
    out_dir = os.path.join(model_dir, f"axes_{cond}")
    os.makedirs(out_dir, exist_ok=True)
    
    for t in periodes:
        for type_v in types_vol:
            filename = f"{type_v}_{t}.asc"
            filepath = os.path.join(src_dir, filename)
            
            if os.path.exists(filepath):
                # 1. Copier l'en-tête intact
                with open(filepath, "r") as f:
                    header_lines = [next(f) for _ in range(6)]
                
                # 2. Lire les données de volume
                data = np.loadtxt(filepath, skiprows=6)
                
                # 3. Appliquer le filtre : 
                # Si le pixel n'est pas un NoData ET qu'il dépasse le seuil, on garde sa valeur.
                # Sinon, on le force en NoData (-9999).
                axes_data = np.where((data != -9999) & (data >= SEUIL_VOLUME), data, -9999)
                
                # 4. Sauvegarder le nouveau fichier
                out_filename = f"axes_{type_v}_{t}.asc"
                out_path = os.path.join(out_dir, out_filename)
                
                with open(out_path, "w") as f:
                    f.writelines(header_lines)
                    # On sauvegarde au format %.2f pour garder la précision des m³
                    np.savetxt(f, axes_data, fmt="%.2f")

print("\n" + "="*60)
print(f"✅ Extraction terminée ! Les rasters filtrés ont été créés.")
print(f"Rendez-vous dans les dossiers : 'axes_normal' et 'axes_humide'.")
print("="*60)