import re
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import database as db


def _extraire_tarif_salarial_moyen(type_contrat="CDI"):
    """Récupère le coût journalier moyen d'un employé depuis Firebase."""
    tarifs_cloud = db.charger_synthese_salaires()
    suffixe = "CDI (Salaire mensuel)" if type_contrat == "CDI" else "CDD (Salaire par jour)"
    valeurs = [
        tarifs_cloud.get(f"Conducteur_{suffixe}"),
        tarifs_cloud.get(f"Chef_{suffixe}"),
        tarifs_cloud.get(f"Ouvrier_{suffixe}"),
    ]
    valeurs_valides = [float(v) for v in valeurs if v is not None and float(v) > 0]
    if valeurs_valides:
        return sum(valeurs_valides) / len(valeurs_valides)
    return 245.0 if type_contrat == "CDI" else 280.0


def _chercher_tarif_engin_cloud(nom_engin, niveau, tarifs_engins):
    """Recherche le prix de location journalier d'un engin dans le cache Firestore."""
    nom_clean = nom_engin.strip()
    correspondances = {
        "camion toupie": "Camion malaxeur",
        "chargeur télescopique": "Chargeur téléscopique",
        "compacteur enrobé": "Compacteur d'enrobé",
        "grue mobile": "Grue mobile",
    }
    nom_officiel = correspondances.get(nom_clean.lower(), nom_clean)

    paliers = ["N1", "N2", "N3", "N4"]
    idx_depart = paliers.index(niveau) if niveau in paliers else 0

    for i in range(idx_depart, len(paliers)):
        cle_test = f"{nom_officiel} ({paliers[i]})"
        if cle_test in tarifs_engins:
            return float(tarifs_engins[cle_test]), True

    return 450.0, False


