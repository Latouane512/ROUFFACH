import processing
from qgis.core import QgsProject, QgsVectorLayer

# 1. Couche source
layer_name = "parcelle"  # Assure-toi que la couche s'appelle bien ainsi dans QGIS
parcelle = QgsProject.instance().mapLayersByName(layer_name)[0]

# 2. Dossier de sortie
output_path = "D:/2_MASTER_ISIE/SIG_AVANCE/Projet_SIG/route_chemin.shp"

# 3. Filtrage automatique des routes, chemins et fossés existants
expr = "\"OS\" = 'chemin' OR \"OS\" = 'passage' OR \"OS\" = 'fosse'"
processing.run("native:extractbyexpression", {
    'INPUT': parcelle,
    'EXPRESSION': expr,
    'OUTPUT': output_path
})

# 4. Charger la nouvelle couche dans le projet
layer_chemins = QgsVectorLayer(output_path, "route_chemin", "ogr")
QgsProject.instance().addMapLayer(layer_chemins)
print("Couche extraite et chargée avec succès.")