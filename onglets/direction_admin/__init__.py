# Fichier complet et corrigé : onglets/direction_admin/__init__.py
import streamlit as st
import database as db
from .blocs import afficher_onglet_blocs, afficher_onglet_doublons
from .grille import afficher_onglet_salaires, afficher_onglet_materiaux
from .flotte import afficher_onglet_flotte
from .tables import afficher_centre_controle
from .outils import afficher_comparateur, afficher_quotas, afficher_journaux

def afficher_onglet_direction(SALAIRES_DB, MATERIAUX_DB):
    st.subheader("🔑 Connexion Administrateur Direction")
    mot_de_passe = st.text_input("Veuillez saisir le code d'accès :", type="password")
    
    if mot_de_passe == "adminBTP2026":
        st.success("🔓 Accès accordé au panneau de contrôle.")
        
        df_stats = db.charger_donnees()
        if not df_stats.empty and "Revenus (€)" in df_stats.columns:
            st.markdown("### 🏢 Bilan Général de l'Entreprise (Consolidé Cloud)")
            total_chantiers = len(df_stats)
            somme_revenus = float(df_stats["Revenus (€)"].sum())
            somme_depenses = float(df_stats["Dépenses Totales (€)"].sum()) if "Dépenses Totales (€)" in df_stats.columns else 0.0
            somme_benefices = float(df_stats["Bénéfice Net (€)"].sum())
            
            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
            with c_st1: st.metric(label="💼 Chantiers Signés", value=f"{total_chantiers}")
            with c_st2: st.metric(label="💰 Chiffre d'Affaires Cumulé", value=f"{somme_revenus:,.0f}".replace(",", " ") + " €")
            with c_st3: st.metric(label="📉 Dépenses Totales", value=f"{somme_depenses:,.0f}".replace(",", " ") + " €")
            with c_st4: st.metric(label="📈 Résultat Net / Bénéfice", value=f"{somme_benefices:,.0f}".replace(",", " ") + " €")
        else:
            st.info("💡 Historique vierge : Aucun chantier n'est encore enregistré en base de données.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("🚨 Zone de Danger : Réinitialisation et Nettoyage des Tables"):
            st.warning("Attention : Ces actions suppriment définitivement les données stockées sur Firebase.")
            col_del1, col_del2, col_del3 = st.columns(3)
            with col_del1:
                if st.button("🗑️ Vider l'Historique des Chantiers", type="secondary", width="stretch"):
                    docs = db.db.collection("chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Historique des chantiers supprimé !")
                    st.rerun()
            with col_del2:
                if st.button("🗑️ Vider les Modèles Préfabriqués", type="secondary", width="stretch"):
                    docs = db.db.collection("modeles_chantiers").stream()
                    for d in docs: d.reference.delete()
                    st.cache_data.clear()
                    st.toast("Catalogue des modèles vidé !")
                    st.rerun()
            with col_del3:
                if st.button("💥 TOUT RÉINITIALISER", type="primary", width="stretch"):
                    db.reinitialiser_db()
                    st.rerun()
                    
        st.markdown("---")

        # Configuration des sous-onglets de l'Espace Direction
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6, sub_tab7, sub_tab8, sub_tab9 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins", "🗂️ Consulter les Bases Données",
            "🔎 Comparateur de Fiches", "🔍 Vérificateur de Doublons", "📊 Quotas Firebase", "📜 Historique des Actions"
        ])
        
        with sub_tab1: afficher_onglet_blocs()
        with sub_tab2: afficher_onglet_salaires(SALAIRES_DB)
        with sub_tab3: afficher_onglet_materiaux(MATERIAUX_DB)
        with sub_tab4: afficher_onglet_flotte()
        
        # --- CORRECTIF : Le centre de contrôle NoSQL est désormais isolé ici ---
        with sub_tab5: afficher_centre_controle()
        
        with sub_tab6: afficher_comparateur()
        with sub_tab7: afficher_onglet_doublons()
        with sub_tab8: afficher_quotas()
        with sub_tab9: afficher_journaux()

    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect.")
