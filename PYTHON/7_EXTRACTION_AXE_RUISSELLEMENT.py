# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 08:22:27 2026

@author: ASUS
"""
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from rasterio.windows import from_bounds

# =========================================================
# CONFIGURATION
# =========================================================
model_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee"
dossiers_in = ["resultats_normal", "resultats_humide"]
raster_mnt_path = os.path.join(model_dir, "Donnee", "MNT2.tif")

# SEUIL MINIMAL
seuil_min_volume = 0.1

print(f"Vectorisation brute des axes (seuil > {seuil_min_volume})...")
print("AUCUNE reprojection ne sera appliquée (coordonnées natives de l'ASC).")

# =========================================================
# PRÉPARATION DE L'EMPRISE (MNT)
# =========================================================
try:
    with rasterio.open(raster_mnt_path) as src_mnt:
        mnt_bounds = src_mnt.bounds
        mnt_disponible = True
        print(f"Emprise MNT détectée : {mnt_bounds}")
except Exception as e:
    print(f"Attention: Impossible d'ouvrir le raster MNT ({e}). L'emprise totale sera utilisée.")
    mnt_disponible = False

# =========================================================
# TRAITEMENT
# =========================================================
fichiers_traites = 0

for dossier in dossiers_in:
    src_dir = os.path.join(model_dir, dossier)
    
    if not os.path.exists(src_dir):
        print(f"Dossier source introuvable : {src_dir}")
        continue
        
    # Création dynamique du nom du sous-dossier de sortie 
    nom_out_dir = dossier.replace("resultats_", "resultat_axe_") + "_vecteur"
    out_dir = os.path.join(model_dir, nom_out_dir)
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"\n--- Traitement du dossier '{dossier}' vers '{nom_out_dir}' ---")
        
    for filename in os.listdir(src_dir):
        if filename.endswith(".asc"):
            filepath = os.path.join(src_dir, filename)
            out_filename = filename.replace(".asc", ".geojson")
            out_path = os.path.join(out_dir, out_filename)
            
            print(f"  Vectorisation de {filename}...")
            
            try:
                with rasterio.open(filepath) as src:
                    # Lecture selon l'emprise du MNT (si dispo) ou globale
                    if mnt_disponible:
                        window = from_bounds(*mnt_bounds, transform=src.transform)
                        band = src.read(1, window=window)
                        current_transform = src.window_transform(window)
                    else:
                        band = src.read(1)
                        current_transform = src.transform

                    nodata_val = src.nodata if src.nodata is not None else -9999.0
                    
                    # Filtre des valeurs > 0.1
                    mask = (band != nodata_val) & (band > seuil_min_volume)
                    
                    # Création des géométries avec la localisation native de l'ASC
                    results = (
                        {'properties': {'volume_m3': float(val)}, 'geometry': s}
                        for i, (s, val) 
                        in enumerate(shapes(band, mask=mask, transform=current_transform))
                    )
                    
                    features = list(results)
                         
                    # Export GeoJSON sans imposer de CRS
                    if features:
                        gdf = gpd.GeoDataFrame.from_features(features)
                        gdf.to_file(out_path, driver="GeoJSON")
                        fichiers_traites += 1
                    else:
                        print(f"    -> Aucun pixel d'eau > {seuil_min_volume} trouvé.")
                        
            except Exception as e:
                print(f"Erreur lors du traitement de {filename}: {e}")

print("\n" + "="*60)
print(f" Terminée ! {fichiers_traites} fichiers .geojson créés en coordonnées natives.")
print("="*60)