def parser_html_groupements(html_brut):
    """Extrait les informations du GPE et la liste complète des contrats à 4 phases."""
    soup = BeautifulSoup(html_brut, "html.parser")

    # 1. Extraction de la trésorerie
    tresorerie = "Non détectée"
    header_money = soup.find("div", id="header-breadcrumb-container")
    if header_money and header_money.find("p"):
        chiffres = re.sub(r"[^0-9]", "", header_money.find("p").text)
        if chiffres:
            tresorerie = f"{int(chiffres):,} €".replace(",", " ")

    # 2. Extraction des infos du groupement (Nom, places, membres)
    infos_gpe = {
        "nom": "Aucun groupement détecté",
        "occupation": "0/4 entreprises",
        "membres": [],
        "est_membre": False,
    }
    section_hq = soup.find(class_="cm60-hq")
    if section_hq:
        infos_gpe["est_membre"] = True
        nom_el = section_hq.find(class_="cm60-hq__name")
        meta_el = section_hq.find(class_="cm60-hq__meta")
        if nom_el:
            infos_gpe["nom"] = nom_el.text.strip()
        if meta_el:
            infos_gpe["occupation"] = meta_el.text.strip()

        for item_crew in section_hq.find_all(class_="cm60-crew__item"):
            if "cm60-crew__item--vacant" in item_crew.get("class", []):
                continue
            name_span = item_crew.find(class_="cm60-crew__name")
            role_span = item_crew.find(class_="cm60-crew__role")
            if name_span:
                infos_gpe["membres"].append({
                    "pseudo": name_span.text.strip(),
                    "role": role_span.text.strip() if role_span else "Membre",
                })

    # 3. Extraction des contrats ouverts aux groupements
    contrats = []
    for article in soup.find_all("article", class_="cm60-offer"):
        lvl_el = article.find(class_="cm60-lvl")
        title_el = article.find(class_="cm60-offer__title")
        client_el = article.find(class_="cm60-site__client")
        desc_el = article.find(class_="cm60-offer__desc")

        niveau_requis = lvl_el.text.strip() if lvl_el else "Niveau ?"
        titre = title_el.text.strip() if title_el else "Contrat sans titre"
        client = client_el.text.strip() if client_el else ""
        description = desc_el.text.strip() if desc_el else ""

        # Données chiffrées globales (Marché, Travaux, Délai)
        marche_eur = 0.0
        travaux_j = 0
        delai_j = 0
        for li in article.select("ul.cm60-facts li"):
            label = li.find("span").text.strip().lower() if li.find("span") else ""
            val_txt = li.find("strong").text.strip() if li.find("strong") else ""
            num_txt = re.sub(r"[^0-9]", "", val_txt)
            if "marché" in label and num_txt:
                marche_eur = float(num_txt)
            elif "travaux" in label and num_txt:
                travaux_j = int(num_txt)
            elif "délai" in label and num_txt:
                delai_j = int(num_txt)

        # Extraction des 4 phases
        phases = []
        for li_phase in article.select("ol.cm60-phases li.cm60-phase"):
            num_el = li_phase.find(class_="cm60-phase__num")
            name_el = li_phase.find(class_="cm60-phase__name")
            meta_el = li_phase.find(class_="cm60-phase__meta")
            pay_el = li_phase.find(class_="cm60-phase__pay")

            num_phase = int(num_el.text.strip()) if num_el and num_el.text.strip().isdigit() else len(phases) + 1
            nom_phase = name_el.text.strip() if name_el else f"Phase {num_phase}"
            pay_txt = re.sub(r"[^0-9]", "", pay_el.text) if pay_el else "0"
            remuneration = float(pay_txt) if pay_txt else 0.0

            duree_j = 1
            nb_employes = 0
            if meta_el:
                m_j = re.search(r"(\d+)\s*j", meta_el.text)
                m_emp = re.search(r"(\d+)\s*employ", meta_el.text)
                if m_j:
                    duree_j = int(m_j.group(1))
                if m_emp:
                    nb_employes = int(m_emp.group(1))

            engins_liste = []
            for chip in li_phase.find_all(class_="cm60-chip"):
                chip_txt = chip.get_text(" ", strip=True)
                m_chip = re.match(r"(\d+)\s*[×x]\s*(.+?)\s+(N\d+)", chip_txt, re.IGNORECASE)
                if m_chip:
                    engins_liste.append({
                        "qte": int(m_chip.group(1)),
                        "type": m_chip.group(2).strip(),
                        "niveau": m_chip.group(3).upper(),
                    })

            phases.append({
                "num": num_phase,
                "nom": nom_phase,
                "duree_j": duree_j,
                "nb_employes": nb_employes,
                "engins": engins_liste,
                "remuneration": remuneration,
            })

        contrats.append({
            "titre": titre,
            "niveau": niveau_requis,
            "client": client,
            "description": description,
            "marche_eur": marche_eur,
            "travaux_j": travaux_j,
            "delai_j": delai_j,
            "phases": phases,
        })

    return tresorerie, infos_gpe, contrats


