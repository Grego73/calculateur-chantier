# Fichier complet, nettoyé et indexé avec le ROI/jour : onglets/consulter_modeles.py
import streamlit as st
import pandas as pd
import math
import database as db

def extraire_tarif_jour_cdi_firebase(poste):
    """
    Extrait le tarif journalier amorti sur 7 jours depuis la table NoSQL
    'synthese_grille_tarifaire' en ciblant exclusivement le contrat CDI.
    """
    doc_id_synthese = f"{poste}_CDI (Salaire mensuel)"
    
    try:
        doc_snap = db.db.collection("synthese_grille_tarifaire").document(doc_id_synthese).get()
        if doc_snap.exists:
            d_data = doc_snap.to_dict()
            return float(d_data.get("prix_moyen_journalier_7", d_data.get("prix_moyen_mensuel", 244.91)))
    except Exception:
        pass
    
    secours = {"Conducteur": 244.91, "Chef": 300.0, "Ouvrier": 210.0}
    return secours.get(poste, 200.0)

def afficher_onglet_consulter_modeles():
    st.subheader("🗂️ Catalogue des Modèles NoSQL — Rentabilité Théorique Complète")
    st.write("Consultez l'évaluation financière en direct basée sur la grille CDI active et le catalogue des matériaux du calculateur.")

    # 1. Chargement des configurations cloud depuis database.py
    with st.spinner("Synchronisation des grilles et tarifs cloud..."):
        catalogue_chantiers = db.charger_catalogue_chantiers()
        MATERIAUX_DB = db.charger_materiaux_config()

    if not catalogue_chantiers:
        st.info("💡 Le catalogue des modèles pré-configurés est actuellement vide.")
        return

    # 2. Outil de filtrage textuel
    recherche = st.text_input("🔍 Rechercher un modèle par son nom :", value="").strip()

    # Dictionnaire d'harmonisation rigoureux indexé sur votre table 'configuration_materiaux'
    traduction_mats = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", "beton": "Béton",
        "armature": "Armature", "tole": "Tôle", "poutres": "Poutres",
        "tuyaux": "Tuyaux", "canalisations": "Canalisations", "panneaux": "Panneaux"
    }

    # Extraction des moyennes journalières CDI depuis Firebase
    px_cond = extraire_tarif_jour_cdi_firebase("Conducteur")
    px_chef = extraire_tarif_jour_cdi_firebase("Chef")
    px_ouvrier = extraire_tarif_jour_cdi_firebase("Ouvrier")

    # 3. Rendu récursif des chantiers
    for ch_id, ch_data in catalogue_chantiers.items():
        nom_modele = ch_data.get("nom_modele", ch_id)
        
        if recherche and recherche.lower() not in nom_modele.lower():
            continue
            
        revenus = float(ch_data.get("revenus", 0.0))
        j = ch_data.get("jours_globaux", 0)
        h = ch_data.get("heures_globales", 0)
        m = ch_data.get("minutes_globales", 0)
        etapes = ch_data.get("etapes_techniques", [])

        # Compteurs pour la synthèse générale du modèle actif
        cumul_cout_rh_chantier = 0.0
        cumul_cout_mats_chantier = 0.0
        jours_totaux_calcul_etapes = 0.0

        titre_expander = f"🏗️ {nom_modele} — 💰 {revenus:,.0f} € — ⏱️ {j}j {h}h {m}m ({len(etapes)} étapes)".replace(",", " ")
        
        with st.expander(titre_expander, expanded=False):
            if not etapes:
                st.caption("⚪ Aucune étape technique enregistrée pour ce modèle.")
                continue

            st.markdown("##### 📋 Décomposition financière par étape technique (Table 2)")
            
            for etape in etapes:
                num_e = etape.get("num_etape", 1)
                nom_etape = etape.get("nom_etape", "Étape sans nom")
                duree_j = float(etape.get("duree_jours", 1.0))
                jours_totaux_calcul_etapes += duree_j
                
                # Règle de calcul Sim-TP : application forfaitaire au jour supérieur pour l'étape
                jours_forfait = float(math.ceil(duree_j))
                
                # --- CALCUL RH COMPOSÉ CDI ---
                cond = float(etape.get("jh_cond", 0.0))
                chef = float(etape.get("jh_chef", 0.0))
                ouv = float(etape.get("jh_ouvrier", 0.0))
                
                cout_rh_etape = (cond * px_cond + chef * px_chef + ouv * px_ouvrier) * jours_forfait
                cumul_cout_rh_chantier += cout_rh_etape
                
                # --- CALCUL MATÉRIAUX COMPOSÉ ---
                mats = etape.get("materiaux", {})
                cout_mats_etape = 0.0
                mats_affiches = []
                
                if isinstance(mats, dict):
                    for mat_cle, qte in mats.items():
                        qte_val = float(qte)
                        if qte_val > 0:
                            nom_officiel_db = traduction_mats.get(mat_cle, mat_cle.capitalize())
                            prix_unitaire = float(MATERIAUX_DB.get(nom_officiel_db, 0.0))
                            cout_ligne_mat = qte_val * prix_unitaire
                            cout_mats_etape += cout_ligne_mat
                            
                            mats_affiches.append(f"- {nom_officiel_db} : `{int(qte_val)}` *({prix_unitaire:.0f} €/unités = {cout_ligne_mat:,.0f} €)*")

                cumul_cout_mats_chantier += cout_mats_etape
                engins = etape.get("engins", [])

                st.markdown(f"**🔹 Étape {num_e:02d} : {nom_etape}** *({duree_j} jour(s) réel(s) ➔ {int(jours_forfait)}j forfaitisés)*")
                
                c_rh, c_mats, c_engins = st.columns(3)
                
                with c_rh:
                    st.markdown("**👥 Équipe (Taux CDI Réel) :**")
                    st.markdown(f"- 🕹️ Cond : `{int(cond)}` *({px_cond:.2f}€/j)*")
                    st.markdown(f"- 🧑‍💼 Chef : `{int(chef)}` *({px_chef:.2f}€/j)*")
                    st.markdown(f"- 👷 Ouv : `{int(ouv)}` *({px_ouvrier:.2f}€/j)*")
                    st.markdown(f"💰 **Masse Salariale Étape :** `{cout_rh_etape:,.2f} €`".replace(",", " "))
                
                with c_mats:
                    st.markdown("**🧱 Matériaux Requis :**")
                    if mats_affiches:
                        for item_txt in mats_affiches:
                            st.markdown(item_txt.replace(",", " "))
                        st.markdown(f"💰 **Total Matériaux Étape :** `{cout_mats_etape:,.0f} €`".replace(",", " "))
                    else:
                        st.caption("Aucun matériau requis (0 €)")

                with c_engins:
                    st.markdown("**🚜 Flotte d'engins requis :**")
                    if engins:
                        for eng in engins:
                            st.markdown(f"- {eng.get('type')} `({eng.get('niveau')})`")
                    else:
                        st.caption("Aucun engin requis")
                
                total_etape = cout_rh_etape + cout_mats_etape
                st.markdown(f"➡️ **Coût Consolidé Étape {num_e:02d} :** `{total_etape:,.2f} €`".replace(",", " "))
                st.markdown("<div style='border-bottom: 1px dashed #dedede; margin: 15px 0;'></div>", unsafe_allow_html=True)

            # ==============================================================================
            # 🎯 SECTION MIS À JOUR : BILAN BUDGÉTAIRE AVEC ANALYSE ROI / JOUR
            # ==============================================================================
            total_charges_chantier = cumul_cout_rh_chantier + cumul_cout_mats_chantier
            marge_net_theorique = revenus - total_charges_chantier
            
            # Calculs des ROI de l'activité
            roi_theorique = (marge_net_theorique / total_charges_chantier * 100) if total_charges_chantier > 0 else 0.0
            
            # Utilisation de la durée cumulée des étapes (ou fallback de sécurité sur l'en-tête)
            duree_totale_jours = jours_totaux_calcul_etapes if jours_totaux_calcul_etapes > 0 else float(j + (h/24.0) + (m/1440.0))
            roi_par_jour_theorique = (roi_theorique / duree_totale_jours) if duree_totale_jours > 0 else roi_theorique

            st.markdown("##### 📊 Bilan Budgétaire Prévisionnel du Modèle Ouvrage")
            cb1, cb2, cb3, cb4 = st.columns(4)
            with cb1:
                st.metric(label="👥 Masse Salariale CDI Totale", value=f"{cumul_cout_rh_chantier:,.2f} €".replace(",", " "))
            with cb2:
                st.metric(label="🧱 Budget Matériaux Global", value=f"{cumul_cout_mats_chantier:,.2f} €".replace(",", " "))
            with cb3:
                st.metric(label="📊 ROI Global", value=f"{roi_theorique:.2f} %")
            with cb4:
                # ⚙️ AJOUT DE LA METRIC DU ROI / JOUR
                st.metric(label="⚡ ROI / Jour", value=f"{roi_par_jour_theorique:.2f} %/j")

            if marge_net_theorique >= 0:
                st.success(f"🟢 **Rentabilité positive estimée :** Marge nette de **{marge_net_theorique:,.2f} €** pour {duree_totale_jours:.1f} jours d'activité.".replace(",", " "))
            else:
                st.error(f"🔴 **Modèle déficitaire :** Perte sèche évaluée à **{abs(marge_net_theorique):,.2f} €**.".replace(",", " "))
