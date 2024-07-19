import os
import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Obtenez le répertoire courant du script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Charger les données nécessaires pour vérifier les IDs valides
path_df_train = os.path.join(current_directory, "df300.csv")
df_train = pd.read_csv(path_df_train)

st.set_page_config(layout="wide")

st.markdown(
    "<h1 style='text-align: center; color: black;'>Risque de non-remboursement</h1>",
    unsafe_allow_html=True,
)
sk_id_curr = st.text_input("Entrez le SK_ID_CURR:")

# Fonction pour convertir les nombres de jours Excel en dates
def convert_excel_date(excel_date_number):
    if pd.isna(excel_date_number):
        return "Non disponible"
    return (datetime(1900, 1, 1) + timedelta(days=excel_date_number - 2)).strftime('%d/%m/%Y')

# Fonction pour créer une jauge
def create_gauge(proba):
    if proba <= 30:
        gauge_color = "green"
    elif proba <= 52:
        gauge_color = "orange"
    else:
        gauge_color = "red"
        
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = proba,
        title = {'text': "Probabilité de non-remboursement"},
        number = {'font': {'color': gauge_color}},  # Change the color of the number
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 30], 'color': "green"},
                {'range': [30, 52], 'color': "orange"},
                {'range': [52, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': proba
            }
        }
    ))
    return fig

# Fonction pour créer le graphique de distribution
def create_distribution_chart(feature, client_value, distribution_data):
    fig = px.histogram(distribution_data, x=feature, nbins=50, title=f'Distribution de {feature}')
    fig.add_vline(x=client_value, line_width=3, line_dash="dash", line_color="red")
    return fig

# Base URL de l'API déployée
api_base_url = "https://p7-ocr-api-mathis-d22bcf66c298.herokuapp.com"

if st.button("Run"):
    if sk_id_curr.isdigit() and int(sk_id_curr) in df_train['SK_ID_CURR'].values:
        # Appel à l'API pour la prédiction
        response = requests.post(
            f"{api_base_url}/predict", json={"SK_ID_CURR": int(sk_id_curr)}
        )
        if response.status_code != 200:
            st.error(f"Erreur lors de l'appel à l'API: {response.status_code}")
        else:
            data = response.json()
            proba = data["probability"]

            fig = create_gauge(proba)
            st.plotly_chart(fig)

            decision_message = (
                "Le prêt sera accordé." if proba < 53 else "Le prêt ne sera pas accordé."
            )
            st.markdown(
                f"<div style='text-align: center; color: {'green' if proba < 53 else 'red'}; font-size:30px; border:2px solid {'green' if proba < 53 else 'red'}; padding:10px;'>{decision_message}</div>",
                unsafe_allow_html=True,
            )

        # Appel à l'API pour les informations personnelles
        info_response = requests.post(
            f"{api_base_url}/info", json={"SK_ID_CURR": int(sk_id_curr)}
        )
        if info_response.status_code != 200:
            st.error(f"Erreur lors de l'appel à l'API pour les informations personnelles: {info_response.status_code}")
        else:
            info_data = info_response.json()
            st.markdown("<h2>Informations Personnelles</h2>", unsafe_allow_html=True)
            st.write(f"**Date de Naissance:** {convert_excel_date(info_data.get('Date_Naissance', 'Non disponible'))}")
            st.write(f"**Emploi Depuis:** {convert_excel_date(info_data.get('Emploi_Depuis', 'Non disponible'))}")
            st.write(f"**Statut Marital:** {info_data.get('NAME_FAMILY_STATUS_Married', 'Non disponible')}")
            st.write(f"**Revenu par Personne:** {info_data.get('INCOME_PER_PERSON', 'Non disponible')}")
            st.write(f"**Niveau d'Éducation supérieur:** {info_data.get('NAME_EDUCATION_TYPE_Highereducation', 'Non disponible')}")

# Sélection de la variable pour la distribution
st.markdown("<h2>Analyse de Distribution</h2>", unsafe_allow_html=True)
feature_list = [
    "EXT_SOURCE_2", "EXT_SOURCE_3", "EXT_SOURCE_1", "PAYMENT_RATE", 
    "DAYS_BIRTH", "DAYS_EMPLOYED", "DAYS_ID_PUBLISH", "DAYS_REGISTRATION", 
    "AMT_ANNUITY", "DAYS_EMPLOYED_PERC"
]
feature = st.selectbox("Choisissez une variable pour voir la distribution:", feature_list)

if feature:
    if sk_id_curr.isdigit() and int(sk_id_curr) in df_train['SK_ID_CURR'].values:
        dist_response = requests.post(
            f"{api_base_url}/distribution", json={"SK_ID_CURR": int(sk_id_curr), "feature": feature}
        )
        if dist_response.status_code != 200:
            st.error(f"Erreur lors de l'appel à l'API pour la distribution: {dist_response.status_code}")
        else:
            dist_data = dist_response.json()
            client_value = dist_data["client_value"]
            distribution = pd.DataFrame(dist_data["distribution"], columns=[feature])

            dist_chart = create_distribution_chart(feature, client_value, distribution)
            st.plotly_chart(dist_chart)
    else:
        st.error("Veuillez entrer un SK_ID_CURR valide.")
