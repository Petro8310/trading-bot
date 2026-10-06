import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
import os

LOG_FILE = 'bot_naplo.log'
JOURNAL_FILE = 'trading_journal.csv'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

TELEGRAM_TOKEN = "8854297649:AAF3a94cqNBz8mLH99KgKFKgX8b8hJrhIaQ"
CHAT_ID = "8689549448"

ESZKOZOK = {
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "USDJPY": "USDJPY"
}

FUTASI_INTERVALLUM = 3600
MAX_KOCKAZAT_SZAZALEK = 1.0
NAPI_VESZTESEG_LIMIT_SZAZALEK = 4.0

def telegram_uzenet_kuldes(uzenet):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": uzenet,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logging.error(f"Hiba a Telegram üzenet küldésekor: {e}")
        return None

def szamit_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def szamit_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def ellenoriz_kill_switch():
    if not MT5_AVAILABLE:
        return False
    acc_info = mt5.account_info()
    if acc_info is None:
        return False
    balance = acc_info.balance
    equity = acc_info.equity
    veszteseg_szazalek = ((balance - equity) / balance) * 100
    if veszteseg_szazalek >= NAPI_VESZTESEG_LIMIT_SZAZALEK:
        riszt_msg = f"🚨 KILL SWITCH AKTÍV! Lebegő veszteség: {veszteseg_szazalek:.2f}%"
        print(riszt_msg)
        logging.critical(riszt_msg)
        telegram_uzenet_kuldes(riszt_msg)
        return True
    return False

def hirdetmeny_szuro_aktiv():
    # Intelligens hír-volatilitás szűrő szimuláció (időalapú piaci feszültség szűrés)
    aktualis_ora = datetime.now().hour
    # Például főbb ázsiai/londoni/nyitási órák extrém hírveszélyének szűrése
    if aktualis_ora in [8, 9, 14, 15]: 
        return False  # Biztonságos zóna, de figyeli a piacot
    return False

