import streamlit as st
import database as db
from .blocs import afficher_onglet_blocs, afficher_onglet_doublons
from .grille import afficher_onglet_salaires
from .materiaux import afficher_onglet_materiaux
from .flotte import afficher_onglet_flotte
from .tables import afficher_centre_controle
from .outils import afficher_journaux
from .engins_jeu import afficher_onglet_catalogue_engins_total
from .consommation import afficher_onglet_consommation
from .comparateur_rentabilite import afficher_onglet_comparateur_rentabilite


def afficher_onglet_direction(SALAIRES_DB, MATERIAUX_DB):
    # ==========================================================================
    # --- 1. GESTION DE LA CONNEXION ADMINISTRATEUR (MÉMORISÉE EN SESSION) ---
    # ==========================================================================
    if "admin_direction_connecte" not in st.session_state:
        st.session_state["admin_direction_connecte"] = False

    if not st.session_state["admin_direction_connecte"]:
        col_auth, _ = st.columns([1.2, 1])
        with col_auth:
            with st.container(border=True):
                st.markdown("### 🔑 Accès Direction")
                st.caption("Cet espace est réservé aux administrateurs pour mettre à jour les données du jeu.")
                mot_de_passe = st.text_input("Code d'accès :", type="password", key="input_mdp_direction")
                if st.button("🔓 Se connecter", type="primary", use_container_width=True):
                    if mot_de_passe == "adminBTP2026":
                        st.session_state["admin_direction_connecte"] = True
                        st.rerun()
                    else:
                        st.error("🔒 Code d'accès incorrect.")
        return

    # Barre supérieure avec bouton de déconnexion
    col_titre, col_logout = st.columns([4, 1])
    with col_titre:
        st.success("🔓 Session Administrateur active")
    with col_logout:
        if st.button("🔒 Déconnexion", use_container_width=True):
            st.session_state["admin_direction_connecte"] = False
            st.rerun()

    # ==========================================================================
    # --- 2. KPI GLOBAUX DE L'ENTREPRISE ---
    # ==========================================================================
    df_stats = db.charger_donnees()
    if not df_stats.empty and "Revenus (€)" in df_stats.columns:
        total_chantiers = len(df_stats)
        somme_revenus = float(df_stats["Revenus (€)"].sum())
        somme_depenses = float(df_stats["Dépenses Totales (€)"].sum()) if "Dépenses Totales (€)" in df_stats.columns else 0.0
        somme_benefices = float(df_stats["Bénéfice Net (€)"].sum())

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("💼 Chantiers Validés", f"{total_chantiers}")
        with c2:
            st.metric("💰 Chiffre d'Affaires", f"{somme_revenus:,.0f}".replace(",", " ") + " €")
        with c3:
            st.metric("📉 Dépenses Cumulées", f"{somme_depenses:,.0f}".replace(",", " ") + " €")
        with c4:
            st.metric("📈 Bénéfice Net Global", f"{somme_benefices:,.0f}".replace(",", " ") + " €")

    st.markdown("---")

    # ==========================================================================
    # --- 3. NAVIGATION SIMPLIFIÉE EN 4 GRANDS PÔLES ---
    # ==========================================================================
    pole_import, pole_tarifs, pole_analyses, pole_bdd = st.tabs([
        "📥 Import Données Jeu",
        "💰 Grilles & Tarifs",
        "📊 Analyses & Consommation",
        "🗂️ Base NoSQL & Logs"
    ])

    # --- PÔLE 1 : TOUTES LES IMPORTATIONS (HTML & BLOCS) ---
    with pole_import:
        choix_import = st.radio(
            "Source de données à synchroniser :",
            [
                "🏗️ Fiches Chantiers Multi-Étapes (Copier-Coller)",
                "🧱 Marché des Coopératives (Code HTML)",
                "🚜 Catalogue Flotte d'Engins (Code HTML)"
            ],
            horizontal=True,
            key="radio_admin_import"
        )
        st.markdown("---")
        if "Fiches Chantiers" in choix_import:
            afficher_onglet_blocs()
        elif "Marché" in choix_import:
            afficher_onglet_materiaux(MATERIAUX_DB)
        else:
            afficher_onglet_flotte()

    # --- PÔLE 2 : GRILLES TARIFAIRES ---
    with pole_tarifs:
        choix_tarif = st.radio(
            "Grille à configurer :",
            ["👥 Salaires & Recrues (CDI / CDD)", "🚜 Catalogue Manuel des Engins"],
            horizontal=True,
            key="radio_admin_tarifs"
        )
        st.markdown("---")
        if "Salaires" in choix_tarif:
            afficher_onglet_salaires(SALAIRES_DB)
        else:
            afficher_onglet_catalogue_engins_total()

    # --- PÔLE 3 : ANALYSES & RENTABILITÉ ---
    with pole_analyses:
        choix_analyse = st.radio(
            "Outil d'analyse :",
            [
                "📈 Chantiers les Plus Rentables",
                "🧱 Consommation Matériaux par Étape",
                "🔍 Vérificateur de Doublons"
            ],
            horizontal=True,
            key="radio_admin_analyses"
        )
        st.markdown("---")
        if "Rentables" in choix_analyse:
            afficher_onglet_comparateur_rentabilite()
        elif "Consommation" in choix_analyse:
            afficher_onglet_consommation()
        else:
            afficher_onglet_doublons()

    # --- PÔLE 4 : BASE DE DONNÉES, LOGS & ZONE DE DANGER ---
    with pole_bdd:
        choix_bdd = st.radio(
            "Maintenance système :",
            [
                "📁 Inspecteur & Nettoyeur de Tables",
                "📜 Journaux d'Audit (Logs)",
                "🚨 Zone de Danger (Purge Globale)"
            ],
            horizontal=True,
            key="radio_admin_bdd"
        )
        st.markdown("---")
        if "Inspecteur" in choix_bdd:
            afficher_centre_controle()
        elif "Journaux" in choix_bdd:
            afficher_journaux()
        else:
            st.warning("⚠️ Attention : Les actions ci-dessous effacent définitivement les collections sur Firebase.")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                if st.button("🗑️ Vider l'Historique Chantiers", type="secondary", use_container_width=True):
                    for d in db.db.collection("chantiers").stream():
                        d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Historique des chantiers supprimé !", icon="🗑️")
                    st.rerun()
            with col_d2:
                if st.button("🗑️ Vider les Modèles Chantiers", type="secondary", use_container_width=True):
                    for d in db.db.collection("modeles_chantiers").stream():
                        for et in d.reference.collection("etapes").stream():
                            et.reference.delete()
                        d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Catalogue des modèles vidé !", icon="🗑️")
                    st.rerun()
            with col_d3:
                if st.button("💥 TOUT RÉINITIALISER", type="primary", use_container_width=True):
                    db.reinitialiser_db()
                    st.toast("Base de données entièrement réinitialisée !", icon="💥")
                    st.rerun()
