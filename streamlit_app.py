import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import StringIO
import requests
from datetime import datetime, timedelta

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

# Calcola il valore medio dell'orario di pesata
df['Ora'] = pd.to_datetime(df['Ora'], format='%H:%M').dt.time

# Converti l'orario in minuti
df['Ora_in_minuti'] = df['Ora'].apply(lambda x: x.hour * 60 + x.minute)

# Calcola la media dei minuti
media_minuti = df['Ora_in_minuti'].mean()
# Converti il risultato in formato datetime.time
media_ora = datetime.min + timedelta(minutes=media_minuti)
media_ora = media_ora.time()

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
# st.markdown("Statistiche peso aggiornate quotidianamente. I valori usati per le metriche vengono prelevati da un *Google Spreadisheet*")
st.divider()
col1, col2, col3 = st.columns(3)

st.write(
    """
    <style>
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
    background-color: rgba(28, 131, 225, 0.1);
    border: 1px solid rgba(28, 131, 225, 0.1);
    padding: 5% 5% 5% 10%;
    border-radius: 5px;
    color: rgb(30, 103, 119);
    overflow-wrap: break-word;
    }

    /* breakline for metric text         */
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
    overflow-wrap: break-word;
    white-space: break-spaces;
    color: red;
    }
    </style>
    """
, unsafe_allow_html=True)


with col1:
    # Trova il valore minimo dell'orario
    min_ora = divmod(df['Ora_in_minuti'].min(), 60)
    # Trova il valore massimo dell'orario
    max_ora = divmod(df['Ora_in_minuti'].max(), 60)
    st.metric(
        ":clock7: Orario medio pesata", 
        media_ora.strftime('%H:%M'), 
        f"min: {min_ora[0]:02g}:{min_ora[1]:02g}, max: {max_ora[0]:02g}:{max_ora[1]:02g}"
    )
    
with col2:
    # Trova l'indice del valore minimo del peso giornaliero
    indice_minimo_peso = df['Kg'].idxmin()
    # Estrai la data corrispondente all'indice minimo
    data_minimo_peso = df.loc[indice_minimo_peso, 'Data']
    giorno_minimo_peso = df.loc[indice_minimo_peso, 'Giorno']
    st.metric(":arrow_down: Minimo", df['Kg'].min(), giorno_minimo_peso+", "+str(data_minimo_peso.strftime("%d/%m/%Y")))
    
with col3:
    # Trova l'indice del valore massimo del peso giornaliero
    indice_massimo_peso = df['Kg'].idxmax()
    # Estrai la data corrispondente all'indice minimo
    data_massimo_peso = df.loc[indice_massimo_peso, 'Data']
    giorno_massimo_peso = df.loc[indice_massimo_peso, 'Giorno']
    st.metric(":arrow_up: Massimo", df['Kg'].max(), giorno_massimo_peso+", "+str(data_massimo_peso.strftime("%d/%m/%Y")))

tab1, tab2 = st.tabs(["Grafico", "Tabella"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)
    
with tab2:
    df.drop('Ora_in_minuti', inplace=True, axis='columns')
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

