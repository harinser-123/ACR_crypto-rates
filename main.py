import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime

# Список монет для отображения (id из CoinPaprika)
CRYPTO_COINS = [
    ("Bitcoin", "btc-bitcoin"),
    ("Ethereum", "eth-ethereum"),
    ("Solana", "sol-solana"),
    ("Cardano", "ada-cardano"),
    ("Dogecoin", "doge-dogecoin"),
]

API_URL = "https://api.coinpaprika.com/v1/tickers"
REFRESH_INTERVAL_MS = 120_000  # автообновление раз в 2 минуты


def fetch_prices():
    """Получает курсы криптовалют из API CoinPaprika.

    Возвращает словарь {id монеты: цена в USD}
    или None, если запрос не удался.
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        tickers = response.json()
        # Превращаем список тикеров в словарь {id: цена}
        return {t["id"]: t["quotes"]["USD"]["price"] for t in tickers}
    except Exception as e:
        print("Ошибка запроса:", e)
        return None

# Каркас приложения. Логика API будет добавлена на следующих этапах.

root = tk.Tk()
root.title("Курсы криптовалют")
root.geometry("450x400")

# Заголовок
lbl_title = ttk.Label(root, text="Курсы криптовалют", font=("Arial", 16, "bold"))
lbl_title.pack(pady=20)

# Место под будущую таблицу
frame_table = ttk.Frame(root)
frame_table.pack(fill="both", expand=True, padx=10, pady=5)

# Кнопка обновления (пока без функционала)
btn_refresh = ttk.Button(root, text="Обновить курсы")
btn_refresh.pack(pady=10)

# Статус обновления
lbl_updated = ttk.Label(root, text="Обновлено: —", foreground="gray")
lbl_updated.pack(side="bottom", pady=10)

root.mainloop()