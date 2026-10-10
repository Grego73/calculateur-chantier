import streamlit as st
import database as db
from bs4 import BeautifulSoup
import re

def afficher_onglet_marche_actuel():
    st.header("🌍 Observatoire en Direct du Marché des Coopératives")
    st.write(
        "Collez ci-dessous le code HTML de votre page 'Acheter des matériaux' pour mettre à jour "
        "l'intégralité du marché sur la base de données Firebase, ou consultez les offres déjà enregistrées."
    )

    # ==========================================================================
    # --- 🎯 1. INJECTEUR ET ENREGISTREMENT TOTAL DANS FIREBASE ---
    # ==========================================================================
    with st.expander("📥 METTRE À JOUR LA BASE DE DONNÉES CLOUD (HTML SIM-TP)", expanded=False):
        html_marche = st.text_area(
            "Collez le code HTML complet du marché des coopératives :", 
            height=150, 
            placeholder="<!DOCTYPE html> ... </html>", 
            key="text_area_marche_save_database"
        )
        
        if st.button("⚡ TOUT ENREGISTRER DANS LA BASE DE DONNÉES", type="primary", use_container_width=True):
            if html_marche.strip():
                try:
                    soup = BeautifulSoup(html_marche, 'html.parser')
                    
                    liaison_categories = {
                        "sable": {"nom": "Sable", "unite": "tonne", "type": "vrac"},
                        "terre": {"nom": "Terre", "unite": "tonne", "type": "vrac"},
                        "enrobe": {"nom": "Enrobé", "unite": "tonne", "type": "vrac"},
                        "beton": {"nom": "Béton", "unite": "tonne", "type": "vrac"},
                        "tuyaux": {"nom": "Tuyaux d'eau standards", "unite": "u", "type": "structure"},
                        "tuyaux_assainissement": {"nom": "Canalisations eaux usées", "unite": "u", "type": "structure"},
                        "armature": {"nom": "Armature métallique", "unite": "u", "type": "structure"},
                        "toles_ondulees": {"nom": "Plaque de tôle ondulée", "unite": "u", "type": "structure"},
                        "poutres_acier": {"nom": "Poutres en acier", "unite": "u", "type": "structure"},
                        "panneaux": {"nom": "Panneaux de signalisation", "unite": "u", "type": "structure"}
                    }

                    cartes_offres = soup.find_all(class_="exp-card")
                    
                    # Purge préventive de l'ancien marché pour éviter les résidus périmés
                    docs_anciens = db.db.collection("offres_cooperatives").stream()
                    for doc in docs_anciens:
                        doc.reference.delete()

                    compteur_enregistrements = 0

                    for idx, carte in enumerate(cartes_offres):
                        cat_brute = carte.get("data-category")
                        if cat_brute in liaison_categories:
                            config = liaison_categories[cat_brute]
                            
                            # Extraction du prix unitaire
                            title_span = carte.find(class_="exp-title")
                            prix_unitaire = 0.0
                            if title_span:
                                match_prix = re.search(r"(\d[\d\s]*)\s*€", title_span.text)
                                if match_prix:
                                    prix_unitaire = float(match_prix.group(1).replace(" ", ""))

                            # Extraction de la coopérative et des quantités disponibles
                            form_body = carte.find(class_="exp-body")
                            if form_body:
                                p_elements = form_body.find_all('p')
                                nom_coop = "Système / Inconnu"
                                quantite_dispo = "illimité"
                                
                                if len(p_elements) >= 2:
                                    nom_coop = p_elements[0].text.strip()
                                    txt_qte = p_elements[1].text.lower()
                                    
                                    if "illimite" not in txt_qte:
                                        match_qte = re.search(r"(\d[\d\s]*)", txt_qte)
                                        if match_qte:
                                            quantite_dispo = f"{int(match_qte.group(1).replace(' ', ''))} {config['unite']}s dispos"

                                # 💾 ÉCRITURE DOCUMENTAIRE SUR FIRESTORE
                                id_unique_offre = f"offre_{idx:03d}_{cat_brute}_{nom_coop.lower().replace(' ', '_')}"
                                db.db.collection("offres_cooperatives").document(id_unique_offre).set({
                                    "materiau": config["nom"],
                                    "type_logistique": config["type"],
                                    "unite": config["unite"],
                                    "cooperative": nom_coop,
                                    "prix_unitaire": prix_unitaire,
                                    "quantite_dispo": quantite_dispo
                                })
                                compteur_enregistrements += 1

                    st.cache_data.clear()
                    st.success(f"🟢 Synchronisation réussie ! {compteur_enregistrements} offres de coopératives ont été injectées en base Cloud.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'injection en base NoSQL : {e}")
            else:
                st.error("⚠️ La zone de texte est vide.")

    st.markdown("---")

    # ==========================================================================
    # --- 📋 2. CHARGEMENT ET RENDU SYNCHRONISÉ DEPUIS LA BASE DE DONNÉES ---
    # ==========================================================================
    try:
        # Lecture en flux direct depuis la collection Cloud Firestore
        offres_stream = db.db.collection("offres_cooperatives").stream()
        
        # Structure de données pour le classement
        marche_vrac = {}
        marche_structure = {}

        for doc in offres_stream:
            data = doc.to_dict()
            mat = data.get("materiau")
            t_log = data.get("type_logistique")
            
            cle_affichage = f"{int(data.get('prix_unitaire'))} € / {data.get('unite')}"
            if data.get("quantite_dispo") != "illimité":
                cle_affichage += f" *({data.get('quantite_dispo')})*"

            structure_cible = marche_vrac if t_log == "vrac" else marche_structure
            
            if mat not in structure_cible:
                structure_cible[mat] = {}
                
            if cle_affichage not in structure_cible[mat]:
                structure_cible[mat][cle_affichage] = []
                
            structure_cible[mat][cle_affichage].append(data.get("cooperative"))

        # Si la base est peuplée, on affiche les données comme sur la capture d'écran
        if marche_vrac or marche_structure:
            
            # --- RENDU SECTION VRAC ---
            st.markdown("### 🧱 Matériaux en vrac (Tonne)")
            for mat_nom, offres in marche_vrac.items():
                st.markdown(f"**• {mat_nom}**")
                for desc_prix, coops in offres.items():
                    liste_coops_txt = " / ".join(coops)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◦ **{liste_coops_txt} :** {desc_prix}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- RENDU SECTION STRUCTURE ---
            st.markdown("### ⚙️ Éléments de structure & Réseaux (Unité)")
            for mat_nom, offres in marche_structure.items():
                st.markdown(f"**• {mat_nom}**")
                for desc_prix, coops in offres.items():
                    liste_coops_txt = " / ".join(coops)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◦ **{liste_coops_txt} :** {desc_prix}")
        else:
            st.info("💡 L'historique du marché est vide. Dépliez le panneau ci-dessus pour y injecter le code HTML de votre jeu.")

    except Exception as e:
        st.error(f"❌ Impossible de charger le marché depuis la base de données : {e}")
