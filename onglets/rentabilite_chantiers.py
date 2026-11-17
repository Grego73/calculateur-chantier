import math
import streamlit as st
import pandas as pd
import database as db


def _charger_tarifs_salaires(type_contrat="CDI"):
    """Récupère les tarifs journaliers (Conducteur, Chef, Ouvrier) depuis le cache Firebase."""
    tarifs_cloud = db.charger_synthese_salaires()
    suffixe = "CDI (Salaire mensuel)" if type_contrat == "CDI" else "CDD (Salaire par jour)"
    defauts = {"Conducteur": 244.91, "Chef": 239.45, "Ouvrier": 256.00}
    if type_contrat == "CDD":
        defauts = {"Conducteur": 290.00, "Chef": 280.00, "Ouvrier": 300.00}

    px_cond = float(tarifs_cloud.get(f"Conducteur_{suffixe}", defauts["Conducteur"]))
    px_chef = float(tarifs_cloud.get(f"Chef_{suffixe}", defauts["Chef"]))
    px_ouv = float(tarifs_cloud.get(f"Ouvrier_{suffixe}", defauts["Ouvrier"]))
    return px_cond, px_chef, px_ouv


def _chercher_tarif_location_engin(type_engin, niveau_engin, tarifs_engins):
    """Trouve le tarif journalier de location d'un engin (avec repli sur niveau supérieur si absent)."""
    nom_clean = str(type_engin).strip()
    niv_clean = str(niveau_engin).strip().upper()
    if not niv_clean.startswith("N"):
        niv_clean = f"N{niv_clean}"

    correspondances = {
        "camion toupie": "Camion malaxeur",
        "chargeur télescopique": "Chargeur téléscopique",
        "compacteur enrobé": "Compacteur d'enrobé",
        "camion grue": "Grue mobile",
    }
    nom_officiel = correspondances.get(nom_clean.lower(), nom_clean)

    paliers = ["N1", "N2", "N3", "N4"]
    idx_depart = paliers.index(niv_clean) if niv_clean in paliers else 0

    for i in range(idx_depart, len(paliers)):
        cle = f"{nom_officiel} ({paliers[i]})"
        if cle in tarifs_engins:
            return float(tarifs_engins[cle]), cle

    return 380.0, f"{nom_officiel} ({niv_clean})"


