import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

# ==============================================================================
# --- 1. INITIALISATION DE FIREBASE & FIRESTORE (SÉCURISÉE) ---
# ==============================================================================
if not firebase_admin._apps:
    firebase_info = dict(st.secrets["firebase"])
    if "private_key" in firebase_info:
        firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(firebase_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==============================================================================
# --- 2. FONCTIONS DE CHARGEMENT ET SAUVEGARDE DYNAMIQUES (FIREBASE) ---
# ==============================================================================

def charger_salaires_config():
    try:
        doc_ref = db.collection("configuration_salaires").document("grille")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception:
        pass
    
    # Données par défaut si le document n'existe pas encore ou bug
    data_defaut = {"Chef": 230.0, "Ouvrier": 230.0, "Conducteur": 230.0, "Intérim": 220.0}
    try:
        db.collection("configuration_salaires").document("grille").set(data_defaut)
    except Exception:
        pass
    return data_defaut

def charger_materiaux_config():
    try:
        doc_ref = db.collection("configuration_materiaux").document("catalogue")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception:
        pass
        
    data_defaut = {
        "Sable": 12.0, "Terre": 16.0, "Enrobé": 42.0, "Armature": 70.0, "Tôle": 55.0,
        "Béton": 45.0, "Panneaux": 90.0, "Tuyaux": 32.0, "Canalisations": 35.0, "Poutres": 70.0
    }
    try:
        db.collection("configuration_materiaux").document("catalogue").set(data_defaut)
    except Exception:
        pass
    return data_defaut

def charger_catalogue_engins():
    docs = db.collection("catalogue_engins").stream()
    catalogue = {}
    for doc in docs:
        catalogue[doc.id] = doc.to_dict().get("prix_jour", 0.0)
    if not catalogue:
        engins_base = {
            "Camion Benne N3 - Renault Trucks K 430 (430 cv)": {"type_brut": "Camions Benne", "prix_jour": 420.0},
            "Pelleteuse N2 - Takeuchi TB2150 (85.0 kW)": {"type_brut": "Pelleteuses", "prix_jour": 200.0},
            "Niveleuse N2 - CAT 14 (178 kW)": {"type_brut": "Niveleuse", "prix_jour": 580.0},
            "Finisseur N3 - CAT AP600 (129 kW)": {"type_brut": "Finisseur", "prix_jour": 490.0},
            "Compacteur Enrobé N3 - Dynapac CC4200 VI (100 kW)": {"type_brut": "Compacteur pour enrobé", "prix_jour": 340.0},
            "Fraiseuse N2 - CAT PM312 (256 kW)": {"type_brut": "Fraiseuse", "prix_jour": 380.0}
        }
        for k, v in engins_base.items():
            db.collection("catalogue_engins").document(k).set(v)
            catalogue[k] = v["prix_jour"]
    return catalogue

def charger_types_engins_bruts():
    docs = db.collection("catalogue_engins").stream()
    types = set()
    for doc in docs:
        types.add(doc.to_dict().get("type_brut", "Autre"))
    return sorted(list(types)) if types else ["Pelleteuses", "Camions Benne", "Niveleuse", "Finisseur", "Compacteur pour enrobé", "Fraiseuse"]

def charger_catalogue_chantiers():
    docs = db.collection("modeles_chantiers").stream()
    catalogue = {"Choisir un chantier pré-configuré...": {
        "revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
        "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
        "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []
    }}
    for doc in docs:
        catalogue[doc.id] = doc.to_dict()
        
    if len(catalogue) == 1:
        engins_demo = [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Fraiseuse", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 4, "Type d'engin requis": "Niveleuse", "Niveau requis": "N2"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Finisseur", "Niveau requis": "N3"},
            {"N° Étape": 4, "Durée Étape (jours)": 4, "Type d'engin requis": "Compacteur pour enrobé", "Niveau requis": "N3"}
        ]
        demo_data = {"nom_modele": "Goudronnage d'une route (Grande surface) (214 599 €)", "revenus": 214599.0, "jours": 16, "sable": 488.0, "terre": 0.0, "enrobe": 618.0, "armature": 0.0, "tole": 0.0, "beton": 0.0, "panneaux": 6.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0, "jh_chef": 16.0, "jh_ouvrier": 48.0, "jh_cond": 28.0, "engins_requis": engins_demo}
        db.collection("modeles_chantiers").document(demo_data["nom_modele"]).set(demo_data)
        catalogue[demo_data["nom_modele"]] = demo_data
    return catalogue

def charger_donnees():
    docs = db.collection("chantiers").stream()
    liste_chantiers = []
    for doc in docs:
        d = doc.to_dict()
        liste_chantiers.append({
            'Nom du Chantier': doc.id,
            'Revenus (€)': d.get('revenus', 0.0),
            'Durée (Jours)': d.get('jours', 0),
            'Coût Matériaux (€)': d.get('cout_materiaux', 0.0),
            'Coût Location Engins (€)': d.get('cout_location', 0.0),
            'Coût Salaires (€)': d.get('cout_salaires', 0.0),
            'Dépenses Totales (€)': d.get('depenses_totales', 0.0),
            'Bénéfice Net (€)': d.get('benefice_net', 0.0),
            'Gain / Jour (€)': d.get('gain_par_jour', 0.0),
            'ROI (%)': d.get('roi', 0.0),
            'ROI / Jour (%)': d.get('roi_par_jour', 0.0)
        })
    return pd.DataFrame(liste_chantiers) if liste_chantiers else pd.DataFrame(columns=["Nom du Chantier", "Revenus (€)", "Durée (Jours)", "Coût Matériaux (€)", "Coût Location Engins (€)", "Coût Salaires (€)", "Dépenses Totales (€)", "Bénéfice Net (€)", "Gain / Jour (€)", "ROI (%)", "ROI / Jour (%)"])

def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    db.collection("chantiers").document(nom).set({
        "revenus": rev, "cout_materiaux": mats, "cout_location": loc, "cout_salaires": sal,
        "depenses_totales": total, "benefice_net": net, "roi": roi, "jours": jours,
        "gain_par_jour": gpj, "roi_par_jour": rpj
    })

def reinitialiser_db():
    collections = ["chantiers", "modeles_chantiers", "configuration_salaires", "configuration_materiaux", "catalogue_engins"]
    for col_name in collections:
        docs = db.collection(col_name).stream()
        for doc in docs:
            doc.reference.delete()
    st.toast("Base Firebase réinitialisée ! Rechargement...")

# Chargement initial des configurations dynamiques
SALAIRES_DB = charger_salaires_config()
MATERIAUX_DB = charger_materiaux_config()
CATALOGUE_ENGINS = charger_catalogue_engins()
TYPES_ENGINS_BRUTS = charger_types_engins_bruts()
CATALOGUE_CHANTIERS = charger_catalogue_chantiers()

# ==============================================================================
# --- 3. CONCEPTION DES ONGLETS DE L'APPLICATION ---
# ==============================================================================
onglet1, onglet2, onglet3 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement", "🔒 Espace Direction"])

# --- ONGLET 1 : FORMULAIRE DE SAISIE PRINCIPAL ---
with onglet1:
    st.subheader("Formulaire de saisie")
    liste_triee = ["Choisir un chantier pré-configuré..."] + sorted([k for k in CATALOGUE_CHANTIERS.keys() if k != "Choisir un chantier pré-configuré..."])
    chantier_selectionne = st.selectbox("🚀 Sélectionner un modèle de chantier dynamique :", liste_triee)
    
    donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
    valeur_nom_defaut = "" if chantier_selectionne == "Choisir un chantier pré-configuré..." else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=float(donnees_modele["revenus"]))
        jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=int(donnees_modele["jours"]), min_value=0)

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=float(donnees_modele["sable"]))
            qte_terre = st.number_input("Tonnes de Terre :", value=float(donnees_modele["terre"]))
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=float(donnees_modele["enrobe"]))
            qte_armature = st.number_input("Unités d'Armature métallique :", value=float(donnees_modele["armature"]))
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=float(donnees_modele["tole"]))
            qte_beton = st.number_input("Tonnes de Béton :", value=float(donnees_modele["beton"]))
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=float(donnees_modele["panneaux"]))
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=float(donnees_modele["tuyaux"]))
            qte_eaux_usees = st.number_input("Unités de Canalisations eaux usées :", value=float(donnees_modele["canalisations"]))
            qte_poutres = st.number_input("Unités de Poutres en acier :", value=float(donnees_modele["poutres"]))
        with c_px:
            prix_sable = st.number_input("Prix Sable (€/t) :", value=float(MATERIAUX_DB.get("Sable", 12)))
            prix_terre = st.number_input("Prix Terre (€/t) :", value=float(MATERIAUX_DB.get("Terre", 16)))
            prix_enrobe = st.number_input("Prix Enrobé (€/t) :", value=float(MATERIAUX_DB.get("Enrobé", 42)))
            prix_armature = st.number_input("Prix Armature (€/u) :", value=float(MATERIAUX_DB.get("Armature", 70)))
            prix_tole = st.number_input("Prix Tôle (€/u) :", value=float(MATERIAUX_DB.get("Tôle", 55)))
            prix_beton = st.number_input("Prix Béton (€/t) :", value=float(MATERIAUX_DB.get("Béton", 45)))
            prix_panneaux = st.number_input("Prix Panneaux (€/u) :", value=float(MATERIAUX_DB.get("Panneaux", 90)))
            prix_tuyaux = st.number_input("Prix Tuyaux d'eau (€/u) :", value=float(MATERIAUX_DB.get("Tuyaux", 32)))
            prix_eaux_usees = st.number_input("Prix Canalisations (€/u) :", value=float(MATERIAUX_DB.get("Canalisations", 35)))
            prix_poutres = st.number_input("Prix Poutres acier (€/u) :", value=float(MATERIAUX_DB.get("Poutres", 70)))

        # Calcul instantané du coût de revient des fournitures
        total_mats_direct = float((qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_eaux_usees*prix_eaux_usees) + (qte_poutres*prix_poutres))
        total_mats_formatte = f"{total_mats_direct:,.0f}".replace(",", " ")
        st.info(f"🧱 **Total estimé des matériaux :** {total_mats_formatte} €")
        
    with col2:
        st.markdown("### --- GRILLE SALARIALE & INTERIM ---")
        px_chef = st.number_input("Coût journalier Chef (€/jour) :", value=float(SALAIRES_DB.get("Chef", 230)))
        jh_chef = st.number_input("Total Jours-Homme Chef :", value=float(donnees_modele["jh_chef"]))
        
        px_ouvrier = st.number_input("Coût journalier Ouvrier (€/jour) :", value=float(SALAIRES_DB.get("Ouvrier", 230)))
        jh_ouvrier = st.number_input("Total Jours-Homme Ouvrier :", value=float(donnees_modele["jh_ouvrier"]))
        
        px_cond = st.number_input("Coût journalier Conducteur (€/jour) :", value=float(SALAIRES_DB.get("Conducteur", 230)))
        jh_cond = st.number_input("Total Jours-Homme Conducteur :", value=float(donnees_modele["jh_cond"]))
        
        st.caption("⚙️ Options intérimaires externes")
        px_interim = st.number_input("Coût journalier moyen d'un Intérimaire (€/jour) :", value=float(SALAIRES_DB.get("Intérim", 220)))
        jh_interim = st.number_input("Total Jours-Homme requis en Intérim :", value=0.0)

        total_salaires_direct = float((jh_chef * px_chef) + (jh_ouvrier * px_ouvrier) + (jh_cond * px_cond) + (jh_interim * px_interim))
        total_salaires_formatte = f"{total_salaires_direct:,.0f}".replace(",", " ")
        st.info(f"👥 **Total estimé salaires + intérim :** {total_salaires_formatte} €")

        st.markdown("### --- TABLE DES ENGINS NÉCESSAIRES ---")
        engins_bruts_modele = []
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            for item in donnees_modele["engins_requis"]:
                engins_bruts_modele.append({
                    "N° Étape": item.get("N° Étape", 1), "Durée Étape (jours)": item.get("Durée Étape (jours)", 1),
                    "Type d'engin requis": item.get("Type d'engin requis", "Pelleteuses"), "Niveau requis": item.get("Niveau requis", "N1"), "À louer ?": False
                })
        df_besoins_init = pd.DataFrame(engins_bruts_modele)
        if df_besoins_init.empty: df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        
        engins_necessaires = st.data_editor(
            df_besoins_init, num_rows="dynamic", use_container_width=True, key="table_engins_necessaires",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N° Étape", min_value=1, step=1, required=True),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée (jours)", min_value=1, step=1, required=True),
                "Type d'engin requis": st.column_config.SelectboxColumn("Type d'engin", options=TYPES_ENGINS_BRUTS, required=True),
                "Niveau requis": st.column_config.SelectboxColumn("Niveau requis", options=["N1", "N2", "N3", "N4"], required=True),
                "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False)
            }
        )

        # Logique de transfert universelle vers la table des engins à louer
        engins_transferes_list = []
        if not engins_necessaires.empty:
            df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
            for _, row in df_coches.iterrows():
                type_demande, niveau_demande, duree_etape = str(row["Type d'engin requis"]).strip(), str(row["Niveau requis"]).strip(), int(row["Durée Étape (jours)"])
                
                def nettoyer_mots(texte):
                    texte = texte.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                    for char in ["'", "-", "/", "’"]: texte = texte.replace(char, " ")
                    mots, mots_propres = texte.split(), []
                    mots_utiles = ["pour", "de", "d", "un", "une", "le", "la", "les", "sur"]
                    for m in mots:
                        if m in mots_utiles: continue
                        if m.endswith("s") and m not in ["tapis", "fraiseuse", "niveleuse", "sol"]: m = m[:-1]
                        mots_propres.append(m)
                    return mots_propres

                mots_cles_recherche = nettoyer_mots(type_demande)
                modele_trouve, prix_trouve = None, 380.0
                for engin_nom, prix in CATALOGUE_ENGINS.items():
                    if niveau_demande.lower() in engin_nom.lower() and all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                        modele_trouve, prix_trouve = engin_nom, prix
                        break
                if not modele_trouve:
                    for engin_nom, prix in CATALOGUE_ENGINS.items():
                        if all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                            modele_trouve, prix_trouve = engin_nom, prix
                            break
                if modele_trouve:
                    engins_transferes_list.append({"Sélection de l'engin / Modèle": modele_trouve, "Quantité": 1, "Prix Location (€/jour)": prix_trouve, "Jours de Location": duree_etape})

        st.markdown("### --- TABLE DES ENGINS À LOUER ---")
        df_engins_init = pd.DataFrame(columns=["Sélection de l'engin / Modèle", "Quantité", "Prix Location (€/jour)", "Jours de Location"])
        if len(engins_transferes_list) > 0: df_engins_init = pd.DataFrame(engins_transferes_list)
        
        engins_edites = st.data_editor(
            df_engins_init, num_rows="dynamic", use_container_width=True, key="table_engins_a_louer",
            column_config={
                "Sélection de l'engin / Modèle": st.column_config.SelectboxColumn("Engin & Modèle", options=list(CATALOGUE_ENGINS.keys()), required=True),
                "Quantité": st.column_config.NumberColumn("Quantité", min_value=1, default=1, step=1),
                "Prix Location (€/jour)": st.column_config.NumberColumn("Prix / Jour (€)", min_value=0, step=10),
                "Jours de Location": st.column_config.NumberColumn("Jours à louer", min_value=1, max_value=365, step=1)
            }
        )
        
        total_loc_engins_direct = 0.0
        if engins_edites is not None and not engins_edites.empty:
            df_propres_direct = engins_edites.dropna(subset=["Sélection de l'engin / Modèle"])
            df_propres_direct["Jours de Location"] = pd.to_numeric(df_propres_direct["Jours de Location"]).fillna(1).astype(int)
            total_loc_engins_direct = (df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * df_propres_direct["Jours de Location"]).sum()
            
        total_engins_formatte = f"{total_loc_engins_direct:,.0f}".replace(",", " ")
        st.info(f"💰 **Total des engins loués (Calcul personnalisé) :** {total_engins_formatte} €")

    # --- RECAPITULATIF FINANCIER GLOBAL ---
    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Global Estimé")

    total_mats_recap = float(total_mats_direct)
    total_location_recap = float(total_loc_engins_direct)
    total_salaires_recap = float(total_salaires_direct)
    total_depenses_recap = float(total_mats_recap + total_location_recap + total_salaires_recap)
    benefice_net_recap = float(revenus - total_depenses_recap)
    roi_recap = float((benefice_net_recap / total_depenses_recap) * 100 if total_depenses_recap > 0 else 0)
    
    gain_par_jour_recap = float(benefice_net_recap / jours_totaux if jours_totaux > 0 else 0.0)
    roi_par_jour_recap = float(roi_recap / jours_totaux if jours_totaux > 0 else roi_recap)

    txt_mats, txt_loc, txt_sal, txt_depenses, txt_gain_jour, txt_benefice = f"{total_mats_recap:,.0f}".replace(",", " "), f"{total_location_recap:,.0f}".replace(",", " "), f"{total_salaires_recap:,.0f}".replace(",", " "), f"{total_depenses_recap:,.0f}".replace(",", " "), f"{gain_par_jour_recap:,.0f}".replace(",", " "), f"{abs(benefice_net_recap):,.0f}".replace(",", " ")

    c_rc1, c_rc2, c_rc3, c_rc4, c_rc5, c_rc6 = st.columns(6)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires & Intérim", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")
    with c_rc5: st.metric(label="⏱️ Durée du Projet", value=f"{int(jours_totaux)} jours")
    with c_rc6: st.metric(label="📈 Rentabilité Quotidienne", value=f"{txt_gain_jour} €/j")

    mot_jour = "jours" if jours_totaux >= 2 else "jour"
    if benefice_net_recap >= 0: st.success(f"🟢 **Rentabilité positive :** Bénéfice de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** de **{int(jours_totaux)} {mot_jour}** de travail (ROI Global : **{roi_recap:.2f} %** | ROI / Jour : **{roi_par_jour_recap:.2f} %/j**)")
    else: st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** de **{int(jours_totaux)} {mot_jour}** de perte (ROI Global : **{roi_recap:.2f} %** | ROI / Jour : **{roi_par_jour_recap:.2f} %/j**)")

    st.markdown("<br>", unsafe_allow_html=True) 

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary"):
        df_actuel = charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier: st.error("Veuillez donner un nom ou un numéro valide.")
        elif doublon_existe: st.error(f"Impossible d'enregistrer : ce chantier existe déjà.")
        else:
            inserer_chantier(nom_chantier, revenus, total_mats_recap, total_location_recap, total_salaires_recap, total_depenses_recap, benefice_net_recap, round(roi_recap, 2), int(jours_totaux), round(gain_par_jour_recap, 2), round(roi_par_jour_recap, 2))
            st.toast("Chantier enregistré avec succès dans Firebase Firestore !")
            st.rerun()

