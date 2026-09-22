# Fichier mis à jour avec traçabilité complète : onglets/direction_admin/grille.py
import streamlit as st
import pandas as pd
import database as db
import math
import re

def afficher_onglet_salaires(SALAIRES_DB):
    st.markdown("### 👥 Calculateur de Grille Salariale active")
    
    # 1. Sélections des critères
    c_admin_poste, c_admin_contrat = st.columns(2)
    with c_admin_poste: 
        metier_cible = st.selectbox("Poste à analyser :", ["Conducteur", "Chef", "Ouvrier"])
    with c_admin_contrat: 
        type_contrat_cible = st.selectbox("Type de contrat :", ["CDI (Salaire mensuel)", "CDD (Salaire par jour)"])
    
    # 2. Formulaire d'injection et sauvegarde automatique
    with st.form("form_grille_salariale_cloud"):
        texte_brut = st.text_area("Collez le tableau des recrues ici (Format brut Sim-TP) :", height=120)
        
        # 🎯 BOUTON DE SAUVEGARDE SUR FIRESTORE
        if st.form_submit_button("💾 ENREGISTRER CETTE SÉLECTION SUR FIREBASE", type="primary", use_container_width=True):
            st.info("🔍 Lancement du moteur d'analyse du texte...")
            
            if texte_brut.strip():
                lignes = texte_brut.split("\n")
                compteur_recrues = 0
                
                for idx, ligne in enumerate(lignes):
                    l_clean = ligne.strip()
                    if not l_clean:
                        continue
                    
                    st.caption(f"📋 Analyse de la ligne {idx+1} : `{l_clean}`")
                    
                    try:
                        # 🎯 TENTATIVE 1 : Format standard avec l'âge (Mathilde 44 ans 1 716 € Engager)
                        match_recrue = re.search(r"^([a-zA-Z0-9_\-]+)\s+\d+\s+ans\s+([\d\s]+)\s*€", l_clean, re.IGNORECASE)
                        
                        if match_recrue:
                            pseudo_brut = str(match_recrue.group(1)).strip().capitalize()
                            prix_txt = "".join(c for c in match_recrue.group(2) if c.isdigit())
                            prix_val = float(prix_txt) if prix_txt else 1716.0
                            st.write(f"✅ [Format Standard] Détecté : **{pseudo_brut}** avec un tarif de **{prix_val} €**")
                        else:
                            # 🎯 TENTATIVE 2 : Format brut sans l'âge (Découpage par mots)
                            mots = l_clean.split()
                            if len(mots) >= 2:
                                pseudo_brut = str(mots[0]).strip().capitalize()
                                chiffres_prix = "".join(c for c in l_clean if c.isdigit())
                                prix_val = float(chiffres_prix) if chiffres_prix else 1716.0
                                st.write(f"⚠️ [Format de Secours] Détecté : **{pseudo_brut}** avec un tarif estimé à **{prix_val} €**")
                            else:
                                st.error(f"❌ Impossible de découper la ligne {idx+1}. Trop peu de mots détectés.")
                                continue
                        
                        # 🎯 SÉCURITÉ ANTI-DOUBLON : Nettoyage des fautes d'orthographe à la volée
                        if pseudo_brut in ["Grgo73", "Grrgo73", "Grego"]:
                            st.warning(f"🔄 Redressement automatique du pseudo : `{pseudo_brut}` ➡️ `Grego73`")
                            pseudo_brut = "Grego73"
                        
                        # Clé technique NoSQL pour la table des configurations salariales
                        cle_document_nosql = f"{pseudo_brut} ({metier_cible})"
                        
                        # Écriture directe dans Firebase Firestore
                        st.write(f"🚀 Envoi réseau vers Firestore pour le document : `{cle_document_nosql}`")
                        db.db.collection("configuration_salaires").document(cle_document_nosql).set({
                            "nom_recrue": pseudo_brut,
                            "poste": metier_cible,
                            "contrat": type_contrat_cible,
                            "tarif_unitaire": float(prix_val)
                        })
                        compteur_recrues += 1
                        
                    except Exception as error_ligne:
                        st.error(f"💥 Erreur critique au traitement de la ligne {idx+1} : {error_ligne}")
                
                if compteur_recrues > 0:
                    st.success(f"🟢 Synchronisation de {compteur_recrues} recrue(s) réussie sur Firebase !")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Aucune recrue n'a pu être enregistrée. Vérifiez le format de votre texte.")
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
        st.error(f"⚠️ Erreur d'affichage du tableau général : {e}")
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
