# Fichier complet et certifié : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 📊 Observatoire & Grille Salariale active")
    
    # ==========================================================================
    # 🎯 1. RENDU DE LA TABLE DE SYNTHÈSE DIRECTEMENT AU TARIF JOURNALIER
    # ==========================================================================
    try:
        synthese_stream = db.db.collection("synthese_grille_tarifaire").stream()
        lignes_synthese = []
        
        for doc in synthese_stream:
            d = doc.to_dict()
            lignes_synthese.append({
                "ID Document": doc.id,
                "🛠️ Métier": d.get("poste"),
                "📇 Type de Contrat": d.get("contrat"),
                "📉 Prix Mini (/j)": float(d.get("prix_minimal", 0.0)),
                "📈 Prix Maxi (/j)": float(d.get("prix_maximal", 0.0)),
                "📊 Moyenne Journalière": float(d.get("prix_moyen_mensuel", 0.0)) # Stocké directement en jour
            })
            
        if lignes_synthese:
            df_synthese = pd.DataFrame(lignes_synthese)
            
            st.markdown("#### 📋 Synthèse Générale du Marché du Travail (Tarifs Journaliers)")
            
            # Case globale Tout Sélectionner
            cocher_tout = st.checkbox("🔄 Tout sélectionner pour suppression", value=False, key="check_tout_synthese")
            df_synthese["Supprimer ?"] = cocher_tout
            
            # Rendu du tableau d'édition interactif
            synthese_editee = st.data_editor(
                df_synthese, use_container_width=True, hide_index=True, key="editeur_synthese_salaires_v21",
                column_config={
                    "ID Document": None,  # Reste caché en arrière-plan
                    "📉 Prix Mini (/j)": st.column_config.NumberColumn(format="%.2f €/j"),
                    "📈 Prix Maxi (/j)": st.column_config.NumberColumn(format="%.2f €/j"),
                    "📊 Moyenne Journalière": st.column_config.NumberColumn(format="%.2f €/j"),
                    "Supprimer ?": st.column_config.CheckboxColumn("🗑️ Supprimer ?", default=False)
                }
            )
            
            lignes_visees = synthese_editee[synthese_editee["Supprimer ?"] == True]
            nb_a_suppr = len(lignes_visees)
            
            if st.button(f"🔥 SUPPRIMER LES {nb_a_suppr} SYNTHÈSES SÉLECTIONNÉES", type="secondary", use_container_width=True, disabled=(nb_a_suppr == 0)):
                for doc_id in lignes_visees["ID Document"].tolist():
                    db.db.collection("synthese_grille_tarifaire").document(doc_id).delete()
                st.success("💥 Synthèse(s) effacée(s) de Firebase.")
                st.cache_data.clear()
                st.rerun()
                
            st.markdown("---")
        else:
            st.info("💡 Aucune synthèse enregistrée sur Firebase. Collez un tableau ci-dessous.")
            
    except Exception as e:
        st.error(f"⚠️ Erreur d'affichage de l'observatoire : {e}")

    # ==========================================================================
    # ⚙️ 2. FORMULAIRE DE CONVERSION ET ENREGISTREMENT JOURNALIER DIRECT
    # ==========================================================================
    st.markdown("#### ➕ Calculer et Enregistrer une Synthèse")
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    with st.form("form_grille_salariale_cloud_direct"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=150)
        
        if st.form_submit_button("💾 CALCULER ET PROPULSER LES TARIFS JOURNALIERS CUMULÉS", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.strip().split("\n")
                liste_salaires_journaliers = []
                
                for ligne in lignes:
                    l_clean = ligne.strip()
                    if not l_clean or l_clean.lower().startswith("prénom") or "salaire" in l_clean.lower():
                        continue
                    
                    match_salaire = re.search(r"([\d\s]+)\s*€", l_clean)
                    if match_salaire:
                        prix_brut = float(match_salaire.group(1).replace(" ", ""))
                        
                        # 🎯 CONVERSION IMMÉDIATE LORS DE LA SAISIE
                        if "cdi" in type_contrat_cible.lower():
                            # C'est un CDI mensuel, on le ramène tout de suite au jour réel
                            liste_salaires_journaliers.append(prix_brut / 7.0)
                        else:
                            # C'est un CDD, c'est déjà un tarif journalier
                            liste_salaires_journaliers.append(prix_brut)
                
                if liste_salaires_journaliers:
                    # Les statistiques minimales, maximales et moyennes sont désormais 100% journalières
                    p_min_j = float(min(liste_salaires_journaliers))
                    p_max_j = float(max(liste_salaires_journaliers))
                    p_moyen_j = float(sum(liste_salaires_journaliers) / len(liste_salaires_extraits if 'liste_salaires_extraits' in locals() else liste_salaires_journaliers))
                    
                    # 💾 ENREGISTREMENT DES COMPOSANTES JOURNALIÈRES DIRECTES SUR FIREBASE
                    cle_synthese_coop = f"{metier_cible}_{type_contrat_cible}"
                    db.db.collection("synthese_grille_tarifaire").document(cle_synthese_coop).set({
                        "poste": metier_cible,
                        "contrat": type_contrat_cible,
                        "prix_minimal": p_min_j,
                        "prix_maximal": p_max_j,
                        "prix_moyen_mensuel": p_moyen_j,  # Écrit en tarif jour
                        "prix_moyen_journalier_7": p_moyen_j
                    })
                    
                    st.success(f"🎰 Synthèse Journalière sauvegardée pour {metier_cible} ! Min: {p_min_j:.2f}€/j | Max: {p_max_j:.2f}€/j | Moyenne: {p_moyen_j:.2f}€/j")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Aucun salaire valide détecté.")
            else:
                st.error("⚠️ La zone de texte est vide.")
