import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

# URL adresa vášho Google Scriptu
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")

# --- FUNKCIA NA NAČÍTANIE DÁT PRE GRAFY ---
# Poznámka: Aby grafy fungovali, apka musí mať prístup k čítaniu vašej tabuľky. 
# Ak váš script zatiaľ len zapisuje, grafy sa zobrazia po pridaní funkcie na čítanie.
def zobraziť_prehľady():
    st.subheader("📊 Aktuálny prehľad tržieb")
    
    # Príklad vizualizácie (Tieto čísla sa v ostrej verzii napojia na váš stĺpec I)
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Tržba - Aktuálny týždeň", value="1 250 €", delta="15% oproti min. týždňu")
    with col_b:
        st.metric(label="Tržba - Rok 2026", value="5 400 €")

    # Ukážkový graf týždennej tržby
    data = pd.DataFrame({
        "Deň": ["Po", "Ut", "St", "Št", "Pi", "So", "Ne"],
        "Tržba (€)": [150, 210, 180, 250, 300, 450, 0]
    })
    fig = px.bar(data, x="Deň", y="Tržba (€)", title="Priebeh tržieb v tomto týždni", color="Tržba (€)")
    st.plotly_chart(fig, use_container_width=True)

st.title("💸 Moja Účtovná Apka")

# --- ZOBRAZENIE GRAFOV ---
zobraziť_prehľady()

st.divider()

# --- FORMULÁR PRE ZÁPIS ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

v_datum = st.date_input("Vyber dátum", date.today())
v_den = dni_sk[v_datum.weekday()]
v_tyzden_cislo = v_datum.isocalendar()[1]
v_rok = v_datum.year
v_tyzden_text = f"{v_tyzden_cislo}. týždeň"

st.write(f"✍️ **Nový záznam:** {v_den} | {v_tyzden_text} | Rok {v_rok}")

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
    # Rozdelenie súm pre tabuľku
    rano = v_suma if kategoria == "Ranný stav pokladne" else 0
    vybery = v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0
    vecer = v_suma if kategoria == "Večerný stav (Uzávierka) " else 0
    
    riadok = [v_datum.strftime("%d.%m.%Y"), v_den, v_tyzden_text, v_rok, v_firma, rano, vybery, vecer, 0, kategoria, v_poznamka]
    
    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success(f"Dáta úspešne uložené!")
        else:
            st.error("Chyba pri zápise do tabuľky.")
    except Exception as e:
        st.error(f"Chyba: {e}")
