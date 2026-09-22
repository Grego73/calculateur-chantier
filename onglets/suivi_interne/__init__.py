# Contenu complet et corrigé de : onglets/suivi_interne/__init__.py
import streamlit as st
import database as db

# 🟢 CONFIGURATION DE TOUTES LES IMPORTATIONS INTERNES SÉPARÉES
from .tab_distribution import afficher_tab_distribution
from onglets.suivi_interne.tab_marche import afficher_tab_marche
from onglets.suivi_interne.tab_parseur import afficher_tab_parseur
from onglets.suivi_interne.tab_gestion import afficher_tab_gestion
from .tab_diagnostic import afficher_tab_diagnostic  # <-- NOUVEL IMPORT

def afficher_onglet_suivi_interne(SALAIRES_DB, CATALOGUE_ENGINS, MATERIAUX_DB):
    if "auth_suivi_coop" not in st.session_state:
        st.session_state["auth_suivi_coop"] = None
        st.session_state["auth_suivi_joueur"] = None
    if "coop_privilege_level" not in st.session_state:
        st.session_state["coop_privilege_level"] = 1

    # --- ÉCRAN DE CONNEXION ---
    if st.session_state["auth_suivi_coop"] is None:
        coops_enregistrees = db.lister_toutes_les_cooperatives()
        options_coop = ["-- Choisir une coopérative existante --"] + coops_enregistrees + ["➕ Créer une nouvelle coopérative..."]

        with st.form("form_auth_coop_joueur"):
            st.markdown("#### 🔒 Authentification Équipe & Enregistrement")
            coop_selection = st.selectbox("Sélectionner votre Coopérative :", options_coop)
            nom_coop_finale = st.text_input("Saisissez le NOM de la Coop :").strip() if coop_selection == "➕ Créer une nouvelle coopérative..." else (coop_selection if coop_selection != "-- Choisir une coopérative existante --" else "")
            
            st.caption("💡 Si vous créez une Coop, le mot de passe ci-dessous deviendra votre code Créateur (Niveau 3).")
            mdp_input = st.text_input("Mot de passe :", type="password").strip()
            pseudo_input = st.text_input("Votre Pseudo Unique :").strip()
            
            if st.form_submit_button("🔑 REJOINDRE L'ESPACE COMPTABLE", width="stretch") and mdp_input and pseudo_input and nom_coop_finale:
                succes, message, niveau_attribue = db.verifier_et_inscrire_joueur(nom_coop_finale, mdp_input, pseudo_input)
                if succes:
                    st.session_state["auth_suivi_coop"] = nom_coop_finale
                    st.session_state["auth_suivi_joueur"] = pseudo_input
                    st.session_state["coop_privilege_level"] = niveau_attribue
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)
        return

    nom_coop_active = st.session_state["auth_suivi_coop"]
    joueur_actif = st.session_state["auth_suivi_joueur"]
    niveau_actuel = st.session_state["coop_privilege_level"]

    dict_badges = {1: "👷 Niveau 1 : Ouvrier", 2: "🎖️ Niveau 2 : Membre Fiable", 3: "🏆 Niveau 3 : Créateur / Admin"}
    c_head1, c_head2 = st.columns(2)
    with c_head1: st.success(f"🔓 Coop : **{nom_coop_active}** | {dict_badges[niveau_actuel]}")
    with c_head2: 
        if st.button("🚪 DÉCONNEXION / CHANGER DE COOP", type="secondary", width="stretch"):
            st.session_state["auth_suivi_coop"] = None; st.session_state["auth_suivi_joueur"] = None; st.session_state["coop_privilege_level"] = 1; st.rerun()

    st.markdown("---")
    
    # Construction dynamique de la liste des onglets selon le grade
    titres_onglets = [
        "🏆 1. Parts & Bénéfices de la Coop", 
        "🌍 2. Marché Global", 
        "📥 Déposer l'Historique du Jeu", 
        "⚙️ Gérer les Droits & Associés"
    ]
    # Si le joueur est Niveau 3, on rajoute l'onglet diagnostic secret
    if niveau_actuel >= 3:
        titres_onglets.append("🚨 Centre de Nettoyage NoSQL")

    liste_onglets_st = st.tabs(titres_onglets)

    # Chargement des structures et flux depuis la base NoSQL
    liste_flux_bruts = db.charger_flux_coop_cache(nom_coop_active)
    coop_snap = db.db.collection("cooperatives").document(nom_coop_active).get().to_dict() or {}
    membres_inscrits = coop_snap.get("membres", [joueur_actif])

    # SÉCURITÉ ANTI-CRASH : Configuration d'une valeur temporelle par défaut dans la session
    if "point_reprise_date_compta" not in st.session_state:
        st.session_state["point_reprise_date_compta"] = "01/08/2026"

    # BOUTON GLOBAL DE FORÇAGE DE LA SYNCHRONISATION
    if st.button("🔄 FORCER LA SYNCHRONISATION DES NOUVEAUX CALCULS", type="secondary", width="stretch"):
        st.cache_data.clear()
        db.charger_flux_coop_cache.clear()
        st.rerun()

    # 🟢 DÉFINITION STRICTE ET FILTRAGE DE "liste_flux" POUR LES ONGLETS SUIVANTS
    liste_flux = []
    ids_traites = set()
    try:
        date_limite_cle = int("".join(reversed(st.session_state["point_reprise_date_compta"].split("/"))))
        for fl in liste_flux_bruts:
            doc_id = fl.get("ID_Document_Firestore", "")
            id_normalise = doc_id.replace("['", "").replace("']", "").strip() if doc_id else ""
            if id_normalise in ids_traites and id_normalise: 
                continue
            if id_normalise: 
                ids_traites.add(id_normalise)

            d_txt = fl.get("date_jeu", "01/01/2000")
            try:
                date_doc_cle = int("".join(reversed(d_txt.split("/"))))
                if date_doc_cle >= date_limite_cle: 
                    liste_flux.append(fl)
            except Exception: 
                liste_flux.append(fl)
    except Exception:
        liste_flux = liste_flux_bruts

    # --- ROUTAGE VERS LES CONTENUS D'ONGLETS ---
    with liste_onglets_st[0]:
        afficher_tab_distribution(nom_coop_active, joueur_actif, niveau_actuel, liste_flux_bruts)
        
    with liste_onglets_st[1]:
        afficher_tab_marche(liste_flux, membres_inscrits)
        
    with liste_onglets_st[2]:
        afficher_tab_parseur(nom_coop_active, membres_inscrits, joueur_actif, liste_flux)
        
    with liste_onglets_st[3]:
        afficher_tab_gestion(nom_coop_active, joueur_actif, niveau_actuel, membres_inscrits, coop_snap)

    # Si le joueur est Niveau 3, on peuple le 5ème onglet
    if niveau_actuel >= 3:
        with liste_onglets_st[4]:
            afficher_tab_diagnostic(nom_coop_active)
