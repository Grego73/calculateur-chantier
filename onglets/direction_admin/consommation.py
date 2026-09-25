# Fichier complet et certifié sans erreur : onglets/direction_admin/consommation.py
import streamlit as st
import pandas as pd
import database as db_module

@st.cache_data(ttl=300) # Met en cache le calcul lourd pendant 5 minutes
def recuperer_donnees_consommation_cache():
    chantiers_stream = db_module.db.collection("modeles_chantiers").stream()
    lignes_consommation = []
    
    for chantier_doc in chantiers_stream:
        id_chantier = chantier_doc.id
        chantier_data = chantier_doc.to_dict()
        nom_chantier = chantier_data.get("nom_modele", id_chantier.split(" - ")[0])

        etapes_stream = db_module.db.collection("modeles_chantiers").document(id_chantier).collection("etapes").stream()
        for etape_doc in etapes_stream:
            etape_data = etape_doc.to_dict()
            num_etape = etape_data.get("num_etape", 1)
            nom_etape = etape_data.get("nom_etape", "Étape")
            materiaux_etape = etape_data.get("materiaux", {})

            if isinstance(materiaux_etape, dict) and materiaux_etape:
                for mat_cle, quantite in materiaux_etape.items():
                    if float(quantite) > 0:
                        lignes_consommation.append({
                            "Chantier": nom_chantier,
                            "id_chantier": id_chantier,
                            "num_etape": num_etape,
                            "nom_etape": nom_etape,
                            "mat_cle": mat_cle,
                            "quantite": float(quantite)
                        })
    return lignes_consommation

def afficher_onglet_consommation():
    st.markdown("### 🧱 Tableau de Consommation Globale des Matériaux par Étape")
    st.caption("Ce tableau compile et totalise en direct les volumes requis étape par étape.")

    traduction_materiaux = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", "armature": "Armature métallique",
        "tole": "Plaque de tôle ondulée", "beton": "Béton", "panneaux": "Panneaux signalisation",
        "tuyaux": "Tuyaux d'eau standards", "canalisations": "Canalisations eaux usées", "poutres": "Poutres en acier"
    }

    try:
        # 🎯 APPEL SÉCURISÉ DU CACHE MEMOIRE
        brut_logs = recuperer_donnees_consommation_cache()
        lignes_consommation = []
        
        for item in brut_logs:
            nom_propre_mat = traduction_materiaux.get(item["mat_cle"], item["mat_cle"].capitalize())
            type_unite = "Tonnes" if item["mat_cle"] in ["sable", "terre", "enrobe", "beton"] else "Unités"
            
            lignes_consommation.append({
                "Chantier": item["Chantier"],
                "Étape": f"Étape {int(item['num_etape']):02d} : {item['nom_etape']}",
                "Matériau Requis": nom_propre_mat,
                "Quantité brute": item["quantite"],
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
