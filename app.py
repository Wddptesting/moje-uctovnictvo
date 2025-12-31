import streamlit as st
import requests
import pandas as pd
from datetime import date

# Adresa vášho Google Apps Script "mosta"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

with st.form("form_vypocet", clear_on_submit=True):
    v_datum = st.date_input("Dátum", date.today())
    v_den = dni_sk[v_datum.weekday()]
    v_tyzden_cislo = v_datum.isocalendar()[1]
    v_rok = v_datum.year
    
    st.subheader(f"Nový záznam: {v_den} | Týždeň {v_tyzden_cislo}")
    kategoria = st.radio("Kategória", ["Platba dodávateľovi (Výber)", "Ranný stav pokladne", "Večerný stav (Uzávierka)"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        v_firma = st.selectbox("Firma / Dodávateľ", ["Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky", "POKLADŇA"])
    with col2:
        v_suma = st.number_input("Suma (€)", min_value=0.0, step=0.1)
    
    v_poznamka = st.text_input("Poznámka")
    submit = st.form_submit_button("Uložiť záznam")

if submit:
    # Definícia hodnôt na základe kategórie
    rano = v_suma if kategoria == "Ranný stav pokladne" else 0
    vybery = v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0
    vecer = v_suma if kategoria == "Večerný stav (Uzávierka)" else 0
    
    # Výpočet Dennej tržby (iba pri večernej uzávierke, inak 0)
    # Logika: (Suma všetkých výberov dňa + Večerný stav) - Ranný stav
    denna_trzba = 0
    if kategoria == "Večerný stav (Uzávierka)":
        # Tu by apka v ideálnom prípade musela načítať predchádzajúce dnešné záznamy,
        # ale pre zjednodušenie a stabilitu sa výpočty tržieb (Týždenná/Ročná) 
        # zvyčajne robia priamo v Google Tabuľke pomocou vzorcov v stĺpcoch L, M, N.
        denna_trzba = 0 # Necháme na vzorec v tabuľke pre maximálnu presnosť

    riadok = [
        v_datum.strftime("%d.%m.%Y"),      # A: Datum
        v_den,                             # B: Den
        f"{v_tyzden_cislo}. týždeň",       # C: Tyzden
        v_rok,                             # D: Rok
        v_firma,                           # E: Firma
        rano,                              # F: Rano
        vybery,                            # G: Vybery
        vecer,                             # H: Vecer
        denna_trzba,                       # I: Cista_Trzba (Denná)
        kategoria,                         # J: Kategoria
        v_poznamka                         # K: Poznamka
    ]
    
    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success(f"Dáta úspešne odoslané! (Týždeň {v_tyzden_cislo}, Rok {v_rok})")
        else:
            st.error("Chyba pri odosielaní.")
    except Exception as e:
        st.error(f"Chyba: {e}")

st.divider()
st.info("Tip: Pre automatické súčty Týždennej a Ročnej tržby odporúčam pridať do Google tabuľky Pivot Table (Kontingenčnú tabuľku).")
