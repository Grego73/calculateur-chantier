# Contenu complet validé pour : onglets/suivi_interne.py
import streamlit as st
import pandas as pd
import database as db

# IMPORTATION DE VOS NOUVEAUX MODULES SÉPARÉS
from coops.calculs import compiler_compta_membres, appliquer_parts_et_primes
from coops.parseur import analyser_historique_brut

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB):
    st.markdown("### 👥 Espace de Planification & Suivi des Coopératives")
    
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None

    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement Joueur")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            nom_coop_finale = st.text_input("Saisissez le NOM de la Coopérative :").strip() if coop_selection == "➕ Créer une nouvelle coopérative..." else (coop_selection if coop_selection != "-- Choisir une coopérative existante --" else "")
            mdp_input = st.text_input("Mot de passe de la Coopérative :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique (Joueur) :").strip()
            
            if st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch") and mdp_input and pseudo_input and nom_coop_finale:
                succes, message = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                if succes:
                    st.session_state["auth_suivi_coop"] = nom_coop_finale
                    st.session_state["auth_suivi_joueur"] = pseudo_input
                    st.cache_data.clear()
                    st.rerun()
        return

    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]

    c_head1, c_head2 = st.columns(2)
    with c_head1: st.success(f"🔓 Coopérative active : **{nom_coop_active}** | Session : **{joueur_actif}**")
    with c_head2: 
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None; st.session_state["auth_suivi_joueur"] = None; st.rerun()

    st.markdown("---")
    tab_coop_interne, tab_joueurs_externes, tab_depot_flux, tab_gestion_membres = st.tabs(["🏆 1. Parts & Bénéfices de la Coop (Max 4)", "🌍 2. Marché Global & Matériau Favori", "📥 Déposer l'Historique du Jeu", "⚙️ Gérer les Collaborateurs"])

    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]
    capital_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("capital_initial").stream()
    dict_capitaux = {doc.to_dict().get("joueur"): doc.to_dict().get("montant", 0.0) for doc in capital_stream}
    coop_ref = db.db.collection("cooperatives").document(nom_coop_active).get()
    membres_inscrits = coop_ref.to_dict().get("membres", []) if coop_ref.exists else [joueur_actif]

    # --- 1. DISTRIBUTION DES LOGIQUES MÉTIER APPELÉES DEPUIS COOPS/CALCULS.PY ---
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

    # --- 2. MARCHE GLOBAL COMPACTÉ ---
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Registre Général des Flux du Marché (Membres & Externes/Clients)")
        if liste_flux:
            stats = {}
            for f in liste_flux:
                j = f.get("joueur", "Inconnu")
                if j.lower().startswith("réappro"): continue
                if j not in stats: stats[j] = 0.0
                stats[j] += sum(f.get("materiaux", {}).values())
            df_m = pd.DataFrame([{"Joueur": k, "Statut": "🏆 Membre Coop" if k in membres_inscrits else "👤 Client", "Volume (u)": v} for k, v in stats.items()])
            st.dataframe(df_m.sort_values(by="Volume (u)", ascending=False), width="stretch", hide_index=True)

    # --- 3. INJECTION VIA LE MODULE DE PARSEUR UNIQUE DOSSIER ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_séparée_coop")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
            mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
            for mv in mouvements:
                db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            st.success(f"🎯 Synchronisation NoSQL réussie : {len(mouvements)} ligne(s) ajoutée(s) !")
            st.cache_data.clear(); st.rerun()

    # ==============================================================================
    # --- 4. GESTION DES COLLABORATEURS ET LICENCIEMENT SÉCURISÉ ---
    # ==============================================================================
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Gérer les Collaborateurs")
        slots_occupes = len(membres_inscrits)
        st.info(f"📊 **Occupation de la Coopérative :** `{slots_occupes} / 4` places verrouillées.")
        
        st.markdown("##### 🚨 Zone de Gestion des Effectifs (Licenciement)")
        
        # CORRECTIF : Menu déroulant connecté à une clé stable pour la réinitialisation forcée
        membre_a_retirer = st.selectbox(
            "Sélectionner un membre à retirer de la Coopérative :", 
            ["-- Choisir un membre --"] + membres_inscrits, 
            key="selectbox_retirer_membre_coop"
        )
        
        if membre_a_retirer != "-- Choisir un membre --":
            st.warning(f"⚠️ **Attention :** Retirer {membre_a_retirer} libérera un slot. Ses transactions resteront sauvegardées sous l'étiquette 'Client / Ex-Membre' dans le Marché Global.")
            confirmer_retrait = st.checkbox(f"Je confirme vouloir retirer {membre_a_retirer} de la coopérative.")
            
            if st.button(f"🗑️ RETIRER {membre_a_retirer.upper()} DE LA COOP", type="primary", width="stretch", disabled=not confirmer_retrait):
                try:
                    # 1. Lecture de la liste sur Firestore
                    coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                    coop_data = coop_doc_ref.get().to_dict()
                    membres_actuels = coop_data.get("membres", [])
                    
                    # 2. Retrait physique du tableau NoSQL
                    if membre_a_retirer in membres_actuels:
                        membres_actuels.remove(membre_a_retirer)
                        coop_doc_ref.update({"membres": membres_actuels})
                        
                        # 3. Écriture immédiate du log d'audit
                        db.enregistrer_log(
                            type_action="COOPERATIVE",
                            details=f"Le joueur [{joueur_actif}] a retiré le membre [{membre_a_retirer}] de la coopérative [{nom_coop_active}]."
                        )
                        
                        # CORRECTIF TECHNIQUE : Reset forcé du composant selectbox en session state
                        st.session_state["selectbox_retirer_membre_coop"] = "-- Choisir un membre --"
                        
                        # Déconnexion automatique si le joueur s'auto-licencie
                        if membre_a_retirer == joueur_actif:
                            st.session_state["auth_suivi_coop"] = None
                            st.session_state["auth_suivi_joueur"] = None
                        
                        st.success(f"🏃 {membre_a_retirer} a été retiré avec succès !")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors du retrait : {e}")

        st.markdown("---")
        st.markdown("##### ➕ Enregistrer un NOUVEAU Réinvestissement Cash (Rallonge)")
        with st.form("form_nouveau_reinvestissement_cash"):
            c_re1, c_fl2 = st.columns(2)
            with c_re1: membre_reinvestit = st.selectbox("Sélectionner le collaborateur :", membres_inscrits)
            with c_fl2: montant_rallonge = st.number_input("Montant de l'apport complémentaire (€) :", min_value=0.0, value=0.0, step=5000.0)
                
            if st.form_submit_button("💰 APPLIQUER LA RALLONGE", width="stretch"):
                if montant_rallonge <= 0:
                    st.error("❌ Veuillez saisir un montant supérieur à 0 €.")
                else:
                    db.ajouter_reinvestissement_membre(nom_coop_active, membre_reinvestit, montant_rallonge)
                    db.enregistrer_log(type_action="COMPTABILITE", details=f"Rallonge financière de {montant_rallonge} € appliquée à [{membre_reinvestit}].")
                    st.success(f"🎯 Rallonge validée pour [ {membre_reinvestit} ] !")
                    st.cache_data.clear()
                    st.rerun()
                    
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
                db.enregistrer_log(type_action="COMPTABILITE", details=f"Mise à jour globale des capitaux initiaux pour {nom_coop_active}.")
                st.success("🎯 Tous les investissements de base ont été verrouillés.")
                st.cache_data.clear()
                st.rerun()

        st.markdown("---")
        if slots_occupes < 4:
            st.markdown("##### ➕ Ajouter de nouveaux collaborateurs")
            texte_bloc_membres = st.text_input("Saisissez les pseudos manquants (séparés par un espace) :", value="", placeholder="Ex: Grego73 Adri1").strip()
            
            if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch"):
                if not texte_bloc_membres:
                    st.error("⚠️ Saisissez au moins un pseudo.")
                else:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        db.enregistrer_log(type_action="COOPERATIVE", details=f"Recrutement de nouveaux membres en bloc dans {nom_coop_active}.")
                        st.success(msg_ins)
                        st.rerun()
                    else:
                        st.error(msg_ins)
        else:
            st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")

