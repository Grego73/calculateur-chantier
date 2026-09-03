import streamlit as st
import pandas as pd
from google.cloud import firestore
import json
from google.oauth2 import service_account

if "text_key" in st.secrets:
    info_cles = json.loads(st.secrets["text_key"])
    creds = service_account.Credentials.from_service_account_info(info_cles)
    db = firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
else:
    db = firestore.Client(project="calculateur-chantier-dc921")

# Vos fonctions (charger_salaires_config, etc.) restent en dessous...


# ==============================================================================
# --- FONCTIONS DE LECTURE (SÉCURISÉES PAR CACHE EXTENSIBLE DE 10 MIN) ---
# ==============================================================================
# Le reste de votre fichier database.py d'origine reste inchangé...

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
# --- FONCTIONS D'ÉCRITURE ---
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
        
        # Écriture NoSQL dans la collection de traçabilité
        db.collection("journaux_actions").add({
            "timestamp": timestamp_txt,
            "type_action": type_action,
            "details": details
        })
    except Exception as e:
        pass
        
# À ajouter tout en bas de : database.py

def verifier_et_inscrire_joueur(nom_coop, mdp_saisi, pseudo_joueur):
    """
    Vérifie le mot de passe de la coopérative et inscrit le joueur si la limite 
    des 4 membres inscrits n'est pas atteinte.
    """
    if not nom_coop or not mdp_saisi or not pseudo_joueur:
        return False, "⚠️ Veuillez remplir tous les champs."
        
    coop_ref = db.collection("cooperatives").document(nom_coop)
    coop_doc = coop_ref.get()
    
    # Si la coopérative n'existe pas encore, on la crée avec le mot de passe fourni
    if not coop_doc.exists:
        coop_ref.set({
            "mot_de_passe": mdp_saisi,
            "membres": [pseudo_joueur]
        })
        return True, f"🟢 Coopérative créée ! Bienvenue à bord, premier membre : {pseudo_joueur}"
    
    coop_data = coop_doc.to_dict()
    
    # Vérification du mot de passe de la coop
    if coop_data.get("mot_de_passe") != mdp_saisi:
        return False, "🔒 Mot de passe de la coopérative incorrect."
        
    membres_actuels = coop_data.get("membres", [])
    
    # Si le joueur fait déjà partie des inscrits, on le laisse entrer
    if pseudo_joueur in membres_actuels:
        return True, f"👋 Content de vous revoir, {pseudo_joueur}."
        
    # Si le joueur n'est pas inscrit, on vérifie la jauge limite de 4 joueurs max
    if len(membres_actuels) >= 4:
        return False, f"🚫 Accès refusé : La coopérative '{nom_coop}' a atteint sa limite maximale de 4 joueurs inscrits."
        
    # Le joueur est valide et il reste de la place, on l'ajoute au tableau NoSQL
    membres_actuels.append(pseudo_joueur)
    coop_ref.update({"membres": membres_actuels})
    return True, f"📝 Inscription réussie ! Bienvenue dans la coopérative, membre n°{len(membres_actuels)} : {pseudo_joueur}"

# À coller tout en bas de : database.py

def enregistrer_mouvement_coop(nom_coop, pseudo_joueur, type_mouvement, materiaux_dict, apport_financier=0.0):
    """
    Enregistre un flux financier ou matériel pour un membre de la coopérative.
    type_mouvement peut être : "APPORT_INITIAL", "REAPPROVISIONNEMENT" ou "ACHAT_INTERNE"
    """
    mouvement_id = f"flux_{int(pd.Timestamp.now().timestamp())}_{pseudo_joueur}"
    db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").document(mouvement_id).set({
        "joueur": pseudo_joueur,
        "type": type_mouvement,
        "apport_cash": float(apport_financier),
        "materiaux": materiaux_dict,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def charger_tous_les_achats_globaux():
    """
    Parcourt toutes les structures pour offrir un récapitulatif complet de chaque joueur
    inscrit, peu importe sa coopérative.
    """
    coops = db.collection("cooperatives").stream()
    tous_achats = []
    
    for coop in coops:
        flux_stream = coop.reference.collection("comptabilite_interne").stream()
        for flux in flux_stream:
            data = flux.to_dict()
            tous_achats.append(data)
            
    return tous_achats

# À ajouter tout en bas de : database.py

def lister_toutes_les_cooperatives():
    """
    Récupère la liste de tous les noms de coopératives enregistrées dans Firestore.
    """
    try:
        coops_stream = db.collection("cooperatives").stream()
        list_coops = [doc.id for doc in coops_stream]
        return sorted(list_coops)
    except Exception:
        return []

# À ajouter tout en bas de : database.py

def ajouter_membre_manuel_coop(nom_coop, pseudo_a_ajouter):
    """
    Force l'inscription d'un collaborateur dans le tableau des membres d'une coopérative,
    dans la limite stricte de 4 personnes au total.
    """
    if not nom_coop or not pseudo_a_ajouter:
        return False, "⚠️ Pseudo invalide."
        
    coop_ref = db.collection("cooperatives").document(nom_coop)
    coop_doc = coop_ref.get()
    
    if not coop_doc.exists:
        return False, "❌ La coopérative n'existe pas."
        
    coop_data = coop_doc.to_dict()
    membres_actuels = coop_data.get("membres", [])
    
    if pseudo_a_ajouter in membres_actuels:
        return False, f"ℹ️ {pseudo_a_ajouter} fait déjà partie des membres inscrits."
        
    if len(membres_actuels) >= 4:
        return False, "🚫 Limite atteinte : Impossible d'ajouter. La coopérative compte déjà 4 membres."
        
    membres_actuels.append(pseudo_a_ajouter)
    coop_ref.update({"membres": membres_actuels})
    return True, f"✅ {pseudo_a_ajouter} a été ajouté avec succès à la coopérative !"
