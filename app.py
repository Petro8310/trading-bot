
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime

class InstitutionalRiskGovernor:
    def _init_(self, symbol="EURUSD"):
        self.symbol = symbol

    def check_market_regime(self):
        """
        1. Multi-Timeframe ATR + ADX Rezsim-Szűrő:
        Megállapítja, hogy a piac trendel-e, vagy csapkodó/oldalazó.
        Visszatérés: True, ha engedélyezett a kereskedés; False, ha tiltott.
        """
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < 50:
            return False
        
        df = pd.DataFrame(rates)
        
        # ATR számítás (Volatilitás)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # Mozgóátlagok távolsága mint trend-erősség
        ma_fast = df['close'].ewm(span=10).mean().iloc[-1]
        ma_slow = df['close'].ewm(span=30).mean().iloc[-1]
        trend_strength = abs(ma_fast - ma_slow) / atr
        
        # Ha a trend erősség megfelelő, engedélyezzük a kereskedést
        if trend_strength > 1.1:
            return True  # Trendelő piac (Kereskedhetünk)
        return False     # Oldalazó/bizonytalan piac (Tiltás)

    def is_high_impact_news_time(self):
        """
        2. Automatikus Hírfigyelő (News Governor):
        Éles környezetben itt hívható le a gazdasági naptár API (pl. Forex Factory).
        Jelenleg biztonsági szűrésként logikai alapú.
        """
        # Példa: Ha fontos hír időpontja van, True-t ad vissza
        return False 

    def get_equity_curve_multiplier(self):
        """
        3. Dinamikus Equity Curve Guard (Tőkeörv-védelem):
        Visszaad egy szorzót (0.5 - 1.0), ami a nap közbeni profit/veszteség 
        függvényében skálázza a kockázatot.
        """
        account = mt5.account_info()
        if not account:
            return 1.0
            
        daily_pnl = account.equity - account.balance
        
        if daily_pnl < -150:  # Ha közeledünk a napi kockázati zónához
            return 0.5        # Felezzük a lot méretet
        elif daily_pnl > 250: # Ha már van szép napi profitunk
            return 0.75       # Óvatosabb méretezés a nyereség megőrzésére
            
        return 1.0            # Normál kockázat

# --- FŐ VEZÉRLŐ HURKOLÁS ---
def run_institutional_bot(symbol="EURUSD"):
    print(f"Intézményi Kvantitatív Bot indítása a következő páron: {symbol}...")
    
    if not mt5.initialize():
        print("Hiba az MT5 inicializálásakor:", mt5.last_error())
        return

    governor = InstitutionalRiskGovernor(symbol)

    while True:
        try:
            # 1. Hírfigyelő ellenőrzés
            if governor.is_high_impact_news_time():
                print("[HÍR VÉDELEM] Fontos makrogazdasági hír közeleg. Kereskedés szüneteltetve.")
                time.sleep(300)
                continue
                
            # 2. Piaci Rezsim Ellenőrzés
            if not governor.check_market_regime():
                print("[REZSIM SZŰRŐ] A piac jelenleg oldalazó vagy bizonytalan. Várakozás...")
                time.sleep(60)
                continue
                
            # 3. Dinamikus Kockázat Szorzó lekérése
            risk_multiplier = governor.get_equity_curve_multiplier()
            print(f"[TŐKE VÉDELEM] Aktív kockázati szorzó: {risk_multiplier}")
            
            # Itt futna be a stratégia jelgenerálása és a pozíciónyitás 
            # a kiszámolt risk_multiplier figyelembevételével.
            print("[STATUS] A rendszer stabil, piaci feltételek ideálisak a kötéshez.")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("Bot manuálisan leállítva.")
            mt5.shutdown()
            break

if _name_ == "_main_":
    run_institutional_bot("EURUSD")
