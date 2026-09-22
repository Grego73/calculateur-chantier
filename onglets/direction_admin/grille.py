# Fichier complet et certifié : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 📊 Observatoire & Grille Salariale active")
    
    # ==========================================================================
    # 🎯 1. COMPILATION ET RENDU DE LA TABLE DE SYNTHÈSE (DEPUIS FIREBASE)
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
                "📉 Prix Mini": float(d.get("prix_minimal", 0.0)),
                "📈 Prix Maxi": float(d.get("prix_maximal", 0.0)),
                "📊 Moyenne Brut": float(d.get("prix_moyen_mensuel", 0.0)),
                "⏳ Moyenne / Jour Réel": float(d.get("prix_moyen_journalier_7", 0.0))
            })
            
        if lignes_synthese:
            df_synthese = pd.DataFrame(lignes_synthese)
            
            st.markdown("#### 📋 Synthèse Générale du Marché du Travail (Enregistrée)")
            
            # 🎯 BOUTON TOUT SÉLECTIONNER POUR SUPPRESSION
            cocher_tout = st.checkbox("🔄 Tout sélectionner pour suppression", value=False, key="check_tout_synthese")
            df_synthese["Supprimer ?"] = cocher_tout
            
            # Rendu du tableau d'édition
            synthese_editee = st.data_editor(
                df_synthese, use_container_width=True, hide_index=True, key="editeur_synthese_salaires_v20",
                column_config={
                    "ID Document": None,  # Caché
                    "📉 Prix Mini": st.column_config.NumberColumn(format="%.0f €"),
                    "📈 Prix Maxi": st.column_config.NumberColumn(format="%.0f €"),
                    "📊 Moyenne Brut": st.column_config.NumberColumn(format="%.2f €"),
                    "⏳ Moyenne / Jour Réel": st.column_config.NumberColumn(format="%.2f €/j"),
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
    # ⚙️ 2. FORMULAIRE DE CALCUL EN MÉMOIRE ET UNIQUE ENREGISTREMENT
    # ==========================================================================
    st.markdown("#### ➕ Calculer et Enregistrer une Synthèse")
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    with st.form("form_grille_salariale_cloud_direct"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=150)
        
        if st.form_submit_button("💾 ENREGISTRER DIRECTEMENT LES STATS (MIN, MAX, MOYENNE)", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                liste_salaires_extraits = []
                
                for ligne in lignes:
                    l_clean = ligne.strip()
                    if not l_clean or l_clean.lower().startswith("prénom") or "salaire" in l_clean.lower():
                        continue
                    
                    # 🎯 REGEX INFAILLIBLE : Capture le prix juste avant le symbole € (ignore l'âge et le prénom)
                    match_salaire = re.search(r"([\d\s]+)\s*€", l_clean)
                    if match_salaire:
                        prix_val = float(match_salaire.group(1).replace(" ", ""))
                        liste_salaires_extraits.append(prix_val)
                
                # S'il y a des salaires valides, on fait le calcul direct
                if liste_salaires_extraits:
                    p_min = float(min(liste_salaires_extraits))
                    p_max = float(max(liste_salaires_extraits))
                    p_moyen = float(sum(liste_salaires_extraits) / len(liste_salaires_extraits))
                    p_moyen_jour_reel = p_moyen / 7.0
                    
                    # 💾 UNIQUE ÉCRITURE SUR FIREBASE (Pas de liste de recrues individuelles !)
                    cle_synthese_coop = f"{metier_cible}_{type_contrat_cible}"
                    db.db.collection("synthese_grille_tarifaire").document(cle_synthese_coop).set({
                        "poste": metier_cible,
                        "contrat": type_contrat_cible,
                        "prix_minimal": p_min,
                        "prix_maximal": p_max,
                        "prix_moyen_mensuel": p_moyen,
                        "prix_moyen_journalier_7": p_moyen_jour_reel
                    })
                    
                    st.success(f"🎰 Agrégats sauvegardés pour {metier_cible} ! Min: {p_min:.0f}€ | Max: {p_max:.0f}€ | Moy/7: {p_moyen_jour_reel:.2f}€")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Aucun salaire valide trouvé dans le texte fourni.")
            else:
                st.error("⚠️ La zone de texte est vide.")
