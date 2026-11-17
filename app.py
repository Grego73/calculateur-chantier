import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import database as db
from styles import appliquer_theme_moderne, afficher_entete_page

from onglets.direction_admin import afficher_onglet_direction
from onglets.suivi_interne import afficher_onglet_suivi_interne
from onglets.suivi_contrats import afficher_onglet_suivi_contrats
from onglets.marche_actuel import afficher_onglet_marche_actuel
from onglets.rentabilite_chantiers import afficher_onglet_rentabilite_chantiers
from onglets.groupements import afficher_onglet_groupements

st.set_page_config(
    page_title="Sim-TP | Gestion & Rentabilité",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

appliquer_theme_moderne()

config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()

# ==============================================================================
# --- BARRE LATÉRALE DE NAVIGATION ---
# ==============================================================================
with st.sidebar:
    st.markdown("## 🏗️ Sim-TP Manager")
    st.caption("Pilotage financier, logistique & coopératives")
    st.markdown("---")

    navigation = st.radio(
        "Navigation :",
        [
            "📋 Contrats & Logistique",
            "📊 Rentabilité des Chantiers",
            "🤝 Groupements (GPE)",
            "👥 Espace Coopérative",
            "🌍 Marché des Coopératives",
            "🔒 Administration"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    if st.button("🔄 Actualiser les données Cloud", use_container_width=True):
        st.cache_data.clear()
        st.toast("Cache actualisé depuis Firestore !", icon="✅")
        st.rerun()

# ==============================================================================
# --- ROUTAGE DES PAGES ---
# ==============================================================================
if navigation == "📋 Contrats & Logistique":
    afficher_entete_page(
        "📋 Contrats en Cours & Logistique",
        "Croisez vos chantiers signés avec votre aire de stockage pour anticiper vos achats."
    )
    afficher_onglet_suivi_contrats()

elif navigation == "📊 Rentabilité des Chantiers":
    afficher_entete_page(
        "📊 Rentabilité & Classement des Chantiers",
        "Comparez tous vos chantiers enregistrés selon vos contrats employés (CDI/CDD) et votre flotte d'engins."
    )
    afficher_onglet_rentabilite_chantiers()

elif navigation == "🤝 Groupements (GPE)":
    afficher_entete_page(
        "🤝 Groupements d'Entreprises (GPE)",
        "Analysez les contrats de groupement, la rentabilité par phase et répartissez les lots entre associés."
    )
    afficher_onglet_groupements()

elif navigation == "👥 Espace Coopérative":
    afficher_entete_page(
        "👥 Suivi Interne de Coopérative",
        "Gérez les stocks, le fil des événements, les parts d'activité et les versements de dividendes."
    )
    afficher_onglet_suivi_interne(config_salaires, catalogue_engins, config_materiaux)

elif navigation == "🌍 Marché des Coopératives":
    afficher_entete_page(
        "🌍 Observatoire du Marché des Coopératives",
        "Comparez en temps réel les tarifs des matériaux proposés par les coopératives du serveur."
    )
    afficher_onglet_marche_actuel()

elif navigation == "🔒 Administration":
    afficher_entete_page(
        "🔒 Espace Direction & Paramétrage",
        "Importez les données brutes du jeu, mettez à jour les grilles tarifaires et gérez la base NoSQL."
    )
    afficher_onglet_direction(config_salaires, config_materiaux)
