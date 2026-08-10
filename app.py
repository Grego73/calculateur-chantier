import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

# --- INITIALISATION DE LA BASE DE DONNÉES SQLITE ---
DB_NAME = "chantiers.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chantiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_chantier TEXT,
            revenus REAL,
            cout_materiaux REAL,
            cout_location REAL,
            cout_salaires REAL,
            depenses_totales REAL,
            benefice_net REAL,
            roi REAL
        )
    """)
    conn.commit()
    conn.close()

def charger_donnees():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT nom_chantier AS 'Nom du Chantier', 
               revenus AS 'Revenus (€)', 
               cout_materiaux AS 'Coût Matériaux (€)', 
               cout_location AS 'Coût Location Engins (€)', 
               cout_salaires AS 'Coût Salaires (€)', 
               depenses_totales AS 'Dépenses Totales (€)', 
               benefice_net AS 'Bénéfice Net (€)', 
               roi AS 'ROI (%)' 
        FROM chantiers
    """, conn)
    conn.close()
    return df

def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chantiers (nom_chantier, revenus, cout_materiaux, cout_location, cout_salaires, depenses_totales, benefice_net, roi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nom, rev, mats, loc, sal, total, net, roi))
    conn.commit()
    conn.close()

def reinitialiser_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS chantiers")
    conn.commit()
    conn.close()
    init_db()

init_db()

