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

# --- LOGIQUE DE TRI ALPHABÉTIQUE POUR LE MENU DEROULANT ---
liste_complete = list(CATALOGUE_CHANTIERS.keys())
element_defaut = "Choisir un chantier pré-configuré..."

# On retire l'élément par défaut, on trie le reste de A à Z, puis on le remet en premier
if element_defaut in liste_complete:
    liste_complete.remove(element_defaut)
liste_triee = [element_defaut] + sorted(liste_complete)

onglet1, onglet2 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement"])

with onglet1:
    st.subheader("Formulaire de saisie")
    
    # Affichage du menu déroulant trié par ordre alphabétique
    chantier_selectionne = st.selectbox(
        "🚀 Optionnel - Pré-remplir avec un modèle de chantier :",
        liste_triee
    )
    
    # EXTRACTION DES DONNÉES DEPUIS LE CATALOGUE BASE
    donnees_modele = CATALOGUE_CHANTIERS[chantier_selectionne]
    valeur_nom_defaut = "" if chantier_selectionne == element_defaut else chantier_selectionne
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value=valeur_nom_defaut).strip()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=donnees_modele["revenus"])
        jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=donnees_modele["jours"])
        cout_location = st.number_input("Coût de location matériel / jour (€) :", value=donnees_modele["location"])

        st.markdown("### --- MATÉRIAUX ---")
        c_qte, c_px = st.columns(2)
        with c_qte:
            qte_sable = st.number_input("Tonnes de Sable :", value=donnees_modele["sable"])
            qte_terre = st.number_input("Tonnes de Terre :", value=donnees_modele["terre"])
            qte_enrobe = st.number_input("Tonnes d'Enrobé :", value=donnees_modele["enrobe"])
            qte_armature = st.number_input("Unités d'Armature métallique :", value=donnees_modele["armature"])
            qte_tole = st.number_input("Unités de Plaque de tôle ondulée :", value=donnees_modele["tole"])
            qte_beton = st.number_input("Tonnes de Béton :", value=donnees_modele["beton"])
            qte_panneaux = st.number_input("Unités de Panneaux signalisation :", value=donnees_modele["panneaux"])
            qte_tuyaux = st.number_input("Unités de Tuyaux d'eau standards :", value=donnees_modele["tuyaux"])
            qte_eaux_usees = st.number_input("Unités de Canalisations eaux usées :", value=donnees_modele["canalisations"])
            qte_poutres = st.number_input("Unités de Poutres en acier :", value=donnees_modele["poutres"])
        with c_px:
            prix_sable = st.number_input("Prix Sable (€/t) :", value=12)
            prix_terre = st.number_input("Prix Terre (€/t) :", value=16)
            prix_enrobe = st.number_input("Prix Enrobé (€/t) :", value=42)
            prix_armature = st.number_input("Prix Armature (€/u) :", value=70)
            prix_tole = st.number_input("Prix Tôle (€/u) :", value=55)
            prix_beton = st.number_input("Prix Béton (€/t) :", value=45)
            prix_panneaux = st.number_input("Prix Panneaux (€/u) :", value=90)
            prix_tuyaux = st.number_input("Prix Tuyaux d'eau (€/u) :", value=32)
            prix_eaux_usees = st.number_input("Prix Canalisations (€/u) :", value=35)
            prix_poutres = st.number_input("Prix Poutres acier (€/u) :", value=70)

    with col2:
        st.markdown("### --- GRILLE SALARIALE & HEURES ---")
        chef_mensuel = st.number_input("Salaire mensuel Chef (€) :", value=1566)
        jh_chef = st.number_input("Total Jours-Homme Chef :", value=donnees_modele["jh_chef"])
        ouvrier_mensuel = st.number_input("Salaire mensuel Ouvrier (€) :", value=1616)
        jh_ouvrier = st.number_input("Total Jours-Homme Ouvrier :", value=donnees_modele["jh_ouvrier"])
        cond_mensuel = st.number_input("Salaire mensuel Conducteur (€) :", value=1571)
        jh_cond = st.number_input("Total Jours-Homme Conducteur :", value=donnees_modele["jh_cond"])

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary"):
        df_actuel = st.session_state.bdd_chantiers
        doublon_existe = not df_actuel[(df_actuel["Nom du Chantier"] == nom_chantier) & (df_actuel["Revenus (€)"] == revenus)].empty
        
        if not nom_chantier:
            st.error("Veuillez donner un nom ou un numéro valide à votre chantier.")
        elif doublon_existe:
            st.error(f"Impossible d'enregistrer : Ce chantier au montant de {revenus:,.2f} € existe déjà.")
        else:
            mats_sable = qte_sable * prix_sable
            mats_terre = qte_terre * prix_terre
            mats_enrobe = qte_enrobe * prix_enrobe
            mats_armature = qte_armature * prix_armature
            mats_tole = qte_tole * prix_tole
            mats_beton = qte_beton * prix_beton
            mats_panneaux = qte_panneaux * prix_panneaux
            mats_tuyaux = qte_tuyaux * prix_tuyaux
            mats_eaux = qte_eaux_usees * prix_eaux_usees
            mats_poutres = qte_poutres * prix_poutres
            
            total_mats = mats_sable + mats_terre + mats_enrobe + mats_armature + mats_tole + mats_beton + mats_panneaux + mats_tuyaux + mats_eaux + mats_poutres
            total_location = jours_totaux * cout_location
            
            sal_chef = jh_chef * (chef_mensuel / 30)
            sal_ouvrier = jh_ouvrier * (ouvrier_mensuel / 30)
            sal_cond = jh_cond * (cond_mensuel / 30)
            total_salaires = sal_chef + sal_ouvrier + sal_cond

            total_depenses = total_mats + total_location + total_salaires
            benefice_net = revenus - total_depenses
            roi = (benefice_net / total_depenses) * 100 if total_depenses > 0 else 0

            st.markdown("---")
            st.write(f"**Coût Matériaux globaux** : {total_mats:,.2f} €")
            st.write(f"**Coût Location** : {total_location:,.2f} €")
            st.write(f"**Coût Salaires** : {total_salaires:,.2f} €")
            
            if benefice_net >= 0:
                st.success(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")
            else:
                st.error(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")

            nouvel_enregistrement = pd.DataFrame([{
                "Nom du Chantier": nom_chantier,
                "Revenus (€)": revenus,
                "Dépenses (€)": total_depenses,
                "Bénéfice Net (€)": benefice_net,
                "ROI (%)": round(roi, 2)
            }])
            
            st.session_state.bdd_chantiers = pd.concat([st.session_state.bdd_chantiers, nouvel_enregistrement], ignore_index=True)
            st.toast("Chantier enregistré avec succès dans l'historique !")

with onglet2:
    st.subheader("Base de données des chantiers enregistrés")
    
    if st.session_state.bdd_chantiers.empty:
        st.info("Aucun chantier n'a encore été enregistré.")
    else:
        critere_tri = st.selectbox(
            "Classer les chantiers par ordre de rentabilité :",
            ["Plus gros Bénéfice d'abord", "Plus gros ROI d'abord", "Plus de revenus d'abord"]
        )
        
        df_affichage = st.session_state.bdd_chantiers.copy()
        
        if critere_tri == "Plus gros Bénéfice d'abord":
            df_affichage = df_affichage.sort_values(by="Bénéfice Net (€)", ascending=False)
        elif critere_tri == "Plus gros ROI d'abord":
            df_affichage = df_affichage.sort_values(by="ROI (%)", ascending=False)
        elif critere_tri == "Plus de revenus d'abord":
            df_affichage = df_affichage.sort_values(by="Revenus (€)", ascending=False)
            
        st.dataframe(df_affichage, use_container_width=True)
        
        csv = df_affichage.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger la base de données (CSV)",
            data=csv,
            file_name="base_donnies_chantiers.csv",
            mime="text/csv"
        )
