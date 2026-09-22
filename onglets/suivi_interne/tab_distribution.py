# Contenu de : onglets/suivi_interne/tab_distribution.py
import streamlit as st
import pandas as pd
import database as db
from datetime import datetime
import pytz

# Importations sécurisées depuis ton dossier coops d'origine
from coops.calculs import compiler_compta_membres, appliquer_parts_et_primes, generer_excel_distribution_paye, envoyer_releve_sur_discord

def afficher_tab_distribution(nom_coop_active, joueur_actif, niveau_actuel, liste_flux_bruts):
    
    # Nettoyage préventif du pseudo du joueur actif
    joueur_actif = str(joueur_actif).strip()

    # ==================================================================
    # --- 1. INITIALISATION ET DÉTECTION DE LA DATE DE REPÈRE ---
    # ==================================================================
    if "point_reprise_date_compta" not in st.session_state or st.session_state.get("refresh_date_auto", True):
        date_detectee = None
        heure_detectee = None
        
        if liste_flux_bruts:
            try:
                # 🎯 Tentative 1 : Trouver le dernier versement de bénéfice
                versements = [f for f in liste_flux_bruts if str(f.get("type")).strip() == "VERS BENEF"]
                if versements:
                    versements_tries = sorted(
                        versements, 
                        key=lambda x: str(x.get("timestamp_enregistrement", "2000-01-01 00:00:00")), 
                        reverse=True
                    )
                    dernier_doc = next(iter(versements_tries), None)
                    if dernier_doc:
                        date_detectee = dernier_doc.get("date_jeu")
                        heure_detectee = dernier_doc.get("heure_jeu")
                
                # 🎯 Tentative 2 : S'il n'y a JAMAIS eu de versement, on prend la TOUT PREMIÈRE entrée historique
                if not date_detectee:
                    flux_anciens = sorted(
                        liste_flux_bruts, 
                        key=lambda x: str(x.get("timestamp_enregistrement", "2099-12-31 23:59:59"))
                    )
                    premier_doc = next(iter(flux_anciens), None)
                    if premier_doc:
                        date_detectee = premier_doc.get("date_jeu")
                        heure_detectee = premier_doc.get("heure_jeu", "00:00")
            except Exception:
                pass
                
        # Sécurité ultime si la base est totalement vide
        if not date_detectee:
            date_detectee = "17/09/2026"
            heure_detectee = "00:00"
            
        st.session_state["point_reprise_date_compta"] = str(date_detectee).strip()
        st.session_state["point_reprise_heure_compta"] = str(heure_detectee).strip()
        st.session_state["refresh_date_auto"] = False

    coop_snap = db.db.collection("cooperatives").document(nom_coop_active).get().to_dict() or {}
    
    # 🎯 Correction Doublons : Nettoyage des espaces pour la liste des membres inscrits
    membres_inscrits = [str(m).strip() for m in coop_snap.get("membres", [joueur_actif])]
    
    # 🎯 Correction Doublons : Nettoyage des espaces pour le dictionnaire des capitaux
    dict_capitaux = {}
    for doc in db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream():
        d_cap = doc.to_dict()
        j_nom = str(d_cap.get("joueur", "")).strip()
        if j_nom:
            dict_capitaux[j_nom] = float(d_cap.get("montant", 0.0))

    # ==================================================================
    # --- 2. FILTRAGE CHRONOLOGIQUE ET EXTRACTION DES FLUX ---
    # ==================================================================
    liste_flux = []
    ids_traites = set()
    
    global_ventes = 0
    global_quantite = 0.0
    global_benefices_totaux = 0.0
    
    periode_ventes = 0
    periode_quantite = 0.0
    periode_benefices_bruts_periode = 0.0
    total_deja_verse = 0.0

    try:
        date_limite_cle = int("".join(reversed(st.session_state["point_reprise_date_compta"].split("/"))))
    except Exception:
        date_limite_cle = 20260827

    if liste_flux_bruts:
        for fl in liste_flux_bruts:
            # 🎯 Correction Doublons : On nettoie le nom du joueur de la ligne en cours
            if "joueur" in fl:
                fl["joueur"] = str(fl["joueur"]).strip()
            if "acteur" in fl:
                fl["acteur"] = str(fl["acteur"]).strip()
                
            t_mouv = str(fl.get("type", "")).strip()
            d_txt = str(fl.get("date_jeu", "01/01/2000")).strip()
            
            # Décompte du déjà versé historique global
            if t_mouv == "VERS BENEF":
                mats_dict = fl.get("materiaux", {})
                if isinstance(mats_dict, dict):
                    total_deja_verse += float(mats_dict.get("argent_total", mats_dict.get("argent", 0.0)))
                continue 

            # Dédoublonnage structurel Firestore
            doc_id = fl.get("ID_Document_Firestore", "")
            id_normalise = doc_id.replace("['", "").replace("']", "").strip() if doc_id else ""
            if id_normalise in ids_traites and id_normalise: 
                continue
            if id_normalise: 
                ids_traites.add(id_normalise)

            if t_mouv in ["ACHAT_INTERNE", "ACHAT_EXTERNE"]:
                mats_dict = fl.get("materiaux", {})
                if isinstance(mats_dict, dict):
                    volume_ligne = sum(mats_dict.values())
                    
                    # Accumulation Globale (Ligne 1)
                    global_ventes += 1
                    global_quantite += volume_ligne
                    global_benefices_totaux += (volume_ligne * 1.0)
                    
                    # Accumulation de la Période (Ligne 2)
                    try:
                        cle_doc_actuel = int("".join(reversed(d_txt.split("/"))))
                        if cle_doc_actuel >= date_limite_cle:
                            periode_ventes += 1
                            periode_quantite += volume_ligne
                            periode_benefices_bruts_periode += (volume_ligne * 1.0)
                            liste_flux.append(fl)
                    except Exception:
                        liste_flux.append(fl)
            else:
                liste_flux.append(fl)

    # ==================================================================
    # --- 3. RENDU DU TABLEAU 1 (GRAND LIVRE DE LA SEMAINE) ---
    # ==================================================================
    st.markdown("#### 📑 Grand Livre des Comptes Associés (Top 4 Membres)")
    compta_brute = compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits)
    
    if compta_brute:
        # 🎯 FORCE LA FUSION DES DOUBLONS DE PSEUDOS (casse et espaces invisibles)
        compta_nettoyee = {}
        for pseudo, donnees in compta_brute.items():
            # On nettoie et on capitalise (ex: "grego73 ", "Grego73" -> "Grego73")
            pseudo_unique = str(pseudo).strip().capitalize()
            
            if pseudo_unique in compta_nettoyee:
                # Si le joueur existe déjà dans le tableau, on additionne ses valeurs pour fusionner les lignes
                for cle_valeur, valeur in donnees.items():
                    if isinstance(valeur, (int, float)):
                        compta_nettoyee[pseudo_unique][cle_valeur] = compta_nettoyee[pseudo_unique].get(cle_valeur, 0.0) + valeur
            else:
                compta_nettoyee[pseudo_unique] = donnees.copy()
            
        df_coop = pd.DataFrame.from_dict(compta_nettoyee, orient='index')
        df_coop, id_log = appliquer_parts_et_primes(df_coop)
        df_coop.index.name = "Pseudo Membre"
        df_coop = df_coop.reset_index()
        df_coop["Pseudo Membre"] = df_coop["Pseudo Membre"].str.strip()

        st.dataframe(
            df_coop, width="stretch", hide_index=True,
            column_config={"Distribution Bénéfice (%)": st.column_config.NumberColumn("Distribution Bénéfice (%)", format="%.2f %%")}
        )
        if id_log: 
            st.success(f"👑 **Responsable Logistique de la semaine :** [{str(id_log).strip()}]")

        # ==================================================================
        # --- 4. POSITIONNEMENT DE LA LIGNE 2 (SOUS LE TABLEAU 1) ---
        # ==================================================================
        st.write("")
        st.markdown(f"##### 🔄 **Ligne 2 : Période Actuelle (Depuis le repère)**")
        c_per1, c_per2, c_per3, c_per4 = st.columns(4)
        with c_per1: st.metric(label="📊 Ventes Période", value=f"{periode_ventes} trans.")
        with c_per2: st.metric(label="🧱 Quantité Période", value=f"{int(periode_quantite):,}".replace(",", " ") + " u")
        with c_per3: st.metric(label="📈 Bénéfices Restants", value=f"{int(periode_benefices_bruts_periode):,}".replace(",", " ") + " €")
        with c_per4:
            saisie_date = st.text_input("📅 Date du Repère :", value=st.session_state["point_reprise_date_compta"], key="input_repere_dynamique_coop")
            if saisie_date != st.session_state["point_reprise_date_compta"]:
                st.session_state["point_reprise_date_compta"] = str(saisie_date).strip()
                st.rerun()
        st.markdown("---")

        # ==================================================================
        # --- 5. RENDU DU TABLEAU 2 (BILAN HISTORIQUE SANS CAPITAL) ---
        # ==================================================================
        st.markdown("##### 📈 Suivi des Investissements & Rendement de l'Activité")
        
        primes_totales_joueurs = {}
        if liste_flux_bruts:
            for flux_doc in liste_flux_bruts:
                if str(flux_doc.get("type")).strip() == "VERS BENEF":
                    mats_dict = flux_doc.get("materiaux", {})
                    if isinstance(mats_dict, dict):
                        a_des_parts = any(cle.startswith("part_") for cle in mats_dict.keys())
                        if a_des_parts:
                            for cle, valeur in mats_dict.items():
                                if cle.startswith("part_"):
                                    p_nom = str(cle.replace("part_", "")).strip()
                                    primes_totales_joueurs[p_nom] = primes_totales_joueurs.get(p_nom, 0.0) + float(valeur)
                        else:
                            if membres_inscrits:
                                for m in membres_inscrits:
        lignes_activite_globale = []
        for m in membres_inscrits:
            cumul_reappro = 0.0
            cumul_achats = 0.0
            
            if liste_flux_bruts:
                for fl_brut in liste_flux_bruts:
                    user_brut = str(fl_brut.get("joueur", fl_brut.get("acteur", ""))).strip()
                    t_mouv_brut = str(fl_brut.get("type")).strip()
                    mats_brut_dict = fl_brut.get("materiaux", {})
                    qte_brut = float(sum(mats_brut_dict.values())) if isinstance(mats_brut_dict, dict) else 0.0
                    
                    if t_mouv_brut == "REAPPROVISIONNEMENT":
                        if user_brut == m: 
                            cumul_reappro += qte_brut
                        elif user_brut in ["Réapprovisionnement Global", ""]: 
                            cumul_reappro += (qte_brut / len(membres_inscrits))
                    elif user_brut == m and t_mouv_brut in ["ACHAT_INTERNE", "ACHAT_EXTERNE"]:
                        cumul_achats += qte_brut
            
            dividendes_percus = primes_totales_joueurs.get(m, 0.0)
            
            lignes_activite_globale.append({
                "Membre": m,
                "Réappro Total (u)": int(cumul_reappro),
                "Achats Totaux (u)": int(cumul_achats),
                "Primes Touchées (€)": int(dividendes_percus)
            })
            
        df_activite_globale = pd.DataFrame(lignes_activite_globale)
        # Regroupement par membre au cas où un doublon persisterait
        df_activite_globale = df_activite_globale.groupby("Membre", as_index=False).sum()
        df_activite_globale = df_activite_globale.sort_values(by="Primes Touchées (€)", ascending=False)
        
        st.dataframe(
            df_activite_globale, width="stretch", hide_index=True,
            column_config={
                "Membre": st.column_config.TextColumn("👤 Membre"),
                "Réappro Total (u)": st.column_config.NumberColumn("🧱 Réappro Total (u)", format="%d u"),
                "Achats Totaux (u)": st.column_config.NumberColumn("🛒 Achats Totaux (u)", format="%d u"),
                "Primes Touchées (€)": st.column_config.NumberColumn("💵 Primes Touchées (€)", format="%d €")
            }
        )

        # ==================================================================
        # --- 6. POSITIONNEMENT DE LA LIGNE 1 (SOUS LE TABLEAU 2) ---
        # ==================================================================
        st.write("")
        st.markdown("##### 🌍 **Ligne 1 : Historique Global (Depuis la 1ère entrée)**")
        c_glob1, c_glob2, c_glob3, c_glob4 = st.columns(4)
        with c_glob1: st.metric(label="📊 Ventes Globales", value=f"{global_ventes} trans.")
        with c_glob2: st.metric(label="🧱 Quantité Globale", value=f"{int(global_quantite):,}".replace(",", " ") + " u")
        with c_glob3: st.metric(label="📈 Bénéfices Globaux", value=f"{int(global_benefices_totaux):,}".replace(",", " ") + " €")
        with c_glob4: st.metric(label="💰 Déjà Versé (Total)", value=f"{int(total_deja_verse):,}".replace(",", " ") + " €")
        st.markdown("---")

        # ==================================================================
        # --- 7. CALCULATEUR DE PAYE AUTOMATISÉ (COMMISSION DYNAMIQUE) ---
        # ==================================================================
        pourcentage_coop = float(coop_snap.get("pourcentage_commission", 10.0)) / 100.0
        st.markdown(f"##### 💵 Calculateur de Paye & Routage Discord (Configuré à {pourcentage_coop * 100:.1f}%)")
        c_p1, c_p2 = st.columns(2)
        with c_p1: 
            valeur_calculee = float(int(periode_benefices_bruts_periode * pourcentage_coop))
            caisse_saisie = st.number_input(
                "Bénéfice total à distribuer (€) :", min_value=0.0, value=valeur_calculee, step=100.0,
                key=f"saisie_caisse_dynamique_coop_pct_{pourcentage_coop}"  
            )
        with c_p2:
            st.write("")
            data_paye_bytes = generer_excel_distribution_paye(df_coop, caisse_saisie, id_log)
            st.download_button(label="📥 TÉLÉCHARGER LE RELEVÉ EXCEL", data=data_paye_bytes, file_name="releve_paye.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        if st.button("🚀 EXPÉDIER LE BILAN ET LA PAIE SUR DISCORD", type="primary", width="stretch"):
            with st.spinner("Envoi sur Discord..."):
                statut, msg = envoyer_releve_sur_discord(nom_coop_active, joueur_actif, df_coop, liste_flux, caisse_saisie, id_log, data_paye_bytes, "releve.xlsx")
                if statut: 
                    st.success(msg)
                    tz_paris = pytz.timezone('Europe/Paris')
                    maintenant = datetime.now(tz_paris)
                    parts_membres_dict = {"argent_total": float(caisse_saisie)}
                    for _, row in df_coop.iterrows():
                        pseudo_m = str(row["Pseudo Membre"]).strip()
                        pourcentage = float(row["Distribution Bénéfice (%)"])
                        parts_membres_dict[f"part_{pseudo_m}"] = round((float(caisse_saisie) * pourcentage) / 100.0, 2)
                    
                    db.enregistrer_ligne_historique_brute(nom_coop_active, maintenant.strftime("%d/%m/%Y"), maintenant.strftime("%H:%M"), joueur_actif, "VERS BENEF", parts_membres_dict)
                    st.cache_data.clear()
                    db.charger_flux_coop_cache.clear()
                    st.rerun()
                else: 
                    st.error(msg)

        # ==================================================================
        # --- 8. HISTORIQUE NOMINATIF DES VERSEMENTS ---
        # ==================================================================
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 📜 Historique Nominatif des Versements Effectués")
        
        cumul_versements_joueurs = {}
        grand_total_distribue = 0.0
        
        if liste_flux_bruts:
            for flux_doc in liste_flux_bruts:
                if str(flux_doc.get("type")).strip() == "VERS BENEF":
                    mats_dict = flux_doc.get("materiaux", {})
                    if isinstance(mats_dict, dict):
                        montant_transaction = float(mats_dict.get("argent_total", mats_dict.get("argent", 0.0)))
                        grand_total_distribue += montant_transaction
                        
                        a_des_parts_nominatives = any(cle.startswith("part_") for cle in mats_dict.keys())
                        if a_des_parts_nominatives:
                            for cle, valeur in mats_dict.items():
                                if cle.startswith("part_") and valeur:
                                    pseudo_extrait = str(cle.replace("part_", "")).strip()
                                    cumul_versements_joueurs[pseudo_extrait] = cumul_versements_joueurs.get(pseudo_extrait, 0.0) + float(valeur)
                        else:
                            if membres_inscrits:
                                part_egale = montant_transaction / len(membres_inscrits)
                                for m in membres_inscrits:
                                    cumul_versements_joueurs[m] = cumul_versements_joueurs.get(m, 0.0) + part_egale

        if cumul_versements_joueurs:
            lignes_recap_versements = []
            for j_nom, total_recu in cumul_versements_joueurs.items():
                lignes_recap_versements.append({
                    "Collaborateur associé": f"👤 {j_nom}",
                    "Statut de l'équipe": "🏆 Membre Inscrit" if j_nom in membres_inscrits else "🏃 Ancien Collaborateur",
                    "Total des Primes Touchées (€)": int(total_recu)
                })
            
            df_recap_versements = pd.DataFrame(lignes_recap_versements).sort_values(by="Total des Primes Touchées (€)", ascending=False)
            st.dataframe(
                df_recap_versements, width="stretch", hide_index=True,
                column_config={
                    "Collaborateur associé": st.column_config.TextColumn("👤 Bénéficiaire"),
                    "Statut de l'équipe": st.column_config.TextColumn("🏷️ Statut"),
                    "Total des Primes Touchées (€)": st.column_config.NumberColumn("💰 Total Perçu", format="%d €")
                }
            )
            st.info(f"📈 **Bilan Comptable Global :** Un montant total cumulé de **{int(grand_total_distribue):,}".replace(",", " ") + " €** a été reversé à l'équipe depuis l'ouverture de la coopérative.")
        else:
            st.info("💡 Aucun versement n'a été détecté dans l'historique pour le moment.")
