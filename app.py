import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import database as db

# 1. IMPORTATIONS DES ONGLETS DEPUIS VOTRE ARCHITECTURE
from onglets.direction_admin import afficher_onglet_direction
from onglets.suivi_interne import afficher_onglet_suivi_interne
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

# Chargement des configurations de votre base NoSQL Firebase
config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()
types_engins = db.charger_types_engins_bruts()
catalogue_chantiers = db.charger_catalogue_chantiers()

# 2. DÉCLARATION CENTRALISÉE DE VOTRE COMPOSANT D'ONGLETS
onglets_principaux = st.tabs([
    "➕ Ajouter un Chantier", 
    "📊 Historique & Classement", 
    "👥 Suivi Interne Coop",
    "🔒 Espace Direction",
])

# ==============================================================================
# 📋 ROUTAGE SECURISE ET ALIGNÉ DES ONGLETS PRINCIPAUX
# ==============================================================================
with onglets_principaux[0]:
    # Utilise vos fonctions importées et vos variables chargées depuis Firebase
    afficher_onglet_ajouter(config_salaires, catalogue_engins, config_materiaux)

with onglets_principaux[1]:
    afficher_onglet_historique()

with onglets_principaux[2]:
    afficher_onglet_suivi_interne(config_salaires, catalogue_engins, config_materiaux)

with onglets_principaux[3]:
    afficher_onglet_direction(config_salaires, config_materiaux)


# ==============================================================================
# 🎯 BARRE DE DIAGNOSTIC GLOBALE (ALIGNÉE COMPLÈTEMENT À GAUCHE)
# ==============================================================================
from onglets.direction_admin.outils import afficher_barre_diagnostic_globale
afficher_barre_diagnostic_globale()
