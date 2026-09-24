# Fichier 100% épuré sans dictionnaire : onglets/direction_admin/flotte.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_flotte():
    st.markdown("### 📊 Administration et Analyse de Rentabilité de la Flotte")
    
    with st.form("form_parseur_html_flotte_direct"):
        texte_html_brut = st.text_area("Collez le code HTML brut de Sim-TP ici :", height=120)
        
        if st.form_submit_button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True):
            if texte_html_brut.strip():
                modals_machines = texte_html_brut.split('id="modal-materiel-')
                compteur = 0
                
                for bloc_html in modals_machines:
                    if not bloc_html.strip(): 
                        continue
                    
                    # Extraction du nom, du niveau et du prix
                    match_nom = re.search(r"<h5>Voir (?:le|la)\s+([^<]+)</h5>", bloc_html, re.IGNORECASE)
                    match_niveau = re.search(r"<li>Niveau\s+(\d+)\s*:", bloc_html, re.IGNORECASE)
                    match_prix = re.search(r"Prix\s*:\s*([\d\s]+)\s*euros", bloc_html, re.IGNORECASE)
                    
                    if match_nom and match_niveau and match_prix:
                        # 🎯 ON PASSE TOUT EN MAJUSCULE SUR LA PREMIÈRE LETTRE DIRECTEMENT
                        nom_officiel = match_nom.group(1).strip().capitalize()
                        niveau_machine = f"N{match_niveau.group(1).strip()}"
                        prix_val = float("".join(c for c in match_prix.group(1) if c.isdigit()))
                        
                        # Création de la clé Firestore (Ex: "Pelleteuses (N2)")
                        cle_document_nosql = f"{nom_officiel} ({niveau_machine})"
                        
                        db.db.collection("configuration_engins_officiels").document(cle_document_nosql).set({
                            "nom_brut": nom_officiel,
                            "niveau": niveau_machine,
                            "tarif_location_jour": float(prix_val)
                        })
                        compteur += 1
                        
                st.cache_data.clear()
                st.success(f"🚀 {compteur} machine(s) enregistrée(s) proprement avec une Majuscule sur Firebase !")
                st.rerun()
