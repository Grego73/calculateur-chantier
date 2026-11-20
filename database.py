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
@st.cache_resource
def initialiser_firestore():
    """Initialise le client Firestore une seule fois pour toute la durée de vie du serveur."""
    if "text_key" in st.secrets:
        secret_raw = st.secrets["text_key"]
        info_cles = json.loads(secret_raw) if isinstance(secret_raw, str) else dict(secret_raw)
        if "private_key" in info_cles:
            info_cles["private_key"] = info_cles["private_key"].replace("\\n", "\n")
        try:
            creds = service_account.Credentials.from_service_account_info(info_cles)
            return firestore.Client(project="calculateur-chantier-dc921", credentials=creds)
        except Exception as e:
            st.error(f"❌ Erreur lors de l'application des identifiants : {e}")
            return None
    return firestore.Client(project="calculateur-chantier-dc921")

db = initialiser_firestore()
TZ_PARIS = pytz.timezone("Europe/Paris")


# ==============================================================================
# --- 2. FONCTIONS DE LECTURE FIRESTORE (MISES EN CACHE) ---
# ==============================================================================
@st.cache_data(ttl=600)
def charger_salaires_config():
    try:
        doc = db.collection("configuration_salaires").document("grille").get()
        if doc.exists and doc.to_dict() is not None:
            return dict(doc.to_dict())
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les salaires sur Firebase ({e}).")
    return {}

@st.cache_data(ttl=600)
def charger_synthese_salaires():
    """Charge tous les tarifs journaliers moyens (CDI/CDD) depuis synthese_grille_tarifaire."""
    tarifs = {}
    try:
        for doc in db.collection("synthese_grille_tarifaire").stream():
            d = doc.to_dict() or {}
            tarifs[doc.id] = float(d.get("prix_moyen_journalier_7", d.get("prix_moyen_mensuel", 240.0)))
    except Exception:
        pass
    return tarifs

@st.cache_data(ttl=600)
def charger_materiaux_config():
    try:
        doc = db.collection("configuration_materiaux").document("catalogue").get()
        if doc.exists and doc.to_dict() is not None:
            return dict(doc.to_dict())
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire les matériaux sur Firebase ({e}).")
    return {
        "Sable": 12.0, "Terre": 16.0, "Enrobé": 42.0, "Armature": 70.0,
        "Tôle": 55.0, "Béton": 45.0, "Panneaux": 90.0, "Tuyaux": 32.0,
        "Canalisations": 35.0, "Poutres": 70.0
    }

@st.cache_data(ttl=600)
def charger_tarifs_engins_unifies():
    """Charge le dictionnaire complet des engins : {'Pelleteuse (N2)': 450.0, ...}."""
    tarifs = {}
    try:
        for doc in db.collection("engins").stream():
            d = doc.to_dict() or {}
            tarifs[doc.id] = float(d.get("tarif_location_jour", 380.0))
    except Exception:
        pass
    return tarifs

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
    except Exception:
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
        return sorted(list(types)) if types else ["Pelleteuse", "Camion benne"]
    except Exception:
        return ["Pelleteuse", "Camion benne"]

@st.cache_data(ttl=600)
def charger_catalogue_chantiers():
    """Charge l'intégralité du catalogue des modèles de chantiers et leurs étapes."""
    catalog_dict = {}
    try:
        chantiers_stream = db.collection("modeles_chantiers").stream()
        for ch_doc in chantiers_stream:
            ch_id = ch_doc.id
            ch_data = ch_doc.to_dict() or {}
            etapes_stream = db.collection("modeles_chantiers").document(ch_id).collection("etapes").stream()
            liste_etapes = sorted([et.to_dict() for et in etapes_stream], key=lambda x: x.get("num_etape", 1))
            catalog_dict[ch_id] = {
                "nom_modele": ch_data.get("nom_modele", ch_id),
                "revenus": float(ch_data.get("revenus", 0.0)),
                "jours_globaux": int(ch_data.get("jours_globaux", 0)),
                "heures_globales": int(ch_data.get("heures_globales", 0)),
                "minutes_globales": int(ch_data.get("minutes_globales", 0)),
                "etapes_techniques": liste_etapes
            }
    except Exception:
        pass
    return catalog_dict

