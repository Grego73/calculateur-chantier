# Fichier complet et certifié sans erreur : onglets/direction_admin/comparateur_rentabilite.py
import streamlit as st
import pandas as pd
import database as db

def afficher_onglet_comparateur_rentabilite():
    st.markdown("### 📈 Analyse Comparative de Rentabilité des Chantiers")
    st.caption("Comparez les performances financières de vos chantiers pour identifier les modèles les plus lucratifs de l'entreprise.")

    try:
        # 1. Chargement des données consolidées de l'historique depuis database.py
        df_stats = db.charger_donnees()

        if df_stats.empty:
            st.info("💡 Aucun chantier n'est encore enregistré dans l'historique pour établir une comparaison.")
            return

        # 2. Nettoyage et préparation des colonnes financières indispensables
        df_analyse = df_stats.copy()
        
        # S'assurer que les colonnes numériques sont bien typées pour éviter les bugs
        if "Revenus (€)" in df_analyse.columns:
            df_analyse["Revenus (€)"] = pd.to_numeric(df_analyse["Revenus (€)"], errors='coerce').fillna(0.0)
        else:
            df_analyse["Revenus (€)"] = 0.0

        if "Dépenses Totales (€)" in df_analyse.columns:
            df_analyse["Dépenses Totales (€)"] = pd.to_numeric(df_analyse["Dépenses Totales (€)"], errors='coerce').fillna(0.0)
        else:
            df_analyse["Dépenses Totales (€)"] = 0.0

        if "Bénéfice Net (€)" in df_analyse.columns:
            df_analyse["Bénéfice Net (€)"] = pd.to_numeric(df_analyse["Bénéfice Net (€)"], errors='coerce').fillna(0.0)
        else:
            df_analyse["Bénéfice Net (€)"] = 0.0

        if "ROI (%)" in df_analyse.columns:
            df_analyse["ROI (%)"] = pd.to_numeric(df_analyse["ROI (%)"], errors='coerce').fillna(0.0)
        else:
            df_analyse["ROI (%)"] = 0.0

        if "Jours Globaux" in df_analyse.columns:
            df_analyse["Jours Globaux"] = pd.to_numeric(df_analyse["Jours Globaux"], errors='coerce').fillna(1.0)
        else:
            df_analyse["Jours Globaux"] = 1.0
        
        # Sécurité pour éviter la division par zéro sur la durée
        df_analyse["Jours Globaux"] = df_analyse["Jours Globaux"].apply(lambda x: 1.0 if x <= 0 else x)
        
        # Calcul du rendement net par jour de travail
        df_analyse["Gain net / jour (€/j)"] = df_analyse["Bénéfice Net (€)"] / df_analyse["Jours Globaux"]

        # 3. Sélecteur du critère de tri pour le classement de rentabilité
        st.markdown("#### 🔍 Critère de classement")
        critere_tri = st.selectbox(
            "Classer et comparer les chantiers selon :",
            [
                "💰 Plus gros Bénéfice Net (€)", 
                "📊 Plus fort Retour sur Investissement (ROI %)", 
                "⚡ Plus forte rentabilité quotidienne (€ / jour réel)"
            ]
        )

        # Application du tri selon le choix de l'utilisateur
        if critere_tri == "💰 Plus gros Bénéfice Net (€)":
            df_analyse = df_analyse.sort_values(by="Bénéfice Net (€)", ascending=False)
        elif critere_tri == "📊 Plus fort Retour sur Investissement (ROI %)":
            df_analyse = df_analyse.sort_values(by="ROI (%)", ascending=False)
        else:
            df_analyse = df_analyse.sort_values(by="Gain net / jour (€/j)", ascending=False)

        # 4. Top 3 des Chantiers d'Élite (Podium de performance)
        st.markdown("#### 🏆 Le Podium de la Rentabilité")
        top_3 = df_analyse.head(3)
        cols_podium = st.columns(min(3, len(top_3)))
        
        for idx, (_, row_top) in enumerate(top_3.iterrows()):
            with cols_podium[idx]:
                medaille = ["🥇 Top 1", "🥈 Top 2", "🥉 Top 3"][idx]
                st.metric(
                    label=f"{medaille} : {row_top['Nom du Chantier']}",
                    value=f"{int(row_top['Bénéfice Net (€)']):,} €".replace(",", " "),
                    delta=f"{row_top['ROI (%)']:.1f}% ROI"
                )

        # 5. Affichage du tableau comparatif complet des performances
        st.markdown("#### 📋 Tableau comparatif des performances de chantiers")
        
        # Sélection des colonnes disponibles pour affichage épuré
        colonnes_affichage = ["Nom du Chantier", "Revenus (€)", "Dépenses Totales (€)", "Bénéfice Net (€)", "ROI (%)", "Jours Globaux", "Gain net / jour (€/j)"]
        colonnes_existantes = [c for c in colonnes_affichage if c in df_analyse.columns]
        
        st.dataframe(
            df_analyse[colonnes_existantes],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Revenus (€)": st.column_config.NumberColumn("Chiffre d'Affaires", format="%.0f €"),
                "Dépenses Totales (€)": st.column_config.NumberColumn("Coûts globaux", format="%.0f €"),
                "Bénéfice Net (€)": st.column_config.NumberColumn("Bénéfice Net", format="%.0f €"),
                "ROI (%)": st.column_config.NumberColumn("ROI", format="%.2f %%"),
                "Jours Globaux": st.column_config.NumberColumn("Durée (j)", format="%.1f j"),
                "Gain net / jour (€/j)": st.column_config.NumberColumn("Rendement quotidien", format="%.0f €/j")
            }
        )

        # 6. Bilan analytique des moyennes d'activité de l'entreprise
        st.markdown("---")
        st.markdown("#### 📊 Moyennes constatées sur votre activité")
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.metric("Bénéfice moyen / chantier", f"{int(df_analyse['Bénéfice Net (€)'].mean()):,} €".replace(",", " "))
        with c_m2:
            st.metric("Taux de ROI moyen", f"{df_analyse['ROI (%)'].mean():.2f} %")
        with c_m3:
            st.metric("Rendement moyen journalier", f"{int(df_analyse['Gain net / jour (€/j)'].mean()):,} €/j".replace(",", " "))

    except Exception as e:
        st.error(f"Erreur lors de la génération de l'analyse comparative : {e}")
