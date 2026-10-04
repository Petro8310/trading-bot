import os
requests_installed = True
import requests
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

# Telegram beállítások
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Figyelt eszközök listája
tickers = ['BTC-USD', 'ETH-USD', 'GLD', 'AAPL', 'NVDA', 'TSLA']

# Saját portfólió
portfolio = {
    'BTC-USD': 0.05,
    'ETH-USD': 0.5,
    'GLD': 2.0,
    'AAPL': 1.0,
    'NVDA': 1.0,
    'TSLA': 1.0
}

data_results = []
journal_rows = []
names = []
changes = []
alerts = []
total_daily_profit = 0.0
today_str = datetime.now().strftime('%Y-%m-%d')

print("Mester Kvant Bot inditasa...")

# 1. Globális Piaci Hangulat (Crypto Fear & Greed Index lekérése)
market_sentiment = "Ismeretlen"
try:
    fg_res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
    val = fg_res['data'][0]['value']
    text_sent = fg_res['data'][0]['value_classification']
    market_sentiment = f"{val}/100 ({text_sent})"
except Exception as e:
    print(f"Nem sikerült lekérni a hangulatot: {e}")

# 2. Eszközök elemzése
for ticker in tickers:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="60d")
        hist_weekly = t.history(period="6mo", interval="1wk")
        
        if len(hist) >= 15:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            # SMA 50 & SMA 200
            sma_50 = hist['Close'].iloc[-50:].mean() if len(hist) >= 50 else hist['Close'].mean()
            
            # RSI (14 napos)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # ATR alapú Stop-Loss és Take-Profit kalkuláció (Kockázatkezelés)
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (2.5 * atr)
            
            # Multi-Timeframe Trend (Napi vs Heti)
            weekly_trend = "Bika 📈" if len(hist_weekly) >= 2 and hist_weekly['Close'].iloc[-1] > hist_weekly['Close'].iloc[-2] else "Medve 📉"

            # Portfólió profit/veszteség
            holding = portfolio.get(ticker, 0)
            daily_gain_usd = (current_price - prev_price) * holding
            total_daily_profit += daily_gain_usd

            # Eredmény sor
            line = (
                f"• {ticker}: {current_price:.2f} USD ({change:+.2f}%)\n"
                f"  └ RSI: {rsi:.1f} | SMA50: {sma_50:.2f}\n"
                f"  └ Heti Trend: {weekly_trend}\n"
                f"  └ 🛡️ SL: {stop_loss:.2f} | 🎯 TP: {take_profit:.2f}"
            )
            data_results.append(line)
            
            names.append(ticker)
            changes.append(change)

            # Naplózás sor előkészítése
            journal_rows.append({
                'Date': today_str,
                'Ticker': ticker,
                'Price': round(current_price, 2),
                'Change_Pct': round(change, 2),
                'RSI': round(rsi, 1),
                'SMA50': round(sma_50, 2),
                'StopLoss': round(stop_loss, 2),
                'TakeProfit': round(take_profit, 2)
            })

            # Intelligens riasztás (>3%)
            if abs(change) >= 3.0:
                direction = "emelkedés 🚀" if change > 0 else "esés 🩸"
                alerts.append(f"🚨 FIGYELEM: {ticker} {abs(change):.2f}%-os {direction}!")
        else:
            current_price = hist['Close'].iloc[-1]
            data_results.append(f"• {ticker}: {current_price:.2f} USD (N/A)")
    except Exception as e:
        print(f"Hiba a(z) {ticker} lekérdezésekor: {e}")

# 3. CSV Napló mentése és frissítése a repóban
try:
    df_new = pd.DataFrame(journal_rows)
    csv_filename = 'trading_journal.csv'
    if os.path.exists(csv_filename):
        df_old = pd.read_csv(csv_filename)
        df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        df_combined.to_csv(csv_filename, index=False)
    else:
        df_new.to_csv(csv_filename, index=False)
    print("Kereskedési napló sikeresen frissítve.")
except Exception as e:
    print(f"Hiba a naplózáskor: {e}")

# 4. Telegram Üzenet Összeállítása
message = f"🧠 Mester Kvant Jelentés ({today_str})\n\n"
message += f"🌐 Piaci Hangulat (Crypto F&G): {market_sentiment}\n\n"
message += "\n\n".join(data_results) + "\n\n"

if alerts:
    message += "⚠️️ Riasztások:\n" + "\n".join(alerts) + "\n\n"

profit_icon = "🟢" if total_daily_profit >= 0 else "🔴"
message += f"💰 Napi Portfólió Változás: {profit_icon} {total_daily_profit:+.2f} USD"

if datetime.now().weekday() == 4:
    message += "\n\n📅 Heti Záró Összegzés: Szép volt a hét! 🏆"

# 5. Grafikon Generálása
has_chart = False
try:
    plt.figure(figsize=(9, 4.5))
    colors = ['green' if c >= 0 else 'red' for c in changes]
    plt.bar(names, changes, color=colors)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title(f'Napi Változások (%) - {today_str}')
    plt.ylabel('Százalék (%)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    chart_path = 'market_chart.png'
    plt.savefig(chart_path, dpi=150)
    plt.close()
    has_chart = True
    print("Grafikon sikeresen generálva.")
except Exception as e:
    print(f"Hiba a grafikon generálásakor: {e}")

# 6. Küldés Telegramra (Szöveg)
url_text = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'Markdown'
}
response = requests.post(url_text, json=payload)
print(f"Telegram szöveg válasz státusz: {response.status_code}")

# 7. Küldés Telegramra (Kép)
if has_chart and response.status_code == 200:
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as photo_file:
        files = {'photo': photo_file}
        data_photo = {'chat_id': TELEGRAM_CHAT_ID, 'caption': '📈 Mester Kvant Elemzés & Portfólió'}
        resp_photo = requests.post(url_photo, data=data_photo, files=files)
        print(f"Telegram kép válasz státusz: {resp_photo.status_code}")

print("Minden mester feladat sikeresen lefutott!")
