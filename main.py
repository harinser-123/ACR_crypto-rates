import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime
from tkinter import ttk, messagebox

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
def on_refresh():
    """Обновляет таблицу курсов и планирует следующее обновление."""
    # Блокируем кнопку во время загрузки (чтобы не нажимали много раз)
    btn_refresh.config(state="disabled")
    lbl_updated.config(text="Загрузка...")

    data = fetch_prices()

    if data is None:
        messagebox.showerror("Ошибка", "Не удалось получить курсы.\nПроверьте интернет или попробуйте позже.")
        lbl_updated.config(text="Обновлено: —")
    else:
        # Очищаем и заново заполняем таблицу
        for widget in frame_table.winfo_children():
            widget.destroy()

        # Заголовки таблицы
        ttk.Label(frame_table, text="Криптовалюта", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10)
        ttk.Label(frame_table, text="Цена (USD)", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="e", padx=10)

        row = 1
        for name, coin_id in CRYPTO_COINS:
            price = data.get(coin_id)
            if price is not None:
                # Форматируем цену: 2 знака после запятой, разделители тысяч
                price_str = f"{price:,.2f}"
                ttk.Label(frame_table, text=name).grid(row=row, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(frame_table, text=price_str).grid(row=row, column=1, sticky="e", padx=10, pady=5)
            else:
                ttk.Label(frame_table, text=name, foreground="gray").grid(row=row, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(frame_table, text="Нет данных", foreground="gray").grid(row=row, column=1, sticky="e", padx=10, pady=5)
            row += 1

        now = datetime.now().strftime("%H:%M:%S")
        lbl_updated.config(text=f"Обновлено: {now}")

    btn_refresh.config(state="normal")
    # Планируем следующий запуск в любом случае
    root.after(REFRESH_INTERVAL_MS, on_refresh)
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