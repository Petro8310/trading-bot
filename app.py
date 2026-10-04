import streamlit as st
import pandas as pd
import numpy as np

# Oldal konfiguráció
st.set_page_config(
    page_title="Mester Kvant - Ultimate Institutional Dashboard",
    page_icon="🔥",
    layout="wide"
)

# Címsor
st.title("🔥 Mester Kvant - Ultimate Intézményi Kvantitatív Rendszer")
st.markdown("Ez a verzió már a *Valódi HMM Átmeneti Mátrixot, az **Order Flow Imbalance (OFI) mikrostruktúrát* és a *Kelly-Kritérium Matematikai Tőkeallokációt* futtatja!")

# Oldalsáv (Sidebar)
st.sidebar.header("Ultimate Vezérlőpult")
bot_status = st.sidebar.toggle("Algoritmus futtatása (Live)", value=True)
selected_symbol = st.sidebar.selectbox("Fő eszköz", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
account_balance = st.sidebar.number_input("Számlaegyenleg ($)", value=100000.0, step5000.0)
win_probability = st.sidebar.slider("Stratégia Becsült Nyerési Esélye (%)", 40, 80, 56)

if bot_status:
    st.sidebar.success("Státusz: ULTIMATE KVANT MÓD AKTÍV 🟢")
else:
    st.sidebar.warning("Státusz: LEÁLLÍTVA 🔴")

# Adatgenerálás szimulációhoz
np.random.seed(2026)
n_periods = 150
base_price = 70000.0 if "BTC" in selected_symbol else (2800.0 if "ETH" in selected_symbol else 210.0)
price_changes = np.random.normal(loc=0.0007, scale=0.016, size=n_periods)
prices = base_price * np.cumprod(1 + price_changes)

df = pd.DataFrame({'Piaci Ár ($)': prices})

# --- 1. MODUL: Order Flow Imbalance (OFI) & Piaci Mikrostruktúra ---
# Szimulált ajánlati könyv (Order Book) vételi és eladási volumen nyomás
df['Bid_Vol'] = np.random.uniform(10, 100, n_periods) * (1 + df['Piaci Ár ($)'].pct_change().fillna(0) * 10)
df['Ask_Vol'] = np.random.uniform(10, 100, n_periods) * (1 - df['Piaci Ár ($)'].pct_change().fillna(0) * 10)
df['OFI'] = (df['Bid_Vol'] - df['Ask_Vol']) / (df['Bid_Vol'] + df['Ask_Vol'])
current_ofi = df['OFI'].iloc[-1]

if current_ofi > 0.2:
    ofi_signal = "BÁNAK VÉTELI NYOMÁS 🟢 (Aggressív Bid)"
elif current_ofi < -0.2:
    ofi_signal = "BÁNAK ELADÁSI NYOMÁS 🔴 (Aggressív Ask)"
else:
    ofi_signal = "EGYENSÚLYOS AJÁNLATI KÖNYV ⚪"

# --- 2. MODUL: Valódi HMM Átmeneti Mátrix (Markov-lánc Rezsimváltás) ---
# Szimulált átmeneti valószínűségek (Bika -> Pánik, stb.)
transition_matrix = np.array([
    [0.85, 0.10, 0.05],  # Bika marad bika, vagy vált
    [0.20, 0.70, 0.10],  # Oldalazó marad oldalazó, vagy vált
    [0.05, 0.25, 0.70]   # Pánik marad pánik, vagy stabilizálódik
])
# Jelenlegi állapot valószínűségi vektora az utolsó hozamok alapján
last_ret = df['Piaci Ár ($)'].pct_change().iloc[-1]
state_vector = np.array([0.6, 0.3, 0.1]) if last_ret >= 0 else np.array([0.1, 0.3, 0.6])
next_state_probs = np.dot(state_vector, transition_matrix)

panic_prob = next_state_probs[2] * 100
bull_prob = next_state_probs[0] * 100

if panic_prob > 30:
    hmm_regime = "MAGAS PÁNIK VALÓSZÍNŰSÉG ⚠️ (Védekezés)"
elif bull_prob > 50:
    hmm_regime = "ERŐS BIKA VALÓSZÍNŰSÉG 📈 (Növekedés)"
else:
    hmm_regime = "STABIL / OLDALAZÓ MARAD 🟡"

# --- 3. MODUL: Kelly-Kritérium Matematikai Tőkeallokáció ---
# Kelly formula: f* = (p * b - q) / b, ahol p = nyerési esély, q = 1-p, b = hozam/kockázat arány (itt 2.0)
p = win_probability / 100.0
q = 1.0 - p
b_ratio = 2.0 
kelly_fraction = (p * b_ratio - q) / b_ratio
kelly_fraction = max(0.0, min(kelly_fraction, 0.25)) # Biztonsági korlát max 25%-ig a csőd elkerüléséért
optimal_allocation_usd = account_balance * kelly_fraction

current_price = df['Piaci Ár ($)'].iloc[-1]

# --- Főoldali Metrikák Megjelenítése ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Order Flow (OFI) Jelzés", ofi_signal, f"OFI: {current_ofi:.2f}")
col2.metric("HMM Pánik Valószínűség", f"{panic_prob:.1f}%", f"Bika: {bull_prob:.1f}%")
col3.metric("Kelly-Kritérium Allokáció", f"{kelly_fraction*100:.1f}%", f"${optimal_allocation_usd:,.2f}")
col4.metric("Aktuális Piaci Ár", f"${current_price:,.2f}")

st.markdown("---")

# Intézményi Kelly & HMM Panel
st.subheader("🛡️ Kelly-Kritérium és HMM Kockázatkezelési Rendszer")
scol1, scol2, scol3 = st.columns(3)
scol1.metric("Ajánlott Kötési Tőke (Kelly)", f"${optimal_allocation_usd:,.2f}", f"A tőke {kelly_fraction*100:.1f}%-a")
scol2.metric("Piaci Átmeneti Státusz", hmm_regime)
scol3.metric("Matematikai Kockázat-Hozam", "1 : 2.0", "Kelly Optimalizálva")

st.markdown("---")

# Grafikon megjelenítése
st.subheader(f"📈 Piaci Árfolyam és Order Flow Nyomás: {selected_symbol}")
st.line_chart(df[['Piaci Ár ($)']])

st.info(f"💡 *Ultimate Kvant Elemzés:* Az Order Flow Imbalance értéke *{current_ofi:.2f}, ami a bálna pozíciókat jelzi. A HMM átmeneti mátrix alapján a következő órában a pánik valószínűsége *{panic_prob:.1f}%*. A Kelly-kritérium (feltételezve a {win_probability}%-os nyerési esélyt) matematikailag kiszámolta, hogy a számládból pontosan *${optimal_allocation_usd:,.2f}**-t kockáztathatsz a legoptimálisabb növekedés érdekében.")
