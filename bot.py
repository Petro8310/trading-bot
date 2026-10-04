import os
import requests
import yfinance as yf

print("Bot inditasa...")

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not token or not chat_id:
    print("Hiba: Nincsenek beallitva a Telegram kulcsok!")
    exit(1)

tickers = ["BTC-USD", "ETH-USD", "GLD", "AAPL", "NVDA", "TSLA"]
report = "Piaci jelentes:\n\n"

for symbol in tickers:
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="5d")
        if not df.empty:
            p1 = df['Close'].iloc[-1]
            p2 = df['Close'].iloc[-2]
            ch = ((p1 - p2) / p2) * 100
            report += symbol + ": " + str(round(p1, 2)) + " USD (" + str(round(ch, 2)) + "%)\n"
        else:
            report += symbol + ": Nincs adat\n"
    except Exception:
        report += symbol + ": Hiba lekerdezeskor\n"

url = "https://api.telegram.org/bot" + token + "/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": report
}

resp = requests.post(url, json=payload)
print("Telegram valasz sttuszu:", resp.status_code)
print("Keszen van!")
