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

def analyser_consommation_firestore(liste_flux_bruts):
    """
    Analyse les documents bruts de Firestore pour calculer les volumes vendus
    et mesurer l'amplitude en jours de l'historique disponible.
    """
    conso_totale = {}
    dates_constatees = set()
    
    if not liste_flux_bruts:
        return conso_totale, 1
        
    for f in liste_flux_bruts:
        t_mouv = str(f.get("type", "")).strip()
        
        # Filtrage strict sur les types d'achats présents dans vos documents log_
        if t_mouv in ["ACHAT_INTERNE", "ACHAT_EXTERNE"]:
            d_txt = str(f.get("date_jeu", "")).strip()
            if d_txt:
                dates_constatees.add(d_txt)
                
            mats_dict = f.get("materiaux", {})
            if isinstance(mats_dict, dict):
                for m_k, m_v in mats_dict.items():
                    # Correction de la casse pour correspondre au format HTML (Capitalisé)
                    m_nom = m_k.strip().capitalize()
                    conso_totale[m_nom] = conso_totale.get(m_nom, 0.0) + float(m_v)
                    
    nb_jours_logs = len(dates_constatees) if len(dates_constatees) > 0 else 1
    return conso_totale, nb_jours_logs

def afficher_tab_stock(nom_coop_active, liste_flux_bruts=None):
    st.markdown("#### 🌍 Évaluation de la Valeur & Prévision des Besoins")
    st.caption("Collez le code source HTML de votre page de jeu pour auditer la valeur de votre actif et planifier vos commandes selon l'historique réel des ventes.")
    
    # 1. Saisie HTML brute
    html_brut = st.text_area(
        "Collez le code HTML de votre page de coopérative ici :", 
        height=120, 
        placeholder="<!DOCTYPE html> ...",
        key="area_import_html_coop_final_v5"
    )
    
    if html_brut.strip():
        resultats = extraire_donnees_html(html_brut)
        
        if resultats:
            df_inventaire = pd.DataFrame(resultats)
            
            # --- 📈 FINANCES ---
            valeur_totale_marchandises = df_inventaire["Valeur du Stock (€)"].sum()
            volume_total = df_inventaire["Quantité en Stock"].sum()
            
            st.markdown("---")
            c_val1, c_val2 = st.columns(2)
            with c_val1:
                st.metric("🔥 Valeur Estimée des Stocks", f"{int(valeur_totale_marchandises):,}".replace(",", " ") + " €")
            with c_val2:
                st.metric("📦 Volume Global Entreposé", f"{int(volume_total):,}".replace(",", " ") + " u / t")
                
            # --- 🔮 CALCUL PRÉDICTIF SUR LES DOCUMENTS FIRESTORE ---
            st.markdown("---")
            st.markdown("##### 🔮 Analyse Prédictive d'Épuisement (Basée sur vos documents Firestore)")
            
            historique_ventes, jours_observes = analyser_consommation_firestore(liste_flux_bruts)
            
            st.info(f"📊 Analyse basée sur un historique de **{jours_observes} jours** de ventes réelles détectés dans Firestore.")
            
            lignes_predictions = []
            for _, row in df_inventaire.iterrows():
                mat = row["Matériau"]
                stock_actuel = row["Quantité en Stock"]
                unite_mat = row["Unité"]
                
                # Consommation moyenne par jour
                total_vendu = historique_ventes.get(mat, 0.0)
                conso_journaliere = round(total_vendu / jours_observes, 1)
                
                # Calcul de l'autonomie restante
                if conso_journaliere > 0:
                    jours_autonomie = round(stock_actuel / conso_journaliere, 1)
                    qte_securite_7j = int(conso_journaliere * 7)
                    a_commander = max(0, qte_securite_7j - stock_actuel)
                else:
                    jours_autonomie = 999.0
                    a_commander = 0
                
                # Seuils d'alertes graphiques
                if jours_autonomie <= 1.5:
                    statut_alerte = "🚨 Rupture Imminente (< 1.5j)"
                elif jours_autonomie <= 4.0:
                    statut_alerte = "⚠️ Stock Faible (< 4j)"
                elif jours_autonomie == 999.0:
                    statut_alerte = "💤 Dormant (Aucun achat)"
                else:
                    statut_alerte = "🟢 Confortable"
                    
                lignes_predictions.append({
                    "Ressource": mat,
                    "Stock Actuel": stock_actuel,
                    "Ventes Moyennes (/jour)": conso_journaliere,
                    "Autonomie Restante": "Infini" if jours_autonomie == 999.0 else f"{jours_autonomie} j",
                    "État Alerte": statut_alerte,
                    "À Commander (tenir 7j)": f"{a_commander} {unite_mat}" if a_commander > 0 else "Rien à prévoir"
                })
                
            df_predictif = pd.DataFrame(lignes_predictions)
            
            st.dataframe(
                df_predictif,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stock Actuel": st.column_config.NumberColumn("En Stock", format="%d"),
                    "Ventes Moyennes (/jour)": st.column_config.NumberColumn("Conso/jour", format="%.1f"),
                    "État Alerte": st.column_config.TextColumn("🚨 Urgence"),
                    "À Commander (tenir 7j)": st.column_config.TextColumn("🧱 Commande Recommandée"),
                }
            )
            
            # --- 📋 GRAND LIVRE COMPTABLE ---
            st.markdown("---")
            st.markdown("##### 📋 Liste des prix & valeurs de l'inventaire")
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
            st.error("❌ Erreur de lecture de l'HTML. Vérifiez que vous avez copié le code de la page 'Ma coopérative'.")
