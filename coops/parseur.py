import re
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup

TZ_PARIS = pytz.timezone("Europe/Paris")


def normaliser_texte(texte):
    """Nettoie le texte pour éviter les pièges d'encodage et d'accents du jeu."""
    t = texte.lower()
    t = (
        t.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ô", "o")
        .replace("’", "'")
    )
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


def _detecter_materiau(ligne_normalisee):
    """Identifie la clé standardisée du matériau dans une ligne normalisée."""
    correspondances = [
        ("canalisation", "canalisations"),
        ("armature", "armature"),
        ("enrob", "enrobe"),
        ("sable", "sable"),
        ("terre", "terre"),
        ("tole", "tole"),
        ("beton", "beton"),
        ("panneau", "panneaux"),
        ("tuyau", "tuyaux"),
        ("poutre", "poutres"),
    ]
    for mot_cle, cle_officielle in correspondances:
        if mot_cle in ligne_normalisee:
            return cle_officielle
    return None


def analyser_historique_brut(texte_brut, membres_inscrits, joueur_actif):
    """
    Analyse le nouveau format (Aujourd'hui / Hier / JJ/MM/AAAA + HH:MM + Action),
    l'ancien format ('Le JJ/MM/AAAA à HH:MM') ainsi que le code HTML collé.
    """
    if not texte_brut or not texte_brut.strip():
        return []

    if (
        "<html" in texte_brut.lower()
        or "collection-item" in texte_brut.lower()
        or "<li" in texte_brut.lower()
        or "<div" in texte_brut.lower()
    ):
        texte_brut = _extraire_texte_depuis_html_coop(texte_brut)

    lignes_brutes = texte_brut.split("\n")
    membres_lower = {m.lower().strip() for m in (membres_inscrits or [])}

    maintenant_paris = datetime.now(TZ_PARIS)
    date_aujourdhui_str = maintenant_paris.strftime("%d/%m/%Y")
    date_hier_str = (maintenant_paris - timedelta(days=1)).strftime("%d/%m/%Y")

    regex_ancien_format = re.compile(r"^le\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}:\d{2})$", re.IGNORECASE)
    regex_date_seule = re.compile(r"^(\d{2}/\d{2}/\d{4})$")
    regex_heure_seule = re.compile(r"^(\d{2}:\d{2})$")
    regex_compteur_evts = re.compile(r"^\d+\s*evenements?$", re.IGNORECASE)

    date_courante = None
    heure_courante = None
    actions_detectees = []
    compteur_occurrences = {}

    for lg in lignes_brutes:
        l_brute_clean = lg.strip()
        if not l_brute_clean:
            continue

        l_normalisee = normaliser_texte(l_brute_clean)

        if "fil des" in l_normalisee or regex_compteur_evts.match(l_normalisee):
            continue

        match_ancien = regex_ancien_format.match(l_normalisee)
        if match_ancien:
            date_courante = match_ancien.group(1)
            heure_courante = match_ancien.group(2)
            continue

        if l_normalisee in ["aujourd'hui", "aujourdhui"]:
            date_courante = date_aujourdhui_str
            heure_courante = None
            continue

        if l_normalisee == "hier":
            date_courante = date_hier_str
            heure_courante = None
            continue

        match_date_seule = regex_date_seule.match(l_normalisee)
        if match_date_seule:
            date_courante = match_date_seule.group(1)
            heure_courante = None
            continue

        match_heure = regex_heure_seule.match(l_normalisee)
        if match_heure:
            heure_courante = match_heure.group(1)
            continue

        if date_courante and heure_courante:
            mat_cle = _detecter_materiau(l_normalisee)
            if not mat_cle:
                continue

            acteur_final = joueur_actif
            type_mouv_final = "REAPPROVISIONNEMENT"
            partie_droite_quantite = l_brute_clean

            if "reapprovisionne de" in l_normalisee:
                type_mouv_final = "REAPPROVISIONNEMENT"
                match_split = re.split(r"r[ée]approvisionne\s+de", l_brute_clean, maxsplit=1, flags=re.IGNORECASE)
                if len(match_split) == 2:
                    gauche = match_split[0].strip()
                    droite = match_split[1].strip()
                    acteur_candidat = re.sub(r"^le\s+", "", gauche, flags=re.IGNORECASE).strip()
                    acteur_final = acteur_candidat if acteur_candidat else "Réapprovisionnement Global"
                    partie_droite_quantite = droite
                else:
                    acteur_final = "Réapprovisionnement Global"

            elif "a achete" in l_normalisee:
                match_split = re.split(r"a\s+achet[ée]", l_brute_clean, maxsplit=1, flags=re.IGNORECASE)
                if len(match_split) == 2:
                    gauche = match_split[0].strip()
                    droite = match_split[1].strip()
                    acteur_candidat = re.sub(r"^le\s+", "", gauche, flags=re.IGNORECASE).strip()
                    acteur_final = acteur_candidat if acteur_candidat else joueur_actif
                    partie_droite_quantite = droite
                else:
                    acteur_final = joueur_actif

                type_mouv_final = (
                    "ACHAT_INTERNE"
                    if acteur_final.lower().strip() in membres_lower
                    else "ACHAT_EXTERNE"
                )
            else:
                continue

            chiffres = re.findall(r"\d[\d\s]*", partie_droite_quantite)
            qte_val = float(chiffres[0].replace(" ", "")) if chiffres else 1.0

            cle_signature = (
                date_courante,
                heure_courante,
                acteur_final.lower().strip(),
                type_mouv_final,
                mat_cle,
                int(qte_val),
            )
            compteur_occurrences[cle_signature] = compteur_occurrences.get(cle_signature, 0) + 1
            num_occurrence = compteur_occurrences[cle_signature]

            actions_detectees.append({
                "date": date_courante,
                "heure": heure_courante,
                "acteur": acteur_final.strip(),
                "type": type_mouv_final,
                "materiaux": {mat_cle: qte_val},
                "occurrence": num_occurrence,
            })

    return actions_detectees