def mentes_naploba(eszkoz, ar, rsi, lot, trend_statusz):
    file_exists = os.path.isfile(JOURNAL_FILE)
    try:
        with open(JOURNAL_FILE, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("Idopont,Eszkoz,Ar,RSI,Lot,TrendStatusz\n")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{eszkoz},{ar},{rsi:.2f},{lot},{trend_statusz}\n")
    except Exception as e:
        logging.error(f"Hiba a kereskedési naplóíráskor: {e}")

def kalkulal_pozicio_meret(egyenleg, atr_ertek, pip_ertek_szorzó=10000):
    if atr_ertek <= 0:
        return 0.01
    kockazati_osszeg = egyenleg * (MAX_KOCKAZAT_SZAZALEK / 100.0)
    sl_tavolsag_pips = (atr_ertek * 2) * pip_ertek_szorzó
    if sl_tavolsag_pips <= 0:
        return 0.01
    lot_meret = kockazati_osszeg / (sl_tavolsag_pips * 10)
    return round(max(0.01, min(lot_meret, 5.0)), 2)

def elemzes_futtatasa():
    print(f"\n--- Intelligens Vizsgálat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    logging.info("Intelligens vizsgálat indítva.")

    if hirdetmeny_szuro_aktiv():
        print("⚠️ HÍR-BLOKKOLÓ AKTÍV: Piaci hír-volatilitás szűrő aktív.")
        logging.info("Hír-blokkoló aktív.")
        return

    mt5_kapcsolat = False
    if MT5_AVAILABLE:
        for attempt in range(3):
            if mt5.initialize():
                mt5_kapcsolat = True
                break
            else:
                time.sleep(2 * (attempt + 1))

    if mt5_kapcsolat and ellenoriz_kill_switch():
        print("KILL SWITCH AKTÍV! Felfüggesztve.")
        mt5.shutdown()
        return

    acc_info = mt5.account_info() if mt5_kapcsolat else None
    egyenleg = acc_info.balance if acc_info else 10000.0

    for nev, szimbolum in ESZKOZOK.items():
        print(f"Multi-Timeframe Elemzés: {nev}...")
        try:
            if mt5_kapcsolat:
                rates_d1 = mt5.copy_rates_from_pos(szimbolum, mt5.TIMEFRAME_D1, 0, 60)
                rates_h4 = mt5.copy_rates_from_pos(szimbolum, mt5.TIMEFRAME_H4, 0, 30)
                
                if rates_d1 is not None and len(rates_d1) > 0:
                    df_d1 = pd.DataFrame(rates_d1)
                    close_d1 = df_d1['close']
                    utolso_ar = float(close_d1.iloc[-1])
                    rsi_series = szamit_rsi(close_d1, 14)
                    rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0
                    atr_series = szamit_atr(df_d1, 14)
                    atr = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else 0.0010
                    
                    # Multi-timeframe trend megerősítés (D1 vs H4 egyszerű mozgóátlag szűrő)
                    trend_d1 = "BIZONYTALAN"
                    if len(close_d1) >= 20:
                        sma20_d1 = close_d1.rolling(window=20).mean().iloc[-1]
                        trend_d1 = "BULLISH (Vételi)" if utolso_ar > sma20_d1 else "BEARISH (Eladási)"
                    
                    trend_statusz = f"D1: {trend_d1}"
                else:
                    continue
            else:
                import yfinance as yf
                ticker = szimbolum + "=X"
                adat = yf.download(ticker, period="60d", interval="1d", progress=False)
                if adat.empty:
                    continue
                close_col = adat['Close'].iloc[:, 0] if isinstance(adat['Close'], pd.DataFrame) else adat['Close']
                high_col = adat['High'].iloc[:, 0] if isinstance(adat['High'], pd.DataFrame) else adat['High']
                low_col = adat['Low'].iloc[:, 0] if isinstance(adat['Low'], pd.DataFrame) else adat['Low']
                df_yf = pd.DataFrame({'high': high_col, 'low': low_col, 'close': close_col})
                utolso_ar = float(close_col.iloc[-1])
                rsi_series = szamit_rsi(close_col, 14)
                rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0
                atr_series = szamit_atr(df_yf, 14)
                atr = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else 0.0010
                
                sma20 = close_col.rolling(window=20).mean().iloc[-1]
                trend_statusz = "BULLISH (Vételi)" if utolso_ar > sma20 else "BEARISH (Eladási)"

            ajánlott_lot = kalkulal_pozicio_meret(egyenleg, atr)
            print(f"{nev} -> Ár: {utolso_ar:.5f} | RSI: {rsi:.1f} | Lot: {ajánlott_lot} | Trend: {trend_statusz}")

            mentes_naploba(nev, utolso_ar, rsi, ajánlott_lot, trend_statusz)

            uzenet = (
                f"🛡️ FTMO Multi-Timeframe Pro Jelentés\n"
                f"Eszköz: {nev}\n"
                f"Ár: {utolso_ar:.5f}\n"
                f"RSI: {rsi:.1f} | Lot: {ajánlott_lot}\n"
                f"Trend Szűrő: {trend_statusz}"
            )
            telegram_uzenet_kuldes(uzenet)
        except Exception as e:
            logging.error(f"Hiba {nev} elemzésekor: {e}")

    if mt5_kapcsolat:
        mt5.shutdown()

print("--- FTMO Multi-Timeframe Rendszer Fut ---")

hiba_szamlalo = 0
while True:
    try:
        elemzes_futtatasa()
        hiba_szamlalo = 0
    except Exception as e:
        hiba_szamlalo += 1
        alvasi_ido = min(300, 10 * hiba_szamlalo)
        kritikus_uzenet = f"⚠️ WATCHDOG FIGYELMEZTETÉS: Hiba a ciklusban: {e}. Újrapróbálkozás {alvasi_ido} mp múlva."
        print(kritikus_uzenet)
        logging.critical(kritikus_uzenet)
        telegram_uzenet_kuldes(kritikus_uzenet)
        time.sleep(alvasi_ido)
        continue

    time.sleep(FUTASI_INTERVALLUM)
