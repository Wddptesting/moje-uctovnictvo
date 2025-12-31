import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Účtovníctvo", layout="wide")
st.title("💸 Moja Účtovná Apka (Google Sheets)")

# Prepojenie na Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Načítanie existujúcich dát
df = conn.read(ttl="0s")

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
    # Výpočet tržby
    v_trzba = 0
    if kategoria == "Večerný stav (Uzávierka)":
        dnesne_data = df[df["Datum"] == v_datum.strftime("%d.%m.%Y")]
        spolu_vybery = dnesne_data["Vybery"].sum() + (v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0)
        rano_df = dnesne_data[dnesne_data["Kategoria"] == "Ranný stav pokladne"]
        v_rano = rano_df["Rano"].iloc[0] if not rano_df.empty else 100.0
        v_trzba = v_suma + spolu_vybery - v_rano

    novy_riadok = pd.DataFrame([{
        "Datum": v_datum.strftime("%d.%m.%Y"),
        "Den": v_den,
        "Tyzden": v_tyzden_text,
        "Rok": rok,
        "Firma": v_firma,
        "Rano": v_suma if kategoria == "Ranný stav pokladne" else 0,
        "Vybery": v_suma if kategoria == "Platba dodávateľovi (Výber)" else 0,
        "Vecer": v_suma if kategoria == "Večerný stav (Uzávierka)" else 0,
        "Cista_Trzba": v_trzba,
        "Kategoria": kategoria,
        "Poznamka": v_poznamka
    }])
    
    updated_df = pd.concat([df, novy_riadok], ignore_index=True)
    conn.update(data=updated_df)
    st.success("Dáta odoslané do Google tabuľky!")
    st.rerun()

# Štatistiky
st.divider()
if not df.empty:
    st.subheader("Prehľad")
    st.dataframe(df.tail(10), use_container_width=True)