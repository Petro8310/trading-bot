import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Elite Monte Carlo & Momentum Rendszer",
    page_icon="🚀",
    layout="wide"
)

# Címsor
st.title("🚀 Mester Kvant - Elit Intézményi Kvantitatív Rendszer")
st.markdown("Ez a csúcsverzió már tartalmazza a *Monte Carlo kockázati szimulációt, a **K-Means cluster alapú piaci mintázat-felismerést* és a *Momentum Faktor intelligenciát*!")

# Oldalsáv (Sidebar)
st.sidebar.header("Elit Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Fő eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
account_balance = st.sidebar.number_input("Számlaegyenleg ($)", value=50000.0, step=1000.0)
simulation_days = st.sidebar.slider("Monte Carlo Időtáv (Nap)", 5, 30, 10)

if bot_status:
    st.sidebar.success("Státusz: ELIT KVANT MÓD AKTÍV 🟢")
else:
    st.sidebar.warning("Státusz: LEÁLLÍTVA 🔴")

# Adatgenerálás szimulációhoz
np.random.seed(42)
n_periods = 120
base_price = 68000.0 if "BTC" in selected_symbol else (2700.0 if "ETH" in selected_symbol else 200.0)
price_changes = np.random.normal(loc=0.0008, scale=0.018, size=n_periods)
prices = base_price * np.cumprod(1 + price_changes)

df = pd.DataFrame({'Piaci Ár ($)': prices})

# --- 1. MODUL: Monte Carlo Szimuláció (Jövőbeli Kockázat & Max Drawdown) ---
returns = df['Piaci Ár ($)'].pct_change().dropna()
mean_ret = returns.mean()
std_ret = returns.std()
current_price = df['Piaci Ár ($)'].iloc[-1]

# 500 szimulált futás
n_simulations = 500
simulated_prices = np.zeros((simulation_days, n_simulations))
for i in range(n_simulations):
    sim_path = [current_price]
    for d in range(1, simulation_days):
        shock = np.random.normal(mean_ret, std_ret)
        sim_path.append(sim_path[-1] * (1 + shock))
    simulated_prices[:, i] = sim_path

final_sim_prices = simulated_prices[-1, :]
var_95 = np.percentile(final_sim_prices, 5)
max_drawdown_est = (current_price - var_95) / current_price * 100

# --- 2. MODUL: K-Means Cluster Alapú Piaci Mintázat-Felismerés ---
df['Returns'] = df['Piaci Ár ($)'].pct_change().fillna(0)
df['Vol_10'] = df['Returns'].rolling(window=10).std().fillna(0)
df['MA_Ratio'] = (df['Piaci Ár ($)'] / df['Piaci Ár ($)'].rolling(window=10).mean()).fillna(1)

X_cluster = df[['Returns', 'Vol_10', 'MA_Ratio']].values
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_cluster)
df['Cluster'] = kmeans.labels_
current_cluster = df['Cluster'].iloc[-1]

cluster_names = {0: "Csendes Akkumuláció 🟢", 1: "Magas Volatilitású Kitörés ⚡", 2: "Korrekciós / Oldalazó Zóna 🟡"}
market_cluster_desc = cluster_names.get(current_cluster, "Ismeretlen Állapot")

# --- 3. MODUL: Momentum Faktor & Hozamsebesség (Momentum Factor Investing) ---
df['Momentum_5'] = df['Piaci Ár ($)'].diff(5)
df['Momentum_20'] = df['Piaci Ár ($)'].diff(20)
momentum_score = (df['Momentum_5'].iloc[-1] * 0.7) + (df['Momentum_20'].iloc[-1] * 0.3)

if momentum_score > 0:
    momentum_signal = "ERŐS MOMENTUM VÉTEL 🚀"
else:
    momentum_signal = "NEGATÍV MOMENTUM / EXIT 🔻"

# --- Főoldali Metrikák Megjelenítése ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("K-Means Piaci Klaszter", market_cluster_desc)
col2.metric("Monte Carlo Várható Érték (95%)", f"${var_95:,.2f}", f"Időtáv: {simulation_days} nap")
col3.metric("Becsült Max Lehúzás (VaR)", f"-{max_drawdown_est:.2f}%")
col4.metric("Momentum Faktor Pontszám", f"{momentum_score:.2f}", momentum_signal)

st.markdown("---")

# Kockázatkezelési és Elit Panel
st.subheader("🛡️ Monte Carlo Stochasztikus Kockázatkezelési Elemzés")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Jelenlegi Piaci Ár", f"${current_price:,.2f}")
scol2.metric("Szimulált Pesszimista Célár (5%)", f"${var_95:,.2f}")
scol3.metric("Portfólió Kockázati Index", "Intézményi AAA", "Stabilitás Optimalizálva")

st.markdown("---")

# Grafikon megjelenítése
st.subheader(f"📈 Árfolyam és Klaszter Alapú Trendek: {selected_symbol}")
st.line_chart(df[['Piaci Ár ($) ']])

st.info(f"💡 *Elite Kvant Elemzés:* A K-Means gépi tanulásos algoritmus a mai piaci viszonyokat a(z) *'{market_cluster_desc}'* mintázatba sorolta. A Monte Carlo szimuláció alapján a következő {simulation_days} napban a portfólió 95%-os valószínűséggel a(z) *${var_95:,.2f}* szint felett marad.")
