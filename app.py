import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mester Kvant Dashboard", page_icon="📈", layout="wide")

st.title("🏛️ Mester Kvant - Élő Kereskedési & Portfólió Dashboard")
st.markdown("Üdvözlök a saját intézményi szintű elemző rendszeredben! Itt követheted nyomon a virtuális vagyonodat és a naplózott stratégiákat.")

csv_filename = 'trading_journal.csv'
if os.path.exists(csv_filename):
    df = pd.read_csv(csv_filename)
    st.subheader("📊 Legfrissebb Elemzési Adatok")
    st.dataframe(df.tail(10), use_container_width=True)
    
    st.subheader("📈 Árfolyamok és Mutatók Grafikonon")
    selected_ticker = st.selectbox("Válassz eszközt:", df['Ticker'].unique())
    ticker_data = df[df['Ticker'] == selected_ticker]
    if not ticker_data.empty:
        st.line_chart(ticker_data.set_index('Date')['Price'])
else:
    st.warning("Még nincsenek naplózott adatok. Futtasd le a botot egyszer!")

st.sidebar.header("Rendszer Információk")
st.sidebar.info("Státusz: 🟢 Futáskész\nVerzió: 4.0 Intézményi")
