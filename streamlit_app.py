import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import StringIO
import requests

# Scarica il contenuto del Google Sheet
url = "https://docs.google.com/spreadsheets/d/15zspXv1dM__F0uunaG9hT_PsrPfU5MZJ-0IzjULzDXI/export?format=csv"
response = requests.get(url)
data = response.content

# Leggi i dati in un DataFrame
df = pd.read_csv(StringIO(data.decode('utf-8')))

# Sostituisci la virgola con il punto nella colonna 'Kg' e 'Media settimanale (Kg)'
df['Kg'] = df['Kg'].str.replace(',', '.')
df['Media settimanale (Kg)'] = df['Media settimanale (Kg)'].str.replace(',', '.')

# Converti a tipo float
df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce')
df['Media settimanale (Kg)'] = pd.to_numeric(df['Media settimanale (Kg)'], errors='coerce')

# Converti la colonna 'Data' in formato datetime
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
# Sistema la media settimanale
df['Media settimanale (Kg)'].fillna(0, inplace=True)

df.sort_values(by="Data", inplace=True, ascending=True)

# Crea il grafico con Plotly
fig = go.Figure()

# Aggiungi le serie
fig.add_trace(go.Scatter(x=df['Data'], y=df['Kg'], mode='lines+markers', name='Peso Giornaliero'))

# Aggiungi la serie per la media settimanale solo per i valori maggiori di 0.0
filtered_media_settimanale = df[df['Media settimanale (Kg)'] > 0.0]
fig.add_trace(go.Scatter(x=filtered_media_settimanale['Data'], y=filtered_media_settimanale['Media settimanale (Kg)'],
                         mode='lines+markers', name='Media Settimanale'))

# Aggiungi le linee verticali per i giorni con 'Kcal Piano nutrizionale' valorizzato
for index, row in df[df['Kcal Piano nutrizionale'].notna()].iterrows():
    fig.add_shape(
        dict(
            type="line",
            x0=row['Data'],
            x1=row['Data'],
            y0=0,
            y1=100,  # Puoi impostare questo valore in base all'intervallo desiderato sull'asse y
            line=dict(color="green", width=2)
        )
    )

    # Aggiungi etichetta con valore di 'Kcal Piano nutrizionale'
    fig.add_annotation(
        dict(
            x=row['Data'],
            y=75,  # Puoi impostare questo valore in base all'intervallo desiderato sull'asse y
            text=str(row['Kcal Piano nutrizionale']),
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="black",
            font=dict(size=10),
            ax=0,
            ay=-40
        )
    )

# Aggiorna il layout per impostare il range dell'asse Y
fig.update_layout(
    # title='Grafico del Peso Giornaliero e Media Settimanale',
    # xaxis_title='Data',
    yaxis_title='Peso (Kg)',
    yaxis=dict(range=[68, 75]),
    legend=dict(
        orientation="h",  # "h" per orizzontale, "v" per verticale
        x=0.5,  # Posizione orizzontale della legenda (0-1)
        y=-0.35,  # Posizione verticale della legenda (0-1)
        xanchor='center',  # Ancoraggio orizzontale
        yanchor='bottom'  # Ancoraggio verticale
    )
)

# Visualizza il grafico
# fig.show()

# Creazione dell'app Streamlit
st.set_page_config(
    page_title="Peso",
    page_icon=":scales:",
    layout="wide"
)

st.title(':scales: Weight report :weight_lifter:')
st.markdown("L'applicazione è alimentata attraverso un *Google Spreadsheet* e mostra l'andamento del **peso giornaliero** e della **media settimanale**. Le pesate vengono effettuate nelle medesime condizioni (dopo colazione, in mutande) e all'incirca allo stesso orario, tra le 6:00 e le 9:00 del mattino")

tab1, tab2 = st.tabs(["Grafico", "Tabella"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)
    
with tab2:
    df['Media settimanale (Kg)'] = df['Media settimanale (Kg)'].replace(0,'')
    df['Kcal Piano nutrizionale'] = df['Kcal Piano nutrizionale'].fillna('')
    
    st.dataframe(
        df,
        column_config={
            "Data": st.column_config.DateColumn(
                format="DD/MM/YYYY"
            ),
            "Kg": st.column_config.TextColumn(
                label="Peso (Kg)"
            ),
            "Media settimanale (Kg)": st.column_config.TextColumn(
                label="Peso medio della settimana (Kg)"
            ),
            "Kcal Piano nutrizionale": st.column_config.TextColumn(
                label="Intake calorico giornaliero"
            ),
        }, 
        use_container_width=True, 
        hide_index=True
    )

