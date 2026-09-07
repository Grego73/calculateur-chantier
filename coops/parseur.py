# Fichier complet, nettoyé et validé pour : coops/parseur.py
import re

def analyser_historique_brut(texte_brut, membres_inscrits, joueur_actif):
    """
    Analyse le fil des événements bruts et sépare de manière 100% étanche
    les réapprovisionnements (rachats coop) et les achats (consommation).
    """
    lignes_brutes = texte_brut.split("\n")
    regex_date = re.compile(r"Le\s*(\d{2}/\d{2}/\d{4})\s*[aà]\s*(\d{2}:\d{2})", re.IGNORECASE)
    regex_materiau = re.compile(r"(\d[\d\s]*)\s*(tonne|unité|unite)[s]?\s*de\s*(sable|terre|enrob|armature|tôle|tole|béton|beton|panneau|tuyau|canalisation|poutre)", re.IGNORECASE)
    
    date_courante = None
    heure_courante = None
    actions_detectees = []

    for lg in lignes_brutes:
        l_clean = lg.strip()
        if not l_clean or "fil des" in l_clean.lower(): 
            continue

        match_date = regex_date.search(l_clean)
        if match_date:
            date_courante = match_date.group(1)
            heure_courante = match_date.group(2)
            continue

        if date_courante and heure_courante:
            match_mat = regex_materiau.search(l_clean)
            if match_mat:
                qte_val = float(match_mat.group(1).replace(" ", ""))
                type_mat_brut = match_mat.group(3).lower()

                mat_cle = None
                if "sable" in type_mat_brut: mat_cle = "sable"
                elif "terre" in type_mat_brut: mat_cle = "terre"
                elif "enrob" in type_mat_brut: mat_cle = "enrobe"
                elif "armature" in type_mat_brut: mat_cle = "armature"
                elif "tôle" in type_mat_brut or "tole" in type_mat_brut: mat_cle = "tole"
                elif "béton" in type_mat_brut or "beton" in type_mat_brut: mat_cle = "beton"
                elif "panneau" in type_mat_brut: mat_cle = "panneaux"
                elif "tuyau" in type_mat_brut: mat_cle = "tuyaux"
                elif "canalisation" in type_mat_brut: mat_cle = "canalisations"
                elif "poutre" in type_mat_brut: mat_cle = "poutres"

                if mat_cle:
                    l_lower = l_clean.lower()
                    
                    # --- DOUBLE SÉCURITÉ : VERROUILLAGE DU RÉAPPROVISIONNEMENT ---
                    if "réappro" in l_lower or "reappro" in l_lower:
                        type_mouv_final = "REAPPROVISIONNEMENT"
                        if "réapprovisionne de" in l_lower:
                            acteur_final = l_clean.split("réapprovisionne")[0].strip()
                        elif "réapprovisionnement de" in l_lower or "reapprovisionnement de" in l_lower:
                            acteur_final = "Réapprovisionnement Global"
                        else:
                            acteur_final = "Réapprovisionnement Global"
                            
                    # --- BLOC DES ACHATS (UNIQUEMENT SI CE N'EST PAS UN RÉAPPRO) ---
                    elif "acheté" in l_lower or "achete" in l_lower:
                        if "a acheté" in l_lower:
                            acteur_final = l_clean.split("a acheté")[0].strip()
                        else:
                            acteur_final = joueur_actif
                            
                        # Tri automatique : Interne (Coop) ou Externe (Client)
                        type_mouv_final = "ACHAT_INTERNE" if acteur_final in membres_inscrits else "ACHAT_EXTERNE"
                        
                    else:
                        # Sécurité par défaut
                        acteur_final = joueur_actif
                        type_mouv_final = "REAPPROVISIONNEMENT"

                    # Nettoyage ultime du pseudo pour enlever les résidus de texte
                    acteur_final = acteur_final.replace("Le ", "").strip()
                    if not acteur_final:
                        acteur_final = "Réapprovisionnement Global"

                    actions_detectees.append({
                        "date": date_courante, "heure": heure_courante,
                        "acteur": acteur_final, "type": type_mouv_final,
                        "materiaux": {mat_cle: qte_val}
                    })
                    
    return actions_detectees
