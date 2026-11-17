import re
import math
import unicodedata
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import database as db


def _normaliser_texte(texte):
    """Supprime les accents et met en minuscules pour des comparaisons fiables."""
    if not texte:
        return ""
    texte_nfd = unicodedata.normalize("NFD", str(texte).lower())
    return "".join(c for c in texte_nfd if unicodedata.category(c) != "Mn")


def _extraire_tarifs_cdi():
    """Récupère les tarifs journaliers CDI depuis synthese_grille_tarifaire avec repli sécurisé."""
    tarifs_cloud = db.charger_synthese_salaires()
    px_cond = float(tarifs_cloud.get("Conducteur_CDI (Salaire mensuel)", 244.91))
    px_chef = float(tarifs_cloud.get("Chef_CDI (Salaire mensuel)", 239.45))
    px_ouv = float(tarifs_cloud.get("Ouvrier_CDI (Salaire mensuel)", 256.00))
    return px_cond, px_chef, px_ouv


def afficher_onglet_suivi_contrats():
    col_import1, col_import2 = st.columns(2)

    with col_import1:
        html_contrats = st.text_area(
            "1️⃣ Code HTML 'Mes contrats en cours' :",
            height=140,
            placeholder="Collez ici le code source de https://sim-tp.com",
            key="html_contrats_cross",
        )

    with col_import2:
        html_stockage = st.text_area(
            "2️⃣ Code HTML 'Mon aire de stockage' :",
            height=140,
            placeholder="Collez ici le code source de https://sim-tp.com",
            key="html_stockage_cross",
        )

    if not html_contrats.strip() and not html_stockage.strip():
        st.info("💡 Collez le code source HTML de vos **Contrats en cours** (et optionnellement de votre **Aire de stockage**) pour lancer l'analyse.")
        return

    traduction_cles = {
        "sable": "Sable",
        "terre": "Terre",
        "enrobe": "Enrobé",
        "armature": "Armature",
        "tole": "Tôle",
        "beton": "Béton",
        "panneaux": "Panneaux",
        "tuyaux": "Tuyaux",
        "canalisation": "Canalisations",
        "poutre": "Poutres",
    }

    prix_coops_mini = db.charger_materiaux_config()
    px_cond, px_chef, px_ouvrier = _extraire_tarifs_cdi()

    stocks_disponibles = {v: 0.0 for v in traduction_cles.values()}
    besoins_cumules = {v: 0.0 for v in traduction_cles.values()}
    info_capacite_aire = None

    # ==========================================================================
    # --- ÉTAPE A : EXTRACTION DES STOCKS DE L'AIRE DE STOCKAGE ---
    # ==========================================================================
    stocks_extraits = False
    if html_stockage.strip():
        try:
            soup_stock = BeautifulSoup(html_stockage, "html.parser")

            # Extraction de la jauge d'occupation (ex: 5 219 / 10 000 tonnes)
            cm31_title = soup_stock.find(class_="cm31-title")
            if cm31_title:
                info_capacite_aire = cm31_title.get_text(" ", strip=True)

            for chip in soup_stock.find_all(class_="custom-chip"):
                full_w_span = chip.find(class_="full-w")
                if full_w_span:
                    text_spans = full_w_span.find_all("span")
                    if len(text_spans) >= 2:
                        nom_mat_clean = _normaliser_texte(text_spans[0].text.strip())
                        qte_brute = re.sub(r"[^0-9]", "", text_spans[1].text)
                        valeur_num = float(qte_brute) if qte_brute else 0.0

                        for cle_sans_accent, nom_officiel in traduction_cles.items():
                            if cle_sans_accent in nom_mat_clean:
                                stocks_disponibles[nom_officiel] = valeur_num
                                break
            stocks_extraits = True
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse de l'aire de stockage : {e}")

    # ==========================================================================
    # --- ÉTAPE B : EXTRACTION DES CONTRATS EN COURS ---
    # ==========================================================================
    if html_contrats.strip():
        try:
            soup_contrats = BeautifulSoup(html_contrats, "html.parser")

            # Extraction de la trésorerie
            money_container = soup_contrats.find("div", id="header-breadcrumb-container")
            tresorerie_affiche = "Inconnue"
            if money_container and money_container.find("p"):
                tresorerie_chiffre = re.sub(r"[^0-9]", "", money_container.find("p").text)
                if tresorerie_chiffre:
                    tresorerie_affiche = f"{int(tresorerie_chiffre):,} €".replace(",", " ")

            contrats_list = []
            items = soup_contrats.find_all(class_="js-accordion-item")

            for item in items:
                nom = item.get("data-nom", "Chantier Inconnu")
                revenu_brut = item.get("data-revenu", "0")
                revenu = float(revenu_brut) if revenu_brut.isdigit() else 0.0

                # ID Contrat
                form_annuler = item.find("form", action=lambda x: x and "annuler-contrat" in x)
                id_contrat = "—"
                if form_annuler:
                    input_id = form_annuler.find("input", {"name": "id"})
                    if input_id:
                        id_contrat = input_id.get("value", "—")

                # Extraction des paragraphes internes
                materiaux_texte = "Aucun"
                surface_texte = "—"
                nb_etapes_texte = "—"
                temps_restant_global = ""

                for p in item.find_all("p"):
                    text = p.get_text(" ", strip=True)
                    if "Matériaux nécessaires" in text:
                        materiaux_texte = text.split("Matériaux nécessaires :")[-1].strip()
                    elif "Surface du chantier" in text:
                        surface_texte = text.split("Surface du chantier :")[-1].strip()
                    elif "Nombre d'étapes" in text:
                        nb_etapes_texte = text.split("Nombre d'étapes :")[-1].split("-")[0].strip()
                    elif "Temps restant" in text:
                        temps_restant_global = text.split("Temps restant :")[-1].strip()

                # Détection précise : étape en cours vs contrat pas encore démarré
                status_card = item.find(class_="basic-card")
                if status_card:
                    statut = f"🟢 {status_card.get_text(' ', strip=True)}"
                    est_demarre = True
                else:
                    statut = f"⏸️ Non démarré (Reste {temps_restant_global})" if temps_restant_global else "⏸️ Non démarré"
                    est_demarre = False

                # Calcul jours dus sur l'étape en cours
                jours_dus = 1.0 if est_demarre else 0.0
                if est_demarre:
                    match_jours = re.search(r"dans\s*(\d+)\s*jour", statut.lower())
                    if match_jours:
                        jours_dus = max(1.0, math.ceil(float(match_jours.group(1))))

                # Estimation de l'équipe affectée
                nom_norm = _normaliser_texte(nom)
                nb_cond, nb_chef, nb_ouv = 1.0, 0.0, 0.0
                txt_equipe = "1 Cond."
                if "tuyaux" in nom_norm or "assainissement" in nom_norm:
                    nb_cond, nb_chef, nb_ouv = 1.0, 1.0, 2.0
                    txt_equipe = "1 Cond. / 1 Chef / 2 Ouv."
                elif "hangar" in nom_norm or "batiment" in nom_norm:
                    nb_cond, nb_chef, nb_ouv = 1.0, 1.0, 3.0
                    txt_equipe = "1 Cond. / 1 Chef / 3 Ouv."

                cout_salaires_contrat = ((nb_cond * px_cond) + (nb_chef * px_chef) + (nb_ouv * px_ouvrier)) * jours_dus

                # Calcul du coût des matériaux requis pour l'étape suivante
                cout_mats_contrat = 0.0
                if "aucun" not in materiaux_texte.lower():
                    texte_clean = _normaliser_texte(materiaux_texte)
                    for cle_reg, nom_officiel in traduction_cles.items():
                        if cle_reg in texte_clean:
                            pattern = re.compile(rf"{cle_reg}.*?(\d[\d\s]*)", re.IGNORECASE)
                            match = pattern.search(texte_clean)
                            if match:
                                val_requis = float(match.group(1).replace(" ", ""))
                                besoins_cumules[nom_officiel] += val_requis
                                prix_u = float(prix_coops_mini.get(nom_officiel, 0.0))
                                cout_mats_contrat += val_requis * prix_u

                marge_nette_prevue = revenu - cout_mats_contrat - cout_salaires_contrat

                contrats_list.append({
                    "ID": f"#{id_contrat}",
                    "Nom du Chantier": nom,
                    "Étapes": nb_etapes_texte,
                    "Surface": surface_texte,
                    "Équipe": txt_equipe,
                    "Chiffre d'Affaires (€)": revenu,
                    "Coût Matériaux (€)": cout_mats_contrat,
                    "Salaires Étape (€)": round(cout_salaires_contrat, 0),
                    "Marge Estimée (€)": round(marge_nette_prevue, 0),
                    "Matériaux Requis": materiaux_texte,
                    "Statut": statut,
                })

            if contrats_list:
                df_contrats = pd.DataFrame(contrats_list)
                total_ca = df_contrats["Chiffre d'Affaires (€)"].sum()
                total_cout_mats = df_contrats["Coût Matériaux (€)"].sum()
                total_salaires = df_contrats["Salaires Étape (€)"].sum()
                total_marge_nette = df_contrats["Marge Estimée (€)"].sum()

                st.markdown("---")
                c_k1, c_k2, c_k3, c_k4, c_k5 = st.columns(5)
                with c_k1:
                    st.metric("🏦 Trésorerie", tresorerie_affiche)
                with c_k2:
                    st.metric("💰 CA Contrats Signés", f"{total_ca:,.0f}".replace(",", " ") + " €")
                with c_k3:
                    st.metric("🧱 Budget Matériaux", f"{total_cout_mats:,.0f}".replace(",", " ") + " €")
                with c_k4:
                    st.metric("👥 Salaires Étape Active", f"{total_salaires:,.0f}".replace(",", " ") + " €")
                with c_k5:
                    st.metric("📈 Marge Nette Estimée", f"{total_marge_nette:,.0f}".replace(",", " ") + " €")

                st.markdown(f"### 🏗️ Chantiers Signés ({len(contrats_list)} détectés)")
                st.dataframe(
                    df_contrats,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Chiffre d'Affaires (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Coût Matériaux (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Salaires Étape (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Marge Estimée (€)": st.column_config.NumberColumn(format="%.0f €"),
                        "Matériaux Requis": st.column_config.TextColumn(width="large"),
                        "Statut": st.column_config.TextColumn(width="large"),
                    },
                )
            else:
                st.warning("⚠️ Aucun contrat valide trouvé dans le premier bloc HTML.")

        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse des contrats : {e}")

    # ==========================================================================
    # --- ÉTAPE C : COMPARATEUR LOGISTIQUE (BESOINS VS STOCKS DE L'AIRE) ---
    # ==========================================================================
    if html_contrats.strip() or stocks_extraits:
        st.markdown("---")
        st.markdown("### 📊 Bilan Logistique : Besoins Contrats vs Aire de Stockage")

        if info_capacite_aire:
            st.caption(f"📦 {info_capacite_aire}")

        if not stocks_extraits:
            st.info("💡 Collez également le code HTML de votre **Aire de stockage** (en haut à droite) pour calculer automatiquement vos quantités manquantes.")

        lignes_comparatif = []
        cout_total_achat_coop = 0.0

        for mat_nom in traduction_cles.values():
            besoin = besoins_cumules[mat_nom]
            stock = stocks_disponibles[mat_nom]
            ecart = stock - besoin
            prix_unitaire_coop = float(prix_coops_mini.get(mat_nom, 0.0))

            if besoin > 0 or stock > 0:
                manquant = abs(ecart) if ecart < 0 else 0.0
                cout_achat_ligne = manquant * prix_unitaire_coop
                cout_total_achat_coop += cout_achat_ligne

                status_icone = "✅ Stock suffisant" if ecart >= 0 else f"🚨 Manque {int(manquant)}"

                lignes_comparatif.append({
                    "Matériau": mat_nom,
                    "Besoin Contrats": besoin,
                    "En Réserve (Aire)": stock,
                    "Écart": ecart,
                    "Prix Mini Coop": prix_unitaire_coop,
                    "Reste à Payer (€)": cout_achat_ligne,
                    "Statut": status_icone,
                })

        if lignes_comparatif:
            df_comparatif = pd.DataFrame(lignes_comparatif)
            st.dataframe(
                df_comparatif,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Besoin Contrats": st.column_config.NumberColumn(format="%.0f"),
                    "En Réserve (Aire)": st.column_config.NumberColumn(format="%.0f"),
                    "Écart": st.column_config.NumberColumn(format="%+.0f"),
                    "Prix Mini Coop": st.column_config.NumberColumn(format="%.0f €"),
                    "Reste à Payer (€)": st.column_config.NumberColumn(format="%.0f €"),
                },
            )

            if stocks_extraits:
                c_res1, c_res2 = st.columns(2)
                with c_res1:
                    st.metric(
                        label="💰 Reste à débourser en coopératives",
                        value=f"{cout_total_achat_coop:,.0f}".replace(",", " ") + " €",
                    )
                with c_res2:
                    if cout_total_achat_coop > 0:
                        st.error("🚨 Des matériaux manquent pour vos contrats ! Consultez la colonne 'Reste à Payer (€)'.")
                    else:
                        st.success("🎉 Vos stocks actuels couvrent 100 % des besoins détectés !")
        else:
            st.caption("Aucun besoin ni stock détecté.")
