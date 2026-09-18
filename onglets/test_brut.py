import streamlit as st
import pandas as pd
import database as db

def afficher_onglet_test_brut():
    st.title("🚨 Vue Intégrale & Centre de Nettoyage NoSQL")
    st.warning("Cette page affiche absolument TOUTES les colonnes détectées dans Firestore sans aucune restriction.")

    # 1. Récupération de la liste des coopératives disponibles
    try:
        coops = [doc.id for doc in db.db.collection("cooperatives").stream()]
    except Exception as e:
        st.error(f"Impossible de lister les coopératives : {e}")
        return

    if not coops:
        st.info("💡 Aucune coopérative trouvée dans Firestore.")
        return

    # 2. Sélection de la coopérative à analyser
    coop_cible = st.selectbox("Sélectionner la coopérative à inspecter :", coops, key="sb_coop_brut_total")

    if coop_cible:
        st.markdown(f"### 📋 Base de données brute complète pour : `{coop_cible}`")
        
        try:
            # Requête réseau vers la sous-collection Firestore
            doc_ref_coop = db.db.collection("cooperatives").document(coop_cible)
            flux_stream = doc_ref_coop.collection("comptabilite_interne").stream()
            liste_documents_bruts = []
            
            for doc in flux_stream:
                donnees_doc = doc.to_dict()
                
                # Inclusion explicite des identifiants et des chemins systèmes de Firebase
                donnees_doc["ID_Document_Firestore"] = str(doc.id)
                donnees_doc["_Chemin_Systeme_Firestore"] = str(doc.reference.path)
                
                # Formatage des dictionnaires imbriqués sous forme de texte pour éviter les bugs d'affichage de cellules
                for cle, valeur in list(donnees_doc.items()):
                    if isinstance(valeur, dict):
                        donnees_doc[cle] = str(valeur)
                
                liste_documents_bruts.append(donnees_doc)
                
            if liste_documents_bruts:
                df_brut = pd.DataFrame(liste_documents_bruts)
                
                # Pour s'assurer que les identifiants techniques et de suppression entourent proprement les données
                colonnes = list(df_brut.columns)
                if "ID_Document_Firestore" in colonnes:
                    colonnes.remove("ID_Document_Firestore")
                    colonnes.insert(0, "ID_Document_Firestore")
                if "_Chemin_Systeme_Firestore" in colonnes:
                    colonnes.remove("_Chemin_Systeme_Firestore")
                    colonnes.append("_Chemin_Systeme_Firestore")
                
                df_brut = df_brut[colonnes]
                
                # Ajout de la colonne de suppression manuelle
                df_brut["Sélectionner pour suppression"] = False
                
                # Rendu automatique complet de toutes les colonnes sans structure restrictive column_config
                tableau_interactif = st.data_editor(
                    df_brut,
                    width="stretch",
                    hide_index=True,
                    key="editeur_nettoyage_brut_maximal",
                    column_config={
                        "_Chemin_Systeme_Firestore": None, # Masqué en arrière-plan uniquement pour exécution réseau
                        "Sélectionner pour suppression": st.column_config.CheckboxColumn(
                            "🗑️ Supprimer ?",
                            help="Cochez cette case pour purger définitivement la ligne",
                            default=False
                        )
                    }
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # MOTEUR DE PURGE DES COMPTES ASSOCIÉS
                if st.button("🔥 SUPPRIMER DÉFINITIVEMENT LES LIGNES SÉLECTIONNÉES", type="primary", width="stretch", key="btn_purge_maximale"):
                    lignes_a_supprimer = tableau_interactif[tableau_interactif["Sélectionner pour suppression"] == True]
                    
                    if lignes_a_supprimer.empty:
                        st.error("⚠️ Veuillez cocher au moins une ligne du tableau avant de lancer l'opération.")
                    else:
                        compteur_suppressions = 0
                        with st.spinner("Purge réseau en cours sur Google Cloud..."):
                            for _, row in lignes_a_supprimer.iterrows():
                                path_cible = str(row["_Chemin_Systeme_Firestore"]).strip()
                                if path_cible:
                                    db.db.document(path_cible).delete()
                                    compteur_suppressions += 1
                        
                        db.enregistrer_log("NETTOYAGE_EXPLICITE", f"Purge manuelle intégrale de {compteur_suppressions} document(s) pour {coop_cible}.")
                        st.success(f"💥 {compteur_suppressions} document(s) NoSQL effacé(s) de votre serveur cloud !")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("💡 Aucun document trouvé dans la table de cette coopérative.")
                
        except Exception as e:
            st.error(f"Erreur d'extraction sur la table système globale : {e}")
