import streamlit as st
import pandas as pd
import math
import database as db  # Pour l'enregistrement final sur Firebase

def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
    st.subheader("Formulaire de saisie")
    
    # Tri et liste des modèles
    liste_triee = ["Choisir un chantier pré-configuré..."] + sorted([k for k in CATALOGUE_CHANTIERS.keys() if k != "Choisir un chantier pré-configuré..."])
    
    # MODIFICATION PRINCIPALE : On force l'application à se recharger (rerun) dès qu'un modèle est cliqué
    chantier_selectionne = st.selectbox(
        "🚀 Sélectionner un modèle de chantier dynamique :", 
        liste_triee,
        key="select_modele_chantier_dynamique"
    )
    
    donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
    valeur_nom_defaut = "" if chantier_selectionne == "Choisir un chantier pré-configuré..." else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=float(donnees_modele.get("revenus", 0.0)))
        
        st.write("⏱️ **Durée totale du chantier :**")
        c_j, c_h, c_m = st.columns(3)
        with c_j:
            jours_saisis = st.number_input("Jours", min_value=0, value=int(donnees_modele.get("jours", 0)), step=1)
        with c_h:
            heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=0, step=1)
        with c_m:
            minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=1)

        # Logique de jeu : 1 journée = 24 heures = 1440 minutes (Parenthèses de sécurité)
        heures_en_jours = heures_saisies / 24.0
        minutes_en_jours = minutes_saisies / 1440.0
        jours_totaux = float(jours_saisis + heures_en_jours + minutes_en_jours)

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=float(donnees_modele.get("sable", 0.0)))
            qte_terre = st.number_input("Tonnes de Terre :", value=float(donnees_modele.get("terre", 0.0)))
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=float(donnees_modele.get("enrobe", 0.0)))
            qte_armature = st.number_input("Unités d'Armature métallique :", value=float(donnees_modele.get("armature", 0.0)))
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=float(donnees_modele.get("tole", 0.0)))
            qte_beton = st.number_input("Tonnes de Béton :", value=float(donnees_modele.get("beton", 0.0)))
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=float(donnees_modele.get("panneaux", 0.0)))
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=float(donnees_modele.get("tuyaux", 0.0)))
            qte_eaux_usees = st.number_input("Unités de Canalisations eaux usées :", value=float(donnees_modele.get("canalisations", 0.0)))
            qte_poutres = st.number_input("Unités de Poutres en acier :", value=float(donnees_modele.get("poutres", 0.0)))
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
        st.markdown("### --- GRILLE SALARIALE (PALIERS & CONTRATS) ---")
        st.caption("💡 CDI : au prorata réel (1 mois = 7j). CDD : à la journée complète entamée (due).")
        
        # --- 1. CONFIGURATION CONDUCTEURS ---
        st.markdown("**🕹️ PROFIL : CONDUCTEURS D'ENGINS**")
        c_cond_type, c_cond_strat, c_cond_jh = st.columns(3)
        with c_cond_type:
            type_contrat_cond = st.selectbox("Contrat :", ["CDI", "CDD"], key="type_contrat_cond")
        with c_cond_strat:
            p_min_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Min", 230.0))
            p_moy_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Moyen", 230.0))
            p_max_co = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Max", 230.0))
            strat_cond = st.selectbox("Salaire :", [f"Économique ({p_min_co:.0f} €/j)", f"Standard ({p_moy_co:.0f} €/j)", f"Premium ({p_max_co:.0f} €/j)"], key="sel_strat_cond")
            px_cond = p_min_co if "Économique" in strat_cond else (p_moy_co if "Standard" in strat_cond else p_max_co)
        with c_cond_jh:
            # Double sécurité : cherche 'jh_cond' ou 'max_cond'
            val_defaut_cond = float(donnees_modele.get("jh_cond", donnees_modele.get("max_cond", 0.0)))
            jh_cond = st.number_input("Nombre d'employés", min_value=0.0, value=val_defaut_cond, key="jh_input_cond")

        # --- 2. CONFIGURATION CHEFS ---
        st.markdown("**🧑‍💼 PROFIL : CHEFS DE CHANTIER**")
        c_chef_type, c_chef_strat, c_chef_jh = st.columns(3)
        with c_chef_type:
            type_contrat_chef = st.selectbox("Contrat :", ["CDI", "CDD"], key="type_contrat_chef")
        with c_chef_strat:
            p_min_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Min", 230.0))
            p_moy_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Moyen", 230.0))
            p_max_c = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Max", 230.0))
            strat_chef = st.selectbox("Salaire :", [f"Économique ({p_min_c:.0f} €/j)", f"Standard ({p_moy_c:.0f} €/j)", f"Premium ({p_max_c:.0f} €/j)"], key="sel_strat_chef")
            px_chef = p_min_c if "Économique" in strat_chef else (p_moy_c if "Standard" in strat_chef else p_max_c)
        with c_chef_jh:
            # Double sécurité : cherche 'jh_chef' ou 'max_chef'
            val_defaut_chef = float(donnees_modele.get("jh_chef", donnees_modele.get("max_chef", 0.0)))
            jh_chef = st.number_input("Nombre d'employés", min_value=0.0, value=val_defaut_chef, key="jh_input_chef")

        # --- 3. CONFIGURATION OUVRIERS ---
        st.markdown("**👷 PROFIL : OUVRIERS QUALIFIÉS**")
        c_ouv_type, c_ouv_strat, c_ouv_jh = st.columns(3)
        with c_ouv_type:
            type_contrat_ouv = st.selectbox("Contrat :", ["CDI", "CDD"], key="type_contrat_ouv")
        with c_ouv_strat:
            p_min_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Min", 230.0))
            p_moy_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Moyen", 230.0))
            p_max_o = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Max", 230.0))
            strat_ouv = st.selectbox("Salaire :", [f"Économique ({p_min_o:.0f} €/j)", f"Standard ({p_moy_o:.0f} €/j)", f"Premium ({p_max_o:.0f} €/j)"], key="sel_strat_ouv")
            px_ouvrier = p_min_o if "Économique" in strat_ouv else (p_moy_o if "Standard" in strat_ouv else p_max_o)
        with c_ouv_jh:
            # Double sécurité : cherche 'jh_ouvrier' ou 'max_ouvrier'
            val_defaut_ouv = float(donnees_modele.get("jh_ouvrier", donnees_modele.get("max_ouvrier", 0.0)))
            jh_ouvrier = st.number_input("Nombre d'employés", min_value=0.0, value=val_defaut_ouv, key="jh_input_ouv")

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
    # --- LOGIQUE FINALE DE SYNTHÈSE ET DE CALCUL FINANCIER DU JEU ---
    # ==============================================================================
    jours_factures_jeu = math.ceil(jours_totaux)
    total_mats_recap = float(total_mats_direct)

    # Coût de location des machines (Prix * Quantité * Jours facturés arrondis au supérieur)
    total_location_recap = 0.0
    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["Sélection de l'engin / Modèle"])
        total_location_recap = float((df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * jours_factures_jeu).sum())

    # Formules RH spécifiques : 
    # CDI : px_cond contient déjà le coût par jour calculé (Salaire mensuel / 7) dans l'Espace Direction. On applique le prorata exact.
    if "CDI" in type_contrat_cond: 
        cout_cond = jh_cond * px_cond * jours_totaux
    else: 
        cout_cond = jh_cond * px_cond * jours_factures_jeu

    if "CDI" in type_contrat_chef: 
        cout_chefs = jh_chef * px_chef * jours_totaux
    else: 
        cout_chefs = jh_chef * px_chef * jours_factures_jeu

    if "CDI" in type_contrat_ouv: 
        cout_ouvriers = jh_ouvrier * px_ouvrier * jours_totaux
    else: 
        cout_ouvriers = jh_ouvrier * px_ouvrier * jours_factures_jeu

    total_salaires_recap = float(cout_chefs + cout_ouvriers + cout_cond)

    # Totaux globaux
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

    # ==============================================================================
    # --- AFFICHAGE DU RÉCAPITULATIF FINANCIER VISUEL ---
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Global Estimé (Règles du Jeu)")
    if jours_totaux > 0 and jours_totaux != jours_factures_jeu:
        st.warning(f"⚠️ **Pénalité de temps :** Le chantier dépasse sur la journée suivante. Vous êtes facturé **{jours_factures_jeu} jours** au lieu de {jours_totaux:.2f} jours pour la location et vos CDD.")

    txt_duree_precise = f"{jours_saisis}j {heures_saisies}h {minutes_saisies}m" if jours_totaux > 0 else "0 jour"

    c_rc1, c_rc2, c_rc3, c_rc4, c_rc5, c_rc6 = st.columns(6)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires (RH)", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")
    with c_rc5: st.metric(label="⏱️ Durée du Projet", value=txt_duree_precise)
    with c_rc6: st.metric(label="📈 Rentabilité Quotidienne", value=f"{txt_gain_jour} €/j")

    if benefice_net_recap >= 0: 
        st.success(f"🟢 **Rentabilité positive :** Bénéfice de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** (ROI Global : **{roi_recap:.2f} %**)")
    else: 
        st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** soit **{txt_gain_jour} € / jour** sur **{txt_duree_precise}** (ROI Global : **{roi_recap:.2f} %**)")

    st.markdown("<br>", unsafe_allow_html=True) 

    # ==============================================================================
    # --- POP-UP DIALOG INTERACTIF : DÉTAIL DES COULISSES DU CALCUL ---
    # ==============================================================================
    @st.dialog("🔍 Rapport de Calcul et Feuille d'Insertion NoSQL")
    def confirmer_enregistrement_chantier_detaill():
        st.write("Voici la transparence complète des calculs et formules appliqués selon les règles de l'économie du jeu :")
        
        # 1. Détail de la Logique du Temps
        st.markdown("#### ⏱️ 1. Décomposition du Temps")
        st.write(f"- **Durée réelle saisie :** `{jours_saisis} jours, {heures_saisies} heures, {minutes_saisies} minutes`")
        st.write(f"- **Équivalent décimal exact :** `{jours_totaux:.4f} jours` de jeu (base 24h)")
        st.write(f"- **Forfait facturé (Location & CDD) :** `{jours_factures_jeu} jours` (Toute journée entamée est due)")

        # 2. Détail des Formules de la Masse Salariale
        st.markdown("#### 👥 2. Formules appliquées pour la Main-d'œuvre")
        st.write(f"- **Conducteurs d'engins ({type_contrat_cond}) :**")
        if "CDI" in type_contrat_cond:
            st.code(f"{jh_cond} employé(s) × {px_cond:,.2f} €/jour (prorata CDI) × {jours_totaux:.2f}j de présence = {cout_cond:,.0f} €")
        else:
            st.code(f"{jh_cond} employé(s) × {px_cond:,.2f} €/jour × {jours_factures_jeu}j due(s) = {cout_cond:,.0f} €")

        st.write(f"- **Chefs de chantier ({type_contrat_chef}) :**")
        if "CDI" in type_contrat_chef:
            st.code(f"{jh_chef} employé(s) × {px_chef:,.2f} €/jour (prorata CDI) × {jours_totaux:.2f}j de présence = {cout_chefs:,.0f} €")
        else:
            st.code(f"{jh_chef} employé(s) × {px_chef:,.2f} €/jour × {jours_factures_jeu}j due(s) = {cout_chefs:,.0f} €")

        st.write(f"- **Ouvriers qualifiés ({type_contrat_ouv}) :**")
        if "CDI" in type_contrat_ouv:
            st.code(f"{jh_ouvrier} employé(s) × {px_ouvrier:,.2f} €/jour (prorata CDI) × {jours_totaux:.2f}j de présence = {cout_ouvriers:,.0f} €")
        else:
            st.code(f"{jh_ouvrier} employé(s) × {px_ouvrier:,.2f} €/jour × {jours_factures_jeu}j due(s) = {cout_ouvriers:,.0f} €")

        # 3. Tableau Récapitulatif des variables envoyées à Firestore
        st.markdown("#### 🗂️ 3. Structure finale de la ligne NoSQL (Firebase)")
        donnees_popup = {
            "Champ technique (Firestore)": [
                "nom_chantier", "revenus", "cout_materiaux", "cout_location", 
                "cout_salaires", "depenses_totales", "benefice_net", "roi", 
                "jours (exact)", "gain_par_jour", "roi_par_jour"
            ],
            "Valeur brute insérée": [
                nom_chantier,
                f"{revenus:,.0f} €".replace(",", " "),
                f"{total_mats_recap:,.0f} €".replace(",", " "),
                f"{total_location_recap:,.0f} €".replace(",", " "),
                f"{total_salaires_recap:,.0f} €".replace(",", " "),
                f"{total_depenses_recap:,.0f} €".replace(",", " "),
                f"{benefice_net_recap:,.0f} €".replace(",", " "),
                f"{roi_recap:.2f} %",
                f"{jours_totaux:.4f} jours",
                f"{gain_par_jour_recap:,.0f} €/j".replace(",", " "),
                f"{roi_par_jour_recap:.2f} %/j"
            ]
        }
        st.table(pd.DataFrame(donnees_popup))
        
        st.warning("🚨 Confirmez-vous l'envoi de cette simulation vers l'Historique cloud de l'entreprise ?")
        
        col_pop1, col_pop2 = st.columns(2)
        with col_pop1:
            if st.button("✅ ACCEPTER & ENREGISTRER", type="primary", use_container_width=True, key="btn_popup_confirm_final_send_complet"):
                # Envoi des variables brutes et propres sur Firestore
                db.inserer_chantier(
                    nom_chantier, revenus, total_mats_recap, total_location_recap, 
                    total_salaires_recap, total_depenses_recap, benefice_net_recap, 
                    round(roi_recap, 2), float(jours_totaux), round(gain_par_jour_recap, 2), 
                    round(roi_par_jour_recap, 2)
                )
                st.toast("🚀 Simulation enregistrée avec succès sur le Cloud Firestore !")
                st.rerun()
        with col_pop2:
            if st.button("❌ ANNULER & MODIFIER", use_container_width=True, key="btn_popup_cancel_final_send_complet"):
                st.rerun()

    # --- ENCLENCHEMENT DE LA SÉCURITÉ DU FORMULAIRE ---
    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary", use_container_width=True, key="btn_principal_declencher_calcul_rentabilite"):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier: 
            st.error("⚠️ Erreur : Saisissez un nom ou un numéro de chantier valide avant d'exécuter l'insertion.")
        elif doublon_existe: 
            st.error(f"❌ Erreur NoSQL : Une fiche identique au nom de '{nom_chantier}' existe déjà dans l'historique cloud.")
        else: 
            # Si le formulaire passe les contrôles, on déploie le pop-up détaillé
            confirmer_enregistrement_chantier_detaill()
