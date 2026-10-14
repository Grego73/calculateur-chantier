import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def extraire_donnees_html(html_content):
    """Analyse le code HTML de Sim-TP pour extraire les ressources, stocks et prix."""
    soup = BeautifulSoup(html_content, 'html.parser')
    donnees_mats = []
    cartes_materiaux = soup.find_all('div', class_=re.compile(r'cm33-card-project'))
    
    for carte in cartes_materiaux:
        div_nom = carte.find('div', class_='cm33-cp-name')
        if not div_nom:
            continue
        nom_mat = div_nom.text.strip()
        
        span_prog = carte.find('span', class_=re.compile(r'cm33-cp-pct'))
        stock_val = 0
        if span_prog:
            texte_stock = span_prog.text
            match_stock = re.search(r'En stock\s*:\s*([\d\s]+)', texte_stock)
            if match_stock:
                stock_val = int(match_stock.group(1).replace(' ', ''))
        
        input_prix = carte.find('input', attrs={'name': 'prix'})
        prix_val = 0
        if input_prix and input_prix.has_attr('value'):
            try:
                prix_val = float(input_prix['value'])
            except ValueError:
                pass
                
        unite = "u" if nom_mat in ["Armature métallique", "Plaque de tôle ondulée", "Panneaux signalisation", "Tuyaux d'eau standards", "Canalisations eaux usées", "Poutres en acier"] else "t"
                
        donnees_mats.append({
            "Matériau": nom_mat,
            "Quantité en Stock": stock_val,
            "Unité": unite,
            "Prix Unitaire (€)": prix_val,
            "Valeur du Stock (€)": int(stock_val * prix_val)
        })
    return donnees_mats

def calculer_statistiques_ventes(liste_flux):
    """Analyse l'historique des ventes pour en extraire le volume consommé moyen par ressource."""
    conso_par_materiau = {}
    if not liste_flux:
        return conso_par_materiau
        
    for f in liste_flux:
        if f.get("type") in ["ACHAT_INTERNE", "ACHAT_EXTERNE"]:
            mats_dict = f.get("materiaux", {})
            if isinstance(mats_dict, dict):
                for m_k, m_v in mats_dict.items():
                    m_nom = m_k.capitalize()
                    conso_par_materiau[m_nom] = conso_par_materiau.get(m_nom, 0.0) + float(m_v)
                    
    return conso_par_materiau

def afficher_tab_stock(nom_coop_active, liste_flux=None):
    st.markdown("#### 🌍 Évaluation de la Valeur & Prévision des Besoins")
    st.caption("Collez le code source HTML de votre page de jeu pour auditer la valeur de l'actif et planifier vos futurs réapprovisionnements.")
    
    # 1. Zone de saisie HTML
    html_brut = st.text_area(
        "Collez le code HTML de votre page de coopérative ici :", 
        height=120, 
        placeholder="<!DOCTYPE html> ...",
        key="area_import_html_coop_v3"
    )
    
    if html_brut.strip():
        resultats = extraire_donnees_html(html_brut)
        
        if resultats:
            df_inventaire = pd.DataFrame(resultats)
            
            # --- 📈 TABLEAU DE BORD FINANCIER ---
            valeur_totale_marchandises = df_inventaire["Valeur du Stock (€)"].sum()
            volume_total = df_inventaire["Quantité en Stock"].sum()
            
            st.markdown("---")
            c_val1, c_val2 = st.columns(2)
            with c_val1:
                st.metric("🔥 Valeur Estimée des Stocks", f"{int(valeur_totale_marchandises):,}".replace(",", " ") + " €")
            with c_val2:
                st.metric("📦 Volume Évalué Entassé", f"{int(volume_total):,}".replace(",", " ") + " u / t")
                
            # --- 🔮 MOTEUR DE PRÉVISION DES STOCKS (Basé sur l'historique des ventes) ---
            st.markdown("---")
            st.markdown("##### 🔮 Analyse Prédictive d'Épuisement des Stocks")
            
            # Récupération et traitement des ventes historiques
            historique_ventes = calculer_statistiques_ventes(liste_flux)
            
            # Configuration de la fenêtre d'analyse temporelle (ajustable par l'admin)
            nb_jours_historique = st.slider("Fenêtre de l'historique analysé (en jours) :", min_value=1, max_value=30, value=7)
            
            lignes_predictions = []
            for _, row in df_inventaire.iterrows():
                mat = row["Matériau"]
                stock_actuel = row["Quantité en Stock"]
                unite_mat = row["Unité"]
                
                # Calcul de la consommation moyenne par jour constaté dans la base de données
                total_vendu = historique_ventes.get(mat, 0.0)
                conso_journaliere_estimee = round(total_vendu / nb_jours_historique, 1)
                
                # Évaluation de l'autonomie restante en jours
                if conso_journaliere_estimee > 0:
                    jours_autonomie = round(stock_actuel / conso_journaliere_estimee, 1)
                    # Quantité idéale à commander pour tenir une semaine (7 jours de consommation)
                    qte_cible_7_jours = int(conso_journaliere_estimee * 7)
                    a_commander = max(0, qte_cible_7_jours - stock_actuel)
                else:
                    jours_autonomie = 999.0  # Stock dormant ou aucune vente constatée
                    a_commander = 0
                
                # Mise en forme du statut d'alerte pour l'affichage utilisateur
                if jours_autonomie <= 2.0:
                    statut_alerte = "🚨 Rupture Critique (< 2j)"
                elif jours_autonomie <= 5.0:
                    statut_alerte = "⚠️ Stock Faible (< 5j)"
                elif jours_autonomie == 999.0:
                    statut_alerte = "💤 Dormant (Aucune Vente)"
                else:
                    statut_alerte = "🟢 Confortable"
                    
                lignes_predictions.append({
                    "Ressource": mat,
                    "Stock": stock_actuel,
                    "Type": unite_mat,
                    "Vente Moyenne (/jour)": conso_journaliere_estimee,
                    "Autonomie Évaluée (Jours)": "Infini" if jours_autonomie == 999.0 else f"{jours_autonomie} j",
                    "Statut Alerte": statut_alerte,
                    "À Commander pour tenir 7j": f"{a_commander} {unite_mat}" if a_commander > 0 else "Rien à prévoir"
                })
                
            df_predictif = pd.DataFrame(lignes_predictions)
            
            # Rendu du tableau prédictif avec coloration et configurations d'affichage applicatives
            st.dataframe(
                df_predictif,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Vente Moyenne (/jour)": st.column_config.NumberColumn("Conso moyenne/jour", format="%.1f"),
                    "Statut Alerte": st.column_config.TextColumn("🚨 État Critique"),
                    "À Commander pour tenir 7j": st.column_config.TextColumn("🧱 Quantité d'Urgence"),
                }
            )
            
            # --- 📋 GRAND LIVRE COMPTABLE BRUT ---
            st.markdown("---")
            st.markdown("##### 📋 Inventaire Brut Comptable")
            st.dataframe(
                df_inventaire, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Quantité en Stock": st.column_config.NumberColumn("Quantité", format="%d"),
                    "Prix Unitaire (€)": st.column_config.NumberColumn("Prix Vente Fixé", format="%d €"),
                    "Valeur du Stock (€)": st.column_config.NumberColumn("Valeur Évaluée", format="%d €"),
                }
            )
        else:
            st.error("❌ Impossible de décoder le tableau de marchandises. Vérifiez que vous avez copié le code de la page 'Ma coopérative'.")
