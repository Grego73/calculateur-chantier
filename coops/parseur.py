import re
from bs4 import BeautifulSoup


def normaliser_texte(texte):
    """Nettoie le texte pour éviter les pièges d'encodage et d'accents du jeu."""
    t = texte.lower()
    t = t.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ô", "o")
    t = t.replace("(s)", "s").replace("(", "").replace(")", "")
    t = " ".join(t.split())
    return t


def _extraire_texte_depuis_html_coop(html_brut):
    """Extrait proprement les lignes du fil des événements si l'utilisateur colle le code HTML."""
    soup = BeautifulSoup(html_brut, "html.parser")
    lignes_extraites = []

    for li in soup.select("ul.collection li.collection-item"):
        spans = li.find_all("span")
        if len(spans) >= 2:
            date_txt = spans[0].get_text(strip=True)
            action_txt = spans[1].get_text(strip=True)
            if date_txt.lower().startswith("le ") and " à " in date_txt.lower():
                lignes_extraites.append(date_txt)
                lignes_extraites.append(action_txt)

    if lignes_extraites:
        return "\n".join(lignes_extraites)
    return soup.get_text("\n")


def analyser_historique_brut(texte_brut, membres_inscrits, joueur_actif):
    """Analyse le texte copié OU le code HTML complet de la page 'Ma coopérative'."""
    if not texte_brut or not texte_brut.strip():
        return []

    # Détection automatique si l'utilisateur a collé le code source HTML complet
    if "<html" in texte_brut.lower() or "collection-item" in texte_brut.lower() or "<li" in texte_brut.lower():
        texte_brut = _extraire_texte_depuis_html_coop(texte_brut)

    lignes_brutes = texte_brut.split("\n")
    regex_date = re.compile(r"le\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}:\d{2})", re.IGNORECASE)
    membres_lower = {m.lower().strip() for m in (membres_inscrits or [])}

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
            if "sable" in l_normalisee:
                mat_cle = "sable"
            elif "terre" in l_normalisee:
                mat_cle = "terre"
            elif "enrob" in l_normalisee:
                mat_cle = "enrobe"
            elif "armature" in l_normalisee:
                mat_cle = "armature"
            elif "tole" in l_normalisee:
                mat_cle = "tole"
            elif "beton" in l_normalisee:
                mat_cle = "beton"
            elif "panneau" in l_normalisee:
                mat_cle = "panneaux"
            elif "tuyau" in l_normalisee:
                mat_cle = "tuyaux"
            elif "canalisation" in l_normalisee:
                mat_cle = "canalisations"
            elif "poutre" in l_normalisee:
                mat_cle = "poutres"

            if mat_cle:
                acteur_final = joueur_actif
                type_mouv_final = "REAPPROVISIONNEMENT"
                partie_droite_quantite = l_brute_clean

                # 1. Détection des réapprovisionnements
                if "reappro" in l_normalisee:
                    type_mouv_final = "REAPPROVISIONNEMENT"
                    if "réapprovisionne de" in l_brute_clean:
                        parties = l_brute_clean.split("réapprovisionne de", 1)
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        partie_droite_quantite = parties[1]
                    elif "reapprovisionne de" in l_brute_clean:
                        parties = l_brute_clean.split("reapprovisionne de", 1)
                        acteur_final = parties[0].replace("Le ", "").replace("le ", "").strip()
                        partie_droite_quantite = parties[1]
                    else:
                        acteur_final = "Réapprovisionnement Global"

                # 2. Détection des achats (internes membres vs clients externes)
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

                    type_mouv_final = "ACHAT_INTERNE" if acteur_final.lower().strip() in membres_lower else "ACHAT_EXTERNE"

                if " " in acteur_final:
                    acteur_final = acteur_final.split()[-1].strip()

                chiffres = re.findall(r"\d[\d\s]*", partie_droite_quantite)
                qte_val = float(chiffres[0].replace(" ", "")) if chiffres else 1.0

                actions_detectees.append({
                    "date": date_courante,
                    "heure": heure_courante,
                    "acteur": acteur_final.strip(),
                    "type": type_mouv_final,
                    "materiaux": {mat_cle: qte_val},
                })

    return actions_detectees
