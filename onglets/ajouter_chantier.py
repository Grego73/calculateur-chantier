import streamlit as st
import pandas as pd
import math
import database as db

def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
    st.subheader("Formulaire de saisie")
    
    liste_triee = ["Choisir un chantier pré-configuré..."] + sorted([k for k in CATALOGUE_CHANTIERS.keys() if k != "Choisir un chantier pré-configuré..."])
    
    # Fonction de forçage du cache d'affichage des inputs (CORRIGÉE POUR LES ENGINS)
    def mise_a_jour_cache_modele():
        selection = st.session_state["select_modele_chantier_dynamique"]
        modele = CATALOGUE_CHANTIERS[selection]
        
        # 🚨 CORRECTIF SÉCURITÉ STREAMLIT : On détruit l'ancienne mémoire des tableaux éditables
        # Cela force Streamlit à reconstruire le tableau avec les nouvelles données Firebase
        if "table_engins_necessaires" in st.session_state:
            del st.session_state["table_engins_necessaires"]
        if "table_engins_a_louer" in st.session_state:
            del st.session_state["table_engins_a_louer"]
        if "table_employes_planification_etapes" in st.session_state:
            del st.session_state["table_employes_planification_etapes"]
        
        # Injection immédiate des variables de matériaux et RH
        st.session_state["val_revenus"] = float(modele.get("revenus", 0.0))
        st.session_state["val_jours"] = int(modele.get("jours", 0))
        st.session_state["val_sable"] = float(modele.get("sable", 0.0))
        st.session_state["val_terre"] = float(modele.get("terre", 0.0))
        st.session_state["val_enrobe"] = float(modele.get("enrobe", 0.0))
        st.session_state["val_armature"] = float(modele.get("armature", 0.0))
        st.session_state["val_tole"] = float(modele.get("tole", 0.0))
        st.session_state["val_beton"] = float(modele.get("beton", 0.0))
        st.session_state["val_panneaux"] = float(modele.get("panneaux", 0.0))
        st.session_state["val_tuyaux"] = float(modele.get("tuyaux", 0.0))
        st.session_state["val_canalisations"] = float(modele.get("canalisations", 0.0))
        st.session_state["val_poutres"] = float(modele.get("poutres", 0.0))
        
        st.session_state["val_jh_cond"] = float(modele.get("jh_cond", 0.0))
        st.session_state["val_jh_chef"] = float(modele.get("jh_chef", 0.0))
        st.session_state["val_jh_ouvrier"] = float(modele.get("jh_ouvrier", 0.0))

    # Initialisation des variables de secours dans le state au tout premier chargement
    if "val_revenus" not in st.session_state:
        st.session_state["val_revenus"] = 0.0
        st.session_state["val_jours"] = 0
        for k in ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]:
            st.session_state[f"val_{k}"] = 0.0
        st.session_state["val_jh_cond"] = 0.0
        st.session_state["val_jh_chef"] = 0.0
        st.session_state["val_jh_ouvrier"] = 0.0

    chantier_selectionne = st.selectbox(
        "🚀 Sélectionner un modèle de chantier dynamique :", 
        liste_triee,
        key="select_modele_chantier_dynamique",
        on_change=mise_a_jour_cache_modele
    )
    
    valeur_nom_defaut = "" if chantier_selectionne == "Choisir un chantier pré-configuré..." else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=st.session_state["val_revenus"], step=100.0, format="%.0f")
        
        st.write("⏱️ **Durée totale du chantier :**")
        c_j, c_h, c_m = st.columns(3)
        with c_j:
            jours_saisis = st.number_input("Jours", min_value=0, value=st.session_state["val_jours"], step=1)
        with c_h:
            heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=0, step=1)
        with c_m:
            minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1)

        heures_en_jours = heures_saisies / 24.0
        minutes_en_jours = minutes_saisies / 1440.0
        jours_totaux = float(jours_saisis + heures_en_jours + minutes_en_jours)

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
            qte_eaux_usees = st.number_input("Unités de Canalisations eaux usées :", value=st.session_state["val_canalisations"], format="%.0f")
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
            prix_eaux_usees = st.number_input("Prix Canalisations (€/u) :", value=float(MATERIAUX_DB.get("Canalisations", 35)), format="%.0f")
            prix_poutres = st.number_input("Prix Poutres acier (€/u) :", value=float(MATERIAUX_DB.get("Poutres", 70)), format="%.0f")

        total_mats_direct = float((qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_eaux_usees*prix_eaux_usees) + (qte_poutres*prix_poutres))
        st.info(f"🧱 **Total est. matériaux :** {total_mats_direct:,.0f}".replace(",", " ") + " €")
        
    with col2:
        st.markdown("### --- CONFIGURATION DE LA MAIN-D'ŒUVRE PAR ÉTAPE ---")
        st.caption("💡 CDI : au prorata réel (1 mois = 7j). CDD : à la journée complète entamée (due).")
        
        # --- TYPE DE CONTRAT DE L'ÉQUIPE GLOBOALE ---
        c_rh_co, c_rh_ch, c_rh_ou = st.columns(3)
        with c_rh_co: type_contrat_cond = st.selectbox("Contrat Conducteurs :", ["CDI", "CDD"], key="type_contrat_cond")
        with c_rh_ch: type_contrat_chef = st.selectbox("Contrat Chefs :", ["CDI", "CDD"], key="type_contrat_chef")
        with c_rh_ou: type_contrat_ouv = st.selectbox("Contrat Ouvriers :", ["CDI", "CDD"], key="type_contrat_ouv")
        
        # --- STRATÉGIE SALARIALE (PALIERS DE TA GRILLE SANS AUCUNE DIVISION) ---
        p_min_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Min", 235.0))
        p_moy_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Moyen", 235.0))
        p_max_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Max", 235.0))
        
        p_min_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Min", 232.0))
        p_moy_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Moyen", 232.0))
        p_max_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Max", 232.0))
        
        p_min_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Min", 240.0))
        p_moy_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Moyen", 240.0))
        p_max_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Max", 240.0))

        c_strat_co, c_strat_ch, c_strat_ou = st.columns(3)
        with c_strat_co:
            strat_cond = st.selectbox("Salaire Conducteurs :", [f"Éco ({p_min_co:.0f}€)", f"Std ({p_moy_co:.0f}€)", f"Prem ({p_max_co:.0f}€)"], key="sel_strat_cond")
            # 🚀 CORRECTIF : Utilisation directe du prix brut du palier
            px_cond = p_min_co if "Éco" in strat_cond else (p_moy_co if "Std" in strat_cond else p_max_co)
        with c_strat_ch:
            strat_chef = st.selectbox("Salaire Chefs :", [f"Éco ({p_min_c:.0f}€)", f"Std ({p_moy_c:.0f}€)", f"Prem ({p_max_c:.0f}€)"], key="sel_strat_chef")
            # 🚀 CORRECTIF : Utilisation directe du prix brut du palier
            px_chef = p_min_c if "Éco" in strat_chef else (p_moy_c if "Std" in strat_chef else p_max_c)
        with c_strat_ou:
            strat_ouv = st.selectbox("Salaire Ouvriers :", [f"Éco ({p_min_o:.0f}€)", f"Std ({p_moy_o:.0f}€)", f"Prem ({p_max_o:.0f}€)"], key="sel_strat_ouv")
            # 🚀 CORRECTIF : Utilisation directe du prix brut du palier
            px_ouvrier = p_min_o if "Éco" in strat_ouv else (p_moy_o if "Std" in strat_ouv else p_max_o)

        # --- NOUVEAU : LE TABLEAU DES EMPLOYÉS PAR ÉTAPE ---
        st.markdown("**👥 Planification des Effectifs requis à l'Étape :**")
        
        donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
        lignes_employes_modele = []
        
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            etapes_vues = set()
            for item in donnees_modele["engins_requis"]:
                num_e = item.get("N° Étape", 1)
                t_engin = item.get("Type d'engin requis")
                
                # On ignore les étapes fantômes qui n'ont pas d'engin valide rattaché
                if t_engin is None or str(t_engin).strip() == "" or str(t_engin).lower() == "none":
                    continue
                    
                if num_e not in etapes_vues:
                    etapes_vues.add(num_e)
                    lignes_employes_modele.append({
                        "N° Étape": int(num_e),
                        "Durée Étape (jours)": int(item.get("Durée Étape (jours)", 1)),
                        "🕹️ Conducteurs": int(donnees_modele.get("jh_cond", 1)),
                        "🧑‍💼 Chefs": int(donnees_modele.get("jh_chef", 0)),
                        "👷 Ouvriers": int(donnees_modele.get("jh_ouvrier", 0))
                    })

        df_rh_init = pd.DataFrame(lignes_employes_modele)
        if df_rh_init.empty: 
            df_rh_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "🕹️ Conducteurs", "🧑‍💼 Chefs", "👷 Ouvriers"])

        # Affichage du grand Tableau Étape par Étape pour les Employés
        tableau_employes_etapes = st.data_editor(
            df_rh_init, num_rows="dynamic", use_container_width=True, key="table_employes_planification_etapes",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N° Étape", min_value=1, step=1, required=True),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée (jours)", min_value=1, step=1, required=True),
                "🕹️ Conducteurs": st.column_config.NumberColumn("Conducteurs", min_value=0, step=1, default=1),
                "🧑‍💼 Chefs": st.column_config.NumberColumn("Chefs", min_value=0, step=1, default=0),
                "👷 Ouvriers": st.column_config.NumberColumn("Ouvriers", min_value=0, step=1, default=0)
            }
        )

        # --- TON TABLEAU DE GESTION DES ENGINS (IL RESTE ICI) ---
        st.markdown("### --- TABLE DES ENGINS NÉCESSAIRES ---")
        donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
        engins_bruts_modele = []
        
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            for item in donnees_modele["engins_requis"]:
                t_engin = item.get("Type d'engin requis")
                
                # 🚨 FILTRAGE RADICAL : On ignore la ligne si l'engin est absent, vide ou contient textuellement "none"
                if t_engin is None or str(t_engin).strip() == "" or str(t_engin).lower() == "none":
                    continue
                    
                engins_bruts_modele.append({
                    "N° Étape": int(item.get("N° Étape", 1)), 
                    "Durée Étape (jours)": int(item.get("Durée Étape (jours)", 1)),
                    "Type d'engin requis": str(t_engin).strip(), 
                    "Niveau requis": item.get("Niveau requis", "N1"), 
                    "À louer ?": False
                })
                
        df_besoins_init = pd.DataFrame(engins_bruts_modele)
        
        # 🚨 DEUXIÈME BARRIÈRE DE SÉCURITÉ : On nettoie le DataFrame de toutes les lignes incomplètes 
        # pour éliminer les warnings rouges et les lignes vides à la source
        if not df_besoins_init.empty:
            df_besoins_init = df_besoins_init.dropna(subset=["Type d'engin requis"])
            df_besoins_init = df_besoins_init[df_besoins_init["Type d'engin requis"] != ""]
            
        if df_besoins_init.empty: 
            df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        
        # 📏 AMÉLIORATION LARGEUR : On force des colonnes petites pour afficher "À louer ?" du premier coup
        engins_necessaires = st.data_editor(
            df_besoins_init, num_rows="dynamic", use_container_width=True, key="table_engins_necessaires",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Jours", min_value=1, step=1, required=True, width="small"),
                "Type d'engin requis": st.column_config.SelectboxColumn("Type d'engin", options=TYPES_ENGINS_BRUTS, required=True, width="medium"),
                "Niveau requis": st.column_config.SelectboxColumn("Niv", options=["N1", "N2", "N3", "N4"], required=True, width="small"),
                "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False, width="small")
            }
        )

        # 🚜 LOGIQUE DE TRANSFERT SÉCURISÉE AVEC CLÉ TECHNIQUE SIMPLIFIÉE
        engins_transferes_list = []
        if not engins_necessaires.empty and "À louer ?" in engins_necessaires.columns:
            df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
            
            for _, row in df_coches.iterrows():
                type_demande = str(row["Type d'engin requis"]).strip()
                niveau_demande = str(row["Niveau requis"]).strip().lower()
                duree_etape = int(row["Durée Étape (jours)"])
                
                def nettoyer_mots(texte):
                    texte = texte.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                    for char in ["'", "-", "/", "’"]: 
                        texte = texte.replace(char, " ")
                    mots = texte.split()
                    mots_utiles = ["pour", "de", "d", "un", "une", "le", "la", "les", "sur"]
                    return [m for m in mots if m not in mots_utiles]

                mots_cles_recherche = nettoyer_mots(type_demande)
                modele_trouve, prix_trouve = None, 380.0
                
                for engin_nom, prix in CATALOGUE_ENGINS.items():
                    if niveau_demande in engin_nom.lower() and all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                        modele_trouve, prix_trouve = engin_nom, prix
                        break
                
                if not modele_trouve:
                    for engin_nom, prix in CATALOGUE_ENGINS.items():
                        if all(mot in nettoyer_mots(engin_nom) for mot in mots_cles_recherche):
                            modele_trouve, prix_trouve = engin_nom, prix
                            break
                            
                if not modele_trouve:
                    modele_trouve = f"{type_demande} ({niveau_demande.upper()})"
                    prix_trouve = 380.0
                    
                # 🚀 SÉCURITÉ : Clé technique simplifiée 'engin_modele'
                engins_transferes_list.append({
                    "engin_modele": modele_trouve, 
                    "Quantité": 1, 
                    "Prix Location (€/jour)": prix_trouve, 
                    "Jours de Location": duree_etape
                })

        st.markdown("### --- TABLE DES ENGINS À LOUER ---")
        df_engins_init = pd.DataFrame(columns=["engin_modele", "Quantité", "Prix Location (€/jour)", "Jours de Location"])
        if len(engins_transferes_list) > 0: 
            df_engins_init = pd.DataFrame(engins_transferes_list)
        
        # 📏 Rendu visuel compact et synchronisé
        engins_edites = st.data_editor(
            df_ins_init if 'df_ins_init' in locals() else df_engins_init, num_rows="dynamic", use_container_width=True, key="table_engins_a_louer",
            column_config={
                "engin_modele": st.column_config.SelectboxColumn("Engin & Modèle", options=list(CATALOGUE_ENGINS.keys()), required=True, width="medium"),
                "Quantité": st.column_config.NumberColumn("Qté", min_value=1, default=1, step=1, width="small"),
                "Prix Location (€/jour)": st.column_config.NumberColumn("Prix/j", min_value=0, step=10, width="small"),
                "Jours de Location": st.column_config.NumberColumn("Jours", min_value=1, max_value=365, step=1, width="small")
            }
        )

    # ==============================================================================
    # --- LOGIQUE FINALE DE SYNTHÈSE ET DE CALCUL FINANCIER DU JEU (CUMUL ÉTAPES) ---
    # ==============================================================================
    jours_factures_jeu = math.ceil(jours_totaux)
    total_mats_recap = float(total_mats_direct)

    total_location_recap = 0.0
    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["engin_modele"]) # 🚀 Utilise engin_modele ici aussi !
        total_location_recap = float((df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * df_propres_direct["Jours de Location"]).sum())

    # Initialisation des compteurs de jours-hommes cumulés pour le chantier
    total_jours_hommes_cond = 0.0
    total_jours_hommes_chef = 0.0
    total_jours_hommes_ouvrier = 0.0

    if tableau_employes_etapes is not None and not tableau_employes_etapes.empty:
        df_rh_propre = tableau_employes_etapes.dropna(subset=["N° Étape"])
        
        for _, r_rh in df_rh_propre.iterrows():
            # On prend la durée exacte configurée pour cette étape précise
            duree_etape_reelle = float(r_rh.get("Durée Étape (jours)", 1.0))
            
            # Récupération des effectifs de l'étape
            c_count = float(r_rh.get("🕹️ Conducteurs", 0))
            ch_count = float(r_rh.get("🧑‍💼 Chefs", 0))
            o_count = float(r_rh.get("👷 Ouvriers", 0))
            
            # Mathématiques du jeu : Cumul (Effectif x Durée de l'étape)
            total_jours_hommes_cond += c_count * duree_etape_reelle
            total_jours_hommes_chef += ch_count * duree_etape_reelle
            total_jours_hommes_ouvrier += o_count * duree_etape_reelle

    # --- APPLICATION DU TARIF SALARIAL SUR LES CUMULS ---
    cout_cond = total_jours_hommes_cond * px_cond
    cout_chefs = total_jours_hommes_chef * px_chef
    cout_ouvriers = total_jours_hommes_ouvrier * px_ouvrier

    # Sauvegarde des maximums pour l'affichage NoSQL
    jh_cond = total_jours_hommes_cond
    jh_chef = total_jours_hommes_chef
    jh_ouvrier = total_jours_hommes_ouvrier

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
    txt_benefice = f"{abs(benefice_net_recap):,.0f}".replace(",", " ")
    txt_duree_precise = f"{int(jours_totaux)} jours" if jours_totaux >= 1 else f"{heures_saisies}h {minutes_saisies}m"

    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Global Estimé (Règles du Jeu)")
    c_rc1, c_rc2, c_rc3, c_rc4, c_rc5, c_rc6 = st.columns(6)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires (RH)", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")
    with c_rc5: st.metric(label="⏱️ Durée du Projet", value=txt_duree_precise)
    with c_rc6: st.metric(label="📈 Gain / Jour", value=f"{txt_gain_jour} €/j")

    if benefice_net_recap >= 0: 
        st.success(f"🟢 **Rentabilité positive :** Bénéfice de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** (ROI Global : **{roi_recap:.2f} %**)")
    else: 
        st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** (ROI Global : **{roi_recap:.2f} %**)")

    @st.dialog("🔍 Rapport de Calcul et Feuille d'Insertion NoSQL")
    def confirmer_enregistrement_chantier_detaill():
        st.write("Voici la transparence complète des calculs et formules appliqués selon les règles de l'économie du jeu :")
        st.markdown("#### ⏱️ 1. Décomposition du Temps")
        st.write(f"- **Durée réelle saisie :** `{jours_saisis} jours, {heures_saisies} heures, {minutes_saisies} minutes`")
        st.write(f"- **Forfait facturé (Location & CDD) :** `{int(jours_factures_jeu)} jours` (Toute journée entamée est due)")

        st.markdown("#### 👥 2. Formules appliquées pour la Main-d'œuvre")
        if "CDI" in type_contrat_cond:
            st.code(f"{int(jh_cond)} employé(s) × {px_cond:.0f} €/jour (prorata CDI) × {int(jours_totaux)}j de présence = {cout_cond:,.0f} €".replace(",", " "))
        else:
            st.code(f"{int(jh_cond)} employé(s) × {px_cond:.0f} €/jour × {int(jours_factures_jeu)}j due(s) = {cout_cond:,.0f} €".replace(",", " "))

        if "CDI" in type_contrat_chef:
            st.code(f"{int(jh_chef)} employé(s) × {px_chef:.0f} €/jour (prorata CDI) × {int(jours_totaux)}j de présence = {cout_chefs:,.0f} €".replace(",", " "))
        else:
            st.code(f"{int(jh_chef)} employé(s) × {px_chef:.0f} €/jour × {int(jours_factures_jeu)}j due(s) = {cout_chefs:,.0f} €".replace(",", " "))

        if "CDI" in type_contrat_ouv:
            st.code(f"{int(jh_ouvrier)} employé(s) × {px_ouvrier:.0f} €/jour (prorata CDI) × {int(jours_totaux)}j de présence = {cout_ouvriers:,.0f} €".replace(",", " "))
        else:
            st.code(f"{int(jh_ouvrier)} employé(s) × {px_ouvrier:.0f} €/jour × {int(jours_factures_jeu)}j due(s) = {cout_ouvriers:,.0f} €".replace(",", " "))

        st.markdown("#### 🗂️ 3. Structure finale NoSQL (Firebase)")
        donnees_popup = {
            "Champ technique (Firestore)": [
                "nom_chantier", "revenus", "cout_materiaux", "cout_location", 
                "cout_salaires", "depenses_totales", "benefice_net", "roi", 
                "gain_par_jour"
            ],
            "Valeur brute insérée": [
                nom_chantier, 
                f"{revenus:,.0f} €".replace(",", " "), 
                f"{txt_mats} €", 
                f"{txt_loc} €", 
                f"{txt_sal} €", 
                f"{txt_depenses} €", 
                f"{txt_benefice} €", 
                f"{roi_recap:.2f} %", 
                f"{txt_gain_jour} €/j"
            ]
        }
        st.table(pd.DataFrame(donnees_popup))
        
        st.warning("🚨 Confirmez-vous l'envoi de cette simulation vers l'Historique cloud de l'entreprise ?")
        col_pop1, col_pop2 = st.columns(2)
        with col_pop1:
            if st.button("✅ ACCEPTER & ENREGISTRER", type="primary", use_container_width=True):
                db.inserer_chantier(
                    nom_chantier, revenus, total_mats_recap, total_location_recap, 
                    total_salaires_recap, total_depenses_recap, benefice_net_recap, 
                    round(roi_recap, 2), float(jours_totaux), round(gain_par_jour_recap, 2), 
                    round(roi_par_jour_recap, 2)
                )
                st.toast("🚀 Simulation enregistrée avec succès sur le Cloud Firestore !")
                st.rerun()
        with col_pop2:
            if st.button("❌ ANNULER & MODIFIER", use_container_width=True): 
                st.rerun()

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary", use_container_width=True):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        if not nom_chantier: 
            st.error("⚠️ Erreur : Saisissez un nom ou un numéro de chantier valide avant d'exécuter l'insertion.")
        elif doublon_existe: 
            st.error(f"❌ Erreur NoSQL : Une fiche identique au nom de '{nom_chantier}' existe déjà dans l'historique cloud.")
        else: 
            confirmer_enregistrement_chantier_detaill()

