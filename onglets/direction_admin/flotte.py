import re
import math
import streamlit as st
import pandas as pd
import database as db


def _extraire_engins_depuis_html(html_brut):
    """Extrait {cle_doc: {'nom_brut': ..., 'niveau': ..., 'prix': ...}} depuis un HTML location ou neuf."""
    dictionnaire_singulier = {
        "camions benne": "Camion benne",
        "camion benne": "Camion benne",
        "pelleteuses": "Pelleteuse",
        "pelleteuse": "Pelleteuse",
        "petite pelleteuse": "Pelleteuse",
        "grosse pelleteuse": "Pelleteuse",
        "mini-pelle": "Pelleteuse",
        "compacteurs de sol": "Compacteur de sol",
        "compacteur de sol": "Compacteur de sol",
        "compacteur pour enrobé": "Compacteur d'enrobé",
        "compacteur d'enrobé": "Compacteur d'enrobé",
        "compacteur": "Compacteur d'enrobé",
        "finisseur": "Finisseur",
        "les finisseurs": "Finisseur",
        "camion béton malaxeur": "Camion malaxeur",
        "camions béton malaxeur": "Camion malaxeur",
        "camion malaxeur": "Camion malaxeur",
        "camion pompe à béton": "Camion malaxeur",
        "chargeuse compacte": "Chargeuse compacte",
        "chargeuse": "Chargeuse",
        "chargeur téléscopique": "Chargeur téléscopique",
        "chargeur télescopique": "Chargeur téléscopique",
        "niveleuse": "Niveleuse",
        "fraiseuse": "Fraiseuse",
        "camion grue": "Grue mobile",
        "grue mobile": "Grue mobile",
    }

    resultats = {}
    modals_machines = html_brut.split('id="modal-materiel-')

    for bloc_html in modals_machines[1:]:
        if not bloc_html.strip():
            continue

        match_nom = re.search(r"<h5>Voir (?:le|la|l')\s*([^<]+)</h5>", bloc_html, re.IGNORECASE)
        match_niveau = re.search(r"<li>Niveau\s+(\d+)\s*:", bloc_html, re.IGNORECASE)
        match_prix = re.search(r"Prix\s*:\s*([\d\s]+)\s*euros", bloc_html, re.IGNORECASE)

        if match_nom and match_niveau and match_prix:
            nom_brut_jeu = match_nom.group(1).strip().lower()
            niveau_machine = f"N{match_niveau.group(1).strip()}"
            prix_val = float("".join(c for c in match_prix.group(1) if c.isdigit()))

            nom_singulier_officiel = dictionnaire_singulier.get(
                nom_brut_jeu, match_nom.group(1).strip().capitalize()
            )
            cle_doc = f"{nom_singulier_officiel} ({niveau_machine})"

            # On garde le prix le plus bas si plusieurs modèles existent au même niveau
            if cle_doc not in resultats or prix_val < resultats[cle_doc]["prix"]:
                resultats[cle_doc] = {
                    "nom_brut": nom_singulier_officiel,
                    "niveau": niveau_machine,
                    "prix": prix_val,
                }

    return resultats


def afficher_onglet_flotte():
    st.markdown("### 🚜 Importation & Rentabilité de la Flotte (Location vs Neuf)")

    with st.expander("📥 INJECTEUR AUTOMATIQUE DE CATALOGUE (HTML)", expanded=True):
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            html_location = st.text_area(
                "1️⃣ Code HTML 'Location de matériel' (/location) :",
                height=130,
                key="input_html_flotte_loc",
            )
        with col_h2:
            html_neuf = st.text_area(
                "2️⃣ Code HTML 'Catalogue neuf' (/catalogue-neuf) [Optionnel] :",
                height=130,
                key="input_html_flotte_neuf",
            )

        if st.button("⚡ SYNCHRONISER LA FLOTTE SUR FIREBASE", type="primary", use_container_width=True, key="btn_action_parse_flotte"):
            if not html_location.strip() and not html_neuf.strip():
                st.error("⚠️ Collez au moins le code HTML de la page Location ou Catalogue Neuf.")
            else:
                with st.spinner("Analyse des catalogues et synchronisation Cloud en cours..."):
                    donnees_loc = _extraire_engins_depuis_html(html_location) if html_location.strip() else {}
                    donnees_neuf = _extraire_engins_depuis_html(html_neuf) if html_neuf.strip() else {}

                    toutes_cles = set(donnees_loc.keys()) | set(donnees_neuf.keys())
                    compteur = 0

                    for cle_doc in toutes_cles:
                        info_base = donnees_loc.get(cle_doc) or donnees_neuf.get(cle_doc)
                        payload = {
                            "nom_brut": info_base["nom_brut"],
                            "niveau": info_base["niveau"],
                        }
                        if cle_doc in donnees_loc:
                            payload["tarif_location_jour"] = float(donnees_loc[cle_doc]["prix"])
                        if cle_doc in donnees_neuf:
                            payload["prix_achat_neuf"] = float(donnees_neuf[cle_doc]["prix"])

                        db.db.collection("engins").document(cle_doc).set(payload, merge=True)
                        compteur += 1

                if compteur > 0:
                    st.success(f"🚀 Succès ! {compteur} catégorie(s) d'engins synchronisée(s) dans Firebase !")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun engin valide détecté dans les codes HTML fournis.")

    st.markdown("---")
    st.markdown("#### 📊 Comparatif Location vs Achat Neuf en Base")

    try:
        engins_stream = db.db.collection("engins").stream()
        lignes_tableau = []
        for doc in engins_stream:
            d = doc.to_dict() or {}
            px_loc = float(d.get("tarif_location_jour", 0.0))
            px_neuf = float(d.get("prix_achat_neuf", 0.0))
            seuil_jours = math.ceil(px_neuf / px_loc) if (px_neuf > 0 and px_loc > 0) else 0

            lignes_tableau.append({
                "Catégorie": d.get("nom_brut", doc.id),
                "Niveau": d.get("niveau", "—"),
                "Location (€/j)": px_loc,
                "Prix Neuf (€)": px_neuf,
                "Amorti en (Jours)": seuil_jours,
            })

        if lignes_tableau:
            df_flotte = pd.DataFrame(lignes_tableau).sort_values(by=["Catégorie", "Niveau"])
            st.dataframe(
                df_flotte,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Location (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
                    "Prix Neuf (€)": st.column_config.NumberColumn(format="%.0f €"),
                    "Amorti en (Jours)": st.column_config.NumberColumn(format="%d j"),
                },
            )
            st.caption("💡 **Lecture :** La colonne *Amorti en (Jours)* indique au bout de combien de jours d'utilisation l'achat neuf devient plus rentable que la location.")
        else:
            st.info("💡 La collection `engins` est actuellement vide.")
    except Exception as e:
        st.error(f"Erreur d'affichage du catalogue : {e}")
