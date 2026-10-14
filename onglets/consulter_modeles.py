# Fichier complet, nettoyé et aligné sur 4 colonnes d'en-tête : onglets/consulter_modeles.py
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
    
    secours = {"Conducteur": 244.91, "Chef": 239.45, "Ouvrier": 256.00}
    return secours.get(poste, 200.0)

def afficher_onglet_consulter_modeles():
    st.subheader("🗂️ Classement des Modèles NoSQL par Rentabilité Journalière")
    st.write("Consultez les fiches techniques classées par ordre décroissant selon le gain net par jour réel.")

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

    # ==============================================================================
    # 🎯 PHASE 1 : PRÉ-CALCUL ET CLASSEMENT SELON VOTRE FORMULE FINANCIÈRE
    # ==============================================================================
    liste_chantiers_calcules = []

    for ch_id, ch_data in catalogue_chantiers.items():
        nom_modele = ch_data.get("nom_modele", ch_id)
        
        if recherche and recherche.lower() not in nom_modele.lower():
            continue
            
        revenus = float(ch_data.get("revenus", 0.0))
        j = ch_data.get("jours_globaux", 0)
        h = ch_data.get("heures_globales", 0)
        m = ch_data.get("minutes_globales", 0)
        etapes = ch_data.get("etapes_techniques", [])

        cout_rh_total = 0.0
        cout_mats_total = 0.0
        jours_cumules = 0.0

        for etape in etapes:
            duree_j = float(etape.get("duree_jours", 1.0))
            jours_cumules += duree_j
            jours_forfait = float(math.ceil(duree_j))
            
            cond = float(etape.get("jh_cond", 0.0))
            chef = float(etape.get("jh_chef", 0.0))
            ouv = float(etape.get("jh_ouvrier", 0.0))
            
            cout_rh_total += (cond * px_cond + chef * px_chef + ouv * px_ouvrier) * jours_forfait
            
            mats = etape.get("materiaux", {})
            if isinstance(mats, dict):
                for mat_cle, qte in mats.items():
                    qte_val = float(qte)
                    if qte_val > 0:
                        nom_officiel_db = traduction_mats.get(mat_cle, mat_cle.capitalize())
                        prix_unitaire = float(MATERIAUX_DB.get(nom_officiel_db, 0.0))
                        cout_mats_total += (qte_val * prix_unitaire)

        total_charges = cout_rh_total + cout_mats_total
        marge_net = revenus - total_charges
        roi_global = (marge_net / total_charges * 100) if total_charges > 0 else 0.0
        
        duree_totale_jours = jours_cumules if jours_cumules > 0 else float(j + (h/24.0) + (m/1440.0))
        roi_par_jour = (revenus - (cout_rh_total + cout_mats_total)) / duree_totale_jours if duree_totale_jours > 0 else 0.0

        liste_chantiers_calcules.append({
            "ch_id": ch_id,
            "ch_data": ch_data,
            "revenus": revenus,
            "jours_globaux_indic": j,
            "etapes": etapes,
            "cumul_cout_rh": cout_rh_total,
            "cumul_cout_mats": cout_mats_total,
            "total_charges": total_charges,
            "marge_net": marge_net,
            "roi_global": roi_global,
            "roi_par_jour": roi_par_jour,
            "duree_totale_jours": duree_totale_jours
        })

    if liste_chantiers_calcules:
        df_tri = pd.DataFrame(liste_chantiers_calcules)
        df_tri = df_tri.sort_values(by="roi_par_jour", ascending=False)
        liste_chantiers_ordonnes = df_tri.to_dict(orient="records")
    else:
        liste_chantiers_ordonnes = []

    # ==============================================================================
    # 🎯 PHASE 2 : RENDU GRAPHIQUE ET EN-TÊTE SUR 4 COLONNES PARFAITEMENT ALIGNÉES
    # ==============================================================================

    st.markdown("<div style='border-bottom: 2px solid #31333F; margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    for item in liste_chantiers_ordonnes:
        st.markdown("<br>", unsafe_allow_html=True)
        c_head1, c_head2, c_head3, c_head4 = st.columns([5, 2, 2, 3])
        with c_head1: st.markdown("**🏗️ Intitulé du Modèle Ouvrage**")
        with c_head2: st.markdown("**💰 Revenus**")
        with c_head3: st.markdown("**⏱️ Durée**")
        with c_head4: st.markdown("**⚡ Gain Net / Jour**")
        ch_data = item["ch_data"]
        nom_modele = ch_data.get("nom_modele", item["ch_id"])
        
        # 🟢 Création du conteneur d'en-tête aligné sur 4 colonnes de proportions identiques
        with st.container():
            col1, col2, col3, col4 = st.columns([5, 2, 2, 3])
            with col1:
                st.markdown(f"#### {nom_modele}")
            with col2:
                st.markdown(f"#### {item['revenus']:,.0f} €".replace(",", " "))
            with col3:
                st.markdown(f"#### {int(item['duree_totale_jours'])} j")
            with col4:
                st.markdown(f"#### **{item['roi_par_jour']:,.0f} €/j**".replace(",", " "))
            
            # L'expander vide de titre sert de tiroir pour stocker le détail de la Table 2
            with st.expander("Voir le détail technique des étapes et charges", expanded=False):
                if not item["etapes"]:
                    st.caption("⚪ Aucune étape technique enregistrée pour ce modèle.")
                    continue

                st.markdown("##### 📋 Décomposition financière par étape technique (Table 2)")
                
                for etape in item["etapes"]:
                    num_e = etape.get("num_etape", 1)
                    nom_etape = etape.get("nom_etape", "Étape sans nom")
                    duree_j = float(etape.get("duree_jours", 1.0))
                    jours_forfait = float(math.ceil(duree_j))
                    
                    # --- CALCUL RH ---
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
                                prix_unitaire = float(MATERIAUX_DB.get(nom_officiel_db, 0.0))
                                cout_ligne_mat = qte_val * prix_unitaire
                                cout_mats_etape += cout_ligne_mat
                                mats_affiches.append(f"- {nom_officiel_db} : `{int(qte_val)}` *({prix_unitaire:.0f} €/u = {cout_ligne_mat:,.0f} €)*")

                    engins = etape.get("engins", [])

                    st.markdown(f"**🔹 Étape {num_e:02d} : {nom_etape}** *({duree_j} jour(s) réel(s) ➔ {int(jours_forfait)}j forfaitisés)*")
                    
                    c_rh, c_mats, c_engins = st.columns(3)
                    
                    with c_rh:
                        st.markdown("**👥 Équipe (Taux Message CDI) :**")
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

            # --- SYNTHÈSE GLOBALE DU MODÈLE DE CHANTIER ---
            st.markdown("##### 📊 Bilan Budgétaire Prévisionnel du Modèle Ouvrage")
            cb1, cb2, cb3, cb4 = st.columns(4)
            with cb1:
                st.metric(label="👥 Masse Salariale CDI Totale", value=f"{item['cumul_cout_rh']:,.2f} €".replace(",", " "))
            with cb2:
                st.metric(label="🧱 Budget Matériaux Global", value=f"{item['cumul_cout_mats']:,.2f} €".replace(",", " "))
            with cb3:
                st.metric(label="📊 ROI Global", value=f"{item['roi_global']:.2f} %")
            with cb4:
                st.metric(label="⚡ Gain Net / Jour", value=f"{item['roi_par_jour']:,.0f} €/j".replace(",", " "))

            # --- CODE MODIFIÉ AVEC DÉCLENCHEUR POUR TOUTE LA LIGNE DU BAS ---
            st.markdown("<br>", unsafe_allow_html=True)
            col_alerte1, col_alerte2 = st.columns(2)

            # Variable de déclenchement (définie par défaut à False)
            afficher_notification_temps = False

            # Colonne 1 : Rentabilité Financière (Actuelle)
            with col_alerte1:
                if item["marge_net"] >= 0:
                    st.success(f"🟢 **Rentabilité positive estimée :** Marge nette de **{item['marge_net']:,.2f} €** pour {item['duree_totale_jours']:.1f} jours d'activité.".replace(",", " "))
                else:
                    st.error(f"🔴 **Modèle déficitaire :** Perte sèche évaluée à **{abs(item['marge_net']):,.2f} €**.".replace(",", " "))

            # Colonne 2 : Comparaison des Temps (Vert, Bleu Harmonisé, Rouge)
            with col_alerte2:
                temps_chantier = float(item["jours_globaux_indic"])
                temps_etapes = float(item["duree_totale_jours"])
                
                if temps_etapes < temps_chantier:
                    st.success(f"🟢 **Planning optimisé :** Le cumul des étapes ({temps_etapes:.1f} j) est **inférieur** au temps global ({temps_chantier:.1f} j).")
                    afficher_notification_temps = True  # Déclenchement activé
                
                elif temps_etapes == temps_chantier:
                    st.markdown(
                        f"""
                        <div style="background-color: rgba(28, 127, 238, 0.15); color: rgb(100, 180, 255); padding: 16px; border-radius: 0.5rem; border: 1px solid rgba(28, 127, 238, 0.3); font-size: 1rem;">
                            🔵 <b>Planning parfait :</b> Le cumul des étapes ({temps_etapes:.1f} j) est <b>égal</b> au temps global ({temps_chantier:.1f} j).
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Reste à False, car le temps est égal
                
                else:  # temps_etapes > temps_chantier
                    st.error(f"🔴 **Alerte Temps :** Le cumul des étapes ({temps_etapes:.1f} j) est **supérieur** au temps global ({temps_chantier:.1f} j).")
                    afficher_notification_temps = True  # Déclenchement activé

            # --- S'affiche sur toute la largeur de la ligne uniquement si activé ---
            if afficher_notification_temps:
                st.markdown(
                    """
                    <div style="text-align: center; color: rgba(250, 250, 250, 0.6); font-size: 1rem; margin-top: 5px; font-style: italic;">
                        ℹ️ Attention : Le gain net journalier et les calculs financiers sont adaptés et indexés sur la durée réelle cumulée des étapes.
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        st.markdown("<div style='border-bottom: 2px solid #31333F; margin-top: 15px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
