# Contenu complet validé et structuré pour : onglets/suivi_interne.py
import streamlit as st
import pandas as pd
import database as db

# Importations depuis le package coops
from coops.calculs import compiler_compta_membres, appliquer_parts_et_primes, generer_excel_distribution_paye, envoyer_releve_sur_discord
from coops.parseur import analyser_historique_brut

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB):
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None
    if "coop_privilege_level" not in st.session_state:
        st.session_state["coop_privilege_level"] = 1

    # --- ÉCRAN DE CONNEXION ÉPURÉ (UNE SEULE CASE DE MOT DE PASSE) ---
    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            nom_coop_finale = st.text_input("Saisissez le NOM de la Coop :").strip() if coop_selection == "➕ Créer une nouvelle coopérative..." else (coop_selection if coop_selection != "-- Choisir une coopérative existante --" else "")
            
            st.caption("💡 Si vous créez une Coop, le mot de passe ci-dessous deviendra votre code Créateur (Niveau 3).")
            mdp_input = st.text_input("Mot de passe (Ouvrier, Fiable ou Créateur) :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique :").strip()
            
            if st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch") and mdp_input and pseudo_input and nom_coop_finale:
                succes, message, niveau_attribue = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                if succes:
                    st.session_state["auth_suivi_coop"] = nom_coop_finale
                    st.session_state["auth_suivi_joueur"] = pseudo_input
                    st.session_state["coop_privilege_level"] = niveau_attribue
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)
        return

    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]
    niveau_actuel = st.session_state["coop_privilege_level"]

    dict_badges = {1: "👷 Niveau 1 : Ouvrier", 2: "🎖️ Niveau 2 : Membre Fiable", 3: "🏆 Niveau 3 : Créateur / Admin"}
    c_head1, c_head2 = st.columns(2)
    with c_head1: st.success(f"🔓 Coop : **{nom_coop_active}** | {dict_badges[niveau_actuel]}")
    with c_head2: 
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None; st.session_state["auth_suivi_joueur"] = None; st.session_state["coop_privilege_level"] = 1; st.rerun()

    st.markdown("---")
    tab_coop_interne, tab_joueurs_externes, tab_depot_flux, tab_gestion_membres = st.tabs(["🏆 1. Parts & Bénéfices de la Coop", "🌍 2. Marché Global", "📥 Déposer l'Historique du Jeu", "⚙️ Gérer les Droits & Associés"])

    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]
    
    coop_snap = db.db.collection("cooperatives").document(nom_coop_active).get().to_dict() or {}
    membres_inscrits = coop_snap.get("membres", [joueur_actif])
    dict_capitaux = {doc.to_dict().get("joueur"): doc.to_dict().get("montant", 0.0) for doc in db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream()}

    # --- TAB 1 : PARTS & DISTRIBUTION ---
    with tab_coop_interne:
        st.markdown("#### 📊 Grand Livre des Comptes Associés (Top 4 Membres)")
        compta_brute = compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits)
        if compta_brute:
            df_coop = pd.DataFrame.from_dict(compta_brute, orient='index')
            df_coop, id_log = appliquer_parts_et_primes(df_coop)
            df_coop.index.name = "Pseudo Membre"
            df_coop = df_coop.reset_index()

            st.dataframe(df_coop, width="stretch", hide_index=True)
            if id_log: st.success(f"👑 **Responsable Logistique de la semaine :** [{id_log}]")
            
            st.markdown("---")
            st.markdown("##### 💵 Calculateur de Paye & Routage Discord")
            c_p1, c_p2 = st.columns(2)
            with c_p1: caisse_saisie = st.number_input("Bénéfice total à distribuer (€) :", min_value=0.0, value=1000.0, step=500.0)
            with c_p2:
                st.write("")
                data_paye_bytes = generer_excel_distribution_paye(df_coop, caisse_saisie, id_log)
                st.download_button(label="📥 TÉLÉCHARGER LE RELEVÉ EXCEL", data=data_paye_bytes, file_name="releve_paye.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            
            # CORRECTIF : Alignement des paramètres pour envoyer_releve_sur_discord
            if st.button("🚀 EXPÉDIER LE BILAN ET LA PAIE SUR DISCORD", type="primary", width="stretch"):
                with st.spinner("Envoi du relevé de compte et du classement sur Discord..."):
                    # On envoie exactement les variables requises pour le calcul du Top Acheteurs
                    statut, msg = envoyer_releve_sur_discord(
                        nom_coop=nom_coop_active,
                        pseudo_emetteur=joueur_actif,
                        df_coop=df_coop,
                        benefice_total_caisse=caisse_saisie,
                        id_logisticien=id_log,
                        fichier_bytes=data_paye_bytes,
                        nom_fichier=f"releve_comptable_{nom_coop_active}.xlsx"
                    )
                    if statut: 
                        st.success(msg)
                    else: 
                        st.error(msg)

    # ==============================================================================
    # --- TAB 2 : MARCHE GLOBAL & CLASSEMENT GÉNÉRAL DES ACHETEURS ---
    # ==============================================================================
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Classement Général des Acheteurs (Membres & Clients)")
        st.caption("Registre centralisé et classé par volume d'achat total pour l'ensemble des acteurs du serveur.")

        if not liste_flux:
            st.info("💡 Aucun mouvement d'achat n'est enregistré sur le réseau pour le moment.")
        else:
            stats_globales = {}
            total_par_materiau = {}

            # Extraction et compilation des flux de tous les acheteurs du serveur
            for f_g in liste_flux:
                j_nom = f_g.get("joueur", "Inconnu")
                # On filtre les lignes de réapprovisionnement logistique pour ne garder que les achats
                if j_nom.lower().startswith("réappro") or f_g.get("type") == "REAPPROVISIONNEMENT": 
                    continue
                
                if j_nom not in stats_globales:
                    stats_globales[j_nom] = {"Volume Total Acheté (u)": 0.0, "detail_mats": {}}

                mats_dict = f_g.get("materiaux", {})
                for m_key, m_val in mats_dict.items():
                    m_key_cap = m_key.capitalize()
                    stats_globales[j_nom]["Volume Total Acheté (u)"] += m_val
                    stats_globales[j_nom]["detail_mats"][m_key_cap] = stats_globales[j_nom]["detail_mats"].get(m_key_cap, 0.0) + m_val
                    total_par_materiau[m_key_cap] = total_par_materiau.get(m_key_cap, 0.0) + m_val

            lignes_affichage = []
            for joueur, data_ex in stats_globales.items():
                details_ressources = data_ex["detail_mats"]
                if details_ressources:
                    # Détection automatique de la ressource la plus consommée par le joueur
                    materiau_favori = max(details_ressources, key=details_ressources.get)
                    volume_favori = details_ressources[materiau_favori]
                    txt_recap_favori = f"{materiau_favori} ({int(volume_favori)} u)"
                else:
                    txt_recap_favori = "Aucun"

                # Affectation du badge de statut (Interne ou Client Externe)
                badge_statut = "🏆 Membre Coop" if joueur in membres_inscrits else "👤 Client / Joueur Externe"

                lignes_affichage.append({
                    "Statut": badge_statut,
                    "Joueur": joueur,
                    "Volume Global Acquis (u)": data_ex["Volume Total Acheté (u)"],
                    "Matériau le plus acheté": txt_recap_favori
                })

            if lignes_affichage:
                # Création du DataFrame et tri automatique du plus grand au plus petit acheteur
                df_ext = pd.DataFrame(lignes_affichage).sort_values(by="Volume Global Acquis (u)", ascending=False).reset_index(drop=True)
                
                # Injection d'une colonne de classement dynamique (Rang #1, #2, #3...)
                df_ext.index = df_ext.index + 1
                df_ext.index.name = "Rang"
                df_ext = df_ext.reset_index()

                # Affichage du tableau de bord du Marché Global
                st.dataframe(
                    df_ext, width="stretch", hide_index=True,
                    column_config={
                        "Rang": st.column_config.NumberColumn("👑 Clst", format="#%d", width="small"),
                        "Statut": st.column_config.TextColumn("🏷️ Statut Réseau"),
                        "Joueur": st.column_config.TextColumn("👤 Pseudo de l'Acheteur"),
                        "Volume Global Acquis (u)": st.column_config.NumberColumn("📦 Volume Total (u)", format="%,d u"),
                        "Matériau le plus acheté": st.column_config.TextColumn("💎 Matériau Favori")
                    }
                )
                
                # --- LE RETOUR DE VOTRE GRAPHIQUE DES RESSOURCES ---
                st.markdown("---")
                st.markdown("### 📊 Classement des Matériaux les plus Consommés sur le Serveur")
                
                if total_par_materiau:
                    df_graph_mats = pd.DataFrame(list(total_par_materiau.items()), columns=["Matériau", "Quantité Totale Consommée (u)"])
                    df_graph_mats = df_graph_mats.sort_values(by="Quantité Totale Consommée (u)", ascending=True)
                    st.bar_chart(data=df_graph_mats, x="Matériau", y="Quantité Totale Consommée (u)", color="#ff4b4b")
            else:
                st.info("💡 Aucun volume d'achat n'a pu être extrait du fil des événements pour le moment.")

    # --- TAB 3 : PARSEUR LOGS ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_parseur_coop")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
            mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
            for mv in mouvements: db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            st.success(f"🎯 Synchronisation réussie !")
            st.cache_data.clear(); st.rerun()

    # --- TAB 4 : PANNEAU DE GESTION DES PASSES & ATTRIBUTION DES DROITS ---
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Gérer les Collaborateurs (Admin)")
        if niveau_actuel < 2:
            st.error("🔒 Accès refusé : Niveau 2 minimum requis pour voir l'administration.")
            return

        # Rallonge Cash (Niveau 2 et 3)
        with st.form("form_rallonge_cash"):
            m_rev = st.selectbox("Collaborateur :", membres_inscrits)
            m_cash = st.number_input("Montant de la rallonge (€) :", min_value=0.0, step=1000.0)
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE") and m_cash > 0:
                db.ajouter_reinvestissement_membre(nom_coop_active, m_rev, m_cash)
                st.cache_data.clear(); st.rerun()

        # Commandes exclusives du Créateur (Niveau 3)
        if niveau_actuel >= 3:
            st.markdown("---")
            st.markdown("##### 👑 1. Attribution des Mots de Passe des Grades")
            st.write("En tant que Créateur, définissez ici les mots de passe que vous donnerez à vos employés.")
            
            with st.form("form_gestion_mots_de_passe_grades"):
                nouveau_mdp_niv1 = st.text_input("Définir le mot de passe Ouvriers (Niveau 1) :", value=str(coop_snap.get("mdp_niveau1", "")))
                nouveau_mdp_niv2 = st.text_input("Définir le mot de passe Membres Fiables (Niveau 2) :", value=str(coop_snap.get("mdp_niveau2", "")))
                nouveau_mdp_niv3 = st.text_input("Changer votre mot de passe Créateur (Niveau 3) :", value=str(coop_snap.get("mdp_niveau3", "")))
                
                if st.form_submit_button("💾 VERROUILLER ET SAUVEGARDER LES CODES", width="stretch"):
                    db.db.collection("cooperatives").document(nom_coop_active).update({
                        "mdp_niveau1": nouveau_mdp_niv1,
                        "mdp_niveau2": nouveau_mdp_niv2,
                        "mdp_niveau3": nouveau_mdp_niv3
                    })
                    st.success("🟢 Les mots de passe des grades ont été mis à jour avec succès ! Vous pouvez maintenant les distribuer.")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 🚨 2. Zone de Licenciement & Recrutement")
            m_retirer = st.selectbox("Membre à licencier :", ["-- Choisir un membre --"] + membres_inscrits, key="del_mb_key")
            if m_retirer != "-- Choisir un membre --" and st.checkbox("Confirmer le licenciement de " + m_retirer):
                if st.button("🗑️ RETIRER LE MEMBRE", type="primary", width="stretch"):
                    try:
                        coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                        membres_actuels = coop_doc_ref.get().to_dict().get("membres", [])
                        if m_retirer in membres_actuels:
                            membres_actuels.remove(m_retirer)
                            coop_doc_ref.update({"membres": membres_actuels})
                            
                            db.enregistrer_log(
                                type_action="COOPERATIVE", 
                                details=f"Le Créateur [{joueur_actif}] a retiré le membre [{m_retirer}] de la coopérative [{nom_coop_active}]."
                            )
                            
                            if m_retirer == joueur_actif: 
                                st.session_state["auth_suivi_coop"] = None
                                st.session_state["auth_suivi_joueur"] = None
                                st.session_state["coop_privilege_level"] = 1
                                
                            st.success(f"🏃 {m_retirer} a été retiré avec succès !")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors du retrait : {e}")

            # 3. RECRUTEMENT EN BLOC RÉSERVE AU NIVEAU 3
            st.markdown("---")
            slots_occupes = len(membres_inscrits)
            if slots_occupes < 4:
                st.markdown("##### ➕ 3. Recrutement de Collaborateurs en Bloc")
                texte_bloc_membres = st.text_input("Saisissez les pseudos à inscrire (séparés par un espace) :", value="", placeholder="Ex: Adri1 Julo").strip()
                if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch") and texte_bloc_membres:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        db.enregistrer_log(
                            type_action="COOPERATIVE", 
                            details=f"Le Créateur [{joueur_actif}] a ajouté de nouveaux membres en bloc dans [{nom_coop_active}]."
                        )
                        st.success(msg_ins)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg_ins)
            else:
                st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")
