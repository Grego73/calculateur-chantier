import streamlit as st
import database as db
import math
from bs4 import BeautifulSoup
import re

def afficher_onglet_materiaux(MATERIAUX_DB):
    st.markdown("### 🧱 Coût unitaire d'Approvisionnement des Matériaux")
    
    # Table de correspondance entre les identifiants HTML (data-category) et les clés de votre base NoSQL
    liaison_categories = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", 
        "armature": "Armature", "toles_ondulees": "Tôle", 
        "beton": "Béton", "panneaux": "Panneaux", "tuyaux": "Tuyaux", 
        "tuyaux_assainissement": "Canalisations", "poutres_acier": "Poutres"
    }

    form_mats = dict(MATERIAUX_DB)

    # ==========================================================================
    # --- 🎯 PARSEUR ET INJECTEUR AUTOMATIQUE DU MARCHÉ DES COOPÉRATIVES ---
    # ==========================================================================
    with st.expander("📥 MISE À JOUR AUTOMATIQUE VIA HTML DES COOPÉRATIVES", expanded=True):
        st.write("Collez ici le code source HTML de la page 'Acheter des matériaux' pour configurer automatiquement les meilleurs prix du marché.")
        html_coops = st.text_area("Code source HTML du marché :", height=130, key="textarea_update_prix_mats_coop")
        
        if st.button("⚡ ANALYSER LE MARCHÉ & RETENIR LES MEILLEURS TARIFS", type="secondary", use_container_width=True):
            if html_coops.strip():
                try:
                    soup = BeautifulSoup(html_coops, 'html.parser')
                    cartes_offres = soup.find_all(class_="exp-card")
                    
                    meilleurs_prix_detectes = {}
                    compteur_offres = 0

                    for carte in cartes_offres:
                        cat_brute = carte.get("data-category")
                        if cat_brute in liaison_categories:
                            cle_db = liaison_categories[cat_brute]
                            
                            # Extraction du tarif de l'offre (Ex: "13 € / tonne" ou "71 € / unité")
                            title_span = carte.find(class_="exp-title")
                            if title_span:
                                text_prix = title_span.text
                                match_prix = re.search(r"(\d[\d\s]*)\s*€", text_prix)
                                if match_prix:
                                    prix_offre = float(match_prix.group(1).replace(" ", ""))
                                    compteur_offres += 1
                                    
                                    # On retient le prix le plus bas trouvé pour ce matériau (le meilleur tarif)
                                    if cle_db not in meilleurs_prix_detectes or prix_offre < meilleurs_prix_detectes[cle_db]:
                                        meilleurs_prix_detectes[cle_db] = prix_offre

                    # Injection des valeurs détectées dans la structure de session pour mettre à jour les inputs
                    if meilleurs_prix_detectes:
                        for cle_m, prix_m in meilleurs_prix_detectes.items():
                            st.session_state[f"input_prix_dynamique_{cle_m}"] = prix_m
                        
                        st.success(f"🎉 Analyse terminée ! {compteur_offres} offres analysées. Les prix optimaux ont été pré-remplis dans les champs ci-dessous. Cliquez sur le bouton vert pour valider.")
                    else:
                        st.warning("⚠️ Aucun badge de prix valide n'a pu être extrait. Vérifiez que vous avez copié la bonne page.")
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement analytique du fichier : {e}")
            else:
                st.error("⚠️ La zone de texte est vide.")

    # ==========================================================================
    # --- FORMULAIRE D'ÉDITION CLASSIQUE CONSERVÉ ET SYNCHRONISÉ ---
    # ==========================================================================
    st.markdown("#### ⚙️ Ajustement unitaire manuel des tarifs configurés")
    
    col_m1, col_m2 = st.columns(2)
    liste_cles = list(form_mats.keys())
    milieu = math.ceil(len(liste_cles) / 2)
    
    with col_m1:
        for m_k in liste_cles[:milieu]:
            # Initialisation sécurisée par session_state pour capter les modifications du parseur
            key_state = f"input_prix_dynamique_{m_k}"
            if key_state not in st.session_state:
                st.session_state[key_state] = float(form_mats[m_k])
                
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", min_value=0.0, step=1.0, key=key_state)
            
    with col_m2:
        for m_k in liste_cles[milieu:]:
            key_state = f"input_prix_dynamique_{m_k}"
            if key_state not in st.session_state:
                st.session_state[key_state] = float(form_mats[m_k])
                
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", min_value=0.0, step=1.0, key=key_state)
            
    if st.button("✅ RE-SYNCHRONISER LES PRIX MATÉRIAUX", type="primary", use_container_width=True):
        db.db.collection("configuration_materiaux").document("catalogue").set(form_mats)
        st.cache_data.clear()
        
        # Nettoyage des clés temporaires de la session après l'écriture Firebase
        for m_k in liste_cles:
            if f"input_prix_dynamique_{m_k}" in st.session_state:
                del st.session_state[f"input_prix_dynamique_{m_k}"]
                
        st.toast("🧱 Prix synchronisés avec succès sur Firestore !")
        st.rerun()
