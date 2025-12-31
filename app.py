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
        response = requests.get(SCRIPT_URL)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                # Prevod stĺpcov na čísla
                cols = ['Rano', 'Vybery', 'Vecer', 'Cista_Trzba', 'Rok']
                for col in cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)
                return df
    except:
        pass
    return pd.DataFrame()

df_data = naciť_data()
dnes_dt = date.today()

# --- VÝPOČTY A ZOBRAZENIE ---
if not df_data.empty and 'Cista_Trzba' in df_data.columns:
    dnes_str = dnes_dt.strftime("%d.%m.%Y")
    v_rok = dnes_dt.year
    v_mes_filter = dnes_dt.strftime(".%m.%Y")

    s_den = df_data[df_data['Datum'] == dnes_str]['Cista_Trzba'].sum()
    s_tyzden = df_data['Cista_Trzba'].tail(7).sum()
    s_mesiac = df_data[df_data['Datum'].astype(str).str.contains(v_mes_filter, na=False)]['Cista_Trzba'].sum()
    s_rok = df_data[df_data['Rok'] == v_rok]['Cista_Trzba'].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dnes", f"{s_den:,.2f} €")
    c2.metric("7 dní", f"{s_tyzden:,.2f} €")
    c3.metric("Mesiac", f"{s_mesiac:,.2f} €")
    c4.metric("Rok", f"{s_rok:,.2f} €")

    st.subheader("Trend tržieb")
    st.bar_chart(df_data.tail(10), x="Datum", y="Cista_Trzba")
else:
    st.info("Čakám na dáta... Uistite sa, že stĺpec I v tabuľke nie je zablokovaný chybou #REF!.")

st.divider()

# --- FORMULÁR ---
dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
v_datum = st.date_input("Dátum záznamu", dnes_dt)
v_den = dni_sk[v_datum.weekday()]

with st.form("uctovnictvo_form"):
    kat = st.radio("Kategória", ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"], horizontal=True)
    firma = st.selectbox("Položka", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Dušan", "Martinka", "Bagety", "Stravné lístky"])
    suma = st.number_input("Suma v €", min_value=0.0, step=0.01, format="%.2f")
    poslat = st.form_submit_button("💾 ULOŽIŤ DO TABUĽKY")

if poslat:
    # KĽÚČOVÁ ZMENA: Stĺpec I (index 8) posielame ako prázdny reťazec "", nie ako 0!
    novy_riadok = [
        v_datum.strftime("%d.%m.%Y"), v_den, f"{v_datum.isocalendar()[1]}. týždeň", v_datum.year, firma,
        suma if kat == "Ranný stav pokladne" else 0,
        suma if kat == "Platba dodávateľovi (Výber)" else 0,
        suma if kat == "Večerný stav (Uzávierka)" else 0,
        "", # TU MUSÍ BYŤ PRÁZDNO, ABY VZOREC V TABUĽKE FUNGOVAL
        kat, ""
    ]
    requests.post(SCRIPT_URL, json={"row": novy_riadok})
    st.rerun()
