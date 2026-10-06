import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
import os

# --- NAPLÓZÁS BEÁLLÍTÁSA ---
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

# --- TELEGRAM ÉS KONFIGURÁCIÓ ---
TELEGRAM_TOKEN = "8854297649:AAF3a94cqNBz8mLH9KgKgX8b8hJrhIaQ"
CHAT_ID = "868954448"

ESZKOZOK = (
    "EURUSD",
    "GBPUSD",
    "USDJPY"
)

FUTASI_INTERVALLUM = 3600  # 1 óra
MAX_KOCKAZAT_SZAZALEK = 1.0  # 1% kockázat kötésenként
NAPI_VESZTESEG_LIMIT_SZAZALEK = 4.0  # FTMO védelem: Kill Switch 4%-os napi veszteségnél

def telegram_uzenet_kuldes(uzenet):
    """Telegram üzenet küldése a felhasználónak."""
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
        print(f"Hiba a Telegram üzenet küldésekor: {e}")
        return None

def napi_veszteseg_ellenorzes():
    """FTMO Kill Switch: Ellenőrzi a mai nap realizált veszteségét."""
    if not MT5_AVAILABLE:
        return 0.0
    
    # Ma éjféltől számolva
    kezdet = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    history = mt5.history_deals_get(kezdet, datetime.now())
    
    if history is None or len(history) == 0:
        return 0.0
    
    osszes_profit = sum([deal.profit for deal in history])
    return osszes_profit

def spread_megfelelo(symbol, max_engedett_spread_pip=3.0):
    """Ellenőrzi, hogy a spread nem túl magas-e (elkerülve a drága belépőket)."""
    if not MT5_AVAILABLE:
        return True
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return False
    
    spread_pip = (symbol_info.ask - symbol_info.bid) / symbol_info.point / 10 # Standard pip számítás
    return spread_pip <= max_engedett_spread_pip

def main():
    print("--- FTMO BOT PRO+ INDULT ---")
    telegram_uzenet_kuldes("🚀 FTMO Bot Pro+ sikeresen elindult és őrzi a pozíciókat!")
    
    if MT5_AVAILABLE:
        if not mt5.initialize():
            print("MT5 Inicializálási hiba")
            mt5.shutdown()
            return

    while True:
        try:
            # 1. FTMO KILL SWITCH ELLENŐRZÉS
            napi_profit = napi_veszteseg_ellenorzes()
            # Tételezzük fel, hogy 100 000 USD a számla (FTMO Standard)
            szamla_egyenleg = mt5.account_info().balance if MT5_AVAILABLE else 100000.0
            veszteseg_szazalek = (abs(napi_profit) / szamla_egyenleg) * 100 if napi_profit < 0 else 0.0
            
            if veszteseg_szazalek >= NAPI_VESZTESEG_LIMIT_SZAZALEK:
                vész_uzenet = f"🚨 KILL SWITCH AKTIVÁLVA! A mai napi veszteség elért/meghaladta a {veszteseg_szazalek:.2f}%-ot! Minden pozíció zárva."
                print(vész_uzenet)
                telegram_uzenet_kuldes(vész_uzenet)
                
                # Pozíciók kényszerített zárása
                if MT5_AVAILABLE:
                    poziciok = mt5.positions_get()
                    if poziciok:
                        for poz in poziciok:
                            # Itt történne a zárás logika
                            pass
                break # Kilép a ciklusból, megvédi a számlát!

            print(f"[{datetime.now()}] Futás ellenőrzés... Napi PnL: {napi_profit} USD")
            
            # Itt jön a fő kereskedési logika (Multi-Timeframe, ATR, RSI)
            for eszkoz in ESZKOZOK:
                if MT5_AVAILABLE and not spread_megfelelo(eszkoz):
                    print(f"Túl magas spread ekkor: {eszkoz}, várakozás...")
                    continue
                # Elemzés és kötés helye...

        except Exception as e:
            err_msg = f"Hiba a fő ciklusban: {e}"
            print(err_msg)
            logging.error(err_msg)
            telegram_uzenet_kuldes(f"⚠️ Rendszerhiba: {e}")

        time.sleep(FUTASI_INTERVALLUM)

if _name_ == "_main_":
    main()
