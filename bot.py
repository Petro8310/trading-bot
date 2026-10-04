import os
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

# Saját portfólió (Itt írhatod át, hogy miből mennyi van a tulajdonodban)
portfolio = {
    'BTC-USD': 0.05,  # pl. 0.05 Bitcoin
    'ETH-USD': 0.5,   # pl. 0.5 Ethereum
    'GLD': 2.0,       # pl. 2 arany ETF
    'AAPL': 1.0,      # pl. 1 Apple részvény
    'NVDA': 1.0,      # pl. 1 Nvidia részvény
    'TSLA': 1.0       # pl. 1 Tesla részvény
}

data_results = []
names = []
changes = []
alerts = []
total_daily_profit = 0.0

print("Speciális Tőzsdei Bot inditása...")

for ticker in tickers:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="60d") # Kell elegendő adat az SMA-hoz és RSI-hez
        
        if len(hist) >= 15:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            # SMA 50 kiszámítása (ha van elég adat)
            sma_50 = hist['Close'].iloc[-50:].mean() if len(hist) >= 50 else hist['Close'].mean()
            
            # RSI kiszámítása (14 napos)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Portfólió profit/veszteség számítás az adott eszközre
            holding = portfolio.get(ticker, 0)
            daily_gain_usd = (current_price - prev_price) * holding
            total_daily_profit += daily_gain_usd

            # Sor összeállítása
            line = f"• {ticker}: {current_price:.2f} USD ({change:+.2f}%)\n  └ RSI: {rsi:.1f} | SMA50: {sma_50:.2f}"
            data_results.append(line)
            
            names.append(ticker)
            changes.append(change)

            # Intelligens riasztás küszöb: ha a napi változás nagyobb mint ±3.0%
            if abs(change) >= 3.0:
                direction = "emelkedés 🚀" if change > 0 else "esés 🩸"
                alerts.append(f"🚨 FIGYELEM: {ticker} {abs(change):.2f}%-os {direction}!")
        else:
            current_price = hist['Close'].iloc[-1]
            data_results.append(f"• {ticker}: {current_price:.2f} USD (N/A)")
    except Exception as e:
        print(f"Hiba a(z) {ticker} lekérdezésekor: {e}")

# Üzenet összeállítása
today_str = datetime.now().strftime('%Y-%m-%d')
message = f"📊 Intelligens Piaci Jelentés ({today_str})\n\n"
message += "\n".join(data_results) + "\n\n"

# Ha van riasztás, adjuk hozzá az üzenethez
if alerts:
    message += "⚠️ Riasztások:\n" + "\n".join(alerts) + "\n\n"

# Portfólió összegzés hozzáadása
profit_icon = "🟢" if total_daily_profit >= 0 else "🔴"
message += f"💰 Napi Portfólió Változás: {profit_icon} {total_daily_profit:+.2f} USD"

# Heti összesítő ellenőrzés (ha ma péntek van, küld egy külön extra jelet is)
if datetime.now().weekday() == 4:
    message += "\n\n📅 Heti Záró Összegzés napja van! Szép munka a héten!"

# Grafikon generálása
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

# Szöveges üzenet küldése Telegramra
url_text = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'Markdown'
}
response = requests.post(url_text, json=payload)
print(f"Telegram szöveg válasz státusz: {response.status_code}")

# Grafikon küldése Telegramra
if has_chart and response.status_code == 200:
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as photo_file:
        files = {'photo': photo_file}
        data_photo = {'chat_id': TELEGRAM_CHAT_ID, 'caption': '📈 Technikai mutatók & Teljesítmény grafikon'}
        resp_photo = requests.post(url_photo, data=data_photo, files=files)
        print(f"Telegram kép válasz státusz: {resp_photo.status_code}")

print("Minden feladat sikeresen lefutott!")
