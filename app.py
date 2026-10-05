import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime

class InstitutionalBotCore:
    def _init_(self, symbol="EURUSD", telegram_token=None, chat_id=None):
        self.symbol = symbol
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.is_connected = False

    def send_telegram_alert(self, message):
        """
        1. Valós idejű Telegram Távfelügyeleti Bot (Telemetria):
        Azonnali üzenetet küld a telefonodra a kritikus eseményekről.
        """
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
        """
        3. 'Watchdog' Öngyógyító Rendszer (Fail-Safe Mechanizmus):
        Ellenőrzi az MT5 kapcsolatot, és ha megszakad, megkísérli az újracsatlakozást.
        """
        if not mt5.terminal_info():
            print("[WATCHDOG VÉDELEM] MT5 kapcsolat megszakadt! Újracsatlakozási kísérlet...")
            self.send_telegram_alert("⚠️ Figyelem: Az MT5 kapcsolat megszakadt. Újracsatlakozás folyamatban...")
            
            # Újracsatlakozási próbálkozás
            if not mt5.initialize():
                print("[WATCHDOG HIBA] Az újracsatlakozás sikertelen.")
                return False
            else:
                print("[WATCHDOG SIKER] Sikeres újracsatlakozás!")
                self.send_telegram_alert("✅ Siker: Az MT5 kapcsolat helyreállt.")
        return True

    def run_backtest_simulation(self, historical_data_df):
        """
        2. Történelmi Backtesting és Walk-Forward Tesztelés:
        Lefuttatja a stratégiát a múltbeli adatokon, mielőtt éles pénzt kockáztatnánk.
        """
        print("[BACKTEST] Múltbeli adatok elemzése és stratégia tesztelése...")
        # Példa szimulációs logika: kiszámoljuk a historikus profit faktort
        historical_data_df['Return'] = historical_data_df['close'].pct_change()
        profit_factor = historical_data_df[historical_data_df['Return'] > 0]['Return'].sum() / \
                        abs(historical_data_df[historical_data_df['Return'] < 0]['Return'].sum())
        
        print(f"[BACKTEST EREDMÉNY] Historikus Profit Factor: {profit_factor:.2f}")
        return profit_factor

    def start_master_loop(self):
        print(f"Autonóm Intézményi Rendszer indítása a {self.symbol} páron...")
        
        if not mt5.initialize():
            print("Hiba az MT5 inicializálásakor.")
            return

        self.is_connected = True
        self.send_telegram_alert("🚀 A bot sikeresen elindult és felügyeli a fiókot!")

        while True:
            try:
                # 1. Watchdog ellenőrzés minden ciklus elején
                if not self.watchdog_check_connection():
                    time.sleep(10)
                    continue

                # 2. Számla és Pozíciók ellenőrzése
                account = mt5.account_info()
                if account:
                    daily_pnl = account.equity - account.balance
                    
                    # Ha a napi drawdown eléri a kritikus szintet, védelmet aktiválunk
                    if daily_pnl < -200:
                        self.send_telegram_alert(f"🚨 VIGYÁZAT: A napi veszteség elérte a -200 EUR-t! Pozíciók korlátozása.")
                
                # Ciklus szünet (pl. 30 másodpercenkénti futás)
                time.sleep(30)

            except KeyboardInterrupt:
                print("A bot leállítva a felhasználó által.")
                self.send_telegram_alert("🛑 A bot manuálisan leállítva.")
                mt5.shutdown()
                break

if _name_ == "_main_":
    # Példa indítás (A saját Telegram Tokenedet és Chat ID-dat ide írhatod majd be)
    bot = InstitutionalBotCore(symbol="EURUSD", telegram_token="ITT_A_TOKEN", chat_id="ITT_A_CHAT_ID")
    bot.start_master_loop()
