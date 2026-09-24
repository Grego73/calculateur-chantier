import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import database as db

# 1. BIEN VÉRIFIER QUE L'IMPORT DE LA NOUVELLE PAGE EST PRÉSENT ICI :

# Par le nouvel import du dossier segmenté :
from onglets.direction_admin import afficher_onglet_direction
from onglets.suivi_interne import afficher_onglet_suivi_interne
from onglets.ajouter_chantier import afficher_onglet_ajouter
from onglets.historique import afficher_onglet_historique

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
    "👥 Suivi Interne Coop",
    "🔒 Espace Direction",
])

# ==============================================================================
# 📋 ROUTAGE DES ONGLETS PRINCIPAUX DE L'APPLICATION
# ==============================================================================
with onglets_principaux[0]:
    # Remplacer par votre appel exact pour l'ajout de chantier si différent
    afficher_onglet_ajouter_chantier(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB)

with onglets_principaux[1]:
    # Remplacer par votre appel exact pour l'historique si différent
    afficher_onglet_historique_classement()

with onglets_principaux[2]:
    # Appel de l'onglet coopérative qui intègre notre nettoyeur secret
    afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB)

with onglets_principaux[3]:
    # 🎯 CORRECTION DE L'INDENTATION ICI : Ajoutez bien 4 espaces ou 1 tabulation devant cette ligne
    afficher_onglet_direction(SALAIRES_DB, MATERIAUX_DB)


# ==============================================================================
# 🎯 BARRE DE DIAGNOSTIC GLOBALE (ALIGNÉE COMPLÈTEMENT À GAUCHE)
# ==============================================================================
from onglets.direction_admin.outils import afficher_barre_diagnostic_globale
afficher_barre_diagnostic_globale()
