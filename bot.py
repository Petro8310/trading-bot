import os
import requests
import yfinance as yf

# 1. Beolvesszük a GitHub Secret-ként rögzített adatokat
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Ellenőrizzük, hogy megvannak-e a kulcsok
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("Hiba: A TELEGRAM_TOKEN vagy a TELEGRAM_CHAT_ID nincs beállítva!")
    exit(1)

# 3. Az elemzendő eszközök listája
TICKERS = ["BTC-USD", "ETH-USD", "GLD", "AAPL", "NVDA", "TSLA"]

def get_market_data():
    report = "🤖 *PetroCryptoBot - Piaci Elemzés* 📈\n\n"
    
    for symbol in TICKERS:
        try:
            ticker = yf.Ticker(symbol)
            # Az utolsó 5 nap adatait kérjük le a biztonságos számításhoz
            df = ticker.history(period="5d")
            
            if df.empty:
                report += f"❌ *{symbol}*: Nincs elérhető adat.\n\n"
                continue
                
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            emoji = "🟢" if change >= 0 else "🔴"
            report += f"{emoji} *{symbol}*\n"
            report += f"• Ár: ${current_price:,.2f}\n"
            report += f"• Változás: {change:+.2f}%\n\n"
            
        except Exception as e:
            report += f"⚠️ *{symbol}*: Hiba történt az adatok lekérdezésekor.\n\n"
            
    return report

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Üzenet sikeresen elküldve a Telegramra!")
    else:
        print(f"Hiba a küldés során: {response.text}")

if _name_ == "_main_":
    print("Piaci adatok lekérdezése folyamatban...")
    message = get_market_data()
    send_telegram_message(message)
