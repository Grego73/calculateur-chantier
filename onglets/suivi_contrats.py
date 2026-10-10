import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

def afficher_onglet_suivi_contrats():
    st.header("📋 Importation et Extraction des Contrats en Cours")
    st.write("Collez ici le code source HTML de votre page 'Mes contrats' sur Sim-TP pour extraire automatiquement les informations chiffrées.")

    # Zone de saisie pour le code source HTML
    html_data = st.text_area("Code source HTML de la page :", height=200, placeholder="<!DOCTYPE html> ... </html>")

    if html_data:
        try:
            soup = BeautifulSoup(html_data, 'html.parser')
            
            # 1. Extraction du budget/trésorerie
            money_container = soup.find('div', id='header-breadcrumb-container')
            tresorerie = "Inconnue"
            if money_container:
                money_p = money_container.find('p')
                if money_p:
                    # Garde uniquement les chiffres pour le calcul
                    tresorerie_brute = re.sub(r'[^0-9]', '', money_p.text)
                    if tresorerie_brute:
                        tresorerie = f"{int(tresorerie_brute):,} €".replace(",", " ")

            # Affichage de la situation globale
            st.subheader("💰 Situation financière extraite")
            st.metric(label="Trésorerie disponible", value=tresorerie)

            # 2. Extraction des contrats via l'accordéon
            contrats_list = []
            items = soup.find_all(class_='js-accordion-item')

            for item in items:
                # Récupération des attributs de base
                nom = item.get('data-nom', 'Inconnu')
                revenu_brut = item.get('data-revenu', '0')
                revenu = float(revenu_brut) if revenu_brut.isdigit() else 0.0
                niveau = item.get('data-niveau', 'Inconnu')

                # Récupération de l'ID via le formulaire d'annulation
                form_annuler = item.find('form', action=lambda x: x and 'annuler-contrat' in x)
                id_contrat = "Inconnu"
                if form_annuler:
                    input_id = form_annuler.find('input', {'name': 'id'})
                    if input_id:
                        id_contrat = input_id.get('value', 'Inconnu')

                # Parsing des paragraphes de détails
                surface = "Inconnue"
                materiaux = "Aucun"
                paragraphs = item.find_all('p')
                for p in paragraphs:
                    text = p.text.strip()
                    if "Surface du chantier" in text:
                        surface = text.split(':')[-1].strip()
                    if "Matériaux nécessaires" in text:
                        materiaux = text.split(':')[-1].strip()

                # Statut de l'étape en cours
                status_card = item.find(class_='basic-card')
                statut = status_card.text.strip() if status_card else "Non démarré"

                contrats_list.append({
                    "ID Contrat": id_contrat,
                    "Nom du Chantier": nom,
                    "Niveau": niveau,
                    "Revenu (€)": revenu,
                    "Surface": surface,
                    "Matériaux requis": materiaux,
                    "Statut actuel": statut
                })

            if contrats_list:
                df = pd.DataFrame(contrats_list)

                st.subheader(f"🏗️ Liste des chantiers détectés ({len(contrats_list)})")
                
                # Tableau interactif et propre des contrats
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Vue synthétique sous forme de KPI cumulés
                st.subheader("📊 Totaux Prévisionnels")
                col1, col2 = st.columns(2)
                with col1:
                    total_rev = df["Revenu (€)"].sum()
                    st.metric(label="Revenus cumulés attendus", value=f"{total_rev:,} €".replace(",", " "))
                with col2:
                    st.info("💡 Utilisez les filtres natifs du tableau ci-dessus pour trier par revenu ou par état d'avancement.")
            else:
                st.warning("⚠️ Aucun contrat n'a pu être extrait. Vérifiez que vous avez copié l'intégralité du code source.")

        except Exception as e:
            st.error(f"❌ Une erreur est survenue lors de l'analyse du code source : {e}")
