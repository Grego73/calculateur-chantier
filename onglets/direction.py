import streamlit as st
import pandas as pd
import database as db
import math
import re

# ==============================================================================
# --- 1. POP-UP DE VALIDATION : CALCULATEUR DE RECRUTEMENT ---
# ==============================================================================
@st.dialog("📊 Rapport d'Analyse et de Calcul des Paliers")
def pop_up_validation_recrutement(salaires_mensuels, metier, type_contrat, salaires_db_dict):
    st.write(f"Voici le détail de l'analyse et la conversion pour le poste de **{metier}** ({type_contrat}) :")
    
    sm_min = min(salaires_mensuels)
    sm_max = max(salaires_mensuels)
    sm_somme = sum(salaires_mensuels)
    sm_nb = len(salaires_mensuels)
    sm_moyen = sm_somme / sm_nb

    if "CDI" in type_contrat:
        sj_min = math.ceil(sm_min / 7.0)
        sj_moyen = math.ceil(sm_moyen / 7.0)
        sj_max = math.ceil(sm_max / 7.0)
        prefixe_cle = f"{metier}_CDI"
        st.info(f"💡 Conversion CDI mensuelle ramenée au jour (Moyenne : {int(sm_moyen)} €/mois)")
    else:
        sj_min = math.ceil(sm_min)
        sj_moyen = math.ceil(sm_moyen)
        sj_max = math.ceil(sm_max)
        prefixe_cle = f"{metier}_CDD"
        st.info(f"💡 Enregistrement CDD direct au jour (Moyenne : {int(sm_moyen)} €/jour)")

    st.markdown("### 🧮 Conversion ramenée au JOUR :")
    st.success(f"**- Tarif Minimum :** `{int(sj_min)} € / jour`")
    st.success(f"**- Tarif Moyen :** `{int(sj_moyen)} € / jour`")
    st.success(f"**- Tarif Maximum :** `{int(sj_max)} € / jour`")

    if st.button("✅ ENREGISTRER SUR FIREBASE", type="primary", use_container_width=True, key=f"btn_save_cloud_{metier}_{prefixe_cle}"):
        grille_actuelle = dict(salaires_db_dict)
        grille_actuelle[f"{prefixe_cle}_Min"] = int(sj_min)
        grille_actuelle[f"{prefixe_cle}_Moyen"] = int(sj_moyen)
        grille_actuelle[f"{prefixe_cle}_Max"] = int(sj_max)
        grille_actuelle[metier] = int(sj_moyen)

        db.db.collection("configuration_salaires").document("grille").set(grille_actuelle)
        st.toast("🚀 Tarifs enregistrés sur Firebase !")
        st.rerun()