@st.cache_data(ttl=600)
def charger_donnees():
    try:
        docs = db.collection("chantiers").stream()
        liste_chantiers = []
        for doc in docs:
            d = doc.to_dict()
            if d:
                liste_chantiers.append({
                    "Nom du Chantier": str(doc.id),
                    "Revenus (€)": float(d.get("revenus", 0.0)),
                    "Durée (Jours)": float(d.get("jours", 0.0)),
                    "Coût Matériaux (€)": float(d.get("cout_materiaux", 0.0)),
                    "Coût Location Engins (€)": float(d.get("cout_location", 0.0)),
                    "Coût Salaires (€)": float(d.get("cout_salaires", 0.0)),
                    "Dépenses Totales (€)": float(d.get("depenses_totales", 0.0)),
                    "Bénéfice Net (€)": float(d.get("benefice_net", 0.0)),
                    "Gain / Jour (€)": float(d.get("gain_par_jour", 0.0)),
                    "ROI (%)": float(d.get("roi", 0.0)),
                    "ROI / Jour (%)": float(d.get("roi_par_jour", 0.0))
                })
        return pd.DataFrame(liste_chantiers) if liste_chantiers else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def charger_etapes_chantier_cache(chantier_id):
    etapes_liste = []
    try:
        etapes_stream = db.collection("modeles_chantiers").document(chantier_id).collection("etapes").stream()
        for doc in etapes_stream:
            etapes_liste.append(doc.to_dict())
    except Exception:
        pass
    return etapes_liste


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
        for c_mod in db.collection("modeles_chantiers").stream():
            for et in c_mod.reference.collection("etapes").stream():
                et.reference.delete()
            c_mod.reference.delete()

        for col_name in ["chantiers", "configuration_salaires", "configuration_materiaux", "catalogue_engins"]:
            for doc in db.collection(col_name).stream():
                doc.reference.delete()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"❌ Échec de la réinitialisation : {e}")

def enregistrer_log(type_action, details):
    try:
        maintenant = datetime.datetime.now(TZ_PARIS)
        db.collection("journaux_actions").add({
            "timestamp": maintenant.strftime("%Y-%m-%d %H:%M:%S"),
            "type_action": str(type_action),
            "details": str(details)
        })
    except Exception:
        pass


# ==============================================================================
# --- 4. FONCTIONS COOPÉRATIVES ---
# ==============================================================================
def lister_toutes_les_cooperatives():
    try:
        return sorted([str(doc.id) for doc in db.collection("cooperatives").stream()])
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
        return False, "🚫 Limite de 4 joueurs inscrits atteinte.", 1

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
        membres_actuels = coop_doc.to_dict().get("membres", [])
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

def enregistrer_ligne_historique_brute(nom_coop, date_txt, heure_txt, actor_txt, type_mouv, materiaux_dict, occurrence=1):
    if not materiaux_dict:
        return
    try:
        date_cle = "".join(reversed(date_txt.split("/")))
        heure_cle = heure_txt.replace(":", "")
        type_cle = str(type_mouv).lower().strip()
        acteur_cle = str(actor_txt).lower().strip().replace(" ", "_")
        mat_cle = "_".join(
            f"{k.lower().strip()}_{int(v)}" for k, v in sorted(materiaux_dict.items())
        )
        document_id = f"log_{date_cle}_{heure_cle}_{acteur_cle}_{type_cle}_{mat_cle}_n{int(occurrence)}"

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


@st.cache_data(ttl=60)
def charger_flux_coop_cache(nom_coop):
    try:
        flux_stream = db.collection("cooperatives").document(nom_coop).collection("comptabilite_interne").stream()
        return [f.to_dict() for f in flux_stream]
    except Exception:
        return []