# --- DICTIONNAIRE DE TOUS LES CHANTIERS AVEC ÉTAPES DÉTAILLÉES ---
CATALOGUE_CHANTIERS = {
    "Choisir un chantier pré-configuré...": {
        "revenus": 0, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0,
        "engins_requis": []
    },
    "Goudronnage d'une route (112 629 €)": {
        "revenus": 112629, "jours": 10, "location": 0,
        "sable": 200, "terre": 0, "enrobe": 300, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 4, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 10, "jh_ouvrier": 30, "jh_cond": 15,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N1"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N1"},
            {"N° Étape": 2, "Durée Étape (jours)": 3, "Type d'engin requis": "Finisseur", "Niveau requis": "N2"},
            {"N° Étape": 3, "Durée Étape (jours)": 3, "Type d'engin requis": "Compacteur pour enrobé", "Niveau requis": "N1"}
        ]
    },
    "Déblayer - Niveau 2 (6 596 €)": {
        "revenus": 6596, "jours": 3, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 2, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 3, "jh_ouvrier": 6, "jh_cond": 6,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 2, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 1, "Type d'engin requis": "Camions Benne", "Niveau requis": "N1"}
        ]
    },
    "Exhausser un terrain (10 336 €)": {
        "revenus": 10336, "jours": 5, "location": 0,
        "sable": 20, "terre": 80, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 5, "jh_ouvrier": 10, "jh_cond": 10,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 3, "Type d'engin requis": "Chargeuse", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 2, "Type d'engin requis": "Compacteurs de Sol", "Niveau requis": "N2"}
        ]
    },
    "Exhausser un terrain (8 908 €)": {
        "revenus": 8908, "jours": 4, "location": 0,
        "sable": 15, "terre": 60, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 4, "jh_ouvrier": 8, "jh_cond": 8,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 2, "Type d'engin requis": "Chargeuse Compacte", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 2, "Type d'engin requis": "Compacteurs de Sol", "Niveau requis": "N2"}
        ]
    },
    "Construction d'un hangar (129 306 €)": {
        "revenus": 129306, "jours": 20, "location": 0,
        "sable": 40, "terre": 0, "enrobe": 0, "armature": 50, "tole": 100,
        "beton": 80, "panneaux": 0, "tuyaux": 12, "canalisations": 10, "poutres": 25,
        "jh_chef": 20, "jh_ouvrier": 80, "jh_cond": 20,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 5, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 5, "Type d'engin requis": "Camion Béton Malaxeur", "Niveau requis": "N3"},
            {"N° Étape": 3, "Durée Étape (jours)": 10, "Type d'engin requis": "Chargeur Téléscopique", "Niveau requis": "N2"}
        ]
    },
    "Suppression d'un espace vert (18 786 €)": {
        "revenus": 18786, "jours": 6, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 2, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 6, "jh_ouvrier": 18, "jh_cond": 6,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 3, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 3, "Type d'engin requis": "Camions Benne", "Niveau requis": "N1"}
        ]
    },
    "Compacter - Niveau 2 (3 699 €)": {
        "revenus": 3699, "jours": 2, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 2, "jh_ouvrier": 2, "jh_cond": 4,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 2, "Type d'engin requis": "Compacteurs de Sol", "Niveau requis": "N2"}
        ]
    },
    "Goudronnage d'un chemin (34 960 €)": {
        "revenus": 34960, "jours": 5, "location": 0,
        "sable": 50, "terre": 0, "enrobe": 90, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 2, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 5, "jh_ouvrier": 15, "jh_cond": 10,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 1, "Type d'engin requis": "Fraiseuse", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 2, "Type d'engin requis": "Finisseur", "Niveau requis": "N2"},
            {"N° Étape": 3, "Durée Étape (jours)": 2, "Type d'engin requis": "Compacteur pour enrobé", "Niveau requis": "N1"}
        ]
    },
    "Exhausser un terrain (6 664 €)": {
        "revenus": 6664, "jours": 3, "location": 0,
        "sable": 10, "terre": 40, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 3, "jh_ouvrier": 6, "jh_cond": 6,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 3, "Type d'engin requis": "Chargeuse", "Niveau requis": "N2"}
        ]
    },
    "Déblayer - Niveau 3 (21 528 €)": {
        "revenus": 21528, "jours": 7, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 4, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 7, "jh_ouvrier": 21, "jh_cond": 14,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N3"},
            {"N° Étape": 2, "Durée Étape (jours)": 3, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"}
        ]
    },
    "Assainissement de lit (Petit cours d'eau) (12 180 €)": {
        "revenus": 12180, "jours": 4, "location": 0,
        "sable": 10, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 15, "panneaux": 2, "tuyaux": 0, "canalisations": 8, "poutres": 0,
        "jh_chef": 4, "jh_ouvrier": 12, "jh_cond": 4,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 2, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 2, "Type d'engin requis": "Chargeur Téléscopique", "Niveau requis": "N2"}
        ]
    },
    "Assainissement de lit (Cours d'eau) (10 450 €)": {
        "revenus": 10450, "jours": 4, "location": 0,
        "sable": 8, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 10, "panneaux": 2, "tuyaux": 0, "canalisations": 6, "poutres": 0,
        "jh_chef": 4, "jh_ouvrier": 12, "jh_cond": 4,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"}
        ]
    },
    "Goudronnage d'une route (Grande surface) (214 599 €)": {
        "revenus": 214599, "jours": 16, "location": 0,
        "sable": 488, "terre": 0, "enrobe": 618, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 6, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 16, "jh_ouvrier": 48, "jh_cond": 28,
        # Configuration exacte de vos 4 étapes techniques
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Fraiseuse", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 4, "Type d'engin requis": "Niveleuse", "Niveau requis": "N2"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Finisseur", "Niveau requis": "N3"},
            {"N° Étape": 4, "Durée Étape (jours)": 4, "Type d'engin requis": "Compacteur pour enrobé", "Niveau requis": "N3"}
        ]
    },
    "Construction d'un hangar (139 104 €)": {
        "revenus": 139104, "jours": 22, "location": 0,
        "sable": 45, "terre": 0, "enrobe": 0, "armature": 60, "tole": 120,
        "beton": 90, "panneaux": 0, "tuyaux": 16, "canalisations": 12, "poutres": 30,
        "jh_chef": 22, "jh_ouvrier": 90, "jh_cond": 22,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 6, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 6, "Type d'engin requis": "Camion Béton Malaxeur", "Niveau requis": "N3"},
            {"N° Étape": 3, "Durée Étape (jours)": 10, "Type d'engin requis": "Chargeur Téléscopique", "Niveau requis": "N3"}
        ]
    },
    "Compacter - Niveau 2 (4 617 €)": {
        "revenus": 4617, "jours": 3, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 3, "jh_ouvrier": 3, "jh_cond": 6,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 3, "Type d'engin requis": "Compacteurs de Sol", "Niveau requis": "N2"}
        ]
    },
    "Remblayer - Niveau 3 (13 674 €)": {
        "revenus": 13674, "jours": 5, "location": 0,
        "sable": 10, "terre": 120, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 5, "jh_ouvrier": 15, "jh_cond": 10,
        "engins_requis": [
            {"N° Étape": 1, "Durée Étape (jours)": 3, "Type d'engin requis": "Chargeuse", "Niveau requis": "N3"},
            {"N° Étape": 2, "Durée Étape (jours)": 2, "Type d'engin requis": "Compacteurs de Sol", "Niveau requis": "N3"}
        ]
    }
}

