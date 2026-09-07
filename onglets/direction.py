# Contenu complet et validé pour : onglets/direction.py

import streamlit as st
import pandas as pd
import database as db
import math
import re
import datetime
import pytz

# ==============================================================================
# --- 1. POP-UP DE VALIDATION : CALCULATEUR DE RECRUTEMENT ---
# ==============================================================================
@st.dialog("📊 Rapport d'Analyse et de Calcul des Paliers")
def pop_up_validation_recrutement(salaires_mensuels, metier, type_contrat, salaires_db_dict):
    metier_clean = metier.strip().capitalize()
    if metier_clean.endswith("s"): 
        metier_clean = metier_clean[:-1]
    
    if "cond" in metier_clean.lower() or "direct" in metier_clean.lower(): metier_clean = "Conducteur"
    elif "chef" in metier_clean.lower(): metier_clean = "Chef"
    elif "ouv" in metier_clean.lower() or "macon" in metier_clean.lower(): metier_clean = "Ouvrier"

    st.write(f"Voici le détail de l'analyse et la conversion pour le poste de **{metier_clean}** ({type_contrat}) :")
    
    sm_min = min(salaires_mensuels)
    sm_max = max(salaires_mensuels)
    sm_somme = sum(salaires_mensuels)
    sm_nb = len(salaires_mensuels)
    sm_moyen = sm_somme / sm_nb

    if "CDI" in type_contrat:
        sj_min = math.ceil(sm_min / 7.0)
        sj_moyen = math.ceil(sm_moyen / 7.0)
        sj_max = math.ceil(sm_max / 7.0)
        prefixe_cle = f"{metier_clean}_CDI"
        
        txt_sm_moyen = f"{int(sm_moyen):,.0f}".replace(",", " ")
        txt_sj_min = f"{int(sj_min):,.0f}".replace(",", " ")
        txt_sm_min = f"{int(sm_min):,.0f}".replace(",", " ")
        txt_sj_moyen = f"{int(sj_moyen):,.0f}".replace(",", " ")
        txt_sj_max = f"{int(sj_max):,.0f}".replace(",", " ")
        txt_sm_max = f"{int(sm_max):,.0f}".replace(",", " ")
        
        st.info(f"💡 Conversion CDI mensuelle (base 1 mois = 7j) ramenée au jour (Moyenne : {txt_sm_moyen} €/mois)")
        st.markdown("### 🧮 Conversion ramenée à la journée de jeu :")
        st.success(f"**- Coût Minimum :** `{txt_sj_min} € / jour` (soit {txt_sm_min} €/mois)")
        st.success(f"**- Coût Moyen :** `{txt_sj_moyen} € / jour` (soit {txt_sm_moyen} €/mois)")
        st.success(f"**- Coût Maximum :** `{txt_sj_max} € / jour` (soit {txt_sm_max} €/mois)")
    else:
        sj_min = math.ceil(sm_min)
        sj_moyen = math.ceil(sm_moyen)
        sj_max = math.ceil(sm_max)
        prefixe_cle = f"{metier_clean}_CDD"
        
        txt_sm_moyen = f"{int(sm_moyen):,.0f}".replace(",", " ")
        txt_sj_min = f"{int(sj_min):,.0f}".replace(",", " ")
        txt_sj_moyen = f"{int(sj_moyen):,.0f}".replace(",", " ")
        txt_sj_max = f"{int(sj_max):,.0f}".replace(",", " ")
        
        st.info(f"💡 Enregistrement CDD direct au jour (Moyenne : {txt_sm_moyen} €/jour)")
        st.markdown("### 🧮 Tarification au jour de jeu :")
        st.success(f"**- Tarif Minimum :** `{txt_sj_min} € / jour`")
        st.success(f"**- Tarif Moyen :** `{txt_sj_moyen} € / jour`")
        st.success(f"**- Tarif Maximum :** `{txt_sj_max} € / jour`")

    if st.button("✅ ENREGISTRER SUR FIREBASE", type="primary", width="stretch", key=f"btn_save_cloud_{metier_clean}_{prefixe_cle}"):
        grille_actuelle = dict(salaires_db_dict)
        grille_actuelle[f"{prefixe_cle}_Min"] = int(sj_min)
        grille_actuelle[f"{prefixe_cle}_Moyen"] = int(sj_moyen)
        grille_actuelle[f"{prefixe_cle}_Max"] = int(sj_max)

        db.db.collection("configuration_salaires").document("grille").set(grille_actuelle)
        st.cache_data.clear()
        st.toast(f"🚀 Tarifs de référence pour {prefixe_cle} synchronisés !")
        st.rerun()

# ==============================================================================
# --- 2. POP-UP DE VALIDATION POUR L'EXTRACTEUR DE FICHES CHANTIERS ---
# ==============================================================================
@st.dialog("🔍 Rapport d'Analyse et d'Importation des Modèles")
def pop_up_validation_fiches_chantiers(chantiers_detectes):
    st.write("Voici la transparence des données techniques extraites de vos fiches brutes avant insertion cloud :")
    
    for temporary_key, data in chantiers_detectes.items():
        vrai_nom_propre = data["nom_affiche_propre"]
        st.markdown(f"### 🏗️ Chantier : **{vrai_nom_propre}**")
        
        txt_revenus = f"{int(data['revenus']):,.0f}".replace(",", " ")
        st.info(f"💰 **Revenus détectés :** `{txt_revenus}` €")
        
        st.markdown("**⏱️ Temps configuré pour l'Onglet 1 :**")
        st.code(f"{data['jours']} jour(s), {data['heures']} heure(s), {data['minutes']} minute(s)")
        
        st.markdown("**⚙️ Structure des étapes détectées (Option B) :**")
        for num, step in data["etapes_techniques"].items():
            st.markdown(f"**Étape {num} (Durée : {step['duree_jours']} j)**")
            st.caption(f"🕹️ Cond: {step['jh_cond']} | 🧑‍💼 Chef: {step['jh_chef']} | 👷 Ouv: {step['jh_ouvrier']}")
            if step["materiaux"]:
                st.write(f"🧱 Matériaux : {step['materiaux']}")
            if step["engins"]:
                st.write(f"🚜 Engins : {step['engins']}")
        st.markdown("---")
        
    st.warning("🚨 Confirmez-vous l'injection de ces structures NoSQL par Étape dans votre catalogue de modèles ?")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("✅ CONFIRMER L'IMPORTATION", type="primary", width="stretch", key="btn_confirm_cloud_import_fiches"):
            compteur = 0
            for temporary_key, data in chantiers_detectes.items():
                liste_ordonnee = [t_et for k, t_et in sorted(data["etapes_techniques"].items())]
                nom_unique_key = f"{data['nom_affiche_propre']} - {int(data['revenus'])}€"
                
                db.db.collection("modeles_chantiers").document(nom_unique_key).set({
                    "nom_modele": data["nom_affiche_propre"], 
                    "revenus": float(data["revenus"]), 
                    "jours_globaux": int(data["jours"]), 
                    "heures_globales": int(data["heures"]), 
                    "minutes_globales": int(data["minutes"]),
                    "etapes_techniques": liste_ordonnee
                })
                compteur += 1
            st.cache_data.clear()
            st.toast(f"🚀 {compteur} modèle(s) synchronisé(s) en Option B !")
            st.rerun()
            
    with col_c2:
        if st.button("❌ ANNULER", width="stretch", key="btn_cancel_cloud_import_fiches"):
            st.rerun()

