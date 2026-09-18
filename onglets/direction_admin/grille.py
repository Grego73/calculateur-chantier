# Fichier : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import math

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 👥 Calculateur de Grille Salariale active")
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    texte_brut = st.text_area("Collez le tableau des recrues ici :", height=120)
    
    # Logique de calcul des salaires...
    if SALAIRES_DB:
        lignes_grille = [{"Clé technique NoSQL": k, "Tarif (€/j)": v, "Supprimer": False} for k, v in SALAIRES_DB.items()]
        st.data_editor(pd.DataFrame(lignes_grille), use_container_width=True, hide_index=True)

def afficher_onglet_materiaux(MATERIAUX_DB):
    st.markdown("### 🧱 Coût unitaire d'Approvisionnement des Matériaux")
    form_mats = dict(MATERIAUX_DB)
    col_m1, col_m2 = st.columns(2)
    liste_cles = list(form_mats.keys())
    milieu = math.ceil(len(liste_cles) / 2)
    
    with col_m1:
        for m_k in liste_cles[:milieu]:
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), step=1.0)
    with col_m2:
        for m_k in liste_cles[milieu:]:
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), step=1.0)
            
    if st.button("✅ RE-SYNCHRONISER LES PRIX MATÉRIAUX", type="primary", width="stretch"):
        db.db.collection("configuration_materiaux").document("catalogue").set(form_mats)
        st.cache_data.clear(); st.toast("🧱 Prix synchronisés !"); st.rerun()
