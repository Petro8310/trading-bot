import streamlit as st
import pandas as pd
import numpy as np

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Ultimate Terminal & Circuit Breaker",
    page_icon="🛡️",
    layout="wide"
)

# Címsor
st.title("🛡️ Mester Kvant - Ultimate Intézményi Terminál & Vészlekapcsoló")
st.markdown("Ez a csúcsverzió már tartalmazza a *Valós Idejű Hangulatindexet, a **Likvidációs Hőtérképet* és az *Automatikus Circuit Breaker (Vészlekapcsoló) rendszert*!")

# Oldalsáv (Sidebar)
st.sidebar.header("Intézményi Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Fő eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
account_balance = st.sidebar.number_input("Számlaegyenleg ($)", value=150000.0, step=10000.0)
volatility_threshold = st.sidebar.slider("Circuit Breaker Volatilitás Limit (%)", 3, 10, 5)

if bot_status:
    st.sidebar.success("Státusz: ULTIMATE VÉDELEM AKTÍV 🟢")
else:
    st.sidebar.warning("Státusz: LEÁLLÍTVA 🔴")

# Adatgenerálás szimulációhoz
np.random.seed(3030)
n_periods = 160
base_price = 72000.0 if "BTC" in selected_symbol else (2900.0 if "ETH" in selected_symbol else 220.0)
price_changes = np.random.normal(loc=0.0006, scale=0.017, size=n_periods)
prices = base_price * np.cumprod(1 + price_changes)

df = pd.DataFrame({'Piaci Ár ($)': prices})

# --- 1. MODUL: Valós Idejű Hír & Twitter Hangulatindex (NLP Módosító) ---
# Szimulált hangulat (-1.0 (extrém medve) és +1.0 (extrém bika) között)
sentiment_score = np.random.uniform(-0.4, 0.8)
if sentiment_score > 0.3:
    sentiment_status = "EXTRÉM BIKA HANGULAT 🚀"
elif sentiment_score < -0.2:
    sentiment_status = "MEDVE / PANIK HANGULAT ⚠️"
else:
    sentiment_status = "SEMLEGES PIACI HANGULAT ⚪"

# --- 2. MODUL: Likvidációs Hőtérkép (Liquidation Heatmap) ---
current_price = df['Piaci Ár ($)'].iloc[-1]
# Becsült tőkeáttételes long/short likvidációs szintek
long_liq_zone = current_price * (1 - 0.04) # 25x tőkeáttételes longok zónája
short_liq_zone = current_price * (1 + 0.04) # 25x tőkeáttételes shortok zónája

if current_price < long_liq_zone * 1.01:
    liq_alert = "VESZÉLY: Long Likvidációs Zóna Közelében! 🔴"
elif current_price > short_liq_zone * 0.99:
    liq_alert = "VESZÉLY: Short Squeeze Zóna Közelében! 🟢"
else:
    liq_alert = "Biztonságos Likvidációs Távolság 🟢"

# --- 3. MODUL: Automatikus Circuit Breaker (Vészlekapcsoló) ---
recent_volatility = df['Piaci Ár ($)'].pct_change().rolling(window=10).std().iloc[-1] * 100
if recent_volatility > volatility_threshold:
    circuit_breaker_status = "ACTIVATED: VÉDELMI MÓD (Készpénzre váltás) 🚨"
    system_mode = "VÉDEKEZŐ / KÉNYSZER-STOP"
else:
    circuit_breaker_status = "NORMAL: Normál Intézményi Kereskedés ✅"
    system_mode = "AKTÍV KVANT MÓD"

# --- Főoldali Metrikák Megjelenítése ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Circuit Breaker Státusz", system_mode)
col2.metric("Valós Idejű Hangulat", f"{sentiment_score:+.2f}", sentiment_status)
col3.metric("Likvidációs Zóna Figyelő", liq_alert)
col4.metric("Aktuális Volatilitás", f"{recent_volatility:.2f}%", f"Limit: {volatility_threshold}%")

st.markdown("---")

# Részletes Panel
st.subheader("📊 Intézményi Hőtérkép és Biztonsági Paraméterek")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Becsült Long Likvidációs Ár", f"${long_liq_zone:,.2f}", "-4.0% (25x)")
scol2.metric("Becsült Short Likvidációs Ár", f"${short_liq_zone:,.2f}", "+4.0% (25x)")
scol3.metric("Rendszer Biztonsági Szint", "AAA - Max Védelem", circuit_breaker_status)

st.markdown("---")

# Grafikon megjelenítése
st.subheader(f"📈 Árfolyam és Kockázati Zónák: {selected_symbol}")
st.line_chart(df[['Piaci Ár ($)']])

st.info(f"💡 *Terminal Elemzés:* A Circuit Breaker állapota: *{circuit_breaker_status}. A hír-hangulat index értéke *{sentiment_score:+.2f}* ({sentiment_status}). A likvidációs hőtérkép alapján a kritikus long likvidációs zóna *${long_liq_zone:,.2f}-nél** található.")
