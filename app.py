import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

# --- KONFIGURÁCIA ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwDP_pIMWYbSkxvZWM5RnQEhacWMAmKNBusBOGgc22XJKwGsYclk14XCVMfHrNUGQBG/exec"

st.set_page_config(page_title="Moja Účtovná Apka", layout="wide")
st.title("💸 Moja Účtovná Apka")

# --- VÝBER DÁTUMU PRE ZOBRAZENIE (nový picker na aktualizáciu tržieb) ---
selected_date = st.date_input("Vyber dátum pre zobrazenie tržieb", date.today())

# --- NAČÍTANIE DÁT (s cache, ale refresh pri zmene dátumu) ---
@st.cache_data(ttl=30, show_spinner="Načítavam dáta z tabuľky...")
def nacitaj_data(_date):  # Pridanie _date ako kľúč pre cache reset pri zmene dátumu
    try:
        response = requests.get(
            f"{SCRIPT_URL}?nocache={_date}",
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

        # Normalizácia názvov stĺpcov
        df.columns = (
            df.columns
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.strip()
            .str.replace(" ", "_")
        )

        # --- KONVERZIA DÁTUMU – spoľahlivá ---
        if "Datum" in df.columns:
            df["Datum_date"] = pd.to_datetime(df["Datum"], errors="coerce", utc=True)
            mask = df["Datum_date"].isna()
            if mask.any():
                df.loc[mask, "Datum_date"] = pd.to_datetime(
                    df.loc[mask, "Datum"],
                    format="%d.%m.%Y",
                    errors="coerce"
                )
            if df["Datum_date"].dt.tz is not None:
                df["Datum_date"] = df["Datum_date"].dt.tz_localize(None)

        # Konverzia čísel
        num_cols = ["Rano", "Vybery", "Vecer", "Cista_Trzba", "Rok"]
        for col in num_cols:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", ".")
                    .str.replace(" ", "")
                    .replace("", "0")
                )
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"Chyba pri načítaní dát: {e}")
        return pd.DataFrame()

df_data = nacitaj_data(selected_date)

# --- ZOBRAZENIE ---
if not df_data.empty and "Cista_Trzba" in df_data.columns and "Datum_date" in df_data.columns:

    # Filtrovanie len riadkov s vyplnenou čistou tržbou (uzávierky)
    df_trzby = df_data[df_data["Cista_Trzba"] > 0].copy()

    # ✅ TRŽBA ZA VYBRANÝ DEŇ
    s_day = df_data[
        (df_data["Datum_date"].dt.date == selected_date) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # TRŽBA ZA POSLEDNÝCH 30 DNÍ OD VYBRANÉHO DÁTUMU
    pred_30_dni = selected_date - timedelta(days=30)
    s_30_dni = df_data[
        (df_data["Datum_date"].dt.date >= pred_30_dni) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # ROČNÁ TRŽBA – súčet všetkých uzávierok v roku vybraného dátumu
    s_rok = df_data[
        (df_data["Datum_date"].dt.year == selected_date.year) & (df_data["Cista_Trzba"] > 0)
    ]["Cista_Trzba"].sum()

    # Zobrazenie metrík
    c1, c2, c3 = st.columns(3)
    c1.metric("Tržba za deň", f"{s_day:,.2f} €")
    c2.metric("Tržba (posledných 30 dní)", f"{s_30_dni:,.2f} €")
    c3.metric("Tržba za rok", f"{s_rok:,.2f} €")

    # Graf tržieb podľa dňa
    if not df_trzby.empty:
        st.subheader("Graf tržieb")
        df_graf = (
            df_trzby.groupby(df_trzby["Datum_date"].dt.date)["Cista_Trzba"]
            .sum()
            .reset_index()
        )
        df_graf["Datum_date"] = df_graf["Datum_date"].astype(str)  # pre pekné osi
        st.bar_chart(df_graf.set_index("Datum_date")["Cista_Trzba"])
    else:
        st.info("💡 Tip: Aby sa zobrazil graf, urobte záznam v kategórii 'Večerný stav (Uzávierka)'.")

else:
    st.warning("Čakám na prvé dáta z tabuľky...")

st.divider()

# --- FORMULÁR NA ZÁPIS (ostáva rovnaký, ale používa vybraný dátum ako default) ---
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
    suma = st.number_input("Suma v €", min_value=0.0, step=0.01, format="%.2f")
    poslat = st.form_submit_button("💾 ULOŽIŤ")

if poslat:
    dni_sk = {
        0: "Pondelok", 1: "Utorok", 2: "Streda",
        3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"
    }

    riadok = [
        v_datum.strftime("%d.%m.%Y"),        # formát ako v Sheets: 31.12.2025
        dni_sk[v_datum.weekday()],
        f"{v_datum.isocalendar()[1]}. týždeň",
        v_datum.year,
        firma,
        suma if "Ranný" in kat else 0,
        suma if "Výber" in kat else 0,
        suma if "Večerný" in kat else 0,
        "",  # Čistá tržba – počíta sa v Sheets
        kat,
        ""   # Poznámka
    ]

    try:
        response = requests.post(SCRIPT_URL, json={"row": riadok})
        if response.status_code == 200:
            st.success("✅ Zapísané!")
            st.rerun()  # Refresh po zápise
        else:
            st.error(f"Chyba servera: {response.status_code}")
    except Exception as e:
        st.error(f"Chyba pri odosielaní: {e}")

# Automatický refresh pri zmene dátumu (pre istotu)
if st.session_state.get('previous_date') != selected_date:
    st.session_state['previous_date'] = selected_date
    st.rerun()
