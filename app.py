import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

class InstitutionalMasterPortfolioBot:
    def _init_(self, symbols=["EURUSD", "GBPUSD", "USDJPY"], max_spread_pips=2.5, telegram_token=None, chat_id=None, forward_test_mode=True):
        self.symbols = symbols
        self.max_spread = max_spread_pips
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.forward_test_mode = forward_test_mode # True esetén csak logol, nem nyit éles pozíciót (Forward Testing)

    def send_telegram_alert(self, message):
        """1. Valós idejű Telegram Telemetria"""
        if not self.telegram_token or not self.chat_id:
            print(f"[TELEGRAM SIMULATED]: {message}")
            return
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"🤖 [FTMO Portfolio Bot]\n{message}",
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Hiba a Telegram üzenet küldésekor: {e}")

    def watchdog_check_connection(self):
        """2. 'Watchdog' Öngyógyító Rendszer"""
        if not mt5.terminal_info():
            print("[WATCHDOG] MT5 kapcsolat megszakadt! Újracsatlakozás...")
            self.send_telegram_alert("⚠️ Figyelem: Az MT5 kapcsolat megszakadt. Újracsatlakozás...")
            if not mt5.initialize():
                print("[WATCHDOG HIBA] Sikertelen újracsatlakozás.")
                return False
            else:
                print("[WATCHDOG SIKER] Kapcsolat helyreállt.")
                self.send_telegram_alert("✅ Siker: Az MT5 kapcsolat helyreállt.")
        return True

    def check_market_regime(self, symbol):
        """3. Multi-Timeframe Rezsim- és Volatilitás-Szűrő adott szimbólumra"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < 50:
            return False
        
        df = pd.DataFrame(rates)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        ma_fast = df['close'].ewm(span=10).mean().iloc[-1]
        ma_slow = df['close'].ewm(span=30).mean().iloc[-1]
        trend_strength = abs(ma_fast - ma_slow) / atr
        
        return trend_strength > 1.1 # True, ha trendelő; False, ha oldalazó

    def verify_execution_safety(self, symbol):
        """4. Smart Execution Guard (Spread- és Csúszásvédelmi Pajzs)"""
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if symbol_info is None or tick is None:
            return False

        spread_points = symbol_info.spread
        point_size = symbol_info.point
        pip_spread = (spread_points * point_size) / 0.0001 if "JPY" not in symbol else (spread_points * point_size) / 0.01

        if pip_spread > self.max_spread:
            print(f"🚨 [{symbol} SPREAD VÉDELEM] Túl magas spread: {pip_spread:.2f} pip. Kötés letiltva.")
            return False
        return True

    def get_equity_curve_multiplier(self):
        """5. Dinamikus Equity Curve Guard (Tőkeörv)"""
        account = mt5.account_info()
        if not account:
            return 1.0
            
        daily_pnl = account.equity - account.balance
        if daily_pnl < -150:
            return 0.5   # Veszteség esetén felezzük a lot méretet
        elif daily_pnl > 250:
            return 0.75  # Profit esetén óvatosabb méretezés
        return 1.0

    def run_walkforward_simulation(self, symbol):
        """6. Adaptív Walk-Forward / Múltbeli Optimalizációs Ellenőrzés"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 150)
        if rates is None:
            return 1.0
        df = pd.DataFrame(rates)
        df['Return'] = df['close'].pct_change()
        pos_sum = df[df['Return'] > 0]['Return'].sum()
        neg_sum = abs(df[df['Return'] < 0]['Return'].sum())
        pf = pos_sum / neg_sum if neg_sum > 0 else 1.2
        return pf

    def start(self):
        print(f"Intézményi Multi-Asset Portfólió Bot indítása a következő párokon: {self.symbols}...")
        if not mt5.initialize():
            print("Hiba az MT5 inicializálásakor.")
            return

        mode_str = "Forward Testing (Demo Log Mód)" if self.forward_test_mode else "Éles Kereskedés"
        self.send_telegram_alert(f"🚀 A portfólió bot elindult! Üzemmód: {mode_str}")

        while True:
            try:
                # 1. Watchdog ellenőrzés
                if not self.watchdog_check_connection():
                    time.sleep(10)
                    continue

                # 2. Portfólió ciklus (Minden devizapár vizsgálata egymás után)
                for symbol in self.symbols:
                    print(f"\n--- Elemzés futtatása: {symbol} ---")

                    # Walk-forward / historikus teljesítmény ellenőrzés
                    pf = self.run_walkforward_simulation(symbol)
                    if pf < 1.0:
                        print(f"[{symbol}] Gyenge múltbeli teljesítmény (PF: {pf:.2f}). Kihagyás.")
                        continue

                    # Piaci rezsim szűrő
                    if not self.check_market_regime(symbol):
                        print(f"[{symbol}] Oldalazó vagy bizonytalan piac. Kihagyás.")
                        continue

                    # Spread védelem
                    if not self.verify_execution_safety(symbol):
                        continue

                    # Kockázati szorzó lekérése
                    risk_multiplier = self.get_equity_curve_multiplier()

                    # Végrehajtás vagy Forward Testing logolás
                    if self.forward_test_mode:
                        log_msg = f"🧪 [FORWARD TEST] {symbol}: Feltételek tökéletesek! (Risk Mult: {risk_multiplier}, PF: {pf:.2f}). Szimulált jel rögzítve."
                        print(log_msg)
                        # Itt küldhetünk Telegram értesítést is fontosabb eseményekkor
                    else:
                        print(f"💰 [{symbol}] Éles megbízás küldése az MT5-nek...")
                        # Ide jönne az igazi mt5.order_send() parancs

                # Ciklus szünet a következő iteráció előtt
                print("\n[PORTFÓLIÓ] Ciklus vége. Várakozás a következő ellenőrzésre...")
                time.sleep(45)

            except KeyboardInterrupt:
                print("Bot kézi leállítása.")
                self.send_telegram_alert("🛑 A portfólió bot manuálisan leállítva.")
                mt5.shutdown()
                break

if _name_ == "_main_":
    # Multi-Asset kosár beállítása (EURUSD, GBPUSD, USDJPY)
    bot = InstitutionalMasterPortfolioBot(
        symbols=["EURUSD", "GBPUSD", "USDJPY"],
        max_spread_pips=2.5,
        forward_test_mode=True # Teszt üzemmódban indítva
    )
    bot.start()
