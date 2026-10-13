# Fichier complet et certifié sans erreur : onglets/consulter_modeles.py
import streamlit as st
import pandas as pd
import database as db

def afficher_onglet_consulter_modeles():
    st.subheader("🗂️ Catalogue des Modèles de Chantiers et Étapes Techniques")
    st.write("Consultez l'intégralité des fiches pré-configurées en base de données et le détail de leurs étapes.")

    # 1. Chargement de la fonction 100% autonome verrouillée en cache (10 min)
    with st.spinner("Extraction du catalogue NoSQL cloud..."):
        catalogue_chantiers = db.charger_catalogue_chantiers()

    if not catalogue_chantiers:
        st.info("💡 Le catalogue des modèles pré-configurés est actuellement vide.")
        return

    # 2. Barre de recherche rapide
    recherche = st.text_input("🔍 Rechercher un modèle par son nom :", value="").strip()

    # Dictionnaires de traduction pour un rendu visuel impeccable
    traduction_mats = {
        "sable": "Sable (t)", "terre": "Terre (t)", "enrobe": "Enrobé (t)", "beton": "Béton (t)",
        "armature": "Armature métallique (u)", "tole": "Plaque de tôle (u)", "poutres": "Poutres en acier (u)",
        "tuyaux": "Tuyaux d'eau (u)", "canalisations": "Canalisations (u)", "panneaux": "Panneaux (u)"
    }

    # 3. Boucle d'affichage des chantiers
    compteur_affiches = 0
    for ch_id, ch_data in catalogue_chantiers.items():
        nom_modele = ch_data.get("nom_modele", ch_id)
        
        # Application du filtre de recherche textuelle
        if recherche and recherche.lower() not in nom_modele.lower():
            continue
            
        compteur_affiches += 1
        
        # En-tête du chantier (Table 1) sous forme de carte globale
        revenus = ch_data.get("revenus", 0.0)
        j = ch_data.get("jours_globaux", 0)
        h = ch_data.get("heures_globales", 0)
        m = ch_data.get("minutes_globales", 0)
        etapes = ch_data.get("etapes_techniques", [])

        # Création d'un expander principal pour chaque ouvrage détecté
        titre_expander = f"🏗️ {nom_modele} — 💰 {revenus:,.0f} € — ⏱️ {j}j {h}h {m}m ({len(etapes)} étapes)".replace(",", " ")
        
        with st.expander(titre_expander, expanded=False):
            if not etapes:
                st.caption("⚪ Aucune étape technique enregistrée pour ce modèle.")
                continue

            st.markdown("##### 📋 Décomposition des étapes techniques (Table 2)")
            
            # Balayage récursif des sous-étapes liées
            for etape in etapes:
                num_e = etape.get("num_etape", 1)
                nom_etape = etape.get("nom_etape", "Étape sans nom")
                duree_j = etape.get("duree_jours", 1)
                
                # Récupération de la main-d'œuvre
                cond = etape.get("jh_cond", 0)
                chef = etape.get("jh_chef", 0)
                ouv = etape.get("jh_ouvrier", 0)
                
                # Récupération des matériaux et engins
                mats = etape.get("materiaux", {})
                engins = etape.get("engins", [])

                # Rendu propre de la ligne d'étape
                st.markdown(f"**🔹 Étape {num_e:02d} : {nom_etape}** *({duree_j} jour(s) réel(s))*")
                
                # Structure en colonnes légères pour les attributs internes
                c_rh, c_mats, c_engins = st.columns([1, 1.2, 1.2])
                
                with c_rh:
                    st.markdown("**👥 Équipe requise :**")
                    st.markdown(f"- 🕹️ Conducteurs : `{int(cond)}`\n- 🧑‍💼 Chefs d'équipe : `{int(chef)}`\n- 👷 Ouvriers : `{int(ouv)}`")
                
                with c_mats:
                    st.markdown("**🧱 Matériaux requis :**")
                    mats_actifs = {traduction_mats.get(k, k): v for k, v in mats.items() if float(v) > 0}
                    if mats_actifs:
                        for m_nom, m_qte in mats_actifs.items():
                            st.markdown(f"- {m_nom} : `{int(m_qte)}`")
                    else:
                        st.caption("Aucun matériau requis")

                with c_engins:
                    st.markdown("**🚜 Flotte d'engins requis :**")
                    if engins:
                        for eng in engins:
                            st.markdown(f"- {eng.get('type')} `({eng.get('niveau')})`")
                    else:
                        st.caption("Aucun engin requis")
                
                st.markdown("<div style='border-bottom: 1px dashed #dedede; margin: 10px 0;'></div>", unsafe_allow_html=True)

    if compteur_affiches == 0:
        st.warning("⚠️ Aucun modèle de chantier ne correspond à votre recherche.")
