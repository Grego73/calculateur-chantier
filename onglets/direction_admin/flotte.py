import re
import streamlit as st
import pandas as pd
import database as db


def afficher_onglet_flotte():
    st.markdown("### 🚜 Importation & Grille Officielle de Location de la Flotte")

    with st.expander("📥 INJECTEUR ET PARSEUR AUTOMATIQUE DE CATALOGUE (HTML)", expanded=True):
        texte_html_brut = st.text_area(
            "Collez le code source HTML de la page 'Location de matériel' (https://sim-tp.com) :",
            height=130,
            key="input_html_flotte_unique",
        )

        if st.button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True, key="btn_action_parse_flotte"):
            if texte_html_brut.strip():
                modals_machines = texte_html_brut.split('id="modal-materiel-')
                compteur = 0

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

                with st.spinner("Analyse du HTML et synchronisation Cloud en cours..."):
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

                            cle_document_nosql = f"{nom_singulier_officiel} ({niveau_machine})"

                            db.db.collection("engins").document(cle_document_nosql).set({
                                "nom_brut": nom_singulier_officiel,
                                "niveau": niveau_machine,
                                "tarif_location_jour": float(prix_val),
                            })
                            compteur += 1

                if compteur > 0:
                    st.success(f"🚀 Succès ! {compteur} fiche(s) d'engins synchronisée(s) dans la collection `engins` !")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun modèle d'engin valide n'a pu être extrait du code collé.")
            else:
                st.error("⚠️ La zone de texte est vide.")

    st.markdown("---")
    st.markdown("#### 🚜 Grille des Tarifs Enregistrés en Base de Données")

    try:
        engins_stream = db.db.collection("engins").stream()
        lignes_tableau = []
        for doc in engins_stream:
            d = doc.to_dict() or {}
            lignes_tableau.append({
                "Catégorie": d.get("nom_brut", doc.id),
                "Niveau": d.get("niveau", "—"),
                "Clé Système": doc.id,
                "Tarif Location (€/j)": float(d.get("tarif_location_jour", 380.0)),
            })

        if lignes_tableau:
            df_flotte = pd.DataFrame(lignes_tableau).sort_values(by=["Catégorie", "Niveau"])
            st.dataframe(
                df_flotte,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tarif Location (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
                },
            )
        else:
            st.info("💡 La collection `engins` est actuellement vide. Collez le HTML ci-dessus pour l'alimenter.")
    except Exception as e:
        st.error(f"Erreur d'affichage du catalogue : {e}")