# --- ONGLET 2 : HISTORIQUE ET CLASSEMENT ---
with onglet2:
    st.subheader("Base de données des chantiers enregistrés en temps réel")
    df_affichage = charger_donnees()
    
    if df_affichage.empty: 
        st.info("Aucun chantier n'a encore été enregistré dans Firebase.")
    else:
        critere_tri = st.selectbox("Classement initial par défaut :", ["Plus gros Bénéfice d'abord", "Plus gros ROI d'abord", "Plus de revenus d'abord"])
        if critere_tri == "Plus gros Bénéfice d'abord": 
            df_affichage = df_affichage.sort_values(by="Bénéfice Net (€)", ascending=False)
        elif critere_tri == "Plus gros ROI d'abord": 
            df_affichage = df_affichage.sort_values(by="ROI (%)", ascending=False)
        elif critere_tri == "Plus de revenus d'abord": 
            df_affichage = df_affichage.sort_values(by="Revenus (€)", ascending=False)
            
        moyenne_roi_jour = float(df_affichage["ROI / Jour (%)"].mean())
        df_visuel = df_affichage.copy()
        
        def calculer_comparaison(row):
            valeur_chantier = float(row["ROI / Jour (%)"])
            difference = valeur_chantier - moyenne_roi_jour
            return f"🟢 +{difference:.2f} %/j" if difference > 0 else (f"🔴 {difference:.2f} %/j" if difference < 0 else "⚪ Égal")

        df_visuel["Comparaison Moyenne Enterprise"] = df_visuel.apply(calculer_comparaison, axis=1)
        st.info(f"📊 **Moyenne de rentabilité journalière de l'entreprise :** {moyenne_roi_jour:.2f} %/j (Calculée sur {len(df_affichage)} chantier(s))")

        cols_ordre = ["Nom du Chantier", "Revenus (€)", "Durée (Jours)", "Coût Matériaux (€)", "Coût Location Engins (€)", "Coût Salaires (€)", "Dépenses Totales (€)", "Bénéfice Net (€)", "Gain / Jour (€)", "ROI (%)", "ROI / Jour (%)", "Comparaison Moyenne Enterprise"]
        df_visuel = df_visuel[[c for c in cols_ordre if c in df_visuel.columns]]

        st.dataframe(
            df_visuel, use_container_width=True,
            column_config={
                "Nom du Chantier": st.column_config.TextColumn("Nom du Chantier"), 
                "Revenus (€)": st.column_config.NumberColumn("Revenus (€)", format="%,d €"), 
                "Durée (Jours)": st.column_config.NumberColumn("Durée", format="%d j"),
                "Coût Matériaux (€)": st.column_config.NumberColumn("Matériaux", format="%,d €"), 
                "Coût Location Engins (€)": st.column_config.NumberColumn("Location Engins", format="%,d €"), 
                "Coût Salaires (€)": st.column_config.NumberColumn("Salaires + Intérim", format="%,d €"),
                "Dépenses Totales (€)": st.column_config.NumberColumn("Dépenses Totales", format="%,d €"), 
                "Bénéfice Net (€)": st.column_config.NumberColumn("Bénéfice Net (€)", format="%,d €"), 
                "Gain / Jour (€)": st.column_config.NumberColumn("Gain / Jour", format="%,d €/j"),
                "ROI (%)": st.column_config.NumberColumn("ROI (%)", format="%.2f %%"), 
                "ROI / Jour (%)": st.column_config.NumberColumn("ROI / Jour", format="%.2f %%/j"), 
                "Comparaison Moyenne Enterprise": st.column_config.TextColumn("Comparaison Moyenne")
            }
        )
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Télécharger la base de données cloud (CSV)", data=csv, file_name="base_donnies_chantiers.csv", mime="text/csv")
        st.markdown("---")
        if st.button("🗑️ Vider définitivement la base de données cloud FIREBASE", type="secondary"):
            reinitialiser_db()
            st.rerun()

