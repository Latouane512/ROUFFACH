import os
import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsField
from PyQt5.QtCore import QVariant

out_dir = "D:/2_MASTER_ISIE/SIG_AVANCE/Projet_SIG/"

# 1. Récupération des couches
layer_bv = QgsProject.instance().mapLayersByName("bv_final_corrige")[0]
layer_sol_bv = QgsProject.instance().mapLayersByName("aptisol_bv")[0]

# Recherche de la couche parcelle
matches_p = QgsProject.instance().mapLayersByName("parcelle")
layer_parcelle = matches_p[0] if matches_p else QgsVectorLayer(os.path.join(out_dir, "Base_projet/Base_projet/BD_TOPO/parcelle.shp"), "parcelle", "ogr")

# 2. Tampon de 100 m autour du bassin versant
buf_bv = processing.run("native:buffer", {
    'INPUT': layer_bv,
    'DISTANCE': 100.0,
    'SEGMENTS': 5,
    'END_CAP_STYLE': 0,
    'JOIN_STYLE': 0,
    'MITER_LIMIT': 2.0,
    'DISSOLVE': True,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 3. Union entre le tampon et les parcelles
union_parcelle = processing.run("native:union", {
    'INPUT': buf_bv,
    'OVERLAY': layer_parcelle,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 4. Découpage aux limites strictes du bassin versant
parcelle_bv = processing.run("native:clip", {
    'INPUT': union_parcelle,
    'OVERLAY': layer_bv,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 5. Combler les trous extérieurs avec OS = 'passage' et EDS = 'enherbe'
parcelle_bv.startEditing()
fields = parcelle_bv.fields()
idx_os = fields.indexFromName("OS")
idx_eds = fields.indexFromName("EDS")

# Si les champs n'existent pas sous ce nom exact, chercher des variantes ou créer
if idx_os == -1:
    for f in fields:
        if "os" in f.name().lower():
            idx_os = fields.indexFromName(f.name())
            break
if idx_eds == -1:
    for f in fields:
        if "eds" in f.name().lower():
            idx_eds = fields.indexFromName(f.name())
            break

for feat in parcelle_bv.getFeatures():
    # Si la parcelle provient de la zone tampon vide (valeur NULL ou vide)
    if not feat[idx_os] or feat[idx_os] == QVariant():
        parcelle_bv.changeAttributeValue(feat.id(), idx_os, "passage")
        if idx_eds != -1:
            parcelle_bv.changeAttributeValue(feat.id(), idx_eds, "enherbe")

parcelle_bv.commitChanges()

# 6. Intersection finale : Sols x Occupation du sol
unitehydro_path = os.path.join(out_dir, "unitehydro.shp")
processing.run("native:intersection", {
    'INPUT': parcelle_bv,
    'OVERLAY': layer_sol_bv,
    'OUTPUT': unitehydro_path
})

# 7. Chargement de la couche finale
layer_unitehydro = QgsVectorLayer(unitehydro_path, "unitehydro", "ogr")
QgsProject.instance().addMapLayer(layer_unitehydro)
print("Couche unitehydro générée et chargée avec succès !")