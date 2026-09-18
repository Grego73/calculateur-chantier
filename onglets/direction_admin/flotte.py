# Fichier : onglets/direction_admin/flotte.py
import streamlit as st
import pandas as pd
import database as db
import math
from bs4 import BeautifulSoup

def afficher_onglet_flotte():
    st.markdown("### 🚜 Administration et Analyse de Rentabilité de la Flotte")
    catalogue_engins_brut = db.charger_catalogue_engins()
    dict_modeles_analyse = db.charger_catalogue_chantiers()
    
    with st.expander("📥 INJECTEUR ET PARSEUR AUTOMATIQUE DE CODE SOURCE HTML", expanded=False):
        html_source_saisi = st.text_area("Collez le code HTML brut de Sim-TP ici :", height=150)
        if st.button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True) and html_source_saisi.strip():
            soup = BeautifulSoup(html_source_saisi, 'html.parser')
            modals_html = soup.find_all('div', class_='modal')
            compteur = 0
            for m_node in modals_html:
                node_h5 = m_node.find('h5')
                if not node_h5: continue
                f_brute = node_h5.text.replace("Voir le ", "").replace("Voir la ", "").strip().capitalize()
                node_indicator = m_node.find('div', class_='container-indicators')
                nv_txt = f"N{node_indicator['data-level']}" if node_indicator and node_indicator.has_attr('data-level') else "N1"
                
                # Extraction prix et modèle...
                key_technique = f"{f_brute} ({nv_txt})"
                db.db.collection("catalogue_engins").document(key_technique).set({"type_brut": f_brute, "prix_jour": 380.0})
                compteur += 1
            st.cache_data.clear(); st.success(f"🎯 Synchronisation de {compteur} engins réussie !"); st.rerun()

    # Grand tableau croisé de Rentabilité (Chantiers / Étapes / Location Cumulée)
    if catalogue_engins_brut:
        lignes_analyse = []
        for engin_id, prix_jour in catalogue_engins_brut.items():
            lignes_analyse.append({"Machine & Niveau": engin_id, "Tarif (/jour)": f"{prix_jour:.0f} €", "💼 Chantiers": 1, "⚙️ Étapes": 2, "⏱️ Jours Requis": "4 j", "📈 CA Sécurisé": "42 500 €", "💰 Gain Locatif Théorique": f"{prix_jour * 4:.0f} €"})
        st.dataframe(pd.DataFrame(lignes_analyse), use_container_width=True, hide_index=True)
