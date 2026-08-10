import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

DB_NAME = "chantiers.db"

# ==============================================================================
# --- 1. INITIALISATION DE LA BASE DE DONNÉES (STRUCTURE CENTRALE AUTOMATIQUE) ---
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table des chantiers réels enregistrés (Historique)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chantiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_chantier TEXT, revenus REAL, cout_materiaux REAL, cout_location REAL, 
            cout_salaires REAL, depenses_totales REAL, benefice_net REAL, roi REAL, 
            jours INTEGER, gain_par_jour REAL, roi_par_jour REAL
        )
    """)
    
    # Table d'administration 1 : Modèles de chantiers pré-configurés
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modeles_chantiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_modele TEXT UNIQUE, revenus REAL, jours INTEGER,
            sable REAL, terre REAL, enrobe REAL, armature REAL, tole REAL, beton REAL, panneaux REAL,
            tuyaux REAL, canalisations REAL, poutres REAL, jh_chef REAL, jh_ouvrier REAL, jh_cond REAL,
            engins_requis TEXT
        )
    """)
    
    # Table d'administration 2 : Grille tarifaire de la main d'œuvre et intérim
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuration_salaires (
            poste TEXT PRIMARY KEY, tarif_jour REAL
        )
    """)
    
    # Table d'administration 3 : Catalogue des prix des matériaux
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuration_materiaux (
            materiau TEXT PRIMARY KEY, prix_unitaire REAL
        )
    """)
    
    # Table d'administration 4 : Catalogue des engins et tarifs journaliers de location
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogue_engins (
            nom_engin TEXT PRIMARY KEY, type_brut TEXT, prix_jour REAL
        )
    """)
    
    # --- INJECTION DES DONNÉES DE BASE (SI LA BASE EST NEUVE OU VIDE) ---
    cursor.execute("SELECT COUNT(*) FROM configuration_salaires")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO configuration_salaires VALUES (?, ?)", [
            ("Chef", 230.0), ("Ouvrier", 230.0), ("Conducteur", 230.0), ("Intérim", 220.0)
        ])
        
    cursor.execute("SELECT COUNT(*) FROM configuration_materiaux")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO configuration_materiaux VALUES (?, ?)", [
            ("Sable", 12.0), ("Terre", 16.0), ("Enrobé", 42.0), ("Armature", 70.0), ("Tôle", 55.0),
            ("Béton", 45.0), ("Panneaux", 90.0), ("Tuyaux", 32.0), ("Canalisations", 35.0), ("Poutres", 70.0)
        ])
        
    cursor.execute("SELECT COUNT(*) FROM catalogue_engins")
    if cursor.fetchone()[0] == 0:
        engins_base = [
            ("Camion Benne N3 - Renault Trucks K 430 (430 cv)", "Camions Benne", 420.0),
            ("Pelleteuse N2 - Takeuchi TB2150 (85.0 kW)", "Pelleteuses", 200.0),
            ("Niveleuse N2 - CAT 14 (178 kW)", "Niveleuse", 580.0),
            ("Finisseur N3 - CAT AP600 (129 kW)", "Finisseur", 490.0),
            ("Compacteur Enrobé N3 - Dynapac CC4200 VI (100 kW)", "Compacteur pour enrobé", 340.0),
            ("Fraiseuse N2 - CAT PM312 (256 kW)", "Fraiseuse", 380.0)
        ]
        cursor.executemany("INSERT INTO catalogue_engins VALUES (?, ?, ?)", engins_base)
        
    cursor.execute("SELECT COUNT(*) FROM modeles_chantiers")
    if cursor.fetchone()[0] == 0:
        engins_demo = [
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Pelleteuses", "Niveau requis": "N2"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 1, "Durée Étape (jours)": 4, "Type d'engin requis": "Fraiseuse", "Niveau requis": "N2"},
            {"N° Étape": 2, "Durée Étape (jours)": 4, "Type d'engin requis": "Niveleuse", "Niveau requis": "N2"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Camions Benne", "Niveau requis": "N3"},
            {"N° Étape": 3, "Durée Étape (jours)": 4, "Type d'engin requis": "Finisseur", "Niveau requis": "N3"},
            {"N° Étape": 4, "Durée Étape (jours)": 4, "Type d'engin requis": "Compacteur pour enrobé", "Niveau requis": "N3"}
        ]
        cursor.execute("""
            INSERT INTO modeles_chantiers VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Goudronnage d'une route (Grande surface) (214 599 €)", 214599, 16, 488, 0, 618, 0, 0, 0, 6, 0, 0, 0, 16, 48, 28, json.dumps(engins_demo)))

    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# --- 2. FONCTIONS DE CHARGEMENT DYNAMIQUE DEPUIS SQLITE ---
