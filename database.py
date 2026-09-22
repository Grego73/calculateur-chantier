# Contenu complet et validé pour le début de : database.py
import datetime
import json
import streamlit as st
import pandas as pd
import pytz
from google.cloud import firestore
from google.oauth2 import service_account

# ==============================================================================
# --- 1. INITIALISATION DE LA CONNEXION UNIQUE CLOUD FIRESTORE ---
# ==============================================================================
if "text_key" in st.secrets:
    import json
    secret_raw = st.secrets["text_key"]
    
    # Si le secret est une chaîne de caractères (texte), on utilise json.loads
    if isinstance(secret_raw, str):
        info_cles = json.loads(secret_raw)
    # Si Streamlit l'a déjà converti en dictionnaire/objet, on le convertit proprement
    else:
        info_cles = dict(secret_raw)
        
    creds = service_account.Credentials.from_service_account_info(info_cles)
    db = firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
else:
    db = firestore.Client(project="calculateur-chantier-dc921")


# Fuseau horaire de référence pour l'application
TZ_PARIS = pytz.timezone('Europe/Paris')


# ==============================================================================
# --- 2. FONCTIONS DE LECTURE FIRESTORE ---
# ==============================================================================
@st.cache_data(ttl=600)
def charger_salaires_config():
    try:
        doc_ref = db.collection("configuration_salaires").document("grille")
        doc = doc_ref.get()
        if doc.exists and doc.to_dict() is not None: 
            return dict(doc.to_dict())
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les salaires sur Firebase ({e}).")
    return {}

@st.cache_data(ttl=600)
def charger_materiaux_config():
    try:
        doc_ref = db.collection("configuration_materiaux").document("catalogue")
        doc = doc_ref.get()
        if doc.exists and doc.to_dict() is not None: 
            return dict(doc.to_dict())
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les matériaux sur Firebase ({e}).")
    return {"Sable": 12.0, "Terre": 16.0, "Enrobé": 42.0, "Armature": 70.0, "Tôle": 55.0, "Béton": 45.0, "Panneaux": 90.0, "Tuyaux": 32.0, "Canalisations": 35.0, "Poutres": 70.0}

@st.cache_data(ttl=600)
def charger_catalogue_engins():
    try:
        docs = db.collection("catalogue_engins").stream()
        catalogue = {}
        for doc in docs: 
            data = doc.to_dict()
            if data:
                catalogue[str(doc.id)] = float(data.get("prix_jour", 380.0))
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
                types.add(str(data.get("type_brut", "Autre")))
        return sorted(list(types)) if types else ["Pelleteuses", "Camions Benne"]
    except Exception:
        return ["Pelleteuses", "Camions Benne"]

@st.cache_data(ttl=600)
def charger_catalogue_chantiers():
    try:
        docs = db.collection("modeles_chantiers").stream()
        catalogue = {
            "Choisir un chantier pré-configuré...": {
                "revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, 
                "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, 
                "canalisations": 0.0, "poutres": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, 
                "jh_cond": 0.0, "etapes_techniques": []
            }
        }
        for doc in docs: 
            data = doc.to_dict()
            if data:
                etapes_stream = doc.reference.collection("etapes").stream()
                liste_etapes = []
                for sub_doc in etapes_stream:
                    sub_data = sub_doc.to_dict()
                    if sub_data:
                        liste_etapes.append(dict(sub_data))
                
                data["etapes_techniques"] = sorted(liste_etapes, key=lambda x: x.get("num_etape", 1))
                catalogue[str(doc.id)] = data
        return catalogue
    except Exception:
        return {
            "Choisir un chantier pré-configuré...": {
                "revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, 
                "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, 
                "canalisations": 0.0, "poutres": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, 
                "jh_cond": 0.0, "etapes_techniques": []
            }
        }

@st.cache_data(ttl=600)
def charger_donnees():
    try:
        docs = db.collection("chantiers").stream()
        liste_chantiers = []
        for doc in docs:
            d = doc.to_dict()
            if d:
                liste_chantiers.append({
                    'Nom du Chantier': str(doc.id), 
                    'Revenus (€)': float(d.get('revenus', 0.0)), 
                    'Durée (Jours)': float(d.get('jours', 0.0)), 
                    'Coût Matériaux (€)': float(d.get('cout_materiaux', 0.0)), 
                    'Coût Location Engins (€)': float(d.get('cout_location', 0.0)), 
                    'Coût Salaires (€)': float(d.get('cout_salaires', 0.0)), 
                    'Dépenses Totales (€)': float(d.get('depenses_totales', 0.0)), 
                    'Bénéfice Net (€)': float(d.get('benefice_net', 0.0)), 
                    'Gain / Jour (€)': float(d.get('gain_par_jour', 0.0)), 
                    'ROI (%)': float(d.get('roi', 0.0)), 
                    'ROI / Jour (%)': float(d.get('roi_par_jour', 0.0))
                })
        return pd.DataFrame(liste_chantiers) if liste_chantiers else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# ==============================================================================
# --- 3. FONCTIONS D'ÉCRITURE ---
# ==============================================================================
def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    try:
        db.collection("chantiers").document(nom).set({
            "revenus": float(rev), "cout_materiaux": float(mats), "cout_location": float(loc), 
            "cout_salaires": float(sal), "depenses_totales": float(total), "benefice_net": float(net), 
            "roi": float(roi), "jours": float(jours), "gain_par_jour": float(gpj), "roi_par_jour": float(rpj)
        })
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de l'enregistrement du chantier : {e}")

