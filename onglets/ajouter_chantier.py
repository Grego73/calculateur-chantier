import streamlit as st
import pandas as pd
import math
import database as db

def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
    st.subheader("Formulaire de saisie")
    
    # 🚀 CONFIGURATION DE L'ESPACEMENT MAXIMAL ALIGNÉ
    options_menu = ["Choisir un chantier pré-configuré..."]
    correspondance_cles = {}
    
    # Largeur fixe pour le nom (augmente à 70 ou 80 si tu as des noms de chantiers extrêmement longs)
    largeur_alignement = 65 
    
    for cle_document, donnees in CATALOGUE_CHANTIERS.items():
        if cle_document == "Choisir un chantier pré-configuré...":
            continue
            
        nom_propre_affichage = donnees.get("nom_modele", cle_document)
        prix_formate = f"{int(donnees.get('revenus', 0)):,.0f}".replace(",", " ")
        
        # 🎯 Force le nom à occuper exactement 'largeur_alignement' caractères en complétant avec des espaces
        nom_aligne = nom_propre_affichage.ljust(largeur_alignement)
        
        # Construction de l'option avec un alignement parfait à droite pour le prix
        texte_option = f"{nom_aligne} ({prix_formate} euros)"
        options_menu.append(texte_option)
        correspondance_cles[texte_option] = cle_document
        
    options_menu_triees = ["Choisir un chantier pré-configuré..."] + sorted(options_menu[1:])
    
    # Fonction de forçage du cache d'affichage des inputs
    def mise_a_jour_cache_modele():
        selection_affichage = st.session_state["select_modele_chantier_dynamique"]
        
        if selection_affichage == "Choisir un chantier pré-configuré...":
            modele = {}
        else:
            vrai_nom_firebase = correspondance_cles.get(selection_affichage, selection_affichage)
            modele = CATALOGUE_CHANTIERS[vrai_nom_firebase]
        
        if "table_engins_necessaires" in st.session_state: del st.session_state["table_engins_necessaires"]
        if "table_engins_a_louer" in st.session_state: del st.session_state["table_engins_a_louer"]
        if "table_employes_planification_etapes" in st.session_state: del st.session_state["table_employes_planification_etapes"]
            
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
        options_menu_triees, key="select_modele_chantier_dynamique", on_change=mise_a_jour_cache_modele
    )
    
    vrai_nom_propre = correspondance_cles.get(chantier_selectionne, "")
    valeur_nom_defaut = "" if chantier_selectionne == "Choisir un chantier pré-configuré..." else vrai_nom_propre
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()

    # 2. SECTIONS DE COLONNES (UNIQUEMENT POUR LES INPUTS GENERAUX ET RH)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=st.session_state["val_revenus"], step=100.0, format="%.0f")
        
        st.write("⏱️ **Durée totale du chantier :**")
        c_j, c_h, c_m = st.columns(3)
        with c_j: jours_saisis = st.number_input("Jours", min_value=0, value=st.session_state["val_jours"], step=1)
        with c_h: heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=0, step=1)
        with c_m: minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1)

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
        st.markdown("### --- CONFIGURATION DE LA MAIN-D'ŒUVRE PAR ÉTAPE ---")
        st.caption("💡 CDI : au prorata réel. CDD : à la journée complète entamée (due).")
        
        c_rh_co, c_rh_ch, c_rh_ou = st.columns(3)
        with c_rh_co: type_contrat_cond = st.selectbox("Contrat Conducteurs :", ["CDI", "CDD"], key="type_contrat_cond")
        with c_rh_ch: type_contrat_chef = st.selectbox("Contrat Chefs :", ["CDI", "CDD"], key="type_contrat_chef")
        with c_rh_ou: type_contrat_ouv = st.selectbox("Contrat Ouvriers :", ["CDI", "CDD"], key="type_contrat_ouv")
        
        px_cond = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Moyen", SALAIRES_DB.get("Conducteur", 230.0)))
        px_chef = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Moyen", SALAIRES_DB.get("Chef", 230.0)))
        px_ouvrier = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Moyen", SALAIRES_DB.get("Ouvrier", 230.0)))

        st.info(f"💰 Tarifs : 🕹️ Cond : {px_cond:.0f}€/j | 🧑‍💼 Chef : {px_chef:.0f}€/j | 👷 Ouv : {px_ouvrier:.0f}€/j")

        st.markdown("**👥 Planification des Effectifs requis à l'Étape :**")
        donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
        lignes_employes_modele = []
        
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            etapes_vues = set()
            for item in donnees_modele["engins_requis"]:
                num_e = item.get("N° Étape", 1)
                t_engin = item.get("Type d'engin requis")
                if t_engin is None or str(t_engin).strip() == "" or str(t_engin).lower() == "none": continue
                if num_e not in etapes_vues:
                    etapes_vues.add(num_e)
                    lignes_employes_modele.append({
                        "N° Étape": int(num_e), "Durée Étape (jours)": int(item.get("Durée Étape (jours)", 1)),
                        "🕹️ Conducteurs": int(donnees_modele.get("jh_cond", 1)), "🧑‍💼 Chefs": int(donnees_modele.get("jh_chef", 0)), "👷 Ouvriers": int(donnees_modele.get("jh_ouvrier", 0))
                    })
        
        df_rh_init = pd.DataFrame(lignes_employes_modele)
        if df_rh_init.empty: df_rh_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "🕹️ Conducteurs", "🧑‍💼 Chefs", "👷 Ouvriers"])

        tableau_employes_etapes = st.data_editor(
            df_rh_init, num_rows="dynamic", use_container_width=True, key="table_employes_planification_etapes",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Jours", min_value=1, step=1, required=True, width="small"),
                "🕹️ Conducteurs": st.column_config.NumberColumn("Cond", min_value=0, step=1, default=1, width="small"),
                "🧑‍💼 Chefs": st.column_config.NumberColumn("Chef", min_value=0, step=1, default=0, width="small"),
                "👷 Ouvriers": st.column_config.NumberColumn("Ouv", min_value=0, step=1, default=0, width="small")
            }
        )

    # 🚨 SORTIE DES COLONNES : LES TABLES D'ENGINS SONT DEPLOYÉES SUR TOUTE LA LARGEUR (ZÉRO NAMEERROR POSSIBLE)
    st.markdown("---")
    st.markdown("### 🚜 --- TABLE DES ENGINS NÉCESSAIRES ---")
    
    engins_bruts_modele = []
    if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
        for item in donnees_modele["engins_requis"]:
            t_engin = item.get("Type d'engin requis")
            if t_engin is None or str(t_engin).strip() == "" or str(t_engin).lower() == "none": continue
            engins_bruts_modele.append({
                "N° Étape": int(item.get("N° Étape", 1)), "Durée Étape (jours)": int(item.get("Durée Étape (jours)", 1)),
                "Type d'engin requis": str(t_engin).strip(), "Niveau requis": item.get("Niveau requis", "N1"), "À louer ?": False
            })
            
    df_besoins_init = pd.DataFrame(engins_bruts_modele)
    if not df_besoins_init.empty: df_besoins_init = df_besoins_init.dropna(subset=["Type d'engin requis"])
    if df_besoins_init.empty: df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
    
    # 📏 Version corrigée : On passe le Type d'engin en TextColumn pour éviter les cases blanches
    engins_necessaires = st.data_editor(
        df_besoins_init, num_rows="dynamic", use_container_width=True, key="table_engins_necessaires",
        column_config={
            "N° Étape": st.column_config.NumberColumn("N° Étape", min_value=1, step=1, required=True),
            "Durée Étape (jours)": st.column_config.NumberColumn("Durée (jours)", min_value=1, step=1, required=True),
            "Type d'engin requis": st.column_config.TextColumn("Type d'engin requis", disabled=True), # 🚀 FIX : Plus de blocage d'options !
            "Niveau requis": st.column_config.SelectboxColumn("Niveau requis", options=["N1", "N2", "N3", "N4"], required=True),
            "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False)
        }
    )


    engins_transferes_list = []
    if not engins_necessaires.empty and "À louer ?" in engins_necessaires.columns:
        df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
        for _, row in df_coches.iterrows():
            type_demande = str(row["Type d'engin requis"]).strip()
            niveau_demande = str(row["Niveau requis"]).strip().lower()
            duree_etape = int(row["Durée Étape (jours)"])
            
            def nettoyer_mots(texte):
                texte = texte.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                for char in ["'", "-", "/", "’"]: texte = texte.replace(char, " ")
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
                
            engins_transferes_list.append({
                "engin_modele": modele_trouve, "Quantité": 1, "Prix Location (€/jour)": prix_trouve, "Jours de Location": duree_etape
            })

    st.markdown("### 🚜 --- TABLE DES ENGINS À LOUER ---")
    df_engins_init = pd.DataFrame(columns=["engin_modele", "Quantité", "Prix Location (€/jour)", "Jours de Location"])
    if len(engins_transferes_list) > 0: df_engins_init = pd.DataFrame(engins_transferes_list)
    
    engins_edites = st.data_editor(
        df_engins_init, num_rows="dynamic", use_container_width=True, key="table_engins_a_louer",
        column_config={
            "engin_modele": st.column_config.TextColumn("Engin & Modèle", disabled=True),
            "Quantité": st.column_config.NumberColumn("Quantité", min_value=1, default=1, step=1),
            "Prix Location (€/jour)": st.column_config.NumberColumn("Prix Location (€/jour)", min_value=0, step=10),
            "Jours de Location": st.column_config.NumberColumn("Jours de Location", min_value=1, max_value=365, step=1)
        }
    )

    # ==============================================================================
    # --- LOGIQUE FINALE DE SYNTHÈSE ET DE CALCUL FINANCIER ---
    # ==============================================================================
    jours_factures_jeu = math.ceil(jours_totaux)
    total_mats_recap = float(total_mats_direct)

    total_location_recap = 0.0
    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["engin_modele"])
        total_location_recap = float((df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * df_propres_direct["Jours de Location"]).sum())

    cout_cond, cout_chefs, cout_ouvriers = 0.0, 0.0, 0.0
    jh_cond, jh_chef, jh_ouvrier = 0.0, 0.0, 0.0

    if tableau_employes_etapes is not None and not tableau_employes_etapes.empty:
        df_rh_propre = tableau_employes_etapes.dropna(subset=["N° Étape"])
        for _, r_rh in df_rh_propre.iterrows():
            duree_etape_reelle = float(r_rh.get("Durée Étape (jours)", 1.0))
            c_count = float(r_rh.get("🕹️ Conducteurs", 0))
            ch_count = float(r_rh.get("🧑‍💼 Chefs", 0))
            o_count = float(r_rh.get("👷 Ouvriers", 0))
            
            cout_cond += c_count * duree_etape_reelle * px_cond
            cout_chefs += ch_count * duree_etape_reelle * px_chef
            cout_ouvriers += o_count * duree_etape_reelle * px_ouvrier
            
            jh_cond += c_count * duree_etape_reelle
            jh_chef += ch_count * duree_etape_reelle
            jh_ouvrier += o_count * duree_etape_reelle

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
        st.code(f"Conducteurs : {cout_cond:,.0f} € (basé sur le cumul des étapes)")
        st.code(f"Chefs : {cout_chefs:,.0f} € (basé sur le cumul des étapes)")
        st.code(f"Ouvriers : {cout_ouvriers:,.0f} € (basé sur le cumul des étapes)")

        st.markdown("#### 🗂️ 3. Structure finale NoSQL (Firebase)")
        donnees_popup = {
            "Champ technique (Firestore)": ["nom_chantier", "revenus", "cout_materiaux", "cout_location", "cout_salaires", "depenses_totales", "benefice_net", "roi", "gain_par_jour"],
            "Valeur brute insérée": [nom_chantier, f"{revenus:,.0f} €".replace(",", " "), f"{txt_mats} €", f"{txt_loc} €", f"{txt_sal} €", f"{txt_depenses} €", f"{txt_benefice} €", f"{roi_recap:.2f} %", f"{txt_gain_jour} €/j"]
        }
        st.table(pd.DataFrame(donnees_popup))
        
        st.warning("🚨 Confirmez-vous l'envoi de cette simulation vers l'Historique cloud de l'entreprise ?")
        col_pop1, col_pop2 = st.columns(2)
        with col_pop1:
            if st.button("✅ ACCEPTER & ENREGISTRER", type="primary", use_container_width=True):
                db.inserer_chantier(nom_chantier, revenus, total_mats_recap, total_location_recap, total_salaires_recap, total_depenses_recap, benefice_net_recap, round(roi_recap, 2), float(jours_totaux), round(gain_par_jour_recap, 2), round(roi_par_jour_recap, 2))
                st.toast("🚀 Simulation enregistrée avec succès sur le Cloud Firestore !")
                st.rerun()
        with col_pop2:
            if st.button("❌ ANNULER & MODIFIER", use_container_width=True): st.rerun()

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary", use_container_width=True):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        if not nom_chantier: 
            st.error("⚠️ Erreur : Saisissez un nom ou un numéro de chantier valide avant d'exécuter l'insertion.")
        elif doublon_existe: 
            st.error(f"❌ Erreur NoSQL : Une fiche identique au nom de '{nom_chantier}' existe déjà dans l'historique cloud.")
        else: 
            confirmer_enregistrement_chantier_detaill()

