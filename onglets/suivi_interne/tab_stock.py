import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re
import unicodedata
from datetime import datetime
import database as db

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

def identifier_cle_unique(texte):
    """Fonction universelle de nettoyage par détection de racine (casse/accents/pluriels)."""
    if not texte:
        return "inconnu"
    
    texte_nettoye = str(texte).lower().strip()
    texte_nettoye = ''.join(c for c in unicodedata.normalize('NFD', texte_nettoye) if unicodedata.category(c) != 'Mn')
    texte_nettoye = texte_nettoye.replace(" ", "")

    if "sable" in texte_nettoye: return "sable"
    if "beton" in texte_nettoye: return "beton"
    if "poutre" in texte_nettoye: return "poutres"
    if "enrob" in texte_nettoye: return "enrobe"
    if "armatur" in texte_nettoye: return "armature"
    if "tole" in texte_nettoye: return "tole"
    if "pannea" in texte_nettoye: return "panneaux"
    if "canalisa" in texte_nettoye: return "canalisations"
    if "tuyau" in texte_nettoye: return "tuyaux"
    if "terre" in texte_nettoye: return "terre"
    
    return texte_nettoye

def analyser_consommation_periode(liste_flux_bruts):
    """
    Analyse les volumes vendus sur la période en cours.
    🎯 Uniquement basé sur ACHAT_INTERNE et ACHAT_EXTERNE (les réapprovisionnements sont exclus).
    """
    conso_totale = {}
    
    date_repere_str = st.session_state.get("point_reprise_date_compta", "01/08/2026")
    try:
        date_limite_cle = int("".join(reversed(date_repere_str.split("/"))))
        date_repere_dt = datetime.strptime(date_repere_str, "%d/%m/%Y")
        jours_ecoules = (datetime.now() - date_repere_dt).days
        if jours_ecoules <= 0:
            jours_ecoules = 1
    except Exception:
        date_limite_cle = 20260801
        jours_ecoules = 7

    if not liste_flux_bruts:
        return conso_totale, jours_ecoules
        
    for f in liste_flux_bruts:
        t_mouv = str(f.get("type", "")).strip()
        
        # 🎯 Filtrage strict sur les ACHATS uniquement
        if t_mouv in ["ACHAT_INTERNE", "ACHAT_EXTERNE"]:
            d_txt = str(f.get("date_jeu", "01/01/2000")).strip()
            
            try:
                cle_doc_actuel = int("".join(reversed(d_txt.split("/"))))
                if cle_doc_actuel < date_limite_cle:
                    continue 
            except Exception:
                pass
                
            mats_dict = f.get("materiaux", {})
            if isinstance(mats_dict, dict):
                for m_k, m_v in mats_dict.items():
                    cle_nosql = identifier_cle_unique(m_k)
                    conso_totale[cle_nosql] = conso_totale.get(cle_nosql, 0.0) + float(m_v)
                    
    return conso_totale, jours_ecoules

