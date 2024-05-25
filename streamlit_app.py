import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import StringIO
import requests
from datetime import datetime, timedelta

today = datetime.now().date()
year = today.year
first_day = datetime(year, 1, 1).date()

# Stato per memorizzare le date selezionate
if 'start_date' not in st.session_state:
    st.session_state.start_date = first_day
if 'end_date' not in st.session_state:
    st.session_state.end_date = today

# Scarica il contenuto del Google Sheet
url = "https://docs.google.com/spreadsheets/d/15zspXv1dM__F0uunaG9hT_PsrPfU5MZJ-0IzjULzDXI/export?format=csv"
response = requests.get(url)
data = response.content

# Leggi i dati in un DataFrame
df = pd.read_csv(StringIO(data.decode('utf-8')))

df.drop(columns="Media settimanale (Kg)", inplace=True)
df = df.dropna(subset=['Kg'])

# Sostituisci la virgola con il punto nella colonna 'Kg'
df['Kg'] = df['Kg'].str.replace(',', '.')

# Converti a tipo float
df['Kg'] = pd.to_numeric(df['Kg'], errors='coerce')

# Converti la colonna 'Data' in formato datetime
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')

if st.session_state.end_date >= st.session_state.start_date:
    df = df[(df['Data'].dt.date >= st.session_state.start_date) & (df['Data'].dt.date <= st.session_state.end_date)]

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

df['Media ultimi 7 giorni'] = df['Kg'].rolling(window=7).mean()
df['Media ultimi 7 giorni'] = df['Media ultimi 7 giorni'].round(2)

# Crea il grafico con Plotly
fig = go.Figure()

# Aggiungi le serie
fig.add_trace(go.Scatter(x=df['Data'], y=df['Kg'], mode='lines+markers', name='Peso Giornaliero'))

# Aggiungi la serie per la media settimanale solo per i valori maggiori di 0.0
filtered_media_settimanale = df[df['Media ultimi 7 giorni'] > 0.0]
fig.add_trace(go.Scatter(x=filtered_media_settimanale['Data'], y=filtered_media_settimanale['Media ultimi 7 giorni'],
                         mode='lines+markers', name='Peso medio negli ultimi 7 giorni'))

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
    yaxis_title='Peso (Kg)',
    yaxis=dict(range=[69, 75]),
    legend=dict(
        orientation="h",  # "h" per orizzontale, "v" per verticale
        x=0.5,  # Posizione orizzontale della legenda (0-1)
        y=-0.35,  # Posizione verticale della legenda (0-1)
        xanchor='center',  # Ancoraggio orizzontale
        yanchor='bottom'  # Ancoraggio verticale
    )
)

# Creazione dell'app Streamlit
st.set_page_config(
    page_title="Peso",
    page_icon=":scales:",
    layout="wide"
)

st.title(':scales: Weight report :weight_lifter:')
st.divider()
col1, col2, col3, col4 = st.columns(4)

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

def set_start_date():
    st.session_state.start_date = st.session_state.start_date_input

def set_end_date():
    st.session_state.end_date = st.session_state.end_date_input

with st.sidebar:
    
    st.header('Periodo di interesse')
    st.caption('Filtra i dati per concentrarti su una finestra temporale specifica')
    
    # Widget date_input con le date iniziali dallo stato della sessione
    st.date_input(':spiral_calendar_pad: Dal:', value = st.session_state.start_date, max_value = today, format="DD.MM.YYYY", key='start_date_input', on_change=set_start_date)
    st.date_input(':spiral_calendar_pad: al:', value = st.session_state.end_date, max_value = today, format="DD.MM.YYYY", key='end_date_input', on_change=set_end_date)
    
    if st.session_state.end_date >= st.session_state.start_date:
        observed_period = st.session_state.end_date - st.session_state.start_date 
        st.info(':information_source: Stai visualizzando le informazioni per un periodo di **{} giorni**, che va dal {} al {}'.format(
            observed_period.days,
            st.session_state.start_date.strftime("%d/%m/%Y"), 
            st.session_state.end_date.strftime("%d/%m/%Y"))
        )
    else:
        st.error(':warning: L\'intervallo temporale inserito non è corretto!')
              
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
    st.metric(":arrow_down: Minimo", str(df['Kg'].min())+" Kg", giorno_minimo_peso+", "+str(data_minimo_peso.strftime("%d/%m/%Y")))
    
with col3:
    df = df.sort_values(by='Data')
    df = df.dropna(subset=['Kg'])
    max_date = df['Data'].max()
    start_date = max_date - pd.DateOffset(6)
    end_date = max_date
    # Filtra il DataFrame per ottenere solo le osservazioni degli ultimi 7 giorni
    last_7_days = df[(df['Data'] >= start_date) & (df['Data'] <= end_date)]
    # Calcola la media dei pesi
    media_pesi_ultimi_7_giorni = last_7_days['Kg'].mean()
    
    # Media ultimi 7 giorni
    st.metric(':spiral_calendar_pad: Media ultimi 7 giorni', 
              f"{media_pesi_ultimi_7_giorni:.2f} Kg", 
              f"dal {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}")

with col4:
    # Trova l'indice del valore massimo del peso giornaliero
    indice_massimo_peso = df['Kg'].idxmax()
    # Estrai la data corrispondente all'indice minimo
    data_massimo_peso = df.loc[indice_massimo_peso, 'Data']
    giorno_massimo_peso = df.loc[indice_massimo_peso, 'Giorno']
    st.metric(":arrow_up: Massimo", str(df['Kg'].max())+" Kg", giorno_massimo_peso+", "+str(data_massimo_peso.strftime("%d/%m/%Y")))

tab1, tab2 = st.tabs(["Grafico", "Tabella"])

with tab1:
    st.plotly_chart(fig, use_container_width=True)
    
with tab2:
    df.drop('Ora_in_minuti', inplace=True, axis='columns')
    df['Kcal Piano nutrizionale'] = df['Kcal Piano nutrizionale'].fillna('')
    df = df[['Giorno', 'Data', 'Ora', 'Kg', 'Media ultimi 7 giorni','Kcal Piano nutrizionale']]

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
