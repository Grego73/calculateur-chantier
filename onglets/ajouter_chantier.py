import streamlit as st
import pandas as pd
import math
import database as db  # Accès aux fonctions d'insertion

def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
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
        
        st.write("⏱️ **Durée totale du chantier :**")
        c_j, c_h, c_m = st.columns(3)
        with c_j:
            jours_saisis = st.number_input("Jours", min_value=0, value=int(donnees_modele["jours"]), step=1)
        with c_h:
            heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=0, step=1)
        with c_m:
            minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1)

        # Logique de jeu : 1 journée = 24 heures
        jours_totaux = jours_saisis + (heures_saisies / 24.0) + (minutes_saisies / 1440.0)

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

        total_mats_direct = float((qte_sable*prix_sable) + (qte_terre*prix_terre) + (qte_enrobe*prix_enrobe) + (qte_armature*prix_armature) + (qte_tole*prix_tole) + (qte_beton*prix_beton) + (qte_panneaux*prix_panneaux) + (qte_tuyaux*prix_tuyaux) + (qte_eaux_usees*prix_eaux_usees) + (qte_poutres*prix_poutres))
        st.info(f"🧱 **Total est. matériaux :** {total_mats_direct:,.0f}".replace(",", " ") + " €")
        
    with col2:
        st.markdown("### --- GRILLE SALARIALE & INTERIM (PALIERS DYNAMIQUES) ---")
        st.caption("💡 Sélectionnez pour chaque profil la stratégie de rémunération recopiée depuis vos analyses de recrutement.")
        
        # --- 1. CONFIGURATION CONDUCTEURS ---
        st.markdown("**🕹️ PROFIL : CONDUCTEURS D'ENGINS**")
        c_cond_strat, c_cond_jh = st.columns(2)  # Ajout du chiffre 2 ici
        with c_cond_strat:
            p_min_co = float(SALAIRES_DB.get("Conducteur_Min", 230.0))
            p_moy_co = float(SALAIRES_DB.get("Conducteur_Moyen", 230.0))
            p_max_co = float(SALAIRES_DB.get("Conducteur_Max", 230.0))
            strat_cond = st.selectbox("Salaire Conducteur :", [f"Économique ({p_min_co:.0f} €)", f"Standard ({p_moy_co:.0f} €)", f"Premium ({p_max_co:.0f} €)"], key="sel_strat_cond")
            px_cond = p_min_co if "Économique" in strat_cond else (p_moy_co if "Standard" in strat_cond else p_max_co)
        with c_cond_jh:
            jh_cond = st.number_input("Jours-Homme", value=float(donnees_modele["jh_cond"]), key="jh_input_cond")

        # --- 2. CONFIGURATION CHEFS ---
        st.markdown("**🧑‍💼 PROFIL : CHEFS DE CHANTIER**")
        c_chef_strat, c_chef_jh = st.columns(2)  # Ajout du chiffre 2 ici
        with c_chef_strat:
            p_min_c = float(SALAIRES_DB.get("Chef_Min", 230.0))
            p_moy_c = float(SALAIRES_DB.get("Chef_Moyen", 230.0))
            p_max_c = float(SALAIRES_DB.get("Chef_Max", 230.0))
            strat_chef = st.selectbox("Salaire Chef :", [f"Économique ({p_min_c:.0f} €)", f"Standard ({p_moy_c:.0f} €)", f"Premium ({p_max_c:.0f} €)"], key="sel_strat_chef")
            px_chef = p_min_c if "Économique" in strat_chef else (p_moy_c if "Standard" in strat_chef else p_max_c)
        with c_chef_jh:
            jh_chef = st.number_input("Jours-Homme", value=float(donnees_modele["jh_chef"]), key="jh_input_chef")

        # --- 3. CONFIGURATION OUVRIERS ---
        st.markdown("**👷 PROFIL : OUVRIERS QUALIFIÉS**")
        c_ouv_strat, c_ouv_jh = st.columns(2)  # Ajout du chiffre 2 ici
        with c_ouv_strat:
            p_min_o = float(SALAIRES_DB.get("Ouvrier_Min", 230.0))
            p_moy_o = float(SALAIRES_DB.get("Ouvrier_Moyen", 230.0))
            p_max_o = float(SALAIRES_DB.get("Ouvrier_Max", 230.0))
            strat_ouv = st.selectbox("Salaire Ouvrier :", [f"Économique ({p_min_o:.0f} €)", f"Standard ({p_moy_o:.0f} €)", f"Premium ({p_max_o:.0f} €)"], key="sel_strat_ouv")
            px_ouvrier = p_min_o if "Économique" in strat_ouv else (p_moy_o if "Standard" in strat_ouv else p_max_o)
        with c_ouv_jh:
            jh_ouvrier = st.number_input("Jours-Homme", value=float(donnees_modele["jh_ouvrier"]), key="jh_input_ouv")

        # --- 4. CONFIGURATION INTÉRIMAIRES ---
        st.markdown("**⏱️ PROFIL : INTÉRIMAIRES EXTERNES**")
        c_int_strat, c_int_jh = st.columns(2)  # Ajout du chiffre 2 ici
        with c_int_strat:
            p_min_i = float(SALAIRES_DB.get("Intérim_Min", 220.0))
            p_moy_i = float(SALAIRES_DB.get("Intérim_Moyen", 220.0))
            p_max_i = float(SALAIRES_DB.get("Intérim_Max", 220.0))
            strat_int = st.selectbox("Tarif Intérim :", [f"Économique ({p_min_i:.0f} €)", f"Standard ({p_moy_i:.0f} €)", f"Premium ({p_max_i:.0f} €)"], key="sel_strat_int")
            px_interim = p_min_i if "Économique" in strat_int else (p_moy_i if "Standard" in strat_int else p_max_i)
        with c_int_jh:
            jh_interim = st.number_input("Nombre d'Intérimaires", value=0.0, key="jh_input_int")

        st.markdown("### --- TABLE DES ENGINS NÉCESSAIRES ---")

        engins_bruts_modele = []
        if "engins_requis" in donnees_modele and len(donnees_modele["engins_requis"]) > 0:
            for item in donnees_modele["engins_requis"]:
                engins_bruts_modele.append({
                    "N° Étape": item.get("N° Étape", 1), "Durée Étape (jours)": item.get("Durée Étape (jours)", 1),
                    "Type d'engin requis": item.get("Type d'engin requis", "Pelleteuses"), "Niveau requis": item.get("Niveau requis", "N1"), "À louer ?": False
                })
        df_besoins_init = pd.DataFrame(engins_bruts_modele)
        if df_besoins_init.empty: 
            df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        
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


    # ==============================================================================
    # --- LOGIQUE DE CALCUL DU JEU (ARRONDI AU JOUR SUPÉRIEUR POUR LOC/INTÉRIM) ---
    # ==============================================================================
    # Règle du jeu : toute journée entamée est entièrement due pour la location et l'intérim
    jours_factures_jeu = math.ceil(jours_totaux)

    # 1. Calcul des Matériaux
    total_mats_recap = float(total_mats_direct)

    # 2. Calcul de la Location des Engins
    total_location_recap = 0.0
    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["Sélection de l'engin / Modèle"])
        total_location_recap = float((df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * jours_factures_jeu).sum())

    # 3. Calcul de la Grille Salariale
    # Fixes (Mensuels) : au prorata réel du temps de jeu du chantier (1 semaine = 7 jours = 1 mois)
    cout_chefs = jh_chef * (px_chef / 7.0) * jours_totaux
    cout_ouvriers = jh_ouvrier * (px_ouvrier / 7.0) * jours_totaux
    cout_cond = jh_cond * (px_cond / 7.0) * jours_totaux
    # Intérimaires (Journaliers) : payés à la journée entamée (arrondi supérieur)
    cout_interim = jh_interim * px_interim * jours_factures_jeu

    total_salaires_recap = float(cout_chefs + cout_ouvriers + cout_cond + cout_interim)

    # 4. Synthèse financière globale
    total_depenses_recap = float(total_mats_recap + total_location_recap + total_salaires_recap)
    benefice_net_recap = float(revenus - total_depenses_recap)
    roi_recap = float((benefice_net_recap / total_depenses_recap) * 100 if total_depenses_recap > 0 else 0)
    
    gain_par_jour_recap = float(benefice_net_recap / jours_totaux if jours_totaux > 0 else 0.0)
    roi_par_jour_recap = float(roi_recap / jours_totaux if jours_totaux > 0 else roi_recap)

    # Formatage des textes pour affichage
    txt_mats = f"{total_mats_recap:,.0f}".replace(",", " ")
    txt_loc = f"{total_location_recap:,.0f}".replace(",", " ")
    txt_sal = f"{total_salaires_recap:,.0f}".replace(",", " ")
    txt_depenses = f"{total_depenses_recap:,.0f}".replace(",", " ")
    txt_gain_jour = f"{gain_par_jour_recap:,.0f}".replace(",", " ")
    txt_benefice = f"{abs(benefice_net_recap):,.0f}".replace(",", " ")

    # --- AFFICHAGE DU RÉCAPITULATIF FINANCIER VISUEL ---
    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Global Estimé (Règles du Jeu)")
    if jours_totaux > 0 and jours_totaux != jours_factures_jeu:
        st.warning(f"⚠️ **Pénalité de temps :** Le chantier dépasse sur la journée suivante. Vous êtes facturé **{jours_factures_jeu} jours** au lieu de {jours_totaux:.2f} jours pour la location et l'intérim.")

    txt_duree_precise = f"{jours_saisis}j {heures_saisies}h {minutes_saisies}m" if jours_totaux > 0 else "0 jour"

    c_rc1, c_rc2, c_rc3, c_rc4, c_rc5, c_rc6 = st.columns(6)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires & Intérim", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")
    with c_rc5: st.metric(label="⏱️ Durée du Projet", value=txt_duree_precise)
    with c_rc6: st.metric(label="📈 Rentabilité Quotidienne", value=f"{txt_gain_jour} €/j")

    if benefice_net_recap >= 0: 
        st.success(f"🟢 **Rentabilité positive :** Bénéfice de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** de travail (ROI Global : **{roi_recap:.2f} %** | ROI / Jour : **{roi_par_jour_recap:.2f} %/j**)")
    else: 
        st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** de perte (ROI Global : **{roi_recap:.2f} %** | ROI / Jour : **{roi_par_jour_recap:.2f} %/j**)")

    st.markdown("<br>", unsafe_allow_html=True) 

    # --- BOUTON DE SAUVEGARDE ET LIEN VERS DATABASE.PY ---
    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary"):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier: st.error("Veuillez donner un nom ou un numéro valide.")
        elif doublon_existe: st.error(f"Impossible d'enregistrer : ce chantier existe déjà.")
        else:
            db.inserer_chantier(nom_chantier, revenus, total_mats_recap, total_location_recap, total_salaires_recap, total_depenses_recap, benefice_net_recap, round(roi_recap, 2), float(jours_totaux), round(gain_par_jour_recap, 2), round(roi_par_jour_recap, 2))
            st.toast("Chantier enregistré avec succès dans Firebase !")
            st.rerun()