def afficher_onglet_groupements():
    # Zone d'importation HTML + paramètres de simulation
    col_html, col_param = st.columns([2, 1])

    with col_html:
        html_gpe = st.text_area(
            "📋 Collez le code source HTML de la page 'Groupements d'entreprises' :",
            height=140,
            placeholder="<!DOCTYPE html> ... </html>",
            key="html_input_gpe_page",
        )

    with col_param:
        st.markdown("#### ⚙️ Paramètres de calcul")
        type_contrat_rh = st.radio(
            "Type de contrats des employés :",
            ["CDI", "CDD"],
            horizontal=True,
            key="gpe_type_contrat_rh",
        )
        mode_flotte = st.radio(
            "Situation de votre flotte d'engins :",
            ["Location 100% des engins", "Engins déjà possédés (0 € loc.)"],
            key="gpe_mode_flotte",
        )

    if not html_gpe.strip():
        st.info(
            "💡 **Mode d'emploi :** Rendez-vous sur la page **Groupements d'entreprises** de Sim-TP, "
            "faites `Ctrl + U` puis `Ctrl + A` / `Ctrl + C`, et collez le code ci-dessus."
        )
        return

    tresorerie, infos_gpe, contrats = parser_html_groupements(html_gpe)

    if not contrats and not infos_gpe["est_membre"]:
        st.error("❌ Aucune donnée de groupement valide détectée dans le code collé.")
        return

    # ==========================================================================
    # --- 1. FICHE D'IDENTITÉ DU GROUPEMENT ---
    # ==========================================================================
    st.markdown("---")
    c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
    with c_kpi1:
        st.metric("🏢 Groupement", infos_gpe["nom"])
    with c_kpi2:
        st.metric("👥 Effectif GPE", infos_gpe["occupation"])
    with c_kpi3:
        st.metric("💰 Trésorerie Entreprise", tresorerie)
    with c_kpi4:
        st.metric("📜 Contrats Disponibles", f"{len(contrats)} contrat(s)")

    if infos_gpe["membres"]:
        membres_txt = "  •  ".join([f"**{m['pseudo']}** ({m['role']})" for m in infos_gpe["membres"]])
        st.caption(f"Entreprises membres détectées : {membres_txt}")

    if "1/4" in infos_gpe["occupation"]:
        st.warning("⚠️ **Condition Sim-TP :** Invitez au moins 1 autre entreprise (minimum 2/4) pour pouvoir signer un contrat de groupement.")

    # ==========================================================================
    # --- 2. ANALYSE FINANCIÈRE COMPARATIVE DES CONTRATS ---
    # ==========================================================================
    tarif_jour_employe = _extraire_tarif_salarial_moyen(type_contrat_rh)
    tarifs_engins_cloud = db.charger_tarifs_engins_unifies()
    louer_engins = mode_flotte == "Location 100% des engins"

    st.markdown("---")
    st.markdown("### 📊 Classement des Contrats par Rentabilité Nette")
    st.caption(f"Calculé avec 0 € de matériaux (fournis par le client) • Salaire moyen : {tarif_jour_employe:.2f} €/j ({type_contrat_rh})")

    resume_contrats = []
    contrats_enrichis = {}

    for c in contrats:
        ca_total = c["marche_eur"]
        cout_rh_contrat = 0.0
        cout_loc_contrat = 0.0
        phases_detaillees = []

        for ph in c["phases"]:
            duree = ph["duree_j"]
            cout_rh_ph = ph["nb_employes"] * tarif_jour_employe * duree
            cout_loc_ph = 0.0
            engins_str_list = []

            for eng in ph["engins"]:
                px_j, trouve = _chercher_tarif_engin_cloud(eng["type"], eng["niveau"], tarifs_engins_cloud)
                if louer_engins:
                    cout_loc_ph += eng["qte"] * px_j * duree
                tag_px = "" if trouve else "*"
                engins_str_list.append(f"{eng['qte']}× {eng['type']} ({eng['niveau']}{tag_px})")

            charges_ph = cout_rh_ph + cout_loc_ph
            benef_ph = ph["remuneration"] - charges_ph
            gain_j_ph = benef_ph / duree if duree > 0 else 0.0

            cout_rh_contrat += cout_rh_ph
            cout_loc_contrat += cout_loc_ph

            phases_detaillees.append({
                "Phase": f"Phase {ph['num']} : {ph['nom']}",
                "Durée (j)": duree,
                "Employés": ph["nb_employes"],
                "Engins Requis": ", ".join(engins_str_list),
                "Paie Phase (€)": ph["remuneration"],
                "Coût Salaires (€)": round(cout_rh_ph, 0),
                "Coût Location (€)": round(cout_loc_ph, 0),
                "Bénéfice Net (€)": round(benef_ph, 0),
                "Gain / Jour (€/j)": round(gain_j_ph, 0),
            })

        charges_totales = cout_rh_contrat + cout_loc_contrat
        benefice_net_contrat = ca_total - charges_totales
        gain_jour_contrat = benefice_net_contrat / c["travaux_j"] if c["travaux_j"] > 0 else 0.0
        roi_contrat = (benefice_net_contrat / charges_totales * 100) if charges_totales > 0 else 0.0

        resume_contrats.append({
            "Niveau": c["niveau"],
            "Contrat GPE": c["titre"],
            "Durée Cumulée": f"{c['travaux_j']} j (Délai {c['delai_j']} j)",
            "Marché Total (€)": ca_total,
            "Charges Totales (€)": round(charges_totales, 0),
            "Bénéfice Net (€)": round(benefice_net_contrat, 0),
            "Gain / Jour (€/j)": round(gain_jour_contrat, 0),
            "ROI (%)": round(roi_contrat, 1),
        })
        contrats_enrichis[c["titre"]] = {
            "meta": c,
            "phases_df": pd.DataFrame(phases_detaillees),
            "benefice_net": benefice_net_contrat,
            "gain_jour": gain_jour_contrat,
        }

    df_resume = pd.DataFrame(resume_contrats).sort_values(by="Gain / Jour (€/j)", ascending=False)
    st.dataframe(
        df_resume,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Marché Total (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Charges Totales (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Bénéfice Net (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Gain / Jour (€/j)": st.column_config.NumberColumn(format="%.0f €/j"),
            "ROI (%)": st.column_config.NumberColumn(format="%.1f %%"),
        },
    )
    st.caption("*Les engins marqués d'un astérisque (ex. Grue mobile) utilisent un tarif estimé s'ils ne sont pas encore dans votre catalogue Firebase.*")

    # ==========================================================================
    # --- 3. DÉTAIL PHASE PAR PHASE & RÉPARTITION ENTRE MEMBRES ---
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 🔍 Détail des 4 Phases & Répartition Entre Associés")

    titres_ordonnes = df_resume["Contrat GPE"].tolist()
    contrat_choisi = st.selectbox("Sélectionner un contrat à inspecter :", titres_ordonnes)

    if contrat_choisi and contrat_choisi in contrats_enrichis:
        bloc = contrats_enrichis[contrat_choisi]
        meta_c = bloc["meta"]
        df_phases = bloc["phases_df"].copy()

        st.info(f"**Client :** {meta_c['client']} — {meta_c['description']}")

        pseudos_membres = [m["pseudo"] for m in infos_gpe["membres"]]
        while len(pseudos_membres) < 4:
            pseudos_membres.append(f"Entreprise {len(pseudos_membres) + 1}")

        df_phases["Entreprise Affectée"] = pseudos_membres[: len(df_phases)]

        df_phases_edite = st.data_editor(
            df_phases,
            use_container_width=True,
            hide_index=True,
            key=f"editor_phases_gpe_{contrat_choisi}",
            column_config={
                "Phase": st.column_config.TextColumn(disabled=True),
                "Durée (j)": st.column_config.NumberColumn(format="%d j", disabled=True),
                "Employés": st.column_config.NumberColumn(disabled=True),
                "Engins Requis": st.column_config.TextColumn(disabled=True, width="large"),
                "Paie Phase (€)": st.column_config.NumberColumn(format="%.0f €", disabled=True),
                "Coût Salaires (€)": st.column_config.NumberColumn(format="%.0f €", disabled=True),
                "Coût Location (€)": st.column_config.NumberColumn(format="%.0f €", disabled=True),
                "Bénéfice Net (€)": st.column_config.NumberColumn(format="%.0f €", disabled=True),
                "Gain / Jour (€/j)": st.column_config.NumberColumn(format="%.0f €/j", disabled=True),
                "Entreprise Affectée": st.column_config.SelectboxColumn(
                    "Attribuer à",
                    options=pseudos_membres,
                    required=True,
                ),
            },
        )

        st.markdown("#### 💸 Bilan Prévisionnel par Entreprise du Groupement")
        bilan_membres = (
            df_phases_edite.groupby("Entreprise Affectée", as_index=False)
            .agg({
                "Durée (j)": "sum",
                "Paie Phase (€)": "sum",
                "Bénéfice Net (€)": "sum",
            })
            .sort_values(by="Bénéfice Net (€)", ascending=False)
        )

        cols_bilan = st.columns(len(bilan_membres))
        for idx, (_, row_m) in enumerate(bilan_membres.iterrows()):
            with cols_bilan[idx]:
                st.metric(
                    label=f"🏢 {row_m['Entreprise Affectée']} ({int(row_m['Durée (j)'])} j)",
                    value=f"{int(row_m['Bénéfice Net (€)']):,} €".replace(",", " "),
                    delta=f"CA : {int(row_m['Paie Phase (€)']):,} €".replace(",", " "),
                )
