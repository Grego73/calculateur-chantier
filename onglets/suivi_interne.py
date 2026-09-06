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

    # --- 4. PANNEAU ADMIN GESTION DES SALARIÉS ---
    with tab_gestion_membres:
        st.markdown("#### ⚙️ Gérer les Collaborateurs")
        slots_occupes = len(membres_inscrits)
        membre_a_retirer = st.selectbox("Sélectionner un membre à licencier :", ["-- Choisir un membre --"] + membres_inscrits)
        if membre_a_retirer != "-- Choisir un membre --" and st.checkbox("Confirmer le licenciement définitif"):
            if st.button(f"🗑️ VIRER {membre_a_retirer.upper()}", type="primary", width="stretch"):
                coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                membres_actuels = coop_doc_ref.get().to_dict().get("membres", [])
                if membre_a_retirer in membres_actuels:
                    membres_actuels.remove(membre_a_retirer)
                    coop_doc_ref.update({"membres": membres_actuels})
                    db.enregistrer_log("COOPERATIVE", f"Retrait de [{membre_a_retirer}] par [{joueur_actif}]")
                    st.cache_data.clear(); st.rerun()

