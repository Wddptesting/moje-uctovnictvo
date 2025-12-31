import streamlit as st
import requests
import pandas as pd
from datetime import date

# === SEM VLOŽTE VAŠU URL ADRESU ===
# Túto adresu ste skopírovali po "Nasadení" v Google Apps Script
SCRIPT_URL = "VAŠA_URL_ADRESA_KTORÚ_STE_SKOPÍROVALI"

st.set_page_config(page_title="Účtovníctvo", layout="wide")
st.title("💸 Moja Účtovná Apka (Google Sheets)")

dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

with st.form("form_vypocet", clear_on_submit=True):
    v_datum = st.date_input("Dátum", date.today())
    v_den = dni_sk[v_datum.weekday()]
    cislo_tyzdna = v_datum.isocalendar()[1]
    rok = v_datum.year
    v_tyzden_text = f"Týždeň {cislo_tyzdna}"
    
    st.subheader(f"Nový záznam: {v_den} | {v_tyzden_text}")
    kategoria = st.radio("Kategória", ["Platba dodávateľovi (Výber)", "Ranný stav pokladne", "Večerný stav (Uzávierka)"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        v_firma = st.selectbox("Firma / Dodávateľ", ["Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky", "POKLADŇA"])
    with col2:
        v_suma = st.number_input("Suma (€)", min_value=0.0, step=0.1)
    
    v_poznamka = st.text_input("Poznámka")
    submit = st.form_submit_button("Uložiť záznam")

if submit:
    # Príprava dát pre odoslanie
    # (Výpočet čistej tržby sa v tomto zjednodušenom modeli vykoná až v tabuľke, 
    # alebo si ju môžete dopočítať neskôr)
    v_trzba = 0 
    
    riadok_pre_tabulku = [
        v_datum.strftime("%d.%m.%Y"),
        v_den,
        v_tyzden_text,
        rok,
        v_firma,
        v_suma if kategoria == "Ranný stav pokladne" else 0,
        v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0,
        v_suma if kategoria == "Večerný stav (Uzávierka)" else 0,
        v_trzba,
        kategoria,
        v_poznamka
    ]
    
    # Odoslanie dát cez Google Apps Script "most"
    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok_pre_tabulku})
        if response.status_code == 200:
            st.success("Dáta úspešne odoslané do Google tabuľky!")
        else:
            st.error(f"Chyba na serveri: {response.status_code}")
    except Exception as e:
        st.error(f"Nepodarilo sa pripojiť: {e}")

# Zobrazenie posledných dát (voliteľné)
st.divider()
st.info("Tip: Nové záznamy sa objavia priamo vo vašej Google tabuľke.")
