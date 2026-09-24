# Fichier : onglets/direction_admin/flotte.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_flotte():
    st.markdown("### 📊 Administration et Analyse de Rentabilité de la Flotte")
    
    with st.form("form_parseur_html_flotte_singulier_strict"):
        texte_html_brut = st.text_area("Collez le code HTML brut de Sim-TP ici :", height=120)
        
        if st.form_submit_button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True):
            if texte_html_brut.strip():
                modals_machines = texte_html_brut.split('id="modal-materiel-')
                compteur = 0
                
                # Table de correspondance de sécurité ramenée au SINGULIER CAPITALIZE
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
                
                for bloc_html in modals_machines:
                    if not bloc_html.strip(): continue
                    
                    match_nom = re.search(r"<h5>Voir (?:le|la)\s+([^<]+)</h5>", bloc_html, re.IGNORECASE)
                    match_niveau = re.search(r"<li>Niveau\s+(\d+)\s*:", bloc_html, re.IGNORECASE)
                    match_prix = re.search(r"Prix\s*:\s*([\d\s]+)\s*euros", bloc_html, re.IGNORECASE)
                    
                    if match_nom and match_niveau and match_prix:
                        nom_brut_jeu = match_nom.group(1).strip().lower()
                        niveau_machine = f"N{match_niveau.group(1).strip()}"
                        prix_val = float("".join(c for c in match_prix.group(1) if c.isdigit()))
                        
                        nom_singulier_officiel = dictionnaire_singulier.get(nom_brut_jeu, match_nom.group(1).strip().capitalize())
                        
                        # ID Document Firestore au singulier : "Pelleteuse (N1)"
                        cle_document_nosql = f"{nom_singulier_officiel} ({niveau_machine})"
                        
                        # Enregistrement à la racine dans la collection "engins"
                        db.db.collection("engins").document(cle_document_nosql).set({
                            "nom_brut": nom_singulier_officiel,
                            "niveau": niveau_machine,
                            "tarif_location_jour": float(prix_val)
                        })
                        compteur += 1
                        
                st.cache_data.clear()
                st.success(f"🚀 {compteur} machine(s) enregistrée(s) au singulier strict dans la collection `engins` !")
                st.rerun()