def afficher_onglet_rentabilite_chantiers():
    catalogue = db.charger_catalogue_chantiers()
    materiaux_db = db.charger_materiaux_config()
    tarifs_engins = db.charger_tarifs_engins_unifies()

    if not catalogue:
        st.info("💡 Aucun chantier enregistré dans votre base. Ajoutez vos fiches depuis **Administration > Import Données Jeu**.")
        return

    # ==========================================================================
    # --- 1. PANNEAU DE RÉGLAGES DE L'ENTREPRISE (EMPLOYÉS & FLOTTE) ---
    # ==========================================================================
    with st.container(border=True):
        st.markdown("#### ⚙️ Configuration de votre Entreprise")
        col_opt1, col_opt2, col_opt3 = st.columns([1, 1.3, 1.5])

        with col_opt1:
            type_contrat = st.radio(
                "👥 Contrats des employés :",
                ["CDI", "CDD"],
                horizontal=True,
                key="rent_type_contrat",
            )

        with col_opt2:
            mode_engins = st.radio(
                "🚜 Gestion de votre flotte :",
                [
                    "Tous possédés (0 € location)",
                    "Personnaliser mon parc",
                    "Tout louer (100 % location)",
                ],
                key="rent_mode_engins",
            )

        # Collecte de tous les engins existants dans les chantiers pour le sélecteur
        engins_rencontres = set()
        for ch_data in catalogue.values():
            for et in ch_data.get("etapes_techniques", []):
                for eng in et.get("engins", []):
                    _, cle_norm = _chercher_tarif_location_engin(
                        eng.get("type", ""), eng.get("niveau", "N1"), tarifs_engins
                    )
                    engins_rencontres.add(cle_norm)

        engins_possedes = set()
        with col_opt3:
            if mode_engins == "Personnaliser mon parc":
                selection = st.multiselect(
                    "✅ Cochez les engins que vous possédez déjà :",
                    options=sorted(list(engins_rencontres)),
                    default=[],
                    placeholder="Choisir vos engins...",
                    key="rent_engins_possedes",
                )
                engins_possedes = set(selection)
            elif mode_engins == "Tous possédés (0 € location)":
                engins_possedes = engins_rencontres
                st.caption("🟢 Aucun frais de location facturé sur les chantiers.")
            else:
                st.caption("🟠 100 % des engins requis sont facturés au tarif location/jour.")

    # ==========================================================================
    # --- 2. CALCUL DE RENTABILITÉ DE TOUS LES CHANTIERS ---
    # ==========================================================================
    px_cond, px_chef, px_ouv = _charger_tarifs_salaires(type_contrat)
    traduction_mats = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", "beton": "Béton",
        "armature": "Armature", "tole": "Tôle", "poutres": "Poutres",
        "tuyaux": "Tuyaux", "canalisations": "Canalisations", "panneaux": "Panneaux"
    }

    resultats_chantiers = []

    for ch_id, ch_data in catalogue.items():
        nom = ch_data.get("nom_modele", ch_id)
        revenus = float(ch_data.get("revenus", 0.0))
        etapes = ch_data.get("etapes_techniques", [])

        cout_rh_total = 0.0
        cout_mats_total = 0.0
        cout_loc_total = 0.0
        jours_cumules = 0.0
        details_etapes = []

        for et in etapes:
            num_e = et.get("num_etape", 1)
            nom_e = et.get("nom_etape", f"Étape {num_e}")
            duree_j = float(et.get("duree_jours", 1.0))
            jours_forfait = float(math.ceil(duree_j))
            jours_cumules += duree_j

            # Salaires
            cond = float(et.get("jh_cond", 0.0))
            chef = float(et.get("jh_chef", 0.0))
            ouv = float(et.get("jh_ouvrier", 0.0))
            cout_rh_et = (cond * px_cond + chef * px_chef + ouv * px_ouv) * jours_forfait

            # Matériaux
            cout_mats_et = 0.0
            mats_txt = []
            mats = et.get("materiaux", {})
            if isinstance(mats, dict):
                for m_cle, qte in mats.items():
                    q_val = float(qte)
                    if q_val > 0:
                        nom_off = traduction_mats.get(m_cle, m_cle.capitalize())
                        px_u = float(materiaux_db.get(nom_off, 0.0))
                        cout_mats_et += q_val * px_u
                        mats_txt.append(f"{int(q_val)} {nom_off}")

            # Location engins
            cout_loc_et = 0.0
            engins_txt = []
            for eng in et.get("engins", []):
                qte_eng = int(eng.get("qte", 1))
                px_j_eng, cle_eng = _chercher_tarif_location_engin(
                    eng.get("type", ""), eng.get("niveau", "N1"), tarifs_engins
                )
                est_possede = cle_eng in engins_possedes
                if not est_possede:
                    cout_loc_et += qte_eng * px_j_eng * jours_forfait
                    engins_txt.append(f"🟠 {qte_eng}× {cle_eng} (Loué)")
                else:
                    engins_txt.append(f"🟢 {qte_eng}× {cle_eng} (Parc)")

            cout_rh_total += cout_rh_et
            cout_mats_total += cout_mats_et
            cout_loc_total += cout_loc_et

            details_etapes.append({
                "Étape": f"Étape {num_e} : {nom_e}",
                "Durée (j)": duree_j,
                "Matériaux": ", ".join(mats_txt) if mats_txt else "Aucun",
                "Coût Matériaux (€)": round(cout_mats_et, 0),
                "Équipe": f"{int(cond)} Cond / {int(chef)} Chef / {int(ouv)} Ouv",
                "Coût Salaires (€)": round(cout_rh_et, 0),
                "Engins": ", ".join(engins_txt) if engins_txt else "Aucun",
                "Coût Location (€)": round(cout_loc_et, 0),
                "Total Étape (€)": round(cout_rh_et + cout_mats_et + cout_loc_et, 0),
            })

        j_glob = int(ch_data.get("jours_globaux", 0))
        h_glob = int(ch_data.get("heures_globales", 0))
        m_glob = int(ch_data.get("minutes_globales", 0))
        duree_globale_j = float(j_glob + (h_glob / 24.0) + (m_glob / 1440.0))
        duree_retenue = jours_cumules if jours_cumules > 0 else max(1.0, duree_globale_j)

        depenses_totales = cout_rh_total + cout_mats_total + cout_loc_total
        benefice_net = revenus - depenses_totales
        gain_par_jour = benefice_net / duree_retenue if duree_retenue > 0 else 0.0
        roi_pct = (benefice_net / depenses_totales * 100) if depenses_totales > 0 else 0.0

        resultats_chantiers.append({
            "ch_id": ch_id,
            "Chantier": nom,
            "Étapes": len(etapes),
            "Durée (j)": round(duree_retenue, 1),
            "Revenus (€)": revenus,
            "Matériaux (€)": round(cout_mats_total, 0),
            "Salaires (€)": round(cout_rh_total, 0),
            "Location (€)": round(cout_loc_total, 0),
            "Dépenses (€)": round(depenses_totales, 0),
            "Bénéfice Net (€)": round(benefice_net, 0),
            "Gain / Jour (€/j)": round(gain_par_jour, 0),
            "ROI (%)": round(roi_pct, 1),
            "details_etapes": details_etapes,
        })

    df_classement = pd.DataFrame(resultats_chantiers).sort_values(by="Gain / Jour (€/j)", ascending=False)

    # ==========================================================================
    # --- 3. PODIUM TOP 3 ---
    # ==========================================================================
    st.markdown("### 🏆 Top 3 des Chantiers les Plus Rentables")
    top_3 = df_classement.head(3)
    cols_top = st.columns(len(top_3))
    medailles = ["🥇 1er", "🥈 2e", "🥉 3e"]

    for idx, (_, row_t) in enumerate(top_3.iterrows()):
        with cols_top[idx]:
            st.metric(
                label=f"{medailles[idx]} • {row_t['Chantier']}",
                value=f"{int(row_t['Gain / Jour (€/j)']):,} €/j".replace(",", " "),
                delta=f"Net : {int(row_t['Bénéfice Net (€)']):,} € ({row_t['ROI (%)']:.1f}% ROI)".replace(",", " "),
            )

    st.markdown("---")

    # ==========================================================================
    # --- 4. TABLEAU DE CLASSEMENT GLOBAL ---
    # ==========================================================================
    col_f1, col_f2 = st.columns([1.5, 1])
    with col_f1:
        filtre_nom = st.text_input("🔍 Filtrer les chantiers :", placeholder="Tapez un nom de chantier...").strip()
    with col_f2:
        uniquement_rentables = st.checkbox("🟢 Afficher uniquement les chantiers rentables", value=False)

    df_affiche = df_classement.drop(columns=["ch_id", "details_etapes"]).copy()
    if filtre_nom:
        df_affiche = df_affiche[df_affiche["Chantier"].str.contains(filtre_nom, case=False, na=False)]
    if uniquement_rentables:
        df_affiche = df_affiche[df_affiche["Bénéfice Net (€)"] >= 0]

    st.dataframe(
        df_affiche,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Durée (j)": st.column_config.NumberColumn(format="%.1f j"),
            "Revenus (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Salaires (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Location (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Dépenses (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Bénéfice Net (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Gain / Jour (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
            "ROI (%)": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )

    csv_data = df_affiche.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Exporter ce classement en CSV",
        data=csv_data,
        file_name="classement_rentabilite_simtp.csv",
        mime="text/csv",
    )

    # ==========================================================================
    # --- 5. INSPECTEUR DÉTAILLÉ D'UN CHANTIER ---
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 🔍 Détail Étape par Étape d'un Chantier")

    liste_noms = df_classement["Chantier"].tolist()
    chantier_inspecte = st.selectbox("Choisir un chantier à détailler :", liste_noms)

    if chantier_inspecte:
        ligne_ch = next((x for x in resultats_chantiers if x["Chantier"] == chantier_inspecte), None)
        if ligne_ch and ligne_ch["details_etapes"]:
            st.dataframe(
                pd.DataFrame(ligne_ch["details_etapes"]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Durée (j)": st.column_config.NumberColumn(format="%.1f j"),
                    "Coût Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
                    "Coût Salaires (€)": st.column_config.NumberColumn(format="%.0f €"),
                    "Coût Location (€)": st.column_config.NumberColumn(format="%.0f €"),
                    "Total Étape (€)": st.column_config.NumberColumn(format="%.0f €"),
                },
            )
        else:
            st.caption("Aucune étape enregistrée pour ce chantier.")
