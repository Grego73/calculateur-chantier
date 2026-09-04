# Contenu complet, sécurisé et configuré avec réinvestissements pour : onglets/suivi_interne.py

import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS):
    st.markdown("### 👥 Espace de Planification & Suivi des Coopératives")
    
    # 1. INITIALISATION ET VÉRIFICATION DE L'AUTHENTIFICATION SÉCURISÉE
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None

    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement Joueur")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            
            nom_coop_finale = ""
            if coop_selection == "➕ Créer une nouvelle coopérative...":
                nom_coop_finale = st.text_input("Saisissez le NOM de la nouvelle Coopérative :").strip()
            elif coop_selection != "-- Choisir une coopérative existante --":
                nom_coop_finale = coop_selection

            mdp_input = st.text_input("Mot de passe de la Coopérative :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique (Joueur) :").strip()
            
            btn_soumettre = st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch")
            
            if btn_soumettre:
                if coop_selection == "-- Choisir une coopérative existante --":
                    st.error("⚠️ Veuillez sélectionner une coopérative dans la liste déroulante.")
                elif coop_selection == "➕ Créer une nouvelle coopérative..." and not nom_coop_finale:
                    st.error("⚠️ Veuillez donner un nom à votre nouvelle coopérative.")
                elif not mdp_input or not pseudo_input:
                    st.error("⚠️ Le mot de passe et le pseudo sont obligatoires.")
                else:
                    succes, message = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                    if succes:
                        st.session_state["auth_suivi_coop"] = nom_coop_finale
                        st.session_state["auth_suivi_joueur"] = pseudo_input
                        st.cache_data.clear()
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        return

    # ==============================================================================
    # --- INTERFACE ACTIVE APRÈS CONNEXION RÉUSSIE ---
    # ==============================================================================
    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]

    c_head1, c_head2 = st.columns(2)
    with c_head1:
        st.success(f"🔓 Coopérative active : **{nom_coop_active}** | Session : **{joueur_actif}**")
    with c_head2:
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None
            st.session_state["auth_suivi_joueur"] = None
            st.rerun()

    st.markdown("---")

    tab_coop_interne, tab_joueurs_externes, tab_depot_flux, tab_gestion_membres = st.tabs([
        "🏆 1. Parts & Bénéfices de la Coop (Max 4)", 
        "🌍 2. Marché Global & Matériau Favori",
        "📥 Déposer l'Historique du Jeu",
        "⚙️ Gérer les Collaborateurs"
    ])

    # --- LECTURE COMPTABLE DE FIRESTORE ---
    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]

    capital_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream()
    dict_capitaux = {doc.to_dict().get("joueur"): doc.to_dict().get("montant", 0.0) for doc in capital_stream}

    coop_ref = db.db.collection("cooperatives").document(nom_coop_active).get()
    membres_inscrits = coop_ref.to_dict().get("membres", []) if coop_ref.exists else [joueur_actif]

    # ==============================================================================
    # --- TABLEAU 1 : AFFICHAGE AVEC COLONNES CAPITAL & REINVESTISSEMENTS ---
    # ==============================================================================
    with tab_coop_interne:
        st.markdown("#### 📊 Grand Livre des Comptes Associés (Top 4 Membres)")
        st.caption("Suivi précis des apports financiers de départ, des réinvestissements ultérieurs et des coefficients de dividendes.")

        compta_membres = {
            m: {
                "Capital Départ (€)": float(dict_capitaux.get(m, 0.0)),
                "Réinvestissements (€)": 0.0,
                "Réappro Matériaux (u)": 0.0, 
                "Consommation (u)": 0.0, 
                "Score d'Apport Total": float(dict_capitaux.get(m, 0.0))
            } for m in membres_inscrits
        }

        # Parsing comptable cumulé
        for fl in liste_flux:
            user = fl.get("joueur")
            if user not in compta_membres: continue
            
            t_mouv = fl.get("type")
            cash = fl.get("apport_cash", 0.0)
            mats_qte = sum(fl.get("materiaux", {}).values())

            if t_mouv == "REINVESTISSEMENT_CASH":
                compta_membres[user]["Réinvestissements (€)"] += cash
                compta_membres[user]["Score d'Apport Total"] += cash
            elif t_mouv == "REAPPROVISIONNEMENT":
                compta_membres[user]["Réappro Matériaux (u)"] += mats_qte
                compta_membres[user]["Score d'Apport Total"] += (mats_qte * 30.0)
            elif t_mouv == "ACHAT_INTERNE":
                compta_membres[user]["Consommation (u)"] += mats_qte

        if compta_membres:
            df_coop = pd.DataFrame.from_dict(compta_membres, orient='index')
            total_points_coop = df_coop["Score d'Apport Total"].sum()
            
            if total_points_coop > 0:
                df_coop["Distribution Bénéfice (%)"] = (df_coop["Score d'Apport Total"] / total_points_coop) * 100
            else:
                df_coop["Distribution Bénéfice (%)"] = 100.0 / len(df_coop) if len(df_coop) > 0 else 0.0

            df_coop.index.name = "Pseudo Membre"
            df_coop = df_coop.reset_index()

            st.dataframe(
                df_coop, width="stretch", hide_index=True,
                column_config={
                    "Pseudo Membre": st.column_config.TextColumn("👤 Membre de la Coop"),
                    "Capital Départ (€)": st.column_config.NumberColumn("💰 Capital Initial", format="%.0f €"),
                    "Réinvestissements (€)": st.column_config.NumberColumn("➕ Réinvestissements Cash", format="%.0f €"),
                    "Réappro Matériaux (u)": st.column_config.NumberColumn("🧱 Matériaux Apportés (Qté)"),
                    "Consommation (u)": st.column_config.NumberColumn("🛒 Consommation (Qté)"),
                    "Score d'Apport Total": st.column_config.NumberColumn("📈 Score Global", format="%.0f pts"),
                    "Distribution Bénéfice (%)": st.column_config.NumberColumn("🏆 Distribution Bénéfice légitime", format="%.2f %%")
                }
            )
        else:
            st.info("Aucune donnée comptable n'est encore enregistrée.")

    # ==============================================================================
    # --- TABLEAU 2 : TOUS LES AUTRES JOUEURS EXTERNES ---
    # ==============================================================================
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Registre Général des Flux du Marché (Joueurs Externes)")
        st.caption("Analyse les volumes de l'ensemble des acteurs hors-coopérative.")

        flux_globaux = db.charger_tous_les_achats_globaux()

        if not flux_globaux:
            st.info("💡 Aucun mouvement global n'est enregistré sur le réseau.")
        else:
            stats_externes = {}
            for f_g in flux_globaux:
                j_nom = f_g.get("joueur", "Inconnu")
                if j_nom in membres_inscrits or j_nom.lower().startswith("réappro"): continue
                
                if j_nom not in stats_externes:
                    stats_externes[j_nom] = {"Volume Total Acheté (u)": 0.0, "detail_mats": {}}

                mats_dict = f_g.get("materiaux", {})
                for m_key, m_val in mats_dict.items():
                    stats_externes[j_nom]["Volume Total Acheté (u)"] += m_val
                    stats_externes[j_nom]["detail_mats"][m_key] = stats_externes[j_nom]["detail_mats"].get(m_key, 0.0) + m_val

            lignes_externes_affichage = []
            for joueur_ex, data_ex in stats_externes.items():
                details_ressources = data_ex["detail_mats"]
                if details_ressources:
                    materiau_favori = max(details_ressources, key=details_ressources.get).capitalize()
                    volume_favori = details_ressources[max(details_ressources, key=details_ressources.get)]
                    txt_recap_favori = f"{materiau_favori} ({int(volume_favori)} u)"
                else:
                    txt_recap_favori = "Aucun"

                lignes_externes_affichage.append({
                    "Joueur": joueur_ex,
                    "Volume Global Acquis (u)": data_ex["Volume Total Acheté (u)"],
                    "Matériau le plus acheté": txt_recap_favori
                })

            if lignes_externes_affichage:
                df_ext = pd.DataFrame(lignes_externes_affichage)
                
                st.dataframe(df_ext, width="stretch", hide_index=True)
            else:
                st.info("💡 Aucun joueur externe n'a encore été extrait de vos lignes d'historiques.")

    # ==============================================================================
    # --- 3. PARSEUR AUTOMATIQUE DE LOGS CHRONOLOGIQUES ---
    # ==============================================================================
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        st.write("Collez l'historique brut du jeu ici. Le parseur filtre et applique automatiquement les entrées temporelles uniques.")

        zone_texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=300, key="txt_logs_flux_coop_final_v4")

        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch"):
            if not zone_texte_logs.strip():
                st.error("❌ Veuillez coller du texte avant de valider.")
            else:
                lignes_brutes = zone_texte_logs.split("\n")
                
                regex_date = re.compile(r"Le\s*(\d{2}/\d{2}/\d{4})\s*à\s*(\d{2}:\d{2})", re.IGNORECASE)
                regex_materiau = re.compile(r"(\d[\d\s]*)\s*(tonne|unité|unite)[s]?\s*de\s*(sable|terre|enrob|armature|tôle|tole|béton|beton|panneau|tuyau|canalisation|poutre)", re.IGNORECASE)
                
                date_courante = None
                heure_courante = None
                compteur_enregistres = 0

                for i, lg in enumerate(lignes_brutes):
                    l_clean = lg.strip()
                    if not l_clean: continue

                    match_date = regex_date.search(l_clean)
                    if match_date:
                        date_courante = match_date.group(1)
                        heure_courante = match_date.group(2)
                        continue

                    if date_courante and heure_courante:
                        match_mat = regex_materiau.search(l_clean)
                        if match_mat:
                            qte_val = float(match_mat.group(1).replace(" ", ""))
                            type_mat_brut = match_mat.group(3).lower()

                            mat_cle = None
                            if "sable" in type_mat_brut: mat_cle = "sable"
                            elif "terre" in type_mat_brut: mat_cle = "terre"
                            elif "enrob" in type_mat_brut: mat_cle = "enrobe"
                            elif "armature" in type_mat_brut: mat_cle = "armature"
                            elif "tôle" in type_mat_brut or "tole" in type_mat_brut: mat_cle = "tole"
                            elif "béton" in type_mat_brut or "beton" in type_mat_brut: mat_cle = "beton"
                            elif "panneau" in type_mat_brut: mat_cle = "panneaux"
                            elif "tuyau" in type_mat_brut: mat_cle = "tuyaux"
                            elif "canalisation" in type_mat_brut: mat_cle = "canalisations"
                            elif "poutre" in type_mat_brut: mat_cle = "poutres"

                            if mat_cle:
                                if "réapprovisionnement" in l_clean.lower():
                                    acteur_final = "Réapprovisionnement Global"
                                    type_mouv_final = "REAPPROVISIONNEMENT"
                                elif "a acheté" in l_clean.lower():
                                    acteur_final = l_clean.split("a acheté")[0].strip()
                                    type_mouv_final = "ACHAT_INTERNE" if acteur_final in membres_inscrits else "ACHAT_EXTERNE"
                                else:
                                    acteur_final = joueur_actif
                                    type_mouv_final = "REAPPROVISIONNEMENT"

                                db.enregistrer_ligne_historique_brute(
                                    nom_coop_active, date_courante, heure_courante, 
                                    acteur_final, type_mouv_final, {mat_cle: qte_val}
                                )
                                compteur_enregistres += 1

                if compteur_enregistres > 0:
                    st.success(f"🎯 Traitement terminé ! {compteur_enregistres} ligne(s) d'événements synchronisée(s).")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Aucun bloc chronologique ou matériel valide détecté.")

    # ==============================================================================
    # --- 4. GESTION DES REINVESTISSEMENTS ET DES COLLABORATEURS ---
    # ==============================================================================
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Panneau de Recrutement & Registre des Flux Financiers")
        
        slots_occupes = len(membres_inscrits)
        st.info(f"📊 **Occupation de la Coopérative :** `{slots_occupes} / 4` places verrouillées.")
        
        # --- BLOC N°1 : REINVESTIR DE L'ARGENT SUR LE COMPTE DE LA COOP ---
        st.markdown("##### ➕ Enregistrer un NOUVEAU Réinvestissement Cash (Rallonge)")
        st.write("Si un collaborateur réinjecte des fonds pour financer l'entreprise, déclarez sa rallonge ici :")
        
        with st.form("form_nouveau_reinvestissement_cash"):
            c_re1, c_fl2 = st.columns(2)
            with c_re1:
                membre_reinvestit = st.selectbox("Sélectionner le collaborateur :", membres_inscrits)
            with c_fl2:
                montant_rallonge = st.number_input("Montant de l'apport complémentaire (€) :", min_value=0.0, value=0.0, step=5000.0)
                
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE AU SCORE GLOBAL", width="stretch"):
                if montant_rallonge <= 0:
                    st.error("❌ Veuillez saisir un montant supérieur à 0 €.")
                else:
                    db.ajouter_reinvestissement_membre(nom_coop_active, membre_reinvestit, montant_rallonge)
                    st.success(f"🎯 Rallonge financière de {montant_rallonge:,.0f} € validée pour [ {membre_reinvestit} ] ! Recalcul des parts instantané.".replace(",", " "))
                    st.cache_data.clear()
                    st.rerun()
                    
        st.markdown("---")
        
        # --- BLOC N°2 : ÉDITION DU CAPITAL DE DÉPART (LES 50K / 100K D'ORIGINE) ---
        st.markdown("##### 💰 Éditer le Capital Initial d'Origine de vos collaborateurs")
        with st.form("form_ajustement_capitaux_coop"):
            champs_capitaux = {}
            for mb in membres_inscrits:
                capital_actuel = float(dict_capitaux.get(mb, 0.0))
                champs_capitaux[mb] = st.number_input(
                    f"Capital de base pour [ {mb} ] (€) :", 
                    min_value=0.0, 
                    value=capital_actuel, 
                    step=10000.0,
                    key=f"input_ajust_cap_{mb}"
                )
            
            if st.form_submit_button("💾 VERROUILLER LE COMPTE DE BASE", width="stretch"):
                for mb_nom, val_money in champs_capitaux.items():
                    db.fixer_capital_initial_membre(nom_coop_active, mb_nom, val_money)
                st.success("🎯 Tous les investissements de base ont été verrouillés et synchronisés.")
                st.cache_data.clear()
                st.rerun()

        st.markdown("---")
        if slots_occupes < 4:
            st.markdown("##### ➕ Étape 2 : Ajouter de nouveaux collaborateurs")
            texte_bloc_membres = st.text_input(
                "Saisissez les pseudos manquants (séparés par un espace) :", 
                value="", 
                placeholder="Ex: Grego73 Adri1 Julo Ctims"
            ).strip()
            
            if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch"):
                if not texte_bloc_membres:
                    st.error("⚠️ Saisissez au moins un pseudo.")
                else:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        st.success(msg_ins)
                        st.rerun()
                    else:
                        st.error(msg_ins)
        else:
            st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")
