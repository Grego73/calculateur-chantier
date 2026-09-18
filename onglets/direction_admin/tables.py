# Fichier complet et certifié sans erreur : onglets/direction_admin/tables.py
import streamlit as st
import pandas as pd
import database as db

def afficher_centre_controle():
    st.markdown("### 📁 Centre de Contrôle NoSQL & Nettoyage des Tables")
    st.caption("Sélectionnez une table système pour inspecter les données brutes. Cochez les cases en fin de ligne pour supprimer définitivement des éléments sur Firebase.")

    choix_table = st.selectbox(
        "Choisir la table système à auditer :",
        [
            "Modèles de Chantiers Pré-configurés", 
            "Chantiers Validés (Historique Général)",
            "Comptabilité Interne (Flux des Coopératives)",
            "Journaux d'Audit (Logs Système)"
        ],
        key="selectbox_audit_tables_split"
    )

    # --- TABLE 1 & 2 REGROUPÉES : TOUTES LES COLONNES CUMULÉES DES DEUX TABLES ---
    if choix_table == "Modèles de Chantiers Pré-configurés":
        try:
            modeles_stream = db.db.collection("modeles_chantiers").stream()
            lignes_globales_modeles = []
            
            with st.spinner("Compilation récursive des tables NoSQL..."):
                for doc in modeles_stream:
                    d = doc.to_dict()
                    
                    # --- NOUVEAUTÉ : Lecture et scan automatique de la Table 2 (Sous-collection etapes) ---
                    etapes_stream = doc.reference.collection("etapes").stream()
                    
                    total_cond = 0
                    total_chef = 0
                    total_ouvrier = 0
                    total_engins_count = 0
                    
                    cumul_mats = {
                        "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, 
                        "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, 
                        "canalisations": 0.0, "poutres": 0.0
                    }
                    
                    for etape_doc in etapes_stream:
                        etape = etape_doc.to_dict()
                        if not etape:
                            continue
                            
                        # Somme des effectifs RH de la Table 2
                        total_cond += int(etape.get("jh_cond", 0))
                        total_chef += int(etape.get("jh_chef", 0))
                        total_ouvrier += int(etape.get("jh_ouvrier", 0))
                        
                        # Somme des volumes de matériaux de la Table 2
                        mats_etape = etape.get("materiaux", {})
                        for m_nom, qte in mats_etape.items():
                            m_nom_clean = m_nom.lower().replace("é", "e").replace("ô", "o")
                            if m_nom_clean in cumul_mats:
                                cumul_mats[m_nom_clean] += float(qte)
                                
                        # Compte des machines de la Table 2
                        total_engins_count += len(etape.get("engins", []))
                    
                    # Assemblage final de la ligne consolidée
                    lignes_globales_modeles.append({
                        "ID Document": doc.id,
                        "🏗️ Nom du Modèle": d.get("nom_modele", doc.id),                        
                        "💰 CA Prévu (€)": float(d.get("revenus", 0.0)),
                        "⏱️ Durée (j)": int(d.get("jours_globaux", 0)),
                        "🕹️ Cond (jh)": total_cond,
                        "🧑‍💼 Chefs (jh)": total_chef,
                        "👷 Ouv (jh)": total_ouvrier,
                        "🧱 Sable (t)": cumul_mats["sable"],
                        "🧱 Terre (t)": cumul_mats["terre"],
                        "🧱 Enrobé (t)": cumul_mats["enrobe"],
                        "🧱 Béton (t)": cumul_mats["beton"],
                        "🔩 Armat. (u)": cumul_mats["armature"],
                        "💿 Tôles (u)": cumul_mats["tole"],
                        "🪵 Poutres (u)": cumul_mats["poutres"],
                        "🚰 Tuyaux (u)": cumul_mats["tuyaux"],
                        "🚜 Engins (Qté)": total_engins_count
                    })
                
            if lignes_globales_modeles:
                df_global_mod = pd.DataFrame(lignes_globales_modeles)
                df_global_mod["Supprimer ?"] = False
                
                mod_edite = st.data_editor(
                    df_global_mod, width="stretch", hide_index=True, key="editor_nettoyage_modeles_split_v15",
                    column_config={
                        "ID Document": None,  # Masque la colonne ID brute pour garder l'écran propre
                        "💰 CA Prévu (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "⏱️ Durée (j)": st.column_config.NumberColumn(format="%d j"),
                        "🕹️ Cond (jh)": st.column_config.NumberColumn(format="%d jh"),
                        "🧑‍💼 Chefs (jh)": st.column_config.NumberColumn(format="%d jh"),
                        "👷 Ouv (jh)": st.column_config.NumberColumn(format="%d jh"),
                        "🧱 Sable (t)": st.column_config.NumberColumn(format="%.0f t"),
                        "🧱 Terre (t)": st.column_config.NumberColumn(format="%.0f t"),
                        "🧱 Enrobé (t)": st.column_config.NumberColumn(format="%.0f t"),
                        "🧱 Béton (t)": st.column_config.NumberColumn(format="%.0f t"),
                        "🔩 Armat. (u)": st.column_config.NumberColumn(format="%d u"),
                        "💿 Tôles (u)": st.column_config.NumberColumn(format="%d u"),
                        "🪵 Poutres (u)": st.column_config.NumberColumn(format="%d u"),
                        "🚰 Tuyaux (u)": st.column_config.NumberColumn(format="%d u"),
                        "🚜 Engins (Qté)": st.column_config.NumberColumn(format="%d machine(s)"),
                        "Supprimer ?": st.column_config.CheckboxColumn(default=False)
                    }
                )
                
                if st.button("🔥 EFFACER LES MODÈLES SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_mod_split_v15"):
                    docs_a_supprimer = mod_edite[mod_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    if not docs_a_supprimer:
                        st.error("⚠️ Veuillez cocher au moins une case avant de valider la suppression.")
                    else:
                        for doc_id in docs_a_supprimer:
                            doc_ref = db.db.collection("modeles_chantiers").document(doc_id)
                            # Purge en cascade de la Table 2
                            sub_etapes = doc_ref.collection("etapes").stream()
                            for et in sub_etapes:
                                et.reference.delete()
                            # Purge de la Table 1
                            doc_ref.delete()
                        db.enregistrer_log("NETTOYAGE", f"Suppression de {len(docs_a_supprimer)} modèle(s) et de leurs sous-étapes techniques.")
                        st.success(f"🟢 {len(docs_a_supprimer)} modèle(s) effacé(s) de Firebase.")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("💡 Le catalogue des modèles pré-configurés est vide.")
        except Exception as e: 
            st.error(f"❌ Erreur lors de la compilation croisée des deux tables : {e}")

    # --- RELANCE DU RENDU CLASSIQUE POUR LES AUTRES SELECTIONS SANS MODIFICATION ---
    elif choix_table == "Chantiers Validés (Historique Général)":
        try:
            chantiers_stream = db.db.collection("chantiers").stream()
            lignes_chantiers = []
            for doc in chantiers_stream:
                d = doc.to_dict()
                lignes_chantiers.append({
                    "ID Document": doc.id, "🏗️ Nom du Chantier": doc.id, "💰 CA (€)": float(d.get("revenus", 0.0)),
                    "🧱 Matériaux (€)": float(d.get("cout_materiaux", 0.0)), "🚜 Locations (€)": float(d.get("cout_location", 0.0)),
                    "👥 Salaires (€)": float(d.get("cout_salaires", 0.0)), "📉 Dépenses (€)": float(d.get("depenses_totales", 0.0)),
                    "📈 Bénéfice (€)": float(d.get("benefice_net", 0.0)), "⏱️ Durée (j)": float(d.get("jours", 0.0)),
                    "⚡ Gain/j (€)": float(d.get("gain_par_jour", 0.0)), "📊 ROI (%)": f"{d.get('roi', 0.0):.2f} %"
                })
            if lignes_chantiers:
                df_ch = pd.DataFrame(lignes_chantiers)
                df_ch["Supprimer ?"] = False
                ch_edite = st.data_editor(df_ch, width="stretch", hide_index=True, key="editor_nettoyage_chantiers_split")
                if st.button("🔥 SUPPRIMER LES CHANTIERS SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_ch_split"):
                    ids_a_detruire = ch_edite[ch_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    for doc_id in ids_a_detruire: db.db.collection("chantiers").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_detruire)} chantier(s) nettoyé(s) !")
                    st.cache_data.clear(); st.rerun()
            else: st.info("💡 Aucun chantier validé en base.")
        except Exception as e: st.error(f"Erreur chantiers : {e}")

    elif choix_table == "Comptabilité Interne (Flux des Coopératives)":
        try:
            coops_stream = db.db.collection_group("comptabilite_interne").stream()
            lignes_coop = []
            for doc in coops_stream:
                d = doc.to_dict()
                lignes_coop.append({
                    "ID Document": doc.id, "Path": doc.reference.path, "👤 Acteur": d.get("joueur", "Inconnu"),
                    "🏷️ Action": d.get("type", "Inconnu"), "💰 Apport Cash": f"{d.get('apport_cash', 0.0):,.0f} €".replace(",", " ")
                })
            if lignes_coop:
                df_cp = pd.DataFrame(lignes_coop)
                df_cp["Supprimer ?"] = False
                cp_edite = st.data_editor(df_cp, width="stretch", hide_index=True, key="editor_nettoyage_coops_split")
                if st.button("🔥 EFFACER LES TRANSACTION COOP COCHÉES", type="primary", width="stretch", key="btn_clear_coop_split"):
                    paths_a_suppr = cp_edite[cp_edite["Supprimer ?"] == True]["Path"].tolist()
                    for path in paths_a_suppr: 
                        db.db.document(path).delete()
                    st.success(f"💥 {len(paths_a_suppr)} flux effacé(s).")
                    st.cache_data.clear()
                    st.rerun()
            else: 
                st.info("💡 Trésorerie des coopératives vide.")
        except Exception as e: 
            st.error(f"Erreur flux coop : {e}")

    elif choix_table == "Journaux d'Audit (Logs Système)":
        try:
            logs_stream = db.db.collection("journaux_actions").stream()
            lignes_logs = []
            for doc in logs_stream:
                d = doc.to_dict()
                lignes_logs.append({
                    "ID Document": doc.id, 
                    "📅 Date": d.get("timestamp", "Inconnue"),
                    "🏷️ Catégorie": d.get("type_action", "Inconnu"), 
                    "📝 Message d'Audit": d.get("details", "")
                })
            if lignes_logs:
                df_lg = pd.DataFrame(lignes_logs).sort_values(by="📅 Date", ascending=False)
                df_lg["Supprimer ?"] = False
                lg_edite = st.data_editor(df_lg, width="stretch", hide_index=True, key="editor_nettoyage_logs_split")
                if st.button("🔥 PURGER LES LOGS SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_logs_split"):
                    ids_a_suppr = lg_edite[lg_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    for doc_id in ids_a_suppr: 
                        db.db.collection("journaux_actions").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_suppr)} log(s) purgé(s).")
                    st.rerun()
            else: 
                st.info("💡 Journaux d'audit vides.")
        except Exception as e: 
            st.error(f"Erreur logs : {e}")
