# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 11:20:42 2026

@author: ASUS
"""
import os
import subprocess
import shutil
import numpy as np
import re

# =========================================================
# CONFIGURATION DES CHEMINS
# =========================================================
data_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee" 
model_dir = r"D:\2_MASTER_ISIE\SIG_AVANCE\donnee"

# Les conditions de sol et les périodes
conditions = ["normal", "humide"]
periodes = ["t2", "t5", "t10", "t20", "t50", "t100"]

sorties_fortran = [
    "volume_avec_inf.asc", 
    "volume_sans_inf.asc", 
    "pluie_effmm.asc", 
    "infiltration.asc"
]
noms_base = ["volume_avec_inf", "volume_sans_inf", "pluie_effmm", "infiltration"]

def trouver_fichier(dossier, mots_cles):
    """Cherche le bon fichier de manière stricte sans bloquer dirflux"""
    for fichier in os.listdir(dossier):
        f_lower = fichier.lower()
        
        # On exclut UNIQUEMENT les fichiers de destination créés par la boucle 
        # pour la pluie et le sol afin qu'il ne lise pas ses propres résultats.
        if f_lower in ["cn_input.asc", "pluie_input.asc"]:
            continue
            
        # On exclut les anciens résidus de pluie
        if f_lower.startswith("pluie_input_t"):
            continue
            
        # On vérifie que tous les mots-clés sont dans le nom
        if all(mot.lower() in f_lower for mot in mots_cles):
            valide = True
            for mot in mots_cles:
                # Distinction stricte entre T2/T20, T5/T50, T10/T100
                if mot.lower().startswith('t') and mot[1:].isdigit():
                    import re
                    pattern = mot.lower() + r'(?!\d)'
                    if not re.search(pattern, f_lower):
                        valide = False
                        break
            
            if valide:
                return os.path.join(dossier, fichier)
            
    raise FileNotFoundError(f"Impossible de trouver un fichier strict contenant {mots_cles} dans {dossier}")

def lire_entete_asc(fichier):
    entete = {}
    with open(fichier, "r") as f:
        for _ in range(6):
            parts = f.readline().strip().split()
            if len(parts) >= 2:
                entete[parts[0].lower()] = float(parts[1])
    return entete

def aligner_raster(ref_file, target_file, output_file, is_float=False):
    """Recadre le raster sur l'emprise exacte de dirflux"""
    ref_h = lire_entete_asc(ref_file)
    target_h = lire_entete_asc(target_file)
    
    ref_ncols, ref_nrows = int(ref_h['ncols']), int(ref_h['nrows'])
    ref_xll, ref_yll = ref_h['xllcorner'], ref_h['yllcorner']
    cellsize = ref_h['cellsize']
    
    target_data = np.loadtxt(target_file, skiprows=6)
    
    col_offset = int(round((ref_xll - target_h['xllcorner']) / cellsize))
    target_ytop = target_h['yllcorner'] + target_h['nrows'] * cellsize
    ref_ytop = ref_yll + ref_nrows * cellsize
    row_offset = int(round((target_ytop - ref_ytop) / cellsize))
    
    dtype = float if is_float else int
    aligned_data = np.full((ref_nrows, ref_ncols), -9999, dtype=dtype)
    t_nrows, t_ncols = target_data.shape
    
    sub = target_data[max(0, row_offset):min(t_nrows, row_offset + ref_nrows),
                      max(0, col_offset):min(t_ncols, col_offset + ref_ncols)]
    
    out_r, out_c = max(0, -row_offset), max(0, -col_offset)
    aligned_data[out_r:out_r+sub.shape[0], out_c:out_c+sub.shape[1]] = sub
    
    with open(output_file, 'w') as f:
        f.writelines([
            f"ncols         {ref_ncols}\n",
            f"nrows         {ref_nrows}\n",
            f"xllcorner     {ref_xll:.6f}\n",
            f"yllcorner     {ref_yll:.6f}\n",
            f"cellsize      {int(cellsize)}\n",
            f"NODATA_value  -9999\n"
        ])
        fmt = "%.2f" if is_float else "%d"
        np.savetxt(f, aligned_data, fmt=fmt)

