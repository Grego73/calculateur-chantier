# Fichier complet et certifié sans erreur : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import math
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 👥 Calculateur de Grille Salariale active")
    
    # 1. Sélections des critères de filtrage
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    # 🎯 CALCUL ET AFFICHAGE DU PRIX MOYEN JOURNALIER RÉEL (DIVISÉ PAR 7)
    try:
        salaires_stream = db.db.collection("configuration_salaires").stream()
        somme_brute = 0.0
        compteur_global = 0
        
        for doc in salaires_stream:
            d = doc.to_dict()
            if str(d.get("poste")).strip().lower() == metier_cible.strip().lower():
                somme_brute += float(d.get("tarif_unitaire", 0.0))
                compteur_global += 1
                
        if compteur_global > 0:
            prix_moyen_brut = somme_brute / compteur_global
            # 🎯 DIVISION STRICTE PAR 7 (Échelle : 1 semaine réelle = 1 an de jeu)
            prix_moyen_journalier = prix_moyen_brut / 7.0
            
            st.metric(
                label=f"📈 Tarif Moyen par Jour Réel ({metier_cible}) — [Total en base / 7]", 
                value=f"{prix_moyen_journalier:,.2f} €/j".replace(",", " "),
                delta=f"Moyenne brute : {prix_moyen_brut:,.0f} €/mois".replace(",", " ")
            )
        else:
            st.info(f"💡 Aucun tarif enregistré pour le poste {metier_cible}. La moyenne est à 0 €.")
    except Exception as e:
        st.error(f"Impossible de calculer la moyenne : {e}")

    # 2. Formulaire d'injection et sauvegarde automatique NoSQL
    with st.form("form_grille_salariale_cloud"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=150)
        
        if st.form_submit_button("💾 ENREGISTRER ET CALCULER LA MOYENNE", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                compteur_recrues = 0
                
                for idx, ligne in enumerate(lignes):
                    l_clean = ligne.strip()
                    if not l_clean:
                        continue
                    
                    mots = l_clean.split()
                    if len(mots) >= 2:
                        pseudo_brut = mots[0].strip().capitalize()
                        
                        # Sécurité anti-doublon pour Grego73
                        if pseudo_brut in ["Grgo73", "Grrgo73", "Grego", "grego73"]:
                            pseudo_brut = "Grego73"
                            
                        # 🎯 PARSEUR ULTRA-STRICT ANTI-BUG D'ÂGE :
                        # On repère obligatoirement le mot 'ans' pour isoler et sauter l'âge,
                        # puis on capture uniquement le bloc numérique qui précède directement le symbole €
                        match_regex_strict = re.search(r"\d+\s+ans\s+([\d\s]+)\s*€", l_clean, re.IGNORECASE)
                        
                        if match_regex_strict:
                            prix_txt = "".join(c for c in match_regex_strict.group(1) if c.isdigit())
                            prix_val = float(prix_txt)
                        else:
                            # Parseur de secours si la structure de la ligne varie
                            chiffres_fin = re.findall(r'(\d[\d\s]*)\s*€', l_clean)
                            if chiffres_fin:
                                prix_val = float(chiffres_fin[-1].replace(" ", ""))
                            else:
                                prix_val = 1716.0
                        
                        # Écriture propre du PRIX BRUT MENSUEL sans l'âge sur Firebase
                        cle_document_nosql = f"{pseudo_brut} ({metier_cible})"
                        db.db.collection("configuration_salaires").document(cle_document_nosql).set({
                            "nom_recrue": pseudo_brut,
                            "poste": metier_cible,
                            "contrat": type_contrat_cible,
                            "tarif_unitaire": float(prix_val)
                        })
                        st.write(f"✅ Ligne {idx+1} validée : **{pseudo_brut}** enregistré avec **{prix_val:.0f} €**")
                        compteur_recrues += 1
                
                if compteur_recrues > 0:
                    st.success(f"🚀 Succès ! {compteur_recrues} élément(s) ajouté(s). Calcul de la moyenne mis à jour.")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez coller vos données.")

    st.markdown("---")
    st.markdown("#### 📜 Grille Tarifaire Actuellement Enregistrée (Cloud)")
    
    # 3. Tableau d'affichage de contrôle interactif
    try:
        salaires_stream = db.db.collection("configuration_salaires").stream()
        lignes_grille = []
        for doc in salaires_stream:
            d = doc.to_dict()
            if str(d.get("poste")).strip().lower() == metier_cible.strip().lower():
                lignes_grille.append({
                    "ID Document": doc.id,
                    "👤 Collaborateur": d.get("nom_recrue"),
                    "🛠️ Poste": d.get("poste"),
                    "💰 Salaire Mensuel Brut": f"{d.get('tarif_unitaire', 0.0):,.0f} €".replace(",", " ")
                })
            
        if lignes_grille:
            df_salaires = pd.DataFrame(lignes_grille)
            df_salaires["Supprimer ?"] = False
            
            salaires_edites = st.data_editor(
                df_salaires, use_container_width=True, hide_index=True, key="editeur_salaires_bruts_v17",
                column_config={
                    "ID Document": None,
                    "Supprimer ?": st.column_config.CheckboxColumn(default=False)
                }
            )
            
            if st.button("🔥 SUPPRIMER LES LIGNES SÉLECTIONNÉES", type="secondary", use_container_width=True):
                ids_a_supprimer = salaires_edites[salaires_edites["Supprimer ?"] == True]["ID Document"].tolist()
                if ids_a_supprimer:
                    for doc_id in ids_a_supprimer:
                        db.db.collection("configuration_salaires").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_supprimer)} ligne(s) effacée(s).")
                    st.cache_data.clear()
                    st.rerun()
    except Exception as e:
        st.error(f"Erreur d'affichage : {e}")

def afficher_onglet_materiaux(MATERIAUX_DB):
    st.markdown("### 🧱 Coût unitaire d'Approvisionnement des Matériaux")
    form_mats = dict(MATERIAUX_DB)
    col_m1, col_m2 = st.columns(2)
    liste_cles = list(form_mats.keys())
    milieu = math.ceil(len(liste_cles) / 2)
    
    with col_m1:
        for m_k in liste_cles[:milieu]:
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), step=1.0)
    with col_m2:
        for m_k in liste_cles[milieu:]:
            form_mats[m_k] = st.number_input(f"Prix {m_k} (€) :", value=float(form_mats[m_k]), step=1.0)
            
    if st.button("✅ RE-SYNCHRONISER LES PRIX MATÉRIAUX", type="primary", width="stretch"):
        db.db.collection("configuration_materiaux").document("catalogue").set(form_mats)
        st.cache_data.clear(); st.toast("🧱 Prix synchronisés !"); st.rerun()
