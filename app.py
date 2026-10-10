import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import database as db

# Importations des onglets applicatifs
from onglets.direction_admin import afficher_onglet_direction
from onglets.suivi_interne import afficher_onglet_suivi_interne
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique
from onglets.suivi_contrats import afficher_onglet_suivi_contrats
from onglets.marche_actuel import afficher_onglet_marche_actuel

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()
types_engins = db.charger_types_engins_bruts()

# 🔥 CORRECTIF : Déclaration stricte des 6 variables pour les 6 onglets créés
onglet1, onglet2, onglet3, onglet4, onglet5, onglet6 = st.tabs([
    "➕ Ajouter un Chantier", 
    "📊 Historique & Classement",
    "📋 Contrats SIM-TP",
    "🌍 Marché des Coopératives",
    "👥 Suivi Interne Coop",
    "🔒 Espace Direction"
])

with onglet1:
    afficher_onglet_ajouter(config_salaires, config_materiaux, catalogue_engins, types_engins)

with onglet2:
    afficher_onglet_historique()

with onglet3:
    afficher_onglet_suivi_contrats()

with onglet4:
    afficher_onglet_marche_actuel()

with onglet5:
    afficher_onglet_suivi_interne(config_salaires, catalogue_engins, config_materiaux)

with onglet6:
    afficher_onglet_direction(config_salaires, config_materiaux)

# ==============================================================================
# 🎯 BARRE DE DIAGNOSTIC GLOBALE
# ==============================================================================
from onglets.direction_admin.outils import afficher_barre_diagnostic_globale
afficher_barre_diagnostic_globale()
