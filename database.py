import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Initialisation unique de Firebase
if not firebase_admin._apps:
    try:
        firebase_info = dict(st.secrets["firebase"])
        if "private_key" in firebase_info:
            firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Erreur critique d'initialisation Firebase : {e}")

db = firestore.client()

# ==============================================================================
# --- FONCTIONS DE LECTURE (SÉCURISÉES PAR CACHE EXTENSIBLE DE 10 MIN) ---
# ==============================================================================

@st.cache_data(ttl=600)
def charger_salaires_config():
    try:
        doc_ref = db.collection("configuration_salaires").document("grille")
        doc = doc_ref.get()
        if doc.exists and doc.to_dict() is not None: 
            return doc.to_dict()
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les salaires sur Firebase ({e}). Utilisation d'une grille vide.")
    
    # Sécurité : Si vide ou erreur, on initialise à vide sans écraser avec les anciens 230€
    data_defaut = {}
    try: 
        db.collection("configuration_salaires").document("grille").set(data_defaut)
        st.cache_data.clear() # On vide le cache car la DB vient de muter
    except Exception: 
        pass
    return data_defaut

@st.cache_data(ttl=600)
def charger_materiaux_config():
    try:
        doc_ref = db.collection("configuration_materiaux").document("catalogue")
        doc = doc_ref.get()
        if doc.exists and doc.to_dict() is not None: 
            return doc.to_dict()
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les matériaux sur Firebase ({e}). Utilisation du catalogue par défaut.")
    
    # Catalogue de secours si Firebase est vide ou inaccessible
    data_defaut = {"Sable": 12.0, "Terre": 16.0, "Enrobé": 42.0, "Armature": 70.0, "Tôle": 55.0, "Béton": 45.0, "Panneaux": 90.0, "Tuyaux": 32.0, "Canalisations": 35.0, "Poutres": 70.0}
    try: 
        db.collection("configuration_materiaux").document("catalogue").set(data_defaut)
        st.cache_data.clear() # On vide le cache car la DB vient de muter
    except Exception: 
        pass
    return data_defaut

@st.cache_data(ttl=600)
def charger_catalogue_engins():
    try:
        docs = db.collection("catalogue_engins").stream()
        catalogue = {}
        for doc in docs: 
            data = doc.to_dict()
            if data:
                catalogue[doc.id] = data.get("prix_jour", 0.0)
        return catalogue
    except Exception as e:
        st.warning(f"⚠️ Impossible de charger le catalogue d'engins ({e}).")
        return {}

@st.cache_data(ttl=600)
def charger_types_engins_bruts():
    try:
        docs = db.collection("catalogue_engins").stream()
        types = set()
        for doc in docs: 
            data = doc.to_dict()
            if data:
                types.add(data.get("type_brut", "Autre"))
        return sorted(list(types)) if types else ["Pelleteuses", "Camions Benne"]
    except Exception:
        return ["Pelleteuses", "Camions Benne"]

@st.cache_data(ttl=600)
def charger_catalogue_chantiers():
    try:
        docs = db.collection("modeles_chantiers").stream()
        catalogue = {"Choisir un chantier pré-configuré...": {"revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []}}
        for doc in docs: 
            data = doc.to_dict()
            if data:
                catalogue[doc.id] = data
        return catalogue
    except Exception:
        return {"Choisir un chantier pré-configuré...": {"revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []}}

@st.cache_data(ttl=600)
def charger_donnees():
    try:
        docs = db.collection("chantiers").stream()
        liste_chantiers = []
        for doc in docs:
            d = doc.to_dict()
            if d:
                liste_chantiers.append({'Nom du Chantier': doc.id, 'Revenus (€)': d.get('revenus', 0.0), 'Durée (Jours)': d.get('jours', 0), 'Coût Matériaux (€)': d.get('cout_materiaux', 0.0), 'Coût Location Engins (€)': d.get('cout_location', 0.0), 'Coût Salaires (€)': d.get('cout_salaires', 0.0), 'Dépenses Totales (€)': d.get('depenses_totales', 0.0), 'Bénéfice Net (€)': d.get('benefice_net', 0.0), 'Gain / Jour (€)': d.get('gain_par_jour', 0.0), 'ROI (%)': d.get('roi', 0.0), 'ROI / Jour (%)': d.get('roi_par_jour', 0.0)})
        return pd.DataFrame(liste_chantiers) if liste_chantiers else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ==============================================================================
# --- FONCTIONS D'ÉCRITURE (FORCENT L'EXPULSION IMMÉDIATE DU VIEUX CACHE) ---
# ==============================================================================

def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    try:
        db.collection("chantiers").document(nom).set({"revenus": rev, "cout_materiaux": mats, "cout_location": loc, "cout_salaires": sal, "depenses_totales": total, "benefice_net": net, "roi": roi, "jours": jours, "gain_par_jour": gpj, "roi_par_jour": rpj})
        # 🚀 LIGNE ANTI-BURST : Force le rafraîchissement au prochain clic sans recharger l'app
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de l'enregistrement du chantier : {e}")

def reinitialiser_db():
    try:
        collections = ["chantiers", "modeles_chantiers", "configuration_salaires", "configuration_materiaux", "catalogue_engins"]
        for col_name in collections:
            docs = db.collection(col_name).stream()
            for doc in docs: 
                doc.reference.delete()
        # 🚀 LIGNE ANTI-BURST : Purge totale du cache après nettoyage complet
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de la réinitialisation : {e}")

