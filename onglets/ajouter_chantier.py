# Contenu complet et validé pour : onglets/ajouter_chantier.py

import streamlit as st
import pandas as pd
import math
import database as db

# ==============================================================================
# --- 1. POPUP DE CONFIRMATION ---
# ==============================================================================
@st.dialog("🔍 Rapport de Calcul et Feuille d'Insertion NoSQL")
def popup_confirmation_enregistrement():
    inputs = st.session_state.get("temp_submit_data", {})
    if not inputs:
        st.error("Aucune donnée de simulation trouvée.")
        return

    st.write("Voici la transparence complète des calculs et formules appliqués selon les règles de l'économie du jeu :")
    
    st.markdown("#### ⏱️ 1. Décomposition du Temps")
    st.write(f"- **Durée réelle saisie :** `{inputs['jours_saisis']} jours, {inputs['heures_saisies']} heures, {inputs['minutes_saisies']} minutes`")
    st.write(f"- **Forfait facturé (Location & CDD) :** `{int(inputs['jours_factures_jeu'])} jours` (Toute journée entamée est due)")

    st.markdown("#### 👥 2. Formules appliquées pour la Main-d'œuvre")
    st.code(f"Conducteurs ({inputs['type_contrat_cond']}) : {inputs['cout_cond']:,.0f} €")
    st.code(f"Chefs ({inputs['type_contrat_chef']}) : {inputs['cout_chefs']:,.0f} €")
    st.code(f"Ouvriers ({inputs['type_contrat_ouv']}) : {inputs['cout_ouvriers']:,.0f} €")

    st.markdown("#### 🗂️ 3. Structure finale NoSQL (Firebase)")
    
    signe_benefice = f"{inputs['benefice_net_recap']:,.0f} €".replace(",", " ")
    
    donnees_popup = {
        "Champ technique (Firestore)": ["nom_chantier", "revenus", "cout_materiaux", "cout_location", "cout_salaires", "depenses_totales", "benefice_net", "roi", "gain_par_jour"],
        "Valeur brute insérée": [
            inputs['nom_chantier'], 
            f"{inputs['revenus']:,.0f} €".replace(",", " "), 
            f"{inputs['txt_mats']} €", 
            f"{inputs['txt_loc']} €", 
            f"{inputs['txt_sal']} €", 
            f"{inputs['txt_depenses']} €", 
            signe_benefice, 
            f"{inputs['roi_recap']:.2f} %", 
            f"{inputs['txt_gain_jour']} €/j"
        ]
    }
    st.table(pd.DataFrame(donnees_popup))
    
    st.warning("🚨 Confirmez-vous l'envoi de cette simulation vers l'Historique cloud de l'entreprise ?")
    col_pop1, col_pop2 = st.columns(2)
    
    with col_pop1:
        if st.button("✅ ACCEPTER & ENREGISTRER", type="primary", width="stretch"):
            db.inserer_chantier(
                inputs['nom_chantier'], inputs['revenus'], inputs['total_mats_recap'], 
                inputs['total_location_recap'], inputs['total_salaires_recap'], 
                inputs['total_depenses_recap'], inputs['benefice_net_recap'], 
                round(inputs['roi_recap'], 2), float(inputs['jours_totaux']), 
                round(inputs['gain_par_jour_recap'], 2), round(inputs['roi_par_jour_recap'], 2)
            )
            st.toast("🚀 Simulation enregistrée avec succès sur le Cloud Firestore !")
            if "temp_submit_data" in st.session_state:
                del st.session_state["temp_submit_data"]
            st.rerun()
            
    with col_pop2:
        if st.button("❌ ANNULER & MODIFIER", width="stretch"): 
            if "temp_submit_data" in st.session_state:
                del st.session_state["temp_submit_data"]
            st.rerun()

