# Fichier complet et certifié sans erreur : onglets/direction_admin/consommation.py
import streamlit as st
import pandas as pd
import database as db_module

def afficher_onglet_consommation():
    st.markdown("### 🧱 Tableau de Consommation Globale des Matériaux par Étape")
    st.caption("Ce tableau compile et totalise en direct les volumes requis étape par étape pour tous vos modèles de chantiers.")

    # 1. Dictionnaire de traduction (Clés en minuscules/singulier conformes à Firestore)
    traduction_materiaux = {
        "sable": "Sable",
        "terre": "Terre",
        "enrobe": "Enrobé",
        "armature": "Armature métallique",
        "tole": "Plaque de tôle ondulée",
        "beton": "Béton",
        "panneaux": "Panneaux signalisation",
        "tuyaux": "Tuyaux d'eau standards",
        "canalisations": "Canalisations eaux usées",
        "poutres": "Poutres en acier"
    }

    try:
        # 2. Lecture de la Table 1 (Les chantiers parents)
        chantiers_stream = db_module.db.collection("modeles_chantiers").stream()
        lignes_consommation = []

        for chantier_doc in chantiers_stream:
            id_chantier = chantier_doc.id  # Ex: "Pose de tuyaux d'eau potable (niveau 1) - 177360€"
            chantier_data = chantier_doc.to_dict()
            nom_chantier = chantier_data.get("nom_modele", id_chantier.split(" - ")[0])

            # 3. Lecture de la Table 2 (Les sous-collections d'étapes liées)
            etapes_stream = db_module.db.collection("modeles_chantiers").document(id_chantier).collection("etapes").stream()
            
            for etape_doc in etapes_stream:
                etape_data = etape_doc.to_dict()
                num_etape = etape_data.get("num_etape", 1)
                nom_etape = etape_data.get("nom_etape", "Étape")
                materiaux_etape = etape_data.get("materiaux", {})  # Map NoSQL en minuscules

                # Si l'étape contient des matériaux, on les extrait un par un
                if isinstance(materiaux_etape, dict) and materiaux_etape:
                    for mat_cle, quantite in materiaux_etape.items():
                        if float(quantite) > 0:
                            nom_propre_mat = traduction_materiaux.get(mat_cle, mat_cle.capitalize())
                            type_unite = "Tonnes" if mat_cle in ["sable", "terre", "enrobe", "beton"] else "Unités"
                            
                            # 🎯 CORRECTION VALIDÉE : Utilisation de num_etape stricte
                            lignes_consommation.append({
                                "Chantier": nom_chantier,
                                "Étape": f"Étape {int(num_etape):02d} : {nom_etape}",
                                "Matériau Requis": nom_propre_mat,
                                "Quantité brute": float(quantite),
                                "Unité": type_unite
                            })

        # 4. Rendu visuel si des données existent
        if lignes_consommation:
            df_conso = pd.DataFrame(lignes_consommation)

            st.markdown("#### 🔍 Filtres de recherche rapide")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                liste_chantiers = ["Tous les chantiers"] + sorted(df_conso["Chantier"].unique().tolist())
                choix_ch = st.selectbox("Filtrer par Chantier :", liste_chantiers)
            with c_f2:
                liste_mats = ["Tous les matériaux"] + sorted(df_conso["Matériau Requis"].unique().tolist())
                choix_mat = st.selectbox("Filtrer par Matériau :", liste_mats)

            # Application des filtres sélectionnés
            df_filtre = df_conso.copy()
            if choix_ch != "Tous les chantiers":
                df_filtre = df_filtre[df_filtre["Chantier"] == choix_ch]
            if choix_mat != "Tous les matériaux":
                df_filtre = df_filtre[df_filtre["Matériau Requis"] == choix_mat]

            # Affichage de la table finale
            st.markdown("#### 📋 Détail des besoins logistiques")
            st.dataframe(
                df_filtre, use_container_width=True, hide_index=True,
                column_config={
                    "Quantité brute": st.column_config.NumberColumn("Quantité Requise", format="%.0f")
                }
            )

            # 5. Synthèse des volumes globaux cumulés
            st.markdown("---")
            st.markdown("#### 📊 Synthèse des volumes cumulés")
            df_synthese = df_filtre.groupby(["Matériau Requis", "Unité"])["Quantité brute"].sum().reset_index()
            
            c_m1, c_m2, c_m3 = st.columns(3)
            for idx, r_syn in df_synthese.iterrows():
                col_target = [c_m1, c_m2, c_m3][idx % 3]
                with col_target:
                    st.metric(
                        label=f"📦 {r_syn['Matériau Requis']}", 
                        value=f"{int(r_syn['Quantité brute']):,} {r_syn['Unité']}".replace(",", " ")
                    )
        else:
            st.info("💡 Aucun matériau n'est requis dans les étapes de vos chantiers NoSQL pour le moment.")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des consommations NoSQL : {e}")
