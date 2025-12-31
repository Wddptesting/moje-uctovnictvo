import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# SEM VLOŽTE VAŠU URL ADRESU (končí na /exec)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- NAČÍTANIE REÁLNYCH DÁT ---
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            # Vytvorenie tabuľky z JSON dát (prvý riadok sú hlavičky)
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            # Prevod na čísla pre výpočty
            stlpce_cisla = ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']
            for col in stlpce_cisla:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
    except Exception as e:
        return pd.DataFrame()

df_data = naciť_data()

# --- ZOBRAZENIE REÁLNYCH SUMIAROV ---
if not df_data.empty:
    dnes = date.today()
    akt_rok = dnes.year
    akt_tyzden = f"{dnes.isocalendar()[1]}. týždeň"
    
    # Filtrovanie pre sumy
    suma_rok = df_data[df_data['Rok'] == akt_rok]['Cista_Trzba'].sum()
    suma_tyzden = df_data[(df_data['Tyzden'] == akt_tyzden) & (df_data['Rok'] == akt_rok)]['Cista_Trzba'].sum()

    c1, c2 = st.columns(2)
    with c1:
        st.metric(label=f"Tržba - {akt_tyzden}", value=f"{suma_tyzden:,.2f} €")
    with c2:
        st.metric(label=f"Tržba - Rok {akt_rok}", value=f"{suma_rok:,.2f} €")
    
    # Čiarový graf posledných 7 tržieb
    df_graf = df_data[df_data['Cista_Trzba'] > 0].tail(7)
    if not df_graf.empty:
        fig = px.line(df_graf, x="Datum", y="Cista_Trzba", title="Trend tržieb (€)", markers=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Čakám na prvé dáta z tabuľky...")

st.divider()

# --- FORMULÁR PRE ZÁPIS ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
v_datum = st.date_input("Vyber dátum", date.today())
v_den = dni_sk[v_datum.weekday()]
v_tyzden_text = f"{v_datum.isocalendar()[1]}. týždeň"

with st.form("form_vypocet", clear_on_submit=True):
    kategoria = st.radio("Kategória", ["Platba dodávateľovi (Výber)", "Ranný stav pokladne", "Večerný stav (Uzávierka)"], horizontal=True)
    v_firma = st.selectbox("Firma / Dodávateľ", ["Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky", "POKLADŇA"])
    v_suma = st.number_input("Suma (€)", min_value=0.0, step=0.1)
    v_poznamka = st.text_input("Poznámka")
    submit = st.form_submit_button("Uložiť záznam")

if submit:
    # Dopočet tržby pre okamžitú vizualizáciu
    cista = 0
    if kategoria == "Večerný stav (Uzávierka)":
        dnesne = df_data[df_data['Datum'] == v_datum.strftime("%d.%m.%Y")]
        vybery_dnes = dnesne['Vybery'].sum() + (v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0)
        rano_dnes = dnesne[dnesne['Kategoria'] == "Ranný stav pokladne"]['Rano'].sum()
        cista = v_suma + vybery_dnes - rano_dnes

    riadok = [v_datum.strftime("%d.%m.%Y"), v_den, v_tyzden_text, v_datum.year, v_firma, 
              v_suma if kategoria == "Ranný stav pokladne" else 0,
              v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0,
              v_suma if kategoria == "Večerný stav (Uzávierka)" else 0,
              cista, kategoria, v_poznamka]
    
    requests.post(SCRIPT_URL, json={"row": riadok})
    st.success("Dáta odoslané! Obnovte apku.")
    st.rerun()
