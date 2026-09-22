# Fichier complet : onglets/direction_admin/engins_jeu.py
import streamlit as st
import pandas as pd
import database as db

def afficher_onglet_catalogue_engins_total():
    st.markdown("### 🚜 Catalogue Officiel des Engins du Jeu (Prix Neufs & Locations)")
    st.info("Saisissez ici les tarifs constructeurs officiels du jeu. Ces valeurs alimenteront automatiquement les menus déroulants de la page d'ajout de chantier.")

    # 1. FORMULAIRE D'INJECTION EN BASE
    with st.form("form_nouvel_engin_jeu"):
        st.markdown("#### ➕ Ajouter ou Mettre à jour un Engin")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            nom_engin = st.text_input("Nom de l'engin (Ex: Pelle, Camion, Dumper) :").strip().capitalize()
        with col_e2:
            niveau_engin = st.selectbox("Niveau requis :", ["N1", "N2", "N3", "N4"])
        with col_e3:
            prix_location = st.number_input("Tarif Location (€/jour) :", min_value=0.0, step=10.0, value=380.0)
            
        if st.form_submit_button("💾 SYNCHRONISER L'ENGIN SUR FIREBASE", type="primary", use_container_width=True):
            if nom_engin:
                # Clé unique NoSQL propre (Ex: "Pelle N1")
                cle_engin = f"{nom_engin} {niveau_engin}"
                
                db.db.collection("configuration_engins").document(cle_engin).set({
                    "nom_brut": nom_engin,
                    "niveau": niveau_engin,
                    "prix_location_jour": float(prix_location)
                })
                st.success(f"🟢 {cle_engin} synchronisé avec succès à {prix_location:.0f} €/j !")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("⚠️ Le nom de l'engin ne peut pas être vide.")

    st.markdown("---")
    st.markdown("#### 📜 Liste des Engins du Jeu enregistrés")

    # 2. AFFICHAGE ET PURGE DU CATALOGUE
    try:
        engins_stream = db.db.collection("configuration_engins").stream()
        liste_engins = []
        for doc in engins_stream:
            d = doc.to_dict()
            liste_engins.append({
                "ID Document": doc.id,
                "🚜 Catégorie": d.get("nom_brut"),
                "🎖️ Niveau": d.get("niveau"),
                "💰 Location (€/j)": float(d.get("prix_location_jour", 380.0))
            })
            
        if liste_engins:
            df_engins = pd.DataFrame(liste_engins)
            
            # Case globale Tout Sélectionner
            cocher_tout = st.checkbox("🔄 Tout sélectionner pour suppression", value=False, key="check_tout_engins_catalogue")
            df_engins["Supprimer ?"] = cocher_tout
            
            engins_edites = st.data_editor(
                df_engins, use_container_width=True, hide_index=True, key="editeur_catalogue_engins_total",
                column_config={
                    "ID Document": None,
                    "💰 Location (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
                    "Supprimer ?": st.column_config.CheckboxColumn("🗑️ Supprimer ?", default=False)
                }
            )
            
            if st.button("🔥 SUPPRIMER LES ENGINS SÉLECTIONNÉS", type="secondary", use_container_width=True):
                ids_a_supprimer = engins_edites[engins_edites["Supprimer ?"] == True]["ID Document"].tolist()
                for doc_id in ids_a_supprimer:
                    db.db.collection("configuration_engins").document(doc_id).delete()
                st.success(f"💥 {len(ids_a_supprimer)} engin(s) retiré(s) du catalogue.")
                st.cache_data.clear()
                st.rerun()
        else:
            st.info("💡 Aucun engin dans le catalogue Cloud. Utilisez le formulaire ci-dessus.")
    except Exception as e:
        st.error(f"Erreur catalogue : {e}")
