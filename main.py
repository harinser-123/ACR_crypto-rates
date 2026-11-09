import tkinter as tk
from tkinter import ttk, messagebox
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

    Делает отдельный запрос для каждой монеты из списка.
    Возвращает словарь {id монеты: цена в USD}
    или None, если не удалось получить ни одного ответа.
    """
    prices = {}
    for _, coin_id in CRYPTO_COINS:
        try:
            response = requests.get(f"{API_URL}/{coin_id}", timeout=30)
            response.raise_for_status()
            t = response.json()
            prices[t["id"]] = t["quotes"]["USD"]["price"]
        except Exception as e:
            print(f"Ошибка запроса ({coin_id}):", e)
    return prices if prices else None

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

btn_refresh = ttk.Button(root, text="Обновить курсы", command=on_refresh)
btn_refresh.pack(pady=10)

# Статус обновления
lbl_updated = ttk.Label(root, text="Обновлено: —", foreground="gray")
lbl_updated.pack(side="bottom", pady=10)
# Первое обновление сразу при запуске
root.after(0, on_refresh)

root.mainloop()