# S'assurer que chaque chantier contient bien les clés d'étapes de base pour éviter les crashs
for chantier, data in CATALOGUE_CHANTIERS.items():
    if "engins_requis" not in data:
        data["engins_requis"] = []

# --- CATALOGUE COMPLET DES ENGINS DISPONIBLES ET LEURS MODÈLES ---
CATALOGUE_ENGINS = {
    "Camion Benne N1 - Iveco Daily (180 cv)": 200,
    "Camion Benne N1 - Renault Master 3 (160 cv)": 200,
    "Camion Benne N3 - Renault Trucks K 430 (430 cv)": 420,
    "Pelleteuse N1 - CAT 301.8 (15.7 kW)": 150,
    "Pelleteuse N1 - CAT 303 CR (17.6 kW)": 150,
    "Pelleteuse N1 - Kubota KX019-4 (11.6 kW)": 150,
    "Pelleteuse N1 - Kubota KX030-4 (17.7 kW)": 150,
    "Pelleteuse N1 - Takeuchi TB225 (16.5 kW)": 150,
    "Pelleteuse N1 - Takeuchi TB325R (16.5 kW)": 150,
    "Pelleteuse N2 - CAT 317 GC (89 kW)": 200,
    "Pelleteuse N2 - Takeuchi TB2150 (85.0 kW)": 200,
    "Pelleteuse N2 - CAT 315 GC (73.3 kW)": 200,
    "Pelleteuse N3 - CAT 330 (203.7 kW)": 280,
    "Pelleteuse N3 - CAT 336 (223.5 kW)": 280,
    "Pelleteuse N4 - Hitachi ZX490LCH-7 (296 kW)": 450,
    "Pelleteuse N4 - CAT 350 (308 kW)": 450,
    "Compacteur Sol N2 - CAT CS11 GC (91.7 kW)": 280,
    "Compacteur Sol N2 - Dynapac CA1300D (55 kW)": 280,
    "Compacteur Sol N3 - CAT CS19 (130.4 kW)": 340,
    "Compacteur Sol N3 - Dynapac CA6500D (149 kW)": 340,
    "Compacteur Enrobé N1 - CAT CB1.8 (N/A)": 220,
    "Compacteur Enrobé N1 - Dynapac CC1000 e (11 kW)": 220,
    "Compacteur Enrobé N2 - CAT CC2.7 (N/A)": 280,
    "Compacteur Enrobé N2 - Dynapac CC1400 VI (35 kW)": 280,
    "Compacteur Enrobé N3 - CAT CB8 (N/A)": 340,
    "Compacteur Enrobé N3 - Dynapac CC4200 VI (100 kW)": 340,
    "Finisseur N2 - CAT AP455 (90 kW)": 425,
    "Finisseur N3 - CAT AP600 (129 kW)": 490,
    "Finisseur N3 - Dynapac SD2500CS (142 kW)": 490,
    "Camion Béton Malaxeur N3 - Renault Trucks C XLOAD (380 cv)": 410,
    "Camion Pompe à béton N4 - Mecbo ATB 30 (400 cv)": 490,
    "Chargeuse Compacte N2 - CAT 249D3 (50.1 kW)": 360,
    "Chargeuse Compacte N2 - Bobcat S510 (34.4 kW)": 360,
    "Chargeuse Compacte N3 - CAT 299D3 XE (82 kW)": 430,
    "Chargeuse Compacte N3 - Bobcat S770 (68.6 kW)": 430,
    "Chargeuse Pneu N2 - Kubota RT160-2 (26 cv)": 490,
    "Chargeuse Pneu N2 - Kubota R070 (37.4 kW)": 490,
    "Chargeuse Pneu N2 - CAT 930 (127 kW)": 490,
    "Chargeuse Pneu N2 - Hitachi ZW75-6 (50 kW)": 490,
    "Chargeuse Pneu N3 - CAT GC 966 (239 kW)": 430,
    "Chargeuse Pneu N3 - Hitachi ZW310-7 (233 kW)": 430,
    "Chargeuse Pneu N4 - CAT 988 GC (335 kW)": 540,
    "Chargeur Téléscopique N2 - JCB 25-60 Hi-Viz (55 kW)": 220,
    "Chargeur Téléscopique N3 - JCB 541-70 (81 kW)": 330,
    "Niveleuse N2 - CAT 14 (178 kW)": 580,
    "Niveleuse N4 - CAT 24 (399 kW)": 680,
    "Fraiseuse N2 - CAT PM312 (256 kW)": 380,
    "Fraiseuse N4 - CAT PM825 (601 kW)": 580
}

