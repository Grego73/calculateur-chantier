import streamlit as st
import database as db

# 1. BIEN VÉRIFIER QUE L'IMPORT DE LA NOUVELLE PAGE EST PRÉSENT ICI :
from onglets.direction import afficher_onglet_direction
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique
from onglets.suivi_interne import afficher_onglet_suivi_interne  # <-- CET IMPORT

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()
types_engins = db.charger_types_engins_bruts()
catalogue_chantiers = db.charger_catalogue_chantiers()

# 2. AJOUTER "👥 Suivi Interne" DANS LA LISTE DES TABS :
onglet1, onglet2, onglet3, onglet4 = st.tabs([
    "➕ Ajouter un Chantier", 
    "📊 Historique & Classement", 
    "👥 Suivi Interne",  # <-- DOIT ÊTRE ICI
    "🔒 Espace Direction"
])

with onglet1:
    afficher_onglet_ajouter(config_salaires, config_materiaux, catalogue_engins, types_engins, catalogue_chantiers)

with onglet2:
    afficher_onglet_historique()

with onglet3:
    # 3. L'APPEL DE LA FONCTION POUR CONSTRUIRE LA PAGE :
    afficher_onglet_suivi_interne(config_salaires, catalogue_engins)

with onglet4:
    afficher_onglet_direction(config_salaires, config_materiaux)