# ==============================================================================
# --- 2. POP-UP DE VALIDATION POUR L'EXTRACTEUR DE FICHES CHANTIERS (MIS À JOUR) ---
# ==============================================================================
@st.dialog("🔍 Rapport d'Analyse et d'Importation des Modèles")
def pop_up_validation_fiches_chantiers(chantiers_detectes):
    st.write("Voici la transparence des données techniques extraites de vos fiches brutes avant insertion cloud :")
    
    for name, data in chantiers_detectes.items():
        st.markdown(f"### 🏗️ Chantier : **{name}**")
        st.info(f"💰 **Revenus détectés :** `{int(data['revenus']):,.0f}` €".replace(",", " "))
        
        # Affichage du temps décomposé
        st.markdown("**⏱️ Temps configuré pour l'Onglet 1 :**")
        st.code(f"{data['jours']} jour(s), {data['heures']} heure(s), {data['minutes']} minute(s)")
        
        # Affichage de l'équipe maximale retenue pour le dimensionnement global
        st.markdown("**👥 Structure de l'équipe globale (Maximum requis) :**")
        st.write(f"- 🕹️ Conducteurs d'engins : `{int(data['max_cond'])}` | - 🧑‍💼 Chefs de chantier : `{int(data['max_chef'])}` | - 👷 Ouvriers : `{int(data['max_ouvrier'])}`")
        
        # Affichage du cumul des matériaux
        st.markdown("**🧱 Approvisionnement Matériaux Cumulés :**")
        mats_list = []
        for m_key in ["sable", "terre", "enrobe", "armature", "tole", "beton", "panneaux", "tuyaux", "canalisations", "poutres"]:
            if data[m_key] > 0:
                mats_list.append(f"{m_key.capitalize()} : `{int(data[m_key])}`")
        if mats_list:
            st.write(" | ".join(mats_list))
        else:
            st.write("*Aucun matériau requis pour ce modèle.*")
            
        # Affichage des étapes de machines reconstruites AVEC LE PERSONNEL PAR ÉTAPE
        st.markdown("**🚜 Étapes techniques, Engins & Employés détectés à l'étape :**")
        df_engins_preview = pd.DataFrame(data["engins_requis"])
        
        # --- REMPLACE LE BLOC ST.DATAFRAME PAR CELUI-CI ---
        st.markdown("**🚜 Étapes techniques, Engins & Employés détectés à l'étape :**")
        df_engins_preview = pd.DataFrame(data["engins_requis"])
        
        # Affichage direct de toutes les colonnes présentes dans le dictionnaire
        st.dataframe(df_engins_preview, use_container_width=True, hide_index=True)

        st.markdown("---")
        
    st.warning("🚨 Confirmez-vous l'injection de ces structures NoSQL dans votre catalogue de modèles ?")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("✅ CONFIRMER L'IMPORTATION", type="primary", use_container_width=True, key="btn_confirm_cloud_import_fiches"):
            compteur = 0
            for name, data in chantiers_detectes.items():
                db.db.collection("modeles_chantiers").document(name).set({
                    "nom_modele": name, "revenus": float(data["revenus"]), 
                    "jours": int(data["jours"]), "heures": int(data["heures"]), "minutes": int(data["minutes"]),
                    "sable": float(data["sable"]), "terre": float(data["terre"]), "enrobe": float(data["enrobe"]), 
                    "armature": float(data["armature"]), "tole": float(data["tole"]), "beton": float(data["beton"]), 
                    "panneaux": float(data["panneaux"]), "tuyaux": float(data["tuyaux"]), 
                    "canalisations": float(data["canalisations"]), "poutres": float(data["poutres"]),
                    "jh_cond": float(data["max_cond"]), "jh_chef": float(data["max_chef"]), "jh_ouvrier": float(data["max_ouvrier"]), 
                    "engins_requis": data["engins_requis"]
                })
                compteur += 1
            st.toast(f"🚀 {compteur} modèle(s) synchronisé(s) avec succès !")
            st.rerun()
    with col_c2:
        if st.button("❌ ANNULER", use_container_width=True, key="btn_cancel_cloud_import_fiches"):
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
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🚨 Zone de Danger : Réinitialisation et Nettoyage des Tables"):
                st.warning("Attention : Ces actions suppriment définitivement les données stockées sur Firebase.")
                col_del1, col_del2, col_del3 = st.columns(3)
                with col_del1:
                    if st.button("🗑️ Vider l'Historique des Chantiers", type="secondary", use_container_width=True):
                        docs = db.db.collection("chantiers").stream()
                        for d in docs: d.reference.delete()
                        st.toast("Historique des chantiers supprimé !")
                        st.rerun()
                with col_del2:
                    if st.button("🗑️ Vider les Modèles Préfabriqués", type="secondary", use_container_width=True):
                        docs = db.db.collection("modeles_chantiers").stream()
                        for d in docs: d.reference.delete()
                        st.toast("Catalogue des modèles vidé !")
                        st.rerun()
                with col_del3:
                    if st.button("💥 TOUT RÉINITIALISER", type="primary", use_container_width=True):
                        db.reinitialiser_db()
                        st.rerun()
            st.markdown("---")

        st.markdown("## ⚙️ Administration Suprême des Bases NoSQL")
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins", "🗂️ Consulter les Bases Données"
        ])
        
        # --- 4.1 IMPORTATION EN BLOC ET DECODAGE AVEC LA FENÊTRE DE VALIDATION ---
        with sub_tab1:
            st.markdown("### 📥 Extracteur de Fiches Chantiers Multi-Étapes")
            texte_fiches_brutes = st.text_area("Collez vos fiches de chantiers détaillées ici :", value="", height=350, key="zone_texte_import_unique_fusionne")
            
            if st.button("🏗️ ANALYSER, NETTOYER ET IMPORTER LES MODÈLES", type="primary"):
                if not texte_fiches_brutes.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    lignes = texte_fiches_brutes.split("\n")
                    chantiers_detectes = {}
                    nom_courant = None
                    etape_courante_num = None
                    
                    for ligne in lignes:
                        l_clean = ligne.strip()
                        if not l_clean: continue
                        
                        # 1. DÉTECTION DU DEBUT DU CHANTIER ET DE SON NOM
                        if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                            match_debut = re.search(r"^(.*?)\s+(\d[\d\s]+)\s+euros", l_clean, re.IGNORECASE)
                            if match_debut:
                                nom_ch = match_debut.group(1).strip()
                                prix_txt = "".join(c for c in match_debut.group(2) if c.isdigit())
                                prix_ch = float(prix_txt) if prix_txt else 0.0
                            else:
                                prix_ch = 0.0
                                nom_ch = l_clean.replace("euros", "").replace("Euros", "").strip()
                                
                            nom_courant = nom_ch
                            if nom_courant not in chantiers_detectes:
                                chantiers_detectes[nom_courant] = {
                                    "revenus": prix_ch, "jours": 0, "heures": 0, "minutes": 0, "nb_etapes": 1,
                                    "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
                                    "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
                                    "max_cond": 0.0, "max_chef": 0.0, "max_ouvrier": 0.0, "engins_requis": []
                                }
                            continue

                        if not nom_courant: continue
                        
                        # 2. CAPTURE DES REVENUS REPETÉS
                        if l_clean.lower().startswith("revenus :"):
                            prix_txt = "".join(c for c in l_clean if c.isdigit())
                            if prix_txt: chantiers_detectes[nom_courant]["revenus"] = float(prix_txt)
                            continue
                            
                        # 3. EXTRACTION DU NOMBRE D'ÉTAPES GLOBOALES
                        if "nombre d'étapes :" in l_clean.lower():
                            num_txt = "".join(c for c in l_clean.split(":")[-1] if c.isdigit())
                            if num_txt: chantiers_detectes[nom_courant]["nb_etapes"] = int(num_txt)
                            continue

                        # 4. DECODAGE DE LA DURÉE DU CHANTIER GLOBALE
                        if "durée du chantier :" in l_clean.lower():
                            partie_duree = l_clean.split(":")[-1].lower()
                            m_j = re.search(r"(\d+)\s*jour", partie_duree)
                            m_h = re.search(r"(\d+)\s*heure", partie_duree)
                            m_m = re.search(r"(\d+)\s*minute", partie_duree)
                            if m_j: chantiers_detectes[nom_courant]["jours"] = int(m_j.group(1))
                            if m_h: chantiers_detectes[nom_courant]["heures"] = int(m_h.group(1))
                            if m_m: chantiers_detectes[nom_courant]["minutes"] = int(m_m.group(1))
                            continue

                        # 5. DÉTECTION ET ISOLEMENT DES ÉTAPES INDIVIDUELLES
                        if l_clean.lower().startswith("etape") and ":" in l_clean:
                            match_e = re.search(r"etape\s*(\d+)", l_clean, re.IGNORECASE)
                            if match_e:
                                etape_courante_num = int(match_e.group(1))
                                # On crée la structure de l'étape incluant les futurs compteurs d'employés
                                chantiers_detectes[nom_courant]["engins_requis"].append({
                                    "N° Étape": etape_courante_num,
                                    "Durée Étape (jours)": 1,
                                    "Type d'engin requis": "Pelleteuses",
                                    "Niveau requis": "N1",
                                    "Conducteurs requis": 0,
                                    "Chefs requis": 0,
                                    "Ouvriers requis": 0
                                })
                            continue

                        # 6. CAPTURE DE LA DURÉE DE CHAQUE ÉTAPE INDIVIDUELLE
                        if l_clean.lower().startswith("durée de l'étape :") or l_clean.lower().startswith("duree de l'etape :"):
                            num_txt = "".join(c for c in l_clean.split(",") if c.isdigit())
                            if num_txt and etape_courante_num is not None:
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Durée Étape (jours)"] = int(num_txt)

                        # 7. LOGIQUE RH : ENREGISTREMENT PAR ÉTAPE + CALCUL DU MAX POUR L'ONGLET 1
                        if "conducteur" in l_clean.lower():
                            match_num = re.search(r":\s*(\d+)", l_clean)
                            if match_num and etape_courante_num is not None:
                                val_cond = int(match_num.group(1))
                                # Insertion spécifique à l'étape en cours
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Conducteurs requis"] = val_cond
                                chantiers_detectes[nom_courant]["max_cond"] = max(chantiers_detectes[nom_courant]["max_cond"], float(val_cond))
                                
                        if "chef" in l_clean.lower():
                            match_num = re.search(r":\s*(\d+)", l_clean)
                            if match_num and etape_courante_num is not None:
                                val_chef = int(match_num.group(1))
                                # Insertion spécifique à l'étape en cours
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Chefs requis"] = val_chef
                                chantiers_detectes[nom_courant]["max_chef"] = max(chantiers_detectes[nom_courant]["max_chef"], float(val_chef))
                                
                        if "ouvrier" in l_clean.lower():
                            match_num = re.search(r":\s*(\d+)", l_clean)
                            if match_num and etape_courante_num is not None:
                                val_ouv = int(match_num.group(1))
                                # Insertion spécifique à l'étape en cours
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Ouvriers requis"] = val_ouv
                                chantiers_detectes[nom_courant]["max_ouvrier"] = max(chantiers_detectes[nom_courant]["max_ouvrier"], float(val_ouv))

                        # 8. CUMUL DES MATÉRIAUX REQUIS
                        if "matériaux requis :" in l_clean.lower() or "materiaux requis :" in l_clean.lower():
                            partie_mats = l_clean.split(":")[-1].lower()
                            if "aucun" not in partie_mats:
                                sous_elements_mats = partie_mats.split("&")
                                for sub_mat in sous_elements_mats:
                                    qte_txt = "".join(c for c in sub_mat if c.isdigit())
                                    if qte_txt:
                                        qte_val = float(qte_txt)
                                        if "canalisation" in sub_mat: chantiers_detectes[nom_courant]["canalisations"] += qte_val
                                        elif "armature" in sub_mat: chantiers_detectes[nom_courant]["armature"] += qte_val
                                        elif "enrob" in sub_mat: chantiers_detectes[nom_courant]["enrobe"] += qte_val
                                        elif "sable" in sub_mat: chantiers_detectes[nom_courant]["sable"] += qte_val
                                        elif "terre" in sub_mat: chantiers_detectes[nom_courant]["terre"] += qte_val
                                        elif "tôle" in sub_mat or "tole" in sub_mat: chantiers_detectes[nom_courant]["tole"] += qte_val
                                        elif "béton" in sub_mat or "beton" in sub_mat: chantiers_detectes[nom_courant]["beton"] += qte_val
                                        elif "panneau" in sub_mat: chantiers_detectes[nom_courant]["panneaux"] += qte_val
                                        elif "tuyau" in sub_mat: chantiers_detectes[nom_courant]["tuyaux"] += qte_val
                                        elif "poutre" in sub_mat: chantiers_detectes[nom_courant]["poutres"] += qte_val

                        # 9. LECTURE DU NOM DE LA MACHINE ET DU NIVEAU REQUIS (CORRIGÉ)
                        if "requis :" in l_clean.lower() and "matériaux" not in l_clean.lower() and "materiaux" not in l_clean.lower() and "nécessite" not in l_clean.lower():
                            match_niv = re.search(r"niveau\s*(\d+)", l_clean, re.IGNORECASE)
                            niv_extrait = f"N{match_niv.group(1)}" if match_niv else "N1"
                            
                            cat_engin = "Pelleteuses"
                            if "camion benne" in l_clean.lower(): cat_engin = "Camions Benne"
                            elif "niveleuse" in l_clean.lower(): cat_engin = "Niveleuse"
                            elif "finisseur" in l_clean.lower(): cat_engin = "Finisseur"
                            elif "compacteur" in l_clean.lower(): cat_engin = "Compacteur pour enrobé"
                            elif "fraiseuse" in l_clean.lower(): cat_engin = "Fraiseuse"
                            
                            # Correction d'indexation : on met à jour la DERNIÈRE étape enregistrée
                            if nom_courant in chantiers_detectes and len(chantiers_detectes[nom_courant]["engins_requis"]) > 0:
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Type d'engin requis"] = cat_engin
                                chantiers_detectes[nom_courant]["engins_requis"][-1]["Niveau requis"] = niv_extrait

                    if len(chantiers_detectes) > 0:
                        pop_up_validation_fiches_chantiers(chantiers_detectes)
                    else:
                        st.error("❌ L'algorithme n'a détecté aucune fiche de chantier valide dans votre texte brut.")

        # --- 4.2 CONFIGURATION GRILLE SALARIALE (SANS AUCUN FILTRE POUR SUPPRESSION DÉFINITIVE) ---
        with sub_tab2:
            st.markdown("### 👥 Extracteur et Calculateur de Salaires par Métier & Contrat")
            
            c_admin_poste, c_admin_contrat = st.columns(2)
            with c_admin_poste:
                metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
            with c_admin_contrat:
                type_contrat_cible = st.selectbox("Type de contrat collé :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])

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
                        if salaire_trouve is not None: liste_salaires_extraits.append(salaire_trouve)

                    if len(liste_salaires_extraits) > 0:
                        pop_up_validation_recrutement(liste_salaires_extraits, metier_cible, type_contrat_cible, SALAIRES_DB)
                    else:
                        st.error("❌ Aucun montant trouvé.")

            # --- AFFICHAGE TOTAL SANS AUCUN FILTRE POUR NETTOYAGE ---
            st.markdown("---")
            st.write("⚙️ **Base Cloud brute (Cochez pour supprimer définitivement de Firebase) :**")
            
            lignes_brutes_firebase = [
                {"Clé": poste, "Montant / jour (€)": int(mt), "🗑️ Retirer": False} 
                for poste, mt in SALAIRES_DB.items()
            ]
            lignes_brutes_firebase.sort(key=lambda x: x["Clé"])
            
            table_retour_edition = st.data_editor(
                pd.DataFrame(lignes_brutes_firebase), use_container_width=True, hide_index=True, key="editeur_interactif_brut_total",
                column_config={
                    "Clé": st.column_config.TextColumn("Donnée en base (Firestore)", disabled=True),
                    "Montant / jour (€)": st.column_config.NumberColumn("Montant (€)", format="%d €", disabled=True),
                    "🗑️ Retirer": st.column_config.CheckboxColumn("🗑️ Retirer", default=False)
                }
            )
            
            if not table_retour_edition.empty:
                lignes_a_supprimer = table_retour_edition[table_retour_edition["🗑️ Retirer"] == True]
                if len(lignes_a_supprimer) > 0:
                    st.warning(f"🚨 Alerte : Vous allez détruire définitivement {len(lignes_a_supprimer)} ligne(s) du Cloud Firebase.")
                    if st.button("💥 CONFIRMER LA SUPPRESSION DU CLOUD", type="primary", use_container_width=True, key="btn_confirm_delete_total_raw"):
                        grille_firebase = dict(SALAIRES_DB)
                        for _, row_del in lignes_a_supprimer.iterrows():
                            cle_a_retirer = row_del["Clé"]
                            if cle_a_retirer in grille_firebase: del grille_firebase[cle_a_retirer]
                        db.db.collection("configuration_salaires").document("grille").set(grille_firebase)
                        st.toast("🔥 Données effacées définitivement !")
                        st.rerun()

        # --- 4.3 CONFIGURATION DES MATÉRIAUX ---
        with sub_tab3:
            st.write("Ajustez le prix unitaire de vos matières premières.")
            mats_edites = st.data_editor(pd.DataFrame(list(MATERIAUX_DB.items()), columns=["materiau", "prix_unitaire"]), use_container_width=True, key="editeur_mats_db", num_rows="fixed")
            if st.button("METTRE À JOUR LE COÛT DES MATÉRIAUX"):
                nouveau_dict = dict(zip(mats_edites["materiau"], mats_edites["prix_unitaire"].astype(float)))
                db.db.collection("configuration_materiaux").document("catalogue").set(nouveau_dict)
                st.success("Tarifs matériaux actualisés !"); st.rerun()

        # --- 4.4 CATALOGUE DE MACHINES ---
        with sub_tab4:
            st.write("Ajoutez ou modifiez vos engins lourds.")
            docs_engins = db.db.collection("catalogue_engins").stream()
            liste_engins = [{"nom_engin": d.id, "type_brut": d.to_dict().get("type_brut", ""), "prix_jour": d.to_dict().get("prix_jour", 0.0)} for d in docs_engins]
            df_engins = pd.DataFrame(liste_engins) if liste_engins else pd.DataFrame(columns=["nom_engin", "type_brut", "prix_jour"])
            
            engins_edites_db = st.data_editor(df_engins, use_container_width=True, key="editeur_engins_db", num_rows="dynamic")
            if st.button("METTRE À JOUR LE CATALOGUE DES ENGINS"):
                old_docs = db.collection("catalogue_engins").stream()
                for od in old_docs: od.reference.delete()
                for _, r in engins_edites_db.iterrows():
                    if pd.notnull(r["nom_engin"]) and str(r["nom_engin"]).strip():
                        db.db.collection("catalogue_engins").document(str(r["nom_engin"]).strip()).set({"type_brut": str(r["type_brut"]), "prix_jour": float(r["prix_jour"])})
                st.success("Parc d'engins synchronisé !"); st.rerun()

        # --- 4.5 VISUALISATION EN DIRECT DES TABLES BRUTES (SANS FILTRE) ---
        with sub_tab5:
            st.markdown("### 🗂️ Consultation brute complète")
            choix_table = st.selectbox("Choisir la table :", ["Modèles de Chantiers Pré-configurés", "Grille Salariale Actuelle", "Prix des Matériaux de base", "Catalogue de Location des Engins"])
            if choix_table == "Modèles de Chantiers Pré-configurés":
                docs = db.db.collection("modeles_chantiers").stream(); res = [d.to_dict() for d in docs]
                if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
                else: st.info("Aucun modèle.")
            elif choix_table == "Grille Salariale Actuelle":
                st.json(SALAIRES_DB)
            elif choix_table == "Prix des Matériaux de base":
                st.json(MATERIAUX_DB)
            elif choix_table == "Catalogue de Location des Engins":
                docs = db.collection("catalogue_engins").stream()
                res = [{"Engin Modèle": d.id, "Catégorie": d.to_dict().get("type_brut"), "Prix/j (€)": d.to_dict().get("prix_jour")} for d in docs]
                if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
                else: st.info("Catalogue vide.")
    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect.")
