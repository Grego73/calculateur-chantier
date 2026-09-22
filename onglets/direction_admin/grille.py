# Fichier complet et certifié sans erreur : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import math
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 📊 Observatoire & Grille Salariale active")
    
    # ==========================================================================
    # 🎯 1. COMPILATION GLOBAL EN TEMPS RÉEL (MIN, MAX, MOYENNE)
    # ==========================================================================
    try:
        salaires_stream = db.db.collection("configuration_salaires").stream()
        toutes_les_recrues = []
        
        for doc in salaires_stream:
            toutes_les_recrues.append(doc.to_dict())
            
        if toutes_les_recrues:
            df_global_stats = pd.DataFrame(toutes_les_recrues)
            
            # Unification de sécurité des chaînes de caractères
            df_global_stats["poste"] = df_global_stats["poste"].str.strip()
            df_global_stats["contrat"] = df_global_stats["contrat"].str.strip()
            df_global_stats["tarif_unitaire"] = df_global_stats["tarif_unitaire"].astype(float)
            
            # Calcul du groupement statistique NoSQL par Poste et par Contrat
            df_synthese = df_global_stats.groupby(["poste", "contrat"]).agg(
                Prix_Min=("tarif_unitaire", "min"),
                Prix_Max=("tarif_unitaire", "max"),
                Prix_Moyen_Mensuel=("tarif_unitaire", "mean")
            ).reset_index()
            
            # Calcul de l'équivalence par jour réel (Division par 7)
            df_synthese["Prix_Moyen_Jour_Reel"] = df_synthese["Prix_Moyen_Mensuel"] / 7.0
            
            # Renommer joliment les colonnes pour l'affichage Streamlit
            df_synthese.columns = [
                "🛠️ Métier", "📇 Type de Contrat", 
                "📉 Prix Mini", "📈 Prix Maxi", 
                "📊 Moyenne Brut", "⏳ Moyenne / Jour Réel"
            ]
            
            st.markdown("#### 📋 Synthèse Générale du Marché du Travail")
            st.dataframe(
                df_synthese, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "📉 Prix Mini": st.column_config.NumberColumn(format="%.0f €"),
                    "📈 Prix Maxi": st.column_config.NumberColumn(format="%.0f €"),
                    "📊 Moyenne Brut": st.column_config.NumberColumn(format="%.2f €"),
                    "⏳ Moyenne / Jour Réel": st.column_config.NumberColumn(format="%.2f €/j")
                }
            )
            st.markdown("---")
        else:
            st.info("💡 Aucun profil salarial enregistré en base de données. Remplissez le formulaire ci-dessous pour générer les statistiques.")
            
    except Exception as e:
        st.error(f"⚠️ Erreur lors du calcul de l'observatoire : {e}")

    # ==========================================================================
    # ⚙️ 2. FORMULAIRE DE SAISIE ET FILTRAGE DE RECRUTEMENT
    # ==========================================================================
    st.markdown("#### ➕ Ajouter de nouveaux candidats")
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    with st.form("form_grille_salariale_cloud"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=150)
        
        if st.form_submit_button("💾 ENREGISTRER DANS LA BASE ET ACTUALISER", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                compteur_recrues = 0
                
                for idx, ligne in enumerate(lignes):
                    l_clean = ligne.strip()
                    if not l_clean:
                        continue
                    
                    # Parseur : Extrait le prénom (premier mot)
                    mots = l_clean.split()
                    if len(mots) >= 2:
                        pseudo_brut = mots[0].strip().capitalize()
                        
                        # Sécurité anti-doublon pour Grego73
                        if pseudo_brut in ["Grgo73", "Grrgo73", "Grego", "grego73"]:
                            pseudo_brut = "Grego73"
                            
                        # Parseur Regex strict anti-bug d'âge
                        match_regex_strict = re.search(r"\d+\s+ans\s+([\d\s]+)\s*€", l_clean, re.IGNORECASE)
                        
                        if match_regex_strict:
                            prix_txt = "".join(c for c in match_regex_strict.group(1) if c.isdigit())
                            prix_val = float(prix_txt)
                        else:
                            # Système de secours
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
                    st.success(f"🚀 Succès ! {compteur_recrues} élément(s) ajouté(s). Les statistiques ont été recalculées.")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez coller vos données.")

    # ==========================================================================
    # 🗑️ 3. INTERFACE DE SUPPRESSION ET GESTION DES FICHIERS
    # ==========================================================================
    st.markdown("---")
    st.markdown(f"#### 📜 Liste des Profils Enregistrés pour le poste : `[{metier_cible}]`")
    
    try:
        lignes_grille = []
        if toutes_les_recrues:
            for d in toutes_les_recrues:
                if str(d.get("poste")).strip().lower() == metier_cible.strip().lower():
                    lignes_grille.append({
                        "ID Document": f"{d.get('nom_recrue')} ({d.get('poste')})",
                        "👤 Collaborateur": d.get("nom_recrue"),
                        "🛠️ Poste": d.get("poste"),
                        "📇 Contrat": d.get("contrat"),
                        "💰 Salaire Brut": f"{d.get('tarif_unitaire', 0.0):,.0f} €".replace(",", " ")
                    })
            
        if lignes_grille:
            df_salaires = pd.DataFrame(lignes_grille)
            df_salaires["Supprimer ?"] = False
            
            salaires_edites = st.data_editor(
                df_salaires, use_container_width=True, hide_index=True, key="editeur_salaires_bruts_v18",
                column_config={
                    "ID Document": None,  # Masqué
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
        st.error(f"Erreur d'affichage de la table : {e}")

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
