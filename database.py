import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Initialisation unique de Firebase
if not firebase_admin._apps:
    firebase_info = dict(st.secrets["firebase"])
    if "private_key" in firebase_info:
        firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def charger_salaires_config():
    try:
        doc_ref = db.collection("configuration_salaires").document("grille")
        doc = doc_ref.get()
        if doc.exists: return doc.to_dict()
    except Exception: pass
    data_defaut = {"Chef": 230.0, "Ouvrier": 230.0, "Conducteur": 230.0, "Intérim": 220.0}
    try: db.collection("configuration_salaires").document("grille").set(data_defaut)
    except Exception: pass
    return data_defaut

def charger_salaires_config():
    try:
        doc_ref = db.collection("configuration_salaires").document("grille")
        doc = doc_ref.get()
        if doc.exists: 
            return doc.to_dict()
    except Exception: 
        pass
    
    # Si le document n'existe vraiment pas du tout sur Firebase, on initialise 
    # une structure vide au lieu de forcer les anciennes lignes à 230€
    data_defaut = {}
    try: 
        db.collection("configuration_salaires").document("grille").set(data_defaut)
    except Exception: 
        pass
    return data_defaut

def charger_catalogue_engins():
    docs = db.collection("catalogue_engins").stream()
    catalogue = {}
    for doc in docs: catalogue[doc.id] = doc.to_dict().get("prix_jour", 0.0)
    return catalogue

def charger_types_engins_bruts():
    docs = db.collection("catalogue_engins").stream()
    types = set()
    for doc in docs: types.add(doc.to_dict().get("type_brut", "Autre"))
    return sorted(list(types)) if types else ["Pelleteuses", "Camions Benne"]

def charger_catalogue_chantiers():
    docs = db.collection("modeles_chantiers").stream()
    catalogue = {"Choisir un chantier pré-configuré...": {"revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []}}
    for doc in docs: catalogue[doc.id] = doc.to_dict()
    return catalogue

def charger_donnees():
    docs = db.collection("chantiers").stream()
    liste_chantiers = []
    for doc in docs:
        d = doc.to_dict()
        liste_chantiers.append({'Nom du Chantier': doc.id, 'Revenus (€)': d.get('revenus', 0.0), 'Durée (Jours)': d.get('jours', 0), 'Coût Matériaux (€)': d.get('cout_materiaux', 0.0), 'Coût Location Engins (€)': d.get('cout_location', 0.0), 'Coût Salaires (€)': d.get('cout_salaires', 0.0), 'Dépenses Totales (€)': d.get('depenses_totales', 0.0), 'Bénéfice Net (€)': d.get('benefice_net', 0.0), 'Gain / Jour (€)': d.get('gain_par_jour', 0.0), 'ROI (%)': d.get('roi', 0.0), 'ROI / Jour (%)': d.get('roi_par_jour', 0.0)})
    return pd.DataFrame(liste_chantiers) if liste_chantiers else pd.DataFrame()

def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    db.collection("chantiers").document(nom).set({"revenus": rev, "cout_materiaux": mats, "cout_location": loc, "cout_salaires": sal, "depenses_totales": total, "benefice_net": net, "roi": roi, "jours": jours, "gain_par_jour": gpj, "roi_par_jour": rpj})

def reinitialiser_db():
    collections = ["chantiers", "modeles_chantiers", "configuration_salaires", "configuration_materiaux", "catalogue_engins"]
    for col_name in collections:
        docs = db.collection(col_name).stream()
        for doc in docs: doc.reference.delete()
