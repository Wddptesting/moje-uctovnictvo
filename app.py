import streamlit as st
import requests
import pandas as pd
from datetime import date

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- NAČÍTANIE DÁT ---
def nacitaj_data():
    try:
        response = requests.get(
            f"{SCRIPT_URL}?nocache={date.today()}",
            timeout=15
        )

        if response.status_code != 200:
            st.error(f"HTTP chyba: {response.status_code}")
            return pd.DataFrame()

        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 2:
            st.error("Neplatná štruktúra dát z Google Sheets")
            return pd.DataFrame()

        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

        # --- NORMALIZÁCIA NÁZVOV STĹPCOV ---
        df.columns = (
            df.columns
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.replace(" ", "_")
        )

        # --- NORMALIZÁCIA DÁTUMU (TEXT, NIE DATE) ---
        if "Datum" in df.columns:
            df["Datum_norm"] = (
                df["Datum"]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", "", regex=True)
            )

        # --- KONVERZIA ČÍSEL ---
        for col in ["Rano", "Vybery", "Vecer", "Cista_Trzba", "Rok"]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", ".")
                    .str.replace(" ", "")
                )
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"Chyba pri načítaní dát: {e}")
        return pd.DataFrame()

df_data = nacitaj_data()
dnes_dt = date.today()

# --- NORMALIZOVANÝ DNES (TEXT) ---
dnes_str = f"{dnes_dt.day}.{dnes_dt.month}.{dnes_dt.year}"

# --- ZOBRAZENIE ---
if not df_data.empty and "Cista_Trzba" in df_data.columns:

    df_trzby = df_data[df_data["Cista_Trzba"] > 0]

    # ✅ DNEŠNÁ TRŽBA – SPOĽAHLIVO CEZ TEXT
    if "Datum_norm" in df_data.columns:
        s_den = df_data[
            df_data["Datum_norm"] == dnes_str
        ]["Cista_Trzba"].sum()
    else:
        s_den = 0

    # ROČNÁ TRŽBA
    s_rok = df_data[
        df_data["Rok"] == dnes_dt.year
    ]["Cista_Trzba"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Dnešná tržba", f"{s_den:,.2f} €")
    c2.metric(
        "Tržba (posledných 30 dní)",
        f"{df_trzby['Cista_Trzba'].tail(30).sum():,.2f} €"
    )
    c3.metric("Tržba za rok", f"{s_rok:,.2f} €")

    if not df_trzby.empty and "Datum_norm" in df_trzby.columns:
        st.subheader("Graf tržieb")
        st.bar_chart(df_trzby, x="Datum_norm", y="Cista_Trzba")
    else:
        st.info(
            "💡 Tip: Aby sa zobrazil graf, urobte záznam v kategórii "
            "'Večerný stav (Uzávierka)'."
        )

else:
    st.warning("Čakám na prvé dáta z tabuľky...")

st.divider()

# --- FORMULÁR ---
with st.form("ucto_form", clear_on_submit=True):
    v_datum = st.date_input("Dátum", dnes_dt)
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
    suma = st.number_input("Suma v €", step=0.01, format="%.2f")
    poslat = st.form_submit_button("💾 ULOŽIŤ")

if poslat:
    dni_sk = {
        0: "Pondelok", 1: "Utorok", 2: "Streda",
        3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"
    }

    riadok = [
        v_datum.strftime("%-d.%-m.%Y"),  # presne rovnaký formát ako čítame
        dni_sk[v_datum.weekday()],
        f"{v_datum.isocalendar()[1]}. týždeň",
        v_datum.year,
        firma,
        suma if "Ranný" in kat else 0,
        suma if "Výber" in kat else 0,
        suma if "Večerný" in kat else 0,
        "",  # Čistá tržba – počíta tabuľka
        kat,
        ""
    ]

    try:
        requests.post(SCRIPT_URL, json={"row": riadok})
        st.success("Zapísané!")
        st.rerun()
    except Exception as e:
        st.error(f"Chyba pri zápise: {e}")
        st.rerun()
