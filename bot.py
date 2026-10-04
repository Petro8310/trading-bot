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

# Intézményi Kockázatkezelési Paraméterek
TOTAL_CAPITAL_USD = 10000.0  
MAX_RISK_PER_TRADE_PCT = 0.015  

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

def generate_ai_commentary(sentiment_text, total_profit, rsi_values, sharpe_dict):
    commentary = "🤖 Mester Kvant AI Elemzés & Intézményi Mutatók:\n"
    
    if "Greed" in sentiment_text or "Kapzsiság" in sentiment_text:
        commentary += "• Piaci struktúra: Magas optimizmus, fegyelmezett kockázatkezelés és stop-level követés javasolt.\n"
    else:
        commentary += "• Piaci struktúra: Óvatos hangulat, kedvező a strukturált, szűrt belépésekhez.\n"
        
    if total_profit >= 0:
        commentary += f"• Portfólió teljesítmény: Napi nyereség: +{total_profit:.2f} USD. A multi-timeframe trendek stabilak.\n"
    else:
        commentary += f"• Portfólió teljesítmény: Napi korrekció: {total_profit:.2f} USD. A védelem aktív.\n"
        
    overbought = [t for t, rsi in rsi_values.items() if rsi > 70]
    oversold = [t for t, rsi in rsi_values.items() if rsi < 40]
    
    if overbought:
        commentary += f"• Túlvett eszközök: {', '.join(overbought)}. Profitrealizálás fontolóra vehető.\n"
    if oversold:
        commentary += f"• Túladott eszközök: {', '.join(oversold)}. Potenciális felpattanási zóna.\n"
        
    high_sharpe = [t for t, sh in sharpe_dict.items() if sh > 1.0]
    if high_sharpe:
        commentary += f"• Kiváló kockázattal súlyozott hozam (Sharpe > 1.0): {', '.join(high_sharpe)}.\n"
        
    commentary += f"• Intézményi fegyelem: Max kockázat pozíciónként: {MAX_RISK_PER_TRADE_PCT*100}%. Multi-timeframe szűrő aktív."
    return commentary

