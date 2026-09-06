# Contenu complet et validé pour : onglets/suivi_interne.py
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

    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement Joueur")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            nom_coop_finale = st.text_input("Saisissez le NOM de la Coop :").strip() if coop_selection == "➕ Créer une nouvelle coopérative..." else (coop_selection if coop_selection != "-- Choisir une coopérative existante --" else "")
            mdp_input = st.text_input("Mot de passe Équipe :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique :").strip()
            mdp_admin_input = st.text_input("Mot de passe Administrateur Coop (Optionnel) :", type="password").strip()
            
            if st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch") and mdp_input and pseudo_input and nom_coop_finale:
                succes, message = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                if succes:
                    st.session_state["auth_suivi_coop"] = nom_coop_finale
                    st.session_state["auth_suivi_joueur"] = pseudo_input
                    if mdp_admin_input == f"{mdp_input}ADMIN": st.session_state["coop_privilege_level"] = 3
                    elif mdp_admin_input == f"{mdp_input}FIABLE": st.session_state["coop_privilege_level"] = 2
                    else: st.session_state["coop_privilege_level"] = 1
                    st.cache_data.clear(); st.rerun()
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
    tab_coop_interne, tab_joueurs_externes, tab_depot_flux, tab_gestion_membres = st.tabs(["🏆 1. Parts & Bénéfices de la Coop", "🌍 2. Marché Global", "📥 Déposer l'Historique du Jeu", "⚙️ Gérer les Collaborateurs"])

    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]
    dict_capitaux = {doc.to_dict().get("joueur"): doc.to_dict().get("montant", 0.0) for doc in db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream()}
    membres_inscrits = db.db.collection("cooperatives").document(nom_coop_active).get().to_dict().get("membres", [])

    # --- TAB 1 : PARTS & DISTRIBUTION EXCEL INTERNE (FONCTIONS MUTUALISÉES DE CALCULS.PY) ---
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
            
            # Formulaire de paye et routage décentralisé
            st.markdown("---")
            st.markdown("##### 💵 Calculateur de Paye & Routage Discord")
            c_p1, c_p2 = st.columns(2)
            with c_p1: caisse_saisie = st.number_input("Bénéfice total à distribuer (€) :", min_value=0.0, value=1000.0, step=500.0)
            with c_p2:
                st.write("")
                data_paye_bytes = generer_excel_distribution_paye(df_coop, caisse_saisie, id_log)
                st.download_button(label="📥 TÉLÉCHARGER LE RELEVÉ EXCEL", data=data_paye_bytes, file_name="releve_paye.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            
            if st.button("🚀 EXPÉDIER LE BILAN ET LA PAIE SUR DISCORD", type="primary", width="stretch"):
                msg_txt = f"```md\n# RELEVÉ DE COMPTE WEEKLY : {nom_coop_active}\n- Caisse : {caisse_saisie} €\n- Logisticien : {id_log}\n```"
                statut, msg = envoyer_releve_sur_discord(nom_coop_active, joueur_actif, msg_txt, data_paye_bytes, "releve.xlsx")
                if statut: st.success(msg)
                else: st.error(msg)

    # --- TAB 2 : MARCHE GLOBAL ET GRAPHIQUE RESTAURÉ ---
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
            st.dataframe(pd.DataFrame([{"Joueur": k, "Volume (u)": v} for k, v in stats_g.items()]), width="stretch", hide_index=True)
            if mats_g: st.bar_chart(pd.DataFrame(list(mats_g.items()), columns=["Matériau", "Volume"]).set_index("Matériau"), color="#ff4b4b")

    # --- TAB 3 : DEPOT DES HISTORIQUES ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_parseur_coop")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
            mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
            for mv in mouvements: db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            st.success(f"🎯 Synchronisation réussie : {len(mouvements)} ligne(s) ajoutée(s) !")
            st.cache_data.clear(); st.rerun()

    # --- TAB 4 : GESTION ADMIN SÉCURISÉE (NIVEAU 2 ET 3) ---
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Gérer les Collaborateurs (Admin)")
        if niveau_actuel < 2:
            st.error("🔒 Accès refusé : Niveau 2 minimum requis.")
            return

        with st.form("form_rallonge_cash"):
            m_rev = st.selectbox("Collaborateur :", membres_inscrits)
            m_cash = st.number_input("Montant de la rallonge (€) :", min_value=0.0, step=1000.0)
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE") and m_cash > 0:
                db.ajouter_reinvestissement_membre(nom_coop_active, m_rev, m_cash)
                db.enregistrer_log("COMPTABILITE", f"Rallonge de {m_cash} € pour {m_rev}")
                st.cache_data.clear(); st.rerun()

        if niveau_actuel >= 3:
            st.markdown("---")
            st.markdown("##### 👑 Commandes du Créateur (Niveau 3)")
            m_retirer = st.selectbox("Membre à licencier :", ["-- Choisir un membre --"] + membres_inscrits, key="del_mb_key")
            if m_retirer != "-- Choisir un membre --" and st.checkbox("Confirmer le licenciement de " + m_retirer):
                if st.button("🗑️ RETIRER LE MEMBRE", type="primary", width="stretch"):
                    coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                    membres_actuels = coop_doc_ref.get().to_dict().get("membres", [])
                    if m_retirer in membres_actuels:
                        membres_actuels.remove(m_retirer)
                        coop_doc_ref.update({"membres": membres_actuels})
                        db.enregistrer_log("COOPERATIVE", f"Bannissement de [{m_retirer}] par le gérant.")
                        if m_retirer == joueur_actif: st.session_state["auth_suivi_coop"] = None
                        st.cache_data.clear(); st.rerun()
