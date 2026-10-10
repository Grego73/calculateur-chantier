import streamlit as st
import database as db
import math
from bs4 import BeautifulSoup
import re

def afficher_onglet_materiaux(MATERIAUX_DB):
    st.markdown("### 🧱 Configuration & Injection Globale du Marché NoSQL")
    
    liaison_categories = {
        "sable": {"nom": "Sable", "unite": "tonne", "type": "vrac"},
        "terre": {"nom": "Terre", "unite": "tonne", "type": "vrac"},
        "enrobe": {"nom": "Enrobé", "unite": "tonne", "type": "vrac"},
        "beton": {"nom": "Béton", "unite": "tonne", "type": "vrac"},
        "tuyaux": {"nom": "Tuyaux", "unite": "u", "type": "structure"},
        "tuyaux_assainissement": {"nom": "Canalisations", "unite": "u", "type": "structure"},
        "armature": {"nom": "Armature", "unite": "u", "type": "structure"},
        "toles_ondulees": {"nom": "Tôle", "unite": "u", "type": "structure"},
        "poutres_acier": {"nom": "Poutres", "unite": "u", "type": "structure"},
        "panneaux": {"nom": "Panneaux", "unite": "u", "type": "structure"}
    }

    form_mats = dict(MATERIAUX_DB)
    liste_cles = list(form_mats.keys())

    with st.expander("📥 IMPORTER LE HTML DU MARCHÉ (SAUVEGARDE & CONFIGURATION GENERALE)", expanded=True):
        st.write("Collez ici le code source HTML de la page 'Acheter des matériaux' pour mettre à jour la page Marché et configurer le calculateur.")
        html_coops = st.text_area("Code source HTML du marché :", height=130, key="textarea_admin_global_injector")
        
        if st.button("⚡ SYNCHRONISER L'INTÉGRALITÉ DU MARCHÉ SUR FIREBASE", type="primary", use_container_width=True):
            if html_coops.strip():
                try:
                    soup = BeautifulSoup(html_coops, 'html.parser')
                    cartes_offres = soup.find_all(class_="exp-card")
                    
                    # 1. Purge complète de l'ancien marché public
                    docs_anciens = db.db.collection("offres_cooperatives").stream()
                    for d_old in docs_anciens:
                        d_old.reference.delete()

                    meilleurs_prix_detectes = {}
                    compteur_offres = 0

                    # 2. Scan et enregistrement de CHAQUE offre individuelle en base
                    for idx, carte in enumerate(cartes_offres):
                        cat_brute = carte.get("data-category")
                        if cat_brute in liaison_categories:
                            config = liaison_categories[cat_brute]
                            cle_db = config["nom"]
                            
                            title_span = carte.find(class_="exp-title")
                            prix_offre = 0.0
                            if title_span:
                                match_prix = re.search(r"(\d[\d\s]*)\s*€", title_span.text)
                                if match_prix:
                                    prix_offre = float(match_prix.group(1).replace(" ", ""))

                            form_body = carte.find(class_="exp-body")
                            if form_body:
                                p_elements = form_body.find_all('p')
                                nom_coop = "Système / Inconnu"
                                quantite_dispo = "illimité"
                                
                                # 🎯 REPAIR DU BUG DE MULTIPLE PARAGRAPHES (Extraction par Index)
                                if len(p_elements) >= 2:
                                    nom_coop = p_elements[0].text.strip()
                                    txt_qte = p_elements[1].text.lower()
                                    
                                    if "illimite" not in txt_qte:
                                        match_qte = re.search(r"(\d[\d\s]*)", txt_qte)
                                        if match_qte:
                                            quantite_dispo = f"{int(match_qte.group(1).replace(' ', ''))} {config['unite']}s dispos"

                                # Enregistrement de l'offre brute pour la page publique
                                id_unique_offre = f"offre_{idx:03d}_{cat_brute}_{nom_coop.lower().replace(' ', '_')}"
                                db.db.collection("offres_cooperatives").document(id_unique_offre).set({
                                    "materiau": config["nom"],
                                    "type_logistique": config["type"],
                                    "unite": config["unite"],
                                    "cooperative": nom_coop,
                                    "prix_unitaire": prix_offre,
                                    "quantite_dispo": quantite_dispo
                                })
                                compteur_offres += 1

                                # Calcul du prix le plus bas pour l'onglet "Ajouter Chantier"
                                if cle_db not in meilleurs_prix_detectes or prix_offre < meilleurs_prix_detectes[cle_db]:
                                    meilleurs_prix_detectes[cle_db] = prix_offre

                    if meilleurs_prix_detectes:
                        # On injecte les meilleurs prix dans le catalogue de calcul
                        for cle_m, prix_m in meilleurs_prix_detectes.items():
                            form_mats[cle_m] = prix_m
                        
                        # Enregistrement du catalogue de calcul
                        db.db.collection("configuration_materiaux").document("catalogue").set(form_mats)
                        
                        st.cache_data.clear()
                        st.success(f"🟢 Marché mis à jour ! {compteur_offres} offres poussées sur le Cloud Firebase. Le calculateur a retenu les prix optimaux.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.warning("⚠️ Aucun prix valide détecté.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'enregistrement NoSQL : {e}")
            else:
                st.error("⚠️ Veuillez coller le code HTML.")

    # ==========================================================================
    # --- AFFICHAGE SIMPLE DES TARIFS EN BASE ---
    # ==========================================================================
    st.markdown("#### 📋 Prix actuellement appliqués sur le Calculateur")
    col_m1, col_m2 = st.columns(2)
    milieu = math.ceil(len(liste_cles) / 2)
    with col_m1:
        for m_k in liste_cles[:milieu]:
            st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), disabled=True)
    with col_m2:
        for m_k in liste_cles[milieu:]:
            st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), disabled=True)
