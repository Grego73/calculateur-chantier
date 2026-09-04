# Contenu complet, sécurisé et dédupliqué pour : onglets/suivi_interne.py

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

    # --- LISEUR GLOBAL DE FLUX (FIRESTORE) ---
    flux_stream = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").stream()
    liste_flux = [f.to_dict() for f in flux_stream]

    coop_ref = db.db.collection("cooperatives").document(nom_coop_active).get()
    membres_inscrits = coop_ref.to_dict().get("membres", []) if coop_ref.exists else [joueur_actif]

    # ==============================================================================
    # --- TABLEAU 1 : LES 4 MEMBRES MAXIMUM ---
    # ==============================================================================
    with tab_coop_interne:
        st.markdown("#### 📊 Grand Livre des Comptes Associés (Top 4 Membres)")
        st.caption("Calcule la quote-part légitime basée sur les réapprovisionnements de votre équipe.")

        compta_membres = {m: {"Réapprovisionnements (u)": 0.0, "Achats Internes (u)": 0.0, "Total Investi Valorisé": 0.0} for m in membres_inscrits}

        for fl in liste_flux:
            user = fl.get("joueur")
            if user not in compta_membres: continue
            
            t_mouv = fl.get("type")
            mats_qte = sum(fl.get("materiaux", {}).values())

            if t_mouv == "REAPPROVISIONNEMENT":
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
                    "Réapprovisionnements (u)": st.column_config.NumberColumn("🧱 Réappro Matériaux (Qté)"),
                    "Achats Internes (u)": st.column_config.NumberColumn("🛒 Consommation Interne (Qté)"),
                    "Total Investi Valorisé": st.column_config.NumberColumn("📈 Score d'Apport Total", format="%.0f pts"),
                    "Quote-part Bénéfice (%)": st.column_config.NumberColumn("🏆 Distribution Bénéfice légitime", format="%.2f %%")
                }
            )
        else:
            st.info("Aucune donnée comptable n'est encore enregistrée pour vos membres.")

    # ==============================================================================
    # --- TABLEAU 2 : TOUS LES AUTRES JOUEURS EXTERNES PARSÉS DYNAMIQUEMENT ---
    # ==============================================================================
    with tab_joueurs_externes:
        st.markdown("#### 🌍 Registre Général des Flux du Marché (Joueurs Externes)")
        st.caption("Extrait et classe automatiquement tous les joueurs détectés dans vos historiques soumis.")

        flux_globaux = db.charger_tous_les_achats_globaux()

        if not flux_globaux:
            st.info("💡 Aucun mouvement global n'est enregistré sur le réseau.")
        else:
            stats_externes = {}
            for f_g in flux_globaux:
                j_nom = f_g.get("joueur", "Inconnu")
                # On filtre : On exclut le mot technique de réapprovisionnement et les membres internes
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
    # --- 3. PARSEUR ET EXTRACTEUR CHRONOLOGIQUE ANTI-DOUBLONS ---
    # ==============================================================================
    with tab_depot_flux:
        st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
        st.write("Collez le bloc d'événements du jeu. L'algorithme associe chaque ligne à sa date et son heure exactes pour bloquer les doublons.")

        zone_texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=300, key="txt_logs_flux_coop_final_v2")
        if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch"):
            if not zone_texte_logs.strip():
                st.error("❌ Veuillez coller du texte avant de valider.")
            else:
                lignes_brutes = zone_texte_logs.split("\n")
                
                # Patterns Regex robustes pour intercepter le bloc double-ligne du jeu
                regex_date = re.compile(r"Le\s*(\d{2}/\d{2}/\d{4})\s*à\s*(\d{2}:\d{2})", re.IGNORECASE)
                regex_materiau = re.compile(r"(\d[\d\s]*)\s*(tonne|unité|unite)[s]?\s*de\s*(sable|terre|enrob|armature|tôle|tole|béton|beton|panneau|tuyau|canalisation|poutre)", re.IGNORECASE)
                
                date_courante = None
                heure_courante = None
                compteur_enregistres = 0

                for i, lg in enumerate(lignes_brutes):
                    l_clean = lg.strip()
                    if not l_clean: continue

                    # Étape A : Repérage de l'horodatage
                    match_date = regex_date.search(l_clean)
                    if match_date:
                        date_courante = match_date.group(1)
                        heure_courante = match_date.group(2)
                        continue

                    # Étape B : Analyse de la ligne d'action juste en dessous de la date
                    if date_courante and heure_courante:
                        match_mat = regex_materiau.search(l_clean)
                        if match_mat:
                            qte_val = float(match_mat.group(1).replace(" ", ""))
                            type_mat_brut = match_mat.group(3).lower()

                            # Normalisation NoSQL
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
                                # Détermination de l'acteur (Membre Coop, Externe ou Réapprovisionnement Global)
                                if "réapprovisionnement" in l_clean.lower():
                                    acteur_final = "Réapprovisionnement Global"
                                    type_mouv_final = "REAPPROVISIONNEMENT"
                                elif "a acheté" in l_clean.lower():
                                    # Extraction du nom (tout ce qui précède "a acheté")
                                    acteur_final = l_clean.split("a acheté")[0].strip()
                                    # Si c'est un membre de notre coop, c'est de la consommation interne, sinon de la stat externe
                                    type_mouv_final = "ACHAT_INTERNE" if acteur_final in membres_inscrits else "ACHAT_EXTERNE"
                                else:
                                    acteur_final = joueur_actif
                                    type_mouv_final = "REAPPROVISIONNEMENT"

                                # Envoi Cloud sécurisé anti-doublon via l'empreinte temporelle unique
                                db.enregistrer_ligne_historique_brute(
                                    nom_coop_active, date_courante, heure_courante, 
                                    acteur_final, type_mouv_final, {mat_cle: qte_val}
                                )
                                compteur_enregistres += 1

                if compteur_enregistres > 0:
                    st.success(f"🎯 Traitement terminé ! {compteur_enregistres} ligne(s) d'événements ont été analysées, dédupliquées et synchronisées cloud.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ L'algorithme n'a pas détecté de bloc chronologique ou de matériaux valides au format officiel du jeu.")

    # ==============================================================================
    # --- 4. SOUS-ONGLET : GESTION DES COLLABORATEURS EN BLOC ---
    # ==============================================================================
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Panneau de Recrutement & Réservation des Places")
        st.write("Saisissez vos collaborateurs séparés par un espace pour leur bloquer l'accès à la coopérative.")
        
        slots_occupes = len(membres_inscrits)
        st.info(f"📊 **Occupation de la Coopérative :** `{slots_occupes} / 4` places verrouillées.")
        
        st.markdown("**Collaborateurs actuellement enregistrés :**")
        for idx_m, mb in enumerate(membres_inscrits):
            st.write(f"{idx_m + 1}. 👤 **{mb}**")
            
        st.markdown("---")
        if slots_occupes < 4:
            st.markdown("##### ➕ Saisie groupée de vos collaborateurs")
            texte_bloc_membres = st.text_input(
                "Saisissez les pseudos (séparés par un espace) :", 
                value="", 
                placeholder="Ex: Grego73 Adri1 Julo Ctims"
            ).strip()
            
            if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch"):
                if not texte_bloc_membres:
                    st.error("⚠️ Saisissez au moins un pseudo dans le champ ci-dessus.")
                else:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        st.success(msg_ins)
                        st.rerun()
                    else:
                        st.error(msg_ins)
        else:
            st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")

