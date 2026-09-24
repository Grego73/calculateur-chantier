# Fichier : onglets/direction_admin/outils.py
import streamlit as st
import pandas as pd
import database as db
import datetime
import pytz

def afficher_comparateur():
    st.markdown("### 🔎 Outil de Comparaison de Modèles")

def afficher_quotas():
    st.markdown("### 📊 Suivi de Consommation & Quotas Firebase (Plan Spark)")
    st.progress(0.12, text="Lectures : 1 240 / 50 000 (2.4%)")

def afficher_journaux():
    st.markdown("### 📜 Journal d'Audit & Traçabilité Cloud NoSQL")
    try:
        logs = [d.to_dict() for d in db.db.collection("journaux_actions").limit(50).stream()]
        if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    except Exception: st.info("Aucun log disponible.")

def afficher_barre_diagnostic_globale():
    """Affiche le panneau de contrôle des variables sur toutes les pages du site"""
    st.markdown("---")
    with st.expander("🔍 Centre de Diagnostic Global (Mode Développeur)", expanded=False):
        st.info("Ce panneau central affiche les variables partagées en mémoire pour tout le site.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 📱 État de la Session (`st.session_state`)")
            # Affiche absolument tout ce qui est stocké en mémoire partagée
            st.json(dict(st.session_state))
        
        with c2:
            st.markdown("##### ⚙️ Infos de Connexion actives")
            infos_auth = {
                "Coopérative connectée": st.session_state.get("auth_suivi_coop", "Aucune"),
                "Utilisateur actif": st.session_state.get("auth_suivi_joueur", "Aucun"),
                "Niveau de privilèges (Grade)": st.session_state.get("coop_privilege_level", "Non connecté")
            }
            st.json(infos_auth)
