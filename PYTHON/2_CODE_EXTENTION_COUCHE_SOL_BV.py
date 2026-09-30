import os
import processing
from qgis.core import QgsProject, QgsVectorLayer

out_dir = "D:/2_MASTER_ISIE/SIG_AVANCE/Projet_SIG/"

# 1. Couches sources
layer_sol = QgsProject.instance().mapLayersByName("aptit_ruiss")[0]
layer_bv = QgsProject.instance().mapLayersByName("bv_final_corrige")[0]

# Identifier le champ attributaire du sol (ex: SolSCS, Type, OS, etc.)
soil_field = [f.name() for f in layer_sol.fields() if f.name().lower() in ['solscs', 'sol', 'type', 'aptitude', 'classe']]
dissolve_fields = [soil_field[0]] if soil_field else []

# 2. Identifier les zones de vide dans le BV non couvertes par le sol
diff = processing.run("native:difference", {
    'INPUT': layer_bv,
    'OVERLAY': layer_sol,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 3. Échantillonner densément la frontière du sol en points de référence
boundary = processing.run("native:boundary", {
    'INPUT': layer_sol,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

pts_sol = processing.run("native:densifygeometriesgivenaninterval", {
    'INPUT': boundary,
    'INTERVAL': 2.0,  # Résolution de 2 m identique au MNT
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

pts_sol = processing.run("native:extractvertices", {
    'INPUT': pts_sol,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# Attribuer la classe de sol aux points d'échantillonnage
pts_sol = processing.run("native:joinattributesbylocation", {
    'INPUT': pts_sol,
    'JOIN': layer_sol,
    'PREDICATE': [0],  # intersecte
    'METHOD': 0,
    'DISCARD_NONMATCHING': True,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 4. Partitionner l'espace vide selon la frontière la plus proche (Voronoï)
voronoi = processing.run("qgis:voronoipolygons", {
    'INPUT': pts_sol,
    'BUFFER': 20.0,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 5. Découper les polygones de Voronoï strictement sur l'emprise des vides
vides_attribues = processing.run("native:clip", {
    'INPUT': voronoi,
    'OVERLAY': diff,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 6. Fusionner le sol initial et les extensions comblées
merged = processing.run("native:mergevectorlayers", {
    'LAYERS': [layer_sol, vides_attribues],
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 7. Dissoudre par type de sol pour éliminer les micro-coutures
dissolved = processing.run("native:dissolve", {
    'INPUT': merged,
    'FIELD': dissolve_fields,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 8. Découpe finale ajustée au contour exact du BV
aptisol_bv_path = os.path.join(out_dir, "aptisol_bv_corrige.shp")
processing.run("native:clip", {
    'INPUT': dissolved,
    'OVERLAY': layer_bv,
    'OUTPUT': aptisol_bv_path
})

sol_final = QgsVectorLayer(aptisol_bv_path, "aptisol_bv", "ogr")
QgsProject.instance().addMapLayer(sol_final)
print("Couche aptisol_bv générée avec extension géométrique cohérente !")