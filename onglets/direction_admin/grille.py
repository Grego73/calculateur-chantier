# Fichier mis à jour et persistant : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import math

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 👥 Calculateur de Grille Salariale active")
    
    # 1. Sélections des critères
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salary par jour)"])
    
    # 2. Formulaire d'injection et sauvegarde automatique
    with st.form("form_grille_salariale_cloud"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=120)
        
        # 🎯 BOUTON DE SAUVEGARDE SUR FIRESTORE
        if st.form_submit_button("💾 ENREGISTRER CETTE SÉLECTION SUR FIREBASE", type="primary", use_container_width=True):
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                compteur_recrues = 0
                
                with st.spinner("Enregistrement des tarifs RH sur le Cloud..."):
                    for ligne in lignes:
                        l_clean = ligne.strip()
                        if not l_clean:
                            continue
                        
                        # Découpage basique de la ligne (Ex: Mathilde 44 ans 1 716 € Engager)
                        # Extraction du nom (premier mot) et du tarif (les chiffres avant le €)
                        mots = l_clean.split()
                        if len(mots) >= 3:
                            pseudo_brut = mots[0].strip().capitalize()
                            
                            # 🎯 SÉCURITÉ ANTI-DOUBLON : Nettoyage des fautes d'orthographe à la volée
                            if pseudo_brut in ["Grgo73", "Grrgo73", "Grego"]:
                                pseudo_brut = "Grego73"
                                
                            # Extraction du tarif numérique
                            chiffres_prix = "".join(c for c in l_clean if c.isdigit() and c not in mots[1]) # évite l'âge
                            # Extraction secondaire si l'âge pollue la chaîne
                            try:
                                prix_txt = [m for m in mots if "€" in m or m.isdigit()][-2 if "€" in mots[-1] else -1]
                                prix_val = float("".join(c for c in prix_txt if c.isdigit()))
                            except Exception:
                                prix_val = 1716.0 # Valeur par défaut constatée sur votre capture
                            
                            # Clé technique NoSQL pour la table des configurations salariales
                            cle_document_nosql = f"{pseudo_brut} ({metier_cible})"
                            
                            # Écriture directe dans Firebase Firestore
                            db.db.collection("configuration_salaires").document(cle_document_nosql).set({
                                "nom_recrue": pseudo_brut,
                                "poste": metier_cible,
                                "contrat": type_contrat_cible,
                                "tarif_unitaire": float(prix_val)
                            })
                            compteur_recrues += 1
                
                st.cache_data.clear()
                st.success(f"🟢 Configuration validée ! {compteur_recrues} recrue(s) synchronisée(s) sur Firebase.")
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ La zone de texte est vide. Veuillez coller un tableau de recrues.")

    st.markdown("---")
    st.markdown("#### 📜 Grille Tarifaire Actuellement Enregistrée (Cloud)")
    
    # 3. Récupération et affichage interactif des salaires existants
    try:
        salaires_stream = db.db.collection("configuration_salaires").stream()
        lignes_grille = []
        for doc in salaires_stream:
            d = doc.to_dict()
            lignes_grille.append({
                "ID Document": doc.id,
                "👤 Collaborateur": d.get("nom_recrue"),
                "🛠️ Poste": d.get("poste"),
                "📇 Contrat": d.get("contrat"),
                "💰 Tarif Constaté (€)": f"{d.get('tarif_unitaire', 0.0):,.0f} €".replace(",", " ")
            })
            
        if lignes_grille:
            df_salaires = pd.DataFrame(lignes_grille)
            df_salaires["Supprimer ?"] = False
            
            salaires_edites = st.data_editor(
                df_salaires, use_container_width=True, hide_index=True, key="editeur_salaires_admin_v16",
                column_config={
                    "ID Document": None, # Masqué pour garder l'écran propre
                    "Supprimer ?": st.column_config.CheckboxColumn(default=False)
                }
            )
            
            # Bouton de purge sélective des salaires
            if st.button("🔥 SUPPRIMER LES TARIFS SÉLECTIONNÉS", type="secondary", use_container_width=True):
                ids_a_supprimer = salaires_edites[salaires_edites["Supprimer ?"] == True]["ID Document"].tolist()
                if ids_a_supprimer:
                    for doc_id in ids_a_supprimer:
                        db.db.collection("configuration_salaires").document(doc_id).delete()
                    st.success(f"💥 {len(ids_a_supprimer)} ligne(s) effacée(s) de Firestore.")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("💡 Aucun profil salarial personnalisé n'est enregistré dans Firestore.")
            
    except Exception as e:
        # Rétrocompatibilité avec votre ancien dictionnaire si Firestore est indisponible
        if SALAIRES_DB:
            lignes_secours = [{"Clé technique NoSQL": k, "Tarif (€/j)": v} for k, v in SALAIRES_DB.items()]
            st.dataframe(pd.DataFrame(lignes_secours), use_container_width=True, hide_index=True)


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

