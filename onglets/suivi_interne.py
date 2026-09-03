# Contenu complet, sécurisé et entièrement corrigé pour : onglets/suivi_interne.py

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

    # Si l'utilisateur n'est pas connecté, on affiche STRICTEMENT le panneau de connexion
    if st.session_state["auth_suivi_coop"] is None:
        # Récupération dynamique de la liste des coops enregistrées sur Firebase
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement Joueur")
            
            # Liste déroulante des coopératives
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            
            # Champ texte secret qui s'affiche si on souhaite créer une coopérative
            nom_coop_finale = ""
            if coop_selection == "➕ Créer une nouvelle coopérative...":
                nom_coop_finale = st.text_input("Saisissez le NOM de la nouvelle Coopérative (Ex: Delta_BTP) :").strip()
            elif coop_selection != "-- Choisir une coopérative existante --":
                nom_coop_finale = coop_selection

            mdp_input = st.text_input("Mot de passe de la Coopérative :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique (Joueur) :").strip()
            
            btn_soumettre = st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch")
            
            if btn_soumettre:
                if coop_selection == "-- Choisir une coopérative existante --":
                    st.error("⚠️ Veuillez sélectionner une coopérative dans la liste déroulante ou choisir d'en créer une nouvelle.")
                elif coop_selection == "➕ Créer une nouvelle coopérative..." and not nom_coop_finale:
                    st.error("⚠️ Veuillez donner un nom à votre nouvelle coopérative.")
                elif not mdp_input or not pseudo_input:
                    st.error("⚠️ Le mot de passe et le pseudo sont obligatoires.")
                else:
                    # Traitement de validation NoSQL (avec blocage strict à 4 joueurs max)
                    succes, message = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                    if succes:
                        st.session_state["auth_suivi_coop"] = nom_coop_finale
                        st.session_state["auth_suivi_joueur"] = pseudo_input
                        st.cache_data.clear()
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        return  # Bloque le reste de la page tant que la connexion n'est pas validée

    # ==============================================================================
    # --- INTERFACE ACTIVE APRÈS CONNEXION RÉUSSIE ---
    # ==============================================================================
    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]

    # CORRECTION DU TYPEERROR ICI : Ajout de l'argument (2) pour spécifier 2 colonnes
    c_head1, c_head2 = st.columns(2)
    with c_head1:
        st.success(f"🔓 Coopérative active : **{nom_coop_active}** | Session Joueur : **{joueur_actif}**")
    with c_head2:
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None
            st.session_state["auth_suivi_joueur"] = None
            st.rerun()

    st.markdown("---")

    tab_coop_interne, tab_joueurs_externes, tab_depot_flux = st.tabs([
        "🏆 1. Parts & Bénéfices de la Coop (Max 4)", 
        "🌍 2. Marché Global & Matériau Favori",
        "📥 Déposer un Flux (Apport / Réappro / Achat)"
    ])

    # --- TABLEAU 1 : LES 4 MEMBRES MAXIMUM ---
    with tab_coop_interne:
        st.markdown("#### 📊 Grand Livre des Comptes Associés (Top 4 Membres)")
        st.caption("Calcule la quote-part de bénéfices basée sur la valeur investie (Apports Cash + Réapprovisionnements).")

        flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
        liste_flux = [f.to_dict() for f in flux_stream]

        coop_ref = db.db.collection("cooperatives").document(nom_coop_active).get()
        membres_inscrits = coop_ref.to_dict().get("membres", []) if coop_ref.exists else [joueur_actif]

        compta_membres = {m: {"Apport Initial (€)": 0.0, "Réapprovisionnements (u)": 0.0, "Achats Internes (u)": 0.0, "Total Investi Valorisé": 0.0} for m in membres_inscrits}

        for fl in liste_flux:
            user = fl.get("joueur")
            if user not in compta_membres: continue
            
            t_mouv = fl.get("type")
            cash = fl.get("apport_cash", 0.0)
            mats_qte = sum(fl.get("materiaux", {}).values())

            if t_mouv == "APPORT_INITIAL":
                compta_membres[user]["Apport Initial (€)"] += cash
                compta_membres[user]["Total Investi Valorisé"] += cash
            elif t_mouv == "REAPPROVISIONNEMENT":
                compta_membres[user]["Réapprovisionnements (u)"] += mats_qte
                compta_membres[user]["Total Investi Valorisé"] += (mats_qte * 30.0)
            elif t_mouv == "ACHAT_INTERNE":
                compta_membres[user]["Achats Internes (u)"] += mats_qte

        if compta_membres:
            df_coop = pd.DataFrame.from_dict(compta_membres, orient='index')
            investissement_global_coop = df_coop["Total Investi Valorisé"].sum()
            
            if investissement_global_coop > 0:
                df_coop["Quote-part Bénéfice (%)"] = (df_coop["Total Investi Valorisé"] / investissement_global_coop) * 100
            else:
                df_coop["Quote-part Bénéfice (%)"] = 100.0 / len(df_coop) if len(df_coop) > 0 else 0.0

            df_coop.index.name = "Pseudo Membre"
            df_coop = df_coop.reset_index()

            st.dataframe(
                df_coop, width="stretch", hide_index=True,
                column_config={
                    "Pseudo Membre": st.column_config.TextColumn("👤 Membre de la Coop"),
                    "Apport Initial (€)": st.column_config.NumberColumn("💰 Investissement Cash", format="%.0f €"),
                    "Réapprovisionnements (u)": st.column_config.NumberColumn("🧱 Réappro Matériaux (Qté)"),
                    "Achats Internes (u)": st.column_config.NumberColumn("🛒 Consommation / Achats (Qté)"),
                    "Total Investi Valorisé": st.column_config.NumberColumn("📈 Score d'Apport Total", format="%.0f pts"),
                    "Quote-part Bénéfice (%)": st.column_config.NumberColumn("🏆 Distribution Bénéfice légitime", format="%.2f %%")
                }
            )
        else:
            st.info("Aucune donnée comptable n'est encore enregistrée pour vos membres.")

    # --- TABLEAU 2 : TOUS LES AUTRES JOUEURS EXTERNES ---
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
                if j_nom in membres_inscrits: continue
                
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
                st.info("💡 Aucun joueur externe n'a encore déposé de flux d'achat.")

    # --- SOUS-ONGLET DE DÉPÔT ---
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Grand Livre Comptable")
        # CORRECTION DU TYPEERROR ICI AUSSI : Spécification explicite des 2 colonnes
        c_fl1, c_fl2 = st.columns(2)
        with c_fl1:
            type_mouv_choisi = st.selectbox("Nature de votre flux :", ["APPORT_INITIAL", "REAPPROVISIONNEMENT", "ACHAT_INTERNE"])
        with c_fl2:
            apport_money = st.number_input("Montant financier si apport cash (€) :", min_value=0.0, value=0.0, step=500.0)

        zone_texte_logs = st.text_area("Collez la facture ou les logs d'achats bruts du jeu ici :", height=150, key="txt_logs_flux_coop")

        if st.button("💾 ENREGISTRER LE MOUVEMENT ET RECALCULER", type="primary", width="stretch"):
            materiaux_parses = {}
            pattern_regex = re.compile(r"(\d[\d\s]*)\s*(sable|terre|enrobe|armature|tole|tôle|beton|béton|panneau|tuyau|canalisation|poutre)", re.IGNORECASE)
            
            for lg in zone_texte_logs.split("\n"):
                match_rg = pattern_regex.search(lg)
                if match_rg:
                    quantite_v = float(match_rg.group(1).replace(" ", ""))
                    label_v = match_rg.group(2).lower()
                    
                    nom_normalise = None
                    if "sable" in label_v: nom_normalise = "sable"
                    elif "terre" in label_v: nom_normalise = "terre"
                    elif "enrob" in label_v: nom_normalise = "enrobe"
                    elif "armature" in label_v: nom_normalise = "armature"
                    elif "tôle" in label_v or "tole" in label_v: nom_normalise = "tole"
                    elif "béton" in label_v or "beton" in label_v: nom_normalise = "beton"
                    elif "panneau" in label_v: nom_normalise = "panneaux"
                    elif "tuyau" in label_v: nom_normalise = "tuyaux"
                    elif "canalisation" in label_v: nom_normalise = "canalisations"
                    elif "poutre" in label_v: nom_normalise = "poutres"
                    
                    if nom_normalise:
                        materiaux_parses[nom_normalise] = materiaux_parses.get(nom_normalise, 0.0) + quantite_v

            if materiaux_parses or apport_money > 0:
                db.enregistrer_mouvement_coop(nom_coop_active, joueur_actif, type_mouv_choisi, materiaux_parses, apport_money)
                st.success("🎯 Flux comptabilisé ! Les bénéfices ont été révisés.")
                st.rerun()
            else:
                st.error("❌ Analyse impossible : Saisissez des données valides.")
