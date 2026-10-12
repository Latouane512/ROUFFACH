import os
import processing
from qgis.core import QgsProject, QgsVectorLayer

out_dir = "D:/2_MASTER_ISIE/SIG_AVANCE/donnee/Donnee"
os.makedirs(out_dir, exist_ok=True)

# 1. Chargement sécurisé des couches
def get_layer(nom):
    layers = QgsProject.instance().mapLayersByName(nom)
    if not layers:
        dispo = [l.name() for l in QgsProject.instance().mapLayers().values()]
        raise ValueError(f"Couche '{nom}' introuvable. Couches disponibles : {dispo}")
    return layers[0]

layer_parcelles = get_layer("parcelle")
layer_bv = get_layer("Bv_reconstruit")

# 2. Réparation géométrique
parcelles_valides = processing.run("native:fixgeometries", {
    'INPUT': layer_parcelles,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

bv_valide = processing.run("native:fixgeometries", {
    'INPUT': layer_bv,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 3. Intersection : découpe propre des parcelles à l'intérieur du BV
parcelles_bv = processing.run("native:intersection", {
    'INPUT': parcelles_valides,
    'OVERLAY': bv_valide,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

parcelles_bv = processing.run("native:fixgeometries", {
    'INPUT': parcelles_bv,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 4. Identification des zones manquantes (différence stricte)
vides = processing.run("native:difference", {
    'INPUT': bv_valide,
    'OVERLAY': parcelles_bv,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

vides = processing.run("native:fixgeometries", {
    'INPUT': vides,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

vides_single = processing.run("native:multiparttosingleparts", {
    'INPUT': vides,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 5. Renseignement des attributs EDS et OCS_1 sur les zones enherbées comblées
vides_attrib = processing.run("native:fieldcalculator", {
    'INPUT': vides_single,
    'FIELD_NAME': 'EDS',
    'FIELD_TYPE': 2,
    'FIELD_LENGTH': 50,
    'FORMULA': "'enherbe'",
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

vides_attrib = processing.run("native:fieldcalculator", {
    'INPUT': vides_attrib,
    'FIELD_NAME': 'OCS_1',
    'FIELD_TYPE': 2,
    'FIELD_LENGTH': 50,
    'FORMULA': "'Herbe'",
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# 6. Fusion finale (sans réappliquer de clip supplémentaire qui rogne les bordures)
out_path = os.path.join(out_dir, "parcelles_bv_complet.shp")
merged = processing.run("native:mergevectorlayers", {
    'LAYERS': [parcelles_bv, vides_attrib],
    'OUTPUT': out_path
})

parcelles_final = QgsVectorLayer(out_path, "parcelles_bv_complet", "ogr")
QgsProject.instance().addMapLayer(parcelles_final)
print(f"Couche OCS générée avec succès : {out_path}")