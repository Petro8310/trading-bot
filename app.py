import streamlit as st
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
account_balance = st.sidebar.number_input("Számlaegyenleg ($)", value=12450.80, step=100.0)
risk_level = st.sidebar.slider("Kockázati szint / Pozíció (%)", 1, 10, 2)

if bot_status:
    st.sidebar.success("Státusz: AKTÍV KOCKÁZATKEZELÉS 🟢")
else:
    st.sidebar.warning("Státusz: SZÜNETEL 🔴")

# Szimulált piaci adatok generálása
np.random.seed(42)
n_periods = 60
base_price = 61000.0 if "BTC" in selected_symbol else (2450.0 if "ETH" in selected_symbol else 180.0)
price_changes = np.random.randn(n_periods) * (base_price * 0.002)
prices = base_price + np.cumsum(price_changes)

df = pd.DataFrame({
    'Piaci Ár ($)': prices
})

# --- 1. MODUL: Bollinger-szalagok és RSI Kiszámítása ---
df['MA20'] = df['Piaci Ár ($)'].rolling(window=10).mean().bfill()
df['STD'] = df['Piaci Ár ($)'].rolling(window=10).std().bfill()
df['Bollinger_Upper'] = df['MA20'] + (df['STD'] * 1.5)
df['Bollinger_Lower'] = df['MA20'] - (df['STD'] * 1.5)

# RSI Egyszerűsített számítás
delta = df['Piaci Ár ($)'].diff().bfill()
gain = (delta.where(delta > 0, 0)).rolling(window=10).mean().bfill()
loss = (-delta.where(delta < 0, 0)).rolling(window=10).mean().bfill()
rs = gain / (loss + 1e-6)
df['RSI'] = 100 - (100 / (1 + rs))

current_price = df['Piaci Ár ($)'].iloc[-1]
current_rsi = df['RSI'].iloc[-1]
current_upper = df['Bollinger_Upper'].iloc[-1]
current_lower = df['Bollinger_Lower'].iloc[-1]

# Automatikus jelzés logika
if current_price < current_lower and current_rsi < 35:
    signal = "ERŐS VÉTEL (BUY) 🟢 - Túladott zóna"
elif current_price > current_upper and current_rsi > 65:
    signal = "ERŐS ELADÁS (SELL) 🔴 - Túlvásárolt zóna"
else:
    signal = "SEMLEGES (HOLD) 🟡 - Kivárás"

# --- 2. MODUL: Dinamikus Stop-Loss és Take-Profit Számítás ---
risk_amount = account_balance * (risk_level / 100.0)
stop_loss_price = current_price * (1 - (risk_level / 100.0))
take_profit_price = current_price * (1 + (risk_level * 2 / 100.0)) # 2:1 hozam-kockázat arány

# --- 3. MODUL: Gépi Tanulásos Irány-Előrejelzés (Linear Regression) ---
X = np.array(range(len(df))).reshape(-1, 1)
y = df['Piaci Ár ($)'].values
model = LinearRegression()
model.fit(X, y)
next_X = np.array([[len(df)]])
predicted_next_price = model.predict(next_X)[0]
trend_direction = "Felfelé 📈" if predicted_next_price > current_price else "Lefelé 📉"

# Főoldali Metrikák Megjelenítése
col1, col2, col3, col4 = st.columns(4)
col1.metric("Aktuális Ár", f"${current_price:,.2f}", f"RSI: {current_rsi:.1f}")
col2.metric("Ajánlott Jelzés", signal)
col3.metric("ML Trend Előrejelzés", trend_direction, f"Várható: ${predicted_next_price:,.2f}")
col4.metric("Kockázat / Kötés", f"${risk_amount:,.2f}", f"{risk_level}%")

st.markdown("---")

# Kockázatkezelési Panel
st.subheader("🛡️ Dinamikus Kockázatkezelési Paraméterek (Stop-Loss / Take-Profit)")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Javasolt Stop-Loss (Veszteségvágás)", f"${stop_loss_price:,.2f}", f"-{risk_level}%")
scol2.metric("Javasolt Take-Profit (Célár)", f"${take_profit_price:,.2f}", f"+{risk_level*2}%")
scol3.metric("Kockázat-Hozam Arány", "1 : 2.0", "Optimális Kvant Arány")

st.markdown("---")

# Grafikon megjelenítése a Bollinger-szalagokkal
st.subheader(f"📈 Technikai Elemzés és Bollinger-szalagok: {selected_symbol}")
chart_data = df[['Piaci Ár ($)', 'Bollinger_Upper', 'Bollinger_Lower']]
st.line_chart(chart_data)

# Információs doboz
st.info(f"💡 *Kvant Magyarázat:* A rendszer az elmúlt adatok alapján kiszámolta, hogy az eszköz RSI értéke *{current_rsi:.1f}. A gépi tanulásos modell a következő időszakra *${predicted_next_price:,.2f}**-es árat valószínűsít.")
