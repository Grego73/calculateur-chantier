import math
import streamlit as st
import pandas as pd
import database as db


def _extraire_tarifs_cdi_cache():
    """Récupère les tarifs journaliers CDI depuis le cache de database.py."""
    tarifs_cloud = db.charger_synthese_salaires()
    px_cond = float(tarifs_cloud.get("Conducteur_CDI (Salaire mensuel)", 244.91))
    px_chef = float(tarifs_cloud.get("Chef_CDI (Salaire mensuel)", 239.45))
    px_ouv = float(tarifs_cloud.get("Ouvrier_CDI (Salaire mensuel)", 256.00))
    return px_cond, px_chef, px_ouv


def afficher_onglet_consulter_modeles():
    st.markdown("### 🗂️ Classement des Modèles NoSQL par Rentabilité Journalière")
    st.caption("Fiches techniques classées par ordre décroissant selon le gain net par jour réel.")

    catalogue_chantiers = db.charger_catalogue_chantiers()
    MATERIAUX_DB = db.charger_materiaux_config()

    if not catalogue_chantiers:
        st.info("💡 Le catalogue des modèles pré-configurés est actuellement vide.")
        return

    recherche = st.text_input("🔍 Rechercher un modèle par son nom :", value="").strip()

    traduction_mats = {
        "sable": "Sable", "terre": "Terre", "enrobe": "Enrobé", "beton": "Béton",
        "armature": "Armature", "tole": "Tôle", "poutres": "Poutres",
        "tuyaux": "Tuyaux", "canalisations": "Canalisations", "panneaux": "Panneaux"
    }

    px_cond, px_chef, px_ouvrier = _extraire_tarifs_cdi_cache()

    # ==========================================================================
    # --- PHASE 1 : PRÉ-CALCUL FINANCIER DE TOUS LES MODÈLES ---
    # ==========================================================================
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
                        cout_mats_total += qte_val * prix_unitaire

        total_charges = cout_rh_total + cout_mats_total
        marge_net = revenus - total_charges
        roi_global = (marge_net / total_charges * 100) if total_charges > 0 else 0.0

        duree_totale_jours = jours_cumules if jours_cumules > 0 else float(j + (h / 24.0) + (m / 1440.0))
        roi_par_jour = marge_net / duree_totale_jours if duree_totale_jours > 0 else 0.0

        liste_chantiers_calcules.append({
            "ch_id": ch_id,
            "ch_data": ch_data,
            "nom_modele": nom_modele,
            "revenus": revenus,
            "jours_globaux_indic": j,
            "etapes": etapes,
            "cumul_cout_rh": cout_rh_total,
            "cumul_cout_mats": cout_mats_total,
            "total_charges": total_charges,
            "marge_net": marge_net,
            "roi_global": roi_global,
            "roi_par_jour": roi_par_jour,
            "duree_totale_jours": duree_totale_jours,
        })

    if not liste_chantiers_calcules:
        st.warning("Aucun modèle ne correspond à votre recherche.")
        return

    liste_chantiers_ordonnes = sorted(liste_chantiers_calcules, key=lambda x: x["roi_par_jour"], reverse=True)

    # ==========================================================================
    # --- PHASE 2 : TABLEAU SYNTHÉTIQUE DE COMPARAISON RAPIDE ---
    # ==========================================================================
    df_synthese = pd.DataFrame([
        {
            "Modèle d'Ouvrage": x["nom_modele"],
            "Revenus (€)": x["revenus"],
            "Durée Étapes (j)": round(x["duree_totale_jours"], 1),
            "Salaires CDI (€)": round(x["cumul_cout_rh"], 0),
            "Matériaux (€)": round(x["cumul_cout_mats"], 0),
            "Bénéfice Net (€)": round(x["marge_net"], 0),
            "Gain / Jour (€/j)": round(x["roi_par_jour"], 0),
            "ROI (%)": round(x["roi_global"], 1),
        }
        for x in liste_chantiers_ordonnes
    ])

    st.dataframe(
        df_synthese,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenus (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Durée Étapes (j)": st.column_config.NumberColumn(format="%.1f j"),
            "Salaires CDI (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Bénéfice Net (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Gain / Jour (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
            "ROI (%)": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )

    st.markdown("---")
    st.markdown("#### 📋 Fiches Détaillées par Modèle")

    # ==========================================================================
    # --- PHASE 3 : FICHES DÉTAILLÉES ENCARTÉES ---
    # ==========================================================================
    for item in liste_chantiers_ordonnes:
        nom_modele = item["nom_modele"]

        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([4.5, 2, 1.5, 2.5, 2])
            with col1:
                st.markdown(f"#### 🏗️ {nom_modele}")
            with col2:
                st.markdown(f"**Revenus :** `{item['revenus']:,.0f} €`".replace(",", " "))
            with col3:
                st.markdown(f"**Durée :** `{item['duree_totale_jours']:.1f} j`")
            with col4:
                st.markdown(f"**Gain/j :** `{item['roi_par_jour']:,.0f} €/j`".replace(",", " "))
            with col5:
                if st.button("🚀 Simuler", key=f"btn_sim_{item['ch_id']}", use_container_width=True):
                    st.session_state["modele_preselectionne"] = item["ch_id"]
                    st.toast(f"'{nom_modele}' chargé dans l'onglet Calculateur !", icon="✅")

            with st.expander("Voir le détail technique des étapes et charges", expanded=False):
                if not item["etapes"]:
                    st.caption("⚪ Aucune étape technique enregistrée pour ce modèle.")
                else:
                    for etape in item["etapes"]:
                        num_e = etape.get("num_etape", 1)
                        nom_etape = etape.get("nom_etape", "Étape sans nom")
                        duree_j = float(etape.get("duree_jours", 1.0))
                        jours_forfait = float(math.ceil(duree_j))

                        cond = float(etape.get("jh_cond", 0.0))
                        chef = float(etape.get("jh_chef", 0.0))
                        ouv = float(etape.get("jh_ouvrier", 0.0))
                        cout_rh_etape = (cond * px_cond + chef * px_chef + ouv * px_ouvrier) * jours_forfait

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
                                    mats_affiches.append(
                                        f"- {nom_officiel_db} : `{int(qte_val)}` *({prix_unitaire:.0f} €/u = {cout_ligne_mat:,.0f} €)*".replace(",", " ")
                                    )

                        engins = etape.get("engins", [])

                        st.markdown(f"**🔹 Étape {num_e:02d} : {nom_etape}** *({duree_j} j réel ➔ {int(jours_forfait)} j forfaitisés)*")
                        c_rh, c_mats, c_engins = st.columns(3)

                        with c_rh:
                            st.markdown("**👥 Équipe (CDI) :**")
                            st.markdown(f"- Cond : `{int(cond)}` *({px_cond:.2f}€/j)* | Chef : `{int(chef)}` | Ouv : `{int(ouv)}`")
                            st.markdown(f"💰 **Salaires :** `{cout_rh_etape:,.2f} €`".replace(",", " "))

                        with c_mats:
                            st.markdown("**🧱 Matériaux :**")
                            if mats_affiches:
                                for item_txt in mats_affiches:
                                    st.markdown(item_txt)
                                st.markdown(f"💰 **Matériaux :** `{cout_mats_etape:,.0f} €`".replace(",", " "))
                            else:
                                st.caption("Aucun matériau requis (0 €)")

                        with c_engins:
                            st.markdown("**🚜 Engins requis :**")
                            if engins:
                                for eng in engins:
                                    st.markdown(f"- {eng.get('type')} `({eng.get('niveau')})`")
                            else:
                                st.caption("Aucun engin requis")

                        st.markdown("---")

                # Synthèse globale du modèle
                cb1, cb2, cb3, cb4 = st.columns(4)
                with cb1:
                    st.metric("👥 Salaires CDI", f"{item['cumul_cout_rh']:,.0f} €".replace(",", " "))
                with cb2:
                    st.metric("🧱 Matériaux", f"{item['cumul_cout_mats']:,.0f} €".replace(",", " "))
                with cb3:
                    st.metric("📊 ROI Global", f"{item['roi_global']:.1f} %")
                with cb4:
                    st.metric("⚡ Gain Net / Jour", f"{item['roi_par_jour']:,.0f} €/j".replace(",", " "))

                col_alerte1, col_alerte2 = st.columns(2)
                with col_alerte1:
                    if item["marge_net"] >= 0:
                        st.success(f"🟢 **Marge nette :** **{item['marge_net']:,.0f} €** ({item['duree_totale_jours']:.1f} j)".replace(",", " "))
                    else:
                        st.error(f"🔴 **Modèle déficitaire :** Perte de **{abs(item['marge_net']):,.0f} €**".replace(",", " "))

                with col_alerte2:
                    temps_chantier = float(item["jours_globaux_indic"])
                    temps_etapes = float(item["duree_totale_jours"])
                    if temps_etapes < temps_chantier:
                        st.success(f"🟢 **Planning optimisé :** Étapes ({temps_etapes:.1f} j) < Global ({temps_chantier:.1f} j)")
                    elif temps_etapes == temps_chantier:
                        st.info(f"🔵 **Planning exact :** Étapes ({temps_etapes:.1f} j) = Global ({temps_chantier:.1f} j)")
                    else:
                        st.warning(f"⚠️ **Alerte Temps :** Étapes ({temps_etapes:.1f} j) > Global ({temps_chantier:.1f} j)")
