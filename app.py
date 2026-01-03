import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import time

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- VÝBER DÁTUMU ---
selected_date = st.date_input("Vyber dátum pre zobrazenie tržieb", date.today())

# --- TLAČIDLO NA AKTUALIZÁCIU ---
if st.button("🔄 Aktualizovať dáta z tabuľky"):
    st.rerun()

# --- NAČÍTANIE DÁT ---
def nacitaj_data():
    try:
        unique_param = int(time.time() * 1000)
        response = requests.get(SCRIPT_URL, params={"nocache": unique_param}, timeout=15)

        if response.status_code != 200:
            st.error(f"Chyba pri načítaní: HTTP {response.status_code}")
            return pd.DataFrame()

        raw_data = response.json()
        if not isinstance(raw_data, list) or len(raw_data) < 2:
            st.error("Neplatné dáta z tabuľky")
            return pd.DataFrame()

        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df["row_number"] = df.index + 2  # technický stĺpec pre číslo riadku

        # Normalizácia stĺpcov
        df.columns = df.columns.str.normalize("NFKD") \
                               .str.encode("ascii", errors="ignore") \
                               .str.decode("utf-8") \
                               .str.strip() \
                               .str.replace(" ", "_")

        # Konverzia dátumu – robustná verzia
 if "Datum" in df.columns:
    df["Datum_date"] = pd.to_datetime(
        df["Datum"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce"
    ).dt.tz_localize(None)
     
        # Konverzia čísel
        num_cols = ["Rano", "Vybery", "Vecer", "Cista_Trzba", "Rok"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", ".").str.replace(" ", ""),
                    errors="coerce"
                ).fillna(0)

        return df

    except Exception as e:
        st.error(f"Chyba pri načítaní: {e}")
        return pd.DataFrame()

df_data = nacitaj_data()

# --- TEST – overenie načítaných dát ---
with st.expander("🧪 TEST – všetky načítané dátumy"):
    if not df_data.empty:
        st.dataframe(df_data[["Datum", "Datum_date", "row_number", "Cista_Trzba"]])
    else:
        st.write("❌ df_data je prázdny")

# --- ZOBRAZENIE ---
if not df_data.empty and "Datum_date" in df_data.columns:
    df_valid = df_data.dropna(subset=["Datum_date"]).copy()
    df_valid["day"] = df_valid["Datum_date"].dt.date

    # Debug: dáta pre vybraný deň
    debug_df = df_valid[df_valid["day"] == selected_date]
    if not debug_df.empty:
        with st.expander("🔍 Detail záznamov pre vybraný deň"):
            st.dataframe(debug_df)

    # Tržba za vybraný deň
    selected_day_rows = df_valid[df_valid["day"] == selected_date]
    s_day = selected_day_rows.iloc[-1]["Cista_Trzba"] if not selected_day_rows.empty else 0

    # Tržba za posledných 30 dní
    pred_30 = selected_date - timedelta(days=29)
    df_last_30 = df_valid[df_valid["day"] >= pred_30]
    df_last_30_grouped = df_last_30.groupby("day").last().reset_index()
    s_30_dni = df_last_30_grouped["Cista_Trzba"].sum()

    # Tržba za rok
    df_year = df_valid[df_valid["Datum_date"].dt.year == selected_date.year]
    df_year_grouped = df_year.groupby("day").last().reset_index()
    s_rok = df_year_grouped["Cista_Trzba"].sum()

    # Metriky
    c1, c2, c3 = st.columns(3)
    c1.metric("Tržba za vybraný deň", f"{s_day:,.2f} €")
    c2.metric("Tržba (posledných 30 dní)", f"{s_30_dni:,.2f} €")
    c3.metric(f"Tržba za rok {selected_date.year}", f"{s_rok:,.2f} €")

    # Graf tržieb
    df_year_for_chart = df_valid[df_valid["Datum_date"].dt.year == selected_date.year]
    df_trzby = df_year_for_chart.groupby("day").last().reset_index()
    df_trzby = df_trzby[df_trzby["Cista_Trzba"] != 0]
    
    if not df_trzby.empty:
        st.subheader("Graf tržieb")
        df_graf = df_trzby[["day", "Cista_Trzba"]].copy()
        df_graf["day"] = df_graf["day"].astype(str)
        st.bar_chart(df_graf.set_index("day")["Cista_Trzba"])
    else:
        st.info("Žiadne tržby na zobrazenie.")

else:
    st.warning("Dáta sa nenačítali. Klikni na 'Aktualizovať dáta z tabuľky'.")

st.divider()

# --- FORMULÁR NA ZÁPIS ---
with st.form("ucto_form", clear_on_submit=True):
    v_datum = st.date_input("Dátum pre zápis", selected_date)
    kat = st.radio("Kategória", 
                   ["Ranný stav pokladne", "Platba dodávateľovi (Výber)", "Večerný stav (Uzávierka)"],
                   horizontal=True)
    firma = st.selectbox("Položka", ["POKLADŇA", "Labaš", "Terminál", "Dušan", "Martinka", "Stravné lístky", "Milka", "Bagety", "Iné"])
    suma = st.number_input("Suma v €", min_value=0.0, step=0.01, format="%.2f")
    poslat = st.form_submit_button("💾 ULOŽIŤ")

if poslat:
    dni_sk = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}

    riadok = [
        v_datum.strftime("%d.%m.%Y"),
        dni_sk[v_datum.weekday()],
        f"{v_datum.isocalendar()[1]}. týždeň",
        v_datum.year,
        firma,
        suma if "Ranný" in kat else 0,
        suma if "Výber" in kat else 0,
        suma if "Večerný" in kat else 0,
        "",
        kat,
        ""
    ]

    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success("✅ Zapísané!")
            st.rerun()
        else:
            st.error(f"Chyba servera: {response.status_code}")
    except Exception as e:
        st.error(f"Chyba odoslania: {e}")
