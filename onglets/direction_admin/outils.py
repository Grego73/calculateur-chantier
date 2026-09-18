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
