import streamlit as st
import pandas as pd
import database as db  # Connexion aux fonctions de lecture Firebase

def afficher_onglet_historique():
    st.subheader("Base de données des chantiers enregistrés en temps réel")
    
    # Récupération des données depuis Firebase
    df_affichage = db.charger_donnees()
    
    if df_affichage.empty: 
        st.info("Aucun chantier n'a encore été enregistré dans Firebase.")
    else:
        # Sélection du critère de tri pour le classement du jeu
        critere_tri = st.selectbox(
            "Classement initial par défaut :", 
            ["Plus gros Bénéfice d'abord", "Plus gros ROI d'abord", "Plus de revenus d'abord"]
        )
        
        # Tri des lignes du DataFrame
        if critere_tri == "Plus gros Bénéfice d'abord": 
            df_affichage = df_affichage.sort_values(by="Bénéfice Net (€)", ascending=False)
        elif critere_tri == "Plus gros ROI d'abord": 
            df_affichage = df_affichage.sort_values(by="ROI (%)", ascending=False)
        elif critere_tri == "Plus de revenus d'abord": 
            df_affichage = df_affichage.sort_values(by="Revenus (€)", ascending=False)
            
        # Calcul de la performance moyenne globale de la guilde / entreprise
        moyenne_roi_jour = float(df_affichage["ROI / Jour (%)"].mean())
        df_visuel = df_affichage.copy()
        
        # Fonction interne pour générer les pastilles de couleur (Gameplay de comparaison)
        def calculer_comparaison(row):
            valeur_chantier = float(row["ROI / Jour (%)"])
            difference = valeur_chantier - moyenne_roi_jour
            if difference > 0:
                return f"🟢 +{difference:.2f} %/j"
            elif difference < 0:
                return f"🔴 {difference:.2f} %/j"
            else:
                return "⚪ Égal"

        # Application de la comparaison
        df_visuel["Comparaison Moyenne Enterprise"] = df_visuel.apply(calculer_comparaison, axis=1)
        st.info(f"📊 **Moyenne de rentabilité journalière de l'entreprise :** {moyenne_roi_jour:.2f} %/j (Calculée sur {len(df_affichage)} chantier(s))")

        # Organisation des colonnes dans l'ordre d'affichage désiré
        cols_ordre = [
            "Nom du Chantier", "Revenus (€)", "Durée (Jours)", "Coût Matériaux (€)", 
            "Coût Location Engins (€)", "Coût Salaires (€)", "Dépenses Totales (€)", 
            "Bénéfice Net (€)", "Gain / Jour (€)", "ROI (%)", "ROI / Jour (%)", "Comparaison Moyenne Enterprise"
        ]
        df_visuel = df_visuel[[c for c in cols_ordre if c in df_visuel.columns]]

        # --- APPLICATION DU SEPARATEUR D'ESPACE VIA PANDAS STYLER ---
        # Cette fonction applique l'espace pour les milliers et conserve la nature numérique des données
        format_monnaie = lambda x: f"{x:,.0f}".replace(",", " ") + " €" if pd.notnull(x) else "-"
        format_gain_jour = lambda x: f"{x:,.0f}".replace(",", " ") + " €/j" if pd.notnull(x) else "-"
        format_duree = lambda x: f"{x:.2f} j" if pd.notnull(x) else "-"
        format_pourcent = lambda x: f"{x:.2f} %" if pd.notnull(x) else "-"
        format_pourcent_jour = lambda x: f"{x:.2f} %/j" if pd.notnull(x) else "-"

        dict_formatage = {}
        
        # Mappage dynamique selon les colonnes présentes
        colonnes_argent = ["Revenus (€)", "Coût Matériaux (€)", "Coût Location Engins (€)", "Coût Salaires (€)", "Dépenses Totales (€)", "Bénéfice Net (€)"]
        for c in colonnes_argent:
            if c in df_visuel.columns: dict_formatage[c] = format_monnaie
            
        if "Gain / Jour (€)" in df_visuel.columns: dict_formatage["Gain / Jour (€)"] = format_gain_jour
        if "Durée (Jours)" in df_visuel.columns: dict_formatage["Durée (Jours)"] = format_duree
        if "ROI (%)" in df_visuel.columns: dict_formatage["ROI (%)"] = format_pourcent
        if "ROI / Jour (%)" in df_visuel.columns: dict_formatage["ROI / Jour (%)"] = format_pourcent_jour

        df_stylise = df_visuel.style.format(dict_formatage)

        # Affichage du grand tableau interactif stylisé
        # Les chaînes de format personnalisées ont été retirées de column_config car gérées en amont par df_stylise
        st.dataframe(
            df_stylise, use_container_width=True, hide_index=True,
            column_config={
                "Nom du Chantier": st.column_config.TextColumn("Nom du Chantier"), 
                "Revenus (€)": st.column_config.NumberColumn("Revenus"), 
                "Durée (Jours)": st.column_config.NumberColumn("Durée"),
                "Coût Matériaux (€)": st.column_config.NumberColumn("Matériaux"), 
                "Coût Location Engins (€)": st.column_config.NumberColumn("Location Engins"), 
                "Coût Salaires (€)": st.column_config.NumberColumn("Salaires + Intérim"),
                "Dépenses Totales (€)": st.column_config.NumberColumn("Dépenses Totales"), 
                "Bénéfice Net (€)": st.column_config.NumberColumn("Bénéfice Net"), 
                "Gain / Jour (€)": st.column_config.NumberColumn("Gain / Jour"),
                "ROI (%)": st.column_config.NumberColumn("ROI (%)"), 
                "ROI / Jour (%)": st.column_config.NumberColumn("ROI / Jour"), 
                "Comparaison Moyenne Enterprise": st.column_config.TextColumn("Comparaison Moyenne")
            }
        )
        
        # Bouton d'exportation de l'historique vers un fichier tableur externe
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger la base de données cloud (CSV)", 
            data=csv, 
            file_name="base_donnies_chantiers.csv", 
            mime="text/csv"
        )
