# Contenu de : onglets/suivi_interne/tab_parseur.py
import streamlit as st
import pandas as pd
import database as db
from coops.parseur import analyser_historique_brut

def afficher_tab_parseur(nom_coop_active, membres_inscrits, joueur_actif, liste_flux):
    st.markdown("#### 📥 Alimenter le Système via le Fil des Événements")
    texte_logs = st.text_area("Collez l'historique brut du jeu ici :", height=200, key="area_parseur_coop_final_v5")
    if st.button("🚀 ENREGISTRER L'HISTORIQUE ET FILTRER LES DOUBLONS", type="primary", width="stretch") and texte_logs.strip():
        mouvements = analyser_historique_brut(texte_logs, membres_inscrits, joueur_actif)
        for mv in mouvements: 
            db.enregistrer_ligne_historique_brute(nom_coop_active, mv["date"], mv["heure"], mv["acteur"], mv["type"], mv["materiaux"])
        
        st.cache_data.clear()
        db.charger_flux_coop_cache.clear()
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
    else: st.info("💡 L'historique de cette coopérative est vierge pour le moment.")
