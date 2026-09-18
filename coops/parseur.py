import re

def normaliser_texte(texte):
    """Nettoie agressivement le texte pour éviter les pièges d'encodage du jeu."""
    t = texte.lower()
    t = t.replace("é", "e").replace("è", "e").replace("à", "a").replace("ô", "o")
    t = t.replace("(s)", "s").replace("(", "").replace(")", "")
    t = " ".join(t.split())
    return t

def analyser_historique_brut(texte_brut, membres_inscrits, joueur_actif):
    lignes_brutes = texte_brut.split("\n")
    regex_date = re.compile(r"le\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}:\d{2})", re.IGNORECASE)
    
    date_courante = None
    heure_courante = None
    actions_detectees = []

    for lg in lignes_brutes:
        l_brute_clean = lg.strip()
        if not l_brute_clean or "fil des" in l_brute_clean.lower():
            continue

        l_normalisee = normaliser_texte(l_brute_clean)
        match_date = regex_date.search(l_normalisee)
        if match_date:
            date_courante = match_date.group(1)
            heure_courante = match_date.group(2)
            continue

        if date_courante and heure_courante:
            mat_cle = None
            if "sable" in l_normalisee: mat_cle = "sable"
            elif "terre" in l_normalisee: mat_cle = "terre"
            elif "enrob" in l_normalisee: mat_cle = "enrobe"
            elif "armature" in l_normalisee: mat_cle = "armature"
            elif "tole" in l_normalisee: mat_cle = "tole"
            elif "beton" in l_normalisee: mat_cle = "beton"
            elif "panneau" in l_normalisee: mat_cle = "panneaux"
            elif "tuyau" in l_normalisee: mat_cle = "tuyaux"
            elif "canalisation" in l_normalisee: mat_cle = "canalisations"
            elif "poutre" in l_normalisee: mat_cle = "poutres"

            if mat_cle:
                acteur_final = joueur_actif
                type_mouv_final = "REAPPROVISIONNEMENT"
                partie_droite_quantite = l_brute_clean # Variable de sécurité pour chercher le nombre

                # --- 1. DETECTION DES REAPPROVISIONNEMENTS ---
                if "reappro" in l_normalisee:
                    type_mouv_final = "REAPPROVISIONNEMENT"
                    if "réapprovisionne de" in l_brute_clean:
                        parties = l_brute_clean.split("réapprovisionne de", 1)
                        # Acteur = ce qui est à gauche
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        # Quantité = à chercher uniquement dans ce qui est à droite
                        partie_droite_quantite = parties[1]
                    elif "reapprovisionne de" in l_brute_clean:
                        parties = l_brute_clean.split("reapprovisionne de", 1)
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        partie_droite_quantite = parties[1]
                    else:
                        acteur_final = "Réapprovisionnement Global"

                # --- 2. DETECTION DES ACHATS ---
                elif "achete" in l_normalisee:
                    if "a acheté" in l_brute_clean:
                        parties = l_brute_clean.split("a acheté", 1)
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        partie_droite_quantite = parties[1]
                    elif "a achete" in l_brute_clean:
                        parties = l_brute_clean.split("a achete", 1)
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        partie_droite_quantite = parties[1]
                    else:
                        acteur_final = joueur_actif
                    
                    type_mouv_final = "ACHAT_INTERNE" if acteur_final in membres_inscrits else "ACHAT_EXTERNE"

                # Nettoyage ultime du pseudo (si l'heure est restée collée devant le nom)
                if " " in acteur_final:
                    acteur_final = acteur_final.split()[-1].strip()

                # Extraction de la quantité UNIQUEMENT dans la partie droite isolée
                chiffres = re.findall(r"\d[\d\s]*", partie_droite_quantite)
                if chiffres:
                    qte_val = float(chiffres[0].replace(" ", ""))
                else:
                    qte_val = 1.0 # Sécurité par défaut

                actions_detectees.append({
                    "date": date_courante,
                    "heure": heure_courante,
                    "acteur": acteur_final.strip(),
                    "type": type_mouv_final,
                    "materiaux": {mat_cle: qte_val}
                })

    return actions_detectees
