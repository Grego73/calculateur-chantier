import streamlit as st
import database as db

def afficher_onglet_marche_actuel():
    st.header("🌍 Observatoire en Direct du Marché des Coopératives")
    st.write("Consultez ci-dessous l'état des prix du marché mis à jour en temps réel par les administrateurs.")

    try:
        # Lecture en flux direct depuis Firebase
        offres_stream = db.db.collection("offres_cooperatives").stream()
        
        marche_vrac = {}
        marche_structure = {}

        # Table d'affichage pour harmoniser l'orthographe textuelle
        harmonisation_noms = {
            "Armature": "Armature métallique", "Tôle": "Plaque de tôle ondulée", 
            "Tuyaux": "Tuyaux d'eau standards", "Canalisations": "Canalisations eaux usées", 
            "Poutres": "Poutres en acier", "Panneaux": "Panneaux de signalisation"
        }

        for doc in offres_stream:
            data = doc.to_dict()
            mat_brut = data.get("materiau")
            mat = harmonisation_noms.get(mat_brut, mat_brut)
            t_log = data.get("type_logistique")
            
            cle_affichage = f"{int(data.get('prix_unitaire'))} € / {data.get('unite')}"
            if data.get("quantite_dispo") != "illimité":
                cle_affichage += f" *({data.get('quantite_dispo')})*"

            structure_cible = marche_vrac if t_log == "vrac" else marche_structure
            
            if mat not in structure_cible:
                structure_cible[mat] = {}
            if cle_affichage not in structure_cible[mat]:
                structure_cible[mat][cle_affichage] = []
                
            structure_cible[mat][cle_affichage].append(data.get("cooperative"))

        if marche_vrac or marche_structure:
            # --- SECTION 1 ---
            st.markdown("### 🧱 Matériaux en vrac (Tonne)")
            for mat_nom, offres in marche_vrac.items():
                st.markdown(f"**• {mat_nom}**")
                for desc_prix, coops in offres.items():
                    liste_coops_txt = " / ".join(coops)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◦ **{liste_coops_txt} :** {desc_prix}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- SECTION 2 ---
            st.markdown("### ⚙️ Éléments de structure & Réseaux (Unité)")
            for mat_nom, offres in marche_structure.items():
                st.markdown(f"**• {mat_nom}**")
                for desc_prix, coops in offres.items():
                    liste_coops_txt = " / ".join(coops)
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;◦ **{liste_coops_txt} :** {desc_prix}")
        else:
            st.info("💡 L'observatoire du marché est vide. Un administrateur doit injecter le HTML du jeu depuis l'Espace Direction.")

    except Exception as e:
        st.error(f"❌ Impossible de charger les données du marché : {e}")
