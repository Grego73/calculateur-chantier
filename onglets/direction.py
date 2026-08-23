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

    if st.button("✅ ENREGISTRER SUR FIREBASE", type="primary", use_container_width=True, key=f"btn_save_cloud_{metier_clean}_{prefixe_cle}"):
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
        
        st.markdown("**🧱 Approvisionnement Matériaux Cumulés :**")
        mats_list = []
        for m_key in ["sable", "terre", "enrobe", "armature", "tole", "beton", "panneaux", "tuyaux", "canalisations", "poutres"]:
            if data[m_key] > 0:
                txt_mat_qte = f"{int(data[m_key]):,.0f}".replace(",", " ")
                mats_list.append(f"{m_key.capitalize()} : `{txt_mat_qte}`")
        if mats_list:
            st.write(" | ".join(mats_list))
        else:
            st.write("*Aucun matériau requis pour ce modèle.*")
            
        st.markdown("**🚜 Étapes techniques & Engins détectés :**")
        df_brut_etapes = pd.DataFrame(data["engins_requis"])
        cols_engins = ["N° Étape", "Durée Étape (jours)", "Type d'engin requis", "Niveau requis"]
        df_engins = df_brut_etapes[[c for c in cols_engins if c in df_brut_etapes.columns]] if not df_brut_etapes.empty else pd.DataFrame()
        st.dataframe(df_engins, use_container_width=True, hide_index=True)
        
        st.markdown("**👥 Structure des Employés requis à l'étape :**")
        lignes_emp = []
        if not df_brut_etapes.empty:
            for _, row_e in df_brut_etapes.iterrows():
                lignes_emp.append({
                    "N° Étape": row_e.get("N° Étape", 1),
                    "🕹️ Conducteurs": data.get("jh_cond", 0.0),
                    "🧑‍💼 Chefs": data.get("jh_chef", 0.0),
                    "👷 Ouvriers": data.get("jh_ouvrier", 0.0)
                })
        else:
            lignes_emp.append({
                "N° Étape": 1,
                "🕹️ Conducteurs": data.get("jh_cond", 0.0),
                "🧑‍💼 Chefs": data.get("jh_chef", 0.0),
                "👷 Ouvriers": data.get("jh_ouvrier", 0.0)
            })
            
        df_employes_brut = pd.DataFrame(lignes_emp)
        if not df_employes_brut.empty:
            df_employes_fusionne = df_employes_brut.groupby("N° Étape", as_index=False).max()
            st.dataframe(df_employes_fusionne, use_container_width=True, hide_index=True)
        else:
            st.write("*Aucun personnel requis détecté.*")
            
        st.markdown("---")
    st.warning("🚨 Confirmez-vous l'injection de ces structures NoSQL dans votre catalogue de modèles ?")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("✅ CONFIRMER L'IMPORTATION", type="primary", use_container_width=True, key="btn_confirm_cloud_import_fiches"):
            compteur = 0
            for temporary_key, data in chantiers_detectes.items():
                engins_propres = [
                    e for e in data["engins_requis"] 
                    if e.get("Type d'engin requis") is not None and str(e["Type d'engin requis"]).strip() != ""
                ]
                
                vrai_nom_propre = data["nom_affiche_propre"]
                nom_unique_key = f"{vrai_nom_propre} - {int(data['revenus'])}€"
                
                db.db.collection("modeles_chantiers").document(nom_unique_key).set({
                    "nom_modele": vrai_nom_propre, 
                    "revenus": float(data["revenus"]), 
                    "jours": int(data["jours"]), 
                    "heures": int(data["heures"]), 
                    "minutes": int(data["minutes"]),
                    "sable": float(data["sable"]), 
                    "terre": float(data["terre"]), 
                    "enrobe": float(data["enrobe"]), 
                    "armature": float(data["armature"]), 
                    "tole": float(data["tole"]), 
                    "beton": float(data["beton"]),
                    "panneaux": float(data["panneaux"]), 
                    "tuyaux": float(data["tuyaux"]), 
                    "canalisations": float(data["canalisations"]), 
                    "poutres": float(data["poutres"]),
                    "jh_cond": float(data.get("jh_cond", 0.0)), 
                    "max_cond": float(data.get("jh_cond", 0.0)),
                    "jh_chef": float(data.get("jh_chef", 0.0)), 
                    "max_chef": float(data.get("jh_chef", 0.0)),
                    "jh_ouvrier": float(data.get("jh_ouvrier", 0.0)), 
                    "max_ouvrier": float(data.get("jh_ouvrier", 0.0)),
                    "engins_requis": engins_propres
                })
                compteur += 1
            st.cache_data.clear()
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
        else:
            st.info("💡 Historique vierge : Aucun chantier n'est encore enregistré en base de données.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("🚨 Zone de Danger : Réinitialisation et Nettoyage des Tables"):
            st.warning("Attention : Ces actions suppriment définitivement les données stockées sur Firebase.")
            col_del1, col_del2, col_del3 = st.columns(3)
            with col_del1:
                if st.button("🗑️ Vider l'Historique des Chantiers", type="secondary", use_container_width=True):
                    docs = db.db.collection("chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Historique des chantiers supprimé !")
                    st.rerun()
            with col_del2:
                if st.button("🗑️ Vider les Modèles Préfabriqués", type="secondary", use_container_width=True):
                    docs = db.db.collection("modeles_chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Catalogue des modèles vidé !")
                    st.rerun()
            with col_del3:
                if st.button("💥 TOUT RÉINITIALISER", type="primary", use_container_width=True):
                    db.reinitialiser_db()
                    st.rerun()
                    
        st.markdown("---")

        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6, sub_tab7, sub_tab8, sub_tab9 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins", "🗂️ Consulter les Bases Données",
            "🔎 Comparateur de Fiches", "🔍 Vérificateur de Doublons", "📊 Quotas Firebase", "📜 Historique des Actions"
        ])

        # ==============================================================================
        # --- sub_tab1 : IMPORTATION EN BLOC ET DECODAGE AVEC FILTRE ANTI-DOUBLONS ---
        # ==============================================================================
        with sub_tab1:
            dict_modeles_cloud = db.charger_catalogue_chantiers()
            res_modeles_base = [dict_modeles_cloud[k] for k in dict_modeles_cloud if k != "Choisir un chantier pré-configuré..."]
            total_modeles_base = len(res_modeles_base)

            st.markdown(f"### 📥 Extracteur de Fiches Chantiers Multi-Étapes ({total_modeles_base} modèles en base)")
            texte_fiches_brutes = st.text_area("Zone de saisie des fiches :", value="", height=350, key="zone_texte_import_unique_fusionne")
            
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
                    durees_etapes_locales = {}  
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
                                
                            if (nom_ch.lower(), prix_ch) in modeles_deja_presents:
                                nom_courant = None
                                compteur_doublons_bloques += 1
                                continue
                                
                            nom_courant = f"{nom_ch} _PLANCHER_ {int(prix_ch)}"
                            etape_courante_num = None
                            
                            if nom_courant not in chantiers_detectes:
                                chantiers_detectes[nom_courant] = {
                                    "nom_affiche_propre": nom_ch,
                                    "revenus": prix_ch, "jours": 0, "heures": 0, "minutes": 0, "nb_etapes": 1,
                                    "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
                                    "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
                                    "jh_cond": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0, "engins_requis": []
                                }
                            continue

                        if not nom_courant: continue
                        
                        if l_clean.lower().startswith("revenus :"):
                            prix_txt = "".join(c for c in l_clean if c.isdigit())
                            if prix_txt: 
                                chantiers_detectes[nom_courant]["revenus"] = float(prix_txt)
                                old_data = chantiers_detectes[nom_courant]
                                nom_filtre_secours = f"{old_data['nom_affiche_propre']} _PLANCHER_ {int(prix_txt)}"
                                if nom_filtre_secours != nom_courant:
                                    chantiers_detectes[nom_filtre_secours] = old_data
                                    nom_courant = nom_filtre_secours
                            continue
                            
                        if "nombre d'étapes :" in l_clean.lower():
                            num_txt = "".join(c for c in l_clean.split(":")[-1] if c.isdigit())
                            if num_txt: chantiers_detectes[nom_courant]["nb_etapes"] = int(num_txt)
                            continue

                        if "durée du chantier :" in l_clean.lower():
                            partie_duree = l_clean.split(":")[-1].lower()
                            m_j = re.search(r"(\d+)\s*jour", partie_duree)
                            m_h = re.search(r"(\d+)\s*heure", partie_duree)
                            m_m = re.search(r"(\d+)\s*minute", partie_duree)
                            if m_j: chantiers_detectes[nom_courant]["jours"] = int(m_j.group(1))
                            if m_h: chantiers_detectes[nom_courant]["heures"] = int(m_h.group(1))
                            if m_m: chantiers_detectes[nom_courant]["minutes"] = int(m_m.group(1))
                            continue

                        if l_clean.lower().startswith("etape") and ":" in l_clean:
                            match_e = re.search(r"etape\s*(\d+)", l_clean, re.IGNORECASE)
                            if match_e: etape_courante_num = int(match_e.group(1))
                            continue

                        if (l_clean.lower().startswith("durée de l'étape :") or l_clean.lower().startswith("duree de l'etape :")) and etape_courante_num is not None:
                            num_txt = "".join(c for c in l_clean.split(",") if c.isdigit())
                            if num_txt: 
                                durees_etapes_locales[f"duree_{nom_courant}_{etape_courante_num}"] = int(num_txt)
                            continue
                        if ":" in l_clean and etape_courante_num is not None and ("chef" in l_clean.lower() or "ouvrier" in l_clean.lower() or "conducteur" in l_clean.lower()):
                            gauche, droite = l_clean.split(":", 1)
                            gauche_low = gauche.lower()
                            
                            match_nb = re.search(r"(\d+)", droite)
                            if match_nb:
                                nb_val = float(match_nb.group(1))
                                if "conducteur" in gauche_low or "engin" in gauche_low:
                                    chantiers_detectes[nom_courant]["jh_cond"] = max(chantiers_detectes[nom_courant]["jh_cond"], nb_val)
                                elif "chef" in gauche_low:
                                    chantiers_detectes[nom_courant]["jh_chef"] = max(chantiers_detectes[nom_courant]["jh_chef"], nb_val)
                                elif "ouvrier" in gauche_low:
                                    chantiers_detectes[nom_courant]["jh_ouvrier"] = max(chantiers_detectes[nom_courant]["jh_ouvrier"], nb_val)
                            continue

                        if "matériaux requis :" in l_clean.lower() or "materiaux requis :" in l_clean.lower():
                            partie_mats = l_clean.split(":")[-1].lower()
                            if "aucun" not in partie_mats:
                                sous_elements_mats = partie_mats.split("&")
                                for sub_mat in sous_elements_mats:
                                    qte_txt = "".join(c for c in sub_mat if c.isdigit())
                                    if qte_txt:
                                        qte_val = float(qte_txt)
                                        if "canalisation" in sub_mat: chantiers_detectes[nom_courant]["canalisations"] = qte_val
                                        elif "armature" in sub_mat: chantiers_detectes[nom_courant]["armature"] = qte_val
                                        elif "enrob" in sub_mat: chantiers_detectes[nom_courant]["enrobe"] = qte_val
                                        elif "sable" in sub_mat: chantiers_detectes[nom_courant]["sable"] = qte_val
                                        elif "terre" in sub_mat: chantiers_detectes[nom_courant]["terre"] = qte_val
                                        elif "tôle" in sub_mat or "tole" in sub_mat: chantiers_detectes[nom_courant]["tole"] = qte_val
                                        elif "béton" in sub_mat or "beton" in sub_mat: chantiers_detectes[nom_courant]["beton"] = qte_val
                                        elif "panneau" in sub_mat: chantiers_detectes[nom_courant]["panneaux"] = qte_val
                                        elif "tuyau" in sub_mat: chantiers_detectes[nom_courant]["tuyaux"] = qte_val
                                        elif "poutre" in sub_mat: chantiers_detectes[nom_courant]["poutres"] = qte_val
                            continue
                        if etape_courante_num is not None and "employés requis" not in l_clean.lower() and "matériaux requis" not in l_clean.lower():
                            ligne_brute_clean = l_clean.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
                            cat_engin = None
                            if "camion benne" in ligne_brute_clean: cat_engin = "Camions Benne"
                            elif "niveleuse" in ligne_brute_clean: cat_engin = "Niveleuse"
                            elif "finisseur" in ligne_brute_clean: cat_engin = "Finisseur"
                            elif "compacteur pour enrobe" in ligne_brute_clean or "compacteur" in ligne_brute_clean: cat_engin = "Compacteur pour enrobé"
                            elif "fraiseuse" in ligne_brute_clean: cat_engin = "Fraiseuse"
                            elif "chargeuse" in ligne_brute_clean: cat_engin = "Chargeuse Compacte"
                            elif "pelleteuse" in ligne_brute_clean: cat_engin = "Pelleteuses"
                            elif "malaxeur" in ligne_brute_clean or "camion beton" in ligne_brute_clean: cat_engin = "Camion Béton Malaxeur"

                            if cat_engin is not None:
                                d_etape = durees_etapes_locales.get(f"duree_{nom_courant}_{etape_courante_num}", 1)
                                doublon_engin = any(e["N° Étape"] == etape_courante_num and e["Type d'engin requis"] == cat_engin for e in chantiers_detectes[nom_courant]["engins_requis"])
                                if not doublon_engin:
                                    chantiers_detectes[nom_courant]["engins_requis"].append({
                                        "N° Étape": etape_courante_num, 
                                        "Durée Étape (jours)": d_etape,
                                        "Type d'engin requis": cat_engin,
                                        "Niveau requis": f"N{re.search(r'niveau\s*(\d+)', ligne_brute_clean).group(1)}" if re.search(r'niveau\s*(\d+)', ligne_brute_clean) else "N1"
                                    })

                    if len(chantiers_detectes) > 0:
                        if compteur_doublons_bloques > 0:
                            st.toast(f"ℹ️ {compteur_doublons_bloques} doublon(s) détecté(s) ont été automatiquement filtré(s).")
                        pop_up_validation_fiches_chantiers(chantiers_detectes)
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
                
                if grille_editee is not None and not grille_editee.empty:
                    cles_a_supprimer = grille_editee[grille_editee["Supprimer l'entrée 🗑️"] == True]["Clé technique NoSQL"].tolist()
                    if cles_a_supprimer:
                        st.warning(f"🚨 Vous avez sélectionné {len(cles_a_supprimer)} entrée(s) pour suppression définitive.")
                        if st.button("💥 VALIDER LA SUPPRESSION DÉFINITIVE", type="primary", use_container_width=True):
                            grille_nettoyee = dict(SALAIRES_DB)
                            for cle in cles_a_supprimer:
                                if cle in grille_nettoyee: del grille_nettoyee[cle]
                            db.db.collection("configuration_salaires").document("grille").set(grille_nettoyee)
                            st.cache_data.clear()
                            st.toast("🗑️ Entrées supprimées de la base Firebase Cloud avec succès !")
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
                    
            if st.button("✅ METTRE À JOUR LES TARIFS MATÉRIAUX", type="primary", use_container_width=True):
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
                
                submit_engin = st.form_submit_button("🚜 INSÉRER L'ENGIN DANS LE CATALOGUE GLOBAL", type="primary", use_container_width=True)
                
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
        # --- sub_tab5 : CONSULTATION BRUTE DES TABLES ---
        # ==============================================================================
        with sub_tab5:
            dict_modeles = db.charger_catalogue_chantiers()
            res_modeles = [dict_modeles[k] for k in dict_modeles if k != "Choisir un chantier pré-configuré..."]
            total_modeles = len(res_modeles)

            st.markdown(f"### 🗂️ Consultation brute complète ({total_modeles} chantiers en base)")
            choix_table = st.selectbox(
                "Choisir la table :", ["Modèles de Chantiers Pré-configurés", "Grille Salariale Actuelle", "Prix des Matériaux de base", "Catalogue de Location des Engins"]
            )
            if choix_table == "Modèles de Chantiers Pré-configurés":
                if res_modeles:
                    df_apercu = pd.DataFrame(res_modeles)
                    if "engins_requis" in df_apercu.columns: df_apercu = df_apercu.drop(columns=["engins_requis"])
                    colonnes_numeriques = df_apercu.select_dtypes(include=['number']).columns
                    df_stylise = df_apercu.style.format({col: lambda x: f"{x:,.0f}".replace(",", " ") if pd.notnull(x) else "-" for col in colonnes_numeriques})
                    st.dataframe(df_stylise, use_container_width=True, hide_index=True)
                else: 
                    st.info("Aucun modèle configuré sur votre base Firebase.")
            elif choix_table == "Grille Salariale Actuelle": 
                salaires_formates = {k: f"{v:,.0f}".replace(",", " ") + " €" for k, v in SALAIRES_DB.items()}
                st.json(salaires_formates)
            elif choix_table == "Prix des Matériaux de base": 
                materiaux_formates = {k: f"{v:,.0f}".replace(",", " ") + " €" for k, v in MATERIAUX_DB.items()}
                st.json(materiaux_formates)
            elif choix_table == "Catalogue de Location des Engins":
                catalogue_engins_brut = db.charger_catalogue_engins()
                if catalogue_engins_brut: 
                    res = [{"Engin Modèle": k, "Prix/j (€)": v} for k, v in catalogue_engins_brut.items()]
                    df_engins_apercu = pd.DataFrame(res)
                    df_engins_stylise = df_engins_apercu.style.format({"Prix/j (€)": lambda x: f"{x:,.0f}".replace(",", " ") + " €" if pd.notnull(x) else "-"})
                    st.dataframe(df_engins_stylise, use_container_width=True, hide_index=True)
                else: 
                    st.info("Catalogue vide.")

        # ==============================================================================
        # --- sub_tab6 : COMPARATEUR DE FICHES CHANTIERS ---
        # ==============================================================================
        with sub_tab6:
            st.markdown("### 🔎 Outil de Comparaison de Modèles Préfabriqués")
            dict_modeles_comp = db.charger_catalogue_chantiers()
            liste_selection_comp = [k for k in dict_modeles_comp.keys() if k != "Choisir un chantier pré-configuré..."]
            
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
                        "Indicateur structurel": ["Revenus Fixes du Modèle", "Durée Théorique (jours)", "Sable global requis", "Béton global requis", "Terre globale requise"],
                        f"Chantier A : {data_A.get('nom_modele', ch_A)}": [f"{data_A.get('revenus', 0):,.0f}".replace(",", " ") + " €", f"{data_A.get('jours', 0)} jours", f"{data_A.get('sable', 0)} t", f"{data_A.get('beton', 0)} t", f"{data_A.get('terre', 0)} t"],
                        f"Chantier B : {data_B.get('nom_modele', ch_B)}": [f"{data_B.get('revenus', 0):,.0f}".replace(",", " ") + " €", f"{data_B.get('jours', 0)} jours", f"{data_B.get('sable', 0)} t", f"{data_B.get('beton', 0)} t", f"{data_B.get('terre', 0)} t"]
                    }
                    st.table(pd.DataFrame(metrics_comparatives))
        # ==============================================================================
        # --- sub_tab7 : VÉRIFICATEUR DE DOUBLONS EN BLOC (PASSIF) ---
        # ==============================================================================
        with sub_tab7:
            st.markdown(f"### 🔍 Vérificateur de Chantiers en Bloc ({total_modeles} modèles en base)")
            st.write("Collez vos fiches brutes ci-dessous pour savoir instantanément si elles sont déjà présentes.")

            texte_verification_brut = st.text_area("Collez les chantiers à vérifier (Nom + Prix) :", value="", height=250, key="zone_texte_verif_bloc_doublons")
            
            if st.button("🔍 ANALYSER ET VÉRIFIER LA PRÉSENCE EN BASE", type="primary", use_container_width=True):
                if not texte_verification_brut.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    chantiers_existants = set()
                    for doc_id, data_m in dict_modeles.items():
                        if doc_id == "Choisir un chantier pré-configuré...": continue
                        nom_m = str(data_m.get("nom_modele", doc_id)).strip().lower()
                        prix_m = float(data_m.get("revenus", 0.0))
                        chantiers_existants.add((nom_m, prix_m))

                    lignes_verif = texte_verification_brut.split("\n")
                    chantiers_uniques_saisis = {} 
                    
                    for ligne in lignes_verif:
                        l_clean = ligne.strip()
                        if not l_clean: continue
                        
                        match_verif = re.search(r"^(.*?)\s+(\d[\d\s]+)\s+euros", l_clean, re.IGNORECASE)
                        if match_verif:
                            nom_extrait = match_verif.group(1).strip()
                            prix_net_txt = "".join(c for c in match_verif.group(2) if c.isdigit())
                            prix_extrait = float(prix_net_txt) if prix_net_txt else 0.0
                            
                            chantiers_uniques_saisis[(nom_extrait.lower(), prix_extrait)] = nom_extrait

                    resultats_analyse = []
                    for (nom_low, prix_val), nom_propre in chantiers_uniques_saisis.items():
                        statut = "🟢 Déjà enregistré (Doublon)" if (nom_low, prix_val) in chantiers_existants else "🔴 Absent de la base (Nouveau)"
                        resultats_analyse.append({"Nom du Chantier Détecté": nom_propre, "Revenus (€)": prix_val, "Statut Base Cloud": statut})

                    if resultats_analyse:
                        df_resultats = pd.DataFrame(resultats_analyse)
                        df_resultats = df_resultats.sort_values(by="Revenus (€)", ascending=True)
                        
                        total_analyses = len(df_resultats)
                        nb_nouveaux = len(df_resultats[df_resultats["Statut Base Cloud"].str.contains("🔴")])
                        nb_doublons = len(df_resultats[df_resultats["Statut Base Cloud"].str.contains("🟢")])
                        
                        c_v1, c_v2, c_v3 = st.columns(3)
                        with c_v1: st.metric("Chantiers uniques analysés", f"{total_analyses}")
                        with c_v2: st.metric("Nouveaux chantiers (Absents)", f"{nb_nouveaux}")
                        with c_v3: st.metric("Doublons détectés (À éviter)", f"{nb_doublons}")
                        
                        st.markdown("#### 📊 Rapport de présence NoSQL en Temps Réel :")
                        st.dataframe(
                            df_resultats, use_container_width=True, hide_index=True,
                            column_config={
                                "Nom du Chantier Détecté": st.column_config.TextColumn("Nom de la Fiche"),
                                "Revenus (€)": st.column_config.NumberColumn("Prix de l'Ouvrage", format="%d €"),
                                "Statut Base Cloud": st.column_config.TextColumn("Disponibilité")
                            }
                        )
                    else:
                        st.error("❌ L'algorithme n'a pas réussi à extraire de fiches valides.")

        # ==============================================================================
        # --- sub_tab8 : MONITEUR DE QUOTAS ET CONSOMMATION FIREBASE ---
        # ==============================================================================
        with sub_tab8:
            st.markdown("### 📊 Suivi de Consommation & Quotas Journaliers (Plan Gratuit)")
            st.write("Firestore comptabilise l'usage quotidien. Voici l'état estimé de vos limites système réinitialisées toutes les 24h par Google.")

            # --- NOUVEAUTÉ : CALCUL DU TEMPS RESTANT AVANT LA RÉINITIALISATION (09h00 Paris) ---
            import datetime
            import pytz
            
            # On se calfeutre sur le fuseau horaire de Paris
            tz_paris = pytz.timezone('Europe/Paris')
            maintenant = datetime.datetime.now(tz_paris)
            
            # La réinitialisation Firebase se fait à 09:00 heure de Paris
            cible_aujourdhui = maintenant.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if maintenant < cible_aujourdhui:
                echeance_reinit = cible_aujourdhui
            else:
                echeance_reinit = cible_aujourdhui + datetime.timedelta(days=1)
                
            temps_restant = echeance_reinit - maintenant
            heures_r, secondes_restantes = divmod(temps_restant.seconds, 3600)
            minutes_r, _ = divmod(secondes_restantes, 60)
            
            # Affichage du compte à rebours sous forme de badge d'information
            st.warning(f"⏱️ **Prochaine réinitialisation des quotas Google Firebase dans :** `{heures_r} heure(s) et {minutes_r} minute(s)` (chaque jour à 09h00)")

            # 1. Tentative de lecture du document des compteurs réels dans Firebase
            try:
                quota_doc = db.db.collection("configuration_systeme").document("quotas_journaliers").get()
                if quota_doc.exists:
                    donnees_quota = quota_doc.to_dict()
                else:
                    donnees_quota = {}
            except Exception:
                donnees_quota = {}

            # Récupération des valeurs enregistrées ou valeurs de secours par défaut si vide
            lectures_faites = int(donnees_quota.get("lectures", 1240))
            ecritures_faites = int(donnees_quota.get("ecritures", 315))
            suppressions_faites = int(donnees_quota.get("suppressions", 45))

            # Constantes officielles des limites gratuites Google Firebase (Plan Spark)
            LIMITE_LECTURES = 50000
            LIMITE_ECRITURES = 20000
            LIMITE_SUPPRESSIONS = 20000

            # 2. Calculs mathématiques des pourcentages et des restes
            pct_lectures = min(float(lectures_faites / LIMITE_LECTURES), 1.0)
            pct_ecritures = min(float(ecritures_faites / LIMITE_ECRITURES), 1.0)
            pct_suppressions = min(float(suppressions_faites / LIMITE_SUPPRESSIONS), 1.0)

            reste_lectures = LIMITE_LECTURES - lectures_faites
            reste_ecritures = LIMITE_ECRITURES - ecritures_faites
            reste_suppressions = LIMITE_SUPPRESSIONS - suppressions_faites

            # 3. Affichage visuel sous forme de cartes d'indicateurs (Metrics)
            c_q1, c_q2, c_v3 = st.columns(3)
            with c_q1:
                st.metric("Lectures Restantes", f"{reste_lectures:,.0f}".replace(",", " "), f"-{lectures_faites} faites", delta_color="inverse")
            with c_q2:
                st.metric("Écritures Restantes", f"{reste_ecritures:,.0f}".replace(",", " "), f"-{ecritures_faites} faites", delta_color="inverse")
            with c_v3:
                st.metric("Suppressions Restantes", f"{reste_suppressions:,.0f}".replace(",", " "), f"-{suppressions_faites} faites", delta_color="inverse")

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. Rendu visuel avec des barres de progression interactives
            st.markdown("**📉 Jauge d'utilisation des Lectures (Limite : 50 000 / jour) :**")
            st.progress(pct_lectures, text=f"{lectures_faites} / {LIMITE_LECTURES} ({pct_lectures*100:.1f}%)")

            st.markdown("**✍️ Jauge d'utilisation des Écritures (Limite : 20 000 / jour) :**")
            st.progress(pct_ecritures, text=f"{ecritures_faites} / {LIMITE_ECRITURES} ({pct_ecritures*100:.1f}%)")

            st.markdown("**🗑️ Jauge d'utilisation des Suppressions (Limite : 20 000 / jour) :**")
            st.progress(pct_suppressions, text=f"{suppressions_faites} / {LIMITE_SUPPRESSIONS} ({pct_suppressions*100:.1f}%)")

            # Bouton de rafraîchissement manuel
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 ACTUALISER LES COMPTEURS COMPTABLES", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

            # ==============================================================================
        # --- sub_tab9 : TRAÇABILITÉ ET JOURNAL DES ACTIONS (LOGS) ---
        # ==============================================================================
        with sub_tab9:
            st.markdown("### 📜 Journal d'Audit & Traçabilité NoSQL")
            st.write("Historique chronologique des modifications apportées aux configurations de l'entreprise.")

            # Lecture des logs depuis Firebase
            try:
                logs_stream = db.db.collection("journaux_actions").order_by("timestamp", direction="DESCENDING").limit(100).stream()
                liste_logs = [d.to_dict() for d in logs_stream]
            except Exception:
                liste_logs = []

            if liste_logs:
                df_logs = pd.DataFrame(liste_logs)
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
