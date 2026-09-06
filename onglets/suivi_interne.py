# Contenu complet validé et sécurisé pour : onglets/suivi_interne.py
import streamlit as st
import pandas as pd
import database as db

# IMPORTATION DES MODULES SÉPARÉS
from coops.calculs import compiler_compta_membres, appliquer_parts_et_primes
from coops.parseur import analyser_historique_brut

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB):
    st.markdown("### 👥 Espace de Planification & Suivi des Coopératives")
    
    # 1. INITIALISATION DES SESSIONS DE SÉCURITÉ
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None
    if "coop_privilege_level" not in st.session_state:
        st.session_state["coop_privilege_level"] = 1  # Niveau 1 par défaut

    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement Joueur")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            nom_coop_finale = st.text_input("Saisissez le NOM de la Coopérative :").strip() if coop_selection == "➕ Créer une nouvelle coopérative..." else (coop_selection if coop_selection != "-- Choisir une coopérative existante --" else "")
            mdp_input = st.text_input("Mot de passe Équipe (Standard) :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique (Joueur) :").strip()
            
            st.markdown("---")
            st.caption("🔑 Débloquer des privilèges supérieurs dès la connexion (Optionnel) :")
            mdp_admin_input = st.text_input("Mot de passe Administrateur Coop :", type="password").strip()
            
            if st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch") and mdp_input and pseudo_input and nom_coop_finale:
                succes, message = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                if succes:
                    st.session_state["auth_suivi_coop"] = nom_coop_finale
                    st.session_state["auth_suivi_joueur"] = pseudo_input
                    
                    # Détermination du niveau selon le mot de passe admin de la coop
                    # Règle : mot de passe de la coop + "ADMIN" (Ex: si mdp=btp123, l'admin sera btp123ADMIN)
                    if mdp_admin_input == f"{mdp_input}ADMIN":
                        st.session_state["coop_privilege_level"] = 3 # Créateur
                    elif mdp_admin_input == f"{mdp_input}FIABLE":
                        st.session_state["coop_privilege_level"] = 2 # Membre Fiable
                    else:
                        st.session_state["coop_privilege_level"] = 1 # Ouvrier
                        
                    st.cache_data.clear()
                    st.rerun()
        return

    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]
    niveau_actuel = st.session_state["coop_privilege_level"]

    # Affichage du badge de grade
    dict_badges = {1: "👷 Niveau 1 : Ouvrier", 2: "🎖️ Niveau 2 : Membre Fiable", 3: "🏆 Niveau 3 : Créateur / Admin"}
    
    c_head1, c_head2 = st.columns(2)
    with c_head1: 
        st.success(f"🔓 Coop : **{nom_coop_active}** | 👤 Session : **{joueur_actif}** | {dict_badges[niveau_actuel]}")
    with c_head2: 
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None
            st.session_state["auth_suivi_joueur"] = None
            st.session_state["coop_privilege_level"] = 1
            st.rerun()

    st.markdown("---")
    tab_coop_interne, tab_joueurs_externes, tab_depot_flux, tab_gestion_membres = st.tabs([
        "🏆 1. Parts & Bénéfices de la Coop (Max 4)", 
        "🌍 2. Marché Global & Matériau Favori", 
        "📥 Déposer l'Historique du Jeu", 
        "⚙️ Gérer les Collaborateurs (Admin)"
    ])

    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]
    capital_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream()
    dict_capitaux = {doc.to_dict().get("joueur"): doc.to_dict().get("montant", 0.0) for doc in capital_stream}
    coop_ref = db.db.collection("cooperatives").document(nom_coop_active).get()
    membres_inscrits = coop_ref.to_dict().get("membres", []) if coop_ref.exists else [joueur_actif]

    # --- TAB 1 : GRAND LIVRE (ACCESSIBLE TOUS NIVEAUX) ---
    with tab_coop_interne:
        st.markdown("#### 📊 Grand Livre des Comptes Associés (Top 4 Membres)")
        compta_brute = compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits)
        if compta_brute:
            df_coop = pd.DataFrame.from_dict(compta_brute, orient='index')
            df_coop, id_log = appliquer_parts_et_primes(df_coop)
            df_coop.index.name = "Pseudo Membre"
            df_coop = df_coop.reset_index()

            st.dataframe(
                df_coop, width="stretch", hide_index=True,
                column_config={
                    "Pseudo Membre": st.column_config.TextColumn("👤 Membre"), "Rôle cette semaine": st.column_config.TextColumn("🎖️ Statut"),
                    "Capital Départ (€)": st.column_config.NumberColumn("💰 Initial", format="%.0f €"), "Réinvestissements (€)": st.column_config.NumberColumn("➕ Rallonges", format="%.0f €"),
                    "Réappro Matériaux (u)": st.column_config.NumberColumn("🚜 Volume Rachat"), "Consommation Interne (u)": st.column_config.NumberColumn("🛒 Achats Perso"),
                    "Bénéfices Générés (€)": st.column_config.NumberColumn("💸 Marge (1€/u)", format="%.0f €"), "Score d'Apport Total": st.column_config.NumberColumn("📈 Score", format="%.0f pts"),
                    "Distribution Bénéfice (%)": st.column_config.NumberColumn("🏆 Part des Dividendes", format="%.2f %%")
                }
            )
            if id_log: st.success(f"👑 **Félicitations à [{id_log}]** (Responsable Logistique de la semaine) !")
            # --- EXTENSION : SIMULATEUR DE DISTRIBUTION ET TÉLÉCHARGEMENT EXCEL ---
            st.markdown("---")
            st.markdown("##### 💵 Calculateur de Paye & Exportation du Relevé de Compte")
            
            c_paye1, c_paye2 = st.columns([1, 2])
            with c_paye1:
                caisse_coop_saisie = st.number_input(
                    "Bénéfice total à distribuer cette semaine (€) :", 
                    min_value=0.0, value=1000.0, step=500.0, key="input_calcul_paye_euros_coop"
                )
            with c_paye2:
                st.write("") # Espacement visuel
                st.write("") 
                
                # Génération du fichier Excel via notre module séparé
                from coops.calculs import generer_excel_distribution_paye
                data_paye_bytes = generer_excel_distribution_paye(df_coop, caisse_coop_saisie, id_log)
                
                st.download_button(
                    label="📥 TÉLÉCHARGER LE RELEVÉ DE PAYE DES ASSOCIÉS (EXCEL)",
                    data=data_paye_bytes,
                    file_name=f"releve_paye_hebdo_{nom_coop_active}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )

    # ==============================================================================
    # --- TABLEAU 2 : TOUS LES ACTEURS DU MARCHÉ & GRAPHIQUE DES QUANTITÉS ---
    # ==============================================================================
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Registre Général des Flux du Marché (Membres & Externes/Clients)")
        st.caption("Analyse et compare les volumes de l'ensemble des acteurs du serveur. Les anciens membres restent visibles ici.")

        if not liste_flux:
            st.info("💡 Aucun mouvement global n'est enregistré sur le réseau.")
        else:
            stats_globales = {}
            total_par_materiau = {}

            # Reconstruction de la boucle d'analyse croisée des matériaux
            for f_g in liste_flux:
                j_nom = f_g.get("joueur", "Inconnu")
                if j_nom.lower().startswith("réappro"): 
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
                    materiau_favori = max(details_ressources, key=details_ressources.get)
                    volume_favori = details_ressources[materiau_favori]
                    txt_recap_favori = f"{materiau_favori} ({int(volume_favori)} u)"
                else:
                    txt_recap_favori = "Aucun"

                badge_statut = "🏆 Membre Coop" if joueur in membres_inscrits else "👤 Client / Ex-Membre"

                lignes_affichage.append({
                    "Statut": badge_statut,
                    "Joueur": joueur,
                    "Volume Global Acquis (u)": data_ex["Volume Total Acheté (u)"],
                    "Matériau le plus acheté": txt_recap_favori
                })

            if lignes_affichage:
                df_ext = pd.DataFrame(lignes_affichage).sort_values(by="Volume Global Acquis (u)", ascending=False)
                st.dataframe(df_ext, width="stretch", hide_index=True)
                
                # --- LE RETOUR DU GRAPHIQUE DES RESSOURCES ---
                st.markdown("---")
                st.markdown("### 📊 Classement des Matériaux les plus Consommés sur le Serveur")
                
                if total_par_materiau:
                    df_graph_mats = pd.DataFrame(list(total_par_materiau.items()), columns=["Matériau", "Quantité Totale Consommée (u)"])
                    df_graph_mats = df_graph_mats.sort_values(by="Quantité Totale Consommée (u)", ascending=True)
                    st.bar_chart(data=df_graph_mats, x="Matériau", y="Quantité Totale Consommée (u)", color="#ff4b4b")
            else:
                st.info("💡 Aucun volume d'achat n'a pu être extrait pour alimenter le graphique.")

    # --- TAB 3 : PARSEUR DE LOGS (ACCESSIBLE TOUS NIVEAUX) ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_séparée_coop")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
            mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
            for mv in mouvements:
                db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            st.success(f"🎯 Synchronisation NoSQL réussie : {len(mouvements)} ligne(s) ajoutée(s) !")
            st.cache_data.clear(); st.rerun()

    # --- TAB 4 : PANNEAU DE CONTRÔLE AVANCÉ (SÉCURISÉ SELON LE NIVEAU) ---
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Panneau d'Administration et Gestion des Droits")
        
        # SÉCURITÉ NIVEAU 1 : Bloqué
        if niveau_actuel < 2:
            st.error("🔒 **Accès Refusé :** Vous devez posséder le grade **Niveau 2 (Membre Fiable)** ou **Niveau 3 (Créateur)** pour modifier les paramètres de l'équipe.")
            return

        # SÉCURITÉ NIVEAU 2 : Autorisé uniquement à injecter des rallonges financières
        if niveau_actuel == 2:
            st.info("🎖️ **Mode Membre Fiable :** Vous pouvez enregistrer des rallonges financières pour l'équipe.")
            
        # --- SECTION COMPTABILITÉ (ACCESSIBLE NIVEAU 2 & 3) ---
        st.markdown("##### ➕ Enregistrer un NOUVEAU Réinvestissement Cash (Rallonge)")
        with st.form("form_nouveau_reinvestissement_cash"):
            c_re1, c_fl2 = st.columns(2)
            with c_re1: membre_reinvestit = st.selectbox("Sélectionner le collaborateur :", membres_inscrits)
            with c_fl2: montant_rallonge = st.number_input("Montant de l'apport complémentaire (€) :", min_value=0.0, value=0.0, step=5000.0)
                
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE", width="stretch") and montant_rallonge > 0:
                db.ajouter_reinvestissement_membre(nom_coop_active, membre_reinvestit, montant_rallonge)
                db.enregistrer_log(type_action="COMPTABILITE", details=f"Rallonge de {montant_rallonge} € par [{joueur_actif}] pour [{membre_reinvestit}].")
                st.success(f"🎯 Rallonge validée !")
                st.cache_data.clear(); st.rerun()

        # --- SECTIONS SUPÉRIEURES : STRICTEMENT RÉSERVÉES AU NIVEAU 3 (CRÉATEUR) ---
        st.markdown("---")
        st.markdown("##### 👑 Commandes du Créateur de la Coopérative (Niveau 3 requis)")
        
        if niveau_actuel < 3:
            st.warning("🔒 Les fonctions de licenciement et de modification du capital de base sont verrouillées (Niveau 3 requis).")
        else:
            # 1. ZONE DE LICENCIEMENT CRÉATEUR
            st.markdown("##### 🚨 Zone de Gestion des Effectifs (Licenciement)")
            membre_a_retirer = st.selectbox(
                "Sélectionner un membre à retirer de la Coopérative :", 
                ["-- Choisir un membre --"] + membres_inscrits, key="selectbox_retirer_membre_coop"
            )
            if membre_a_retirer != "-- Choisir un membre --":
                confirmer_retrait = st.checkbox(f"Je confirme le retrait immédiat de {membre_a_retirer}.")
                if st.button(f"🗑️ RETIRER {membre_a_retirer.upper()} DE LA COOP", type="primary", width="stretch", disabled=not confirmer_retrait):
                    try:
                        coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                        membres_actuels = coop_doc_ref.get().to_dict().get("membres", [])
                        if membre_a_retirer in membres_actuels:
                            membres_actuels.remove(membre_a_retirer)
                            coop_doc_ref.update({"membres": membres_actuels})
                            
                            db.enregistrer_log(
                                type_action="COOPERATIVE", 
                                details=f"Le Créateur [{joueur_actif}] a banni [{membre_a_retirer}] de la coopérative [{nom_coop_active}]."
                            )
                            
                            if membre_a_retirer == joueur_actif:
                                st.session_state["auth_suivi_coop"] = None
                                st.session_state["auth_suivi_joueur"] = None
                                st.session_state["coop_privilege_level"] = 1
                            
                            st.success(f"🏃 {membre_a_retirer} a été retiré avec succès !")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e: 
                        st.error(f"❌ Erreur : {e}")

            # 2. ÉDITION DU CAPITAL DE BASE CRÉATEUR
            st.markdown("---")
            st.markdown("##### 💰 Éditer le Capital Initial d'Origine")
            with st.form("form_ajustement_capitaux_coop"):
                champs_capitaux = {}
                for mb in membres_inscrits:
                    capital_actuel = float(dict_capitaux.get(mb, 0.0))
                    champs_capitaux[mb] = st.number_input(f"Capital de base pour [ {mb} ] (€) :", min_value=0.0, value=capital_actuel, step=10000.0, key=f"input_ajust_cap_{mb}")
                if st.form_submit_button("💾 VERROUILLER LE COMPTE DE BASE", width="stretch"):
                    for mb_nom, val_money in champs_capitaux.items():
                        db.fixer_capital_initial_membre(nom_coop_active, mb_nom, val_money)
                    db.enregistrer_log(type_action="COMPTABILITE", details=f"Le Créateur [{joueur_actif}] a modifié la grille des capitaux de base.")
                    st.success("🎯 Investissements de base verrouillés.")
                    st.cache_data.clear()
                    st.rerun()

            # 3. RECRUTEMENT EN BLOC CRÉATEUR
            st.markdown("---")
            if slots_occupes < 4:
                st.markdown("##### ➕ Ajouter de nouveaux collaborateurs")
                texte_bloc_membres = st.text_input("Saisissez les pseudos manquants (séparés par un espace) :", value="", placeholder="Ex: Adri1").strip()
                if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch") and texte_bloc_membres:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a recruté du personnel en bloc.")
                        st.success(msg_ins)
                        st.cache_data.clear()
                        st.rerun()
                    else: 
                        st.error(msg_ins)
