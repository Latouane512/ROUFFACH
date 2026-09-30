import math
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsRasterLayer
)
from PyQt5.QtCore import QVariant

# --- PARAMÉTRAGE ---
layer_name = "axes_ruissellement"    # Nom de votre couche vectorielle de lignes (axes)
slope_raster_name = "pente"          # Nom de votre raster de pente (en % ou degrés) dans QGIS (laissez None si non utilisé)

processing_width = 15.0      # Largeur totale de l'aménagement transversal (en mètres)
distance_intervalle = 150.0   # Intervalle le long du thalweg entre chaque aménagement (en mètres)
pente_seuil = 15.0           # Seuil de pente minimal (%) pour déclencher l'installation d'une SFN

# Récupération de la couche des axes
layers = QgsProject.instance().mapLayersByName(layer_name)
if not layers:
    print(f"Erreur : La couche vectorielle '{layer_name}' est introuvable.")
else:
    layer = layers[0]
    crs = layer.crs().authid()
    
    # Récupération optionnelle du raster de pente
    slope_layer = None
    if slope_raster_name:
        slope_layers = QgsProject.instance().mapLayersByName(slope_raster_name)
        if slope_layers:
            slope_layer = slope_layers[0]
            slope_provider = slope_layer.dataProvider()
    
    # Création de la couche mémoire de sortie pour les SFN
    out_layer = QgsVectorLayer(f"LineString?crs={crs}", "amenagements_sfn_cibles", "memory")
    prov = out_layer.dataProvider()
    
    prov.addAttributes([
        QgsField("id_troncon", QVariant.Int),
        QgsField("pente_pct", QVariant.Double),
        QgsField("type_sfn", QVariant.String)
    ])
    out_layer.updateFields()
    
    feature_id = 1
    ouvrages_crees = 0
    
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom.isNull():
            continue
        
        length = geom.length()
        
        # Condition 1 : On ignore les micro-axes de ruissellement de moins de 100m
        if length < 100.0:
            continue
            
        distance = distance_intervalle
        while distance < length - (distance_intervalle / 4):
            point = geom.interpolate(distance)
            if point:
                pt = point.asPoint()
                
                # Échantillonnage de la pente au point d'implantation (si le raster de pente est fourni)
                valeur_pente = 0.0
                if slope_layer:
                    ident = slope_provider.identify(pt, QgsRaster.IdentifyFormatValue)
                    if ident.isValid():
                        results = ident.results()
                        if results:
                            valeur_pente = list(results.values())[0]
                
                # Condition 2 : Si un raster de pente est actif, on vérifie qu'on dépasse le seuil critique
                # (Si aucun raster de pente n'est trouvé, le script place l'ouvrage en se basant uniquement sur l'espacement et la taille de l'axe)
                if not slope_layer or valeur_pente >= pente_seuil:
                    
                    # Calcul de la direction locale pour orienter le segment perpendiculairement au thalweg
                    pt_avant = geom.interpolate(max(0.0, distance - 2.0)).asPoint()
                    pt_apres = geom.interpolate(min(length, distance + 2.0)).asPoint()
                    
                    dx = pt_apres.x() - pt_avant.x()
                    dy = pt_apres.y() - pt_avant.y()
                    
                    norm = math.sqrt(dx*dx + dy*dy)
                    if norm > 0:
                        nx = -dy / norm
                        ny = dx / norm
                        
                        half_w = processing_width / 2.0
                        p1 = QgsPointXY(pt.x() - nx * half_w, pt.y() - ny * half_w)
                        p2 = QgsPointXY(pt.x() + nx * half_w, pt.y() + ny * half_w)
                        
                        new_feat = QgsFeature()
                        new_feat.setGeometry(QgsGeometry.fromPolylineXY([p1, p2]))
                        new_feat.setAttributes([feature_id, round(valeur_pente, 1), "Fascine / Noue transversale"])
                        
                        prov.addFeature(new_feat)
                        feature_id += 1
                        ouvrages_crees += 1
                        
            distance += distance_intervalle
            
    QgsProject.instance().addMapLayer(out_layer)
    print(f"Génération terminée : {ouvrages_crees} aménagements SFN stratégiques créés (filtrés par espacement et pente >= {pente_seuil}%).")