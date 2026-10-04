import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Beállítások
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

tickers = ['BTC-USD', 'ETH-USD', 'GLD', 'AAPL', 'NVDA', 'TSLA']
portfolio = {'BTC-USD': 0.05, 'ETH-USD': 0.5, 'GLD': 2.0, 'AAPL': 1.0, 'NVDA': 1.0, 'TSLA': 1.0}

today_str = datetime.now().strftime('%Y-%m-%d')
print("Mester Kvant - Intézményi Motor Indítása...")

# 1. Piaci Hangulat (Crypto Fear & Greed)
market_sentiment = "Ismeretlen"
try:
    fg_res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
    val = fg_res['data'][0]['value']
    text_sent = fg_res['data'][0]['value_classification']
    market_sentiment = f"{val}/100 ({text_sent})"
except Exception as e:
    print(f"F&G Hiba: {e}")

data_results = []
journal_rows = []
total_daily_profit = 0.0
alerts = []

for ticker in tickers:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y") # 1 év adat a backtesthez és elemzéshez
        
        if len(hist) >= 50:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            # SMA 50 & RSI
            sma_50 = hist['Close'].iloc[-50:].mean()
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # ATR Stop-Loss / Take-Profit
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (2.5 * atr)

            # --- BACKTESTING / VISSZATESZTELÉSI MOTOR ---
            hist['SMA20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            hist['Signal'] = np.where(hist['SMA20'] > hist['SMA50'], 1, -1)
            hist['Strategy_Return'] = hist['Signal'].shift(1) * hist['Close'].pct_change()
            total_strategy_return = (1 + hist['Strategy_Return'].dropna()).prod() - 1
            backtest_score = f"{total_strategy_return * 100:.1f}% (1 éves hozam)"

            # Portfólió profit
            holding = portfolio.get(ticker, 0)
            daily_gain_usd = (current_price - prev_price) * holding
            total_daily_profit += daily_gain_usd

            line = (
                f"• {ticker}: {current_price:.2f} USD ({change:+.2f}%)\n"
                f"  └ RSI: {rsi:.1f} | SMA50: {sma_50:.2f}\n"
                f"  └ Backtest (1Y): {backtest_score}\n"
                f"  └ 🛡️ SL: {stop_loss:.2f} | 🎯 TP: {take_profit:.2f}"
            )
            data_results.append(line)

            journal_rows.append({
                'Date': today_str, 'Ticker': ticker, 'Price': round(current_price, 2),
                'Change_Pct': round(change, 2), 'RSI': round(rsi, 1), 'SMA50': round(sma_50, 2),
                'StopLoss': round(stop_loss, 2), 'TakeProfit': round(take_profit, 2)
            })

            if abs(change) >= 3.0:
                direction = "emelkedés 🚀" if change > 0 else "esés 🩸"
                alerts.append(f"🚨 FIGYELEM: {ticker} {abs(change):.2f}%-os {direction}!")
    except Exception as e:
        print(f"Hiba {ticker} feldolgozásakor: {e}")

# Napló mentése CSV-be
try:
    df_new = pd.DataFrame(journal_rows)
    csv_filename = 'trading_journal.csv'
    if os.path.exists(csv_filename):
        df_old = pd.read_csv(csv_filename)
        df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        df_combined.to_csv(csv_filename, index=False)
    else:
        df_new.to_csv(csv_filename, index=False)
except Exception as e:
    print(f"Naplózási hiba: {e}")

# Üzenet összeállítása Telegramra interaktív gombokkal
message = f"🏛️ Mester Kvant Intézményi Jelentés ({today_str})\n\n"
message += f"🌐 Piaci Hangulat: {market_sentiment}\n\n"
message += "\n\n".join(data_results) + "\n\n"

if alerts:
    message += "⚠️ Riasztások:\n" + "\n".join(alerts) + "\n\n"

profit_icon = "🟢" if total_daily_profit >= 0 else "🔴"
message += f"💰 Napi Portfólió Változás: {profit_icon} {total_daily_profit:+.2f} USD"

# Telegram API hívás inline gombokkal
url_text = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
keyboard = {
    "inline_keyboard": [
        [{"text": "🔄 Frissítés / Újraelemzés", "callback_data": "refresh_data"}],
        [{"text": "📊 Részletes Statisztika", "callback_data": "show_stats"}]
    ]
}
payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'Markdown',
    'reply_markup': keyboard
}
response = requests.post(url_text, json=payload)
print(f"Telegram üzenet státusz: {response.status_code}")
