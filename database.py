# Contenu complet et validé pour : database.py
import datetime
import json
import streamlit as st
import pandas as pd
import pytz
from google.cloud import firestore
from google.oauth2 import service_account
import base64

# ==============================================================================
# --- 1. INITIALISATION DE LA CONNEXION UNIQUE CLOUD FIRESTORE ---
# ==============================================================================
if "text_key" in st.secrets:
    info_cles = dict(st.secrets["text_key"])
    if "private_key" in info_cles:
        raw_key = info_cles["private_key"]
        info_cles["private_key"] = raw_key.replace("\\n", "\n").replace("\n\n", "\n")
    creds = service_account.Credentials.from_service_account_info(info_cles)
    db = firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
else:
    # 🟢 SECOURS BASE64 ULTRA-STABLE : Décryptage et correction automatique du padding RSA
    try:
        cle_obscure = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImNhbGN1bGF0ZXVyLWNoYW50aWVyLWRjOTIxIiwgInByaXZhdGVfa2V5X2lkIjogIjZkMTFhNzY4NmYyOWRhZGRmODEwNWNmNTczODg2ZjAzOWM4NmEzZGQiLCAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdkFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLWXdnd1NpQWdFQUFvSUJBUURDRU81ZTB4TVpEMVRtXG4zL0hiU0EyM0ZkYXpjUnRHY1grTGhldWM0ZitRUm9vTEFzMXpheDhXTEpzcmt0TUZWSy9yZEtRV21qSXRFaVY3XG44MEdDS08rcWtIeHBFYkQyeGhQL0dmcC8rU1JwR3NVYlRyRjZDTEFYSE5QRk5TQXcvaFVkT3VyL3hPc0NiVFpSXG5McnFkbnlFblVzSVYrRVg2Z2hIK2phaU4vWWN4QlBZZHliR1dydkhCUmYyc3Z5dSt6bkZGUFFxdm9yZ0l0bkRwXG5nMS9VaGlzZHJwaWkvcm5rZW5jZHorNnBmO0tRYTN2MndMRTYzV0JIM05ubW1jRGszajZCTHN3bWFRdEpZZzAvXG54LzNxN3B1Y0kxd3JOYzgyVnBSS1J5bVhrQ0RLREVmdkgwRk1icG1scjFlQWgyRkZUNDlCeE9ndVViSW9ZYkZUXG5ubmZpTjd4VkFnTUJBQUVDZ2dFQURmUXFNNUxCT1ltcnotTHowTFRNV2FqK0ZFNXlhOXorMHdFbzJSR3Q3c21IXG5wV1pYdnZsNEMrZU9xN0lscnFvTkxhQ29LTURqRVRjUUQyckUvODhpTm5Vbm9PVm5BRU5yVGlrbnlCcFpxaDRFXG41S3NDbTFmeEUyTHBXS2x5REZ2RW1HS3pZWHNlKzhCdkNxVE53Y1llbStWNU01dXpxbWkzYStwekhleUdremxiXG4wSmU0Q1plcFdaMEZBRy96K2V4NVZYc21tWHJCWU1zYnNGRVM1QzF2Q20vV3ZDUkdiRWFPZ0xBTDlqSmVhenRmWFxuZjlJQnBvbld0emlkdE1QdUh6RWRSUkhYMzRqZnpSOUVUelhoZ2dLVHRFSVBleXFMVkxOdXU4cSt3RVRlTzcwR1xuUWZKRDR0Z040dVhqZFZ2UG0xSU9QbEVhZmJ1LytDYTV5bjA5OHBJclFRS0JnUUR4ditPWWE2QzYrYnZnUzVoTVxuVGY1U3lqK2RGV1czTkZlWENHK0ZhRnM0T3NxMUxqMm0xWSsyNUVMTFBpK05qNmJEdzVyR1d4ZjVrQlduWldITVxuQmwxMGl3OWFIVmNqWHBjS0s1bS84bU8zcmNrcWRTa1ZqV2h4WGhQekpRbkRJZmpSWjVna052c2pUcXEvcmdZVFxudmpJVStlMXRjWXpWT09nYklJZGY0UUZxUVFCZ1FETmdYbzUyeGIyc3pPS0RHUXkweS8yMHhUSXNqN3E0UWVGXG5kc05wV3Y4YjZPTlQ4bWtyc1V6TGllSkplYW9xV1hzM2dPQUNZSU12SU4vTVd0TkdqSHZvL0tvQjIwODErSy9cbjlhMzNJUEt6T002YVNuZkgrVzJDS0l0WWdsOVZCc1JFeXdVc2JwQW5qcVpqcjErdGI1K3E2T2FpSllMTitVeGVcbi9XbThoTmJGRlFLQmdRQzcgbmY3V2xnRGgyMXN4MGJsYXp0VG9EOHFhOEd2RktTd3BIUVRmOW9PRStpdkR2U1ZmXG55ektEOEZiZVFWN0tjSUd1T2lwdWN0Z0NlUTQxSWZ0cVNpNVJlbkxwcndlbmpZdU8reE9SNGwzOWVVUThUVDBiXG5XdW1Kd2tlZFZrdGpRNFJGa0M2RlBKNWZ5aUU2RGFidHY1aENxMDBXdVY5aFE1U1A1MFFQVDZLM2dSSi9GTjhSXG5pczYxaGxpczQxaGUxTXFlRkhOYnFRZXBYREYra2c5OXlUVjBzMkQwWHBvQUhDL2xuTVprTlJJbU5pYmdYTUswXG5BQjczRmxRUEJ0ditDZGFmTzdkcTdhWFRjbHA2clFSR3B0TGNFMktwbVFIM0tGZ3N4d1hHNmRpaUNJQ25ibFdZXG5NT3NKdVByRDZsZnZINjQyaVNlZVIxbUg3Mk5pWGtOZWVDY0VDUUtCZ1FEZktLN1NnWnl0OTNCWUdPbi9RRUlcbkdWSVZzYVMwdTI4VlREb3d6aUlpUFZqVG0ydVYzelZtcU5xcm4wVEt5b1ZwQ3NoejVoSVQrdnEvUkZVS0RHeXFcblA0L0xuZTJsaEtVbzBycjJXRld1WitPUy9lMUhxd0E2QzlsQWN6M0p6QXFtczh0dTdvdDJMZEEwVHBpdXhpOGZcbjJzVU9yTkdIVXFMcllidWc0cFZyWGc9PVxuLS0tLS1FTkQgUFJJVkFTERSBLRVktLS0tLVxuIiwgImNsaWVudF9lbWFpbCI6ICJmaXJlYmFzZS1hZG1pbnNkay1mYnN2Y0BjYWxjdWxhdGV1ci1jaGFudGllci1kYzkyMS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJjbGllbnRfaWQiOiAiMTA5MDQ3NjI0OTkxOTAyMzM3NDEwIiwgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsICJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3YxL2NlcnRzIiwgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tYy9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ZpcmViYXNlLWFkbWluc2RrLWZic3ZjJTQwY2FsY3VsYXRldXItY2hhbnRpZXItZGM5MjEuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0="
        
        info_cles = json.loads(base64.b64decode(cle_obscure).decode("utf-8"))
        if "private_key" in info_cles:
            # 🟢 RESTAURATION MANUELLE DES VRAIS ESCAPES DU CERTIFICAT PEM RSA
            info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
            
        creds = service_account.Credentials.from_service_account_info(info_cles)
        db = firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
    except Exception as e:
        db = firestore.Client(project="calculateur-chantier-dc921")

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
