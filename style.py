import streamlit as st

def appliquer_theme_moderne():
    """Applique un habillage visuel épuré, moderne et structuré à toute l'application."""
    st.markdown(
        """
        <style>
        /* --- POLICE ET ESPACEMENT GLOBAL --- */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* --- CARTES KPI (st.metric) --- */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-left: 4px solid #F59E0B;
            padding: 14px 18px;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            opacity: 0.85;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            font-weight: 700 !important;
        }

        /* --- ENCADRÉS EXPANDERS & CONTENEURS --- */
        [data-testid="stExpander"] {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.015);
        }

        /* --- BOUTONS MODERNES --- */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        /* --- BARRE LATÉRALE --- */
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.2);
        }

        /* --- BADGE EN-TÊTE --- */
        .banner-titre {
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.02) 100%);
            border-left: 5px solid #F59E0B;
            padding: 1rem 1.5rem;
            border-radius: 0 10px 10px 0;
            margin-bottom: 1.5rem;
        }
        .banner-titre h1 {
            margin: 0;
            font-size: 1.85rem;
            font-weight: 700;
        }
        .banner-titre p {
            margin: 4px 0 0 0;
            opacity: 0.8;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def afficher_entete_page(titre, sous_titre):
    """Affiche un bandeau d'en-tête propre et harmonisé en haut de chaque page."""
    st.markdown(
        f"""
        <div class="banner-titre">
            <h1>{titre}</h1>
            <p>{sous_titre}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
