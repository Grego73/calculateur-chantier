# Fichier : coops/parseur.py
import re

def analyser_historique_brut(texte_brut, membres_inscrits, joueur_actif):
    """
    Analyse le fil des événements bruts et extrait les actions de Réappro et d'Achats nominatifs
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
                    if "réapprovisionne de" in l_clean.lower():
                        parties = l_clean.split("réapprovisionne")
                        acteur_final = parties[0].strip() if parties[0].strip() else "Réapprovisionnement Global"
                        type_mouv_final = "REAPPROVISIONNEMENT"
                    elif l_clean.lower().startswith("réapprovisionnement de"):
                        acteur_final = "Réapprovisionnement Global"
                        type_mouv_final = "REAPPROVISIONNEMENT"
                    elif "a acheté" in l_clean.lower():
                        parties = l_clean.split("a acheté")
                        acteur_final = parties[0].strip() if len(parties) > 0 else joueur_actif
                        type_mouv_final = "ACHAT_INTERNE" if acteur_final in membres_inscrits else "ACHAT_EXTERNE"
                    else:
                        acteur_final = joueur_actif
                        type_mouv_final = "REAPPROVISIONNEMENT"

                    actions_detectees.append({
                        "date": date_courante, "heure": heure_courante,
                        "acteur": acteur_final, "type": type_mouv_final,
                        "materiaux": {mat_cle: qte_val}
                    })
                    
    return actions_detectees
