import streamlit as st
import pandas as pd
import database as db
from bs4 import BeautifulSoup
import re
import math

def afficher_onglet_suivi_contrats():
    st.subheader("📋 Analyse des Contrats, Logistique & Masse Salariale CDI")
    st.write(
        "Collez le code source HTML de vos **Contrats** et de votre **Aire de Stockage** "
        "pour croiser vos besoins logistiques de l'étape suivante avec vos stocks réels et vos paies CDI."
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
    traduction_cles = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", 
        "armature": "Armature", "tole": "Tôle", 
        "beton": "Béton", "panneaux": "Panneaux",
        "tuyaux": "Tuyaux", "canalisation": "Canalisations", 
        "poutre": "Poutres"
    }

    # Récupération en direct des configurations de prix mini et de salaires sur Firebase
    prix_coops_mini = db.charger_materiaux_config()
    
    # --- 👥 EXTRACTION DES TARIFS CDI DEPUIS FIREBASE ---
    px_cond = 1600.0 / 7.0  
    px_chef = 2100.0 / 7.0
    px_ouvrier = 1470.0 / 7.0
    
    try:
        snap_cond = db.db.collection("synthese_grille_tarifaire").document("Conducteur_CDI (Salaire mensuel)").get().to_dict()
        if snap_cond: 
            px_cond = float(snap_cond.get("prix_moyen_mensuel", 1600.0)) / 7.0
            
        snap_chef = db.db.collection("synthese_grille_tarifaire").document("Chef_CDI (Salaire mensuel)").get().to_dict()
        if snap_chef: 
            px_chef = float(snap_chef.get("prix_moyen_mensuel", 2100.0)) / 7.0
            
        snap_ouv = db.db.collection("synthese_grille_tarifaire").document("Ouvrier_CDI (Salaire mensuel)").get().to_dict()
        if snap_ouv: 
            px_ouvrier = float(snap_ouv.get("prix_moyen_mensuel", 1470.0)) / 7.0
    except Exception:
        pass

    # Initialisation des compteurs logistiques globaux
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
    # --- ÉTAPE B : EXTRACTION DES CONTRATS EN COURS & CALCULS RH ---
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

                form_annuler = item.find('form', action=lambda x: x and 'annuler-contrat' in x)
                id_contrat = "Inconnu"
                if form_annuler:
                    input_id = form_annuler.find('input', {'name': 'id'})
                    if input_id:
                        id_contrat = input_id.get('value', 'Inconnu')

                surface = "Inconnue"
                materiaux_texte = "Aucun"
                statut = "Non démarré"
                
                paragraphs = item.find_all('p')
                for p in paragraphs:
                    text = p.text.strip()
                    if "Surface du chantier" in text:
                        surface = text.split(':')[-1].strip()
                    if "Matériaux nécessaires" in text:
                        materiaux_texte = text.split('Matériaux nécessaires :')[-1].strip()

                status_card = item.find(class_='basic-card')
                if status_card:
                    statut = status_card.text.strip()

                # --- 👥 1. MASSE SALARIALE CDI (JOURNÉE ENTAMÉE = DUE) ---
                duree_totale_jours = 1.0
                chiffres_surface = re.findall(r"(\d+)", surface)
                if chiffres_surface:
                    val_surface = float(chiffres_surface[0])
                    if "km" in surface.lower():
                        duree_totale_jours = val_surface 
                    elif "m2" in surface.lower():
                        duree_totale_jours = max(1.0, math.ceil(val_surface / 100.0))

                # Définition des structures RH d'étapes Sim-TP
                nb_cond, nb_chef, nb_ouv = 1.0, 0.0, 0.0
                if "tuyaux" in nom.lower() or "assainissement" in nom.lower():
                    nb_cond, nb_chef, nb_ouv = 1.0, 1.0, 2.0
                elif "hangar" in nom.lower() or "batiment" in nom.lower():
                    nb_cond, nb_chef, nb_ouv = 1.0, 1.0, 3.0

                # Calcul de la main d'œuvre sur les journées dues
                jours_dus = math.ceil(duree_totale_jours)
                cout_salaires_contrat = (
                    (nb_cond * px_cond) + (nb_chef * px_chef) + (nb_ouv * px_ouvrier)
                ) * jours_dus

                # --- 🧱 2. CALCUL DU COÛT DES MATÉRIAUX ---
                cout_mats_contrat = 0.0
                if "aucun" not in materiaux_texte.lower():
                    for cle_reg, nom_officiel in traduction_cles.items():
                        if cle_reg in materiaux_texte.lower():
                            pattern = re.compile(rf"{cle_reg}.*?(\d[\d\s]*)", re.IGNORECASE)
                            match = pattern.search(materiaux_texte.lower().replace("é", "e").replace("ô", "o"))
                            if match:
                                val_requis = float(match.group(1).replace(" ", ""))
                                besoins_cumules[nom_officiel] += val_requis
                                prix_u = float(prix_coops_mini.get(nom_officiel, 0.0))
                                cout_mats_contrat += val_requis * prix_u

                # Rentabilité nette
                marge_nette_prevue = revenu - cout_mats_contrat - cout_salaires_contrat

                # 🎯 Les colonnes Niveau et Surface ne sont plus injectées ici
                contrats_list.append({
                    "ID Contrat": id_contrat,
                    "Nom du Chantier": nom,
                    "Chiffre d'Affaires (€)": revenu,
                    "Coût Matériaux (€)": cout_mats_contrat,
                    "Masse Salariale (€)": cout_salaires_contrat,
                    "Marge Nette (€)": marge_nette_prevue,
                    "Matériaux Étape Suivante": materiaux_texte,
                    "Statut Actuel": statut
                })

            if contrats_list:
                df_contrats = pd.DataFrame(contrats_list)
                total_ca = df_contrats["Chiffre d'Affaires (€)"].sum()
                total_cout_mats = df_contrats["Coût Matériaux (€)"].sum()
                total_salaires = df_contrats["Masse Salariale (€)"].sum()
                total_marge_nette = df_contrats["Marge Nette (€)"].sum()

                # Rendu du tableau principal filtré sans Niveau ni Surface
                st.markdown(f"### 🏗️ Vos Chantiers Signés ({len(contrats_list)} détectés)")
                st.dataframe(
                    df_contrats, 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Chiffre d'Affaires (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Coût Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Masse Salariale (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Marge Nette (€)": st.column_config.NumberColumn(format="%.0f €")
                    }
                )

                # KPIs macro-économiques consolidés d'entreprise
                c_total1, c_total2, c_total3, c_total4 = st.columns(4)
                with c_total1:
                    st.metric(label="Chiffre d'Affaires Prévu", value=f"{total_ca:,.0f}".replace(",", " ") + " €")
                with c_total2:
                    st.metric(label="Budget Matériaux Étape Suivante", value=f"{total_cout_mats:,.0f}".replace(",", " ") + " €", delta_color="inverse")
                with c_total3:
                    st.metric(label="Masse Salariale Globale CDI", value=f"{total_salaires:,.0f}".replace(",", " ") + " €", delta_color="inverse")
                with c_total4:
                    st.metric(label="Bénéfice Net Réel Estimé", value=f"{total_marge_nette:,.0f}".replace(",", " ") + " €")

                # ==========================================================================
                # --- ÉTAPE C : COMPARATEUR LOGISTIQUE (BESOINS VS STOCKS DE L'AIRE) ---
                # ==========================================================================
                st.markdown("---")
                st.markdown("### 📊 Comparateur Logistique : Besoins Étape Suivante vs Stocks Disponibles")

                if not stocks_extraits:
                    st.info("💡 Pour activer la comparaison de votre stock réel (Aire) et calculer vos restes à charge, collez le code HTML de votre aire de stockage en haut à droite.")

                lignes_comparatif = []
                cout_total_achat_coop = 0.0

                for mat_nom in traduction_cles.values():
                    besoin = besoins_cumules[mat_nom]
                    stock = stocks_disponibles[mat_nom]
                    ecart = stock - besoin

                    prix_unitaire_coop = float(prix_coops_mini.get(mat_nom, 0.0))

                    if besoin > 0 or stock > 0:
                        manquant = abs(ecart) if ecart < 0 else 0.0
                        cout_achat_ligne = manquant * prix_unitaire_coop
                        cout_total_achat_coop += cout_achat_ligne

                        status_icone = "✅ Stock OK" if ecart >= 0 else "🚨 À commander"

                        lignes_comparatif.append({
                            "Matériau": mat_nom,
                            "Total Requis (Étape Suivante)": besoin,
                            "En Réserve (Aire)": stock,
                            "Écart Restant": ecart,
                            "Prix Mini Coop": f"{prix_unitaire_coop:.0f} €",
                            "Reste à Payer (€)": cout_achat_ligne,
                            "Statut Logistique": status_icone
                        })

                if lignes_comparatif:
                    df_comparatif = pd.DataFrame(lignes_comparatif)

                    st.dataframe(
                        df_comparatif,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Requis (Étape Suivante)": st.column_config.NumberColumn(format="%.0f"),
                            "En Réserve (Aire)": st.column_config.NumberColumn(format="%.0f"),
                            "Écart Restant": st.column_config.NumberColumn(format="%.0f"),
                            "Reste à Payer (€)": st.column_config.NumberColumn(format="%.0f €"),
                            "Statut Logistique": st.column_config.TextColumn("Disponibilité")
                        }
                    )

                    if stocks_extraits:
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric(
                                label="💰 Reste à débourser en coopératives pour l'étape suivante",
                                value=f"{cout_total_achat_coop:,.0f}".replace(",", " ") + " €"
                            )
                        with col_res2:
                            manquants_check = df_comparatif[df_comparatif["Écart Restant"] < 0]
                            if not manquants_check.empty:
                                st.error("🚨 Des matériaux manquent pour ouvrir l'étape suivante ! Consultez la colonne 'Reste à Payer (€)'.")
                            else:
                                st.success("🎉 Vos stocks actuels couvrent à 100% vos besoins futurs. Aucun achat requis !")
                else:
                    st.caption("Félicitations, aucun besoin en matériau détecté sur vos fiches.")
            else:
                st.warning("⚠️ Aucun contrat valide trouvé dans le premier bloc HTML.")

        except Exception as e:
            st.error(f"❌ Erreur lors du parsing des fichiers : {e}")