def afficher_tab_stock(nom_coop_active, liste_flux_bruts=None):
    st.markdown("#### 🌍 Évaluation de la Valeur & Prévision des Besoins")
    st.caption("Collez le code source HTML de votre page de jeu pour auditer l'inventaire et sauvegarder la valeur de votre actif.")
    
    html_brut = st.text_area(
        "Collez le code HTML de votre page de coopérative ici :", 
        height=120, 
        placeholder="<!DOCTYPE html> ...",
        key="area_import_html_coop_predict_v13"
    )
    
    if html_brut.strip():
        resultats = extraire_donnees_html(html_brut)
        
        if resultats:
            df_inventaire = pd.DataFrame(resultats)
            
            # --- 📈 FINANCES GLOBALES ---
            valeur_totale_marchandises = df_inventaire["Valeur du Stock (€)"].sum()
            volume_total = df_inventaire["Quantité en Stock"].sum()
            
            st.markdown("---")
            c_val1, c_val2 = st.columns(2)
            with c_val1:
                st.metric("🔥 Valeur Estimée des Stocks", f"{int(valeur_totale_marchandises):,}".replace(",", " ") + " €")
            with c_val2:
                st.metric("📦 Volume Global Entreposé", f"{int(volume_total):,}".replace(",", " ") + " u / t")
            
            # --- 💾 ENREGISTRER DANS FIRESTORE ---
            st.write("")
            if st.button("💾 ENREGISTRER CET INVENTAIRE DANS FIRESTORE", type="primary", use_container_width=True):
                with st.spinner("Mise à jour de la base de données..."):
                    try:
                        dictionnaire_stocks_nosql = {}
                        dictionnaire_prix_nosql = {}
                        
                        for _, row in df_inventaire.iterrows():
                            cle_technique = identifier_cle_unique(row["Matériau"])
                            dictionnaire_stocks_nosql[f"stock_{cle_technique}"] = int(row["Quantité en Stock"])
                            dictionnaire_prix_nosql[f"prix_{cle_technique}"] = float(row["Prix Unitaire (€)"])
                        
                        maintenant = datetime.now()
                        id_document = f"snapshot_stock_{maintenant.strftime('%Y%m%d_%H%M%S')}"
                        
                        donnees_a_sauvegarder = {
                            "type": "SNAPSHOT_STOCK",
                            "date_jeu": maintenant.strftime("%d/%m/%Y"),
                            "heure_jeu": maintenant.strftime("%H:%M"),
                            "valeur_totale_stock": valeur_totale_marchandises,
                            "volume_total_stock": volume_total,
                            "details_quantites": dictionnaire_stocks_nosql,
                            "details_prix": dictionnaire_prix_nosql,
                            "timestamp_enregistrement": maintenant.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne").document(id_document).set(donnees_a_sauvegarder)
                        db.enregistrer_log(type_action="INVENTAIRE", details=f"Mise à jour complète des stocks. Valeur totale arrêtée à {int(valeur_totale_marchandises):,} €.")
                        
                        st.success("🟢 L'inventaire réel et sa valeur globale ont été figés avec succès dans Firestore !")
                        st.cache_data.clear()
                        db.charger_flux_coop_cache.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'écriture Firestore : {e}")
            st.markdown("---")
                
            # --- 🔮 CALCUL PRÉDICTIF SUR LES ACHATS ---
            st.markdown("##### 🔮 Ordre d'Urgence des Réapprovisionnements (Basé sur le rythme des achats)")
            
            historique_ventes, jours_observes = analyser_consommation_periode(liste_flux_bruts)
            date_repere_active = st.session_state.get("point_reprise_date_compta", "01/08/2026")
            st.caption(f"Moyenne journalière des achats calculée sur {jours_observes} jours écoulés depuis le {date_repere_active}.")
            
            lignes_predictions = []
            for _, row in df_inventaire.iterrows():
                mat = row["Matériau"]
                stock_actuel = row["Quantité en Stock"]
                unite_mat = row["Unité"]
                
                cle_commune = identifier_cle_unique(mat)
                total_vendu = historique_ventes.get(cle_commune, 0.0)
                conso_journaliere = round(total_vendu / jours_observes, 1)
                
                if conso_journaliere > 0:
                    jours_autonomie = round(stock_actuel / conso_journaliere, 1)
                    qte_securite_7j = int(conso_journaliere * 7)
                    a_commander = max(0, qte_securite_7j - stock_actuel)
                    cle_tri_autonomie = jours_autonomie
                else:
                    jours_autonomie = 999.0
                    a_commander = 0
                    cle_tri_autonomie = 8888.0
                
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
                    "🚨 Urgence": statut_alerte,
                    "🧱 Commande Recommandée": f"{a_commander} {unite_mat}" if a_commander > 0 else "Rien à prévoir",
                    "_tri_technique": cle_tri_autonomie
                })
            df_predictif = pd.DataFrame(lignes_predictions)
            
            # 🎯 CLASSEMENT SYSTÉMATIQUE : Du stock le plus critique au plus confortable
            df_predictif = df_predictif.sort_values(by="_tri_technique", ascending=True)
            
            # Rendu du tableau prédictif principal trié par urgence
            st.dataframe(
                df_predictif,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stock Actuel": st.column_config.NumberColumn("En Stock", format="%d"),
                    "Ventes Moyennes (/jour)": st.column_config.NumberColumn("Achats/jour", format="%.1f"),
                    "🚨 Urgence": st.column_config.TextColumn("🚨 État Critique"),
                    "🧱 Commande Recommandée": st.column_config.TextColumn("🧱 Commande Conseil"),
                    "_tri_technique": None  # Masque complètement la colonne technique de tri à l'affichage
                }
            )
            
            # --- 📋 GRAND LIVRE DE L'INVENTAIRE COMPTABLE ---
            st.markdown("---")
            st.markdown("##### 📋 Liste des prix & valeurs de l'inventaire")
            st.dataframe(
                df_inventaire, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Matériau": st.column_config.TextColumn("🧱 Ressource"),
                    "Quantité en Stock": st.column_config.NumberColumn("Quantité", format="%d"),
                    "Unité": st.column_config.TextColumn("📦 Type"),
                    "Prix Unitaire (€)": st.column_config.NumberColumn("Prix Vente Fixé", format="%d €"),
                    "Valeur du Stock (€)": st.column_config.NumberColumn("Valeur Évaluée", format="%d €"),
                }
            )
        else:
            st.error("❌ Erreur de lecture de l'HTML. Vérifiez que vous avez copié le code de la page 'Ma coopérative'.")
