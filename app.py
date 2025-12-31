import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# URL adresa vášho Google Scriptu
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- NAČÍTANIE REÁLNYCH DÁT ---
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            stlpce_cisla = ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']
            for col in stlpce_cisla:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Prevod dátumu na skutočný dátumový formát pre mesačné filtre
            df['Datum_DT'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
            return df
    except:
        return pd.DataFrame()

df_data = naciť_data()

# --- ZOBRAZENIE REÁLNYCH SUMIAROV (Týždeň, Mesiac, Rok) ---
if not df_data.empty:
    dnes = date.today()
    akt_rok = dnes.year
    akt_mesiac = dnes.month
    akt_tyzden = f"{dnes.isocalendar()[1]}. týždeň"
    
    # Výpočty
    suma_rok = df_data[df_data['Rok'] == akt_rok]['Cista_Trzba'].sum()
    suma_tyzden = df_data[(df_data['Tyzden'] == akt_tyzden) & (df_data['Rok'] == akt_rok)]['Cista_Trzba'].sum()
    
    # Mesačný výpočet (filtrujeme cez pomocný stĺpec Datum_DT)
    suma_mesiac = df_data[(df_data['Datum_DT'].dt.month == akt_mesiac) & (df_data['Datum_DT'].dt.year == akt_rok)]['Cista_Trzba'].sum()

    # Zobrazenie 3 stĺpcov
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label=f"Tržba - {akt_tyzden}", value=f"{suma_tyzden:,.2f} €")
    with c2:
        # Názov mesiaca slovensky
        mesiace_sk = {1:"Január", 2:"Február", 3:"Marec", 4:"Apríl", 5:"Máj", 6:"Jún", 7:"Júl", 8:"August", 9:"September", 10:"Október", 11:"November", 12:"December"}
        st.metric(label=f"Tržba - {mesiace_sk[akt_mesiac]}", value=f"{suma_mesiac:,.2f} €")
    with c3:
        st.metric(label=f"Tržba - Rok {akt_rok}", value=f"{suma_rok:,.2f} €")
    
    # Graf
    df_graf = df_data[df_data['Cista_Trzba'] > 0].tail(7)
    if not df_graf.empty:
        fig = px.line(df_graf, x="Datum", y="Cista_Trzba", title="Trend posledných tržieb (€)", markers=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Čakám na prvé dáta...")

st.divider()

# --- ZVYŠOK KÓDU (FORMULÁR) ZOSTÁVA ROVNAKÝ ---
# ... (tu pokračuje tvoj kód s formulárom, ako si ho mal predtým)
