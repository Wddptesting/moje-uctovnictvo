import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")

# Vizuálna úprava (farby a veľkosť písma)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #0080ff; }
    [data-testid="stMetricLabel"] { font-size: 1rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 Moja Účtovná Apka")

# --- FUNKCIA NA NAČÍTANIE DÁT ---
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                # Prevod na čísla (oprava čiarky na bodku a odstránenie medzier)
                cols_to_fix = ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']
                for col in cols_to_fix:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
                return df
    except Exception as e:
        st.error(f"Chyba spojenia: {e}")
    return pd.DataFrame()

df_data = naciť_data()

# --- VÝPOČTY PREHĽADOV ---
if not df_data.empty:
    dnes_dt = date.today()
    dnes_str = dnes_dt.strftime("%d.%m.%Y")
    v_rok = dnes_dt.year
    v_mesiac_filter = dnes_dt.strftime(".%m.%Y") # Hľadá napr. .12.2025

    # 1. DENNÁ TRŽBA (Dnes)
    suma_den = df_data[df_data['Datum'] == dnes_str]['Cista_Trzba'].sum()

    # 2. TÝŽDENNÁ TRŽBA (Posledných 7 dní)
    # Použijeme tail(30) na analýzu posledných riadkov a sčítame posledných 7 kalendárnych dní
    suma_tyzden = df_data['Cista_Trzba'].tail(7).sum()
    
    # 3. MESAČNÁ TRŽBA
    suma_mesiac = df_data[df_data['Datum'].astype(str).str.contains(v_mesiac_filter, na=False)]['Cista_Trzba'].sum()
    
    # 4. ROČNÁ TRŽBA
    suma_rok = df_data[df_data['Rok'] == v_rok]['Cista_Trzba'].sum()

    # Zobrazenie 4 stĺpcov (Den, Tyzden, Mesiac, Rok)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Dnešná tržba", value=f"{suma_den:,.2f} €")
    with c2:
        st.metric(label="Posledných 7 dní", value=f"{suma_tyzden:,.2f} €")
    with c3:
        mesiace_sk = {1:"Január", 2:"Február", 3:"Marec", 4:"Apríl", 5:"Máj", 6:"Jún", 7:"Júl", 8:"August", 9:"September", 10:"Október", 11:"November", 12:"December"}
        st.metric(label=f"{mesiace_sk[dnes_dt.month]}", value=f"{suma_mesiac:,.2f} €")
    with c4:
        st.metric(label=f"Rok {v_rok}", value=f"{suma_rok:,.2f} €")

    # Graf tržieb
    df_graf = df_data[df_data['Cista_Trzba'] > 0].tail(10)
    if not df_graf.empty:
        fig = px.bar(df_graf, x="Datum", y="Cista_Trzba", title="Prehľad tržieb po dňoch (€)", color_discrete_sequence=['#0080ff'])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Načítavam dáta z tabuľky...")

st.divider()

# --- FORMULÁR PRE ZÁPIS ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
v_datum = st.date_input("Dátum záznamu", dnes_dt)
v_den = dni_sk[v_datum.weekday()]
v_tyzden_text = f"{v_datum.isocalendar()[1]}. týždeň"

with st.form("form_zapis", clear_on_submit=True):
    kat = st.radio("Kategória", ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"], horizontal=True)
    firma = st.selectbox("Položka/Firma", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky"])
    suma = st.number_input("Suma v €", min_value=0.0, step=0.01, format="%.2f")
    pozn = st.text_input("Poznámka")
    
    tlacidlo = st.form_submit_button("💾 ULOŽIŤ ZÁZNAM")

if tlacidlo:
    novy_riadok = [
        v_datum.strftime("%d.%m.%Y"), v_den, v_tyzden_text, v_datum.year, firma,
        suma if kat == "Ranný stav pokladne" else 0,
        suma if kat == "Platba dodávateľovi (Výber)" else 0,
        suma if kat == "Večerný stav (Uzávierka)" else 0,
        0, # Cista_Trzba - vypočíta Google Tabuľka
        kat, pozn
    ]
    try:
        requests.post(SCRIPT_URL, json={"row": novy_riadok})
        st.success(f"Uložené: {kat} - {suma} €")
        st.rerun()
    except:
        st.error("Chyba pri odosielaní.")
