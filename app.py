import streamlit as st
import requests
import pandas as pd
from datetime import date

# Adresa vášho Google Apps Script "mosta"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Účtovníctvo", layout="wide")
st.title("💸 Moja Účtovná Apka")

dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

with st.form("form_vypocet", clear_on_submit=True):
    v_datum = st.date_input("Dátum", date.today())
    v_den = dni_sk[v_datum.weekday()]
    
    st.subheader(f"Nový záznam: {v_den}")
    kategoria = st.radio("Kategória", ["Platba dodávateľovi (Výber)", "Ranný stav pokladne", "Večerný stav (Uzávierka)"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        v_firma = st.selectbox("Firma / Dodávateľ", ["Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky", "POKLADŇA"])
    with col2:
        v_suma = st.number_input("Suma (€)", min_value=0.0, step=0.1)
    
    v_poznamka = st.text_input("Poznámka")
    submit = st.form_submit_button("Uložiť záznam")

if submit:
    # Príprava dát pre odoslanie do tabuľky
    riadok = [
        v_datum.strftime("%d.%m.%Y"),                  # Stĺpec A: Datum
        v_den,                                         # Stĺpec B: Den
        f"Týždeň {v_datum.isocalendar()[1]}",          # Stĺpec C: Tyzden
        v_datum.year,                                  # Stĺpec D: Rok
        v_firma,                                       # Stĺpec E: Firma
        v_suma if kategoria == "Ranný stav pokladne" else 0,             # Stĺpec F: Rano
        v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0,      # Stĺpec G: Vybery
        v_suma if kategoria == "Večerný stav (Uzávierka)" else 0,         # Stĺpec H: Vecer
        0,                                             # Stĺpec I: Cista_Trzba
        kategoria,                                     # Stĺpec J: Kategoria
        v_poznamka                                     # Stĺpec K: Poznamka
    ]
    
    try:
        # Odoslanie dát cez Google Apps Script
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success("Dáta úspešne odoslané do Google tabuľky!")
        else:
            st.error(f"Chyba servera (Status: {response.status_code}). Skontrolujte nasadenie skriptu.")
    except Exception as e:
        st.error(f"Nepodarilo sa pripojiť k tabuľke: {e}")

st.divider()
st.info("Tip: Po uložení skontrolujte vašu Google tabuľku 'Uctovnictvo_Data'.")
