import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def afficher_onglet_suivi_contrats():
    st.subheader("📋 Analyse des Contrats & Vérification des Matériaux Disponibles")
    st.write(
        "Collez le code source HTML de vos **Contrats** et de votre **Aire de Stockage** "
        "pour croiser vos besoins logistiques avec vos stocks réels."
    )

    # Double zone d'importation HTML en colonnes
    col_import1, col_import2 = st.columns(2)
    
    with col_import1:
        html_contrats = st.text_area(
            "1. Code HTML 'Mes contrats en cours' :", 
            height=150, 
            placeholder="<!DOCTYPE html> ... </html>", 
            key="html_contrats_cross"
        )
        
    with col_import2:
        html_stockage = st.text_area(
            "2. Code HTML 'Mon aire de stockage' :", 
            height=150, 
            placeholder="<!DOCTYPE html> ... </html>", 
            key="html_stockage_cross"
        )

    # Dictionnaires de parsing et de traduction standardisés
    traduction_cles = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", 
        "armature": "Armature métallique", "tole": "Plaque de tôle ondulée", 
        "beton": "Béton", "panneaux": "Panneaux signalisation",
        "tuyaux": "Tuyaux d'eau standards", "canalisations": "Canalisations eaux usées", 
        "poutres": "Poutres en acier"
    }

    # Initialisation des compteurs
    stocks_disponibles = {v: 0.0 for v in traduction_cles.values()}
    besoins_cumules = {v: 0.0 for v in traduction_cles.values()}

    # ==========================================================================
    # --- ÉTAPE A : EXTRACTION DES STOCKS DISPONIBLES ---
    # ==========================================================================
    stocks_extraits = False
    if html_stockage:
        try:
            soup_stock = BeautifulSoup(html_stockage, 'html.parser')
            chips_elements = soup_stock.find_all(class_='custom-chip')

            for chip in chips_elements:
                full_w_span = chip.find(class_='full-w')
                if full_w_span:
                    text_spans = full_w_span.find_all('span')
                    if len(text_spans) >= 2:
                        nom_mat_brut = text_spans[0].text.strip()
                        qte_brute = text_spans[1].text.strip()
                        valeur_num = float(re.sub(r'[^0-9]', '', qte_brute)) if re.sub(r'[^0-9]', '', qte_brute) else 0.0
                        
                        for cle_regex, nom_officiel in traduction_cles.items():
                            if cle_regex in nom_mat_brut.lower() or nom_officiel.lower() in nom_mat_brut.lower():
                                stocks_disponibles[nom_officiel] = valeur_num
                                break
            stocks_extraits = True
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse de l'aire de stockage : {e}")

    # ==========================================================================
    # --- ÉTAPE B : EXTRACTION DES CONTRATS EN COURS ---
    # ==========================================================================
    if html_contrats:
        try:
            soup_contrats = BeautifulSoup(html_contrats, 'html.parser')
            
            # Extraction de la trésorerie
            money_container = soup_contrats.find('div', id='header-breadcrumb-container')
            tresorerie_affiche = "Inconnue"
            if money_container:
                money_p = money_container.find('p')
                if money_p:
                    tresorerie_chiffre = re.sub(r'[^0-9]', '', money_p.text)
                    if tresorerie_chiffre:
                        tresorerie_affiche = f"{int(tresorerie_chiffre):,} €".replace(",", " ")

            st.markdown("### 💰 Situation Financière Extraite")
            st.metric(label="Trésorerie en compte de l'entreprise", value=tresorerie_affiche)
            st.markdown("---")

            # Parsing des contrats
            contrats_list = []
            items = soup_contrats.find_all(class_='js-accordion-item')

            for item in items:
                nom = item.get('data-nom', 'Chantier Inconnu')
                revenu_brut = item.get('data-revenu', '0')
                revenu = float(revenu_brut) if revenu_brut.isdigit() else 0.0
                niveau = item.get('data-niveau', 'N/A')

                form_annuler = item.find('form', action=lambda x: x and 'annuler-contrat' in x)
                id_contrat = "Inconnu"
                if form_annuler:
                    input_id = form_annuler.find('input', {'name': 'id'})
                    if input_id:
                        id_contrat = input_id.get('value', 'Inconnu')

                surface = "Inconnue"
                materiaux_texte = "Aucun"
                paragraphs = item.find_all('p')
                for p in paragraphs:
                    text = p.text.strip()
                    if "Surface du chantier" in text:
                        surface = text.split(':')[-1].strip()
                    if "Matériaux nécessaires" in text:
                        # On nettoie la chaîne pour enlever l'en-tête "Matériaux nécessaires :"
                        materiaux_texte = text.split('Matériaux nécessaires :')[-1].strip()

                # --- 🎯 CORRECTIF DU MOTEUR LOGISTIQUE (REGEX ROBUSTE) ---
                if "aucun" not in materiaux_texte.lower():
                    # Recherche globale de tous les couples [Nom / Chiffre] dans la chaîne nettoyée
                    # Exemple traité : "Enrobé : 1710 tonnes + Sable : 1350 tonnes"
                    for cle_reg, nom_officiel in traduction_cles.items():
                        if cle_reg in materiaux_texte.lower():
                            # Extraction du nombre spécifique qui suit directement le nom du matériau
                            pattern = re.compile(rf"{cle_reg}.*?(\d[\d\s]*)", re.IGNORECASE)
                            match = pattern.search(materiaux_texte.lower().replace("é", "e").replace("ô", "o"))
                            if match:
                                val_requis = float(match.group(1).replace(" ", ""))
                                besoins_cumules[nom_officiel] += val_requis

                status_card = item.find(class_='basic-card')
                statut = status_card.text.strip() if status_card else "Non démarré"

                contrats_list.append({
                    "ID Contrat": id_contrat,
                    "Nom du Chantier": nom,
                    "Niveau": f"Niveau {niveau}",
                    "Chiffre d'Affaires (€)": revenu,
                    "Surface": surface,
                    "Matériaux Requis": materiaux_texte,
                    "Statut Actuel": statut
                })

            if contrats_list:
                df_contrats = pd.DataFrame(contrats_list)
                total_ca = df_contrats["Chiffre d'Affaires (€)"].sum()

                # Rendu du tableau des contrats
                st.markdown(f"### 🏗️ Vos Chantiers Signés ({len(contrats_list)} détectés)")
                st.dataframe(df_contrats, use_container_width=True, hide_index=True)
                st.metric(label="Chiffre d'Affaires global prévisionnel", value=f"{total_ca:,.0f}".replace(",", " ") + " €")
                
                # ==========================================================================
                # --- ÉTAPE C : COMPARATEUR BESOINS VS STOCKS ---
                # ==========================================================================
                st.markdown("---")
                st.markdown("### 📊 Comparateur Logistique : Besoins Chantiers vs Stocks Disponibles")
                
                if not stocks_extraits:
                    st.info("💡 Pour activer la comparaison des stocks en temps réel, collez le code HTML de votre aire de stockage dans la zone supérieure droite.")
                
                lignes_comparatif = []
                for mat_nom in traduction_cles.values():
                    besoin = besoins_cumules[mat_nom]
                    stock = stocks_disponibles[mat_nom]
                    ecart = stock - besoin
                    
                    if besoin > 0 or stock > 0:
                        status_icone = "✅ OK" if ecart >= 0 else "🚨 MANQUANT"
                        lignes_comparatif.append({
                            "Matériau": mat_nom,
                            "Total Requis (Chantiers)": besoin,
                            "En Réserve (Aire)": stock,
                            "Écart Restant": ecart,
                            "Statut Logistique": status_icone
                        })

                if lignes_comparatif:
                    df_comparatif = pd.DataFrame(lignes_comparatif)
                    
                    st.dataframe(
                        df_comparatif,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Requis (Chantiers)": st.column_config.NumberColumn(format="%.0f"),
                            "En Réserve (Aire)": st.column_config.NumberColumn(format="%.0f"),
                            "Écart Restant": st.column_config.NumberColumn(format="%.0f"),
                            "Statut Logistique": st.column_config.TextColumn("Disponibilité")
                        }
                    )
                    
                    # Alertes visuelles de santé logistique
                    manquants = df_comparatif[df_comparatif["Écart Restant"] < 0]
                    if not manquants.empty and stocks_extraits:
                        st.error("⚠️ **Alerte Approvisionnement :** Vos stocks actuels ne couvrent pas la totalité des besoins de vos chantiers en cours.")
                    elif stocks_extraits:
                        st.success("🎉 **Logistique Parfaite :** Votre aire de stockage contient toutes les provisions requises pour couvrir vos contrats actuels !")
            else:
                st.warning("⚠️ Aucun contrat valide trouvé dans le premier bloc HTML.")

        except Exception as e:
            st.error(f"❌ Erreur lors du parsing des fichiers : {e}")
