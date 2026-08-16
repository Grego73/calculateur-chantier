import streamlit as st
import pandas as pd
import database as db

def afficher_onglet_direction(SALAIRES_DB, MATERIAUX_DB):
    st.subheader("🔑 Connexion Administrateur Direction")
    mot_de_passe = st.text_input("Veuillez saisir le code d'accès :", type="password")
    
    if mot_de_passe == "adminBTP2026":
        st.success("🔓 Accès accordé au panneau de contrôle.")
        
        df_stats = db.charger_donnees()
        if not df_stats.empty and "Revenus (€)" in df_stats.columns:
            st.markdown("### 🏢 Bilan Général de l'Entreprise (Consolidé Cloud)")
            total_chantiers = len(df_stats)
            somme_revenus = float(df_stats["Revenus (€)"].sum())
            somme_depenses = float(df_stats["Dépenses Totales (€)"].sum())
            somme_benefices = float(df_stats["Bénéfice Net (€)"].sum())
            
            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
            with c_st1: st.metric(label="💼 Chantiers Signés", value=f"{total_chantiers}")
            with c_st2: st.metric(label="💰 Chiffre d'Affaires Cumulé", value=f"{somme_revenus:,.0f}".replace(",", " ") + " €")
            with c_st3: st.metric(label="📉 Dépenses Totales", value=f"{somme_depenses:,.0f}".replace(",", " ") + " €")
            with c_st4: st.metric(label="📈 Résultat Net / Bénéfice", value=f"{somme_benefices:,.0f}".replace(",", " ") + " €")
            
            # --- ZONE DE SÉCURITÉ ET NETTOYAGE CIBLÉ ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🚨 Zone de Danger : Réinitialisation et Nettoyage des Tables"):
                st.warning("Attention : Ces actions suppriment définitivement les données stockées sur Firebase.")
                col_del1, col_del2, col_del3 = st.columns(3)
                with col_del1:
                    if st.button("🗑️ Vider l'Historique des Chantiers", type="secondary", use_container_width=True):
                        docs = db.db.collection("chantiers").stream()
                        for d in docs: d.reference.delete()
                        st.toast("Historique des chantiers supprimé !")
                        st.rerun()
                with col_del2:
                    if st.button("🗑️ Vider les Modèles Préfabriqués", type="secondary", use_container_width=True):
                        docs = db.db.collection("modeles_chantiers").stream()
                        for d in docs: d.reference.delete()
                        st.toast("Catalogue des modèles vidé !")
                        st.rerun()
                with col_del3:
                    if st.button("💥 TOUT RÉINITIALISER", type="primary", use_container_width=True):
                        db.reinitialiser_db()
                        st.rerun()
            st.markdown("---")

        st.markdown("## ⚙️ Administration Suprême des Bases NoSQL")
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
            "🏗️ Saisie Multi-Chantiers en Bloc", "👥 Éditer Grille Salariale", 
            "🧱 Éditer Prix Matériaux", "🚜 Éditer Catalogue Engins", "🗂️ Consulter les Bases Données"
        ])
        
        # --- 4.1 IMPORTATION EN BLOC ---
        with sub_tab1:
            st.markdown("### 📥 Extracteur de Fiches Chantiers Multi-Étapes")
            texte_fiches_brutes = st.text_area("Collez vos fiches de chantiers détaillées ici :", value="", height=350, key="zone_texte_import_unique_fusionne")
            
            if st.button("🏗️ ANALYSER, NETTOYER ET IMPORTER EN BLOC", type="primary"):
                if not texte_fiches_brutes.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    lignes = texte_fiches_brutes.split("\n")
                    chantiers_detectes = {}
                    nom_courant = None
                    
                    for ligne in lignes:
                        l_clean = ligne.strip()
                        if not l_clean: continue
                        
                        if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                            mots = l_clean.split()
                            mots_sans_euro = [m for m in mots if m.lower() not in ["euros", "euro", "€"]]
                            if len(mots_sans_euro) >= 2:
                                p1 = "".join(c for c in mots_sans_euro[-1] if c.isdigit())
                                p2 = "".join(c for c in mots_sans_euro[-2] if c.isdigit()) if len(mots_sans_euro) > 2 else ""
                                try:
                                    prix_ch = float(p2 + p1) if (p2 and p1 and len(p1) == 3) else float(p1)
                                    nom_ch = " ".join(mots_sans_euro[:-2]) if (p2 and p1 and len(p1) == 3) else " ".join(mots_sans_euro[:-1])
                                except ValueError:
                                    prix_ch = 0.0; nom_ch = l_clean
                                
                                nom_courant = nom_ch.strip()
                                if nom_courant not in chantiers_detectes:
                                    chantiers_detectes[nom_courant] = {
                                        "revenus": prix_ch, "jours": 1, "nb_etapes": 1,
                                        "sable": 0.0, "terre": 0.0, "enrobe": 0.0, "armature": 0.0, "tole": 0.0,
                                        "beton": 0.0, "panneaux": 0.0, "tuyaux": 0.0, "canalisations": 0.0, "poutres": 0.0,
                                        "jh_chef": 0.0, "jh_ouvrier": 0.0, "jh_cond": 0.0, "engins_requis": []
                                    }
                            continue

                        if not nom_courant: continue
                        if l_clean.lower().startswith("revenus"):
                            num_part = "".join(c for c in l_clean if c.isdigit())
                            if num_part: chantiers_detectes[nom_courant]["revenus"] = float(num_part)
                        if "nombre d'étapes" in l_clean.lower() or "nb ombre" in l_clean.lower():
                            partie_etape = l_clean.split(":")[-1] if ":" in l_clean else l_clean
                            num_etapes = "".join(c for c in partie_etape.split() if c.isdigit()) if partie_etape.split() else ""
                            if not num_etapes: num_etapes = "".join(c for c in partie_etape if c.isdigit())
                            if num_etapes: chantiers_detectes[nom_courant]["nb_etapes"] = int(num_etapes)
                        if "durée du chantier" in l_clean.lower() or "duree du chantier" in l_clean.lower():
                            partie_droite = l_clean.split(":")[-1] if ":" in l_clean else l_clean
                            mots_jours = partie_droite.split()
                            num_jours = ""
                            for mj in mots_jours:
                                if any(c.isdigit() for c in mj): num_jours = "".join(c for c in mj if c.isdigit()); break
                            if num_jours: chantiers_detectes[nom_courant]["jours"] = int(num_jours)
                        if "surface du chantier" in l_clean.lower():
                            partie_mats = l_clean.split(":")[-1].lower() if ":" in l_clean else l_clean.lower()
                            mots_mats = partie_mats.split()
                            if mots_mats:
                                qte_txt = "".join(c for c in mots_mats if c.isdigit())
                                if not qte_txt: qte_txt = "".join(c for c in partie_mats if c.isdigit())
                                if qte_txt:
                                    qte_val = float(qte_txt); type_mat = " ".join(mots_mats[1:])
                                    if "tuyau" in type_mat or "km" in type_mat: chantiers_detectes[nom_courant]["tuyaux"] = qte_val
                                    elif "panneau" in type_mat: chantiers_detectes[nom_courant]["panneaux"] = qte_val
                                    elif "sable" in type_mat: chantiers_detectes[nom_courant]["sable"] = qte_val
                                    elif "terre" in type_mat: chantiers_detectes[nom_courant]["terre"] = qte_val
                                    elif "enrob" in type_mat: chantiers_detectes[nom_courant]["enrobe"] = qte_val
                                    elif "armat" in type_mat: chantiers_detectes[nom_courant]["armature"] = qte_val
                                    elif "tôle" in type_mat or "tole" in type_mat: chantiers_detectes[nom_courant]["tole"] = qte_val
                                    elif "béton" in type_mat or "beton" in type_mat: chantiers_detectes[nom_courant]["beton"] = qte_val
                                    elif "canal" in type_mat: chantiers_detectes[nom_courant]["canalisations"] = qte_val
                                    elif "poutre" in type_mat: chantiers_detectes[nom_courant]["poutres"] = qte_val

                    compteur_total = 0
                    for name, data in chantiers_detectes.items():
                        if data["jh_chef"] == 0 and data["jh_ouvrier"] == 0:
                            data["jh_chef"] = float(data["jours"]); data["jh_ouvrier"] = float(data["jours"] * 3)
                        if not data["engins_requis"]:
                            for e_num in range(1, data["nb_etapes"] + 1):
                                data["engins_requis"].append({"N° Étape": e_num, "Durée Étape (jours)": max(1, int(data["jours"] / data["nb_etapes"])), "Type d'engin requis": "Pelleteuses" if e_num == 1 else "Camions Benne", "Niveau requis": "N2"})
                        
                        db.db.collection("modeles_chantiers").document(name).set({
                            "nom_modele": name, "revenus": data["revenus"], "jours": data["jours"],
                            "sable": data["sable"], "terre": data["terre"], "enrobe": data["enrobe"], "armature": data["armature"], "tole": data["tole"],
                            "beton": data["beton"], "panneaux": data["panneaux"], "tuyaux": data["tuyaux"], "canalisations": data["canalisations"], "poutres": data["poutres"],
                            "jh_chef": data["jh_chef"], "jh_ouvrier": data["jh_ouvrier"], "jh_cond": data["jh_cond"], "engins_requis": data["engins_requis"]
                        })
                        compteur_total += 1
                    if compteur_total > 0: st.success(f"🟢 {compteur_total} fiche(s) injectée(s) !"); st.rerun()

        # --- 4.2 CONFIGURATION GRILLE SALARIALE AVEC POP-UP DE VALIDATION ET DÉTAIL DES CALCULS ---
        with sub_tab2:
            st.markdown("### 👥 Extracteur et Calculateur de Salaires par Métier")
            st.write("Sélectionnez le poste concerné, puis collez le tableau brut de vos recrues potentielles.")

            metier_cible = st.selectbox(
                "💼 Pour quel poste analysez-vous ces salaires ?",
                ["Conducteur", "Chef", "Ouvrier", "Intérim"]
            )

            texte_recrutement_brut = st.text_area(
                f"Collez le tableau des recrues pour le poste [{metier_cible}] ici :",
                value="",
                height=250,
                key="zone_texte_recrutement_brut",
                placeholder="Betty\t48 ans\t1 622 €\tEngager\nJean-pierre\t45 ans\t1 623 €\tEngager"
            )

            # --- POP-UP DIALOG POUR LE DÉTAIL DES CALCULS DE RECRUTEMENT ---
            @st.dialog("📊 Rapport d'Analyse et de Calcul des Paliers")
            def pop_up_validation_recrutement(salaires, metier):
                st.write(f"Voici le détail de l'analyse textuelle pour le poste de **{metier}** :")
                
                # 1. Calculs statistiques
                s_min = min(salaires)
                s_max = max(salaires)
                s_somme = sum(salaires)
                s_nb = len(salaires)
                s_moyen = s_somme / s_nb

                # 2. Affichage des coulisses du calcul
                st.info(f"🔍 **Données extraites :** L'algorithme a trouvé **{s_nb} salaires valides** dans votre texte brut.")
                
                with st.expander("📄 Voir la liste complète des prix détectés"):
                    st.write(", ".join([f"{s:.0f} €" for s in salaires]))

                st.markdown("### 🧮 Formules et Paliers calculés :")
                st.markdown(f"- **Prix Minimum détecté :** `{s_min:.0f} €`")
                st.markdown(f"- **Prix Maximum détecté :** `{s_max:.0f} €`")
                st.markdown(f"- **Prix Moyen calculé :** `Somme ({s_somme:,.0f} €) / Nombre ({s_nb})` = `{s_moyen:.2f} €`")

                st.write("Voulez-vous écraser la grille actuelle du jeu avec ces nouvelles valeurs sur le cloud ?")

                # Boutons de décision finale
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    if st.button("✅ ENREGISTRER SUR FIREBASE", type="primary", use_container_width=True):
                        # Lecture de la grille pour ne pas effacer les autres métiers
                        grille_actuelle = dict(SALAIRES_DB)
                        
                        # Injection des nouveaux paliers
                        grille_actuelle[f"{metier}_Min"] = float(s_min)
                        grille_actuelle[f"{metier}_Moyen"] = float(round(s_moyen, 2))
                        grille_actuelle[f"{metier}_Max"] = float(s_max)
                        grille_actuelle[metier] = float(round(s_moyen, 2))

                        # Envoi cloud
                        db.db.collection("configuration_salaires").document("grille").set(grille_actuelle)
                        st.toast(f"🚀 Grille mise à jour pour les {metier}s !")
                        st.rerun()
                with c_p2:
                    if st.button("❌ ANNULER", use_container_width=True):
                        st.rerun()

            # --- LE BOUTON PRINCIPAL D'ANALYSE CORRIGÉ ---
            if st.button("📊 ANALYSER LES SALAIRES SOUMIS"):
                if not texte_recrutement_brut.strip():
                    st.error("❌ La zone de texte est vide.")
                else:
                    lignes_recrues = texte_recrutement_brut.split("\n")
                    liste_salaires_extraits = []

                    for ligne in lignes_recrues:
                        l_clean = ligne.strip()
                        if not l_clean or "salaire" in l_clean.lower(): 
                            continue 
                        
                        elements = l_clean.split("\t") if "\t" in l_clean else l_clean.split()
                        
                        # --- STRATÉGIE DE LECTURE DU COMPAGNON DU JEU ---
                        salaire_trouve = None
                        
                        # Étape 1 : On cherche d'abord la case qui contient STRICTEMENT le symbole €
                        for el in elements:
                            if "€" in el:
                                chiffre_net = "".join(c for c in el if c.isdigit())
                                if chiffre_net:
                                    salaire_trouve = float(chiffre_net)
                                    break
                        
                        # Étape 2 : Si pas de €, on cherche de droite à gauche (l'âge est au début, le salaire à la fin)
                        if salaire_trouve is None:
                            for el in reversed(elements):
                                if any(c.isdigit() for c in el) and "an" not in el.lower():
                                    chiffre_net = "".join(c for c in el if c.isdigit())
                                    if chiffre_net:
                                        salaire_trouve = float(chiffre_net)
                                        break
                                        
                        if salaire_trouve is not None:
                            liste_salaires_extraits.append(salaire_trouve)

                    if len(liste_salaires_extraits) > 0:
                        # Si l'extraction fonctionne, on ouvre la boîte de dialogue avec les vrais salaires
                        pop_up_validation_recrutement(liste_salaires_extraits, metier_cible)
                    else:
                        st.error("❌ Aucun montant de salaire valide n'a pu être extrait. Vérifiez le format de votre texte.")

            st.markdown("---")
            st.write("⚙️ **Grille tarifaire enregistrée en base :**")
            st.dataframe(pd.DataFrame(list(SALAIRES_DB.items()), columns=["Poste / Palier", "Montant (€)"]), use_container_width=True, hide_index=True)

        # --- 4.3 CONFIGURATION DES MATÉRIAUX ---
        with sub_tab3:
            st.write("Ajustez le prix unitaire de vos matières premières.")
            mats_edites = st.data_editor(pd.DataFrame(list(MATERIAUX_DB.items()), columns=["materiau", "prix_unitaire"]), use_container_width=True, key="editeur_mats_db", num_rows="fixed")
            if st.button("METTRE À JOUR LE COÛT DES MATÉRIAUX"):
                nouveau_dict = dict(zip(mats_edites["materiau"], mats_edites["prix_unitaire"].astype(float)))
                db.db.collection("configuration_materiaux").document("catalogue").set(nouveau_dict)
                st.success("Tarifs matériaux actualisés !"); st.rerun()

        # --- 4.4 CATALOGUE DE MACHINES ---
        with sub_tab4:
            st.write("Ajoutez ou modifiez vos engins lourds.")
            docs_engins = db.db.collection("catalogue_engins").stream()
            liste_engins = [{"nom_engin": d.id, "type_brut": d.to_dict().get("type_brut", ""), "prix_jour": d.to_dict().get("prix_jour", 0.0)} for d in docs_engins]
            df_engins = pd.DataFrame(liste_engins) if liste_engins else pd.DataFrame(columns=["nom_engin", "type_brut", "prix_jour"])
            
            engins_edites_db = st.data_editor(df_engins, use_container_width=True, key="editeur_engins_db", num_rows="dynamic")
            if st.button("METTRE À JOUR LE CATALOGUE DES ENGINS"):
                old_docs = db.db.collection("catalogue_engins").stream()
                for od in old_docs: od.reference.delete()
                for _, r in engins_edites_db.iterrows():
                    if pd.notnull(r["nom_engin"]) and str(r["nom_engin"]).strip():
                        db.db.collection("catalogue_engins").document(str(r["nom_engin"]).strip()).set({"type_brut": str(r["type_brut"]), "prix_jour": float(r["prix_jour"])})
                st.success("Parc d'engins synchronisé !"); st.rerun()

        # --- 4.5 VISUALISATION EN DIRECT ---
        with sub_tab5:
            st.markdown("### 🗂️ Consultation brute")
            choix_table = st.selectbox("Choisir la table :", ["Modèles de Chantiers Pré-configurés", "Grille Salariale Actuelle", "Prix des Matériaux de base", "Catalogue de Location des Engins"])
            if choix_table == "Modèles de Chantiers Pré-configurés":
                docs = db.db.collection("modeles_chantiers").stream(); res = [d.to_dict() for d in docs]
                if res: st.dataframe(pd.DataFrame(res)[["nom_modele", "revenus", "jours", "jh_chef", "jh_ouvrier", "jh_cond"]], use_container_width=True)
                else: st.info("Aucun modèle.")
            elif choix_table == "Grille Salariale Actuelle": st.json(SALAIRES_DB)
            elif choix_table == "Prix des Matériaux de base": st.json(MATERIAUX_DB)
            elif choix_table == "Catalogue de Location des Engins":
                docs = db.db.collection("catalogue_engins").stream()
                res = [{"Engin Modèle": d.id, "Catégorie": d.to_dict().get("type_brut"), "Prix/j (€)": d.to_dict().get("prix_jour")} for d in docs]
                if res: st.dataframe(pd.DataFrame(res), use_container_width=True)
                else: st.info("Catalogue vide.")
    elif mot_de_passe != "":
        st.error("🔒 Code d'accès incorrect.")
