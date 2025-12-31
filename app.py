import streamlit as st
import requests
import pandas as pd
from datetime import date

# Tvoja URL adresa
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

# --- TOTO JE ZMENA: Kalkulácia hodnôt mimo formulára, aby reagovali na zmenu ---
v_datum = st.date_input("Vyber dátum", date.today())
v_den = dni_sk[v_datum.weekday()]
v_tyzden_cislo = v_datum.isocalendar()[1]
v_rok = v_datum.year
v_tyzden_text = f"{v_tyzden_cislo}. týždeň"

# Dynamický podnadpis, ktorý sa mení podľa kalendára
st.subheader(f"Záznam pre: {v_den} | {v_tyzden_text} | Rok {v_rok}")

with st.form("form_vypocet", clear_on_submit=True):
    kategoria = st.radio("Kategória", ["Platba dodávateľovi (Výber)", "Ranný stav pokladne", "Večerný stav (Uzávierka)"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        v_firma = st.selectbox("Firma / Dodávateľ", ["Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky", "POKLADŇA"])
    with col2:
        v_suma = st.number_input("Suma (€)", min_value=0.0, step=0.1)
    
    v_poznamka = st.text_input("Poznámka")
    submit = st.form_submit_button("Uložiť záznam")

if submit:
    # Definícia hodnôt
    rano = v_suma if kategoria == "Ranný stav pokladne" else 0
    vybery = v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0
    vecer = v_suma if kategoria == "Večerný stav (Uzávierka)" else 0
    
    riadok = [
        v_datum.strftime("%d.%m.%Y"), 
        v_den, 
        v_tyzden_text, 
        v_rok, 
        v_firma, 
        rano, 
        vybery, 
        vecer, 
        0, # Cista_Trzba (počíta vzorec v tabuľke)
        kategoria, 
        v_poznamka
    ]
    
    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success(f"Dáta pre {v_datum.strftime('%d.%m.%Y')} úspešne uložené!")
        else:
            st.error("Chyba pripojenia k tabuľke.")
    except Exception as e:
        st.error(f"Chyba: {e}")

st.divider()
st.info("Tip: Po uložení uzávierky skontroluj hárok 'PREHĽAD' v Google tabuľke pre súčty.")
