# Contenu complet et nettoyé pour : onglets/historique.py

import streamlit as st
import pandas as pd
import database as db  # Connexion aux fonctions de lecture Firebase

def afficher_onglet_historique():
    st.subheader("📊 Tableau de Bord & Historique Cloud des Chantiers")
    
    # 1. Récupération des données depuis Firebase
    df_brut = db.charger_donnees()
    
    if df_brut.empty: 
        st.info("💡 Aucun chantier n'a encore été enregistré dans la base de données cloud.")
        return

    df_affichage = df_brut.copy()

    # 2. SECTION 1 : KPI ET STATISTIQUES GLOBALES D'ENTREPRISE
    st.markdown("### 📈 Indicateurs clés de Performance (KPI)")
    
    total_projets = len(df_affichage)
    somme_revenus = float(df_affichage["Revenus (€)"].sum())
    somme_depenses = float(df_affichage["Dépenses Totales (€)"].sum())
    somme_benefices = float(df_affichage["Bénéfice Net (€)"].sum())
    moyenne_roi_jour = float(df_affichage["ROI / Jour (%)"].mean())
    
    # Identification du meilleur chantier
    meilleur_chantier_row = df_affichage.loc[df_affichage["Bénéfice Net (€)"].idxmax()]
    nom_top_chantier = meilleur_chantier_row["Nom du Chantier"]
    val_top_chantier = meilleur_chantier_row["Bénéfice Net (€)"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.metric(label="🏗️ Total Chantiers Cloud", value=f"{total_projets}")
    with c2: 
        st.metric(label="💰 Marge Bénéficiaire Globale", value=f"{somme_benefices:,.0f}".replace(",", " ") + " €")
    with c3: 
        st.metric(label="⚡ ROI Moyen / Jour", value=f"{moyenne_roi_jour:.2f} %/j")
    with c4: 
        st.metric(label="🏆 Top Projet (Bénéfice)", value=f"{val_top_chantier:,.0f}".replace(",", " ") + " €", delta=nom_top_chantier, delta_color="normal")

    st.markdown("---")

    # 3. SECTION 2 : SYSTÈME DE FILTRES AVANCÉS (RECHERCHE ET TRIS)
    st.markdown("### 🔍 Filtres et Outils de Recherche")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        recherche_nom = st.text_input("🔍 Rechercher un chantier par son nom :", value="").strip()
    
    with col_f2:
        statut_filtre = st.selectbox(
            "Filtrer par Rentabilité :",
            ["Tous les chantiers", "🟢 Rentables uniquement", "🔴 Déficitaires uniquement"]
        )
        
    with col_f3:
        critere_tri = st.selectbox(
            "Classer les résultats par :", 
            ["Plus gros Bénéfice d'abord", "Plus gros ROI d'abord", "Plus de revenus d'abord", "Durée la plus courte"]
        )

    # Application des filtres de recherche textuelle
    if recherche_nom:
        df_affichage = df_affichage[df_affichage["Nom du Chantier"].str.contains(recherche_nom, case=False, na=False)]

    # Application des filtres de santé financière
    if statut_filtre == "🟢 Rentables uniquement":
        df_affichage = df_affichage[df_affichage["Bénéfice Net (€)"] >= 0]
    elif statut_filtre == "🔴 Déficitaires uniquement":
        df_affichage = df_affichage[df_affichage["Bénéfice Net (€)"] < 0]

    # Application du tri des données
    if critere_tri == "Plus gros Bénéfice d'abord": 
        df_affichage = df_affichage.sort_values(by="Bénéfice Net (€)", ascending=False)
    elif critere_tri == "Plus gros ROI d'abord": 
        df_affichage = df_affichage.sort_values(by="ROI (%)", ascending=False)
    elif critere_tri == "Plus de revenus d'abord": 
        df_affichage = df_affichage.sort_values(by="Revenus (€)", ascending=False)
    elif critere_tri == "Durée la plus courte":
        df_affichage = df_affichage.sort_values(by="Durée (Jours)", ascending=True)

    # Si le filtre élimine tous les chantiers
    if df_affichage.empty:
        st.warning("⚠️ Aucun chantier ne correspond à vos critères de recherche.")
        return

    # 4. SECTION 3 : ANALYSE DES ÉCARTS DE RENTABILITÉ (COLONNE DYNAMIQUE)
    def calculer_comparaison(row):
        valeur_chantier = float(row["ROI / Jour (%)"])
        difference = valeur_chantier - moyenne_roi_jour
        if difference > 0:
            return f"🟢 +{difference:.2f} %/j vs Moyenne"
        elif difference < 0:
            return f"🔴 {difference:.2f} %/j vs Moyenne"
        else:
            return "⚪ Égal à la Moyenne"

    df_affichage["Comparaison Moyenne Enterprise"] = df_affichage.apply(calculer_comparaison, axis=1)

    # Réorganisation des colonnes pour l'affichage final
    cols_ordre = [
        "Nom du Chantier", "Revenus (€)", "Durée (Jours)", "Coût Matériaux (€)", 
        "Coût Location Engins (€)", "Coût Salaires (€)", "Dépenses Totales (€)", 
        "Bénéfice Net (€)", "Gain / Jour (€)", "ROI (%)", "ROI / Jour (%)", "Comparaison Moyenne Enterprise"
    ]
    df_affichage = df_affichage[[c for c in cols_ordre if c in df_affichage.columns]]

    # 5. SECTION 4 : GRAPHIQUE VISUEL DE COMPARAISON DES BÉNÉFICES
    with st.expander("📈 Voir l'analyse visuelle des bénéfices nets", expanded=True):
        df_graph = df_affichage.set_index("Nom du Chantier")
        st.bar_chart(df_graph["Bénéfice Net (€)"], color="#2da25f" if somme_benefices >= 0 else "#de2d26")

    # 6. SECTION 5 : TABLEAU INTERACTIF DES DONNÉES CLOUD
    st.markdown(f"### 📋 Liste des chantiers filtrés ({len(df_affichage)} affiché(s))")
    
    st.dataframe(
        df_affichage, use_container_width=True, hide_index=True,
        column_config={
            "Nom du Chantier": st.column_config.TextColumn("Nom du Chantier"), 
            "Revenus (€)": st.column_config.NumberColumn("Revenus", format="%.0f €"), 
            "Durée (Jours)": st.column_config.NumberColumn("Durée", format="%.2f j"),
            "Coût Matériaux (€)": st.column_config.NumberColumn("Matériaux", format="%.0f €"), 
            "Coût Location Engins (€)": st.column_config.NumberColumn("Location Engins", format="%.0f €"), 
            "Coût Salaires (€)": st.column_config.NumberColumn("Salaires + Intérim", format="%.0f €"),
            "Dépenses Totales (€)": st.column_config.NumberColumn("Dépenses Totales", format="%.0f €"), 
            "Bénéfice Net (€)": st.column_config.NumberColumn("Bénéfice Net", format="%.0f €"), 
            "Gain / Jour (€)": st.column_config.NumberColumn("Gain / Jour", format="%.0f €/j"),
            "ROI (%)": st.column_config.NumberColumn("ROI (%)", format="%.2f %%"), 
            "ROI / Jour (%)": st.column_config.NumberColumn("ROI / Jour", format="%.2f %%/j"), 
            "Comparaison Moyenne Enterprise": st.column_config.TextColumn("Performance relative")
        }
    )
    
    # 7. EXPORTATION EXTRACTIBLE
    st.markdown("<br>", unsafe_allow_html=True)
    csv = df_affichage.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger l'historique filtré en format CSV", 
        data=csv, 
        file_name="historique_chantiers_filtres.csv", 
        mime="text/csv",
        use_container_width=True
    )
