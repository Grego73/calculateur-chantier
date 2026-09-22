# Fichier complet : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 📊 Observatoire & Grille Salariale active")
    
    # ==========================================================================
    # 🎯 1. COMPILATION ET AFFICHAGE DES STATISTIQUES GLOBALES EN TEMPS RÉEL
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
            
            # Renommer les colonnes pour l'affichage Streamlit
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
    # ⚙️ 2. FORMULAIRE DE SAISIE, PARSTAGE ET ENREGISTREMENT DES AGRÉGATS
    # ==========================================================================
    st.markdown("#### ➕ Ajouter de nouveaux candidats")
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    with st.form("form_grille_salariale_cloud"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=150)
        
        if st.form_submit_button("💾 ENREGISTRER DANS LA BASE ET CALCULER LES AGRÉGATS", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                compteur_recrues = 0
                
                with st.spinner("Analyse et synchronisation NoSQL en cours..."):
                    for idx, ligne in enumerate(lignes):
                        l_clean = ligne.strip()
                        
                        # On ignore les lignes vides et la ligne d'en-tête du tableau
                        if not l_clean or l_clean.lower().startswith("prénom") or "salaire" in l_clean.lower():
                            continue
                        
                        mots = l_clean.split()
                        if len(mots) >= 2:
                            # 1. Extraction propre du prénom (premier élément de la ligne)
                            pseudo_brut = str(mots[0]).strip().capitalize()
                            
                            # Sécurité anti-doublon pour Grego73
                            if pseudo_brut in ["Grgo73", "Grrgo73", "Grego", "grego73"]:
                                pseudo_brut = "Grego73"
                                
                            # 🎯 LA REGEX INFAILLIBLE ANTI-BUG D'ÂGE :
                            # Elle attrape uniquement la chaîne numérique (avec ou sans espaces) placée juste devant le symbole €
                            match_salaire_strict = re.search(r"([\d\s]+)\s*€", l_clean)
                            
                            if match_salaire_strict:
                                # On supprime les espaces internes (ex: "1 712" -> "1712")
                                prix_txt = "".join(c for c in match_salaire_strict.group(1) if c.isdigit())
                                prix_val = float(prix_txt)
                            else:
                                continue # Si on ne trouve pas de prix en euros, on passe à la ligne suivante
                            
                            # 2. Écriture de la recrue individuelle sur Firebase
                            cle_document_nosql = f"{pseudo_brut} ({metier_cible})"
                            db.db.collection("configuration_salaires").document(cle_document_nosql).set({
                                "nom_recrue": pseudo_brut,
                                "poste": metier_cible,
                                "contrat": type_contrat_cible,
                                "tarif_unitaire": float(prix_val)
                            })
                            compteur_recrues += 1

                # ==================================================================
                # 🎯 3. MOTEUR D'ÉCRITURE DES AGRÉGATS (MIN, MAX, MOYENNE) DANS FIREBASE
                # ==================================================================
                try:
                    # On recharge la collection pour intégrer les nouvelles recrues dans le calcul
                    flux_nouveau = db.db.collection("configuration_salaires").stream()
                    recrues_regroupees = [d.to_dict() for d in flux_nouveau]
                    
                    df_calcul = pd.DataFrame(recrues_regroupees)
                    df_filtre = df_calcul[
                        (df_calcul["poste"].str.strip() == metier_cible) & 
                        (df_calcul["contrat"].str.strip() == type_contrat_cible)
                    ]
                    
                    if not df_filtre.empty:
                        tarifs = df_filtre["tarif_unitaire"].astype(float)
                        p_min = float(tarifs.min())
                        p_max = float(tarifs.max())
                        p_moyen = float(tarifs.mean())
                        p_moyen_jour_reel = p_moyen / 7.0
                        
                        # Écriture du document de synthèse dans la collection dédiée
                        cle_synthese_coop = f"{metier_cible}_{type_contrat_cible}"
                        db.db.collection("synthese_grille_tarifaire").document(cle_synthese_coop).set({
                            "poste": metier_cible,
                            "contrat": type_contrat_cible,
                            "prix_minimal": p_min,
                            "prix_maximal": p_max,
                            "prix_moyen_mensuel": p_moyen,
                            "prix_moyen_journalier_7": p_moyen_jour_reel,
                            "derniere_mise_a_jour": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                        })
                        st.write(f"💾 **Agrégats Firebase synchronisés** (`{cle_synthese_coop}`) ➡️ Min: {p_min:.0f}€ | Max: {p_max:.0f}€ | Moy/7: {p_moyen_jour_reel:.2f}€")
                except Exception as ex_stats:
                    st.error(f"Impossible de générer le document de synthèse NoSQL : {ex_stats}")

                if compteur_recrues > 0:
                    st.success(f"🚀 Succès ! {compteur_recrues} recrues enregistrées proprement (sans l'âge) et indicateurs sauvegardés sur Firebase !")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez coller vos données.")

    # ==========================================================================
    # 🗑️ 4. INTERFACE DE SUPPRESSION ET DE CONTRÔLE DES PROFILS
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
                    "ID Document": None,
                    "Supprimer ?": st.column_config.CheckboxColumn(default=False)
                }
            )
            
            if st.button("🔥 SUPPRIMER LES TARIFS SÉLECTIONNÉS", type="secondary", use_container_width=True):
                ids_a_supprimer = salaires_edites[salaires_edites["Supprimer ?"] == True]["ID Document"].tolist()
                if ids_a_supprimer:
                    for doc_id in ids_a_supprimer:
                        db.db.collection("configuration_salaires").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_supprimer)} ligne(s) effacée(s).")
                    st.cache_data.clear()
                    st.rerun()
    except Exception as e:
        st.error(f"Erreur d'affichage de la table : {e}")
