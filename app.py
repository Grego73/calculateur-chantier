import streamlit as st
import database as db  # On importe notre fichier de base de données

# On importe les fonctions d'affichage de nos futurs fichiers onglets
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique


st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

# Chargement unique des configurations au démarrage
config_salaires = db.charger_salaires_config()
config_materiaux = db.charger_materiaux_config()
catalogue_engins = db.charger_catalogue_engins()
types_engins = db.charger_types_engins_bruts()
catalogue_chantiers = db.charger_catalogue_chantiers()

# Création des onglets
onglet1, onglet2, onglet3 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement", "🔒 Espace Direction"])

with onglet1:
    afficher_onglet_ajouter(config_salaires, config_materiaux, catalogue_engins, types_engins, catalogue_chantiers)

with onglet2:
    afficher_onglet_historique()

with onglet3:
    afficher_onglet_direction(config_salaires, config_materiaux)
