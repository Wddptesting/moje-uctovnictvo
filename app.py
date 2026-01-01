import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import time  # pridávame pre unikátny timestamp

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- VÝBER DÁTUMU ---
selected_date = st.date_input("Vyber dátum pre zobrazenie tržieb", date.today())

# --- TLAČIDLO NA AKTUALIZÁCIU DÁT ---
if st.button("🔄 Aktualizovať dáta z tabuľky"):
    # Vynútime refresh dát
    st.rerun()

# --- NAČÍTANIE DÁT ---
def nacitaj_data():
    try:
        # Unikátny parameter pomocou aktuálneho času (v milisekundách)
        unique_param = int(time.time() * 1000)
        
        response = requests.get(
            SCRIPT_URL,
            params={"nocache": unique_param},
            timeout=15
        )

        if response.status_code != 200:
            st.error(f"Chyba pri načítaní: HTTP {response.status_code}")
            return pd.DataFrame()

        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 2:
            st.error("Neplatné dáta z tabuľky")
            return pd.DataFrame()

        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

        # Normalizácia stĺpcov
        df.columns = df.columns.str.normalize("NFKD") \
                               .str.encode("ascii", errors="ignore") \
                               .str.decode("utf-8") \
                               .str.strip() \
                               .str.replace(" ", "_")

        # Konverzia dátumu
        if "Datum" in df.columns:
            df["Datum_date"] = pd.to_datetime(df["Datum"], errors="coerce")
            mask = df["Datum_date"].isna()
            if mask.any():
                df.loc[mask, "Datum_date"] = pd.to_datetime(
                    df.loc[mask, "Datum"],
                    format="%d.%m.%Y",
                    errors="coerce"
                )

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

# Načítame dáta (pri každom kliknutí na tlačidlo sa načítajú znova)
df_data = nacitaj_data()

# --- ZOBRAZENIE ---
if not df_data.empty and "Cista_Trzba" in df_data.columns and "Datum_date" in df_data.columns:

    df_trzby = df_data[df_data["Cista_Trzba"] > 0].copy()

    # Tržba za vybraný deň
    s_day = df_data[
        (df_data["Datum_date"].dt.date == selected_date) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # Tržba za posledných 30 dní od vybraného dátumu
    pred_30 = selected_date - timedelta(days=30)
    s_30_dni = df_data[
        (df_data["Datum_date"].dt.date >= pred_30) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # Tržba za rok vybraného dátumu
    s_rok = df_data[
        (df_data["Datum_date"].dt.year == selected_date.year) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # Metriky
    c1, c2, c3 = st.columns(3)
    c1.metric("Tržba za vybraný deň", f"{s_day:,.2f} €")
    c2.metric("Tržba (posledných 30 dní)", f"{s_30_dni:,.2f} €")
    c3.metric(f"Tržba za rok {selected_date.year}", f"{s_rok:,.2f} €")

    # Graf
    if not df_trzby.empty:
        st.subheader("Graf tržieb")
        df_graf = df_trzby.groupby(df_trzby["Datum_date"].dt.date)["Cista_Trzba"].sum().reset_index()
        df_graf["Datum_date"] = df_graf["Datum_date"].astype(str)
        st.bar_chart(df_graf.set_index("Datum_date")["Cista_Trzba"])
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
    firma = st.selectbox("Položka", ["POKLADŇA", "Labaš", "Terminál", "Milka", "Bagety", "Iné"])
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