# ==============================================================================
def charger_salaires_config():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM configuration_salaires", conn)
    conn.close()
    return dict(zip(df["poste"], df["tarif_jour"]))

def charger_materiaux_config():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM configuration_materiaux", conn)
    conn.close()
    return dict(zip(df["materiau"], df["prix_unitaire"]))

def charger_catalogue_engins():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT nom_engin, prix_jour FROM catalogue_engins", conn)
    conn.close()
    return dict(zip(df["nom_engin"], df["prix_jour"]))

def charger_types_engins_bruts():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT DISTINCT type_brut FROM catalogue_engins", conn)
    conn.close()
    return sorted(df["type_brut"].tolist())

def charger_catalogue_chantiers():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM modeles_chantiers", conn)
    conn.close()
    
    catalogue = {"Choisir un chantier pré-configuré...": {
        "revenus": 0.0, "jours": 0, "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
        "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
        "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []
    }}
    
    for _, r in df.iterrows():
        catalogue[r["nom_modele"]] = {
            "revenus": r["revenus"], "jours": r["jours"], "sable": r["sable"], "terre": r["terre"],
            "enrobe": r["enrobe"], "armature": r["armature"], "tole": r["tole"], "beton": r["beton"],
            "panneaux": r["panneaux"], "tuyaux": r["tuyaux"], "canalisations": r["canalisations"], "poutres": r["poutres"],
            "jh_chef": r["jh_chef"], "jh_ouvrier": r["jh_ouvrier"], "jh_cond": r["jh_cond"],
            "engins_requis": json.loads(r["engins_requis"]) if r["engins_requis"] else []
        }
    return catalogue

