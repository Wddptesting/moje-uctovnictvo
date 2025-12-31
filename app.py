import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# --- KONFIGURÁCIA ---
# Vložte vašu URL adresu z Google Apps Script (končí na /exec)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide", initial_sidebar_state="collapsed")

# Úprava vzhľadu (väčšie písmo pre metriky)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 Moja Účtovná Apka")

# --- FUNKCIA NA NAČÍTANIE DÁT ---
@st.cache_data(ttl=60)  # Dáta sa obnovia každú minútu
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                # Prevod stĺpcov na čísla
                for col in ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                return df
    except Exception as e:
        st.error(f"Chyba pri načítaní: {e}")
    return pd.DataFrame()

df_data = naciť_data()

# --- VÝPOČTY A ZOBRAZENIE ---
if not df_data.empty:
    dnes = date.today()
    akt_rok = dnes.year
    akt_mesiac_cislo = dnes.month
    akt_tyzden_text = f"{dnes.isocalendar()[1]}. týždeň"
    
    # 1. Týždenná tržba (podľa textu týždňa)
    suma_tyzden = df_data[(df_data['Tyzden'] == akt_tyzden_text) & (df_data['Rok'] == akt_rok)]['Cista_Trzba'].sum()
    
    # 2. Mesačná tržba (Hľadáme reťazec mesiaca v dátume, napr. ".12.2025")
    mesiac_str = dnes.strftime(".%m.%Y")
    suma_mesiac = df_data[df_data['Datum'].astype(str).str.contains(mesiac_str, na=False)]['Cista_Trzba'].sum()
    
    # 3. Ročná tržba
    suma_rok = df_data[df_data['Rok'] == akt_rok]['Cista_Trzba'].sum()

    # Zobrazenie v troch stĺpcoch
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label=f"Týždeň ({akt_tyzden_text})", value=f"{suma_tyzden:,.2f} €")
    with c2:
        mesiace_sk = {1:"Január", 2:"Február", 3:"Marec", 4:"Apríl", 5:"Máj", 6:"Jún", 7:"Júl", 8:"August", 9:"September", 10:"Október", 11:"November", 12:"December"}
        st.metric(label=f"Mesiac {mesiace_sk[akt_mesiac_cislo]}", value=f"{suma_mesiac:,.2f} €")
    with c3:
        st.metric(label=f"Rok {akt_rok}", value=f"{suma_rok:,.2f} €")
    
    # Graf posledných 7 uzávierok
    df_graf = df_data[df_data['Cista_Trzba'] > 0].tail(7)
    if not df_graf.empty:
        fig = px.line(df_graf, x="Datum", y="Cista_Trzba", title="Trend tržieb (€)", markers=True)
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Zatiaľ nie sú k dispozícii žiadne dáta.")

st.divider()

# --- FORMULÁR PRE ZÁPIS ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
v_datum = st.date_input("Vyber dátum", date.today())
v_den = dni_sk[v_datum.weekday()]
v_tyzden_cislo = f"{v_datum.isocalendar()[1]}. týždeň"

with st.form("uctovna_form", clear_on_submit=True):
    kategoria = st.radio("Čo zapisujete?", ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"], horizontal=True)
    v_firma = st.selectbox("Firma / Položka", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky"])
    v_suma = st.number_input("Suma v €", min_value=0.0, step=0.1, format="%.2f")
    v_poznamka = st.text_input("Poznámka")
    
    poslat = st.form_submit_button("✅ Uložiť do tabuľky")

if poslat:
    # Príprava riadku (Cista_Trzba na indexe 8 sa nechá 0, vypočíta ju vzorec v Exceli)
    novy_riadok = [
        v_datum.strftime("%d.%m.%Y"), 
        v_den, 
        v_tyzden_cislo, 
        v_datum.year, 
        v_firma,
        v_suma if kategoria == "Ranný stav pokladne" else 0,
        v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0,
        v_suma if kategoria == "Večerný stav (Uzávierka)" else 0,
        0, # Toto je stĺpec I, ktorý prepočíta tabuľka
        kategoria,
        v_poznamka
    ]
    
    try:
        res = requests.post(SCRIPT_URL, json={"row": novy_riadok})
        if res.status_code == 200:
            st.success("Záznam bol úspešne uložený!")
            st.cache_data.clear() # Vymaže vyrovnávaciu pamäť, aby sa dáta hneď načítali
            st.rerun()
        else:
            st.error("Chyba pri komunikácii s Google Scriptom.")
    except Exception as e:
        st.error(f"Nepodarilo sa odoslať dáta: {e}")
