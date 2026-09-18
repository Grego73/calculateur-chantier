# Fichier complet et certifié fonctionnel : onglets/ajouter_chantier.py

import streamlit as st
import pandas as pd
import math
import database as db

# ==============================================================================
# --- 1. POPUP DE CONFIRMATION AVEC EXPORT EXCEL ---
# ==============================================================================
@st.dialog("🔍 Rapport de Calcul et Feuille d'Insertion NoSQL")
def popup_confirmation_enregistrement():
    inputs = st.session_state.get("temp_submit_data", {})
    if not inputs:
        st.error("Aucune donnée de simulation trouvée.")
        return

    st.write("Voici la transparence complète des calculs et formules appliqués selon les règles de l'économie du jeu :")
    
    st.markdown("#### ⏱️ 1. Décomposition du Temps Réel")
    st.write(f"- **Durée du contrat (En-tête) :** `{inputs['txt_duree_indic']}`")
    st.write(f"- **Durée réelle (Cumul étapes) :** `{inputs['txt_duree_etapes']}`")

    st.markdown("#### 👥 2. Formules appliquées pour la Main-d'œuvre")
    st.code(f"Conducteurs ({inputs['type_contrat_cond']}) : {inputs['cout_cond']:,.0f} €")
    st.code(f"Chefs ({inputs['type_contrat_chef']}) : {inputs['cout_chefs']:,.0f} €")
    st.code(f"Ouvriers ({inputs['type_contrat_ouv']}) : {inputs['cout_ouvriers']:,.0f} €")

    st.markdown("#### 🗂️ 3. Structure finale NoSQL (Firebase)")
    
    txt_benefice_net = f"{inputs['benefice_net_recap']:,.0f}".replace(",", " ") + " €"
    txt_roi_global = f"{inputs['roi_recap']:.2f} %"
    txt_roi_jour = f"{inputs['roi_par_jour_recap']:.2f} %/j"
    
    donnees_popup = {
        "Champ technique (Firestore)": [
            "nom_chantier", "revenus", "cout_materiaux", "cout_location", 
            "cout_salaires", "depenses_totales", "benefice_net", "roi", "roi_par_jour", "gain_par_jour"
        ],
        "Valeur brute insérée en base": [
            inputs['nom_chantier'], 
            f"{inputs['revenus']:,.0f} €".replace(",", " "), 
            f"{inputs['txt_mats']} €", 
            f"{inputs['txt_loc']} €", 
            f"{inputs['txt_sal']} €", 
            f"{inputs['txt_depenses']} €", 
            txt_benefice_net,
            txt_roi_global,
            txt_roi_jour,
            f"{inputs['txt_gain_jour']} €/j"
        ]
    }
    df_popup = pd.DataFrame(donnees_popup)
    st.table(df_popup)
    
    try:
        df_excel = pd.DataFrame({
            "Indicateur Financier": [
                "Nom du Chantier", "Chiffre d'Affaires Prévu", "Coût Estimé Matériaux", 
                "Coût Location Engins", "Masse Salariale Totale", "Dépenses Globales Consolidées", 
                "Bénéfice Net Estimé", "ROI Global", "ROI / Jour", "Rentabilité Quotidienne (€/j)"
            ],
            "Valeur": [
                inputs['nom_chantier'], inputs['revenus'], inputs['total_mats_recap'],
                inputs['total_location_recap'], inputs['total_salaires_recap'], inputs['total_depenses_recap'],
                inputs['benefice_net_recap'], txt_roi_global, txt_roi_jour, inputs['gain_par_jour_recap']
            ]
        })
        
        import io
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name="Bilan Chantier")
        data_excel_bytes = buffer_excel.getvalue()
        
        st.download_button(
            label="📥 TÉLÉCHARGER LA FICHE COMPTABLE (EXCEL)",
            data=data_excel_bytes,
            file_name=f"fiche_rentabilite_{inputs['nom_chantier'].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    except Exception as e:
        st.caption(f"ℹ️ Optionnel : Échec du compilateur Excel ({e})")
        
    st.warning("🚨 Confirmez-vous l'envoi de cette simulation vers l'Historique cloud de l'entreprise ?")
    col_pop1, col_pop2 = st.columns(2)
    
    with col_pop1:
        if st.button("✅ ACCEPTER & CONFIGURER EN BASE", type="primary", width="stretch"):
            db.inserer_chantier(
                inputs['nom_chantier'], inputs['revenus'], inputs['total_mats_recap'], 
                inputs['total_location_recap'], inputs['total_salaires_recap'], 
                inputs['total_depenses_recap'], inputs['benefice_net_recap'], 
                round(inputs['roi_recap'], 2), float(inputs['jours_totaux']), 
                round(inputs['gain_par_jour_recap'], 2), round(inputs['roi_par_jour_recap'], 2)
            )
            
            db.enregistrer_log(
                type_action="CHANTIER",
                details=f"Création et insertion du chantier cloud [{inputs['nom_chantier']}] pour un CA de {inputs['revenus']} €."
            )
            
            st.session_state["activer_popup_confirmation"] = False
            if "temp_submit_data" in st.session_state:
                del st.session_state["temp_submit_data"]
            st.toast("🚀 Simulation enregistrée avec succès sur le Cloud Firestore !")
            st.rerun()
            
    with col_pop2:
        if st.button("❌ ANNULER & MODIFIER", width="stretch"): 
            st.session_state["activer_popup_confirmation"] = False
            if "temp_submit_data" in st.session_state:
                del st.session_state["temp_submit_data"]
            st.rerun()

# ==============================================================================
# --- 2. EN-TÊTE PRINCIPAL DE SAISIE ---
# ==============================================================================
def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
    st.subheader("Formulaire de saisie")
    
    liste_triee = ["Choisir un chantier pré-configuré..."] + sorted([k for k in CATALOGUE_CHANTIERS.keys() if k != "Choisir un chantier pré-configuré..."])
    
    if "val_revenus" not in st.session_state:
        st.session_state["val_revenus"] = 0.0
        st.session_state["val_jours"] = 0
        st.session_state["val_heures"] = 0
        st.session_state["val_minutes"] = 0
        for k in ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]:
            st.session_state[f"val_{k}"] = 0.0
            
    if "compteur_refresh_engins" not in st.session_state:
        st.session_state["compteur_refresh_engins"] = 0

    def mise_a_jour_cache_modele():
        selection = st.session_state["select_modele_chantier_dynamique"]
        st.session_state["compteur_refresh_engins"] += 1
        
        for key in list(st.session_state.keys()):
            if "editor_rh_data" in key or "editor_engins_data" in key:
                del st.session_state[key]

        if selection == "Choisir un chantier pré-configuré...":
            st.session_state["val_revenus"] = 0.0
            st.session_state["val_jours"] = 0
            st.session_state["val_heures"] = 0
            st.session_state["val_minutes"] = 0
            for mat in ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]:
                st.session_state[f"val_{mat}"] = 0.0
            st.session_state["cache_df_rh"] = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "🕹️ Conducteurs", "🧑‍💼 Chefs", "👷 Ouvriers"])
            st.session_state["cache_df_engins"] = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
            return
            
        modele = CATALOGUE_CHANTIERS[selection]
        etapes_cloud = modele.get("etapes_techniques", [])
            
        st.session_state["val_revenus"] = float(modele.get("revenus", 0.0))
        st.session_state["val_jours"] = int(modele.get("jours_globaux", 0))
        st.session_state["val_heures"] = int(modele.get("heures_globales", 0))
        st.session_state["val_minutes"] = int(modele.get("minutes_globales", 0))
        
        liste_mats_cles = ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]
        for mat in liste_mats_cles:
            st.session_state[f"val_{mat}"] = 0.0
            
        lignes_rh = []
        lignes_engins = []
        
        for etape in etapes_cloud:
            num_e = etape.get("num_etape", 1)
            duree_j = etape.get("duree_jours", 1)
            
            mats_qp = etape.get("materiaux", {})
            for mat_nom, qte in mats_qp.items():
                if mat_nom in liste_mats_cles:
                    st.session_state[f"val_{mat_nom}"] += float(qte)
                    
            lignes_rh.append({
                "N° Étape": int(num_e), "Durée Étape (jours)": int(duree_j),
                "🕹️ Conducteurs": int(etape.get("jh_cond", 0)), "🧑‍💼 Chefs": int(etape.get("jh_chef", 0)), "👷 Ouvriers": int(etape.get("jh_ouvrier", 0))
            })
            
            engins_etape = etape.get("engins", [])
            for engine in engins_etape:
                lignes_engins.append({
                    "N° Étape": int(num_e), "Durée Étape (jours)": int(duree_j),
                    "Type d'engin requis": engine.get("type", "Autre"), "Niveau requis": engine.get("niveau", "N1"), "À louer ?": False
                })
                
        st.session_state["cache_df_rh"] = pd.DataFrame(lignes_rh)
        df_engins_brut = pd.DataFrame(lignes_engins)
        if not df_engins_brut.empty:
            st.session_state["cache_df_engins"] = df_engins_brut.drop_duplicates(
                subset=["N° Étape", "Type d'engin requis", "Niveau requis"], keep="first"
            ).reset_index(drop=True)
        else:
            st.session_state["cache_df_engins"] = df_engins_brut
            
    idx_refresh = st.session_state["compteur_refresh_engins"]

    chantier_selectionne = st.selectbox(
        "🚀 Sélectionner un modèle de chantier dynamique :", 
        liste_triee, key="select_modele_chantier_dynamique", on_change=mise_a_jour_cache_modele
    )
    
    valeur_nom_defaut = "" if chantier_selectionne == "Choisir un chantier pré-configuré..." else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=st.session_state["val_revenus"], step=100.0, format="%.0f")
        
        st.write("⏱️ **Durée globale de l'en-tête du chantier (Sim-TP) :**")
        c_j, c_h, c_m = st.columns(3)
        with c_j: jours_saisis = st.number_input("Jours", min_value=0, value=st.session_state["val_jours"], step=1)
        with c_h: heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=st.session_state["val_heures"], step=1)
        with c_m: minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=st.session_state["val_minutes"], step=1)

        heures_en_jours = heures_saisies / 24.0
        minutes_en_jours = minutes_saisies / 1440.0
        jours_totaux_indicatif = float(jours_saisis + heures_en_jours + minutes_en_jours)

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=st.session_state["val_sable"], format="%.0f")
            qte_terre = st.number_input("Tonnes de Terre :", value=st.session_state["val_terre"], format="%.0f")
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=st.session_state["val_enrobe"], format="%.0f")
            qte_armature = st.number_input("Unités d'Armature métallique :", value=st.session_state["val_armature"], format="%.0f")
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=st.session_state["val_tole"], format="%.0f")
            qte_beton = st.number_input("Tonnes de Béton :", value=st.session_state["val_beton"], format="%.0f")
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=st.session_state["val_panneaux"], format="%.0f")
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=st.session_state["val_tuyaux"], format="%.0f")
            qte_canalisations = st.number_input("Unités de Canalisations eaux usées :", value=st.session_state["val_canalisations"], format="%.0f")
            qte_poutres = st.number_input("Unités de Poutres en acier :", value=st.session_state["val_poutres"], format="%.0f")
        with c_px:
            prix_sable = st.number_input("Prix Sable (€/t) :", value=float(MATERIAUX_DB.get("Sable", 12)), format="%.0f")
            prix_terre = st.number_input("Prix Terre (€/t) :", value=float(MATERIAUX_DB.get("Terre", 16)), format="%.0f")
            prix_enrobe = st.number_input("Prix Enrobé (€/t) :", value=float(MATERIAUX_DB.get("Enrobé", 42)), format="%.0f")
            prix_armature = st.number_input("Prix Armature (€/u) :", value=float(MATERIAUX_DB.get("Armature", 70)), format="%.0f")
            prix_tole = st.number_input("Prix Tôle (€/u) :", value=float(MATERIAUX_DB.get("Tôle", 55)), format="%.0f")
            prix_beton = st.number_input("Prix Béton (€/t) :", value=float(MATERIAUX_DB.get("Béton", 45)), format="%.0f")
            prix_panneaux = st.number_input("Prix Panneaux (€/u) :", value=float(MATERIAUX_DB.get("Panneaux", 90)), format="%.0f")
            prix_tuyaux = st.number_input("Prix Tuyaux d'eau (€/u) :", value=float(MATERIAUX_DB.get("Tuyaux", 32)), format="%.0f")
            prix_canalisations = st.number_input("Prix Canalisations (€/u) :", value=float(MATERIAUX_DB.get("Canalisations", 35)), format="%.0f")
            prix_poutres = st.number_input("Prix Poutres acier (€/u) :", value=float(MATERIAUX_DB.get("Poutres", 70)), format="%.0f")

        total_mats_direct = float((qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_canalisations*prix_canalisations) + (qte_poutres*prix_poutres))
        st.info(f"🧱 **Total est. matériaux :** {total_mats_direct:,.0f}".replace(",", " ") + " €")

    with col2:
        st.markdown("### --- CONFIGURATION DES RESSOURCES D'ÉTAPE ---")
        
        c_rh_co, c_rh_ch, c_rh_ou = st.columns(3)
        with c_rh_co: type_contrat_cond = st.selectbox("Contrat Conducteurs :", ["CDI", "CDD"], key="type_contrat_cond")
        with c_rh_ch: type_contrat_chef = st.selectbox("Contrat Chefs :", ["CDI", "CDD"], key="type_contrat_chef")
        with c_rh_ou: type_contrat_ouv = st.selectbox("Contrat Ouvriers :", ["CDI", "CDD"], key="type_contrat_ouv")
        
        px_cond = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Moyen") or SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}") or SALAIRES_DB.get("Conducteur") or 230.0)
        px_chef = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Moyen") or SALAIRES_DB.get(f"Chef_{type_contrat_chef}") or SALAIRES_DB.get("Chef") or 230.0)
        px_ouvrier = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Moyen") or SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}") or SALAIRES_DB.get("Ouvrier") or 230.0)

        st.info(f"💰 Tarifs : 🕹️ Cond : {px_cond:.0f}€/j | 🧑‍💼 Chef : {px_chef:.0f}€/j | 👷 Ouv : {px_ouvrier:.0f}€/j")

        st.markdown("**👥 Planification de la Durée Réelle (Par Étape) :**")
        df_rh_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "🕹️ Conducteurs", "🧑‍💼 Chefs", "👷 Ouvriers"])
        raw_rh_state = st.session_state.get("cache_df_rh", df_rh_init)

        tableau_employes_etapes = st.data_editor(
            raw_rh_state, num_rows="dynamic", width="stretch", key=f"editor_rh_data_{idx_refresh}",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée Réelle (j)", min_value=1, step=1, required=True, width="small"),
                "🕹️ Conducteurs": st.column_config.NumberColumn(f"Cond ({px_cond:.0f}€)", min_value=0, step=1, default=1, width="small"),
                "🧑‍💼 Chefs": st.column_config.NumberColumn(f"Chef ({px_chef:.0f}€)", min_value=0, step=1, default=0, width="small"),
                "👷 Ouvriers": st.column_config.NumberColumn(f"Ouv ({px_ouvrier:.0f}€)", min_value=0, step=1, default=0, width="small")
            }
        )

        st.markdown("### --- FLOTTE D'ENGINS PAR ÉTAPE ---")
        df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        raw_engins_state = st.session_state.get("cache_df_engins", df_besoins_init)

        engins_necessaires = st.data_editor(
            raw_engins_state, num_rows="dynamic", width="stretch", key=f"editor_engins_data_{idx_refresh}", 
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée Réelle (j)", min_value=1, step=1, required=True, disabled=True),
                "Type d'engin requis": st.column_config.TextColumn("Type d'engin requis", disabled=False),
                "Niveau requis": st.column_config.SelectboxColumn("Niveau requis", options=["N1", "N2", "N3", "N4"], required=True),
                "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False)
            }
        )

        engins_transferes_list = []
        if engins_necessaires is not None and not engins_necessaires.empty and "À louer ?" in engins_necessaires.columns:
            df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
            for _, row in df_coches.iterrows():
                type_demande = str(row["Type d'engin requis"]).strip()
                level_demande = str(row["Niveau requis"]).strip().lower()
                duree_etape_eng = float(row["Durée Étape (jours)"])
                
                def nettoyer_mots(texte):
                    texte = texte.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                    for char in ["'", "-", "/", "’"]: texte = texte.replace(char, " ")
                    return [m for m in texte.split() if m not in ["pour", "de", "d", "un", "une", "le", "la", "les", "sur"]]

                mots_cles_recherche = nettoyer_mots(type_demande)
                modele_trouve, prix_trouve = None, 380.0
                for engin_nom, prix in CATALOGUE_ENGINS.items():
                    if level_demande in engin_nom.lower() and all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                        modele_trouve, prix_trouve = engin_nom, prix
                        break
                if not modele_trouve:
                    for engin_nom, prix in CATALOGUE_ENGINS.items():
                        if all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                            modele_trouve, prix_trouve = engin_nom, prix
                            break
                if not modele_trouve:
                    modele_trouve = f"{type_demande} ({level_demande.upper()})"
                    prix_trouve = 380.0
                    
                engins_transferes_list.append({
                    "engin_modele": modele_trouve, 
                    "Quantité": 1, 
                    "Prix Location (€/jour)": prix_trouve, 
                    "Jours de Location (Réels)": duree_etape_eng
                })
                
        st.markdown("### --- RELEVÉ LOGISTIQUE DES ENGINS À LOUER ---")
        df_engins_init = pd.DataFrame(columns=["engin_modele", "Quantité", "Prix Location (€/jour)", "Jours de Location (Réels)"])
        if len(engins_transferes_list) > 0: 
            df_engins_init = pd.DataFrame(engins_transferes_list)
        
        engins_edites = st.data_editor(
            df_engins_init, num_rows="dynamic", width="stretch", key=f"table_engins_a_louer_{idx_refresh}",
            column_config={
                "engin_modele": st.column_config.TextColumn("Engin & Modèle", disabled=True),
                "Quantité": st.column_config.NumberColumn("Quantité", min_value=1, default=1, step=1),
                "Prix Location (€/jour)": st.column_config.NumberColumn("Prix/j", min_value=0, step=10),
                "Jours de Location (Réels)": st.column_config.NumberColumn("Durée Réelle (j)", format="%.2f j", disabled=True)
            }
        )

    # ==============================================================================
    # --- 3. CONSOLIDATION FINANCIÈRE PAR ÉTAPE (TOUTE JOURNÉE ENTAMÉE EST DUE) ---
    # ==============================================================================
    total_mats_recap = float(total_mats_direct)
    total_location_recap = 0.0
    cout_cond, cout_chefs, cout_ouvriers = 0.0, 0.0, 0.0
    jours_totaux_calcul_etapes = 0.0

    if tableau_employes_etapes is not None and not tableau_employes_etapes.empty:
        df_rh_propre = tableau_employes_etapes.dropna(subset=["N° Étape"])
        jours_totaux_calcul_etapes = float(df_rh_propre["Durée Étape (jours)"].sum())
        
        for _, r_rh in df_rh_propre.iterrows():
            duree_etape_reelle = float(r_rh.get("Durée Étape (jours)", 1.0))
            duree_etape_forfait = float(math.ceil(duree_etape_reelle))
            
            c_count = float(r_rh.get("🕹️ Conducteurs", 0))
            ch_count = float(r_rh.get("🧑‍💼 Chefs", 0))
            o_count = float(r_rh.get("👷 Ouvriers", 0))
            
            d_cond = duree_etape_reelle if type_contrat_cond == "CDI" else duree_etape_forfait
            d_chef = duree_etape_reelle if type_contrat_chef == "CDI" else duree_etape_forfait
            d_ouv  = duree_etape_reelle if type_contrat_ouv  == "CDI" else duree_etape_forfait
            
            cout_cond += c_count * d_cond * px_cond
            cout_chefs += ch_count * d_chef * px_chef
            cout_ouvriers += o_count * d_ouv * px_ouvrier

    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["engin_modele"])
        for _, r_eng in df_propres_direct.iterrows():
            qte_eng = float(r_eng.get("Quantité", 1))
            px_loc_j = float(r_eng.get("Prix Location (€/jour)", 380.0))
            jours_reels_eng = float(r_eng.get("Jours de Location (Réels)", 1.0))
            
            total_location_recap += qte_eng * px_loc_j * float(math.ceil(jours_reels_eng))

    jours_totaux = jours_totaux_calcul_etapes if jours_totaux_calcul_etapes > 0 else jours_totaux_indicatif

    total_salaires_recap = float(cout_chefs + cout_ouvriers + cout_cond)
    total_depenses_recap = float(total_mats_recap + total_location_recap + total_salaires_recap)
    benefice_net_recap = float(revenus - total_depenses_recap)
    roi_recap = float((benefice_net_recap / total_depenses_recap) * 100 if total_depenses_recap > 0 else 0)
    
    gain_par_jour_recap = float(benefice_net_recap / jours_totaux if jours_totaux > 0 else 0.0)
    roi_par_jour_recap = float(roi_recap / jours_totaux if jours_totaux > 0 else roi_recap)

    txt_mats = f"{total_mats_recap:,.0f}".replace(",", " ")
    txt_loc = f"{total_location_recap:,.0f}".replace(",", " ")
    txt_sal = f"{total_salaires_recap:,.0f}".replace(",", " ")
    txt_depenses = f"{total_depenses_recap:,.0f}".replace(",", " ")
    txt_gain_jour = f"{gain_par_jour_recap:,.0f}".replace(",", " ")
    txt_benefice = f"{benefice_net_recap:,.0f}".replace(",", " ")
    
    jours_e_entiers = int(jours_totaux)
    heures_e_restantes = int(round((jours_totaux - jours_e_entiers) * 24))
    txt_duree_etapes_kpi = f"{jours_e_entiers}j {heures_e_restantes}h"
    
    jours_indic_entiers = int(jours_totaux_indicatif)
    heures_indic_restantes = int(round((jours_totaux_indicatif - jours_indic_entiers) * 24))
    txt_duree_indic_kpi = f"{jours_indic_entiers}j {heures_indic_restantes}h"

    # ==============================================================================
    # --- 4. AFFICHAGE DES KPIS COMPTABLES SUR DEUX LIGNES PROPRES ---
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Budgétaire Consolidé (Sim-TP)")
    
    # Ligne 1 : Les centres de coûts
    c_rc1, c_rc2, c_rc3, c_rc4 = st.columns(4)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")

    # Ligne 2 : Restauration et alignement du montant, des bénéfices nets et des ROIs
    c_g1, c_g2, c_g3, c_g4, c_g5, c_g6 = st.columns(6)
    with c_g1: st.metric(label="💰 Montant du Chantier", value=f"{revenus:,.0f}".replace(",", " ") + " €")
    with c_g2: st.metric(label="📈 Bénéfice Net", value=f"{txt_benefice} €")
    with c_g3: st.metric(label="📊 ROI Global", value=f"{roi_recap:.2f} %")
    with c_g4: st.metric(label="⚡ ROI / Jour", value=f"{roi_par_jour_recap:.2f} %/j")
    with c_g5: st.metric(label="⏱ Honoraires Contrat", value=txt_duree_indic_kpi) 
    with c_g6: st.metric(label="⏱ Planification Élaborée (Réelle)", value=txt_duree_etapes_kpi)

    if jours_totaux_calcul_etapes > 0 and abs(jours_totaux_indicatif - jours_totaux_calcul_etapes) > 0.05:
        st.warning(
            f"⚠️ **Désynchronisation de planning :** La durée globale du contrat (`{txt_duree_indic_kpi}`) "
            f"diffère de la durée réelle cumulée étape par étape (`{txt_duree_etapes_kpi}`)."
        )
    else:
        st.success("✅ **Planning Parfaitement Aligné :** La durée réelle des étapes correspond à l'en-tête du contrat.")

    if benefice_net_recap >= 0: 
        st.success(f"🟢 **Rentabilité positive :** Bénéfice net estimé de **{txt_benefice} €** (ROI Global : **{roi_recap:.2f} %**)")
    else: 
        st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** (ROI Global : **{roi_recap:.2f} %**)")

    # --- 5. LIAISON COMPTABLE DIRECTE HISTORIQUE CLOUD ---
    if st.button("✅ VALIDER LE CALCUL ET ENVOYER À LA PAGE HISTORIQUE & CLASSEMENT", type="primary", width="stretch", key="btn_ajouter_chantier_final_v20"):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier: 
            st.error("⚠️ Erreur : Saisissez un nom ou un numéro de chantier valide.")
        elif doublon_existe: 
            st.error(f"❌ Erreur NoSQL : Une fiche identique au nom de '{nom_chantier}' existe déjà dans l'Historique.")
        else:
            st.session_state["temp_submit_data"] = {
                "nom_chantier": nom_chantier, 
                "revenus": revenus, 
                "jours_saisis": jours_indic_entiers,
                "heures_saisies": heures_indic_restantes, 
                "minutes_saisies": 0,
                "type_contrat_cond": type_contrat_cond, 
                "type_contrat_chef": type_contrat_chef, 
                "type_contrat_ouv": type_contrat_ouv,
                "cout_cond": cout_cond, 
                "cout_chefs": cout_chefs, 
                "cout_ouvriers": cout_ouvriers,
                "txt_mats": txt_mats, 
                "txt_loc": txt_loc, 
                "txt_sal": txt_sal, 
                "txt_depenses": txt_depenses,
                "roi_recap": roi_recap, 
                "roi_par_jour_recap": roi_par_jour_recap,
                "txt_gain_jour": txt_gain_jour, 
                "total_mats_recap": total_mats_recap,
                "total_location_recap": total_location_recap, 
                "total_salaires_recap": total_salaires_recap,
                "total_depenses_recap": total_depenses_recap, 
                "benefice_net_recap": benefice_net_recap,
                "jours_totaux": jours_totaux, 
                "gain_par_jour_recap": gain_par_jour_recap,
                "txt_duree_indic": txt_duree_indic_kpi,
                "txt_duree_etapes": txt_duree_etapes_kpi
            }
            st.session_state["activer_popup_confirmation"] = True
            st.rerun()

    if st.session_state.get("activer_popup_confirmation") and "temp_submit_data" in st.session_state:
        popup_confirmation_enregistrement()

