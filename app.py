import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestion des Chantiers", page_icon="🏗️", layout="wide")
st.title("Gestion et Rentabilité des Chantiers")

# Initialisation de la base de données en mémoire
if "bdd_chantiers" not in st.session_state:
    st.session_state.bdd_chantiers = pd.DataFrame(columns=[
        "Nom du Chantier", "Revenus (€)", "Dépenses (€)", 
        "Bénéfice Net (€)", "ROI (%)"
    ])

# --- DICTIONNAIRE DE TOUS LES CHANTIERS POSSIBLES ---
CATALOGUE_CHANTIERS = {
    "Choisir un chantier pré-configuré...": {
        "revenus": 0, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Goudronnage d'une route (112 629 €)": {
        "revenus": 112629, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Déblayer - Niveau 2 (6 596 €)": {
        "revenus": 6596, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Exhausser un terrain (10 336 €)": {
        "revenus": 10336, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Exhausser un terrain (8 908 €)": {
        "revenus": 8908, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Construction d'un hangar (129 306 €)": {
        "revenus": 129306, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Suppression d'un espace vert (18 786 €)": {
        "revenus": 18786, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Compacter - Niveau 2 (3 699 €)": {
        "revenus": 3699, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Goudronnage d'un chemin (34 960 €)": {
        "revenus": 34960, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Exhausser un terrain (6 664 €)": {
        "revenus": 6664, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Déblayer - Niveau 3 (21 528 €)": {
        "revenus": 21528, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Assainissement de lit (Petit cours d'eau) (12 180 €)": {
        "revenus": 12180, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Assainissement de lit (Cours d'eau) (10 450 €)": {
        "revenus": 10450, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Goudronnage d'une route (Grande surface) (214 599 €)": {
        "revenus": 214599, "jours": 15, "location": 1200,
        "sable": 488, "terre": 0, "enrobe": 618, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 16, "jh_ouvrier": 48, "jh_cond": 28
    },
    "Construction d'un hangar (139 104 €)": {
        "revenus": 139104, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Compacter - Niveau 2 (4 617 €)": {
        "revenus": 4617, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    },
    "Remblayer - Niveau 3 (13 674 €)": {
        "revenus": 13674, "jours": 0, "location": 0,
        "sable": 0, "terre": 0, "enrobe": 0, "armature": 0, "tole": 0,
        "beton": 0, "panneaux": 0, "tuyaux": 0, "canalisations": 0, "poutres": 0,
        "jh_chef": 0, "jh_ouvrier": 0, "jh_cond": 0
    }
}

# --- LOGIQUE DE TRI ALPHABÉTIQUE ---
liste_complete = list(CATALOGUE_CHANTIERS.keys())
element_defaut = "Choisir un chantier pré-configuré..."

if element_defaut in liste_complete:
    liste_complete.remove(element_defaut)
liste_triee = [element_defaut] + sorted(liste_complete)

onglet1, onglet2 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement"])

with onglet1:
    st.subheader("Formulaire de saisie")
    
    chantier_selectionne = st.selectbox(
        "🚀 Optionnel - Pré-remplir avec un modèle de chantier :",
        liste_triee
    )
    
    donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
    valeur_nom_defaut = "" if chantier_selectionne == element_defaut else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=int(donnees_modele["revenus"]), min_value=0)
        jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=int(donnees_modele["jours"]), min_value=0)
        cout_location = st.number_input("Coût de location matériel / jour (€) :", value=int(donnees_modele["location"]), min_value=0)

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=int(donnees_modele["sable"]), min_value=0)
            qte_terre = st.number_input("Tonnes de Terre :", value=int(donnees_modele["terre"]), min_value=0)
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=int(donnees_modele["enrobe"]), min_value=0)
            qte_armature = st.number_input("Unités d'Armature métallique :", value=int(donnees_modele["armature"]), min_value=0)
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=int(donnees_modele["tole"]), min_value=0)
            qte_beton = st.number_input("Tonnes de Béton :", value=int(donnees_modele["beton"]), min_value=0)
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=int(donnees_modele["panneaux"]), min_value=0)
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=int(donnees_modele["tuyaux"]), min_value=0)
            qte_canalisations = st.number_input("Unités de Canalisations béton :", value=int(donnees_modele.get("canalisations", 0)), min_value=0)
            qte_poutres = st.number_input("Unités de Poutres IPN :", value=int(donnees_modele.get("poutres", 0)), min_value=0)
        
        with c_px:
            px_sable = st.number_input("Prix unitaire Sable (€) :", value=15, min_value=0)
            px_terre = st.number_input("Prix unitaire Terre (€) :", value=10, min_value=0)
            px_enrobe = st.number_input("Prix unitaire Enrobé (€) :", value=45, min_value=0)
            px_armature = st.number_input("Prix unitaire Armature (€) :", value=35, min_value=0)
            px_tole = st.number_input("Prix unitaire Tôle (€) :", value=20, min_value=0)
            px_beton = st.number_input("Prix unitaire Béton (€) :", value=80, min_value=0)
            px_panneaux = st.number_input("Prix unitaire Panneaux (€) :", value=50, min_value=0)
            px_tuyaux = st.number_input("Prix unitaire Tuyaux (€) :", value=15, min_value=0)
            px_canalisations = st.number_input("Prix unitaire Canalisations (€) :", value=60, min_value=0)
            px_poutres = st.number_input("Prix unitaire Poutres IPN (€) :", value=120, min_value=0)

    with col2:
        st.markdown("### --- MAIN D'ŒUVRE ---")
        c_jh, c_taux = st.columns(2)
        with c_jh:
            jh_chef = st.number_input("Jours-Homme Chef d'équipe :", value=int(donnees_modele["jh_chef"]), min_value=0)
            jh_ouvrier = st.number_input("Jours-Homme Ouvrier :", value=int(donnees_modele["jh_ouvrier"]), min_value=0)
            jh_cond = st.number_input("Jours-Homme Conducteur d'engins :", value=int(donnees_modele["jh_cond"]), min_value=0)
        
        with c_taux:
        taux_chef = st.number_input("Taux Journalier Chef (€) :", value=250, min_value=0)
        taux_ouvrier = st.number_input("Taux Journalier Ouvrier (€) :", value=180, min_value=0)
        taux_cond = st.number_input("Taux Journalier Conducteur (€) :", value=220, min_value=0)

    # --- CALCULS FINANCIERS ---
    total_materiaux = (
        (qte_sable * px_sable) + (qte_terre * px_terre) + (qte_enrobe * px_enrobe) +
        (qte_armature * px_armature) + (qte_tole * px_tole) + (qte_beton * px_beton) +
        (qte_panneaux * px_panneaux) + (qte_tuyaux * px_tuyaux) +
        (qte_canalisations * px_canalisations) + (qte_poutres * px_poutres)
    )
    
    total_mo = (jh_chef * taux_chef) + (jh_ouvrier * taux_ouvrier) + (jh_cond * taux_cond)
    total_location = jours_totaux * cout_location
    depenses_totales = total_materiaux + total_mo + total_location
    benefice_net = revenus - depenses_totales
    roi = (benefice_net / depenses_totales * 100) if depenses_totales > 0 else 0.0

    st.markdown("---")
    
    if st.button("💾 Enregistrer le chantier", use_container_width=True):
        if not nom_chantier:
            st.error("Veuillez donner un nom au chantier.")
        else:
            nouvel_enregistrement = pd.DataFrame([{
                "Nom du Chantier": nom_chantier,
                "Revenus (€)": revenus,
                "Dépenses (€)": depenses_totales,
                "Bénéfice Net (€)": benefice_net,
                "ROI (%)": round(roi, 2)
            }])
            st.session_state.bdd_chantiers = pd.concat(
                [st.session_state.bdd_chantiers, nouvel_enregistrement],
                ignore_index=True
            )
            st.success(f"Chantier '{nom_chantier}' enregistré avec succès !")

with onglet2:
    st.subheader("Historique des chantiers enregistrés")
    
    if st.session_state.bdd_chantiers.empty:
        st.info("Aucun chantier enregistré pour le moment.")
    else:
        # Tri automatique par Bénéfice Net décroissant
        df_affichage = st.session_state.bdd_chantiers.sort_values(by="Bénéfice Net (€)", ascending=False)
        st.dataframe(df_affichage, use_container_width=True)
        
        # Bouton pour réinitialiser l'historique
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.bdd_chantiers = pd.DataFrame(columns=[
                "Nom du Chantier", "Revenus (€)", "Dépenses (€)",
                "Bénéfice Net (€)", "ROI (%)"
            ])
            st.rerun()

            
