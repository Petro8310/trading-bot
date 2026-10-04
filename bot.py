import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Beállítások
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    return requests.post(url, json=payload)

def send_telegram_photo(photo_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        return requests.post(url, data=data, files=files)

def generate_ai_commentary(sentiment_text, total_profit, rsi_values):
    """Intézményi szintű AI elemző szöveg generálása a kiszámolt adatok alapján"""
    commentary = "🤖 Mester Kvant AI Elemzés & Döntéstámogatás:\n"
    
    # Piaci hangulat és profit alapján történő értékelés
    if "Greed" in sentiment_text or "Kapzsiság" in sentiment_text:
        commentary += "• Piaci struktúra: A piaci hangulat optimizmust mutat. Ajánlott óvatosnak lenni a túlzott kockázatvállalással a magasabb RSI zónákban.\n"
    else:
        commentary += "• Piaci struktúra: A hangulat óvatos vagy félelem zónában van, ami kedvező belépési pontokat teremthet a hosszú távú portfólióépítéshez.\n"
        
    if total_profit >= 0:
        commentary += f"• Portfólió teljesítmény: A napi portfólió pozitív dinamikát mutat (+{total_profit:.2f} USD), a trendkövető pozíciók stabilan teljesítenek.\n"
    else:
        commentary += f"• Portfólió teljesítmény: A mai napon kisebb korrekció tapasztalható ({total_profit:.2f} USD), a Stop-Loss szintek véδik a tőkét.\n"
        
    # Extrém RSI figyelés
    overbought = [t for t, rsi in rsi_values.items() if rsi > 70]
    oversold = [t for t, rsi in rsi_values.items() if rsi < 40]
    
    if overbought:
        commentary += f"• Figyelmeztetés: Túlvett zónához közelít: {', '.join(overbought)}. Profitrealizálás fontolóra vehető.\n"
    if oversold:
        commentary += f"• Lehetőség: Alulárazott/túladott zóna: {', '.join(oversold)}. Potenciális felpattanási esély.\n"
        
    commentary += "• Stratégia javaslat: Kövesse fegyelmezetten az ATR alapú SL/TP szinteket, ne hagyja magát érzelmektől vezérelni."
    return commentary

try:
    tickers = ['BTC-USD', 'ETH-USD', 'GLD', 'AAPL', 'NVDA', 'TSLA']
    portfolio = {'BTC-USD': 0.05, 'ETH-USD': 0.5, 'GLD': 2.0, 'AAPL': 1.0, 'NVDA': 1.0, 'TSLA': 1.0}

    today_str = datetime.now().strftime('%Y-%m-%d')
    print("Mester Kvant - Intézményi Motor Indítása (AI Elemzéssel)...")

    # Piaci Hangulat (Crypto Fear & Greed)
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
    prices_for_chart = {}
    rsi_dict = {}

    for ticker in tickers:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        
        if len(hist) >= 50:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            prices_for_chart[ticker] = hist['Close'].tail(30)
            
            # SMA 50 & RSI
            sma_50 = hist['Close'].iloc[-50:].mean()
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            rsi_dict[ticker] = rsi
            
            # ATR Stop-Loss / Take-Profit
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (2.5 * atr)

            # --- BACKTESTING MOTOR ---
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

    # Napló mentése CSV-be
    df_new = pd.DataFrame(journal_rows)
    csv_filename = 'trading_journal.csv'
    if os.path.exists(csv_filename):
        df_old = pd.read_csv(csv_filename)
        df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        df_combined.to_csv(csv_filename, index=False)
    else:
        df_new.to_csv(csv_filename, index=False)

    # --- GRAFIKON GENERÁLÁS MATPLOTLIB-BEL ---
    plt.figure(figsize=(10, 5))
    for t_name, series in prices_for_chart.items():
        norm_series = (series / series.iloc[0]) * 100
        plt.plot(norm_series.index, norm_series, label=t_name)
    
    plt.title("Mester Kvant - Eszközök Teljesítménye (Utolsó 30 nap, Normalizált)")
    plt.xlabel("Dátum")
    plt.ylabel("Érték (%)")
    plt.legend(loc="upper left")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    chart_path = "market_chart.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()

    # AI Elemzés generálása
    ai_text = generate_ai_commentary(market_sentiment, total_daily_profit, rsi_dict)

    # Üzenet összeállítása Telegramra
    message = f"🏛️ Mester Kvant Intézményi Jelentés ({today_str})\n\n"
    message += f"🌐 Piaci Hangulat: {market_sentiment}\n\n"
    message += "\n\n".join(data_results) + "\n\n"

    if alerts:
        message += "⚠️ Riasztások:\n" + "\n".join(alerts) + "\n\n"

    profit_icon = "🟢" if total_daily_profit >= 0 else "🔴"
    message += f"💰 Napi Portfólió Változás: {profit_icon} {total_daily_profit:+.2f} USD\n\n"
    message += f"-----------------------------------\n{ai_text}"

    # Telegram üzenet + Gombok küldése
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 Frissítés / Újraelemzés", "callback_data": "refresh_data"}],
            [{"text": "📊 Részletes Statisztika", "callback_data": "show_stats"}]
        ]
    }
    
    send_telegram_message(message, reply_markup=keyboard)

    # Grafikon küldése képtként
    if os.path.exists(chart_path):
        send_telegram_photo(chart_path, caption="📈 30 napos normalizált piaci teljesítmény")

    print("Futás sikeresen lezajlott AI elemzéssel!")

except Exception as err:
    error_msg = f"🚨 KRITIKUS HIBA A KVANTOVÁSI MOTORBAN:\n`{str(err)}`"
    print(error_msg)
    try:
        send_telegram_message(error_msg)
    except Exception:
        pass
    raise err
