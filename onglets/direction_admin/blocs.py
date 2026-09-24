# Fichier complet et certifié sans erreur : onglets/direction_admin/blocs.py
import pandas as pd
import streamlit as st
import database as db_module
import re
import math

# Récupération propre du client de base de données Firebase
db_client = db_module.db 

def enregistrer_chantiers_cloud(chantiers_detectes):
    """Moteur d'écriture bloquant et insère simultanément sur les 2 Tables NoSQL"""
    compteur = 0
    for temporary_key, data in chantiers_detectes.items():
        nom_unique_key = f"{data['nom_affiche_propre']} - {int(data['revenus'])}€"
        
        # --- TABLE 1 : Entête du modèle de chantier ---
        doc_chantier_ref = db_client.collection("modeles_chantiers").document(nom_unique_key)
        doc_chantier_ref.set({
            "nom_modele": data["nom_affiche_propre"], 
            "revenus": float(data["revenus"]), 
            "jours_globaux": int(data["jours"]), 
            "heures_globales": int(data["heures"]), 
            "minutes_globales": int(data["minutes"])
        })
        
        # --- TABLE 2 : Sous-collection d'étapes liées (Chaque étape est isolée) ---
        for num_e, step_data in data["etapes_techniques"].items():
            document_etape_id = f"etape_{int(num_e):02d}"
            doc_chantier_ref.collection("etapes").document(document_etape_id).set(step_data)
            
        compteur += 1
        
    db_module.st.cache_data.clear()
    st.success(f"🟢 Extraction et synchronisation de {compteur} chantier(s) réussie sur vos 2 tables cloud !")
    st.balloons()

