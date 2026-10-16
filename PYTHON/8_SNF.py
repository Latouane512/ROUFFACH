# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 08:22:27 2026

@author: ASUS
"""
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import math
import geopandas as gpd
import rasterio
from shapely.geometry import LineString
import os

# =========================================================
# PARAMÉTRAGE DES FICHIERS
# =========================================================
model_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee"

# Chemins vers les GeoJSON des axes vectorisés
geojson_fichiers = {
    "normal": os.path.join(model_dir, "resultat_axe_normal_vecteur", "volume_sans_inf_T20.geojson"),
    "humide": os.path.join(model_dir, "resultat_axe_humide_vecteur", "volume_sans_inf_T20.geojson")
}

raster_pente_path = os.path.join(model_dir, "Donnee", "pente.tif") 

# =========================================================
# PARAMÉTRAGE MÉTIER
# =========================================================
seuil_volume_m3 = 50.0       # Volume minimum d'eau en m3
seuil_pente_pct = 15.0       # Seuil de pente minimal en %
processing_width = 8.0       # Largeur de la ligne (8 mètres pour traverser l'axe)
distance_intervalle = 50.0   # Espacement MINIMUM entre deux SFN (en mètres)

print(f"Analyse des zones critiques à partir des GeoJSON : Volume >= {seuil_volume_m3} m3 ET Pente >= {seuil_pente_pct}%")
print("Export brut SANS reprojection (coordonnées natives).\n")

try:
    # 1. Ouverture du raster de pente pour l'échantillonnage
    src_pente = rasterio.open(raster_pente_path)
    pente_disponible = True
except Exception as e:
    print(f"Attention: Impossible d'ouvrir le raster de pente ({e}).")
    pente_disponible = False

# =========================================================
# TRAITEMENT PAR SCÉNARIO
# =========================================================
for condition, geojson_path in geojson_fichiers.items():
    print(f"--- Traitement du scénario : {condition.upper()} ---")
    
    output_sfn_path = os.path.join(model_dir, f"amenagements_sfn_lignes_{condition}.geojson")
    
    if not os.path.exists(geojson_path):
        print(f"  -> Erreur : Le fichier GeoJSON est introuvable : {geojson_path}\n")
        continue
        
    try:
        # 2. Lecture du fichier GeoJSON des axes avec Geopandas
        gdf_axes = gpd.read_file(geojson_path)
        
        # Filtrage initial sur le volume minimal requis
        if 'volume_m3' in gdf_axes.columns:
            gdf_filtered = gdf_axes[gdf_axes['volume_m3'] >= seuil_volume_m3].copy()
        else:
            print("  -> Erreur : La colonne 'volume_m3' est absente de ce GeoJSON.")
            continue
            
        print(f"  {len(gdf_filtered)} entités vectorielles dépassent le seuil de volume. Vérification de la pente...")
        
        accepted_sfns = []
        feature_id = 1
        half_w = processing_width / 2.0
        
        # Tri des entités du plus gros volume au plus petit pour prioriser les zones à fort risque
        gdf_filtered = gdf_filtered.sort_values(by='volume_m3', ascending=False)
        
        for idx, row in gdf_filtered.iterrows():
            geom = row['geometry']
            vol = float(row['volume_m3'])
            
            # Utilisation du centroïde de l'entité pour échantillonner la pente locale
            pt = geom.centroid
            x, y = pt.x, pt.y
            
            valeur_pente = 0.0
            if pente_disponible:
                try:
                    sample_gen = src_pente.sample([(x, y)])
                    valeur_pente = float(list(sample_gen)[0][0])
                except Exception:
                    pass
            
            # Application du seuil de pente
            if not pente_disponible or valeur_pente >= seuil_pente_pct:
                
                # Vérification de l'espacement minimal avec les aménagements déjà placés
                trop_proche = False
                for sfn in accepted_sfns:
                    if math.hypot(x - sfn["x"], y - sfn["y"]) < distance_intervalle:
                        trop_proche = True
                        break
                
                if trop_proche:
                    continue
                
                # Création d'une ligne transversale (orientée par défaut de manière horizontale/orthogonale)
                p1 = (x - half_w, y)
                p2 = (x + half_w, y)
                geom_ligne = LineString([p1, p2])
                
                accepted_sfns.append({
                    "x": x, "y": y,
                    "geometry": geom_ligne,
                    "id_sfn": feature_id,
                    "volume_m3": round(vol, 2),
                    "pente_pct": round(valeur_pente, 1),
                    "type": "Bande enherbée transversale",
                    "scenario": condition
                })
                feature_id += 1

        # 3. Export des aménagements validés
        if accepted_sfns:
            gdf_out = gpd.GeoDataFrame(accepted_sfns)
            gdf_out = gdf_out.drop(columns=['x', 'y'])
            
            gdf_out.to_file(output_sfn_path, driver="GeoJSON")
            print(f"  -> Succès ! {len(accepted_sfns)} LIGNES transversales créées.")
            print(f"  -> Fichier enregistré : {output_sfn_path}\n")
        else:
            print(f"  -> Aucun aménagement ne correspond aux critères pour le scénario {condition}.\n")

    except Exception as e:
        print(f"  -> Une erreur est survenue : {e}\n")

if pente_disponible:
    src_pente.close()