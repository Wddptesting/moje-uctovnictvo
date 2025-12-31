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
        # Pridaný parameter na zabránenie starých dát (cache)
        response = requests.get(f"{SCRIPT_URL}?nocache={date.today()}", timeout=15)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                for col in ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
                return df
    except:
        pass # Ignorujeme chybu formátu, skúsime to pri ďalšom načítaní
    return pd.DataFrame()

df_data = naciť_data()
dnes_dt = date.today()

# --- ZOBRAZENIE ---
if not df_data.empty and 'Cista_Trzba' in df_data.columns:
    # Filtrujeme len riadky, kde je skutočná tržba (viac ako 0)
    df_trzby = df_data[df_data['Cista_Trzba'] > 0]
    
    # Výpočty metrík
    s_den = df_data[df_data['Datum'] == dnes_dt.strftime("%d.%m.%Y")]['Cista_Trzba'].sum()
    s_rok = df_data[df_data['Rok'] == dnes_dt.year]['Cista_Trzba'].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Dnešná tržba", f"{s_den:,.2f} €")
    c2.metric("Tržba (posledných 30 dní)", f"{df_trzby['Cista_Trzba'].tail(30).sum():,.2f} €")
    c3.metric("Tržba za rok", f"{s_rok:,.2f} €")

    if not df_trzby.empty:
        st.subheader("Graf tržieb")
        st.bar_chart(df_trzby, x="Datum", y="Cista_Trzba")
    else:
        st.info("💡 Tip: Aby sa zobrazil graf, urobte záznam v kategórii 'Večerný stav (Uzávierka)'.")
else:
    st.warning("Čakám na prvé dáta z tabuľky...")

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
    # Dôležité: posielame prázdny reťazec pre stĺpec I, aby ho tabuľka dopočítala sama
    riadok = [
        v_datum.strftime("%d.%m.%Y"), dni_sk[v_datum.weekday()], 
        f"{v_datum.isocalendar()[1]}. týždeň", v_datum.year, firma,
        suma if "Ranný" in kat else 0,
        suma if "Výber" in kat else 0,
        suma if "Večerný" in kat else 0,
        "", kat, ""
    ]
    try:
        requests.post(SCRIPT_URL, json={"row": riadok})
        st.success("Zapísané!")
        st.rerun()
    except:
        st.rerun() # Pri chybe len obnovíme apku, dáta sú väčšinou už v tabuľke
