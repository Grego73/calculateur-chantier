import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def extraire_donnees_html(html_content):
    """
    Analyse le code HTML du jeu Sim-TP pour en extraire les stocks et les prix.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    donnees_mats = []
    
    # 🎯 On cible toutes les cartes de projet de matériaux (cm33-card-project)
    cartes_materiaux = soup.find_all('div', class_=re.compile(r'cm33-card-project'))
    
    for carte in cartes_materiaux:
        # 1. Extraction du nom du matériau
        div_nom = carte.find('div', class_='cm33-cp-name')
        if not div_nom:
            continue
        nom_mat = div_nom.text.strip()
        
        # 2. Extraction de la quantité en stock via le texte de progression
        span_prog = carte.find('span', class_=re.compile(r'cm33-cp-pct'))
        stock_val = 0
        if span_prog:
            texte_stock = span_prog.text
            # Recherche de la suite de chiffres (ex: "2350 tonne(s)" ou "1139 unité(s)")
            match_stock = re.search(r'En stock\s*:\s*([\d\s]+)', texte_stock)
            if match_stock:
                # Nettoyage des espaces pour les grands nombres (ex: "5 000" -> 5000)
                stock_val = int(match_stock.group(1).replace(' ', ''))
        
        # 3. Extraction de la valeur / prix de vente configuré
        input_prix = carte.find('input', attrs={'name': 'prix'})
        prix_val = 0
        if input_prix and input_prix.has_attr('value'):
            try:
                prix_val = float(input_prix['value'])
            except ValueError:
                pass
                
        donnees_mats.append({
            "Matériau": nom_mat,
            "Quantité en Stock": stock_val,
            "Prix Actuel (€)": prix_val,
            "Valeur Totale (€)": int(stock_val * prix_val)
        })
        
    return donnees_mats

def afficher_tab_import_html(nom_coop_active):
    st.markdown("#### 📥 Importation de l'inventaire en direct depuis Sim-TP")
    st.caption("Alimentez l'état des stocks réels de votre coopérative en y collant le code source de votre page de jeu.")
    
    # Zone de saisie pour coller l'HTML brut
    html_brut = st.text_area(
        "Collez l'intégralité du code HTML (Ctrl+A puis Ctrl+C sur Sim-TP) :", 
        height=250, 
        placeholder="<!DOCTYPE html> ...",
        key="area_import_html_coop"
    )
    
    if st.button("🚀 ANALYSER ET METTRE À JOUR L'INVENTAIRE", type="primary", use_container_width=True):
        if html_brut.strip():
            with st.spinner("Analyse du DOM HTML en cours..."):
                resultats = extraire_donnees_html(html_brut)
                
            if resultats:
                df_inventaire = pd.DataFrame(resultats)
                
                # --- AFFICHAGE DU RÉCAPITULATIF EXTRAIT ---
                st.success(f"🎯 Analyse réussie ! {len(df_inventaire)} matériaux identifiés.")
                
                # Calculs globaux pour le tableau de bord
                valeur_totale_stock = df_inventaire["Valeur Totale (€)"].sum()
                
                c_inv1, c_inv2 = st.columns(2)
                with c_inv1:
                    st.metric("📦 Volume Global Matériaux", f"{df_inventaire['Quantité en Stock'].sum():,} u".replace(",", " "))
                with c_inv2:
                    st.metric("💰 Valeur Théorique Marché", f"{valeur_totale_stock:,} €".replace(",", " "))
                
                st.markdown("##### 📋 Détail des ressources détectées :")
                st.dataframe(
                    df_inventaire, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Quantité en Stock": st.column_config.NumberColumn("Quantité", format="%d"),
                        "Prix Actuel (€)": st.column_config.NumberColumn("Prix Unitaire", format="%d €"),
                        "Valeur Totale (€)": st.column_config.NumberColumn("Valeur Évaluée", format="%d €"),
                    }
                )
                
                # --- ÉTAPE SUIVANTE : ENREGISTREMENT EN BASE NoSQL ---
                # Optionnel : Ajoutez ici votre logique `db.sauvegarder_inventaire_coop(nom_coop_active, resultats)`
                
            else:
                st.error("❌ Aucun bloc de matériau Sim-TP valide n'a pu être extrait. Vérifiez que vous avez copié le bon code source.")
        else:
            st.warning("⚠️ La zone de texte est vide. Veuillez y coller du code HTML avant de valider.")
