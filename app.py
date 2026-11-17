import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import database as db
from styles import appliquer_theme_moderne, afficher_entete_page

# Importations des modules applicatifs
from onglets.direction_admin import afficher_onglet_direction
from onglets.suivi_interne import afficher_onglet_suivi_interne
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique
from onglets.suivi_contrats import afficher_onglet_suivi_contrats
from onglets.marche_actuel import afficher_onglet_marche_actuel
from onglets.consulter_modeles import afficher_onglet_consulter_modeles

# Configuration générale de la page
st.set_page_config(
    page_title="Sim-TP | Gestion & Rentabilité",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

appliquer_theme_moderne()

# Chargement des configurations globales (en cache rapide)
config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()
types_engins = db.charger_types_engins_bruts()

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
            "🧮 Simulateur & Modèles",
            "📊 Historique & Rentabilité",
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

elif navigation == "🧮 Simulateur & Modèles":
    afficher_entete_page(
        "🧮 Simulateur de Chantiers & Modèles NoSQL",
        "Consultez la rentabilité des ouvrages pré-configurés ou réalisez une simulation sur-mesure."
    )
    tab_sim, tab_mod = st.tabs(["➕ Calculateur de Rentabilité", "🗂️ Catalogue des Modèles"])
    with tab_sim:
        afficher_onglet_ajouter(config_salaires, config_materiaux, catalogue_engins, types_engins)
    with tab_mod:
        afficher_onglet_consulter_modeles()

elif navigation == "📊 Historique & Rentabilité":
    afficher_entete_page(
        "📊 Historique & Classement des Chantiers",
        "Suivez vos performances globales, votre ROI moyen par jour et vos meilleurs projets."
    )
    afficher_onglet_historique()

elif navigation == "🤝 Groupements (GPE)":
    afficher_entete_page(
        "🤝 Groupements d'Entreprises (GPE)",
        "Analysez les contrats de groupement, la rentabilité par phase et répartissez les lots entre associés."
    )
    try:
        from onglets.groupements import afficher_onglet_groupements
        afficher_onglet_groupements()
    except ImportError:
        st.info("🚧 Le module Groupements d'Entreprises (GPE) sera activé à l'étape suivante !")

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
