import streamlit as st
import pandas as pd
import database as db


def afficher_onglet_marche_actuel():
    try:
        offres_stream = db.db.collection("offres_cooperatives").stream()
        offres_brutes = [doc.to_dict() for doc in offres_stream if doc.to_dict()]

        if not offres_brutes:
            st.info("💡 L'observatoire du marché est vide. Un administrateur doit importer le code HTML depuis **Administration > Import Données Jeu**.")
            return

        harmonisation_noms = {
            "Armature": "Armature métallique",
            "Tôle": "Plaque de tôle ondulée",
            "Tuyaux": "Tuyaux d'eau standards",
            "Canalisations": "Canalisations eaux usées",
            "Poutres": "Poutres en acier",
            "Panneaux": "Panneaux de signalisation",
        }

        lignes_tableau = []
        meilleurs_par_mat = {}

        for data in offres_brutes:
            mat_brut = data.get("materiau", "Inconnu")
            mat_nom = harmonisation_noms.get(mat_brut, mat_brut)
            t_log = "🧱 Vrac (Tonne)" if data.get("type_logistique") == "vrac" else "⚙️ Structure (Unité)"
            prix_u = float(data.get("prix_unitaire", 0.0))
            unite = data.get("unite", "u")
            coop = data.get("cooperative", "Inconnue")
            dispo = data.get("quantite_dispo", "illimité")

            lignes_tableau.append({
                "Catégorie": t_log,
                "Matériau": mat_nom,
                "Coopérative": coop,
                "Prix Unitaire (€)": prix_u,
                "Unité": unite,
                "Disponibilité": dispo,
            })

            if mat_nom not in meilleurs_par_mat or prix_u < meilleurs_par_mat[mat_nom]["prix"]:
                meilleurs_par_mat[mat_nom] = {"prix": prix_u, "coop": coop, "unite": unite}

        df_marche = pd.DataFrame(lignes_tableau).sort_values(by=["Catégorie", "Matériau", "Prix Unitaire (€)"])

        # 1. Filtres rapides en haut de page
        col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 1])
        with col_f1:
            liste_mats = ["Tous les matériaux"] + sorted(df_marche["Matériau"].unique().tolist())
            filtre_mat = st.selectbox("🔍 Filtrer par matériau :", liste_mats)
        with col_f2:
            liste_coops = ["Toutes les coopératives"] + sorted(df_marche["Coopérative"].unique().tolist())
            filtre_coop = st.selectbox("🏢 Filtrer par coopérative :", liste_coops)
        with col_f3:
            masquer_simtp = st.checkbox("Masquer la Coopérative Sim-TP (prix max)", value=True)

        df_filtre = df_marche.copy()
        if filtre_mat != "Tous les matériaux":
            df_filtre = df_filtre[df_filtre["Matériau"] == filtre_mat]
        if filtre_coop != "Toutes les coopératives":
            df_filtre = df_filtre[df_filtre["Coopérative"] == filtre_coop]
        if masquer_simtp:
            df_filtre = df_filtre[~df_filtre["Coopérative"].str.contains("Sim-TP", case=False, na=False)]

        # 2. Cartes des meilleurs prix actuels (Vrac vs Structure)
        st.markdown("### 🏆 Meilleurs Tarifs Relevés sur le Marché")
        cols_top = st.columns(5)
        for idx, (mat_cle, info) in enumerate(sorted(meilleurs_par_mat.items())):
            with cols_top[idx % 5]:
                st.metric(
                    label=mat_cle,
                    value=f"{int(info['prix'])} € / {info['unite']}",
                    delta=info["coop"],
                    delta_color="off",
                )

        st.markdown("---")

        # 3. Tableau détaillé des offres
        st.markdown(f"### 📋 Détail des Offres ({len(df_filtre)} offre(s) affichée(s))")
        st.dataframe(
            df_filtre,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prix Unitaire (€)": st.column_config.NumberColumn(format="%.0f €"),
            },
        )

    except Exception as e:
        st.error(f"❌ Impossible de charger les données du marché : {e}")
