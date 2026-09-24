# Fichier corrigé et certifié fonctionnel : onglets/direction_admin/flotte.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_flotte():
    st.markdown("### 📊 Administration et Analyse de Rentabilité de la Flotte")
    
    # 🎯 CORRECTION : On utilise un expander simple à la place du formulaire bloquant st.form
    with st.expander("📥 INJECTEUR ET PARSEUR AUTOMATIQUE DE CATALOGUE", expanded=True):
        texte_html_brut = st.text_area("Collez le code HTML brut de Sim-TP ici :", height=120, key="input_html_flotte_unique")
        
        # Utilisez un bouton standard (sans form_submit) pour libérer l'écriture Firebase
        if st.button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True, key="btn_action_parse_flotte"):
            if texte_html_brut.strip():
                modals_machines = texte_html_brut.split('id="modal-materiel-')
                compteur = 0
                
                # Table de correspondance de sécurité ramenée au SINGULIER avec première lettre en Majuscule
                dictionnaire_singulier = {
                    "camions benne": "Camion benne",
                    "camion benne": "Camion benne",
                    "pelleteuses": "Pelleteuse",
                    "pelleteuse": "Pelleteuse",
                    "petite pelleteuse": "Pelleteuse",
                    "grosse pelleteuse": "Pelleteuse",
                    "mini-pelle": "Pelleteuse",
                    "compacteurs de sol": "Compacteur de sol",
                    "compacteur de sol": "Compacteur de sol",
                    "compacteur pour enrobé": "Compacteur d'enrobé",
                    "finisseur": "Finisseur",
                    "les finisseurs": "Finisseur",
                    "camion béton malaxeur": "Camion malaxeur",
                    "camions béton malaxeur": "Camion malaxeur",
                    "camion pompe à béton": "Camion malaxeur",
                    "chargeuse compacte": "Chargeuse compacte",
                    "chargeuse": "Chargeuse",
                    "chargeur téléscopique": "Chargeur téléscopique",
                    "niveleuse": "Niveleuse",
                    "fraiseuse": "Fraiseuse"
                }
                
                with st.spinner("Analyse du HTML et synchronisation Cloud en cours..."):
                    for bloc_html in modals_machines:
                        if not bloc_html.strip(): 
                            continue
                        
                        # Extraction du nom, du niveau et du prix
                        match_nom = re.search(r"<h5>Voir (?:le|la)\s+([^<]+)</h5>", bloc_html, re.IGNORECASE)
                        match_niveau = re.search(r"<li>Niveau\s+(\d+)\s*:", bloc_html, re.IGNORECASE)
                        match_prix = re.search(r"Prix\s*:\s*([\d\s]+)\s*euros", bloc_html, re.IGNORECASE)
                        
                        if match_nom and match_niveau and match_prix:
                            nom_brut_jeu = match_nom.group(1).strip().lower()
                            niveau_machine = f"N{match_niveau.group(1).strip()}"
                            prix_val = float("".join(c for c in match_prix.group(1) if c.isdigit()))
                            
                            nom_singulier_officiel = dictionnaire_singulier.get(nom_brut_jeu, match_nom.group(1).strip().capitalize())
                            
                            # ID Document Firestore au singulier conforme à vos exigences : "Pelleteuse (N1)"
                            cle_document_nosql = f"{nom_singulier_officiel} ({niveau_machine})"
                            
                            # 💾 ENREGISTREMENT À LA RACINE DANS LA COLLECTION LÉGALE "engins"
                            db.db.collection("engins").document(cle_document_nosql).set({
                                "nom_brut": nom_singulier_officiel,
                                "niveau": niveau_machine,
                                "tarif_location_jour": float(prix_val)
                            })
                            compteur += 1
                
                if compteur > 0:
                    st.success(f"🚀 Succès ! {compteur} machine(s) enregistrée(s) au singulier strict dans la collection `engins` !")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("⚠️ Aucun modèle d'engin valide n'a pu être extrait du code collé. Vérifiez le texte source.")
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez y coller le code source de Sim-TP.")

    st.markdown("---")
    st.markdown("#### 🚜 Grille des tarifs enregistrés en Base de Données")
    
    # Affichage en direct du contenu de la collection pour valider l'enregistrement
    try:
        engins_stream = db.db.collection("engins").stream()
        lignes_tableau = []
        for doc in engins_stream:
            d = doc.to_dict()
            lignes_tableau.append({
                "Engin": doc.id,
                "Tarif journalier": f"{d.get('tarif_location_jour', 380):,.0f} €"
            })
            
        if lignes_tableau:
            st.dataframe(pd.DataFrame(lignes_tableau), use_container_width=True, hide_index=True)
        else:
            st.info("💡 La collection `engins` est actuellement vide sur Firebase. Collez un code HTML valide ci-dessus pour l'alimenter.")
    except Exception as e:
        st.error(f"Erreur d'affichage du catalogue : {e}")
