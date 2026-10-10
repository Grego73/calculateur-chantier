import streamlit as st
import pandas as pd
import database as db
from bs4 import BeautifulSoup
import re

def afficher_onglet_suivi_contrats():
    st.subheader("📋 Analyse des Contrats & Estimation des Achats Matériaux")
    st.write(
        "Collez le code source HTML de vos **Contrats** et de votre **Aire de Stockage** "
        "pour croiser vos besoins avec vos stocks réels et calculer le coût d'achat au prix mini des coopératives."
    )

    # 1. Double zone d'importation HTML en colonnes
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

    # --- DICTIONNAIRES DE PARSING ET DE TRADUCTION ---
    # Liaison stricte avec les clés de votre base de données config_materiaux
    traduction_cles = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", 
        "armature": "Armature", "tole": "Tôle", 
        "beton": "Béton", "panneaux": "Panneaux",
        "tuyaux": "Tuyaux", "canalisation": "Canalisations", 
        "poutre": "Poutres"
    }

    # Récupération en direct des prix mini calculés et stockés par l'admin sur Firebase
    prix_coops_mini = db.charger_materiaux_config()

    # Initialisation des compteurs logistiques
    stocks_disponibles = {v: 0.0 for v in traduction_cles.values()}
    besoins_cumules = {v: 0.0 for v in traduction_cles.values()}

    # ==========================================================================
    # --- ÉTAPE A : EXTRACTION DES STOCKS DISPONIBLES DE L'AIRE ---
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
                            if cle_regex in nom_mat_brut.lower():
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
                        materiaux_texte = text.split('Matériaux nécessaires :')[-1].strip()

                # --- EXTRACTION DES BESOINS VIA REGEX ULTRA BLINDÉE ---
                if "aucun" not in materiaux_texte.lower():
                    for cle_reg, nom_officiel in traduction_cles.items():
                        if cle_reg in materiaux_texte.lower():
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
                # --- ÉTAPE C : COMPARATEUR BESOINS VS STOCKS AVEC PRIX MINI COOP ---
                # ==========================================================================
                st.markdown("---")
                st.markdown("### 📊 Analyse Logistique & Budget d'Achat Coopératives")
                
                if not stocks_extraits:
                    st.info("💡 Pour activer la comparaison des stocks et le calcul des coûts d'achat, collez le code HTML de votre aire de stockage en haut à droite.")
                
                lignes_comparatif = []
                cout_total_achat_coop = 0.0

                for mat_nom in traduction_cles.values():
                    besoin = besoins_cumules[mat_nom]
                    stock = stocks_disponibles[mat_nom]
                    ecart = stock - besoin
                    
                    # Récupération du prix mini enregistré sur Firebase pour ce matériau
                    prix_unitaire_coop = float(prix_coops_mini.get(mat_nom, 0.0))

                    if besoin > 0 or stock > 0:
                        # Calcul du coût financier de la commande (uniquement sur ce qui manque)
                        manquant = abs(ecart) if ecart < 0 else 0.0
                        cout_achat_ligne = manquant * prix_unitaire_coop
                        cout_total_achat_coop += cout_achat_ligne

                        status_icone = "✅ Stock OK" if ecart >= 0 else "🚨 À commander"
                        
                        lignes_comparatif.append({
                            "Matériau": mat_nom,
                            "Total Requis (Chantiers)": besoin,
                            "En Réserve (Aire)": stock,
                            "Écart Restant": ecart,
                            "Prix Mini Coop (€)": f"{prix_unitaire_coop:.0f} €",
                            "Coût d'Achat Estimé (€)": cout_achat_ligne,
                            "Statut Logistique": status_icone
                        })

                if lignes_comparatif:
                    df_comparatif = pd.DataFrame(lignes_comparatif)
                    
                    # Affichage de la table d'analyse financière et logistique
                    st.dataframe(
                        df_comparatif,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Requis (Chantiers)": st.column_config.NumberColumn(format="%.0f"),
                            "En Réserve (Aire)": st.column_config.NumberColumn(format="%.0f"),
                            "Écart Restant": st.column_config.NumberColumn(format="%.0f"),
                            "Coût d'Achat Estimé (€)": st.column_config.NumberColumn(format="%.0f €"),
                            "Statut Logistique": st.column_config.TextColumn("Disponibilité")
                        }
                    )
                    
                    # --- RENDU DES INDICATEURS DE COMMANDE FINAUX ---
                    if stocks_extraits:
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric(
                                label="💰 Budget d'Achat Total Estimé (Au Prix Mini)", 
                                value=f"{cout_total_achat_coop:,.0f}".replace(",", " ") + " €"
                            )
                        with col_res2:
                            manquants_check = df_comparatif[df_comparatif["Écart Restant"] < 0]
                            if not manquants_check.empty:
                                st.error("🚨 Des matériaux sont manquants ! Consultez la colonne 'Coût d'Achat Estimé' pour vos commandes.")
                            else:
                                st.success("🎉 Vos stocks actuels couvrent à 100% vos besoins. Aucun achat requis !")
                else:
                    st.caption("Félicitations, aucun besoin en matériau détecté sur vos fiches.")
            else:
                st.warning("⚠️ Aucun contrat valide trouvé dans le premier bloc HTML.")

        except Exception as e:
            st.error(f"❌ Erreur lors du parsing des fichiers : {e}")