# =========================================================
# ETAPE 1 : Préparation du fichier d'écoulement
# =========================================================
print("Préparation du modèle...")
ref_dir_src = trouver_fichier(data_dir, ["dirflux"])
ref_dir_dest = os.path.join(model_dir, "dirflux_input.asc")

if os.path.abspath(ref_dir_src) != os.path.abspath(ref_dir_dest):
    shutil.copyfile(ref_dir_src, ref_dir_dest)

bilan_global = {}

# =========================================================
# ETAPE 2 : Boucle sur les Conditions (Normal / Humide)
# =========================================================
for cond in conditions:
    print(f"\n" + "="*60)
    print(f"LANCEMENT DU SCÉNARIO : SOL {cond.upper()}")
    print("="*60)
    
    res_dir = os.path.join(model_dir, f"resultats_{cond}")
    os.makedirs(res_dir, exist_ok=True)
    
    cn_src = trouver_fichier(data_dir, ["cn", cond])
    cn_dest = os.path.join(model_dir, "cn_input.asc")
    aligner_raster(ref_dir_src, cn_src, cn_dest, is_float=False)
    
    bilan_global[cond] = {}

    for t in periodes:
        t_maj = t.upper()
        print(f"-> Calcul hydraulique - Période {t_maj}...")
        
        # Recherche et affichage clair du fichier de pluie utilisé
        pluie_src = trouver_fichier(data_dir, ["pluie", t])
        print(f"   [Lecture du fichier : {os.path.basename(pluie_src)}]")
        
        pluie_dest = os.path.join(model_dir, "pluie_input.asc") 
        aligner_raster(ref_dir_src, pluie_src, pluie_dest, is_float=True)

        try:
            subprocess.run(
                [os.path.join(model_dir, "volume.exe")], 
                cwd=model_dir, 
                check=True,
                capture_output=True,
                text=True,
                encoding='cp1252',
                errors='replace'
            )
        except subprocess.CalledProcessError as e:
            print(f"\n!!! LE PROGRAMME FORTRAN A PLANTÉ SUR LA PÉRIODE {t_maj} !!!")
            print(e.stderr)
            if e.stdout:
                print(e.stdout)
            raise 

        for nom_fortran, nom_base in zip(sorties_fortran, noms_base):
            src = os.path.join(model_dir, nom_fortran)
            if os.path.exists(src):
                dst = os.path.join(res_dir, f"{nom_base}_{t_maj}.asc")
                shutil.copyfile(src, dst)
                os.remove(src)
                
        f_avec = os.path.join(res_dir, f"volume_avec_inf_{t_maj}.asc")
        f_sans = os.path.join(res_dir, f"volume_sans_inf_{t_maj}.asc")

        v_avec, v_sans = 0.0, 0.0
        if os.path.exists(f_avec) and os.path.exists(f_sans):
            d_avec = np.loadtxt(f_avec, skiprows=6)
            d_sans = np.loadtxt(f_sans, skiprows=6)
            val_avec = d_avec[d_avec != -9999]
            val_sans = d_sans[d_sans != -9999]
            v_avec = np.max(val_avec) if val_avec.size > 0 else 0.0
            v_sans = np.max(val_sans) if val_sans.size > 0 else 0.0

        bilan_global[cond][t_maj] = (v_avec, v_sans)

# =========================================================
# ETAPE 3 : Bilan Comparatif Final
# =========================================================
print("\n\n" + "#"*70)
print(" "*25 + "BILANS GLOBAUX")
print("#"*70)

for cond in conditions:
    print(f"\nSCÉNARIO : SOL {cond.upper()} (Dossier: resultats_{cond})")
    print("-" * 70)
    print(f"{'Période':<8} | {'Avec Infiltration':<18} | {'Sans Infiltration':<18} | {'Statut (Bassin 1500 m³)'}")
    print("-" * 70)
    
    for t_maj, (v_avec, v_sans) in bilan_global[cond].items():
        statut = f"DÉBORDEMENT (+{v_avec - 1500:,.1f} m³)" if v_avec > 1500 else "Conforme"
        print(f"{t_maj:<8} | {v_avec:>14,.1f} m³ | {v_sans:>14,.1f} m³ | {statut}")
print("-" * 70)