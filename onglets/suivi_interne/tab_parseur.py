import streamlit as st
import pandas as pd
import database as db
from datetime import datetime
from coops.parseur import analyser_historique_brut
from .tab_stock import identifier_cle_unique  # Extraction du nettoyeur universel

def mettre_a_jour_stock_reappro_firestore(nom_coop_active, materiaux_reappro):
    """
    Va chercher le dernier SNAPSHOT_STOCK dans Firestore, lui ajoute les quantités
    du réapprovisionnement et recrée un nouveau snapshot à jour.
    """
    try:
        col_ref = db.db.collection("cooperatives").document(nom_coop_active).collection("comptabilite_interne")
        
        # 1. On cherche le SNAPSHOT_STOCK le plus récent en base
        query_snapshot = col_ref.where("type", "==", "SNAPSHOT_STOCK")\
                                .order_by("timestamp_enregistrement", direction="DESCENDING")\
                                .limit(1).stream()
                                
        dernier_snapshot = None
        for doc in query_snapshot:
            dernier_snapshot = doc.to_dict()
            break
            
        # 🎯 CORRECTION SYNTAXE SÉCURISÉE : Initialisation des dictionnaires si la base est vide
        if dernier_snapshot is None:
            details_quantites = {}
            details_prix = {}
        else:
            details_quantites = dernier_snapshot.get("details_quantites", {})
            details_prix = dernier_snapshot.get("details_prix", {})
            
        # 2. On ajoute les nouvelles quantités réapprovisionnées au stock existant
        for mat_nom, qte in materiaux_reappro.items():
            cle_technique = identifier_cle_unique(mat_nom)
            cle_stock = f"stock_{cle_technique}"
            
            # Cumul de la quantité actuelle avec la nouvelle
            quantite_actuelle = int(details_quantites.get(cle_stock, 0))
            details_quantites[cle_stock] = quantite_actuelle + int(qte)
            
        # 3. Recalcul des totaux de valeur et de volume
        volume_total = 0
        valeur_totale = 0
        for cle_st, qte_st in details_quantites.items():
            volume_total += qte_st
            # On extrait le nom de la ressource pour trouver son prix associé
            cle_res = cle_st.replace("stock_", "")
            prix_unitaire = float(details_prix.get(f"prix_{cle_res}", 0.0))
            valeur_totale += int(qte_st * prix_unitaire)
            
        # 4. Enregistrement du nouveau snapshot incrémenté dans Firestore
        maintenant = datetime.now()
        id_document = f"snapshot_stock_{maintenant.strftime('%Y%m%d_%H%M%S')}"
        
        nouveau_snapshot = {
            "type": "SNAPSHOT_STOCK",
            "date_jeu": maintenant.strftime("%d/%m/%Y"),
            "heure_jeu": maintenant.strftime("%H:%M"),
            "valeur_totale_stock": valeur_totale,
            "volume_total_stock": volume_total,
            "details_quantites": details_quantites,
            "details_prix": details_prix,
            "timestamp_enregistrement": maintenant.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        col_ref.document(id_document).set(nouveau_snapshot)
        st.toast(f"🧱 Stock mis à jour automatiquement en tâche de fond !", icon="📦")
        
    except Exception as e:
        st.caption(f"ℹ️ Note : Impossible de mettre à jour le snapshot de stock dynamique ({e})")

def afficher_tab_parseur(nom_coop_active, membres_inscrits, joueur_actif, liste_flux):
    st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
    texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_parseur_coop_final_v5")
    
    if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
        mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
        
        compteur_reappro = 0
        for mv in mouvements: 
            # Enregistrement classique dans la base de l'historique brut
            db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
            
            # Détection du réapprovisionnement pour ajuster le stock réel en direct
            if str(mv["type"]).strip() == "REAPPROVISIONNEMENT" and mv["materiaux"]:
                mettre_a_jour_stock_reappro_firestore(nom_coop_active, mv["materiaux"])
                compteur_reappro += 1
        
        st.cache_data.clear()
        db.charger_flux_coop_cache.clear()
        
        if compteur_reappro > 0:
            st.success(f"🎯 Synchronisation réussie ! {compteur_reappro} réapprovisionnement(s) intégré(s) directement dans vos stocks.")
        else:
            st.success("🎯 Synchronisation réussie !")
            
        st.rerun()

    st.markdown("---")
    st.markdown("##### ⏱️ Les 5 dernières entrées de l'historique du jeu (Flux Matériaux)")
    
    if liste_flux:
        try:
            df_flux_recents = pd.DataFrame(liste_flux)
            for c_req in ["joueur", "type", "date_jeu", "heure_jeu", "materiaux"]:
                if c_req not in df_flux_recents.columns: df_flux_recents[c_req] = ""

            types_jeu_valides = ["REAPPROVISIONNEMENT", "ACHAT_INTERNE", "ACHAT_EXTERNE"]
            df_flux_recents = df_flux_recents[df_flux_recents["type"].isin(types_jeu_valides)]

            if not df_flux_recents.empty:
                def generer_cle_tri_jeu(row):
                    d_txt = str(row.get("date_jeu", "01/01/2000")).strip()
                    h_txt = str(row.get("heure_jeu", "00:00")).strip()
                    try:
                        return f"{''.join(reversed(d_txt.split('/')) or '20000101')}_{h_txt.replace(':', '')}"
                    except Exception: return "20000101_0000"

                df_flux_recents["cle_tri_jeu"] = df_flux_recents.apply(generer_cle_tri_jeu, axis=1)
                df_flux_recents = df_flux_recents.sort_values(by="cle_tri_jeu", ascending=False).head(5)

                def formater_materiaux(dict_mats):
                    if not isinstance(dict_mats, dict) or not dict_mats: return "Aucun"
                    return ", ".join([f"{k.capitalize()} ({int(v)} u)" for k, v in dict_mats.items()])

                df_flux_recents["Détail Matériaux"] = df_flux_recents["materiaux"].apply(formater_materiaux)
                df_flux_recents["Type"] = df_flux_recents["type"].apply(lambda t: {"REAPPROVISIONNEMENT": "🧱 Réappro", "ACHAT_INTERNE": "🛒 Achat Int.", "ACHAT_EXTERNE": "🌍 Achat Ext."}.get(t, t))
                df_flux_recents = df_flux_recents[["date_jeu", "heure_jeu", "joueur", "Type", "Détail Matériaux"]]

                st.dataframe(
                    df_flux_recents, width="stretch", hide_index=True,
                    column_config={
                        "date_jeu": st.column_config.TextColumn("📅 Date Jeu"), "heure_jeu": st.column_config.TextColumn("⏱️ Heure Jeu"),
                        "joueur": st.column_config.TextColumn("👤 Joueur / Acteur"), "Type": st.column_config.TextColumn("🏷️ Action"),
                        "Détail Matériaux": st.column_config.TextColumn("🧱 Ressources transférées")
                    }
                )
            else: st.info("💡 Aucun log d'événement de matériel n'est enregistré pour le moment.")
        except Exception as e: st.caption(f"ℹ️ Impossible de mettre en forme le flux récent ({e}).")
    else: st.info("💡 L'historique de cette coopérative is vierge pour le moment.")