try:
    tickers = ['BTC-USD', 'ETH-USD', 'GLD', 'AAPL', 'NVDA', 'TSLA']
    portfolio = {'BTC-USD': 0.05, 'ETH-USD': 0.5, 'GLD': 2.0, 'AAPL': 1.0, 'NVDA': 1.0, 'TSLA': 1.0}

    today_str = datetime.now().strftime('%Y-%m-%d')
    print("Mester Kvant - Intézményi Motor Indítása (Minden funkcióval)...")

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
    sharpe_dict = {}

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
            
            # --- MULTI-TIMEFRAME TRENDSZŰRŐ (Heti + Napi) ---
            weekly_hist = t.history(period="1y", interval="1wk")
            if len(weekly_hist) >= 10:
                weekly_close = weekly_hist['Close'].iloc[-1]
                weekly_sma10 = weekly_hist['Close'].iloc[-10:].mean()
                weekly_trend = "Bika 📈 (Heti felett)" if weekly_close > weekly_sma10 else "Medve 📉 (Heti alatt)"
                trend_confirmed = weekly_close > weekly_sma10
            else:
                weekly_trend = "N/A"
                trend_confirmed = True

            # --- SHARPE-RÁTA & MAX DRAWDOWN ---
            returns = hist['Close'].pct_change().dropna()
            if returns.std() > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0.0
            sharpe_dict[ticker] = sharpe_ratio

            rolling_max = hist['Close'].cummax()
            drawdown = (hist['Close'] - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100

            # ATR Stop-Loss / Take-Profit
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]
            
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (2.5 * atr)

            # Dinamikus pozíció-méretezés
            risk_budget_usd = TOTAL_CAPITAL_USD * MAX_RISK_PER_TRADE_PCT
            sl_distance = current_price - stop_loss
            if sl_distance > 0:
                recommended_shares = risk_budget_usd / sl_distance
            else:
                recommended_shares = 0

            # Backtesting motor
            hist['SMA20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            hist['Signal'] = np.where(hist['SMA20'] > hist['SMA50'], 1, -1)
            hist['Strategy_Return'] = hist['Signal'].shift(1) * hist['Close'].pct_change()
            total_strategy_return = (1 + hist['Strategy_Return'].dropna()).prod() - 1
            backtest_score = f"{total_strategy_return * 100:.1f}% (1Y)"

            holding = portfolio.get(ticker, 0)
            daily_gain_usd = (current_price - prev_price) * holding
            total_daily_profit += daily_gain_usd

            status_icon = "🟢" if trend_confirmed else "🟡"
            line = (
                f"• {ticker}: {current_price:.2f} USD ({change:+.2f}%)\n"
                f"  └ RSI: {rsi:.1f} | SMA50: {sma_50:.2f}\n"
                f"  └ Heti Trend: {status_icon} {weekly_trend}\n"
                f"  └ Sharpe: {sharpe_ratio:.2f} | Max DD: {max_drawdown:.1f}%\n"
                f"  └ Backtest: {backtest_score}\n"
                f"  └ 🛡️ SL: {stop_loss:.2f} | 🎯 TP: {take_profit:.2f}\n"
                f"  └ ⚖️ Méret: {recommended_shares:.2f} db"
            )
            data_results.append(line)

            journal_rows.append({
                'Date': today_str, 'Ticker': ticker, 'Price': round(current_price, 2),
                'Change_Pct': round(change, 2), 'RSI': round(rsi, 1), 'SMA50': round(sma_50, 2),
                'Sharpe': round(sharpe_ratio, 2), 'MaxDD': round(max_drawdown, 1),
                'StopLoss': round(stop_loss, 2), 'TakeProfit': round(take_profit, 2),
                'Rec_Shares': round(recommended_shares, 2)
            })

            if abs(change) >= 3.0:
                direction = "emelkedés 🚀" if change > 0 else "esés 🩸"
                alerts.append(f"🚨 FIGYELEM: {ticker} {abs(change):.2f}%-os {direction}!")

    df_new = pd.DataFrame(journal_rows)
    csv_filename = 'trading_journal.csv'
    if os.path.exists(csv_filename):
        df_old = pd.read_csv(csv_filename)
        df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        df_combined.to_csv(csv_filename, index=False)
    else:
        df_new.to_csv(csv_filename, index=False)

    # Grafikon
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

    ai_text = generate_ai_commentary(market_sentiment, total_daily_profit, rsi_dict, sharpe_dict)

    message = f"🏛️ Mester Kvant Intézményi Jelentés ({today_str})\n\n"
    message += f"🌐 Piaci Hangulat: {market_sentiment}\n\n"
    message += "\n\n".join(data_results) + "\n\n"

    if alerts:
        message += "⚠️ Riasztások:\n" + "\n".join(alerts) + "\n\n"

    profit_icon = "🟢" if total_daily_profit >= 0 else "🔴"
    message += f"💰 Napi Portfólió Változás: {profit_icon} {total_daily_profit:+.2f} USD\n\n"
    message += f"-----------------------------------\n{ai_text}"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 Frissítés / Újraelemzés", "callback_data": "refresh_data"}],
            [{"text": "📊 Részletes Statisztika", "callback_data": "show_stats"}]
        ]
    }
    
    send_telegram_message(message, reply_markup=keyboard)

    if os.path.exists(chart_path):
        send_telegram_photo(chart_path, caption="📈 30 napos normalizált piaci teljesítmény")

    print("Minden intézményi modul sikeresen lefutott!")

except Exception as err:
    error_msg = f"🚨 KRITIKUS HIBA A KVANTOVÁSI MOTORBAN:\n`{str(err)}`"
    print(error_msg)
    try:
        send_telegram_message(error_msg)
    except Exception:
        pass
    raise err
