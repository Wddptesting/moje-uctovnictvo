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
selected_date = st.date_input(
    "Vyber dátum pre zobrazenie tržieb",
    date.today()
)

# --- TLAČIDLO NA AKTUALIZÁCIU ---
if st.button("🔄 Aktualizovať dáta z tabuľky"):
    st.rerun()

# --- NAČÍTANIE DÁT ---
def nacitaj_data():
    try:
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

        # --- NORMALIZÁCIA STĹPCOV ---
        df.columns = (
            df.columns
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.strip()
            .str.replace(" ", "_")
        )

        # --- KONVERZIA DÁTUMU ---
        if "Datum" in df.columns:
            df["Datum_date"] = pd.to_datetime(
                df["Datum"],
                errors="coerce",
                dayfirst=True
            )

        # --- KONVERZIA ČÍSEL ---
        num_cols = ["Rano", "Vybery", "Vecer", "Cista_Trzba", "Rok"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col]
                    .astype(str)
                    .str.replace(",", ".")
                    .str.replace(" ", ""),
                    errors="coerce"
                ).fillna(0)

        return df

    except Exception as e:
        st.error(f"Chyba pri načítaní: {e}")
        return pd.DataFrame()

df_data = nacitaj_data()

# --- ZOBRAZENIE ---
if not df_data.empty and {"Cista_Trzba", "Datum_date"}.issubset(df_data.columns):

    # odstránime len neplatné dátumy
    df_valid = df_data.dropna(subset=["Datum_date"]).copy()

    # 🔑 KRITICKÁ NORMALIZÁCIA – JEDINÝ ZDROJ PRAVDY PRE DÁTUM
    df_valid["Datum_day"] = df_valid["Datum_date"].dt.date

    # --- TRŽBA ZA VYBRANÝ DEŇ ---
    s_day = df_valid.loc[
        df_valid["Datum_day"] == selected_date,
        "Cista_Trzba"
    ].sum()

    # --- TRŽBA ZA POSLEDNÝCH 30 DNÍ (vrátane dneška) ---
    pred_30 = selected_date - timedelta(days=29)
    s_30_dni = df_valid.loc[
        (df_valid["Datum_day"] >= pred_30) &
        (df_valid["Datum_day"] <= selected_date),
        "Cista_Trzba"
    ].sum()

    # --- TRŽBA ZA ROK ---
    s_rok = df_valid.loc[
        df_valid["Datum_day"].apply(lambda d: d.year) == selected_date.year,
        "Cista_Trzba"
    ].sum()

    # --- METRIKY ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Tržba za vybraný deň", f"{s_day:,.2f} €")
    c2.metric("Tržba (posledných 30 dní)", f"{s_30_dni:,.2f} €")
    c3.metric(f"Tržba za rok {selected_date.year}", f"{s_rok:,.2f} €")

    # --- GRAF ---
    df_trzby = df_valid[df_valid["Cista_Trzba"] > 0]

    if not df_trzby.empty:
        st.subheader("Graf tržieb")

        df_graf = (
            df_trzby
            .groupby("Datum_day", as_index=False)["Cista_Trzba"]
            .sum()
            .sort_values("Datum_day")
        )

        df_graf["Datum_day"] = df_graf["Datum_day"].astype(str)
        st.bar_chart(
            df_graf.set_index("Datum_day")["Cista_Trzba"]
        )
    else:
        st.info("Žiadne tržby na zobrazenie.")

else:
    st.warning("Dáta sa nenačítali. Klikni na 'Aktualizovať dáta z tabuľky'.")

st.divider()

# --- FORMULÁR NA ZÁPIS ---
with st.form("ucto_form", clear_on_submit=True):
    v_datum = st.date_input("Dátum pre zápis", selected_date)
    kat = st.radio(
        "Kategória",
        [
            "Ranný stav pokladne",
            "Platba dodávateľovi (Výber)",
            "Večerný stav (Uzávierka)"
        ],
        horizontal=True
    )
    firma = st.selectbox(
        "Položka",
        ["POKLADŇA", "Labaš", "Terminál", "Milka", "Bagety", "Iné"]
    )
    suma = st.number_input(
        "Suma v €",
        min_value=0.0,
        step=0.01,
        format="%.2f"
    )
    poslat = st.form_submit_button("💾 ULOŽIŤ")

if poslat:
    dni_sk = {
        0: "Pondelok",
        1: "Utorok",
        2: "Streda",
        3: "Štvrtok",
        4: "Piatok",
        5: "Sobota",
        6: "Nedeľa"
    }

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
        response = requests.post(
            SCRIPT_URL,
            json={"row": riadok}
        )
        if response.status_code == 200:
            st.success("✅ Zapísané!")
            st.rerun()
        else:
            st.error(f"Chyba servera: {response.status_code}")
    except Exception as e:
        st.error(f"Chyba odoslania: {e}")
