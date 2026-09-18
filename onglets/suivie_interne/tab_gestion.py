# Contenu de : onglets/suivi_interne/tab_gestion.py
import streamlit as st
import pandas as pd
import database as db

def afficher_tab_gestion(nom_coop_active, joueur_actif, niveau_actuel, membres_inscrits, coop_snap):
    st.markdown("#### ⚙️ Gérer les Collaborateurs (Admin)")
    if niveau_actuel < 2:
        st.error("🔒 Accès refusé : Niveau 2 minimum requis pour voir l'administration.")
        return

    with st.form("form_rallonge_cash"):
        m_rev = st.selectbox("Collaborateur :", membres_inscrits)
        m_cash = st.number_input("Montant de la rallonge (€) :", min_value=0.0, step=1000.0)
        if st.form_submit_button("💰 APPLIQUER LA RALLONGE") and m_cash > 0:
            db.ajouter_reinvestissement_membre(nom_coop_active, m_rev, m_cash)
            st.cache_data.clear()
            st.rerun()

    if niveau_actuel >= 3:
        st.markdown("---")
        st.markdown("##### 👑 1. Attribution des Mots de Passe des Grades")
        with st.form("form_gestion_mots_de_passe_grades"):
            nouveau_mdp_niv1 = st.text_input("Définir le mot de passe Ouvriers (Niveau 1) :", value=str(coop_snap.get("mdp_niveau1", "")))
            nouveau_mdp_niv2 = st.text_input("Définir le mot de passe Membres Fiables (Niveau 2) :", value=str(coop_snap.get("mdp_niveau2", "")))
            nouveau_mdp_niv3 = st.text_input("Changer votre mot de passe Créateur (Niveau 3) :", value=str(coop_snap.get("mdp_niveau3", "")))
            if st.form_submit_button("💾 VERROUILLER ET SAUVEGARDER LES CODES", width="stretch"):
                db.db.collection("cooperatives").document(nom_coop_active).update({
                    "mdp_niveau1": nouveau_mdp_niv1, 
                    "mdp_niveau2": nouveau_mdp_niv2, 
                    "mdp_niveau3": nouveau_mdp_niv3
                })
                st.success("🟢 Les mots de passe des grades ont été mis à jour avec succès !")
                st.rerun()

        st.markdown("---")
        st.markdown("##### 📈 1b. Configuration des Dividendes & Commissions")
        with st.form("form_commission_coop"):
            pct_actuel = float(coop_snap.get("pourcentage_commission", 10.0))
            nouveau_pct = st.number_input(
                "Définir le pourcentage par défaut appliqué à la zone de saisie (%) :",
                min_value=0.0, max_value=100.0, value=pct_actuel, step=1.0, format="%.1f"
            )
            if st.form_submit_button("💾 ENREGISTRER LE POURCENTAGE", width="stretch"):
                db.db.collection("cooperatives").document(nom_coop_active).update({
                    "pourcentage_commission": nouveau_pct
                })
                st.success(f"🎯 Commission par défaut mise à jour à {nouveau_pct} % ! Pensez à synchroniser.")
                st.rerun()

        st.markdown("---")
        st.markdown("##### 🚨 2. Zone de Licenciement & Purge d'Apport Initial")
        m_retirer = st.selectbox("Membre à licencier :", ["-- Choisir un membre --"] + membres_inscrits, key="del_mb_key_final_v5")
        if m_retirer != "-- Choisir un membre --" and st.checkbox("Confirmer le licenciement de " + m_retirer):
            if st.button("🗑️ RETIRER LE MEMBRE & PURGER L'APPORT", type="primary", width="stretch"):
                try:
                    coop_doc_ref = db.db.collection("cooperatives").document(nom_coop_active)
                    membres_actuels = coop_doc_ref.get().to_dict().get("membres", [])
                    
                    if m_retirer in membres_actuels:
                        membres_actuels.remove(m_retirer)
                        coop_doc_ref.update({"membres": membres_actuels})
                        
                        # 🎯 SUPPRESSION PHYSIQUE DU COMPTE D'APPORT DANS FIRESTORE
                        try:
                            flux_sub_ref = coop_doc_ref.collection("comptabilite_interne")
                            for doc_flux in flux_sub_ref.stream():
                                dict_f = doc_flux.to_dict()
                                if dict_f.get("joueur") == m_retirer and dict_f.get("type") == "APPORT_INITIAL":
                                    doc_flux.reference.delete()
                                    st.toast(f"🗑️ Document d'apport d'origine de {m_retirer} supprimé de Firestore.")
                        except Exception as e_del:
                            st.caption(f"ℹ️ Note : Impossible de nettoyer le document d'apport initial ({e_del})")
                        
                        db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a banni [{m_retirer}] et purgé son document d'apport d'origine.")
                        st.success(f"🏃 {m_retirer} retiré de l'équipe et ses données d'apport d'origine supprimées de Firebase !")
                        st.cache_data.clear()
                        db.charger_flux_coop_cache.clear()
                        st.rerun()
                except Exception as e: 
                    st.error(f"❌ Erreur : {e}")

        st.markdown("---")
        slots_occupes = len(membres_inscrits)
        if slots_occupes < 4:
            st.markdown("##### ➕ 3. Recrutement de Collaborateurs en Bloc")
            texte_bloc_membres = st.text_input("Saisissez les pseudos à inscrire (séparés par un espace) :", value="", placeholder="Ex: Adri1 Julo", key="recrutement_bloc_key_final_v5").strip()
            if st.button("📝 ENREGISTRER L'ÉQUIPE EN BLOC", type="primary", width="stretch"):
                if texte_bloc_membres:
                    statut_ins, msg_ins = db.ajouter_membres_bloc_coop(nom_coop_active, texte_bloc_membres)
                    if statut_ins:
                        db.enregistrer_log(type_action="COOPERATIVE", details=f"Le Créateur [{joueur_actif}] a recruté du personnel en bloc.")
                        st.success(msg_ins)
                        st.cache_data.clear()
                        db.charger_flux_coop_cache.clear()
                        st.rerun()
                    else: 
                        st.error(msg_ins)
        else: 
            st.warning("🚫 Votre équipe est complète (4/4). Vous ne pouvez plus rajouter de joueurs.")

        st.markdown("---")
        st.markdown("##### 👑 4. Statistiques d'Utilisation & Activité de l'Équipe")
        try:
            logs_stream = db.db.collection("journaux_actions").stream()
            liste_logs_bruts = [doc.to_dict() for doc in logs_stream]
            if liste_logs_bruts:
                df_logs = pd.DataFrame(liste_logs_bruts)
                df_connexions = df_logs[df_logs["type_action"] == "CONNEXION"].copy() if "type_action" in df_logs.columns else pd.DataFrame()
                if not df_connexions.empty:
                    df_connexions = df_connexions.sort_values(by="timestamp", ascending=False).head(10)
                    st.markdown("**⏱️ Dernières connexions enregistrées (Top 10) :**")
                    st.dataframe(df_connexions[["timestamp", "details"]], width="stretch", hide_index=True)
                else: 
                    st.caption("ℹ️ Aucun log de connexion récent détecté.")
        except Exception as e: 
            st.caption(f"ℹ️ Tableau de bord statistique momentanément indisponible ({e}).")
