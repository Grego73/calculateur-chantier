import streamlit as st

st.set_page_config(page_title="Calculateur de Chantier", page_icon="🏗️")
st.title("Calculateur de Rentabilité de Chantier")

st.header("--- PARAMÈTRES GÉNÉRAUX ---")
revenus = st.number_input("Revenus prévus du chantier (€) :", value=214599)
jours_totaux = st.number_input("Durée totale du chantier (jours) :", value=15)
cout_location = st.number_input("Coût de location matériel / jour (€) :", value=1200)

st.header("--- MATÉRIAUX ---")
tonnes_enrobe = st.number_input("Tonnes d'enrobé nécessaires :", value=618)
prix_enrobe = st.number_input("Prix de la tonne d'enrobé (€) :", value=42)
tonnes_sable = st.number_input("Tonnes de sable nécessaires :", value=488)
prix_sable = st.number_input("Prix de la tonne de sable (€) :", value=12)

st.header("--- GRILLE SALARIALE & HEURES ---")
chef_mensuel = st.number_input("Salaire mensuel Chef (€) :", value=1566)
jh_chef = st.number_input("Total Jours-Homme Chef :", value=16)
ouvrier_mensuel = st.number_input("Salaire mensuel Ouvrier (€) :", value=1616)
jh_ouvrier = st.number_input("Total Jours-Homme Ouvrier :", value=48)
cond_mensuel = st.number_input("Salaire mensuel Conducteur (€) :", value=1571)
jh_cond = st.number_input("Total Jours-Homme Conducteur :", value=28)

if st.button("LANCER LE CALCUL", type="primary"):
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

    st.header("--- RÉSULTATS ---")
    st.write(f"Coût Matériaux : {total_mats:,.2f} €")
    st.write(f"Coût Location : {total_location:,.2f} €")
    st.write(f"Coût Salaires : {total_salaires:,.2f} €")
    st.markdown("---")
    st.write(f"Total Dépenses : {total_depenses:,.2f} €")
    
    if benefice_net >= 0:
        st.success(f"Bénéfice Net : {benefice_net:,.2f} €")
    else:
        st.error(f"Bénéfice Net : {benefice_net:,.2f} €")
        
    st.info(f"ROI : {roi:.2f} %")

