import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def afficher_onglet_marche_actuel():
    st.header("🌍 Observatoire du Marché & Comparateur des Coopératives")
    st.write(
        "Collez ci-dessous le code HTML de votre page 'Acheter des matériaux' (les coopératives) "
        "pour extraire, trier et classer toutes les offres de votre région en temps réel."
    )

    # Zone de saisie pour le code source du marché
    html_marche = st.text_area(
        "Collez le code HTML du marché des coopératives :", 
        height=180, 
        placeholder="<!DOCTYPE html> ... </html>", 
        key="text_area_marche_public_coops"
    )

    if html_marche:
        try:
            soup = BeautifulSoup(html_marche, 'html.parser')
            
            # Table de correspondance légale
            liaison_categories = {
                "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", 
                "armature": "Armature métallique", "toles_ondulees": "Plaque de tôle ondulée", 
                "beton": "Béton", "panneaux": "Panneaux signalisation", 
                "tuyaux": "Tuyaux d'eau standards", "tuyaux_assainissement": "Canalisations eaux usées", 
                "poutres_acier": "Poutres en acier"
            }

            cartes_offres = soup.find_all(class_="exp-card")
            offres_recensees = []

            for carte in cartes_offres:
                cat_brute = carte.get("data-category")
                if cat_brute in liaison_categories:
                    nom_materiau = liaison_categories[cat_brute]
                    
                    # 1. Extraction du prix unitaire
                    title_span = carte.find(class_="exp-title")
                    prix_unitaire = 0.0
                    if title_span:
                        match_prix = re.search(r"(\d[\d\s]*)\s*€", title_span.text)
                        if match_prix:
                            prix_unitaire = float(match_prix.group(1).replace(" ", ""))

                    # 2. Extraction du nom de la coopérative et des volumes dispo
                    form_body = carte.find(class_="exp-body")
                    if form_body:
                        p_elements = form_body.find_all('p')
                        nom_coop = "Système / Inconnu"
                        quantite_dispo = "Illimitée"
                        
                        if len(p_elements) >= 2:
                            nom_coop = p_elements[0].text.strip()
                            txt_qte = p_elements[1].text.lower()
                            
                            if "illimite" not in txt_qte:
                                match_qte = re.search(r"(\d[\d\s]*)", txt_qte)
                                if match_qte:
                                    quantite_dispo = int(match_qte.group(1).replace(" ", ""))

                        offres_recensees.append({
                            "Matériau": nom_materiau,
                            "Coopérative": nom_coop,
                            "Prix Unitaire (€)": prix_unitaire,
                            "Quantité Disponible": quantite_dispo
                        })

            if offres_recensees:
                df_marche = pd.DataFrame(offres_recensees)

                # --- FILTRE ET RECHERCHE INTERACTIVE ---
                st.markdown("### 🔍 Moteur de recherche du marché")
                liste_filtre_mat = ["Tous les matériaux"] + sorted(df_marche["Matériau"].unique().tolist())
                choix_mat = st.selectbox("Filtrer par type de ressource :", liste_filtre_mat)

                df_filtre = df_marche.copy()
                if choix_mat != "Tous les matériaux":
                    df_filtre = df_filtre[df_filtre["Matériau"] == choix_mat]

                # Tri automatique : Les moins chers d'abord
                df_filtre = df_filtre.sort_values(by=["Matériau", "Prix Unitaire (€)"], ascending=[True, True])

                # Affichage de la grille du marché
                st.markdown("#### 📊 Tableau Comparatif du Marché (Classé par prix croissant)")
                st.dataframe(
                    df_filtre, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Prix Unitaire (€)": st.column_config.NumberColumn("Prix proposé", format="%.0f €")
                    }
                )

                # --- FOCUS SUR LES MEILLEURS PLANS ---
                st.markdown("---")
                st.markdown("### 🏆 Les Meilleures Offres Détectées (Prix Plancher)")
                
                # Regroupement pour extraire la ligne avec le prix minimum par matériau
                df_meilleures = df_marche.loc[df_marche.groupby("Matériau")["Prix Unitaire (€)"].idxmin()]
                
                c_idx = 0
                cols_cards = st.columns(3)
                for _, r_best in df_meilleures.iterrows():
                    # On évite d'afficher le magasin système "Sim-TP" comme un bon plan (prix max)
                    if "sim-tp" not in r_best["Coopérative"].lower():
                        target_col = cols_cards[c_idx % 3]
                        with target_col:
                            st.metric(
                                label=f"🧱 {r_best['Matériau']}", 
                                value=f"{int(r_best['Prix Unitaire (€)'])} €", 
                                delta=r_best['Coopérative']
                            )
                        c_idx += 1
            else:
                st.warning("⚠️ Aucun élément de marché n'a été trouvé. Vérifiez que vous êtes sur la page d'achat de ressources.")
                
        except Exception as e:
            st.error(f"❌ Impossible d'extraire les offres du marché : {e}")
