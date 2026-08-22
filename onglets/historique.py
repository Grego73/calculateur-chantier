# Contenu complet validé pour : onglets/historique.py

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
        
        # Fonction interne pour générer les pastilles de couleur
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

        # --- FORMATAGE PROPRE VIA STREAMLIT COLUMN_CONFIG (RECOMMANDÉ) ---
        # Au lieu de casser l'interactivité avec pandas.style, on laisse Streamlit formater nativement
        st.dataframe(
            df_visuel, use_container_width=True, hide_index=True,
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
