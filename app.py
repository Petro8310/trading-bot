[19:36, 2026. 10. 04.] Zoltán: import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Haladó Kereskedési Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Címsor
st.title("🚀 Mester Kvant - Haladó Kvantitatív Dashboard")
st.markdown("Ez a verzió már integrált *Bollinger/RSI indikátorokat, **dinamikus Stop-Loss/Take-Profit számítást* és *gépi tanulásos árirány-előrejelzést* tartalmaz!")

# Oldalsáv (Sidebar) beállításai
st.sidebar.header("Kvant Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Kiválasztott eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
account_balance = st.sidebar…
[19:43, 2026. 10. 04.] Zoltán: import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Intézményi Kvant Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Címsor
st.title("⚡ Mester Kvant - Intézményi Kvantitatív Rendszer")
st.markdown("Ez a verzió már a *Piaci Rezsim Váltás detektort, az **EWMA volatilitás-alapú dinamikus kockázatkezelést* és a *Statisztikai Arbitrázs (Z-Score) modult* futtatja!")

# Oldalsáv (Sidebar)
st.sidebar.header("Intézményi Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Fő eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
account_balance = st.sidebar.number_input("Számlaegyenleg ($)", value=25000.0, step500.0)
base_risk = st.sidebar.slider("Alap Kockázat (%)", 1, 5, 2)

if bot_status:
    st.sidebar.success("Státusz: INTÉZMÉNYI MÓD AKTÍV 🟢")
else:
    st.sidebar.warning("Státusz: LEÁLLítVA 🔴")

# Adatgenerálás szimulációhoz
np.random.seed(101)
n_periods = 100
base_price = 65000.0 if "BTC" in selected_symbol else (2600.0 if "ETH" in selected_symbol else 190.0)
price_changes = np.random.normal(loc=0.0005, scale=0.015, size=n_periods)
prices = base_price * np.cumprod(1 + price_changes)

df = pd.DataFrame({'Piaci Ár ($)': prices})

# --- 1. MODUL: Piaci Rezsim Váltás Detektor (Market Regime Classification) ---
df['Returns'] = df['Piaci Ár ($)'].pct_change().fillna(0)
df['Rolling_Vol'] = df['Returns'].rolling(window=15).std() * np.sqrt(365)
df['Trend_MA'] = df['Piaci Ár ($)'].rolling(window=20).mean()

current_price = df['Piaci Ár ($)'].iloc[-1]
current_vol = df['Rolling_Vol'].iloc[-1]

# Rezsim meghatározása
if current_vol > df['Rolling_Vol'].quantile(0.75):
    market_regime = "Pánik / Magas Volatilitás ⚠️ (Védekező Mód)"
    regime_color = "red"
elif current_price > df['Trend_MA'].iloc[-1]:
    market_regime = "Stabil Bika Trend 📈 (Aggressív Mód)"
    regime_color = "green"
else:
    market_regime = "Oldalazó / Medve Zóna 📉 (Kivárás)"
    regime_color = "orange"

# --- 2. MODUL: EWMA Volatilitás-Alapú Dinamikus Pozíciókezelés ---
# Exponenciálisan súlyozott szórás (GARCH-jellegű megközelítés)
ewma_vol = df['Returns'].ewm(span=10).std().iloc[-1]
dynamic_risk_pct = base_risk * (1 + (ewma_vol * 10)) # Volatilitás függvényében növekszik/csökken a védelmi távolság
stop_loss_price = current_price * (1 - dynamic_risk_pct / 100.0)
take_profit_price = current_price * (1 + (dynamic_risk_pct * 2.5 / 100.0))
position_size_usd = account_balance * (base_risk / 100.0) / (ewma_vol + 1e-5)

# --- 3. MODUL: Statisztikai Arbitrázs és Z-Score (Páros Kereskedési Szimuláció) ---
# Szintetikus pár generálása (pl. ETH/BTC jellegű spread)
synthetic_spread = df['Piaci Ár ($)'] / (df['Piaci Ár ($)'] * 0.038 + np.random.normal(0, 5, n_periods))
spread_mean = synthetic_spread.rolling(window=30).mean()
spread_std = synthetic_spread.rolling(window=30).std()
z_score = (synthetic_spread - spread_mean) / (spread_std + 1e-6)
current_z = z_score.iloc[-1]

if current_z > 2.0:
    arb_signal = "SHORT SPREAD 🔴 (Túlárazott)"
elif current_z < -2.0:
    arb_signal = "LONG SPREAD 🟢 (Alulértékelt)"
else:
    arb_signal = "NEUTRÁLIS ZÓNA ⚪"

# --- Főoldali Metrikák Megjelenítése ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Piaci Rezsim", market_regime)
col2.metric("Aktuális Volatilitás (EWMA)", f"{ewma_vol*100:.2f}%")
col3.metric("Stat. Arbitrázs (Z-Score)", f"{current_z:.2f}", arb_signal)
col4.metric("Javasolt Pozíció Érték", f"${position_size_usd:,.2f}")

st.markdown("---")

# Kockázatkezelési Panel
st.subheader("🛡️ GARCH-jellegű Dinamikus Kockázatkezelési Szintek")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Dinamikus Stop-Loss", f"${stop_loss_price:,.2f}", f"-{dynamic_risk_pct:.2f}%")
scol2.metric("Dinamikus Take-Profit", f"${take_profit_price:,.2f}", f"+{dynamic_risk_pct*2.5:.2f}%")
scol3.metric("Kockázat-Hozam Arány", "1 : 2.5", "Intézményi Optimalizált")

st.markdown("---")

# Grafikonok megjelenítése
st.subheader(f"📈 Piaci Árfolyam és Rezsim Alapú Sávok: {selected_symbol}")
chart_df = pd.DataFrame({
    'Piaci Ár ($)': df['Piaci Ár ($)'],
    'Trend MA (20)': df['Trend_MA']
})
st.line_chart(chart_df)

st.info(f"💡 *Intézményi Elemzés:* A rendszer detektálta, hogy a piac jelenleg *{market_regime}* fázisban van. A statisztikai arbitrázs Z-Score értéke *{current_z:.2f}, ami alapján a spread pozíció státusza: *{arb_signal}**.")
