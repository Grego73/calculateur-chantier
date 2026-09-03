# Contenu complet pour : onglets/suivi_interne.py

import streamlit as st
import pandas as pd
import re
from datetime import datetime

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS):
    st.subheader("🔑 Espace Suivi Interne & Analyse des Logs")
    
    # 1. Zone de configuration des Pseudos (1 à 4)
    st.markdown("### 👤 1. Attribution des Pseudos (1 à 4 max)")
    saisie_pseudos_brute = st.text_input(
        "Saisissez les pseudos des joueurs à surveiller (séparés par une virgule) :", 
        value="", 
        placeholder="Ex: greggouze, Grego73, Flo03",
        key="champ_saisie_pseudos_logs"
    )

    # Nettoyage et validation des pseudos
    liste_pseudos = []
    if saisie_pseudos_brute.strip():
        liste_pseudos = [p.strip() for p in saisie_pseudos_brute.split(",") if p.strip()]

    nb_pseudos = len(liste_pseudos)
    pseudos_valides = 0 < nb_pseudos <= 4

    if nb_pseudos == 0:
        st.info("💡 En attente de saisie de pseudo(s).")
    elif nb_pseudos > 4:
        st.error(f"⛔ Limite dépassée : {nb_pseudos} pseudos entrés. Veuillez en garder 4 maximum.")
    else:
        # Affichage des badges de confirmation des joueurs ciblés
        cols_badges = st.columns(4)
        for idx, pseudo in enumerate(liste_pseudos):
            with cols_badges[idx]:
                st.success(f"👤 {pseudo}")

    st.markdown("---")

    # 2. Zone de dépôt des Logs bruts
    st.markdown("### 📋 2. Flux des journaux d'activité de l'entreprise")
    texte_logs_bruts = st.text_area(
        "Collez les lignes de logs bruts ici (les doublons de date/heure/matériau seront automatiquement filtrés) :", 
        value="", 
        height=250, 
        key="zone_texte_flux_logs_btp"
    )

    # 3. Traitement et extraction des données
    if pseudos_valides and texte_logs_bruts.strip():
        lignes = [l.strip() for l in texte_logs_bruts.split("\n") if l.strip()]
        
        donnees_extraites = []
        cles_uniques_detectees = set() # Pour bloquer les doublons absolus
        i = 0
        
        while i < len(lignes):
            ligne_courante = lignes[i]
            
            # Détection de la ligne de date
            if ligne_courante.startswith("Le ") and " à " in ligne_courante:
                date_txt = ligne_courante.replace("Le ", "").strip()
                
                # Vérification de l'existence de la ligne d'action juste après
                if i + 1 < len(lignes):
                    ligne_action = lignes[i+1]
                    
                    # Vérification du pseudo cible
                    pseudo_trouve = None
                    for ps in liste_pseudos:
                        if ligne_action.lower().startswith(ps.lower()):
                            pseudo_trouve = ps
                            break
                    
                    if pseudo_trouve:
                        # Extraction du matériau à la fin de la phrase
                        partie_materiau = "Inconnu"
                        if " de " in ligne_action.lower():
                            partie_materiau = ligne_action.lower().split(" de ")[-1].strip().capitalize()
                        
                        # CRÉATION DE LA CLÉ ANTI-DOUBLON (Date + Pseudo + Matériau)
                        cle_unique = (date_txt, pseudo_trouve.lower(), partie_materiau.lower())
                        
                        if cle_unique not in cles_uniques_detectees:
                            cles_uniques_detectees.add(cle_unique)
                            
                            # Recherche du volume (tonnes ou unités)
                            match_quantite = re.search(r"acheté\s+(\d+)\s+(tonnes|unités)", ligne_action, re.IGNORECASE)
                            quantite = int(match_quantite.group(1)) if match_quantite else 0
                            
                            donnees_extraites.append({
                                "Date & Heure": date_txt,
                                "Pseudo": pseudo_trouve,
                                "Action": "Achat Matériaux",
                                "Quantité": quantite,
                                "Matériau": partie_materiau
                            })
                    
                    i += 2  # Avancer de deux lignes (Date + Action traitées)
                    continue
            i += 1

        # 4. Rendu de l'interface graphique
        if donnees_extraites:
            df_logs_joueurs = pd.DataFrame(donnees_extraites)
            
            # --- AJOUT DU RÉCAPITULATIF DE LA DERNIÈRE ENTRÉE EN DATE ---
            # Conversion temporaire pour trier fidèlement par vraie date chronologique
            def extraire_date_objet(txt):
                try:
                    return datetime.strptime(txt, "%d/%m/%Y à %H:%M")
                except Exception:
                    return datetime.min

            df_logs_joueurs["_date_obj"] = df_logs_joueurs["Date & Heure"].apply(extraire_date_objet)
            derniere_entree = df_logs_joueurs.loc[df_logs_joueurs["_date_obj"].idxmax()]
            df_logs_joueurs = df_logs_joueurs.drop(columns=["_date_obj"]) # Nettoyage de la colonne technique

            st.markdown("### 🔔 Dernier événement en date détecté")
            st.info(
                f"⏱️ **{derniere_entree['Date & Heure']}** — "
                f"👤 **{derniere_entree['Pseudo']}** a effectué un achat de "
                f"📦 **{derniere_entree['Quantité']}** de **{derniere_entree['Matériau']}**."
            )

            # 5. Affichage du Tableau Nettoyé des résultats
            st.markdown(f"### 📊 3. Tableau de traçabilité épuré ({len(df_logs_joueurs)} actions uniques)")
            st.dataframe(
                df_logs_joueurs, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Date & Heure": st.column_config.TextColumn("⏱️ Horodatage", width="medium"),
                    "Pseudo": st.column_config.TextColumn("👤 Pseudo", width="small"),
                    "Action": st.column_config.TextColumn("⚙️ Type d'Action"),
                    "Quantité": st.column_config.NumberColumn("🔢 Quantité", format="%d"),
                    "Matériau": st.column_config.TextColumn("🧱 Matériau extrait")
                }
            )
            
            # Résumé des totaux cumulés sans les doublons
            with st.expander("📊 Voir le résumé cumulé des achats réels"):
                df_total = df_logs_joueurs.groupby(["Pseudo", "Matériau"])["Quantité"].sum().reset_index()
                st.table(df_total)
                
        else:
            st.warning("⚠️ Aucune nouvelle action unique n'a été trouvée pour les pseudos renseignés dans ce bloc de logs.")
