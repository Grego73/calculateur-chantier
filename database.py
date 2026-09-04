# Contenu complet, sécurisé et validé pour : database.py

import streamlit as st
import pandas as pd
from google.cloud import firestore
import json
from google.oauth2 import service_account

# ==============================================================================
# --- 1. INITIALISATION DE LA CONNEXION UNIQUE CLOUD FIRESTORE ---
# ==============================================================================
if "text_key" in st.secrets:
    info_cles = json.loads(st.secrets["text_key"])
    creds = service_account.Credentials.from_service_account_info(info_cles)
    db = firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
else:
    db = firestore.Client(project="calculateur-chantier-dc921")


# ==============================================================================
# --- 2. FONCTIONS DE LECTURE (SÉCURISÉES PAR CACHE EXTENSIBLE DE 10 MIN) ---
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
    
    data_defaut = {}
    try: 
        db.collection("configuration_salaires").document("grille").set(data_defaut)
        st.cache_data.clear()
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
    
    data_defaut = {"Sable": 12.0, "Terre": 16.0, "Enrobé": 42.0, "Armature": 70.0, "Tôle": 55.0, "Béton": 45.0, "Panneaux": 90.0, "Tuyaux": 32.0, "Canalisations": 35.0, "Poutres": 70.0}
    try: 
        db.collection("configuration_materiaux").document("catalogue").set(data_defaut)
        st.cache_data.clear()
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
# --- 3. FONCTIONS D'ÉCRITURE ---
# ==============================================================================
def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    try:
        db.collection("chantiers").document(nom).set({"revenus": rev, "cout_materiaux": mats, "cout_location": loc, "cout_salaires": sal, "depenses_totales": total, "benefice_net": net, "roi": roi, "jours": jours, "gain_par_jour": gpj, "roi_par_jour": rpj})
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
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de la réinitialisation : {e}")

def enregistrer_log(type_action, details):
    import datetime
    import pytz
    try:
        tz_paris = pytz.timezone('Europe/Paris')
        maintenant = datetime.datetime.now(tz_paris)
        timestamp_txt = maintenant.strftime("%Y-%m-%d %H:%M:%S")
        
        db.collection("journaux_actions").add({
            "timestamp": timestamp_txt,
            "type_action": type_action,
            "details": details
        })
    except Exception:
        pass


# ==============================================================================
# --- 4. FONCTIONS AVANCÉES POUR LE SUIVI INTERNE DES COOPÉRATIVES ---
# ==============================================================================
def lister_toutes_les_cooperatives():
    try:
        coops_stream = db.collection("cooperatives").stream()
        list_coops = [doc.id for doc in coops_stream]
        return sorted(list_coops)
    except Exception:
        return []

def verifier_et_inscrire_joueur(nom_coop, mdp_saisi, pseudo_joueur):
    if not nom_coop or not mdp_saisi or not pseudo_joueur:
        return False, "⚠️ Veuillez remplir tous les champs."
        
    coop_ref = db.collection("cooperatives").document(nom_coop)
    coop_doc = coop_ref.get()
    
    if not coop_doc.exists:
        coop_ref.set({
            "mot_de_passe": mdp_saisi,
            "membres": [pseudo_joueur]
        })
        return True, f"🟢 Coopérative créée ! Bienvenue à bord, premier membre : {pseudo_joueur}"
    
    coop_data = coop_doc.to_dict()
    if coop_data.get("mot_de_passe") != mdp_saisi:
        return False, "🔒 Mot de passe de la coopérative incorrect."
        
    membres_actuels = coop_data.get("membres", [])
    if pseudo_joueur in membres_actuels:
        return True, f"👋 Content de vous revoir, {pseudo_joueur}."
        
    if len(membres_actuels) >= 4:
        return False, f"🚫 Accès refusé : La coopérative '{nom_coop}' a atteint sa limite maximale de 4 joueurs inscrits."
        
    membres_actuels.append(pseudo_joueur)
    coop_ref.update({"membres": membres_actuels})
    return True, f"📝 Inscription réussie ! Membre enregistré (Place {len(membres_actuels)}/4) : {pseudo_joueur}"

def ajouter_membres_bloc_coop(nom_coop, texte_membres_brut):
    if not nom_coop or not texte_membres_brut.strip():
        return False, "⚠️ Saisissez au moins un pseudo valide."
        
    coop_ref = db.collection("cooperatives").document(nom_coop)
    coop_doc = coop_ref.get()
    
    if not coop_doc.exists:
        return False, "❌ Coopérative introuvable."
        
    coop_data = coop_doc.to_dict()
    membres_actuels = coop_data.get("membres", [])
    
    pseudos_detectes = [p.strip() for p in texte_membres_brut.replace(",", " ").split() if p.strip()]
    
    compteur_ajouts = 0
    for pseudo in pseudos_detectes:
        if pseudo in membres_actuels:
            continue
        if len(membres_actuels) >= 4:
            break
            
        membres_actuels.append(pseudo)
        compteur_ajouts += 1

    if compteur_ajouts > 0:
        coop_ref.update({"membres": membres_actuels})
        return True, f"🚀 {compteur_ajouts} collaborateur(s) ajouté(s) à la liste ! Initialisez leurs investissements ci-dessous."
    return False, "ℹ️ Aucun nouveau membre unique n'a été détecté ou la limite de 4 est atteinte."

def fixer_capital_initial_membre(nom_coop, pseudo_joueur, montant_cash):
    try:
        doc_id = f"capital_{pseudo_joueur}"
        db.collection("cooperatives").document(nom_coop).collection("capital_initial").document(doc_id).set({
            "joueur": pseudo_joueur,
            "montant": float(montant_cash),
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception:
        return False

def ajouter_reinvestissement_membre(nom_coop, pseudo_joueur, montant_cash):
    try:
        mouvement_id = f"reinvest_{int(pd.Timestamp.now().timestamp())}_{pseudo_joueur}"
        db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").document(mouvement_id).set({
            "joueur": pseudo_joueur,
            "type": "REINVESTISSEMENT_CASH",
            "apport_cash": float(montant_cash),
            "materiaux": {},
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return True
    except Exception:
        return False

def enregistrer_ligne_historique_brute(nom_coop, date_txt, heure_txt, actor_txt, type_mouv, materiaux_dict):
    if not materiaux_dict:
        return
    try:
        date_cle = "".join(reversed(date_txt.split("/")))
        heure_cle = heure_txt.replace(":", "")
        
        # CORRECTION : On joint les matériaux en une chaîne de texte propre
        mat_nom = "_".join(list(materiaux_dict.keys())).lower().strip()
        
        acteur_cle = actor_txt.lower().strip().replace(" ", "_")
        document_id = f"log_{date_cle}_{heure_cle}_{acteur_cle}_{mat_nom}"
        
        db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").document(document_id).set({
            "joueur": actor_txt,
            "type": type_mouv,
            "apport_cash": 0.0,
            "materiaux": materiaux_dict,
            "date_jeu": date_txt,
            "heure_jeu": heure_txt,
            "timestamp_enregistrement": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception:
        pass


def charger_tous_les_achats_globaux():
    try:
        coops = db.collection("cooperatives").stream()
        tous_achats = []
        for coop in coops:
            flux_stream = coop.reference.collection("comptabilite_interne").stream()
            for flux in flux_stream:
                tous_achats.append(flux.to_dict())
        return tous_achats
    except Exception:
        return []
