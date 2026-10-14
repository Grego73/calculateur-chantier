import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def extraire_donnees_html(html_content):
    """
    Analyse le code HTML de Sim-TP pour extraire les matériaux, stocks et prix.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    donnees_mats = []
    
    # Ciblage de toutes les cartes de matériaux du jeu
    cartes_materiaux = soup.find_all('div', class_=re.compile(r'cm33-card-project'))
    
    for carte in cartes_materiaux:
        # 1. Extraction du nom du matériau
        div_nom = carte.find('div', class_='cm33-cp-name')
        if not div_nom:
            continue
        nom_mat = div_nom.text.strip()
        
        # 2. Extraction du volume en stock
        span_prog = carte.find('span', class_=re.compile(r'cm33-cp-pct'))
        stock_val = 0
        if span_prog:
            texte_stock = span_prog.text
            match_stock = re.search(r'En stock\s*:\s*([\d\s]+)', texte_stock)
            if match_stock:
                stock_val = int(match_stock.group(1).replace(' ', ''))
        
        # 3. Extraction du prix de vente unitaire
        input_prix = carte.find('input', attrs={'name': 'prix'})
        prix_val = 0
        if input_prix and input_prix.has_attr('value'):
            try:
                prix_val = float(input_prix['value'])
            except ValueError:
                pass
                
        # Unités de mesure pour l'affichage propre
        unite = "u" if nom_mat in ["Armature métallique", "Plaque de tôle ondulée", "Panneaux signalisation", "Tuyaux d'eau standards", "Canalisations eaux usées", "Poutres en acier"] else "t"
                
        donnees_mats.append({
            "Matériau": nom_mat,
            "Quantité en Stock": stock_val,
            "Unité": unite,
            "Prix Unitaire (€)": prix_val,
            "Valeur du Stock (€)": int(stock_val * prix_val)
        })
        
    return donnees_mats

def afficher_tab_stock(nom_coop_active):
    st.markdown("#### 🌍 Évaluation de la Valeur Réelle des Stocks")
    st.caption("Collez le code source HTML de la page de votre coopérative pour calculer instantanément la valeur financière totale de vos marchandises stockées.")
    
    # Zone de collage de l'HTML
    html_brut = st.text_area(
        "Collez le code HTML de votre page ici (Ctrl+A puis Ctrl+C sur le jeu) :", 
        height=150, 
        placeholder="<!DOCTYPE html> ...",
        key="area_import_html_coop_v2"
    )
    
    if html_brut.strip():
        resultats = extraire_donnees_html(html_brut)
        
        if resultats:
            df_inventaire = pd.DataFrame(resultats)
            
            # --- 📈 INDIFICATEURS CLÉS DE VALEUR ---
            valeur_totale_marchandises = df_inventaire["Valeur du Stock (€)"].sum()
            volume_total = df_inventaire["Quantité en Stock"].sum()
            
            st.markdown("---")
            st.markdown("##### 💰 Bilan Actif de la Coopérative")
            
            c_val1, c_val2 = st.columns(2)
            with c_val1:
                st.metric(
                    label="🔥 Valeur Estimée des Stocks", 
                    value=f"{int(valeur_totale_marchandises):,}".replace(",", " ") + " €"
                )
            with c_val2:
                st.metric(
                    label="📦 Volume Total Entreposé", 
                    value=f"{int(volume_total):,}".replace(",", " ") + " unités / tonnes"
                )
            
            # --- 📊 GRAPHIQUE DES VALEURS PAR RESSOURCE ---
            st.write("")
            st.markdown("**📊 Répartition financière de l'actif par type de matériau :**")
            df_graph = df_inventaire[["Matériau", "Valeur du Stock (€)"]].set_index("Matériau")
            st.bar_chart(df_graph, color="#e8a020")
            
            # --- 📋 GRAND LIVRE DE L'INVENTAIRE ---
            st.markdown("##### 📋 Inventaire Détaillé des Matériaux")
            st.dataframe(
                df_inventaire, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Matériau": st.column_config.TextColumn("🧱 Ressource"),
                    "Quantité en Stock": st.column_config.NumberColumn("Quantité", format="%d"),
                    "Unité": st.column_config.TextColumn("📦 Type"),
                    "Prix Unitaire (€)": st.column_config.NumberColumn("Prix / Unité", format="%d €"),
                    "Valeur du Stock (€)": st.column_config.NumberColumn("Valeur Évaluée", format="%d €"),
                }
            )
            
        else:
            st.error("❌ Impossible de lire les blocs de marchandises Sim-TP. Assurez-vous d'avoir copié le code de la page 'Ma coopérative'.")
