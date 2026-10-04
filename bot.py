
import os
import requests
import yfinance as yf
import matplotlib.pyplot as plt

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

tickers = ['BTC-USD', 'ETH-USD', 'GLD', 'AAPL', 'NVDA', 'TSLA']
data_results = []
names = []
changes = []

print("Bot inditasa es adatok letoltese...")

for ticker in tickers:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            data_results.append(f"• {ticker}: {current_price:.2f} USD ({change:+.2f}%)")
            names.append(ticker)
            changes.append(change)
        else:
            current_price = hist['Close'].iloc[-1]
            data_results.append(f"• {ticker}: {current_price:.2f} USD (N/A)")
    except Exception as e:
        print(f"Hiba a(z) {ticker} lekérdezésekor: {e}")

# Üzenet összeállítása
message = "📊 Automata Piaci Jelentés\n\n" + "\n".join(data_results)

# Grafikon generálása
has_chart = False
try:
    plt.figure(figsize=(8, 4))
    colors = ['green' if c >= 0 else 'red' for c in changes]
    plt.bar(names, changes, color=colors)
    plt.axhline(0, color='black', linewidth=0.8)
    plt.title('Napi Változások (%)')
    plt.ylabel('%')
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

# Grafikon küldése Telegramra (ha sikerült elkészíteni)
if has_chart and response.status_code == 200:
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as photo_file:
        files = {'photo': photo_file}
        data_photo = {'chat_id': TELEGRAM_CHAT_ID, 'caption': '📈 Napi teljesítmény grafikon'}
        resp_photo = requests.post(url_photo, data=data_photo, files=files)
        print(f"Telegram kép válasz státusz: {resp_photo.status_code}")

print("Keszen van!")
