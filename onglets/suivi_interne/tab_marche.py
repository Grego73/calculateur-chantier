# Contenu de : onglets/suivi_interne/tab_marche.py
import streamlit as st
import pandas as pd

def afficher_tab_marche(liste_flux, membres_inscrits):
    st.markdown("#### 🌍 Registre Général des Flux du Marché")
    if liste_flux:
        stats_joueurs = {}
        mats_global_graph = {}
        
        for f in liste_flux:
            if f.get("type") == "REAPPROVISIONNEMENT":
                continue
                
            j = f.get("joueur", "Inconnu").strip()
            if not j: continue
                
            if j not in stats_joueurs:
                stats_joueurs[j] = {"details_mats": {}}
                
            mats_dict = f.get("materiaux", {})
            if isinstance(mats_dict, dict):
                for m_k, m_v in mats_dict.items():
                    m_v_float = float(m_v)
                    m_nom_propre = m_k.capitalize()
                    
                    dict_mats_joueur = stats_joueurs[j]["details_mats"]
                    dict_mats_joueur[m_nom_propre] = dict_mats_joueur.get(m_nom_propre, 0.0) + m_v_float
                    mats_global_graph[m_nom_propre] = mats_global_graph.get(m_nom_propre, 0.0) + m_v_float
        
        if stats_joueurs:
            lignes_tableau_marche = []
            for joueur_nom, data in stats_joueurs.items():
                dict_details = data["details_mats"]
                
                if dict_details:
                    volume_total_reel = sum(dict_details.values())
                    mat_favori = max(dict_details, key=dict_details.get)
                    vol_favori = int(dict_details[mat_favori])
                    texte_mat_favori = f"📦 {mat_favori} ({vol_favori}u)"
                else:
                    volume_total_reel = 0
                    texte_mat_favori = "Aucun"
                    
                lignes_tableau_marche.append({
                    "Joueur": joueur_nom,
                    "Statut": "🏆 Membre" if joueur_nom in membres_inscrits else "👤 Client",
                    "Matériau le plus acheté": texte_mat_favori,
                    "Volume Total (u)": int(volume_total_reel)
                })
            
            df_marche_favori = pd.DataFrame(lignes_tableau_marche)
            df_marche_favori = df_marche_favori.sort_values(by="Volume Total (u)", ascending=False)
            
            st.dataframe(
                df_marche_favori, width="stretch", hide_index=True,
                column_config={
                    "Joueur": st.column_config.TextColumn("👤 Joueur"),
                    "Statut": st.column_config.TextColumn("🏷️ Statut"),
                    "Matériau le plus acheté": st.column_config.TextColumn("🔥 Matériau Favori (Volume)"),
                    "Volume Total (u)": st.column_config.NumberColumn("📊 Volume Global", format="%d u")
                }
            )
        else:
            st.info("💡 Aucun achat n'a été enregistré pour le moment.")
            
        if mats_global_graph:
            st.markdown("##### 📊 Volumes totaux des matériaux achetés sur le serveur :")
            st.bar_chart(pd.DataFrame(list(mats_global_graph.items()), columns=["Matériau", "Volume"]).set_index("Matériau"), color="#ff4b4b")
    else:
        st.info("💡 L'historique de cette coopérative est vierge pour le moment.")