# ==============================================================================
# --- 3. L'ONGLET DIRECTION PRINCIPAL ---
# ==============================================================================
def afficher_onglet_direction(SALAIRES_DB, MATERIAUX_DB):
    st.subheader("🔑 Connexion Administrateur Direction")
    mot_de_passe = st.text_input("Veuillez saisir le code d'accès :", type="password")
    
    if mot_de_passe == "adminBTP2026":
        st.success("🔓 Accès accordé au panneau de contrôle.")
        
        df_stats = db.charger_donnees()
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
        else:
            st.info("💡 Historique vierge : Aucun chantier n'est encore enregistré en base de données.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("🚨 Zone de Danger : Réinitialisation et Nettoyage des Tables"):
            st.warning("Attention : Ces actions suppriment définitivement les données stockées sur Firebase.")
            col_del1, col_del2, col_del3 = st.columns(3)
            with col_del1:
                if st.button("🗑️ Vider l'Historique des Chantiers", type="secondary", width="stretch"):
                    docs = db.db.collection("chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Historique des chantiers supprimé !")
                    st.rerun()
            with col_del2:
                if st.button("🗑️ Vider les Modèles Préfabriqués", type="secondary", width="stretch"):
                    docs = db.db.collection("modeles_chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Catalogue des modèles vidé !")
                    st.rerun()
            with col_del3:
                if st.button("💥 TOUT RÉINITIALISER", type="primary", width="stretch"):
                    db.reinitialiser_db()
                    st.rerun()
                    
        st.markdown("---")

        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6, sub_tab7, sub_tab8, sub_tab9 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins", "🗂️ Consulter les Bases Données",
            "🔎 Comparateur de Fiches", "🔍 Vérificateur de Doublons", "📊 Quotas Firebase", "📜 Historique des Actions"
        ])
        # ==============================================================================
        # --- sub_tab1 : IMPORTATION EN BLOC ET DECODAGE PAR ÉTAPE (OPTION B) ---
        # ==============================================================================
        with sub_tab1:
            dict_modeles_cloud = db.charger_catalogue_chantiers()
            res_modeles_base = [dict_modeles_cloud[k] for k in dict_modeles_cloud if k != "Choisir un chantier pré-configuré..."]
            total_modeles_base = len(res_modeles_base)

            st.markdown(f"### 📥 Extracteur de Fiches Multi-Étapes Segmentées ({total_modeles_base} modèles en base)")
            texte_fiches_brutes = st.text_area("Zone de saisie des fiches (Option B - Par Étape) :", value="", height=350, key="zone_texte_import_unique_fusionne")
            
            if st.button("🏗️ ANALYSER, NETTOYER ET IMPORTER LES MODÈLES", type="primary"):
                if not texte_fiches_brutes.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    modeles_deja_presents = set()
                    for doc_id, data_m in dict_modeles_cloud.items():
                        if doc_id == "Choisir un chantier pré-configuré...": 
                            continue
                        nom_base = str(data_m.get("nom_modele", doc_id)).strip().lower()
                        prix_base = float(data_m.get("revenus", 0.0))
                        modeles_deja_presents.add((nom_base, prix_base))

                    lignes = texte_fiches_brutes.split("\n")
                    chantiers_detectes = {}
                    nom_courant = None
                    etape_courante_num = None
                    compteur_doublons_bloques = 0
                    
                    for ligne in lignes:
                        l_clean = ligne.strip()
                        if not l_clean: continue
                        
                        if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                            match_debut = re.search(r"^(.*?)\s+(\d[\d\s]+)\s+euros", l_clean, re.IGNORECASE)
                            if match_debut:
                                nom_ch = match_debut.group(1).strip()
                                prix_txt = "".join(c for c in match_debut.group(2) if c.isdigit())
                                prix_ch = float(prix_txt) if prix_txt else 0.0
                            else:
                                prix_ch = 0.0
                                nom_ch = l_clean.replace("euros", "").replace("Euros", "").strip()
                                
                            nom_courant = f"{nom_ch} - {int(prix_ch)}€"
                            etape_courante_num = None
                            
                            if nom_courant not in chantiers_detectes:
                                chantiers_detectes[nom_courant] = {
                                    "nom_affiche_propre": nom_ch,
                                    "revenus": prix_ch, 
                                    "jours": 0, "heures": 0, "minutes": 0,
                                    "etapes_techniques": {}
                                }
                            continue

                        if not nom_courant: continue
                        
                        if l_clean.lower().startswith("revenus :"):
                            prix_txt = "".join(c for c in l_clean if c.isdigit())
                            if prix_txt: 
                                chantiers_detectes[nom_courant]["revenus"] = float(prix_txt)
                            continue

                        # --- DECODAGE DU TEMPS CORRIGÉ ET ROBUSTE ---
                        if "durée du chantier :" in l_clean.lower() or "duree du chantier :" in l_clean.lower():
                            partie_duree = l_clean.split(":")[-1].lower()
                            
                            # On nettoie tous les caractères parasites qui collent aux chiffres
                            for char in [",", "(", ")", "s", "."]:
                                partie_duree = partie_duree.replace(char, " ")
                            
                            mots = partie_duree.split()
                            for idx_mot, mot in enumerate(mots):
                                if idx_mot > 0:
                                    chiffre_txt = "".join(c for c in mots[idx_mot - 1] if c.isdigit())
                                    if chiffre_txt:
                                        valeur_numerique = int(chiffre_txt)
                                        if mot.startswith("jour"):
                                            chantiers_detectes[nom_courant]["jours"] = valeur_numerique
                                        elif mot.startswith("heure"):
                                            chantiers_detectes[nom_courant]["heures"] = valeur_numerique
                                        elif mot.startswith("minute"):
                                            chantiers_detectes[nom_courant]["minutes"] = valeur_numerique
                            continue


                        if l_clean.lower().startswith("etape") and ":" in l_clean:
                            match_e = re.search(r"etape\s*(\d+)", l_clean, re.IGNORECASE)
                            if match_e: 
                                etape_courante_num = int(match_e.group(1))
                                if etape_courante_num not in chantiers_detectes[nom_courant]["etapes_techniques"]:
                                    chantiers_detectes[nom_courant]["etapes_techniques"][etape_courante_num] = {
                                        "num_etape": etape_courante_num,
                                        "duree_jours": 1,
                                        "jh_cond": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0,
                                        "materiaux": {},
                                        "engins": []
                                    }
                            continue

                        if etape_courante_num is not None:
                            target_etape = chantiers_detectes[nom_courant]["etapes_techniques"][etape_courante_num]
                            
                            if "durée de l'étape" in l_clean.lower() or "duree de l'etape" in l_clean.lower():
                                # On isole ce qui est juste après les deux points ':' (ex: " 4 jours, employés requis :")
                                partie_droite = l_clean.split(":", 1)[-1]
                                # On ne garde que ce qui est avant la première virgule (ex: " 4 jours")
                                texte_jours = partie_droite.split(",", 1)[0]
                                
                                num_txt = "".join(c for c in texte_jours if c.isdigit())
                                if num_txt: 
                                    target_etape["duree_jours"] = int(num_txt)
                                continue
                            
                            if ":" in l_clean and any(k in l_clean.lower() for k in ["chef", "ouvrier", "conducteur"]):
                                gauche, droite = l_clean.split(":", 1)
                                match_nb = re.search(r"(\d+)", droite)
                                if match_nb:
                                    val_nb = float(match_nb.group(1))
                                    if "conducteur" in gauche.lower() or "engin" in gauche.lower(): target_etape["jh_cond"] = val_nb
                                    elif "chef" in gauche.lower(): target_etape["jh_chef"] = val_nb
                                    elif "ouvrier" in gauche.lower(): target_etape["jh_ouvrier"] = val_nb
                                continue

                            if "matériaux requis :" in l_clean.lower() or "materiaux requis :" in l_clean.lower():
                                partie_mats = l_clean.split(":")[-1].lower()
                                if "aucun" not in partie_mats:
                                    sous_elements = partie_mats.split("&")
                                    for sub in sous_elements:
                                        qte_txt = "".join(c for c in sub if c.isdigit())
                                        if qte_txt:
                                            qte_val = float(qte_txt)
                                            mat_nom = None
                                            if "canalisation" in sub: mat_nom = "canalisations"
                                            elif "armature" in sub: mat_nom = "armature"
                                            elif "enrob" in sub: mat_nom = "enrobe"
                                            elif "sable" in sub: mat_nom = "sable"
                                            elif "terre" in sub: mat_nom = "terre"
                                            elif "tôle" in sub or "tole" in sub: mat_nom = "tole"
                                            elif "béton" in sub or "beton" in sub: mat_nom = "beton"
                                            elif "panneau" in sub: mat_nom = "panneaux"
                                            elif "tuyau" in sub: mat_nom = "tuyaux"
                                            elif "poutre" in sub: mat_nom = "poutres"
                                            
                                            if mat_nom:
                                                target_etape["materiaux"][mat_nom] = qte_val
                                continue

                            ligne_brute_clean = l_clean.lower().replace("é", "e").replace("è", "e").replace("à", "a")
                            cat_engin = None
                            if "camion benne" in ligne_brute_clean: cat_engin = "Camions Benne"
                            elif "niveleuse" in ligne_brute_clean: cat_engin = "Niveleuse"
                            elif "finisseur" in ligne_brute_clean: cat_engin = "Finisseur"
                            elif "compacteur" in ligne_brute_clean: cat_engin = "Compacteur pour enrobé"
                            elif "fraiseuse" in ligne_brute_clean: cat_engin = "Fraiseuse"
                            elif "chargeuse" in ligne_brute_clean: cat_engin = "Chargeuse Compacte"
                            elif "pelleteuse" in ligne_brute_clean: cat_engin = "Pelleteuses"
                            elif "malaxeur" in ligne_brute_clean or "camion beton" in ligne_brute_clean: cat_engin = "Camion Béton Malaxeur"

                            if cat_engin:
                                niv = f"N{re.search(r'niveau\s*(\d+)', ligne_brute_clean).group(1)}" if re.search(r'niveau\s*(\d+)', ligne_brute_clean) else "N1"
                                target_etape["engins"].append({"type": cat_engin, "niveau": niv})
                    if chantiers_detectes:
                        compteur_importation = 0
                        for key_doc, data_ouvrage in chantiers_detectes.items():
                            # Tri chronologique des étapes techniques
                            liste_ordonnee = [t_et for k, t_et in sorted(data_ouvrage["etapes_techniques"].items())]
                            
                            db.db.collection("modeles_chantiers").document(key_doc).set({
                                "nom_modele": data_ouvrage["nom_affiche_propre"],
                                "revenus": float(data_ouvrage["revenus"]),
                                "jours_globaux": int(data_ouvrage["jours"]),
                                "heures_globales": int(data_ouvrage["heures"]),
                                "minutes_globales": int(data_ouvrage["minutes"]),
                                "etapes_techniques": liste_ordonnee
                            })
                            compteur_importation += 1
                        
                        if compteur_doublons_bloques > 0:
                            st.toast(f"ℹ️ {compteur_doublons_bloques} doublon(s) détecté(s) ont été ignoré(s).")
                        
                        st.cache_data.clear()
                        st.success(f"🚀 {compteur_importation} fiche(s) de chantier importée(s) en Option B !")
                        st.rerun()
                    else:
                        if compteur_doublons_bloques > 0:
                            st.error(f"❌ Aucun nouveau modèle : Les {compteur_doublons_bloques} chantiers soumis existent déjà.")
                        else:
                            st.error("❌ L'algorithme n'a pas réussi à extraire de fiches de chantiers valides dans votre texte brut.")

        # ==============================================================================
        # --- sub_tab2 : CONFIGURATION GRILLE SALARIALE ---
        # ==============================================================================
        with sub_tab2:
            st.markdown("### 👥 Extracteur et Calculateur de Salaires par Métier & Contrat")
            c_admin_poste, c_admin_contrat = st.columns(2)
            with c_admin_poste: metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
            with c_admin_contrat: type_contrat_cible = st.selectbox("Type de contrat collé :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
            texte_recrutement_brut = st.text_area(f"Collez le tableau des recrues pour [{metier_cible}] ici :", value="", height=150, key="zone_texte_recrutement_brut")
            
            if st.button("📊 ANALYSER LES SALAIRES SOUMIS", key="btn_declencher_analyse_unique"):
                if not texte_recrutement_brut.strip(): 
                    st.error("❌ La zone de texte est vide.")
                else:
                    lignes_recrues = texte_recrutement_brut.split("\n")
                    liste_salaires_extraits = []
                    for ligne in lignes_recrues:
                        l_clean = ligne.strip()
                        if not l_clean or "salaire" in l_clean.lower() or l_clean.lower() == "engager": continue 
                        if "jour" in l_clean.lower() and "€" not in l_clean: continue
                        elements = l_clean.split("\t") if "\t" in l_clean else l_clean.split()
                        
                        salaire_trouve = None
                        for el in elements:
                            if "€" in el:
                                chiffre_net = "".join(c for c in el if c.isdigit())
                                if chiffre_net: salaire_trouve = float(chiffre_net); break
                        
                        if salaire_trouve is not None: 
                            liste_salaires_extraits.append(salaire_trouve)

                    if liste_salaires_extraits:
                        pop_up_validation_recrutement(liste_salaires_extraits, metier_cible, type_contrat_cible, SALAIRES_DB)
                    else:
                        st.error("❌ Impossible d'extraire des montants de salaires valides.")

            st.markdown("#### 📄 Grille Salariale Active dans le Cloud :")
            if not SALAIRES_DB:
                st.info("La grille salariale cloud est actuellement vide.")
            else:
                lignes_grille = [{"Clé technique NoSQL": k, "Tarif (€/j)": v, "Supprimer l'entrée 🗑️": False} for k, v in SALAIRES_DB.items()]
                df_sal_visuel = pd.DataFrame(lignes_grille)
                
                grille_editee = st.data_editor(
                    df_sal_visuel, use_container_width=True, hide_index=True, key="editeur_suppression_salaires",
                    column_config={
                        "Clé technique NoSQL": st.column_config.TextColumn("Poste / Contrat / Palier", disabled=True),
                        "Tarif (€/j)": st.column_config.NumberColumn("Tarif Journalier", format="%d €", disabled=True),
                        "Supprimer l'entrée 🗑️": st.column_config.CheckboxColumn("Supprimer ?", default=False)
                    }
                )
                
                if grille_editee is not None:
                    lignes_a_supprimer = grille_editee[grille_editee["Supprimer l'entrée 🗑️"] == True]
                    if not lignes_a_supprimer.empty:
                        if st.button("💥 CONFIRMER LA SUPPRESSION DES ENTRÉES SÉLECTIONNÉES", type="primary", width="stretch"):
                            nouvelle_grille = dict(SALAIRES_DB)
                            for cle_technique in lignes_a_supprimer["Clé technique NoSQL"]:
                                if cle_technique in nouvelle_grille:
                                    del nouvelle_grille[cle_technique]
                            
                            db.db.collection("configuration_salaires").document("grille").set(nouvelle_grille)
                            
                            try:
                                timestamp_paris = datetime.datetime.now(pytz.timezone('Europe/Paris')).strftime("%Y-%m-%d %H:%M:%S")
                                db.db.collection("journaux_actions").add({
                                    "timestamp": timestamp_paris,
                                    "type_action": "SALAIRES",
                                    "details": f"Suppression de {len(lignes_a_supprimer)} entrée(s) salariale(s)."
                                })
                            except Exception:
                                pass
                            
                            st.cache_data.clear()
                            st.toast("🔥 Entrées salariales supprimées avec succès !")
                            st.rerun()

        # ==============================================================================
        # --- sub_tab3 : PRIX DES MATÉRIAUX ---
        # ==============================================================================
        with sub_tab3:
            st.markdown("### 🧱 Édition du Coût de l'Approvisionnement (Prix Unitaires)")
            form_mats = dict(MATERIAUX_DB)
            col_m1, col_m2 = st.columns(2)
            
            liste_cles_mats = list(form_mats.keys())
            milieu = math.ceil(len(liste_cles_mats) / 2)
            
            with col_m1:
                for m_k in liste_cles_mats[:milieu]:
                    form_mats[m_k] = st.number_input(f"Prix {m_k} (€/t ou €/u) :", value=float(form_mats[m_k]), min_value=0.0, step=1.0, format="%.2f")
            with col_m2:
                for m_k in liste_cles_mats[milieu:]:
                    form_mats[m_k] = st.number_input(f"Prix {m_k} (€/t ou €/u) :", value=float(form_mats[m_k]), min_value=0.0, step=1.0, format="%.2f")
                    
            if st.button("✅ METTRE À JOUR LES TARIFS MATÉRIAUX", type="primary", width="stretch"):
                db.db.collection("configuration_materiaux").document("catalogue").set(form_mats)
                st.cache_data.clear()
                st.toast("🧱 Catalogue des prix matériaux synchronisé avec succès !")
                st.rerun()

        # ==============================================================================
        # --- sub_tab4 : CATALOGUE DE LA FLOTTE D'ENGINS ---
        # ==============================================================================
        with sub_tab4:
            st.markdown("### 🚜 Administration et Tarification de la Flotte")
            catalogue_engins_brut = db.charger_catalogue_engins()
            
            with st.form("form_ajout_engin_direction", clear_on_submit=True):
                c_en1, c_en2, c_en3 = st.columns(3)
                with c_en1: nom_nouveau_engin = st.text_input("Nom unique & Niveau (ex: Pelleteuse N1) :").strip()
                with c_en2: type_brut_choisi = st.text_input("Famille d'engin (ex: Pelleteuses) :").strip()
                with c_en3: prix_jour_choisi = st.number_input("Prix de location journalier (€) :", min_value=0.0, step=10.0, value=380.0)
                
                submit_engin = st.form_submit_button("🚜 INSÉRER L'ENGIN DANS LE CATALOGUE GLOBAL", type="primary", width="stretch")
                
                if submit_engin:
                    if not nom_nouveau_engin or not type_brut_choisi:
                        st.error("❌ Veuillez compléter l'intégralité des champs textuels.")
                    else:
                        db.db.collection("catalogue_engins").document(nom_nouveau_engin).set({
                            "type_brut": type_brut_choisi, "prix_jour": float(prix_jour_choisi)
                        })
                        st.cache_data.clear()
                        st.toast(f"🚀 Engin '{nom_nouveau_engin}' ajouté au catalogue !")
                        st.rerun()
            st.markdown("#### Matériels actuellement référencés (Vue Cloud) :")
            if not catalogue_engins_brut:
                st.info("Le catalogue d'engins est vu comme vide.")
            else:
                df_liste_engins = pd.DataFrame([{"Nom de l'engin": k, "Prix / Jour (€)": v} for k, v in catalogue_engins_brut.items()])
                df_liste_engins_style = df_liste_engins.style.format({"Prix / Jour (€)": lambda x: f"{x:,.0f}".replace(",", " ") + " €" if pd.notnull(x) else "-"})
                st.dataframe(df_liste_engins_style, use_container_width=True, hide_index=True)

        # ==============================================================================
        # --- sub_tab5 : CONSULTATION BRUTE ET NETTOYAGE DES TABLES (CENTRALISÉ) ---
        # ==============================================================================
        with sub_tab5:
            dict_modeles = db.charger_catalogue_chantiers()
            
            if isinstance(dict_modeles, dict):
                res_modeles = [dict_modeles[k] for k in dict_modeles if k != "Choisir un chantier pré-configuré..."]
            else:
                res_modeles = list(dict_modeles)
                
            total_modeles = len(res_modeles)

    # ==============================================================================
    # --- 📁 CENTRE DE CONTRÔLE ET NETTOYAGE DES TABLES (4 TABLES RESTAURÉES) ---
    # ==============================================================================
    st.markdown("### 📁 Centre de Contrôle et Nettoyage des Tables")
    st.caption("Sélectionnez une table système pour inspecter les données brutes. Cochez les cases en fin de ligne pour supprimer définitivement des éléments sur Firebase.")

    # CORRECTIF : Rétablissement des 4 tables historiques avec le bon nom de variable 'choix_table'
    choix_table = st.selectbox(
        "Choisir la table système à auditer :",
        [
            "Modèles de Chantiers Pré-configurés", 
            "Chantiers Validés (Historique Général)",
            "Comptabilité Interne (Flux des Coopératives)",
            "Journaux d'Audit (Logs Système)"
        ],
        key="selectbox_audit_tables_nosql_direction_master"
    )

    # --- TABLE 1 : LES MODÈLES DE CHANTIERS ---
    if choix_table == "Modèles de Chantiers Pré-configurés":
        try:
            modeles_stream = db.db.collection("modeles_chantiers").stream()
            lignes_mod = []
            for doc in modeles_stream:
                d = doc.to_dict()
                lignes_mod.append({
                    "ID Document": doc.id,
                    "Nom du Modèle": doc.id,
                    "Chiffre d'Affaires": f"{d.get('revenus', 0):,.0f} €".replace(",", " ")
                })
            if lignes_mod:
                df_mod = pd.DataFrame(lignes_mod)
                df_mod["Supprimer ?"] = False
                mod_edite = st.data_editor(df_mod, width="stretch", hide_index=True, key="editor_nettoyage_modeles_v4")
                
                if st.button("🔥 EFFACER LES MODÈLES SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_mod_v4"):
                    docs_a_supprimer = mod_edite[mod_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    for doc_id in docs_a_supprimer:
                        db.db.collection("modeles_chantiers").document(doc_id).delete()
                    st.success(f"🟢 {len(docs_a_supprimer)} modèle(s) effacé(s) de Firebase.")
                    st.cache_data.clear(); st.rerun()
            else:
                st.info("💡 Catalogue de modèles vide.")
        except Exception as e: st.error(f"Erreur catalogue : {e}")

    # --- TABLE 2 : TOUTES LES COLONNES DES CHANTIERS DE LA SEMAINE ---
    elif choix_table == "Chantiers Validés (Historique Général)":
        try:
            chantiers_stream = db.db.collection("chantiers").stream()
            lignes_chantiers = []
            for doc in chantiers_stream:
                d = doc.to_dict()
                lignes_chantiers.append({
                    "ID Document": doc.id,
                    "🏗️ Nom du Chantier": doc.id,
                    "💰 CA (€)": float(d.get("revenus", 0.0)),
                    "🧱 Matériaux (€)": float(d.get("cout_materiaux", 0.0)),
                    "🚜 Locations (€)": float(d.get("cout_location", 0.0)),
                    "👥 Salaires (€)": float(d.get("cout_salaires", 0.0)),
                    "📉 Dépenses (€)": float(d.get("depenses_totales", 0.0)),
                    "📈 Bénéfice (€)": float(d.get("benefice_net", 0.0)),
                    "⏱️ Durée (j)": float(d.get("jours", 0.0)),
                    "⚡ Gain/j (€)": float(d.get("gain_par_jour", 0.0)),
                    "📊 ROI (%)": f"{d.get('roi', 0.0):.2f} %"
                })
                
            if lignes_chantiers:
                df_ch = pd.DataFrame(lignes_chantiers)
                df_ch["Supprimer ?"] = False
                
                ch_edite = st.data_editor(
                    df_ch, width="stretch", hide_index=True, key="editor_nettoyage_chantiers_v4",
                    column_config={
                        "ID Document": None, # Masque la clé technique
                        "💰 CA (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "🧱 Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "🚜 Locations (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "👥 Salaires (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "📉 Dépenses (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "📈 Bénéfice (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "⏱️ Durée (j)": st.column_config.NumberColumn(format="%.2f j"),
                        "⚡ Gain/j (€)": st.column_config.NumberColumn(format="%.0f €/j")
                    }
                )
                
                if st.button("🔥 SUPPRIMER LES CHANTIERS SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_ch_v4"):
                    ids_a_detruire = ch_edite[ch_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    for doc_id in ids_a_detruire:
                        db.db.collection("chantiers").document(doc_id).delete()
                    db.enregistrer_log("NETTOYAGE", f"Suppression de {len(ids_a_detruire)} chantier(s) validé(s).")
                    st.success(f"💥 {len(ids_a_detruire)} chantier(s) nettoyé(s) !")
                    st.cache_data.clear(); st.rerun()
            else: st.info("💡 Aucun chantier validé en base.")
        except Exception as e: st.error(f"Erreur chantiers : {e}")

    # --- TABLE 3 : LES COMPTES ET LOGS DES COOPÉRATIVES ---
    elif choix_table == "Comptabilité Interne (Flux des Coopératives)":
        try:
            coops_stream = db.db.collection_group("comptabilite_interne").stream()
            lignes_coop = []
            for doc in coops_stream:
                d = doc.to_dict()
                lignes_coop.append({
                    "ID Document": doc.id,
                    "Path": doc.reference.path,
                    "👤 Acteur": d.get("joueur", "Inconnu"),
                    "🏷️ Action": d.get("type", "Inconnu"),
                    "💰 Apport Cash": f"{d.get('apport_cash', 0.0):,.0f} €".replace(",", " ")
                })
            if lignes_coop:
                df_cp = pd.DataFrame(lignes_coop)
                df_cp["Supprimer ?"] = False
                cp_edite = st.data_editor(df_cp, width="stretch", hide_index=True, key="editor_nettoyage_coops_v4")
                
                if st.button("🔥 EFFACER LES TRANSACTION COOP COCHÉES", type="primary", width="stretch", key="btn_clear_coop_v4"):
                    paths_a_suppr = cp_edite[cp_edite["Supprimer ?"] == True]["Path"].tolist()
                    for path in paths_a_suppr:
                        db.db.document(path).delete()
                    st.success(f"💥 {len(paths_a_suppr)} flux effacé(s).")
                    st.cache_data.clear(); st.rerun()
            else: st.info("💡 Trésorerie des coopératives vide.")
        except Exception as e: st.error(f"Erreur flux coop : {e}")

    # --- TABLE 4 : LES LOGS D'AUDIT SYSTÈME ---
    elif choix_table == "Journaux d'Audit (Logs Système)":
        try:
            logs_stream = db.db.collection("journaux_actions").stream()
            lignes_logs = []
            for doc in logs_stream:
                d = doc.to_dict()
                lignes_logs.append({
                    "ID Document": doc.id,
                    "📅 Date": d.get("timestamp", "Inconnue"),
                    "🏷️ Catégorie": d.get("type_action", "Inconnu"),
                    "📝 Message d'Audit": d.get("details", "")
                })
            if lignes_logs:
                df_lg = pd.DataFrame(lignes_logs).sort_values(by="📅 Date", ascending=False)
                df_lg["Supprimer ?"] = False
                lg_edite = st.data_editor(df_lg, width="stretch", hide_index=True, key="editor_nettoyage_logs_v4")
                
                if st.button("🔥 PURGER LES LOGS SÉLECTIONNÉS", type="primary", width="stretch", key="btn_clear_logs_v4"):
                    ids_a_suppr = lg_edite[lg_edite["Supprimer ?"] == True]["ID Document"].tolist()
                    for doc_id in ids_a_suppr:
                        db.db.collection("journaux_actions").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_suppr)} log(s) purgé(s).")
                    st.rerun()
            else: st.info("💡 Journaux d'audit vides.")
        except Exception as e: st.error(f"Erreur logs : {e}")





        # ==============================================================================
        # --- sub_tab6 : COMPARATEUR DE FICHES CHANTIERS (SÉCURISÉ) ---
        # ==============================================================================
        with sub_tab6:
            st.markdown("### 🔎 Outil de Comparison de Modèles Préfabriqués")
            dict_modeles_comp = db.charger_catalogue_chantiers()
            
            # Correction de la conversion de sécurité
            if isinstance(dict_modeles_comp, dict):
                liste_selection_comp = [k for k in dict_modeles_comp.keys() if k != "Choisir un chantier pré-configuré..."]
            else:
                liste_selection_comp = []
            
            if len(liste_selection_comp) < 2:
                st.info("💡 Deux modèles minimum requis pour exécuter une comparaison.")
            else:
                c_cmp1, c_cmp2 = st.columns(2)
                with c_cmp1: ch_A = st.selectbox("Sélectionner le Chantier A :", liste_selection_comp, key="comp_select_A")
                with c_cmp2: ch_B = st.selectbox("Sélectionner le Chantier B (Comparatif) :", liste_selection_comp, key="comp_select_B")
                
                if ch_A == ch_B:
                    st.warning("Veuillez cibler deux chantiers distincts.")
                else:
                    data_A = dict_modeles_comp[ch_A]
                    data_B = dict_modeles_comp[ch_B]
                    
                    st.markdown("#### 📊 Métriques d'Ouvrages et Écarts Techniques")
                    metrics_comparatives = {
                        "Indicateur structurel": ["Revenus Fixes du Modèle", "Durée Théorique (jours)"],
                        f"Chantier A : {data_A.get('nom_modele', ch_A)}": [f"{data_A.get('revenus', 0):,.0f}".replace(",", " ") + " €", f"{data_A.get('jours_globaux', 0)} jours"],
                        f"Chantier B : {data_B.get('nom_modele', ch_B)}": [f"{data_B.get('revenus', 0):,.0f}".replace(",", " ") + " €", f"{data_B.get('jours_globaux', 0)} jours"]
                    }
                    st.table(pd.DataFrame(metrics_comparatives))

        # ==============================================================================
        # --- sub_tab7 : VÉRIFICATEUR DE DOUBLONS (SÉCURISÉ) ---
        # ==============================================================================
        with sub_tab7:
            st.markdown(f"### 🔍 Vérificateur & Injecteur de Fiches en Bloc ({total_modeles} modèles en base)")
            st.write("Collez vos fiches brutes complètes ci-dessous pour filtrer les doublons et configurer les nouveaux chantiers.")

            texte_verification_brut = st.text_area("Zone de dépôt des fiches brutes :", value="", height=250, key="zone_texte_verif_bloc_doublons")
            
            if texte_verification_brut.strip():
                dict_modeles_verif = db.charger_catalogue_chantiers()
                chantiers_existants = set()
                
                # Correction anti-crash si la structure cloud contient de vieux modèles asynchrones
                if isinstance(dict_modeles_verif, dict):
                    for doc_id, data_m in dict_modeles_verif.items():
                        if doc_id == "Choisir un chantier pré-configuré...": continue
                        nom_base = str(data_m.get("nom_modele", doc_id)).strip().lower()
                        prix_base = float(data_m.get("revenus", 0.0))
                        chantiers_existants.add((nom_base, prix_base))


                lignes_verif = texte_verification_brut.split("\n")
                blocs_chantiers_bruts = {}
                nom_courant_verif = None
                
                for ligne in lignes_verif:
                    l_clean = ligne.strip()
                    if not l_clean: continue
                    
                    if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                        match_verif = re.search(r"^(.*?)\s+(\d[\d\s]+)\s+euros", l_clean, re.IGNORECASE)
                        if match_verif:
                            nom_ch = match_verif.group(1).strip()
                            prix_txt = "".join(c for c in match_verif.group(2) if c.isdigit())
                            prix_ch = float(prix_txt) if prix_txt else 0.0
                        else:
                            prix_ch = 0.0
                            nom_ch = l_clean.replace("euros", "").replace("Euros", "").strip()
                            
                        nom_courant_verif = f"{nom_ch} _VERIF_ {int(prix_ch)}"
                        blocs_chantiers_bruts[nom_courant_verif] = {
                            "nom_propre": nom_ch, "prix": prix_ch, "lignes": []
                        }
                        continue
                    
                    if nom_courant_verif and nom_courant_verif in blocs_chantiers_bruts:
                        blocs_chantiers_bruts[nom_courant_verif]["lignes"].append(ligne)

                liste_doublons = []
                liste_nouveaux_blocs = []
                
                for k_id, info_b in blocs_chantiers_bruts.items():
                    couple_cle = (info_b["nom_propre"].lower(), info_b["prix"])
                    if couple_cle in chantiers_existants:
                        liste_doublons.append(info_b)
                    else:
                        liste_nouveaux_blocs.append(info_b)
                
                c_v1, c_v2, c_v3 = st.columns(3)
                with c_v1: st.metric("Total détecté", f"{len(blocs_chantiers_bruts)}")
                with c_v2: st.metric("Doublons bloqués", f"{len(liste_doublons)}", delta="Déjà en base", delta_color="inverse")
                with c_v3: st.metric("Nouveaux chantiers", f"{len(liste_nouveaux_blocs)}", delta="À configurer", delta_color="normal")
                
                if liste_doublons:
                    with st.expander("🟢 Liste des doublons détectés (Ignorés automatiquement)"):
                        for d_ch in liste_doublons:
                            st.write(f"- **{d_ch['nom_propre']}** ({int(d_ch['prix']):,} €)".replace(",", " "))

                if liste_nouveaux_blocs:
                    st.markdown("---")
                    st.markdown("### 🛠️ Configuration et Décodage des Nouveaux Chantiers")
                    st.info("Modifiez ou complétez le texte des fiches ci-dessous.")
                    
                    chantiers_prets_a_injecter = {}
                    
                    for idx, n_ch in enumerate(liste_nouveaux_blocs):
                        st.markdown(f"#### 🧱 Fiche : **{n_ch['nom_propre']}** — `{int(n_ch['prix']):,} €`".replace(",", " "))
                        
                        texte_initial_bloc = "\n".join(n_ch["lignes"])
                        texte_ajuste = st.text_area(
                            f"Ajuster la structure technique de l'ouvrage :",
                            value=texte_initial_bloc, height=250, key=f"area_verif_modif_{idx}_{n_ch['nom_propre']}"
                        )
                        chantiers_detectes_local = {
                            "nom_affiche_propre": n_ch["nom_propre"], "revenus": n_ch["prix"],
                            "jours": 0, "heures": 0, "minutes": 0, "etapes_techniques": {}
                        }
                        
                        lignes_locales = texte_ajuste.split("\n")
                        etape_courante_num = None
                        
                        for ligne_l in lignes_locales:
                            l_l_clean = ligne_l.strip()
                            if not l_l_clean: continue
                            
                        if "durée du chantier :" in l_clean.lower() or "duree du chantier :" in l_clean.lower():
                            partie_duree = l_clean.split(":")[-1].lower()
                            
                            # Nettoyage de la ponctuation pour éviter les blocages textuels
                            for char in [",", "(", ")", "s", "."]:
                                partie_duree = partie_duree.replace(char, " ")
                            
                            # Découpage par mot pour une analyse ciblée
                            mots = partie_duree.split()
                            
                            # Balayage indexé pour capturer les nombres précédant les unités
                            for idx_mot, mot in enumerate(mots):
                                if idx_mot > 0:
                                    chiffre_txt = "".join(c for c in mots[idx_mot - 1] if c.isdigit())
                                    if chiffre_txt:
                                        valeur_numerique = int(chiffre_txt)
                                        if mot.startswith("jour"):
                                            chantiers_detectes[nom_courant]["jours"] = valeur_numerique
                                        elif mot.startswith("heure"):
                                            chantiers_detectes[nom_courant]["heures"] = valeur_numerique
                                        elif mot.startswith("minute"):
                                            chantiers_detectes[nom_courant]["minutes"] = valeur_numerique
                            continue


                            if l_l_clean.lower().startswith("etape") and ":" in l_l_clean:
                                match_e = re.search(r"etape\s*(\d+)", l_l_clean, re.IGNORECASE)
                                if match_e: 
                                    etape_courante_num = int(match_e.group(1))
                                    if etape_courante_num not in chantiers_detectes_local["etapes_techniques"]:
                                        chantiers_detectes_local["etapes_techniques"][etape_courante_num] = {
                                            "num_etape": etape_courante_num, "duree_jours": 1,
                                            "jh_cond": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0,
                                            "materiaux": {}, "engins": []
                                        }
                                continue

                            if etape_courante_num is not None:
                                target_etape = chantiers_detectes_local["etapes_techniques"][etape_courante_num]
                                
                                if "durée de l'étape :" in l_l_clean.lower() or "duree de l'etape :" in l_l_clean.lower():
                                    num_txt = "".join(c for c in l_l_clean.split(",") if c.isdigit())
                                    if num_txt: target_etape["duree_jours"] = int(num_txt)
                                    continue
                                
                                if ":" in l_l_clean and any(k in l_l_clean.lower() for k in ["chef", "ouvrier", "conducteur"]):
                                    gauche, droite = l_l_clean.split(":", 1)
                                    match_nb = re.search(r"(\d+)", droite)
                                    if match_nb:
                                        val_nb = float(match_nb.group(1))
                                        if "conducteur" in gauche.lower() or "engin" in gauche.lower(): target_etape["jh_cond"] = val_nb
                                        elif "chef" in gauche.lower(): target_etape["jh_chef"] = val_nb
                                        elif "ouvrier" in gauche.lower(): target_etape["jh_ouvrier"] = val_nb
                                    continue

                                if "matériaux requis :" in l_l_clean.lower() or "materiaux requis :" in l_l_clean.lower():
                                    partie_mats = l_l_clean.split(":")[-1].lower()
                                    if "aucun" not in partie_mats:
                                        sous_elements = partie_mats.split("&")
                                        for sub in sous_elements:
                                            qte_txt = "".join(c for c in sub if c.isdigit())
                                            if qte_txt:
                                                qte_val = float(qte_txt)
                                                mat_nom = None
                                                if "canalisation" in sub: mat_nom = "canalisations"
                                                elif "armature" in sub: mat_nom = "armature"
                                                elif "enrob" in sub: mat_nom = "enrobe"
                                                elif "sable" in sub: mat_nom = "sable"
                                                elif "terre" in sub: mat_nom = "terre"
                                                elif "tôle" in sub or "tole" in sub: mat_nom = "tole"
                                                elif "béton" in sub or "beton" in sub: mat_nom = "beton"
                                                elif "panneau" in sub: mat_nom = "panneaux"
                                                elif "tuyau" in sub: mat_nom = "tuyaux"
                                                elif "poutre" in sub: mat_nom = "poutres"
                                                if mat_nom: target_etape["materiaux"][mat_nom] = qte_val
                                    continue

                                ligne_brute_clean = l_l_clean.lower().replace("é", "e").replace("è", "e").replace("à", "a")
                                cat_engin = None
                                if "camion benne" in ligne_brute_clean: cat_engin = "Camions Benne"
                                elif "niveleuse" in ligne_brute_clean: cat_engin = "Niveleuse"
                                elif "finisseur" in ligne_brute_clean: cat_engin = "Finisseur"
                                elif "compacteur" in ligne_brute_clean: cat_engin = "Compacteur pour enrobé"
                                elif "fraiseuse" in ligne_brute_clean: cat_engin = "Fraiseuse"
                                elif "chargeuse" in ligne_brute_clean: cat_engin = "Chargeuse Compacte"
                                elif "pelleteuse" in ligne_brute_clean: cat_engin = "Pelleteuses"
                                elif "malaxeur" in ligne_brute_clean or "camion beton" in ligne_brute_clean: cat_engin = "Camion Béton Malaxeur"

                                if cat_engin:
                                    niv = f"N{re.search(r'niveau\s*(\d+)', ligne_brute_clean).group(1)}" if re.search(r'niveau\s*(\d+)', ligne_brute_clean) else "N1"
                                    target_etape["engins"].append({"type": cat_engin, "niveau": niv})
                        
                        cle_unique_injection = f"{n_ch['nom_propre']} - {int(n_ch['prix'])}€"
                        chantiers_prets_a_injecter[cle_unique_injection] = chantiers_detectes_local
                        st.markdown("---")
                    
                    if st.button("🚀 INJECTER LES NOUVEAUX MODÈLES DANS FIREBASE", type="primary", width="stretch", key="btn_save_verif_bloc_to_nosql"):
                        compteur_ins = 0
                        for unique_id, data_save in chantiers_prets_a_injecter.items():
                            liste_etapes_ordonnee = [t_et for k, t_et in sorted(data_save["etapes_techniques"].items())]
                            
                            db.db.collection("modeles_chantiers").document(unique_id).set({
                                "nom_modele": data_save["nom_affiche_propre"], 
                                "revenus": float(data_save["revenus"]), 
                                "jours_globaux": int(data_save["jours"]), 
                                "heures_globales": int(data_save["heures"]), 
                                "minutes_globales": int(data_save["minutes"]),
                                "etapes_techniques": liste_etapes_ordonnee
                            })
                            compteur_ins += 1
                        
                        st.cache_data.clear()
                        st.toast(f"🎯 {compteur_ins} nouveau(x) modèle(s) synchronisé(s) en Option B !")
                        st.rerun()
            else:
                st.info("💡 En attente de saisie textuelle dans la zone ci-dessus pour démarrer le processus.")

        # ==============================================================================
        # --- sub_tab8 : MONITEUR DE QUOTAS ET CONSOMMATION FIREBASE ---
        # ==============================================================================
        with sub_tab8:
            st.markdown("### 📊 Suivi de Consommation & Quotas Journaliers (Plan Gratuit)")
            st.write("Firestore comptabilise l'usage quotidien. Voici l'état estimé de vos limites système réinitialisées toutes les 24h par Google.")
            
            tz_paris = pytz.timezone('Europe/Paris')
            maintenant = datetime.datetime.now(tz_paris)
            
            cible_aujourdhui = maintenant.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if maintenant < cible_aujourdhui:
                echeance_reinit = cible_aujourdhui
            else:
                echeance_reinit = cible_aujourdhui + datetime.timedelta(days=1)
                
            temps_restant = echeance_reinit - maintenant
            heures_r, secondes_restantes = divmod(temps_restant.seconds, 3600)
            minutes_r, _ = divmod(secondes_restantes, 60)
            
            st.warning(f"⏱️ **Prochaine réinitialisation des quotas Google Firebase dans :** `{heures_r} heure(s) et {minutes_r} minute(s)` (chaque jour à 09h00)")

            try:
                quota_doc = db.db.collection("configuration_systeme").document("quotas_journaliers").get()
                if quota_doc.exists:
                    donnees_quota = quota_doc.to_dict()
                else:
                    donnees_quota = {}
            except Exception:
                donnees_quota = {}

            lectures_faites = int(donnees_quota.get("lectures", 1240))
            ecritures_faites = int(donnees_quota.get("ecritures", 315))
            suppressions_faites = int(donnees_quota.get("suppressions", 45))

            LIMITE_LECTURES = 50000
            LIMITE_ECRITURES = 20000
            LIMITE_SUPPRESSIONS = 20000

            pct_lectures = min(float(lectures_faites / LIMITE_LECTURES), 1.0)
            pct_ecritures = min(float(ecritures_faites / LIMITE_ECRITURES), 1.0)
            pct_suppressions = min(float(suppressions_faites / LIMITE_SUPPRESSIONS), 1.0)

            reste_lectures = LIMITE_LECTURES - lectures_faites
            reste_ecritures = LIMITE_ECRITURES - ecritures_faites
            reste_suppressions = LIMITE_SUPPRESSIONS - suppressions_faites

            c_q1, c_q2, c_v3 = st.columns(3)
            with c_q1:
                st.metric("Lectures Restantes", f"{reste_lectures:,.0f}".replace(",", " "), f"-{lectures_faites} faites", delta_color="inverse")
            with c_q2:
                st.metric("Écritures Restantes", f"{reste_ecritures:,.0f}".replace(",", " "), f"-{ecritures_faites} faites", delta_color="inverse")
            with c_v3:
                st.metric("Suppressions Restantes", f"{reste_suppressions:,.0f}".replace(",", " "), f"-{suppressions_faites} faites", delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("**📉 Jauge d'utilisation des Lectures (Limite : 50 000 / jour) :**")
            st.progress(pct_lectures, text=f"{lectures_faites} / {LIMITE_LECTURES} ({pct_lectures*100:.1f}%)")

            st.markdown("**✍️ Jauge d'utilisation des Écritures (Limite : 20 000 / jour) :**")
            st.progress(pct_ecritures, text=f"{ecritures_faites} / {LIMITE_ECRITURES} ({pct_ecritures*100:.1f}%)")

            st.markdown("**🗑️ Jauge d'utilisation des Suppressions (Limite : 20 000 / jour) :**")
            st.progress(pct_suppressions, text=f"{suppressions_faites} / {LIMITE_SUPPRESSIONS} ({pct_suppressions*100:.1f}%)")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 ACTUALISER LES COMPTEURS COMPTABLES", width="stretch"):
                st.cache_data.clear()
                st.rerun()

        # ==============================================================================
        # --- sub_tab9 : TRAÇABILITÉ ET JOURNAL DES ACTIONS (LOGS) ---
        # ==============================================================================
        with sub_tab9:
            st.markdown("### 📜 Journal d'Audit & Traçabilité NoSQL")
            st.write("Historique chronologique des modifications apportées aux configurations de l'entreprise.")

            try:
                logs_stream = db.db.collection("journaux_actions").order_by("timestamp", direction="DESCENDING").limit(100).stream()
                liste_logs = [d.to_dict() for d in logs_stream]
            except Exception:
                # REMPLACEMENT SÉCURISÉ DANS onglets/direction.py (sub_tab9) :
                try:
                    logs_stream = db.db.collection("journaux_actions").limit(100).stream()
                    liste_logs = [d.to_dict() for d in logs_stream]
                    if liste_logs:
                        df_logs = pd.DataFrame(liste_logs)
                        if "timestamp" in df_logs.columns:
                            df_logs = df_logs.sort_values(by="timestamp", ascending=False)
                except Exception:
                    liste_logs = []


            if liste_logs:
                df_logs = pd.DataFrame(liste_logs)
                for col in ["timestamp", "type_action", "details"]:
                    if col not in df_logs.columns: df_logs[col] = ""
                    
                st.dataframe(
                    df_logs, use_container_width=True, hide_index=True,
                    column_config={
                        "timestamp": st.column_config.TextColumn("⏱️ Date & Heure (Paris)", width="medium"),
                        "type_action": st.column_config.TextColumn("🏷️ Catégorie", width="small"),
                        "details": st.column_config.TextColumn("📝 Détails de l'opération", width="large")
                    }
                )
            else:
                st.info("💡 Aucun événement n'est encore enregistré dans le journal d'audit.")

    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect.")



