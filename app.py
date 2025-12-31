import streamlit as st
import requests
import pandas as pd
from datetime import date

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- NAČÍTANIE DÁT ---
def naciť_data():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                # Prevod na čísla
                for col in ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
                return df
    except Exception as e:
        st.error(f"Chyba pripojenia: {e}")
    return pd.DataFrame()

df_data = naciť_data()
dnes_dt = date.today()

# --- ZOBRAZENIE ---
if not df_data.empty and 'Cista_Trzba' in df_data.columns:
    # Metriky
    celkova_trzba = df_data['Cista_Trzba'].sum()
    st.metric("Celková tržba v tabuľke", f"{celkova_trzba:,.2f} €")
    
    # Graf - zobrazíme len riadky, kde je tržba (uzávierky)
    df_graf = df_data[df_data['Cista_Trzba'] > 0]
    if not df_graf.empty:
        st.subheader("Trend tržieb")
        st.bar_chart(df_graf, x="Datum", y="Cista_Trzba")
else:
    st.warning("V tabuľke zatiaľ nie sú žiadne vypočítané tržby. Urobte 'Večernú uzávierku'.")

st.divider()

# --- FORMULÁR ---
with st.form("ucto_form", clear_on_submit=True):
    v_datum = st.date_input("Dátum", dnes_dt)
    kat = st.radio("Kategória", ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"], horizontal=True)
    firma = st.selectbox("Položka", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Bagety", "Iné"])
    suma = st.number_input("Suma v €", step=0.01, format="%.2f")
    poslat = st.form_submit_button("💾 ULOŽIŤ")

if poslat:
    dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
    riadok = [
        v_datum.strftime("%d.%m.%Y"), dni_sk[v_datum.weekday()], 
        f"{v_datum.isocalendar()[1]}. týždeň", v_datum.year, firma,
        suma if "Ranný" in kat else 0,
        suma if "Výber" in kat else 0,
        suma if "Večerný" in kat else 0,
        "", kat, ""
    ]
    try:
        res = requests.post(SCRIPT_URL, json={"row": riadok})
        st.success("Zapísané! Obnovujem...")
        st.rerun()
    except:
        st.error("Nepodarilo sa odoslať.")
