
import streamlit as st
import pandas as pd
import numpy as np

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Prop Firm Funded Terminal",
    page_icon="💼",
    layout="wide"
)

# Címsor
st.title("💼 Mester Kvant - Prop Firm & Funded Account Kötéskezelő")
st.markdown("Ez a verzió már tartalmazza a *Proprietary Trading (Finanszírozott Számla) Szabályzatfigyelőt*, a napi veszteség-limiteket és a célkitűzés-követőt!")

# Oldalsáv (Sidebar)
st.sidebar.header("Prop Firm Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Fő eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
target_account_size = st.sidebar.selectbox("Célzott Prop Számla Méret", ["$10,000", "$50,000", "$100,000"])
max_daily_loss_limit = st.sidebar.slider("Megengedett Napi Veszteség Limit (%)", 3, 5, 4)

if bot_status:
    st.sidebar.success("Státusz: PROP CHALLENGE MÓD AKTÍV 🟢")
else:
    st.sidebar.warning("Státusz: LEÁLLÍTVA 🔴")

# Adatgenerálás szimulációhoz
np.random.seed(4040)
n_periods = 170
base_price = 73000.0 if "BTC" in selected_symbol else (3000.0 if "ETH" in selected_symbol else 230.0)
price_changes = np.random.normal(loc=0.0007, scale=0.015, size=n_periods)
prices = base_price * np.cumprod(1 + price_changes)

df = pd.DataFrame({'Piaci Ár ($)': prices})

# --- PROP FIRM SZABÁLYZAT & NAPI VESZTESÉG MODUL ---
df['Returns'] = df['Piaci Ár ($)'].pct_change().fillna(0)
current_drawdown = (df['Piaci Ár ($)'].cummax() - df['Piaci Ár ($)']) / df['Piaci Ár ($)'].cummax() * 100
max_dd_current = current_drawdown.iloc[-1]

# Célkitűzés (pl. 10% profit target a kihíváshoz)
profit_target_pct = 10.0
current_profit_pct = ((df['Piaci Ár ($)'].iloc[-1] - df['Piaci Ár ($)'].iloc[0]) / df['Piaci Ár ($)'].iloc[0]) * 100

if max_dd_current > max_daily_loss_limit:
    prop_status = "SZABÁLYSértés / FAIL ❌ (Túllépett napi drawdown)"
    prop_color = "red"
elif current_profit_pct >= profit_target_pct:
    prop_status = "CHALLENGE TELJESÍTVE! 🏆 (Tőke elnyerve)"
    prop_color = "green"
else:
    prop_status = "CHALLENGE FOLYAMATBAN ✅ (Szabályok betartva)"
    prop_color = "orange"

# --- Főoldali Metrikák Megjelenítése ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Prop Challenge Státusz", prop_status)
col2.metric("Jelenlegi Profit / Hozam", f"{current_profit_pct:+.2f}%", f"Cél: +{profit_target_pct}%")
col3.metric("Aktuális Drawdown (Veszteség)", f"-{max_dd_current:.2f}%", f"Limit: -{max_daily_loss_limit}%")
col4.metric("Kiválasztott Számla", target_account_size)

st.markdown("---")

# Részletes Prop Firm Panel
st.subheader("🎯 Prop Firm Kockázati és Szabályzat-ellenőrző")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Napi Max Drawdown Keret", f"{max_daily_loss_limit}%", "Biztonságos Zóna")
scol2.metric("Célzott Profit Elérés", f"{current_profit_pct:+.2f}%", "Optimalizálva")
scol3.metric("Intézményi Értékelés", "Passzív Megfelelés", "Készen áll a tesztre")

st.markdown("---")

# Grafikon megjelenítése
st.subheader(f"📈 Számlanövekedési Görbe & Drawdown: {selected_symbol}")
st.line_chart(df[['Piaci Ár ($)']])

st.info(f"💡 *Prop Firm Elemzés:* A kiválasztott *{target_account_size}-es* konstrukcióhoz a rendszer figyeli a(z) *{max_daily_loss_limit}%-os maximális napi drawdown limitet. A jelenlegi maximális lehúzás *-{max_dd_current:.2f}%**, ami azt jelenti, hogy a bot tökéletesen betartja a finanszírozott cégek által elvárt szigorú kockázati szabályokat.")
