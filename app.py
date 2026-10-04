import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mester Kvant Dashboard", page_icon="📈", layout="wide")

st.title("🏛️ Mester Kvant - Intézményi Kereskedési Dashboard")
st.markdown("Üdvözlöm a vezérlőpulton! Itt nyomon követheti a felhőben futó kvantitatív motor kereskedési naplóit és teljesítménymutatóit.")

csv_filename = 'trading_journal.csv'

if os.path.exists(csv_filename):
    df = pd.read_csv(csv_filename)
    
    # Utolsó nap adatai
    latest_date = df['Date'].max()
    st.subheader(f"📅 Legfrissebb jelentés dátuma: {latest_date}")
    
    latest_df = df[df['Date'] == latest_date]
    st.dataframe(latest_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📜 Teljes Kereskedési Napló Előzmény")
    st.dataframe(df, use_container_width=True)
    
    # Vizuális elemzés
    st.markdown("---")
    st.subheader("📊 Árak alakulása a naplóban")
    if 'Ticker' in df.columns and 'Price' in df.columns:
        selected_ticker = st.selectbox("Válasszon eszközt a részletes elemzéshez:", df['Ticker'].unique())
        ticker_data = df[df['Ticker'] == selected_ticker]
        st.line_chart(ticker_data.set_index('Date')['Price'])
else:
    st.warning("Még nem található trading_journal.csv naplófájl. Futtassa először a botot a GitHub Actions-ben!")