def reinitialiser_db():
    try:
        chantiers_modeles = db.collection("modeles_chantiers").stream()
        for c_mod in chantiers_modeles:
            sub_etapes = c_mod.reference.collection("etapes").stream()
            for et in sub_etapes:
                et.reference.delete()
            c_mod.reference.delete()

        collections = ["chantiers", "configuration_salaires", "configuration_materiaux", "catalogue_engins"]
        for col_name in collections:
            docs = db.collection(col_name).stream()
            for doc in docs: 
                doc.reference.delete()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de la réinitialisation : {e}")

def enregistrer_log(type_action, details):
    try:
        tz_paris = pytz.timezone('Europe/Paris')
        maintenant = datetime.datetime.now(tz_paris)
        timestamp_txt = maintenant.strftime("%Y-%m-%d %H:%M:%S")
        
        db.collection("journaux_actions").add({
            "timestamp": timestamp_txt,
            "type_action": str(type_action),
            "details": str(details)
        })
    except Exception:
        pass


# ==============================================================================
# --- 4. FONCTIONS AVANCÉES POUR LE SUIVI INTERNE DES COOPÉRATIVES ---
# ==============================================================================
def lister_toutes_les_cooperatives():
    try:
        coops_stream = db.collection("cooperatives").stream()
        return sorted([str(doc.id) for doc in coops_stream])
    except Exception:
        return []

def verifier_et_inscrire_joueur(nom_coop, mdp_saisi, pseudo_joueur):
    if not nom_coop or not mdp_saisi or not pseudo_joueur:
        return False, "⚠️ Veuillez remplir tous les champs.", 1
        
    coop_ref = db.collection("cooperatives").document(nom_coop)
    coop_doc = coop_ref.get()
    
    if not coop_doc.exists:
        coop_ref.set({
            "mdp_niveau3": str(mdp_saisi),
            "mdp_niveau2": f"{mdp_saisi}2",
            "mdp_niveau1": f"{mdp_saisi}1",
            "membres": [str(pseudo_joueur)]
        })
        return True, "🟢 Coopérative créée ! Vous êtes Niveau 3 (Créateur).", 3
    
    coop_data = coop_doc.to_dict()
    mdp3 = coop_data.get("mdp_niveau3") or coop_data.get("mot_de_passe")
    mdp2 = coop_data.get("mdp_niveau2") or f"{mdp3}2"
    mdp1 = coop_data.get("mdp_niveau1") or f"{mdp3}1"
    
    if str(mdp_saisi).strip() == str(mdp3).strip(): 
        niveau_detecte = 3
    elif str(mdp_saisi).strip() == str(mdp2).strip(): 
        niveau_detecte = 2
    elif str(mdp_saisi).strip() == str(mdp1).strip(): 
        niveau_detecte = 1
    else: 
        return False, "🔒 Mot de passe incorrect.", 1
        
    membres_actuels = coop_data.get("membres", [])
    if pseudo_joueur in membres_actuels or niveau_detecte == 3:
        if pseudo_joueur not in membres_actuels:
            membres_actuels.append(str(pseudo_joueur))
            coop_ref.update({"membres": membres_actuels})
        enregistrer_log("CONNEXION", f"Le joueur [{pseudo_joueur}] s'est connecté à la coop [{nom_coop}] (Niveau {niveau_detecte}).")
        return True, "👋 Connexion réussie.", niveau_detecte
        
    if len(membres_actuels) >= 4:
        return False, "🚫 Limite de 4 joueurs inscris atteinte.", 1
        
    membres_actuels.append(str(pseudo_joueur))
    coop_ref.update({"membres": membres_actuels})
    return True, "📝 Inscription réussie !", niveau_detecte

def ajouter_membres_bloc_coop(nom_coop, texte_membres_brut):
    if not nom_coop or not texte_membres_brut.strip():
        return False, "⚠️ Saisissez au moins un pseudo valide."
    try:
        coop_ref = db.collection("cooperatives").document(nom_coop)
        coop_doc = coop_ref.get()
        if not coop_doc.exists: 
            return False, "❌ Coopérative introuvable."
        coop_data = coop_doc.to_dict()
        membres_actuels = coop_data.get("membres", [])
        pseudos = [p.strip() for p in texte_membres_brut.replace(",", " ").split() if p.strip()]
        compteur = 0
        for pseudo in pseudos:
            if pseudo in membres_actuels: 
                continue
            if len(membres_actuels) >= 4: 
                break
            membres_actuels.append(str(pseudo))
            compteur += 1
        if compteur > 0:
            coop_ref.update({"membres": membres_actuels})
            return True, f"🚀 {compteur} collaborateur(s) inscrit(s) !"
    except Exception:
        pass
    return False, "ℹ️ Aucun membre ajouté."

def ajouter_reinvestissement_membre(nom_coop, pseudo_joueur, montant_cash):
    try:
        mouvement_id = f"reinvest_{int(pd.Timestamp.now().timestamp())}_{pseudo_joueur}"
        db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").document(mouvement_id).set({
            "joueur": str(pseudo_joueur), 
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
        mat_nom = "_".join(list(materiaux_dict.keys())).lower().strip()
        document_id = f"log_{date_cle}_{heure_cle}_{actor_txt.lower().strip()}_{mat_nom}"
        
        db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").document(document_id).set({
            "joueur": str(actor_txt), 
            "type": str(type_mouv), 
            "apport_cash": 0.0, 
            "materiaux": materiaux_dict,
            "date_jeu": str(date_txt), 
            "heure_jeu": str(heure_txt), 
            "timestamp_enregistrement": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception:
        pass

@st.cache_data(ttl=60)  # 🟢 Bloque les requêtes réseau identiques pendant 60 secondes
def charger_flux_coop_cache(nom_coop):
    """Récupère les documents de comptabilité en limitant l'impact sur les quotas Firebase."""
    try:
        flux_stream = db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").stream()
        return [f.to_dict() for f in flux_stream]
    except Exception:
        return []
