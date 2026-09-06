# Fichier complet, nettoyé et validé pour : coops/calculs.py
import pandas as pd
import io
import requests
import streamlit as st

def compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits):
    """Calcule le grand livre des comptes associés basé sur les règles fixes de la coop."""
    compta = {
        m: {
            "Capital Départ (€)": float(dict_capitaux.get(m, 0.0)),
            "Réinvestissements (€)": 0.0,
            "Réappro Matériaux (u)": 0.0, 
            "Consommation Interne (u)": 0.0, 
            "Bénéfices Générés (€)": 0.0,
            "Score d'Apport Total": float(dict_capitaux.get(m, 0.0))
        } for m in membres_inscrits
    }

    for fl in liste_flux:
        user = fl.get("joueur")
        if user not in compta: continue
        
        t_mouv = fl.get("type")
        cash = fl.get("apport_cash", 0.0)
        mats_qte = sum(fl.get("materiaux", {}).values())

        if t_mouv == "REINVESTISSEMENT_CASH":
            compta[user]["Réinvestissements (€)"] += cash
            compta[user]["Score d'Apport Total"] += (cash / 100.0)
        elif t_mouv == "REAPPROVISIONNEMENT":
            compta[user]["Réappro Matériaux (u)"] += mats_qte
            compta[user]["Score d'Apport Total"] += 0.0
        elif t_mouv == "ACHAT_INTERNE" or t_mouv == "ACHAT_EXTERNE":
            compta[user]["Consommation Interne (u)"] += mats_qte
            benefice_genere = mats_qte * 1.0
            compta[user]["Bénéfices Générés (€)"] += benefice_genere
            compta[user]["Score d'Apport Total"] += benefice_genere
    return compta

def appliquer_parts_et_primes(df_coop):
    """Détermine les pourcentages de dividendes et le rôle de Responsable Logistique."""
    id_meilleur_logisticiens = df_coop["Réappro Matériaux (u)"].idxmax() if df_coop["Réappro Matériaux (u)"].sum() > 0 else None
    total_points_coop = df_coop["Score d'Apport Total"].sum()
    
    if total_points_coop > 0:
        df_coop["Distribution Bénéfice (%)"] = (df_coop["Score d'Apport Total"] / total_points_coop) * 100
    else:
        df_coop["Distribution Bénéfice (%)"] = 100.0 / len(df_coop) if len(df_coop) > 0 else 0.0

    def calculer_prime_et_statut(row):
        if row.name == id_meilleur_logisticiens:
            return "🏆 Responsable Logistique (+5% Prime)"
        return "👷 Collaborateur"
        
    df_coop["Rôle cette semaine"] = df_coop.apply(calculer_prime_et_statut, axis=1)
    return df_coop, id_meilleur_logisticiens

def generer_excel_distribution_paye(df_coop, benefice_total_caisse, id_logisticien):
    """Génère le fichier Excel stylisé calculant automatiquement l'argent dû."""
    from openpyxl.styles import Font, PatternFill, Alignment
    lignes_paye = []
    benefice_restant = benefice_total_caisse
    
    prime_logistique_globale = 0.0
    if id_logisticien and benefice_total_caisse > 0:
        prime_logistique_globale = benefice_total_caisse * 0.05
        benefice_restant = benefice_total_caisse - prime_logistique_globale

    for _, row in df_coop.iterrows():
        pseudo = row["Pseudo Membre"]
        pct_dividende = row["Distribution Bénéfice (%)"]
        argent_dividendes = (pct_dividende / 100.0) * benefice_restant
        prime_lo = prime_logistique_globale if pseudo == id_logisticien else 0.0
        
        lignes_paye.append({
            "👤 Pseudo Joueur": pseudo,
            "🎖️ Statut Semaine": row["Rôle cette semaine"],
            "📊 Part Dividende (%)": f"{pct_dividende:.2f} %",
            "💰 Gain Dividendes (€)": round(argent_dividendes, 2),
            "👑 Prime Logistique (+5%)": round(prime_lo, 2),
            "💸 TOTAL NET À PAYER (€)": round(argent_dividendes + prime_lo, 2)
        })
        
    df_paye = pd.DataFrame(lignes_paye)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_paye.to_excel(writer, index=False, sheet_name="Distribution de la Paye")
        workbook = writer.book
        worksheet = writer.sheets["Distribution de la Paye"]
        
        fill_header = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        
        for col_idx in range(1, 7):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.fill = fill_header; cell.font = font_header; cell.alignment = Alignment(horizontal="center")
            
        fill_total = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        font_total = Font(name="Calibri", size=11, bold=True, color="15803D")
        
        for row_idx in range(2, len(df_paye) + 2):
            worksheet.cell(row=row_idx, column=4).number_format = '#,##0.00 "€"'
            worksheet.cell(row=row_idx, column=5).number_format = '#,##0.00 "€"'
            cell_net = worksheet.cell(row=row_idx, column=6)
            cell_net.number_format = '#,##0.00 "€"'; cell_net.fill = fill_total; cell_net.font = font_total
            
        for c, w in zip(['A','B','C','D','E','F'], [20, 35, 22, 22, 25, 25]):
            worksheet.column_dimensions[c].width = w
    return buffer.getvalue()

def envoyer_releve_sur_discord(nom_coop, pseudo_emetteur, message_texte, fichier_bytes, nom_fichier):
    """Pousse proprement le relevé textuel et le fichier Excel sur le canal Discord de l'équipe."""
    if "discord_webhook_url" not in st.secrets:
        return False, "⚠️ Webhook Discord non configuré dans les secrets Streamlit."
    url_webhook = st.secrets["discord_webhook_url"]
    
    payload = {
        "username": f"Banque Centrale - {nom_coop}",
        "avatar_url": "https://flaticon.com",
        "content": f"📊 **Nouveau Relevé Comptable soumis par [{pseudo_emetteur}]**\n{message_texte}"
    }
    try:
        files = {"file": (nom_fichier, fichier_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = requests.post(url_webhook, data=payload, files=files, timeout=10)
        # CORRECTION : Remplacement du crochet défectueux par une validation de code 200/204 standard
        if response.status_code in: 
            return True, "🟢 Rapport envoyé avec succès sur Discord !"
        return False, f"❌ Erreur Discord (Code {response.status_code})"
    except Exception as e:
        return False, f"❌ Échec de la connexion Discord : {e}"
