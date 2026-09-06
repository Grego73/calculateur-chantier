# Fichier complet et validé pour : coops/calculs.py
import pandas as pd
import io

def compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits):
    """
    Calcule le grand livre des comptes associés basé sur les règles économiques de la coop.
    """
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
        if user not in compta: 
            continue
        
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
    """
    Détermine automatiquement les pourcentages de dividendes et le rôle de Responsable Logistique
    """
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
    """
    Génère un fichier Excel stylisé calculant automatiquement l'argent en euros dû à chaque membre.
    """
    from openpyxl.styles import Font, PatternFill, Alignment
    
    # 1. Préparation des données de paye en euros
    lignes_paye = []
    benefice_restant = benefice_total_caisse
    
    # Si on a un logisticien, on calcule sa prime de 5% sur le bénéfice global des ventes
    prime_logistique_globale = 0.0
    if id_logisticien and benefice_total_caisse > 0:
        prime_logistique_globale = benefice_total_caisse * 0.05
        benefice_restant = benefice_total_caisse - prime_logistique_globale

    for _, row in df_coop.iterrows():
        pseudo = row["Pseudo Membre"]
        pct_dividende = row["Distribution Bénéfice (%)"]
        
        # Argent gagné grâce aux parts (sur les 95% restants)
        argent_dividendes = (pct_dividende / 100.0) * benefice_restant
        
        # Ajout de la prime si c'est le meilleur logisticien
        prime_lo = prime_logistique_globale if pseudo == id_logisticien else 0.0
        total_a_payer_joueur = argent_dividendes + prime_lo
        
        lignes_paye.append({
            "👤 Pseudo Joueur": pseudo,
            "🎖️ Statut Semaine": row["Rôle cette semaine"],
            "📊 Part Dividende (%)": f"{pct_dividende:.2f} %",
            "💰 Gain Dividendes (€)": round(argent_dividendes, 2),
            "👑 Prime Logistique (+5%)": round(prime_lo, 2),
            "💸 TOTAL NET À PAYER (€)": round(total_a_payer_joueur, 2)
        })
        
    df_paye = pd.DataFrame(lignes_paye)
    
    # 2. Écriture et Stylisation Excel avec OpenPyXL
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_paye.to_excel(writer, index=False, sheet_name="Distribution de la Paye")
        
        workbook = writer.book
        worksheet = writer.sheets["Distribution de la Paye"]
        
        # Style de l'en-tête (Gris foncé pro)
        fill_header = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
        font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        
        for col_idx in range(1, 7):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.fill = fill_header
            cell.font = font_header
            cell.alignment = Alignment(horizontal="center")
            
        # Formatage des lignes et mise en valeur de la colonne "TOTAL NET À PAYER"
        fill_total = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Vert pastel
        font_total = Font(name="Calibri", size=11, bold=True, color="15803D")
        
        for row_idx in range(2, len(df_paye) + 2):
            worksheet.cell(row=row_idx, column=4).number_format = '#,##0.00 "€"' # Dividendes
            worksheet.cell(row=row_idx, column=5).number_format = '#,##0.00 "€"' # Prime
            
            cell_net = worksheet.cell(row=row_idx, column=6)
            cell_net.number_format = '#,##0.00 "€"'
            cell_net.fill = fill_total
            cell_net.font = font_total
            
        # Largeurs de colonnes automatiques
        worksheet.column_dimensions['A'].width = 20
        worksheet.column_dimensions['B'].width = 35
        worksheet.column_dimensions['C'].width = 22
        worksheet.column_dimensions['D'].width = 22
        worksheet.column_dimensions['E'].width = 25
        worksheet.column_dimensions['G'].width = 25

    return buffer.getvalue()
