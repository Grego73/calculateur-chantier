# Contenu complet validé et corrigé pour : onglets/suivi_interne.py
import streamlit as st
import pandas as pd
import database as db

# SÉPARATION STRICTE : Importations depuis le package coops
from coops.calculs import compiler_compta_membres, appliquer_parts_et_primes, generer_excel_distribution_paye, envoyer_releve_sur_discord
from coops.parseur import analyser_historique_brut

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB):
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None
    if "coop_privilege_level" not in st.session_state:
        st.session_state["coop_privilege_level"] = 1

    # --- ÉCRAN DE CONNEXION ÉPURÉ ---
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
            with c_p1: caisse_saisie = st.number_input("Bénéfice total à distribuer (" + "€" + ") :", min_value=0.0, value=1000.0, step=500.0)
            with c_p2:
                st.write("")
                data_paye_bytes = generer_excel_distribution_paye(df_coop, caisse_saisie, id_log)
                st.download_button(label="📥 TÉLÉCHARGER LE RELEVÉ EXCEL", data=data_paye_bytes, file_name="releve_paye.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            
            if st.button("🚀 EXPÉDIER LE BILAN ET LA PAIE SUR DISCORD", type="primary", width="stretch"):
                with st.spinner("Envoi du relevé de compte et du classement sur Discord..."):
                    statut, msg = envoyer_releve_sur_discord(
                        nom_coop=nom_coop_active,
                        pseudo_emetteur=joueur_actif,
                        df_coop=df_coop,
                        liste_flux=liste_flux,
                        benefice_total_caisse=caisse_saisie,
                        id_logisticien=id_log,
                        fichier_bytes=data_paye_bytes,
                        nom_fichier=f"releve_comptable_{nom_coop_active}.xlsx"
                    )
                    if statut: st.success(msg)
                    else: st.error(msg)

    # --- TAB 2 : MARCHE GLOBAL ---
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Registre Général des Flux du Marché")
        if liste_flux:
            stats_g, mats_g = {}, {}
            for f in liste_flux:
                j = f.get("joueur", "Inconnu")
                if j.lower().startswith("réappro"): continue
                if j not in stats_g: stats_g[j] = 0.0
                for m_k, m_v in f.get("materiaux", {}).items():
                    stats_g[j] += m_v
                    mats_g[m_k.capitalize()] = mats_g.get(m_k.capitalize(), 0.0) + m_v
            st.dataframe(pd.DataFrame([{"Joueur": k, "Statut": "🏆 Membre" if k in membres_inscrits else "👤 Client", "Volume (u)": v} for k, v in stats_g.items()]), width="stretch", hide_index=True)
            if mats_g: st.bar_chart(pd.DataFrame(list(mats_g.items()), columns=["Matériau", "Volume"]).set_index("Matériau"), color="#ff4b4b")

    # --- TAB 3 : PARSEUR LOGS (ALIGNEMENT FIXE SÉCURISÉ) ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_parseur_coop")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
            mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
            for mv in mouvements: 
                db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            st.success("🎯 Synchronisation réussie !")
            st.cache_data.clear()
            st.rerun()

        # CORRECTIF D'INDENTATION : Placé à 8 espaces de retrait pour rester aligné sous with tab_depot_flux
        st.markdown("---")
        st.markdown("##### ⏱️ Les 5 dernières entrées de l'historique du jeu (Flux Matériaux)")
        
        if liste_flux:
            try:
                df_flux_recents = pd.DataFrame(liste_flux)
                for c_req in ["joueur", "type", "date_jeu", "heure_jeu", "materiaux"]:
                    if c_req not in df_flux_recents.columns: 
                        df_flux_recents[c_req] = ""

                types_jeu_valides = ["REAPPROVISIONNEMENT", "ACHAT_INTERNE", "ACHAT_EXTERNE"]
                df_flux_recents = df_flux_recents[df_flux_recents["type"].isin(types_jeu_valides)]

                if not df_flux_recents.empty:
                    def generer_cle_tri_jeu(row):
                        d_txt = str(row.get("date_jeu", "01/01/2000")).strip()
                        h_txt = str(row.get("heure_jeu", "00:00")).strip()
                        try:
                            date_cle = "".join(reversed(d_txt.split("/")))
                            heure_cle = h_txt.replace(":", "")
                            return f"{date_cle}_{heure_cle}"
                        except Exception:
                            return "20000101_0000"

                    df_flux_recents["cle_tri_jeu"] = df_flux_recents.apply(generer_cle_tri_jeu, axis=1)
                    df_flux_recents = df_flux_recents.sort_values(by="cle_tri_jeu", ascending=False).head(5)

                    def formater_materiaux(dict_mats):
                        if not isinstance(dict_mats, dict) or not dict_mats: return "Aucun"
                        return ", ".join([f"{k.capitalize()} ({int(v)} u)" for k, v in dict_mats.items()])

                    df_flux_recents["Détail Matériaux"] = df_flux_recents["materiaux"].apply(formater_materiaux)
                    
                    def mapper_type(t):
                        mapping = {"REAPPROVISIONNEMENT": "🧱 Réappro", "ACHAT_INTERNE": "🛒 Achat Int.", "ACHAT_EXTERNE": "🌍 Achat Ext."}
                        return mapping.get(t, t)
                    df_flux_recents["Type"] = df_flux_recents["type"].apply(mapper_type)
                    df_flux_recents = df_flux_recents[["date_jeu", "heure_jeu", "joueur", "Type", "Détail Matériaux"]]

                    st.dataframe(
                        df_flux_recents, width="stretch", hide_index=True,
                        column_config={
                            "date_jeu": st.column_config.TextColumn("📅 Date Jeu"), 
                            "heure_jeu": st.column_config.TextColumn("⏱️ Heure Jeu"),
                            "joueur": st.column_config.TextColumn("👤 Joueur / Acteur"), 
                            "Type": st.column_config.TextColumn("🏷️ Action"),
                            "Détail Matériaux": st.column_config.TextColumn("🧱 Ressources transférées")
                        }
                    )
                else:
                    st.info("💡 Aucun log d'événement de matériel n'est enregistré pour le moment.")
            except Exception as e:
                st.caption(f"ℹ️ Impossible de mettre en forme le flux récent ({e}).")
        else:
            st.info("💡 L'historique de cette coopérative est vierge pour le moment.")

    # --- TAB 4 : GESTION DROITS (ADMIN) ---
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Gérer les Collaborateurs (Admin)")
        if niveau_actuel < 2:
            st.error("🔒 Accès refusé : Niveau 2 minimum requis pour voir l'administration.")
            return

        with st.form("form_rallonge_cash"):
            m_rev = st.selectbox("Collaborateur :", membres_inscrits)
            m_cash = st.number_input("Montant de la rallonge (" + "€" + ") :", min_value=0.0, step=1000.0)
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE") and m_cash > 0:
                db.ajouter_reinvestissement_membre(nom_coop_active, m_rev, m_cash)
                st.cache_data.clear()
                st.rerun()

        # Commandes exclusives du Créateur (Niveau 3)
        if niveau_actuel >= 3:
            st.markdown("---")
            st.markdown("##### 👑 1. Attribution des Mots de Passe des Grades")
            with st.form("form_gestion_mots_de_passe_grades"):
                nouveau_mdp_niv1 = st.text_input("Définir le mot de passe Ouvriers (Niveau 1) :", value=str(coop_snap.get("mdp_niveau1", "")))
                nouveau_mdp_niv2 = st.text_input("Définir le mot de passe Membres Fiables (Niveau 2) :", value=str(coop_snap.get("mdp_niveau2", "")))
                nouveau_mdp_niv3 = st.text_input("Changer votre mot de passe Créateur (Niveau 3) :", value=str(coop_snap.get("mdp_niveau3", "")))
                
                if st.form_submit_button("💾 VERROUILLER ET SAUVEGARDER LES CODES", width="stretch"):
                    db.db.collection("cooperatives").document(nom_coop_active).update({
                        "mdp_niveau1": nouveau_mdp_niv1, "mdp_niveau2": nouveau_mdp_niv2, "mdp_niveau3": nouveau_mdp_niv3
                    })
                    st.success("🟢 Les mots de passe des grades ont été mis à jour avec succès !")
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
                            db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a banni [{m_retirer}].")
                            if m_retirer == joueur_actif: st.session_state["auth_suivi_coop"] = None
                            st.success(f"🏃 {m_retirer} retiré !")
                            st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"❌ Erreur : {e}")

            # --- RETOUR DU BOUTON D'AJOUT DE JOUEUR (SI MOINS DE 4) ---
            st.markdown("---")
            slots_occupes = len(membres_inscrits)
            if slots_occupes < 4:
                st.markdown("##### ➕ 3. Recrutement de Collaborateurs en Bloc")
                texte_bloc_membres = st.text_input("Saisissez les pseudos à inscrire (séparés par un espace) :", value="", placeholder="Ex: Adri1 Julo").strip()
                if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch") and texte_bloc_membres:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a recruté du personnel en bloc.")
                        st.success(msg_ins)
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error(msg_ins)
            else:
                st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")
            # --- 3. RECRUTEMENT EN BLOC (SÉCURISÉ PAR CLÉ UNIQUE) ---
            st.markdown("---")
            slots_occupes = len(membres_inscrits)
            if slots_occupes < 4:
                st.markdown("##### ➕ 3. Recrutement de Collaborateurs en Bloc")
                
                # CORRECTIF : Ajout d'une clé d'identification unique 'key="input_recrutement_bloc_final_v3"'
                texte_bloc_membres = st.text_input(
                    "Saisissez les pseudos à inscrire (séparés par un espace) :", 
                    value="", 
                    placeholder="Ex: Adri1 Julo",
                    key="input_recrutement_bloc_final_v3"
                ).strip()
                
                if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch", key="btn_recrutement_bloc_submit_v3"):
                    if texte_bloc_membres:
                        statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                        if statut_ins:
                            db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a recruté du personnel en bloc.")
                            st.success(msg_ins)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(msg_ins)
            else:
                st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")

            # --- 📈 4. STATISTIQUES D'UTILISATION & SUIVI CONNEXIONS (SÉCURISÉ) ---
            st.markdown("---")
            st.markdown("##### 📈 4. Statistiques d'Utilisation & Activité de l'Équipe")
            st.caption("Suivi des connexions et de l'utilisation du programme à partir du journal d'audit Cloud.")
            
            try:
                logs_stream = db.db.collection("journaux_actions").stream()
                liste_logs_bruts = [doc.to_dict() for doc in logs_stream]
                
                if not liste_logs_bruts:
                    st.info("💡 Aucun journal d'activité enregistré pour le moment.")
                else:
                    df_logs = pd.DataFrame(liste_logs_bruts)
                    
                    # 1. Tableau des connexions récentes
                    df_connexions = df_logs[df_logs["type_action"] == "CONNEXION"].copy() if "type_action" in df_logs.columns else pd.DataFrame()
                    
                    if not df_connexions.empty:
                        df_connexions = df_connexions.sort_values(by="timestamp", ascending=False).head(10)
                        st.markdown("**⏱️ Dernières connexions enregistrées (Top 10) :**")
                        st.dataframe(
                            df_connexions[["timestamp", "details"]], 
                            width="stretch", hide_index=True
                        )
                    else:
                        st.caption("ℹ️ Aucun log de connexion récent détecté.")
                        
                    # 2. Graphique d'utilisation générale du programme (SÉCURISÉ PAR CLÉ)
                    if "type_action" in df_logs.columns:
                        st.markdown("**📊 Répartition de l'utilisation des modules :**")
                        compteur_actions = df_logs["type_action"].value_counts().reset_index()
                        compteur_actions.columns = ["Module de l'Application", "Nombre d'actions posées"]
                        
                        # CORRECTIF : Isolation graphique par clé d'affichage
                        st.bar_chart(compteur_actions.set_index("Module de l'Application"), color="#2563EB", key="graph_utilisation_modules_coop_v3")
            except Exception as e:
                st.caption(f"ℹ️ Tableau de bord statistique momentanément indisponible ({e}).")