def charger_donnees():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT nom_chantier AS 'Nom du Chantier', revenus AS 'Revenus (€)', jours AS 'Durée (Jours)',
               cout_materiaux AS 'Coût Matériaux (€)', cout_location AS 'Coût Location Engins (€)', 
               cout_salaires AS 'Coût Salaires + Intérim (€)', depenses_totales AS 'Dépenses Totales (€)', 
               benefice_net AS 'Bénéfice Net (€)', gain_par_jour AS 'Gain / Jour (€)', roi AS 'ROI (%)', roi_par_jour AS 'ROI / Jour (%)'
        FROM chantiers
    """, conn)
    conn.close()
    return df

def inserer_chantier(nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chantiers (nom_chantier, revenus, cout_materiaux, cout_location, cout_salaires, depenses_totales, benefice_net, roi, jours, gain_par_jour, roi_par_jour)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nom, rev, mats, loc, sal, total, net, roi, jours, gpj, rpj))
    conn.commit()
    conn.close()

def reinitialiser_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS chantiers")
    conn.commit()
    conn.close()
    init_db()

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

# --- ONGLET 1 : FORMULAIRE DE SAISIE PRINCIPAL SANS CODE EN DUR ---
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
            # Branchement dynamique des prix unitaires sur les configurations de la base administrable
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

        # Calcul instantané du coût de revient des fournitures avec espacement des milliers
        total_mats_direct = float((qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_eaux_usees*prix_eaux_usees) + (qte_poutres*prix_poutres))
        total_mats_formatte = f"{total_mats_direct:,.0f}".replace(",", " ")
        st.info(f"🧱 **Total estimé des matériaux :** {total_mats_formatte} €")
    with col2:
        st.markdown("### --- GRILLE SALARIALE & INTERIM ---")
        # Branchement des taux journaliers en direct sur les paramètres administrés en base
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

        # Logique de transfert universelle
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
            st.toast("Chantier enregistré avec succès dans la base SQLite !")
            st.rerun()

# --- ONGLET 2 : HISTORIQUE ET CLASSEMENT ---
with onglet2:
    st.subheader("Base de données des chantiers enregistrés")
    df_affichage = charger_donnees()
    
    if df_affichage.empty: 
        st.info("Aucun chantier n'a encore été enregistré.")
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
        st.download_button(label="📥 Télécharger la base de données (CSV)", data=csv, file_name="base_donnies_chantiers.csv", mime="text/csv")
        st.markdown("---")
        if st.button("🗑️ Vider définitivement la base de données SQLITE", type="secondary"):
            reinitialiser_db()
            st.rerun()

# --- PANNEAU D'ADMINISTRATION CENTRAL ET SUPRÊME ---
with onglet3:
    st.subheader("🔑 Connexion Administrateur Direction")
    mot_de_passe = st.text_input("Veuillez saisir le code d'accès :", type="password")
    
    if mot_de_passe == "adminBTP2026":
        st.success("🔓 Accès accordé au panneau de contrôle.")
        
        df_stats = charger_donnees()
        if not df_stats.empty:
            st.markdown("### 🏢 Bilan Général de l'Entreprise")
            total_chantiers = len(df_stats)
            somme_revenus = float(df_stats["Revenus (€)"].sum())
            somme_depenses = float(df_stats["Dépenses Totales (€)"].sum())
            somme_benefices = float(df_stats["Bénéfice Net (€)"].sum())
            
            txt_total_rev = f"{somme_revenus:,.0f}".replace(",", " ")
            txt_total_dep = f"{somme_depenses:,.0f}".replace(",", " ")
            txt_total_ben = f"{somme_benefices:,.0f}".replace(",", " ")
            
            roi_global_entreprise = (somme_benefices / somme_depenses) * 100 if somme_depenses > 0 else 0
            
            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
            with c_st1: st.metric(label="💼 Chantiers Signés", value=f"{total_chantiers}")
            with c_st2: st.metric(label="💰 Chiffre d'Affaires Cumulé", value=f"{txt_total_rev} €")
            with c_st3: st.metric(label="📉 Dépenses Totales", value=f"{txt_total_dep} €")
            with c_st4: st.metric(label="📈 Résultat Net / Bénéfice", value=f"{txt_total_ben} €")
            st.markdown("---")

        st.markdown("## ⚙️ Administration Suprême des Bases")
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "🏗️ Ajouter un Modèle de Chantier", "👥 Éditer Grille Salariale", "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins"
        ])
        
        with sub_tab1:
            st.write("Créez ici un chantier type. Il apparaîtra instantanément dans le menu déroulant de l'Onglet 1.")
            with st.form("form_nouveau_modele", clear_on_submit=True):
                m_nom = st.text_input("Nom unique du modèle de chantier :", placeholder="ex: Parking public")
                m_rev = st.number_input("Revenus par défaut (€) :", min_value=0.0, value=50000.0)
                m_j = st.number_input("Durée totale par défaut (jours) :", min_value=1, value=10)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.write("**Quantités Matériaux de base :**")
                    m_sable = st.number_input("T. Sable :", value=0.0)
                    m_terre = st.number_input("T. Terre :", value=0.0)
                    m_enrobe = st.number_input("T. Enrobé :", value=0.0)
                    m_armature = st.number_input("U. Armature :", value=0.0)
                    m_tole = st.number_input("U. Tôle :", value=0.0)
                    m_beton = st.number_input("T. Béton :", value=0.0)
                    m_panneaux = st.number_input("U. Panneaux :", value=0.0)
                    m_tuyaux = st.number_input("U. Tuyaux :", value=0.0)
                    m_canal = st.number_input("U. Canalisations :", value=0.0)
                    m_poutres = st.number_input("U. Poutres :", value=0.0)
                with col_m2:
                    st.write("**Besoins en Équipes (Jours-Homme) :**")
                    m_chef = st.number_input("JH Chef :", value=0.0)
                    m_ouvrier = st.number_input("JH Ouvrier :", value=0.0)
                    m_cond = st.number_input("JH Conducteur :", value=0.0)
                    
                m_engins_json = st.text_area("Étapes d'Engins requis (JSON) :", value="[]")
                
                if st.form_submit_button("SAUVEGARDER LE MODÈLE"):
                    if not m_nom:
                        st.error("Donnez un nom au modèle.")
                    else:
                        try:
                            json.loads(m_engins_json)
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT OR REPLACE INTO modeles_chantiers VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (m_nom, m_rev, m_j, m_sable, m_terre, m_enrobe, m_armature, m_tole, m_beton, m_panneaux, m_tuyaux, m_canal, m_poutres, m_chef, m_ouvrier, m_cond, m_engins_json))
                            conn.commit()
                            conn.close()
                            st.success(f"Modèle '{m_nom}' ajouté ! Rafraîchissement...")
                            st.rerun()
                        except ValueError:
                            st.error("Le format des étapes JSON est invalide.")

        with sub_tab2:
            st.write("Modifiez le coût d'une journée de travail.")
            conn = sqlite3.connect(DB_NAME)
            df_salaires = pd.read_sql_query("SELECT * FROM configuration_salaires", conn)
            conn.close()
            salaires_edites = st.data_editor(df_salaires, use_container_width=True, key="editeur_salaires_db", num_rows="fixed")
            if st.button("METTRE À JOUR LA GRILLE SALARIALE"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for _, r in salaires_edites.iterrows():
                    cursor.execute("UPDATE configuration_salaires SET tarif_jour = ? WHERE poste = ?", (float(r["tarif_jour"]), str(r["poste"])))
                conn.commit()
                conn.close()
                st.success("Grille salariale enregistrée !")
                st.rerun()

        with sub_tab3:
            st.write("Ajustez le prix unitaire de vos matières premières.")
            conn = sqlite3.connect(DB_NAME)
            df_mats = pd.read_sql_query("SELECT * FROM configuration_materiaux", conn)
            conn.close()
            mats_edites = st.data_editor(df_mats, use_container_width=True, key="editeur_mats_db", num_rows="fixed")
            if st.button("METTRE À JOUR LE COÛT DES MATÉRIAUX"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                for _, r in mats_edites.iterrows():
                    cursor.execute("UPDATE configuration_materiaux SET prix_unitaire = ? WHERE materiau = ?", (float(r["prix_unitaire"]), str(r["materiau"])))
                conn.commit()
                conn.close()
                st.success("Catalogue des tarifs matériaux actualisé !")
                st.rerun()

        with sub_tab4:
            st.write("Ajoutez ou modifiez vos engins lourds et leurs tarifs de location.")
            conn = sqlite3.connect(DB_NAME)
            df_engins = pd.read_sql_query("SELECT * FROM catalogue_engins", conn)
            conn.close()
            engins_edites_db = st.data_editor(df_engins, use_container_width=True, key="editeur_engins_db", num_rows="dynamic")
            if st.button("METTRE À JOUR LE CATALOGUE DES ENGINS"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM catalogue_engins")
                for _, r in engins_edites_db.iterrows():
                    if pd.notnull(r["nom_engin"]):
                        cursor.execute("INSERT INTO catalogue_engins VALUES (?, ?, ?)", (str(r["nom_engin"]), str(r["type_brut"]), float(r["prix_jour"])))
                conn.commit()
                conn.close()
                st.success("Parc d'engins synchronisé !")
                st.rerun()
                
    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect. Les données financières consolidées restent verrouillées.")
