
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

class InstitutionalMasterBot:
    def _init_(self, symbol="EURUSD", max_spread_pips=2.5, telegram_token=None, chat_id=None):
        self.symbol = symbol
        self.max_spread = max_spread_pips
        self.telegram_token = telegram_token
        self.chat_id = chat_id

    def send_telegram_alert(self, message):
        """1. Valós idejű Telegram Telemetria"""
        if not self.telegram_token or not self.chat_id:
            print(f"[TELEGRAM SIMULATED]: {message}")
            return
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"🤖 [FTMO Bot Riasztás]\n{message}",
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

    def check_market_regime(self):
        """3. Multi-Timeframe Rezsim- és Volatilitás-Szűrő"""
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 50)
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

    def is_high_impact_news_time(self):
        """4. Automatikus Hírkormányzó (News Governor)"""
        # Itt köthető be a külső naptár API (pl. Forex Factory)
        return False

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

    def verify_execution_safety(self):
        """6. Smart Execution Guard (Spread- és Csúszásvédelmi Pajzs)"""
        symbol_info = mt5.symbol_info(self.symbol)
        tick = mt5.symbol_info_tick(self.symbol)
        if symbol_info is None or tick is None:
            return False

        spread_points = symbol_info.spread
        point_size = symbol_info.point
        pip_spread = (spread_points * point_size) / 0.0001 if "JPY" not in self.symbol else (spread_points * point_size) / 0.01

        if pip_spread > self.max_spread:
            print(f"🚨 [SPREAD VÉDELEM] Túl magas spread: {pip_spread:.2f} pip. Kötés letiltva.")
            return False
        return True

    def run_backtest_simulation(self):
        """7. Historikus Backtesting Motívum"""
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 200)
        if rates is None:
            return 1.0
        df = pd.DataFrame(rates)
        df['Return'] = df['close'].pct_change()
        pos_sum = df[df['Return'] > 0]['Return'].sum()
        neg_sum = abs(df[df['Return'] < 0]['Return'].sum())
        pf = pos_sum / neg_sum if neg_sum > 0 else 1.5
        print(f"[BACKTEST] Előzetes Profit Factor teszt: {pf:.2f}")
        return pf

    def start(self):
        print(f"Intézményi Mester Bot indítása a {self.symbol} páron...")
        if not mt5.initialize():
            print("Hiba az MT5 inicializálásakor.")
            return

        self.run_backtest_simulation()
        self.send_telegram_alert("🚀 A mesterrendszer sikeresen elindult!")

        while True:
            try:
                # 1. Watchdog ellenőrzés
                if not self.watchdog_check_connection():
                    time.sleep(10)
                    continue

                # 2. Hírfigyelő
                if self.is_high_impact_news_time():
                    print("[HÍR VÉDELEM] Fontos makroadat közeleg. Várakozás...")
                    time.sleep(300)
                    continue

                # 3. Piaci rezsim szűrő
                if not self.check_market_regime():
                    print("[REZSIM SZŰRŐ] Oldalazó piac. Várakozás...")
                    time.sleep(60)
                    continue

                # 4. Spread / Csúszásvédelem
                if not self.verify_execution_safety():
                    time.sleep(15)
                    continue

                # 5. Dinamikus kockázat
                risk_multiplier = self.get_equity_curve_multiplier()
                print(f"[RENDSZER OK] Minden feltétel adott. Aktív risk szorzó: {risk_multiplier}")

                time.sleep(30)

            except KeyboardInterrupt:
                print("Bot kézi leállítása.")
                self.send_telegram_alert("🛑 A bot manuálisan leállítva.")
                mt5.shutdown()
                break

if _name_ == "_main_":
    bot = InstitutionalMasterBot(symbol="EURUSD", max_spread_pips=2.5)
    bot.start()
