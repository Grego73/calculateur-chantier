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

# Création des deux onglets (Pages)
onglet1, onglet2 = st.tabs(["➕ Ajouter un Chantier", "📊 Historique & Classement"])

with onglet1:
    st.subheader("Formulaire de saisie")
    
    # Saisie du nom du chantier
    nom_chantier = st.text_input("Nom ou Numéro du chantier :", value="Chantier Route A7").strip()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### --- PARAMÈTRES GÉNÉRAUX ---")
        revenus = st.number_input("Revenus prévus du chantier (€) :", value=214599)
        jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=15)
        cout_location = st.number_input("Coût de location matériel / jour (€) :", value=1200)

        st.markdown("### --- MATÉRIAUX ---")
        tonnes_enrobe = st.number_input("Tonnes d'enrobé nécessaires :", value=618)
        prix_enrobe = st.number_input("Prix de la tonne d'enrobé (€) :", value=42)
        tonnes_sable = st.number_input("Tonnes de sable nécessaires :", value=488)
        prix_sable = st.number_input("Prix de la tonne de sable (€) :", value=12)

    with col2:
        st.markdown("### --- GRILLE SALARIALE & HEURES ---")
        chef_mensuel = st.number_input("Salaire mensuel Chef (€) :", value=1566)
        jh_chef = st.number_input("Total Jours-Homme Chef :", value=16)
        ouvrier_mensuel = st.number_input("Salaire mensuel Ouvrier (€) :", value=1616)
        jh_ouvrier = st.number_input("Total Jours-Homme Ouvrier :", value=48)
        cond_mensuel = st.number_input("Salaire mensuel Conducteur (€) :", value=1571)
        jh_cond = st.number_input("Total Jours-Homme Conducteur :", value=28)

    if st.button("LANCER LE CALCUL & ENREGISTRER", type="primary"):
        # --- VERIFICATION ANTI-DOUBLON COMPLÈTE (NOM + REVENUS) ---
        df_actuel = st.session_state.bdd_chantiers
        doublon_existe = not df_actuel[
            (df_actuel["Nom du Chantier"] == nom_chantier) & 
            (df_actuel["Revenus (€)"] == revenus)
        ].empty
        
        if not nom_chantier:
            st.error("Veuillez donner un nom ou un numéro valide à votre chantier.")
        elif doublon_existe:
            st.error(f"Impossible d'enregistrer : Une version du chantier '{nom_chantier}' avec un montant de {revenus:,.2f} € existe déjà.")
        else:
            # Procédure de calcul normale si pas de doublon identique
            total_mats = (tonnes_enrobe * prix_enrobe) + (tonnes_sable * prix_sable)
            total_location = jours_totaux * cout_location
            total_salaires = (
                (jh_chef * (chef_mensuel / 30)) +
                (jh_ouvrier * (ouvrier_mensuel / 30)) +
                (jh_cond * (cond_mensuel / 30))
            )

            total_depenses = total_mats + total_location + total_salaires
            benefice_net = revenus - total_depenses
            roi = (benefice_net / total_depenses) * 100 if total_depenses > 0 else 0

            # Affichage immédiat des résultats
            st.markdown("---")
            st.write(f"**Coût Matériaux** : {total_mats:,.2f} €")
            st.write(f"**Coût Location** : {total_location:,.2f} €")
            st.write(f"**Coût Salaires** : {total_salaires:,.2f} €")
            
            if benefice_net >= 0:
                st.success(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")
            else:
                st.error(f"Bénéfice Net : {benefice_net:,.2f} € (ROI : {roi:.2f} %)")

            # Ajout sécurisé dans la base de données
            nouvel_enregistrement = pd.DataFrame([{
                "Nom du Chantier": nom_chantier,
                "Revenus (€)": revenus,
                "Dépenses (€)": total_depenses,
                "Bénéfice Net (€)": benefice_net,
                "ROI (%)": round(roi, 2)
            }])
            
            st.session_state.bdd_chantiers = pd.concat(
                [st.session_state.bdd_chantiers, nouvel_enregistrement], 
                ignore_index=True
            )
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

