# Fichier complet, enrichi avec calculs financiers : onglets/consulter_modeles.py
import streamlit as st
import pandas as pd
import math
import database as db

def extraire_tarif_jour_firebase_secours(poste, contrat_affiche="CDD"):
    """
    Fonction miroir de secours pour extraire les tarifs journaliers RH.
    S'aligne avec la logique de votre onglet ajouter_chantier.
    """
    type_contrat_nosql = "CDI (Salaire mensuel)" if contrat_affiche == "CDI" else "CDD (Salaire par jour)"
    doc_id_synthese = f"{poste}_{type_contrat_nosql}"
    
    try:
        doc_snap = db.db.collection("synthese_grille_tarifaire").document(doc_id_synthese).get()
        if doc_snap.exists:
            d_data = doc_snap.to_dict()
            return float(d_data.get("prix_moyen_journalier_7", d_data.get("prix_moyen_mensuel", 230.0)))
    except Exception:
        pass
    
    secours = {"Conducteur": 250.0, "Chef": 300.0, "Ouvrier": 210.0}
    return secours.get(poste, 200.0)

def afficher_onglet_consulter_modeles():
    st.subheader("🗂️ Catalogue Évolué des Modèles de Chantiers (Calculs Étape par Étape)")
    st.write("Consultez les fiches techniques avec l'évaluation en direct du coût de la main-d'œuvre et des matériaux requis.")

    # 1. Extraction en cache (10 min)
    with st.spinner("Extraction du catalogue NoSQL cloud..."):
        catalogue_chantiers = db.charger_catalogue_chantiers()
        MATERIAUX_DB = db.charger_materiaux_config()

    if not catalogue_chantiers:
        st.info("💡 Le catalogue des modèles pré-configurés est actuellement vide.")
        return

    # 2. Barre de recherche rapide
    recherche = st.text_input("🔍 Rechercher un modèle par son nom :", value="").strip()

    # Dictionnaires de correspondance des clés
    traduction_mats = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", "beton": "Béton",
        "armature": "Armature métallique", "tole": "Plaque de tôle", "poutres": "Poutres en acier",
        "tuyaux": "Tuyaux d'eau", "canalisations": "Canalisations", "panneaux": "Panneaux"
    }

    # Récupération des tarifs RH par défaut (en mode CDD/Forfait journalier par étape pour les modèles)
    px_cond = extraire_tarif_jour_firebase_secours("Conducteur", "CDD")
    px_chef = extraire_tarif_jour_firebase_secours("Chef", "CDD")
    px_ouvrier = extraire_tarif_jour_firebase_secours("Ouvrier", "CDD")

    # 3. Traitement des chantiers
    for ch_id, ch_data in catalogue_chantiers.items():
        nom_modele = ch_data.get("nom_modele", ch_id)
        
        if recherche and recherche.lower() not in nom_modele.lower():
            continue
            
        revenus = ch_data.get("revenus", 0.0)
        j = ch_data.get("jours_globaux", 0)
        h = ch_data.get("heures_globales", 0)
        m = ch_data.get("minutes_globales", 0)
        etapes = ch_data.get("etapes_techniques", [])

        titre_expander = f"🏗️ {nom_modele} — 💰 {revenus:,.0f} € — ⏱️ {j}j {h}h {m}m ({len(etapes)} étapes)".replace(",", " ")
        
        with st.expander(titre_expander, expanded=False):
            if not etapes:
                st.caption("⚪ Aucune étape technique enregistrée pour ce modèle.")
                continue

            st.markdown("##### 📋 Décomposition financière et technique des étapes (Table 2)")
            
            for etape in etapes:
                num_e = etape.get("num_etape", 1)
                nom_etape = etape.get("nom_etape", "Étape sans nom")
                duree_j = float(etape.get("duree_jours", 1.0))
                
                # Règle de calcul Sim-TP : les journées entamées sont dues au forfait (math.ceil)
                jours_forfait = float(math.ceil(duree_j))
                
                # --- CALCUL MAIN D'ŒUVRE ---
                cond = float(etape.get("jh_cond", 0.0))
                chef = float(etape.get("jh_chef", 0.0))
                ouv = float(etape.get("jh_ouvrier", 0.0))
                
                cout_rh_etape = (cond * px_cond + chef * px_chef + ouv * px_ouvrier) * jours_forfait
                
                # --- CALCUL MATÉRIAUX ---
                mats = etape.get("materiaux", {})
                cout_mats_etape = 0.0
                
                mats_affiches = []
                if isinstance(mats, dict):
                    for mat_cle, qte in mats.items():
                        qte_val = float(qte)
                        if qte_val > 0:
                            nom_officiel_db = traduction_mats.get(mat_cle, mat_cle.capitalize())
                            # Récupération du prix unitaire depuis Firebase (ou fallback)
                            prix_unitaire = float(MATERIAUX_DB.get(nom_officiel_db, 0.0))
                            cout_ligne_mat = qte_val * prix_unitaire
                            cout_mats_etape += cout_ligne_mat
                            
                            mats_affiches.append(f"- {nom_officiel_db} : `{int(qte_val)}` *({prix_unitaire:.0f} €/u = {cout_ligne_mat:,.0f} €)*")

                engins = etape.get("engins", [])

                # En-tête de l'étape
                st.markdown(f"**🔹 Étape {num_e:02d} : {nom_etape}** *({duree_j} jour(s) réel(s) ➔ {int(jours_forfait)}j payé(s))*")
                
                # Rendu en 3 colonnes propres
                c_rh, c_mats, c_engins = st.columns(3)
                
                with c_rh:
                    st.markdown("**👥 Équipe & Masse Salariale :**")
                    st.markdown(f"- 🕹️ Cond : `{int(cond)}` *({px_cond:.0f}€/j)*")
                    st.markdown(f"- 🧑‍💼 Chef : `{int(chef)}` *({px_chef:.0f}€/j)*")
                    st.markdown(f"- 👷 Ouv : `{int(ouv)}` *({px_ouvrier:.0f}€/j)*")
                    st.markdown(f"💰 **Sous-total RH :** `{cout_rh_etape:,.0f} €`".replace(",", " "))
                
                with c_mats:
                    st.markdown("**🧱 Matériaux & Coûts :**")
                    if mats_affiches:
                        for item_txt in mats_affiches:
                            st.markdown(item_txt.replace(",", " "))
                        st.markdown(f"💰 **Sous-total Matériaux :** `{cout_mats_etape:,.0f} €`".replace(",", " "))
                    else:
                        st.caption("Aucun matériau requis (0 €)")

                with c_engins:
                    st.markdown("**🚜 Flotte d'engins requis :**")
                    if engins:
                        for eng in engins:
                            st.markdown(f"- {eng.get('type')} `({eng.get('niveau')})`")
                    else:
                        st.caption("Aucun engin requis")
                
                # Ligne de synthèse budgétaire pour l'étape active
                total_etape = cout_rh_etape + cout_mats_etape
                st.markdown(f"➡️ **Coût Direct Consolidé de l'Étape {num_e:02d} :** `{total_etape:,.0f} €`".replace(",", " "))
                st.markdown("<div style='border-bottom: 1px dashed #dedede; margin: 15px 0;'></div>", unsafe_allow_html=True)

