
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

def check_market_regime(symbol, timeframe=mt5.TIMEFRAME_H1):
    """
    3. Adaptív Piaci Rezsim Váltás:
    Megállapítja, hogy a piac trendel-e (ATR és ADX alapján) vagy oldalaz.
    Visszatérés: 'TRENDING', 'RANGING' vagy 'NO_TRADE'
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
    if rates is None:
        return "NO_TRADE"
    
    df = pd.DataFrame(rates)
    
    # Egyszerűsített Volatilitás (ATR) és Irányjelző szűrés
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(14).mean().iloc[-1]
    
    # Mozgóátlagok távolsága mint trend-erősség
    ma_fast = df['close'].ewm(span=10).mean().iloc[-1]
    ma_slow = df['close'].ewm(span=30).mean().iloc[-1]
    trend_strength = abs(ma_fast - ma_slow) / atr
    
    if trend_strength > 1.2:
        return "TRENDING"  # Mehet a trendkövető stratégia
    elif trend_strength < 0.5:
        return "RANGING"   # Oldalazás - vagy tiltás, vagy mean-reversion
    else:
        return "NO_TRADE"  # Bizonytalan piac, inkább maradjunk távol

def is_high_impact_news_time():
    """
    1. Automatikus Hír- és Eseményfigyelő (News Governor):
    Szimulált/API-alapú ellenőrzés: ha híridő van (pl. 15 percen belül), True-t ad vissza.
    (Itt élesben egy gazdasági naptár API-t, pl. Forex Factory / Investing.com JSON-t hívunk meg)
    """
    now = datetime.now()
    # Példa logika: ha szerda délután 2 óra körüli fontos adat van, vagy CPI/NFP időpont
    # Élesben ezt egy külső naptár adatsorral kötjük össze.
    return False # Alapértelmezésben nincsen tiltott hír

def get_dynamic_risk_multiplier():
    """
    2. Dinamikus Távolságkövető Drawdown Védelem (Equity Curve Guard):
    Ha a nap folyamán már nyereségben vagyunk, bebiztosítjuk; 
    ha közeledünk a napi limithez, csökkentjük a kockázatot.
    """
    account = mt5.account_info()
    if not account:
        return 1.0
        
    daily_pnl = account.equity - account.balance
    
    if daily_pnl < -200:  # Ha már van 200 EUR mínuszunk a napban
        return 0.5        # Felezzük a lot méretet, hogy ne bukjuk el a fiókot
    elif daily_pnl > 300: # Ha már van szép profitunk
        return 0.75       # Óvatosabb méretezés a nyereség megőrzésére
        
    return 1.0            # Normál kockázat

# --- FŐ KERESKEDÉSI CIKLUS ---
def master_trading_bot(symbol="EURUSD"):
    print(f"Kvantitatív Bot elindítva a {symbol} páron a 3 mestermodullal...")
    
    if not mt5.initialize():
        print("Hiba az MT5 csatlakozáskor.")
        return

    while True:
        # 1. Hírfigyelő ellenőrzés
        if is_high_impact_news_time():
            print("[HÍR VÉDELEM] Közel a fontos makrogazdasági hír. Kereskedés szüneteltetve.")
            time.sleep(300)
            continue
            
        # 2. Piaci Rezsim Ellenőrzés
        regime = check_market_regime(symbol)
        if regime != "TRENDING":
            print(f"[REZSIM VÁLTÁS] A piac jelenleg nem alkalmas trendkövetésre ({regime}). Várakozás...")
            time.sleep(60)
            continue
            
        # 3. Dinamikus Kockázat Szorzó lekérése
        risk_multiplier = get_dynamic_risk_multiplier()
        print(f"[KOCKÁZAT VÉDELEM] Aktív risk multiplier: {risk_multiplier}")
        
        # --- ITT JÖNNÉNEK A JELGENERÁLÁSI ÉS POZÍCIÓNYITÁSI LOGIKÁK ---
        # Ha a rezsim rendben van, nincs hír, és a drawdown is biztonságos, 
        # a bot a kiszámolt risk_multiplier-rel nyitja meg a pozíciót.
        
        time.sleep(30) # Ciklus szünet