TYPES_ENGINS_BRUTS = ["Camions Benne", "Pelleteuses", "Compacteurs de Sol", "Compacteur pour enrobé", "Finisseur", "Camion Béton Malaxeur", "Chargeuse Compacte", "Chargeuse", "Chargeur Téléscopique", "Niveleuse", "Fraiseuse"]

liste_complete = list(CATALOGUE_CHANTIERS.keys())
element_defaut = "Choisir un chantier pré-configuré..."

if element_defaut in liste_complete:
    liste_complete.remove(element_defaut)
liste_triee = [element_defaut] + sorted(liste_complete)

onglet1, onglet2 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement"])

with onglet1:
    st.subheader("Formulaire de saisie")
    
    chantier_selectionne = st.selectbox("🚀 Optionnel - Pré-remplir avec un modèle de chantier :", liste_triee)
    
    donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
    valeur_nom_defaut = "" if chantier_selectionne == element_defaut else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=donnees_modele["revenus"])
        jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=donnees_modele["jours"])

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=donnees_modele["sable"])
            qte_terre = st.number_input("Tonnes de Terre :", value=donnees_modele["terre"])
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=donnees_modele["enrobe"])
            qte_armature = st.number_input("Unités d'Armature métallique :", value=donnees_modele["armature"])
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=donnees_modele["tole"])
            qte_beton = st.number_input("Tonnes de Béton :", value=donnees_modele["beton"])
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=donnees_modele["panneaux"])
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=donnees_modele["tuyaux"])
            qte_eaux_usees = st.number_input("Unités de Canalisations eaux usées :", value=donnees_modele["canalisations"])
            qte_poutres = st.number_input("Unités de Poutres en acier :", value=donnees_modele["poutres"])
        with c_px:
            prix_sable = st.number_input("Prix Sable (€/t) :", value=12)
            prix_terre = st.number_input("Prix Terre (€/t) :", value=16)
            prix_enrobe = st.number_input("Prix Enrobé (€/t) :", value=42)
            prix_armature = st.number_input("Prix Armature (€/u) :", value=70)
            prix_tole = st.number_input("Prix Tôle (€/u) :", value=55)
            prix_beton = st.number_input("Prix Béton (€/t) :", value=45)
            prix_panneaux = st.number_input("Prix Panneaux (€/u) :", value=90)
            prix_tuyaux = st.number_input("Prix Tuyaux d'eau (€/u) :", value=32)
            prix_eaux_usees = st.number_input("Prix Canalisations (€/u) :", value=35)
            prix_poutres = st.number_input("Prix Poutres acier (€/u) :", value=70)

    with col2:
        st.markdown("### --- GRILLE SALARIALE & HEURES ---")
        chef_mensuel = st.number_input("Salaire mensuel Chef (€) :", value=1566)
        jh_chef = st.number_input("Total Jours-Homme Chef :", value=donnees_modele["jh_chef"])
        ouvrier_mensuel = st.number_input("Salaire mensuel Ouvrier (€) :", value=1616)
        jh_ouvrier = st.number_input("Total Jours-Homme Ouvrier :", value=donnees_modele["jh_ouvrier"])
        cond_mensuel = st.number_input("Salaire mensuel Conducteur (€) :", value=1571)
        jh_cond = st.number_input("Total Jours-Homme Conducteur :", value=donnees_modele["jh_cond"])

        # --- CALCUL ET AFFICHAGE DU TOTAL DES SALAIRES EN DIRECT ---
        sal_chef_direct = jh_chef * (chef_mensuel / 30)
        sal_ouvrier_direct = jh_ouvrier * (ouvrier_mensuel / 30)
        sal_cond_direct = jh_cond * (cond_mensuel / 30)
        total_salaires_direct = sal_chef_direct + sal_ouvrier_direct + sal_cond_direct
        
        st.info(f"👥 **Total estimé des salaires pour ce chantier :** {total_salaires_direct:,.2f} €")

        # --- TABLE DES ENGINS NÉCESSAIRES ---
        st.markdown("### --- TABLE DES ENGINS NÉCESSAIRES ---")
        st.caption("📋 Cochez les engins à louer. Les informations de planification (Étape & Durée) sont lues depuis le modèle.")
        
        engins_bruts_modele = []
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            for item in donnees_modele["engins_requis"]:
                engins_bruts_modele.append({
                    "N° Étape": item.get("N° Étape", 1),
                    "Durée Étape (jours)": item.get("Durée Étape (jours)", 1),
                    "Type d'engin requis": item.get("Type d'engin requis", "Pelleteuses"),
                    "Niveau requis": item.get("Niveau requis", "N1"),
                    "À louer ?": False
                })
        
        df_besoins_init = pd.DataFrame(engins_bruts_modele)
        if df_besoins_init.empty:
            df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        
        engins_necessaires = st.data_editor(
            df_besoins_init,
            num_rows="dynamic",
            use_container_width=True,
            key="table_engins_necessaires",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N° Étape", min_value=1, step=1, required=True),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée (jours)", min_value=1, step=1, required=True),
                "Type d'engin requis": st.column_config.SelectboxColumn("Type d'engin", options=TYPES_ENGINS_BRUTS, required=True),
                "Niveau requis": st.column_config.SelectboxColumn("Niveau requis", options=["N1", "N2", "N3", "N4"], required=True),
                "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False)
            }
        )

        # --- LOGIQUE DE TRANSFERT ---
        engins_transferes_list = []
        if not engins_necessaires.empty:
            df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
            
            for _, row in df_coches.iterrows():
                type_demande = row["Type d'engin requis"]
                niveau_demande = row["Niveau requis"]
                duree_etape = int(row["Durée Étape (jours)"])
                
                modele_trouve = None
                prix_trouve = 380
                
                cle_recherche_1 = f"{type_demande[:-1] if type_demande.endswith('s') else type_demande} {niveau_demande}"
                cle_recherche_2 = f"{type_demande} {niveau_demande}"
                
                for engin_nom, prix in CATALOGUE_ENGINS.items():
                    if (cle_recherche_1.lower() in engin_nom.lower()) or (cle_recherche_2.lower() in engin_nom.lower()):
                        modele_trouve = engin_nom
                        prix_trouve = prix
                        break
                
                if not modele_trouve:
                    for engin_nom, prix in CATALOGUE_ENGINS.items():
                        if type_demande.lower() in engin_nom.lower() or type_demande[:-1].lower() in engin_nom.lower():
                            modele_trouve = engin_nom
                            prix_trouve = prix
                            break
                
                if modele_trouve:
                    engins_transferes_list.append({
                        "Sélection de l'engin / Modèle": modele_trouve,
                        "Quantité": 1,
                        "Prix Location (€/jour)": prix_trouve,
                        "Jours de Location": duree_etape
                    })

        # --- TABLE DES ENGINS À LOUER ---
        st.markdown("### --- TABLE DES ENGINS À LOUER ---")
        st.caption("🔗 Les machines cochées ci-dessus se chargent automatiquement ici.")
        
        df_engins_init = pd.DataFrame(columns=["Sélection de l'engin / Modèle", "Quantité", "Prix Location (€/jour)", "Jours de Location"])
        if len(engins_transferes_list) > 0:
            df_engins_init = pd.DataFrame(engins_transferes_list)
        
        engins_edites = st.data_editor(
            df_engins_init,
            num_rows="dynamic",
            use_container_width=True,
            key="table_engins_a_louer",
            column_config={
                "Sélection de l'engin / Modèle": st.column_config.SelectboxColumn("Engin & Modèle", options=list(CATALOGUE_ENGINS.keys()), required=True),
                "Quantité": st.column_config.NumberColumn("Quantité", min_value=1, default=1, step=1),
                "Prix Location (€/jour)": st.column_config.NumberColumn("Prix / Jour (€)", min_value=0, step=10),
                "Jours de Location": st.column_config.NumberColumn("Jours à louer", min_value=1, max_value=365, step=1)
            }
        )

        total_loc_engins_direct = 0.0
        if not engins_edites.empty:
            df_propres_direct = engins_edites.dropna(subset=["Sélection de l'engin / Modèle"])
            total_loc_engins_direct = (df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * df_propres_direct["Jours de Location"]).sum()
        
        st.info(f"💰 **Total des engins loués (Calcul personnalisé) :** {total_loc_engins_direct:,.2f} €")

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary"):
        df_actuel = charger_donnees()
        doublon_existe = not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier:
            st.error("Veuillez donner un nom ou un numéro valide à votre chantier.")
        elif doublon_existe:
            st.error(f"Impossible d'enregistrer : Ce chantier au montant de {revenus:,.2f} € existe déjà.")
        else:
            total_mats = (qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_eaux_usees*prix_eaux_usees) + (qte_poutres*prix_poutres)
            
            total_location = 0.0
            if not engins_edites.empty:
                df_propres = engins_edites.dropna(subset=["Sélection de l'engin / Modèle"])
                total_location = (df_propres["Quantité"] * df_propres["Prix Location (€/jour)"] * df_propres["Jours de Location"]).sum()
                
            total_salaires = (jh_chef * (chef_mensuel / 30)) + (jh_ouvrier * (ouvrier_mensuel / 30)) + (jh_cond * (cond_mensuel / 30))
            total_depenses = total_mats + total_location + total_salaires
            benefice_net = revenus - total_depenses
            roi = (benefice_net / total_depenses) * 100 if total_depenses > 0 else 0

            st.markdown("---")
            st.write(f"**Coût Matériaux globaux** : {total_mats:,.2f} €")
            st.write(f"**Coût Location Engins** : {total_location:,.2f} €")
            st.write(f"**Coût Salaires** : {total_salaires:,.2f} €")
            
            if benefice_net >= 0:
                st.success(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")
            else:
                st.error(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")

            inserer_chantier(nom_chantier, revenus, total_mats, total_location, total_salaires, total_depenses, benefice_net, round(roi, 2))
            st.toast("Chantier enregistré avec succès dans la base SQLite !")

with onglet2:
    st.subheader("Base de données des chantiers enregistrés")
    df_affichage = charger_donnees()
    
    if df_affichage.empty:
        st.info("Aucun chantier n'a encore été enregistré.")
    else:
        critere_tri = st.selectbox("Classer les chantiers par ordre de rentabilité :", ["Plus gros Bénéfice d'abord", "Plus gros ROI d'abord", "Plus de revenus d'abord"])
        if critere_tri == "Plus gros Bénéfice d'abord":
            df_affichage = df_affichage.sort_values(by="Bénéfice Net (€)", ascending=False)
        elif critere_tri == "Plus gros ROI d'abord":
            df_affichage = df_affichage.sort_values(by="ROI (%)", ascending=False)
        elif critere_tri == "Plus de revenus d'abord":
            df_affichage = df_affichage.sort_values(by="Revenus (€)", ascending=False)
            
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Télécharger la base de données (CSV)", data=csv, file_name="base_donnies_chantiers.csv", mime="text/csv")
        st.markdown("---")
        if st.button("🗑️ Vider définitivement la base de données SQLITE", type="secondary"):
            reinitialiser_db()
            st.rerun()