# --- PANNEAU DE CONTRÔLE SUPRÊME (🔒 ESPACE DIRECTION) ---
with onglet3:
    st.subheader("🔑 Connexion Administrateur Direction")
    mot_de_passe = st.text_input("Veuillez saisir le code d'accès :", type="password")
    
    if mot_de_passe == "adminBTP2026":
        st.success("🔓 Accès accordé au panneau de contrôle.")
        
        df_stats = charger_donnees()
        if not df_stats.empty and "Revenus (€)" in df_stats.columns:
            st.markdown("### 🏢 Bilan Général de l'Entreprise (Consolidé Cloud)")
            total_chantiers = len(df_stats)
            somme_revenus = float(df_stats["Revenus (€)"].sum())
            somme_depenses = float(df_stats["Dépenses Totales (€)"].sum())
            somme_benefices = float(df_stats["Bénéfice Net (€)"].sum())
            
            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
            with c_st1: st.metric(label="💼 Chantiers Signés", value=f"{total_chantiers}")
            with c_st2: st.metric(label="💰 Chiffre d'Affaires Cumulé", value=f"{somme_revenus:,.0f}".replace(",", " ") + " €")
            with c_st3: st.metric(label="📉 Dépenses Totales", value=f"{somme_depenses:,.0f}".replace(",", " ") + " €")
            with c_st4: st.metric(label="📈 Résultat Net / Bénéfice", value=f"{somme_benefices:,.0f}".replace(",", " ") + " €")
            st.markdown("---")

        st.markdown("## ⚙️ Administration Suprême des Bases NoSQL")
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", 
            "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", 
            "🚜 Éditer Catalogue Engins",
            "🗂️ Consulter les Bases Données"
        ])
        
        # --- 4.1 INTERFACES D'IMPORTATION EN BLOC ---
        with sub_tab1:
            st.markdown("### 📥 Extracteur de Fiches Chantiers Multi-Étapes")
            texte_fiches_brutes = st.text_area(
                "Collez vos fiches de chantiers détaillées ici (Une ou plusieurs à la suite) :",
                value="", height=350, key="zone_texte_import_unique_fusionne"
            )
            
            if st.button("🏗️ ANALYSER, NETTOYER ET IMPORTER EN BLOC", type="primary"):
                if not texte_fiches_brutes.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    lignes = texte_fiches_brutes.split("\n")
                    chantiers_detectes = {}
                    nom_courant = None
                    
                    for ligne in lignes:
                        l_clean = ligne.strip()
                        if not l_clean: continue
                        
                        if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                            mots = l_clean.split()
                            mots_sans_euro = [m for m in mots if m.lower() not in ["euros", "euro", "€"]]
                            if len(mots_sans_euro) >= 2:
                                p1 = "".join(c for c in mots_sans_euro[-1] if c.isdigit())
                                p2 = "".join(c for c in mots_sans_euro[-2] if c.isdigit()) if len(mots_sans_euro) > 2 else ""
                                try:
                                    prix_ch = float(p2 + p1) if (p2 and p1 and len(p1) == 3) else float(p1)
                                    nom_ch = " ".join(mots_sans_euro[:-2]) if (p2 and p1 and len(p1) == 3) else " ".join(mots_sans_euro[:-1])
                                except ValueError:
                                    prix_ch = 0.0
                                    nom_ch = l_clean
                                
                                nom_courant = nom_ch.strip()
                                if nom_courant not in chantiers_detectes:
                                    chantiers_detectes[nom_courant] = {
                                        "revenus": prix_ch, "jours": 1, "nb_etapes": 1,
                                        "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
                                        "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
                                        "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []
                                    }
                            continue

                        if not nom_courant: continue
                            
                        if l_clean.lower().startswith("revenus"):
                            num_part = "".join(c for c in l_clean if c.isdigit())
                            if num_part: chantiers_detectes[nom_courant]["revenus"] = float(num_part)
                        if "nombre d'étapes" in l_clean.lower() or "nb ombre" in l_clean.lower():
                            partie_etape = l_clean.split(":")[-1] if ":" in l_clean else l_clean
                            num_etapes = "".join(c for c in partie_etape.split() if c.isdigit()) if partie_etape.split() else ""
                            if not num_etapes: num_etapes = "".join(c for c in partie_etape if c.isdigit())
                            if num_etapes: chantiers_detectes[nom_courant]["nb_etapes"] = int(num_etapes)
                                
                        if "durée du chantier" in l_clean.lower() or "duree du chantier" in l_clean.lower():
                            partie_droite = l_clean.split(":")[-1] if ":" in l_clean else l_clean
                            mots_jours = partie_droite.split()
                            num_jours = ""
                            for mj in mots_jours:
                                if any(c.isdigit() for c in mj):
                                    num_jours = "".join(c for c in mj if c.isdigit())
                                    break
                            if num_jours: chantiers_detectes[nom_courant]["jours"] = int(num_jours)
                                
                        if "surface du chantier" in l_clean.lower():
                            partie_mats = l_clean.split(":")[-1].lower() if ":" in l_clean else l_clean.lower()
                            mots_mats = partie_mats.split()
                            if mots_mats:
                                qte_txt = "".join(c for c in mots_mats if c.isdigit())
                                if not qte_txt: qte_txt = "".join(c for c in partie_mats if c.isdigit())
                                if qte_txt:
                                    qte_val = float(qte_txt)
                                    type_mat = " ".join(mots_mats[1:])
                                    if "tuyau" in type_mat or "km" in type_mat: chantiers_detectes[nom_courant]["tuyaux"] = qte_val
                                    elif "panneau" in type_mat: chantiers_detectes[nom_courant]["panneaux"] = qte_val
                                    elif "sable" in type_mat: chantiers_detectes[nom_courant]["sable"] = qte_val
                                    elif "terre" in type_mat: chantiers_detectes[nom_courant]["terre"] = qte_val
                                    elif "enrob" in type_mat: chantiers_detectes[nom_courant]["enrobe"] = qte_val
                                    elif "armat" in type_mat: chantiers_detectes[nom_courant]["armature"] = qte_val
                                    elif "tôle" in type_mat or "tole" in type_mat: chantiers_detectes[nom_courant]["tole"] = qte_val
                                    elif "béton" in type_mat or "beton" in type_mat: chantiers_detectes[nom_courant]["beton"] = qte_val
                                    elif "canal" in type_mat: chantiers_detectes[nom_courant]["canalisations"] = qte_val
                                    elif "poutre" in type_mat: chantiers_detectes[nom_courant]["poutres"] = qte_val

                    compteur_total = 0
                    for name, data in chantiers_detectes.items():
                        if data["jh_chef"] == 0 and data["jh_ouvrier"] == 0:
                            data["jh_chef"] = float(data["jours"])
                            data["jh_ouvrier"] = float(data["jours"] * 3)
                        
                        if not data["engins_requis"]:
                            for e_num in range(1, data["nb_etapes"] + 1):
                                data["engins_requis"].append({
                                    "N° Étape": e_num, "Durée Étape (jours)": max(1, int(data["jours"] / data["nb_etapes"])),
                                    "Type d'engin requis": "Pelleteuses" if e_num == 1 else "Camions Benne", "Niveau requis": "N2"
                                })
                        
                        db.collection("modeles_chantiers").document(name).set({
                            "nom_modele": name, "revenus": data["revenus"], "jours": data["jours"],
                            "sable": data["sable"], "terre": data["terre"], "enrobe": data["enrobe"], "armature": data["armature"], "tole": data["tole"],
                            "beton": data["beton"], "panneaux": data["panneaux"], "tuyaux": data["tuyaux"], "canalisations": data["canalisations"], "poutres": data["poutres"],
                            "jh_chef": data["jh_chef"], "jh_ouvrier": data["jh_ouvrier"], "jh_cond": data["jh_cond"], "engins_requis": data["engins_requis"]
                        })
                        compteur_total += 1
                        
                    if compteur_total > 0:
                        st.success(f"🟢 Traitement terminé ! {compteur_total} fiche(s) injectée(s) ! Rechargement...")
                        st.rerun()

        # --- 4.2 CONFIGURATION GRILLE SALARIALE ---
        with sub_tab2:
            st.write("Modifiez le coût d'une journée de travail.")
            salaires_edites = st.data_editor(pd.DataFrame(list(SALAIRES_DB.items()), columns=["poste", "tarif_jour"]), use_container_width=True, key="editeur_salaires_db", num_rows="fixed")
            if st.button("METTRE À JOUR LA GRILLE SALARIALE"):
                nouveau_dict = dict(zip(salaires_edites["poste"], salaires_edites["tarif_jour"].astype(float)))
                db.collection("configuration_salaires").document("grille").set(nouveau_dict)
                st.success("Grille salariale synchronisée sur Firebase !")
                st.rerun()

        # --- 4.3 CONFIGURATION DES MATÉRIAUX ---
        with sub_tab3:
            st.write("Ajustez le prix unitaire de vos matières premières.")
            mats_edites = st.data_editor(pd.DataFrame(list(MATERIAUX_DB.items()), columns=["materiau", "prix_unitaire"]), use_container_width=True, key="editeur_mats_db", num_rows="fixed")
            if st.button("METTRE À JOUR LE COÛT DES MATÉRIAUX"):
                nouveau_dict = dict(zip(mats_edites["materiau"], mats_edites["prix_unitaire"].astype(float)))
                db.collection("configuration_materiaux").document("catalogue").set(nouveau_dict)
                st.success("Tarifs matériaux actualisés sur Firebase !")
                st.rerun()

        # --- 4.4 CATALOGUE DE MACHINES ---
        with sub_tab4:
            st.write("Ajoutez ou modifiez vos engins lourds et leurs tarifs de location.")
            docs_engins = db.collection("catalogue_engins").stream()
            liste_engins = [{"nom_engin": d.id, "type_brut": d.to_dict().get("type_brut", ""), "prix_jour": d.to_dict().get("prix_jour", 0.0)} for d in docs_engins]
            df_engins = pd.DataFrame(liste_engins) if liste_engins else pd.DataFrame(columns=["nom_engin", "type_brut", "prix_jour"])
            
            engins_edites_db = st.data_editor(df_engins, use_container_width=True, key="editeur_engins_db", num_rows="dynamic")
            if st.button("METTRE À JOUR LE CATALOGUE DES ENGINS"):
                old_docs = db.collection("catalogue_engins").stream()
                for od in old_docs: od.reference.delete()
                
                for _, r in engins_edites_db.iterrows():
                    if pd.notnull(r["nom_engin"]) and str(r["nom_engin"]).strip():
                        db.collection("catalogue_engins").document(str(r["nom_engin"]).strip()).set({
                            "type_brut": str(r["type_brut"]), "prix_jour": float(r["prix_jour"])
                        })
                st.success("Parc d'engins synchronisé sur le Cloud !")
                st.rerun()

        # --- 4.5 VISUALISATION EN DIRECT DES TABLES ---
        with sub_tab5:
            st.markdown("### 🗂️ Consultation brute des documents enregistrés en base cloud")
            choix_table = st.selectbox(
                "Choisir la table à afficher :",
                ["Modèles de Chantiers Pré-configurés", "Grille Salariale Actuelle", "Prix des Matériaux de base", "Catalogue de Location des Engins"]
            )
            
            if choix_table == "Modèles de Chantiers Pré-configurés":
                docs = db.collection("modeles_chantiers").stream()
                res = [d.to_dict() for d in docs]
                if res:
                    df_t = pd.DataFrame(res)[["nom_modele", "revenus", "jours", "jh_chef", "jh_ouvrier", "jh_cond"]]
                    st.dataframe(df_t, use_container_width=True)
                else: st.info("Aucun modèle de chantier disponible.")
                
            elif choix_table == "Grille Salariale Actuelle":
                st.json(SALAIRES_DB)
                
            elif choix_table == "Prix des Matériaux de base":
                st.json(MATERIAUX_DB)
                
            elif choix_table == "Catalogue de Location des Engins":
                docs = db.collection("catalogue_engins").stream()
                res = [{"Engin Modèle": d.id, "Catégorie Technique": d.to_dict().get("type_brut"), "Prix de location (€/jour)": d.to_dict().get("prix_jour")} for d in docs]
                if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
                else: st.info("Le catalogue de machines est vide.")
                
    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect. Les privilèges d'administration restent verrouillés.")



