# Fichier : coops/calculs.py
import pandas as pd

def compiler_compta_membres(liste_flux, dict_capitaux, membres_inscrits):
    """
    Calcule le grand livre des comptes associés basé sur les règles économiques fixes :
    - Trésorerie : 100 € de rallonge = 1 point
    - Réapprovisionnement : Payé par la coop = 0 point (uniquement du volume)
    - Achats (Perso ou Ext) : Génère 1 € de marge par unité = 1 point
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
    Détermine automatiquement les pourcentages de dividendes légitimes et le rôle de Responsable Logistique
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