def afficher_onglet_blocs():
    dict_modeles_cloud = db_module.charger_catalogue_chantiers()
    res_modeles_base = [dict_modeles_cloud[k] for k in dict_modeles_cloud if k != "Choisir un chantier pré-configuré..."]
    total_modeles_base = len(res_modeles_base)

    st.markdown(f"### 📥 Extracteur de Fiches Multi-Étapes Segmentées ({total_modeles_base} modèles en base)")
    texte_fiches_brutes = st.text_area("Zone de saisie des fiches (Format Copier-Coller Direct) :", value="", height=250, key="zone_texte_import_unique_fusionne")
    
    # Prise de taux par défaut de l'Espace Direction pour simuler la rentabilité
    px_cond, px_chef, px_ouvrier = 250.0, 300.0, 210.0
    px_location_machine = 380.0
    
    if texte_fiches_brutes.strip():
        lignes = texte_fiches_brutes.split("\n")
        chantiers_detectes = {}
        nom_courant = None
        etape_courante_num = None
        
        for ligne in lignes:
            l_clean = ligne.strip()
            if not l_clean: 
                continue
            
            # 1. Détection de la ligne d'en-tête (Titre du chantier et revenus)
            if "euros" in l_clean.lower() and not l_clean.lower().startswith("revenus"):
                match_debut = re.search(r"^(.*?)\s+(\d[\d\s]+)\s+euros", l_clean, re.IGNORECASE)
                if match_debut:
                    nom_ch = match_debut.group(1).strip()
                    prix_txt = "".join(c for c in match_debut.group(2) if c.isdigit())
                    prix_ch = float(prix_txt) if prix_txt else 0.0
                else:
                    prix_ch = 0.0
                    nom_ch = l_clean.split("\t")[0].strip()
                    
                nom_courant = f"{nom_ch} - {int(prix_ch)}€"
                etape_courante_num = None
                
                chantiers_detectes[nom_courant] = {
                    "nom_affiche_propre": nom_ch,
                    "revenus": prix_ch, 
                    "jours": 0, "heures": 0, "minutes": 0,
                    "etapes_techniques": {}
                }
                continue

            if not nom_courant: 
                continue
            
            # 2. Sécurité : Capture alternative du CA
            if l_clean.lower().startswith("revenus :"):
                prix_txt = "".join(c for c in l_clean if c.isdigit())
                if prix_txt: 
                    chantiers_detectes[nom_courant]["revenus"] = float(prix_txt)
                continue

            # 3. Décodage de la durée globale du chantier
            if "durée du chantier :" in l_clean.lower() or "duree du chantier :" in l_clean.lower():
                partie_duree = l_clean.split(":")[-1].lower()
                for char in [",", "(", ")", "s", "."]:
                    partie_duree = partie_duree.replace(char, " ")
                
                mots = partie_duree.split()
                for idx_mot, mot in enumerate(mots):
                    if idx_mot > 0:
                        chiffre_txt = "".join(c for c in mots[idx_mot - 1] if c.isdigit())
                        if chiffre_txt:
                            valeur_numerique = int(chiffre_txt)
                            if mot.startswith("jour"):
                                chantiers_detectes[nom_courant]["jours"] = valeur_numerique
                            elif mot.startswith("heure"):
                                chantiers_detectes[nom_courant]["heures"] = valeur_numerique
                            elif mot.startswith("minute"):
                                chantiers_detectes[nom_courant]["minutes"] = valeur_numerique
                continue

            # 4. Ouverture d'une étape technique (Ex: Etape 1 : Terrassement)
            if l_clean.lower().startswith("etape") and ":" in l_clean:
                match_e = re.search(r"etape\s*(\d+)\s*:\s*(.*)", l_clean, re.IGNORECASE)
                if match_e: 
                    etape_courante_num = int(match_e.group(1))
                    nom_etape_txt = match_e.group(2).strip()
                    
                    chantiers_detectes[nom_courant]["etapes_techniques"][etape_courante_num] = {
                        "num_etape": etape_courante_num,
                        "nom_etape": nom_etape_txt,
                        "duree_jours": 1,
                        "jh_cond": 0.0, "jh_chef": 0.0, "jh_ouvrier": 0.0,
                        "materiaux": {},
                        "engins": []
                    }
                continue

            # 5. Extraction des attributs de l'étape active
            if etape_courante_num is not None:
                target_etape = chantiers_detectes[nom_courant]["etapes_techniques"][etape_courante_num]
                
                # Extraction Temps de l'étape
                if "durée de l'étape" in l_clean.lower() or "duree de l'etape" in l_clean.lower():
                    num_txt = "".join(c for c in l_clean if c.isdigit())
                    if num_txt: 
                        target_etape["duree_jours"] = int(num_txt)
                    continue
                
                # Extraction Équipes (Chefs, Ouvriers, Conducteurs)
                if ":" in l_clean and any(k in l_clean.lower() for k in ["chef", "ouvrier", "conducteur"]):
                    gauche, droite = l_clean.split(":", 1)
                    match_nb = re.search(r"(\d+)", droite)
                    if match_nb:
                        val_nb = float(match_nb.group(1))
                        if "conducteur" in gauche.lower() or "engin" in gauche.lower(): 
                            target_etape["jh_cond"] = val_nb
                        elif "chef" in gauche.lower(): 
                            target_etape["jh_chef"] = val_nb
                        elif "ouvrier" in gauche.lower(): 
                            target_etape["jh_ouvrier"] = val_nb
                    continue

                # Extraction Matériaux
                if "matériaux requis :" in l_clean.lower() or "materiaux requis :" in l_clean.lower():
                    partie_mats = l_clean.split(":")[-1].lower()
                    if "aucun" not in partie_mats:
                        sous_elements = partie_mats.split("&") if "&" in partie_mats else [partie_mats]
                        for sub in sous_elements:
                            qte_txt = "".join(c for c in sub if c.isdigit())
                            if qte_txt:
                                qte_val = float(qte_txt)
                                mat_nom = None
                                if "canalisation" in sub: mat_nom = "canalisations"
                                elif "armature" in sub: mat_nom = "armature"
                                elif "enrob" in sub: mat_nom = "enrobe"
                                elif "sable" in sub: mat_nom = "sable"
                                elif "terre" in sub: mat_nom = "terre"
                                elif "tôle" in sub or "tole" in sub: mat_nom = "tole"
                                elif "béton" in sub or "beton" in sub: mat_nom = "beton"
                                elif "panneau" in sub: mat_nom = "panneaux"
                                elif "tuyau" in sub: mat_nom = "tuyaux"
                                elif "poutre" in sub: mat_nom = "poutres"
                                
                                if mat_nom:
                                    target_etape["materiaux"][mat_nom] = qte_val
                    continue

                # 🎯 6. EXTRACTION CORRIGÉE ET SÉCURISÉE AU SINGULIER AVEC MAJUSCULE EN PREMIER
                if "requis :" in l_clean.lower() or "necessite :" in l_clean.lower():
                    ligne_brute_clean = l_clean.lower().replace("é", "e").replace("è", "e").replace("à", "a")
                    cat_engin = None
                    
                    if "camion benne" in ligne_brute_clean: cat_engin = "Camion benne"
                    elif "niveleuse" in ligne_brute_clean: cat_engin = "Niveleuse"
                    elif "finisseur" in ligne_brute_clean: cat_engin = "Finisseur"
                    elif "compacteur pour enrobe" in ligne_brute_clean: cat_engin = "Compacteur d'enrobé"
                    elif "compacteur de sol" in ligne_brute_clean or "compacteur" in ligne_brute_clean: cat_engin = "Compacteur de sol"
                    elif "fraiseuse" in ligne_brute_clean: cat_engin = "Fraiseuse"
                    elif "chargeuse compacte" in ligne_brute_clean: cat_engin = "Chargeuse compacte"
                    elif "chargeuse" in ligne_brute_clean: cat_engin = "Chargeuse"
                    elif "pelleteuse" in ligne_brute_clean or "pelle" in ligne_brute_clean: cat_engin = "Pelleteuse"
                    elif "malaxeur" in ligne_brute_clean or "camion beton" in ligne_brute_clean: cat_engin = "Camion malaxeur"
                    elif "telescopique" in ligne_brute_clean: cat_engin = "Chargeur téléscopique"

                    if cat_engin:
                        match_niv = re.search(r'niveau\s*(\d+)', ligne_brute_clean)
                        niv = f"N{match_niv.group(1)}" if match_niv else "N1"
                        
                        if {"type": cat_engin, "niveau": niv} not in target_etape["engins"]:
                            target_etape["engins"].append({"type": cat_engin, "niveau": niv})

        # --- DESSIN GÉNÉRAL DU RAPPORT EN PAGE DIRECTE NATIVE ---
        if chantiers_detectes:
            st.markdown("---")
            st.markdown("### 📊 Rapport de Planification & Consolidation NoSQL en Bloc")
            
            for k_ch, data in chantiers_detectes.items():
                somme_jours_etapes = sum([int(et['duree_jours']) for et in data['etapes_techniques'].values()])
                jours_en_tete = int(data['jours'])
                
                cout_rh_estime = 0.0
                cout_loc_estime = 0.0
                for et_data in data['etapes_techniques'].values():
                    d_forfait = float(math.ceil(et_data['duree_jours']))
                    cout_rh_estime += (et_data['jh_cond'] * d_forfait * px_cond) + (et_data['jh_chef'] * d_forfait * px_chef) + (et_data['jh_ouvrier'] * d_forfait * px_ouvrier)
                    cout_loc_estime += len(et_data['engins']) * d_forfait * px_location_machine
                
                total_charges = cout_rh_estime + cout_loc_estime
                benefice_net = float(data['revenus'] - total_charges)
                roi_global = (benefice_net / total_charges * 100) if total_charges > 0 else 0.0
                roi_par_jour = (roi_global / somme_jours_etapes) if somme_jours_etapes > 0 else 0.0
                
                st.markdown(f"#### 🏗️ Ouvrage Détecté : **{data['nom_affiche_propre']}**")
                
                c_k1, c_k2, c_k3 = st.columns(3)
                with c_k1: st.metric(label="💰 Montant du Chantier", value=f"{int(data['revenus']):,.0f}".replace(",", " ") + " €")
                with c_k2: st.metric(label="📈 Bénéfice Estimé", value=f"{int(benefice_net):,.0f}".replace(",", " ") + " €")
                with c_k3: st.metric(label="📊 ROI Global / ROI Jour", value=f"{roi_global:.2f} %", delta=f"{roi_par_jour:.2f} %/j", delta_color="normal")
                
                if jours_en_tete != somme_jours_etapes:
                    st.warning(f"⚠️ **Écart détecté :** L'en-tête annonce `{jours_en_tete} jours`, mais la somme de vos étapes fait `{somme_jours_etapes} jours` réels.")
                else:
                    st.success(f"✅ **Durée Synchrone :** L'en-tête et le cumul des étapes concordent parfaitement (`{somme_jours_etapes} jours`).")
                
                for n_e, e_data in data['etapes_techniques'].items():
                    desc_mats = f"🧱 Matériaux : {e_data['materiaux']}" if e_data['materiaux'] else "🧱 Matériaux : Aucun"
                    desc_engins = f"🚜 Engins : {len(e_data['engins'])} requis" if e_data['engins'] else "🚜 Engins : Aucun"
                    st.caption(f"▪️ **Étape {n_e} ({e_data['duree_jours']}j) :** 🕹️ Cond: {e_data['jh_cond']} | 🧑‍💼 Chef: {e_data['jh_chef']} | <b>👷 Ouvriers:</b> {e_data['jh_ouvrier']} | {desc_mats} | {desc_engins}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("✅ VALIDER ET INJECTER TOUT DANS L'HISTORIQUE CLOUD", type="primary", width="stretch", key="btn_native_save_btp_v12_direct"):
                with st.spinner("Écriture réseau en cours vers Firestore (2 tables)..."):
                    enregistrer_chantiers_cloud(chantiers_detectes)
                st.rerun()

def afficher_onglet_doublons():
    st.markdown("### 🔍 Vérificateur Intuitif de Doublons Cloud")
    st.caption("Consultez la base NoSQL pour valider l'existence de vos fiches techniques.")
    
    dict_modeles_verif = db_module.charger_catalogue_chantiers()
    if not dict_modeles_verif or len(dict_modeles_verif) <= 1:
        st.info("💡 Aucun modèle enregistré dans le catalogue NoSQL de la Table 1.")
        return
        
    lignes_verif = []
    for doc_id, data_m in dict_modeles_verif.items():
        if doc_id == "Choisir un chantier pré-configuré...": 
            continue
        
        rev_val = float(data_m.get("revenus", 0.0))
        txt_ca = f"{rev_val:,.0f}".replace(",", " ")
        
        lignes_verif.append({
            "Clé Unique (Table 1)": str(doc_id),
            "Nom du Chantier": str(data_m.get("nom_modele", "Inconnu")),
            "Chiffre d'Affaires": f"{txt_ca} €"
        })
        
    df_verif = pd.DataFrame(lignes_verif)
    st.dataframe(df_verif, width="stretch", hide_index=True)