# ==============================================================================
# --- 2. FONCTION PRINCIPALE APPELÉE PAR LE FICHIER APP.PY ---
# ==============================================================================
def afficher_onglet_ajouter(SALAIRES_DB, MATERIAUX_DB, CATALOGUE_ENGINS, TYPES_ENGINS_BRUTS, CATALOGUE_CHANTIERS):
    st.subheader("Formulaire de saisie")
    
    liste_triee = ["Choisir un chantier pré-configuré..."] + sorted([k for k in CATALOGUE_CHANTIERS.keys() if k != "Choisir un chantier pré-configuré..."])
    
    if "val_revenus" not in st.session_state:
        st.session_state["val_revenus"] = 0.0
        st.session_state["val_jours"] = 0
        for k in ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]:
            st.session_state[f"val_{k}"] = 0.0

    # SÉCURITÉ : Initialisation du compteur de rafraîchissement si absent
    if "compteur_refresh_engins" not in st.session_state:
        st.session_state["compteur_refresh_engins"] = 0
    
    # --- ACTION DE RECEPTION DYNAMIQUE PAR ÉTAPES CORRIGÉE ANTI-CRASH ---
    def mise_a_jour_cache_modele():
        selection = st.session_state["select_modele_chantier_dynamique"]
        if selection == "Choisir un chantier pré-configuré...":
            return
            
        modele = CATALOGUE_CHANTIERS[selection]
        etapes_cloud = modele.get("etapes_techniques", [])
        
        # Nettoyage préventif des états d'éditeurs (sans toucher aux clés interdites rattachées directement)
        for k in ["editor_rh_data", "editor_engins_data"]:
            if k in st.session_state: 
                del st.session_state[k]
            
        # Paramètres globaux temporels et financiers
        st.session_state["val_revenus"] = float(modele.get("revenus", 0.0))
        st.session_state["val_jours"] = int(modele.get("jours_globaux", 0))
        st.session_state["val_heures"] = int(modele.get("heures_globales", 0))
        st.session_state["val_minutes"] = int(modele.get("minutes_globales", 0))
        
        # Initialisation des compteurs de matériaux globaux
        liste_mats_cles = ["sable","terre","enrobe","armature","tole","beton","panneaux","tuyaux","canalisations","poutres"]
        for mat in liste_mats_cles:
            st.session_state[f"val_{mat}"] = 0.0
            
        lignes_rh = []
        lignes_engins = []
        
        # Extraction et dispatching des données de chaque étape
        for etape in etapes_cloud:
            num_e = etape.get("num_etape", 1)
            duree_j = etape.get("duree_jours", 1)
            
            # Cumul des volumes de matériaux
            mats_etape = etape.get("materiaux", {})
            for mat_nom, qte in mats_etape.items():
                if mat_nom in liste_mats_cles:
                    st.session_state[f"val_{mat_nom}"] += float(qte)
                    
            # Reconstitution pour le tableau des Employés (RH)
            lignes_rh.append({
                "N° Étape": int(num_e),
                "Durée Étape (jours)": int(duree_j),
                "🕹️ Conducteurs": int(etape.get("jh_cond", 0)),
                "🧑‍💼 Chefs": int(etape.get("jh_chef", 0)),
                "👷 Ouvriers": int(etape.get("jh_ouvrier", 0))
            })
            
            # Reconstitution pour le tableau des Engins requis
            engins_etape = etape.get("engins", [])
            for engin in engins_etape:
                lignes_engins.append({
                    "N° Étape": int(num_e),
                    "Durée Étape (jours)": int(duree_j),
                    "Type d'engin requis": engin.get("type", "Autre"),
                    "Niveau requis": engin.get("niveau", "N1"),
                    "À louer ?": False
                })
                
        # Stockage dans des variables "caches" tampon
        st.session_state["cache_df_rh"] = pd.DataFrame(lignes_rh)
        
        # --- CORRECTION ANTY-DOUBLON ICI ---
        df_engins_brut = pd.DataFrame(lignes_engins)
        if not df_engins_brut.empty:
            # On élimine les doublons stricts basés sur l'étape, le type et le niveau requis
            st.session_state["cache_df_engins"] = df_engins_brut.drop_duplicates(
                subset=["N° Étape", "Type d'engin requis", "Niveau requis"], 
                keep="first"
            ).reset_index(drop=True)
        else:
            st.session_state["cache_df_engins"] = df_engins_brut

    # --- ACTION COMPLÉMENTAIRE CRITIQUE POUR FORCER LE RENOUVELLEMENT DE L'ÉDITEUR ---
    if "compteur_refresh_engins" not in st.session_state:
        st.session_state["compteur_refresh_engins"] = 0
    st.session_state["compteur_refresh_engins"] += 1

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
        
        st.write("⏱️ **Durée totale du chantier :**")
        c_j, c_h, c_m = st.columns(3)
        
        with c_j: jours_saisis = st.number_input("Jours", min_value=0, value=st.session_state["val_jours"], step=1)
        with c_h: heures_saisies = st.number_input("Heures", min_value=0, max_value=23, value=st.session_state.get("val_heures", 0), step=1)
        with c_m: minutes_saisies = st.number_input("Minutes", min_value=0, max_value=59, value=st.session_state.get("val_minutes", 0), step=1)


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
        
        px_cond = float(SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}_Moyen") or SALAIRES_DB.get(f"Conducteur_{type_contrat_cond}") or SALAIRES_DB.get("Conducteur") or 230.0)
        px_chef = float(SALAIRES_DB.get(f"Chef_{type_contrat_chef}_Moyen") or SALAIRES_DB.get(f"Chef_{type_contrat_chef}") or SALAIRES_DB.get("Chef") or 230.0)
        px_ouvrier = float(SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}_Moyen") or SALAIRES_DB.get(f"Ouvrier_{type_contrat_ouv}") or SALAIRES_DB.get("Ouvrier") or 230.0)

        st.info(f"💰 Tarifs Cloud : 🕹️ Cond : {px_cond:.0f}€/j | 🧑‍💼 Chef : {px_chef:.0f}€/j | 👷 Ouv : {px_ouvrier:.0f}€/j")

        st.markdown("**👥 Planification des Effectifs requis à l'Étape :**")
        df_rh_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "🕹️ Conducteurs", "🧑‍💼 Chefs", "👷 Ouvriers"])

        # Lecture depuis la variable tampon intermédiaire sécurisée contre la règle d'écriture directe
        raw_rh_state = st.session_state.get("cache_df_rh", df_rh_init)

        tableau_employes_etapes = st.data_editor(
            raw_rh_state, num_rows="dynamic", use_container_width=True, key="editor_rh_data",
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Jours", min_value=1, step=1, required=True, width="small"),
                "🕹️ Conducteurs": st.column_config.NumberColumn(f"Cond ({px_cond:.0f}€)", min_value=0, step=1, default=1, width="small"),
                "🧑‍💼 Chefs": st.column_config.NumberColumn(f"Chef ({px_chef:.0f}€)", min_value=0, step=1, default=0, width="small"),
                "👷 Ouvriers": st.column_config.NumberColumn(f"Ouv ({px_ouvrier:.0f}€)", min_value=0, step=1, default=0, width="small")
            }
        )

        st.markdown("### 🚜 --- TABLE DES ENGINS NÉCESSAIRES ---")
        df_besoins_init = pd.DataFrame(columns=["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis", "À louer ?"])
        
        # Lecture depuis la variable tampon intermédiaire pour les engins requis
        raw_engins_state = st.session_state.get("cache_df_engins", df_besoins_init)

        # Récupération de l'index de rafraîchissement
        idx_refresh = st.session_state.get("compteur_refresh_engins", 0)

        # L'éditeur possède maintenant une clé contenant l'index (ex: "editor_engins_data_3")
        engins_necessaires = st.data_editor(
            raw_engins_state, num_rows="dynamic", use_container_width=True, 
            key=f"editor_engins_data_{idx_refresh}", # <-- LA CORRECTION TECHNIQUE EST ICI
            column_config={
                "N° Étape": st.column_config.NumberColumn("N°", min_value=1, step=1, required=True, width="small"),
                "Durée Étape (jours)": st.column_config.NumberColumn("Durée (jours)", min_value=1, step=1, required=True),
                "Type d'engin requis": st.column_config.TextColumn("Type d'engin requis", disabled=True),
                "Niveau requis": st.column_config.SelectboxColumn("Niveau requis", options=["N1", "N2", "N3", "N4"], required=True),
                "À louer ?": st.column_config.CheckboxColumn("À louer ?", default=False)
            }
        )


        engins_transferes_list = []
        if engins_necessaires is not None and not engins_necessaires.empty and "À louer ?" in engins_necessaires.columns:
            df_coches = engins_necessaires[engins_necessaires["À louer ?"] == True].dropna(subset=["Type d'engin requis"])
            for _, row in df_coches.iterrows():
                type_demande = str(row["Type d'engin requis"]).strip()
                niveau_demande = str(row["Niveau requis"]).strip().lower()
                duree_etape = int(row["Durée Étape (jours)"])
                
                def nettoyer_mots(texte):
                    texte = texte.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                    for char in ["'", "-", "/", "’"]: texte = texte.replace(char, " ")
                    return [m for m in texte.split() if m not in ["pour", "de", "d", "un", "une", "le", "la", "les", "sur"]]

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
    # --- CONSOLIDATION COMPTABLE ET CALCULS GLOBAUX ---
    # ==============================================================================
    jours_factures_jeu = math.ceil(jours_totaux)
    total_mats_recap = float(total_mats_direct)

    total_location_recap = 0.0
    if engins_edites is not None and not engins_edites.empty:
        df_propres_direct = engins_edites.dropna(subset=["engin_modele"])
        total_location_recap = float((df_propres_direct["Quantité"] * df_propres_direct["Prix Location (€/jour)"] * df_propres_direct["Jours de Location"]).sum())

    cout_cond, cout_chefs, cout_ouvriers = 0.0, 0.0, 0.0
    total_jours_etapes = 0.0

    if tableau_employes_etapes is not None and not tableau_employes_etapes.empty:
        df_rh_propre = tableau_employes_etapes.dropna(subset=["N° Étape"])
        total_jours_etapes = float(df_rh_propre["Durée Étape (jours)"].sum())
        
        for _, r_rh in df_rh_propre.iterrows():
            duree_etape_reelle = float(r_rh.get("Durée Étape (jours)", 1.0))
            c_count = float(r_rh.get("🕹️ Conducteurs", 0))
            ch_count = float(r_rh.get("🧑‍💼 Chefs", 0))
            o_count = float(r_rh.get("👷 Ouvriers", 0))
            
            d_cond = duree_etape_reelle if type_contrat_cond == "CDI" else float(math.ceil(duree_etape_reelle))
            d_chef = duree_etape_reelle if type_contrat_chef == "CDI" else float(math.ceil(duree_etape_reelle))
            d_ouv  = duree_etape_reelle if type_contrat_ouv  == "CDI" else float(math.ceil(duree_etape_reelle))
            
            cout_cond += c_count * d_cond * px_cond
            cout_chefs += ch_count * d_chef * px_chef
            cout_ouvriers += o_count * d_ouv * px_ouvrier
            
    total_salaires_recap = float(cout_chefs + cout_ouvriers + cout_cond)
    total_depenses_recap = float(total_mats_recap + total_location_recap + total_salaires_recap)
    benefice_net_recap = float(revenus - total_depenses_recap)
    roi_recap = float((benefice_net_recap / total_depenses_recap) * 100 if total_depenses_recap > 0 else 0)
    
    gain_par_jour_recap = float(benefice_net_recap / jours_totaux if jours_totaux > 0 else 0.0)
    roi_par_jour_recap = float(roi_recap / jours_totaux if jours_totaux > 0 else roi_recap)

    # --- CORRECTION DE SYNTAXE ET UNIFORMISATION DU FORMAT DES JOURS ---
    txt_mats = f"{total_mats_recap:,.0f}".replace(",", " ")
    txt_loc = f"{total_location_recap:,.0f}".replace(",", " ")
    txt_sal = f"{total_salaires_recap:,.0f}".replace(",", " ")
    txt_depenses = f"{total_depenses_recap:,.0f}".replace(",", " ")
    txt_gain_jour = f"{gain_par_jour_recap:,.0f}".replace(",", " ")
    txt_benefice = f"{abs(benefice_net_recap):,.0f}".replace(",", " ")
    
    # Formatage de la Durée Générale
    txt_duree_precise = f"{jours_saisis}j {heures_saisies}h {minutes_saisies}m" if jours_totaux > 0 else "0j"
    
    # Formatage identique pour le Cumul Étape (Conversion des décimales en heures si existantes)
    jours_e_entiers = int(total_jours_etapes)
    heures_e_restantes = int(round((total_jours_etapes - jours_e_entiers) * 24))
    txt_duree_etapes = f"{jours_e_entiers}j {heures_e_restantes}h 0m"

    # --- METRICS EN BAS ---
    st.markdown("---")
    st.markdown("### 📊 Récapitulatif Global Estimé (Règles du Jeu)")
    c_rc1, c_rc2, c_rc3, c_rc4, c_rc5, c_rc6, c_rc7 = st.columns(7)
    with c_rc1: st.metric(label="🧱 Total Matériaux", value=f"{txt_mats} €")
    with c_rc2: st.metric(label="🚜 Total Location", value=f"{txt_loc} €")
    with c_rc3: st.metric(label="👥 Total Salaires", value=f"{txt_sal} €")
    with c_rc4: st.metric(label="📉 Dépenses Totales", value=f"{txt_depenses} €")
    with c_rc5: st.metric(label="⏱️ Durée Générale", value=txt_duree_precise)
    with c_rc6: st.metric(label="⚙️ Cumul Étape", value=txt_duree_etapes) # Affichage uniformisé
    with c_rc7: st.metric(label="📈 Gain / Jour", value=f"{txt_gain_jour} €/j")

    # --- REMPLACEMENT DU BLOCAGE PAR UN SIMPLE ALERT DE COMPARAISON SANS MATRICULE DE BLOC ---
    planning_incoherent = abs(jours_totaux - total_jours_etapes) > 0.05

    if planning_incoherent:
        st.warning(
            f"⚠️ **Écart de planification détecté :** La durée générale indiquée (`{txt_duree_precise}`) "
            f"diffère du cumul calculé des étapes techniques (`{txt_duree_etapes}`)."
        )
    else:
        st.success("✅ **Planning Synchrone :** La durée globale et le cumul des étapes concordent.")

    if benefice_net_recap >= 0: 
        st.success(f"🟢 **Rentabilité positive :** Bénéfice de **{txt_benefice} €** (ROI Global : **{roi_recap:.2f} %**)")
    else: 
        st.error(f"🔴 **Chantier déficitaire :** Perte de **{txt_benefice} €** (ROI Global : **{roi_recap:.2f} %**)")

    # LE BOUTON EST DÉSORMAIS TOUJOURS ACTIF (disabled=False)
    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary", use_container_width=True, disabled=False):
        df_actuel = db.charger_donnees()
        doublon_existe = False if df_actuel.empty else not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier: 
            st.error("⚠️ Erreur : Saisissez un nom de chantier valide.")
        elif doublon_existe: 
            st.error(f"❌ Erreur NoSQL : Une fiche identique au nom de '{nom_chantier}' existe déjà.")
        else:
            st.session_state["temp_submit_data"] = {
                "nom_chantier": nom_chantier, "revenus": revenus, "jours_saisis": jours_saisis,
                "heures_saisies": heures_saisies, "minutes_saisies": minutes_saisies,
                "jours_factures_jeu": jours_factures_jeu, "type_contrat_cond": type_contrat_cond,
                "type_contrat_chef": type_contrat_chef, "type_contrat_ouv": type_contrat_ouv,
                "cout_cond": cout_cond, "cout_chefs": cout_chefs, "cout_ouvriers": cout_ouvriers,
                "txt_mats": txt_mats, "txt_loc": txt_loc, "txt_sal": txt_sal, "txt_depenses": txt_depenses,
                "roi_recap": roi_recap, "txt_gain_jour": txt_gain_jour, "total_mats_recap": total_mats_recap,
                "total_location_recap": total_location_recap, "total_salaires_recap": total_salaires_recap,
                "total_depenses_recap": total_depenses_recap, "benefice_net_recap": benefice_net_recap,
                "jours_totaux": jours_totaux, "gain_par_jour_recap": gain_par_jour_recap,
                "roi_par_jour_recap": roi_par_jour_recap
            }
            st.rerun()

    if "temp_submit_data" in st.session_state:
        popup_confirmation_enregistrement()
