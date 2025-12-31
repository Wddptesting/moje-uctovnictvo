import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")

# Vizuálna úprava metrík
st.markdown("""<style>[data-testid="stMetricValue"] { font-size: 2rem; color: #0080ff; }</style>""", unsafe_allow_html=True)

st.title("💸 Moja Účtovná Apka")

# --- FUNKCIA NA NAČÍTANIE A OPRAVU DÁT ---
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                
                # KLÚČOVÁ OPRAVA: Prevod na čísla a odstránenie chýb
                cols_to_fix = ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']
                for col in cols_to_fix:
                    if col in df.columns:
                        # Odstráni medzery, nahradí čiarky bodkami a prevedie na číslo
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
                
                return df
    except Exception as e:
        st.error(f"Chyba spojenia: {e}")
    return pd.DataFrame()

df_data = naciť_data()

# --- VÝPOČTY PREHĽADOV ---
if not df_data.empty:
    dnes = date.today()
    v_rok = dnes.year
    v_mesiac_str = dnes.strftime(".%m.%Y") # Hľadá napr. .12.2025
    v_tyzden_text = f"{dnes.isocalendar()[1]}. týždeň"

    # Filtrovanie dát pre súčty
    # Týždeň
    suma_tyzden = df_data[(df_data['Tyzden'] == v_tyzden_text) & (df_data['Rok'] == v_rok)]['Cista_Trzba'].sum()
    # Mesiac
    suma_mesiac = df_data[df_data['Datum'].astype(str).str.contains(v_mesiac_str, na=False)]['Cista_Trzba'].sum()
    # Rok
    suma_rok = df_data[df_data['Rok'] == v_rok]['Cista_Trzba'].sum()

    # Zobrazenie kariet
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Tento týždeň", value=f"{suma_tyzden:,.2f} €")
    with c2:
        mesiace_sk = {1:"Január", 2:"Február", 3:"Marec", 4:"Apríl", 5:"Máj", 6:"Jún", 7:"Júl", 8:"August", 9:"September", 10:"Október", 11:"November", 12:"December"}
        st.metric(label=f"Mesiac {mesiace_sk[dnes.month]}", value=f"{suma_mesiac:,.2f} €")
    with c3:
        st.metric(label=f"Rok {v_rok}", value=f"{suma_rok:,.2f} €")

    # Graf - ukážeme len posledných 10 záznamov, kde je tržba nenulová
    df_graf = df_data[df_data['Cista_Trzba'] > 0].tail(10)
    if not df_graf.empty:
        fig = px.bar(df_graf, x="Datum", y="Cista_Trzba", title="Prehľad tržieb po dňoch (€)", color="Cista_Trzba")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tabuľka je prázdna alebo sa načítava...")

st.divider()

# --- FORMULÁR PRE ZÁPIS ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
v_datum = st.date_input("Dátum", dnes)
v_den = dni_sk[v_datum.weekday()]
v_tyzden_cislo = f"{v_datum.isocalendar()[1]}. týždeň"

with st.form("main_form", clear_on_submit=True):
    kat = st.radio("Kategória", ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"], horizontal=True)
    firma = st.selectbox("Položka", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky"])
    suma = st.number_input("Suma v €", min_value=0.0, step=0.01, format="%.2f")
    pozn = st.text_input("Poznámka")
    
    tlacidlo = st.form_submit_button("💾 Uložiť záznam")

if tlacidlo:
    novy_riadok = [
        v_datum.strftime("%d.%m.%Y"), v_den, v_tyzden_cislo, v_datum.year, firma,
        suma if kat == "Ranný stav pokladne" else 0,
        suma if kat == "Platba dodávateľovi (Výber)" else 0,
        suma if kat == "Večerný stav (Uzávierka)" else 0,
        0, # Cista_Trzba (počíta Google Tabuľka)
        kat, pozn
    ]
    requests.post(SCRIPT_URL, json={"row": novy_riadok})
    st.success("Uložené! Obnovte stránku pre nové súčty.")
    st.rerun()
