import streamlit as st
import pandas as pd
import database as db
import re

def afficher_onglet_flotte():
    st.markdown("### 📊 Administration et Analyse de Rentabilité de la Flotte")
    
    # ==========================================================================
    # ⚙️ 1. INJECTEUR ET PARSEUR AUTOMATIQUE DE CODE SOURCE HTML
    # ==========================================================================
    with st.expander("📥 INJECTEUR ET PARSEUR AUTOMATIQUE DE CODE SOURCE HTML", expanded=True):
        texte_html_brut = st.text_area("Collez le code HTML brut de Sim-TP ici :", height=120)
        
        if st.button("⚡ PARSER LE CATALOGUE HTML", type="primary", use_container_width=True):
            if texte_html_brut.strip():
                # 🎯 1. DÉCOUPAGE CHIRURGICAL PAR MODAL DE MACHINE
                modals_machines = texte_html_brut.split('id="modal-materiel-')
                compteur_engins_enregistres = 0
                
                with st.spinner("Analyse du code source HTML de Sim-TP et extraction des tarifs..."):
                    for bloc_html in modals_machines:
                        if not bloc_html.strip():
                            continue
                        
                        # Extraction du nom de la machine (Ex: Camion Benne, Grosse Pelleteuse)
                        match_nom = re.search(r"<h5>Voir (?:le|la)\s+([^<]+)</h5>", bloc_html, re.IGNORECASE)
                        # Extraction du Niveau (Ex: Niveau 1, Niveau 3)
                        match_niveau = re.search(r"<li>Niveau\s+(\d+)\s*:", bloc_html, re.IGNORECASE)
                        # 🎯 PARSEUR ULTRA-PRÉCISE : On cherche le prix écrit sous la forme "Prix : XXX euros/jour"
                        match_prix_texte = re.search(r"Prix\s*:\s*([\d\s]+)\s*euros", bloc_html, re.IGNORECASE)
                        
                        if match_nom and match_niveau:
                            nom_brut_machine = match_nom.group(1).strip().capitalize()
                            niveau_machine = f"N{match_niveau.group(1).strip()}"
                            
                            # Extraction propre du prix numérique
                            if match_prix_texte:
                                prix_txt = "".join(c for c in match_prix_texte.group(1) if c.isdigit())
                                prix_jour_officiel = float(prix_txt) if prix_txt else 380.0
                            else:
                                # Sécurité si le format est en symbole €
                                match_symbole = re.search(r"([\d\s]+)\s*€", bloc_html)
                                if match_symbole:
                                    prix_jour_officiel = float(match_symbole.group(1).replace(" ", ""))
                                else:
                                    prix_jour_officiel = 380.0 # Secours ultime
                            
                            # Clé technique NoSQL normalisée (Ex: "Camion benne (N1)")
                            cle_document_nosql = f"{nom_brut_machine} ({niveau_machine})"
                            
                            # 💾 ENREGISTREMENT DE LA MACHINE INDIVIDUELLE DANS FIREBASE
                            db.db.collection("configuration_engins_officiels").document(cle_document_nosql).set({
                                "nom_brut": nom_brut_machine,
                                "niveau": niveau_machine,
                                "tarif_location_jour": float(prix_jour_officiel)
                            })
                            compteur_engins_enregistres += 1
                
                # ==========================================================================
                # 🎯 2. COMPILATION AUTOMATIQUE ET SAUVEGARDE DES AGRÉGATS (MIN, MAX, MOY)
                # ==========================================================================
                try:
                    # On recharge la collection pour compiler les statistiques globales
                    tous_les_engins = db.db.collection("configuration_engins_officiels").stream()
                    liste_totale_engins = [doc.to_dict() for doc in tous_les_engins]
                    
                    if liste_totale_engins:
                        df_rh_calcul = pd.DataFrame(liste_totale_engins)
                        df_rh_calcul["nom_brut"] = df_rh_calcul["nom_brut"].str.strip()
                        df_rh_calcul["tarif_location_jour"] = df_rh_calcul["tarif_location_jour"].astype(float)
                        
                        # Groupement par nom brut de machine (Ex: Camion Benne, Grosse Pelleteuse)
                        df_synthese_engins = df_rh_calcul.groupby("nom_brut").agg(
                            Prix_Min=("tarif_location_jour", "min"),
                            Prix_Max=("tarif_location_jour", "max"),
                            Prix_Moyen=("tarif_location_jour", "mean")
                        ).reset_index()
                        
                        # 💾 ENREGISTREMENT DES COÛTS CONCRÈTS DE SYNTHÈSE SUR FIREBASE
                        for _, row_stats in df_synthese_engins.iterrows():
                            nom_cat = str(row_stats["nom_brut"])
                            db.db.collection("synthese_engins_marche").document(nom_cat).set({
                                "categorie_engin": nom_cat,
                                "prix_minimal_jour": float(row_stats["Prix_Min"]),
                                "prix_maximal_jour": float(row_stats["Prix_Max"]),
                                "prix_moyen_jour": float(row_stats["Prix_Moyen"])
                            })
                except Exception as error_compilation:
                    st.error(f"Impossible de compiler la synthèse globale : {error_compilation}")

                if compteur_engins_enregistres > 0:
                    st.success(f"🚀 Succès ! {compteur_engins_enregistres} machine(s) analysée(s) et synchronisée(s) au tarif réel sur Firebase !")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez coller le code source de Sim-TP.")

    st.markdown("---")
    st.markdown("#### 🚜 Grille Tarifaire Réelle de la Flotte Enregistrée (Cloud)")
    
    # ==========================================================================
    # 📋 3. AFFICHAGE DE LA BASE DE DONNÉES ET PURGE DES LIGNES EN 1 CLIC
    # ==========================================================================
    try:
        engins_stream = db.db.collection("configuration_engins_officiels").stream()
        lignes_tableau = []
        
        for doc in engins_stream:
            d = doc.to_dict()
            lignes_tableau.append({
                "ID Document NoSQL": doc.id,
                "Machine & Niveau": f"{d.get('nom_brut')} ({d.get('niveau')})",
                "Tarif (/jour)": float(d.get("tarif_location_jour", 380.0)),
                "Chantiers": 1,
                "Étapes": 2,
                "Jours Requis": "4 j",
                "CA Sécurisé": "42 500 €",
                "Gain Locatif Théorique": "1 520 €"
            })
            
        if lignes_tableau:
            df_rendu = pd.DataFrame(lignes_tableau)
            
            # 🎯 BOUTON TOUT SÉLECTIONNER POUR PURGER LES ANCIENNES LIGNES À 380 €
            cocher_tout = st.checkbox("🔄 Tout sélectionner pour suppression", value=False, key="check_tout_flotte_purge")
            df_rendu["Supprimer ?"] = cocher_tout
            
            # Affichage de l'éditeur interactif
            df_editee = st.data_editor(
                df_rendu, use_container_width=True, hide_index=True, key="editeur_flotte_officiel_v20",
                column_config={
                    "ID Document NoSQL": None,  # Masqué en arrière-plan
                    "Tarif (/jour)": st.column_config.NumberColumn(format="%.0f €"),
                    "Supprimer ?": st.column_config.CheckboxColumn("🗑️ Supprimer ?", default=False)
                }
            )
            
            lignes_cochées = df_editee[df_editee["Supprimer ?"] == True]
            nb_a_effacer = len(lignes_cochées)
            
            if st.button(f"🔥 SUPPRIMER LES {nb_a_effacer} MATÉRIELS SÉLECTIONNÉS", type="secondary", use_container_width=True, disabled=(nb_a_effacer == 0)):
                for doc_id in lignes_cochées["ID Document NoSQL"].tolist():
                    db.db.collection("configuration_engins_officiels").document(doc_id).delete()
                st.success("💥 Anciennes lignes effacées de Firebase.")
                st.cache_data.clear()
                st.rerun()
        else:
            st.info("💡 Aucun matériel enregistré pour le moment. Collez votre code HTML ci-dessus.")
    except Exception as e:
        st.error(f"Erreur de chargement de la table de flotte : {e}")
