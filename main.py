import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import requests

# --- НАСТРОЙКИ ---
COINS = ["BTC", "ETH", "SOL", "ADA", "DOGE"]

PROVIDERS = [
    {"name": "Bybit", "url": "https://api.bybit.com/v5/market/tickers"},
    {"name": "MEXC", "url": "https://api.mexc.com/api/v3/ticker/price"},
    {"name": "KuCoin", "url": "https://api.kucoin.com/api/v1/market/orderbook/level1"},
]

REFRESH_INTERVAL_MS = 120_000  # автообновление раз в 2 минуты

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

POPULAR_COINS = {
    "Bitcoin": "BTC", "Ethereum": "ETH", "Tether": "USDT", "BNB": "BNB",
    "Solana": "SOL", "Ripple": "XRP", "Cardano": "ADA", "Dogecoin": "DOGE",
    "TRON": "TRX", "Toncoin": "TON", "Avalanche": "AVAX", "Polkadot": "DOT",
    "Chainlink": "LINK", "Polygon": "POL", "Litecoin": "LTC", "Shiba Inu": "SHIB",
    "Bitcoin Cash": "BCH", "Uniswap": "UNI", "Cosmos": "ATOM", "Stellar": "XLM",
    "Ethereum Classic": "ETC", "Filecoin": "FIL", "Arbitrum": "ARB", "Optimism": "OP",
    "Aptos": "APT", "Sui": "SUI", "NEAR Protocol": "NEAR", "Injective": "INJ",
    "Aave": "AAVE", "Algorand": "ALGO", "VeChain": "VET", "Internet Computer": "ICP",
    "Hedera": "HBAR", "Pepe": "PEPE", "FLOKI": "FLOKI", "Bonk": "BONK",
    "USD Coin": "USDC", "Dai": "DAI", "Wrapped Bitcoin": "WBTC", "Render": "RENDER",
    "Artificial Superintelligence Alliance": "FET", "Celestia": "TIA", "Jupiter": "JUP",
    "Pyth Network": "PYTH", "THORChain": "RUNE", "The Graph": "GRT", "The Sandbox": "SAND",
    "Decentraland": "MANA", "Gala": "GALA", "Chiliz": "CHZ", "Curve DAO": "CRV",
    "Maker": "MKR", "Lido DAO": "LDO", "Stacks": "STX", "Sei": "SEI", "Kaspa": "KAS",
}

last_error = ""
rub_rate = 1.0  # по умолчанию 1, если курс не пришёл


def fetch_one_price(provider, symbol):
    """Получает цену одной пары у конкретной биржи."""
    if provider["name"] == "Bybit":
        params = {"category": "spot", "symbol": f"{symbol}USDT"}
    elif provider["name"] == "MEXC":
        params = {"symbol": f"{symbol}USDT"}
    else:  # KuCoin
        params = {"symbol": f"{symbol}-USDT"}

    try:
        response = requests.get(
            provider["url"],
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()

        if provider["name"] == "Bybit":
            result = body.get("result", {})
            items = result.get("list", [])
            if body.get("retCode") != 0 or not items:
                return None
            return float(items[0]["lastPrice"])
        elif provider["name"] == "MEXC":
            return float(body["price"])
        else:  # KuCoin
            data = body.get("data")
            if not data or not data.get("price"):
                return None
            return float(data["price"])
    except Exception:
        return None


def fetch_rub_rate():
    """Отдельный запрос за курсом USD/RUB у Bybit."""
    global rub_rate
    try:
        params = {"category": "spot", "symbol": "USDTRUB"}
        response = requests.get(
            "https://api.bybit.com/v5/market/tickers",
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()
        result = body.get("result", {})
        items = result.get("list", [])
        if body.get("retCode") == 0 and items:
            rate = float(items[0]["lastPrice"])
            rub_rate = rate
            return rate
    except Exception as e:
        print("Ошибка получения курса RUB:", e)
    return None


def fetch_prices():
    """Получает курсы всех монет списка точечными запросами."""
    global last_error
    last_error = ""
    errors = []

    for provider in PROVIDERS:
        prices = {}
        for symbol in COINS:
            price = fetch_one_price(provider, symbol)
            if price is not None:
                prices[symbol] = price
        if prices:
            return prices

    last_error = "\n".join(errors) if errors else "неизвестная ошибка"
    return None


def on_refresh():
    """Обновляет таблицу курсов, добавляет расчёт в рублях и планирует следующее обновление."""
    btn_refresh.config(state="disabled")
    lbl_updated.config(text="Загрузка...")

    # Сначала пробуем получить курс рубля — это отдельный независимый запрос
    rub_ok = fetch_rub_rate() is not None

    data = fetch_prices()

    if data is None:
        messagebox.showerror(
            "Ошибка",
            f"Не удалось получить курсы.\nПодробности:\n{last_error}",
        )
        lbl_updated.config(text="Обновлено: —")
    else:
        # Очищаем таблицу
        for widget in frame_table.winfo_children():
            widget.destroy()

        # Заголовки: 3 колонки (Криптовалюта, Цена USD, Цена RUB)
        ttk.Label(frame_table, text="Криптовалюта", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10)
        ttk.Label(frame_table, text="Цена (USD)", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="e", padx=10)
        ttk.Label(frame_table, text="Цена (RUB)", font=("Arial", 12, "bold")).grid(row=0, column=2, sticky="e", padx=10)

        row = 1
        for symbol in COINS:
            name = get_coin_name(symbol)
            price_usd = data.get(symbol)

            if price_usd is not None:
                price_str_usd = f"{price_usd:,.2f}"
                price_rub = price_usd * rub_rate
                # Форматируем рубли: разделители тысяч, 2 знака, символ ₽
                price_str_rub = f"{price_rub:,.2f} ₽"

                ttk.Label(frame_table, text=name).grid(row=row, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(frame_table, text=price_str_usd).grid(row=row, column=1, sticky="e", padx=10, pady=5)
                ttk.Label(frame_table, text=price_str_rub).grid(row=row, column=2, sticky="e", padx=10, pady=5)
            else:
                ttk.Label(frame_table, text=name, foreground="gray").grid(row=row, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(frame_table, text="-", foreground="gray").grid(row=row, column=1, sticky="e", padx=10, pady=5)
                ttk.Label(frame_table, text="-", foreground="gray").grid(row=row, column=2, sticky="e", padx=10, pady=5)
            row += 1

        now = datetime.now().strftime("%H:%M:%S")
        rate_text = f"{rub_rate:,.2f}" if rub_ok else "курс не получен"
        lbl_updated.config(text=f"Обновлено: {now} | USD/RUB = {rate_text}")

    btn_refresh.config(state="normal")
    root.after(REFRESH_INTERVAL_MS, on_refresh)


def get_coin_name(symbol):
    for name, sym in POPULAR_COINS.items():
        if sym == symbol:
            return name
    return symbol


# --- Логика списков (два столбца) ---

def refresh_current_list():
    lb_current.delete(0, tk.END)
    for symbol in COINS:
        name = get_coin_name(symbol)
        lb_current.insert(tk.END, f"{name} ({symbol})")


def refresh_catalog():
    lb_catalog.delete(0, tk.END)
    sorted_coins = sorted(POPULAR_COINS.items(), key=lambda x: x[0])
    for name, symbol in sorted_coins:
        lb_catalog.insert(tk.END, f"{name} ({symbol})")


def on_add_from_catalog():
    selection = lb_catalog.curselection()
    if not selection:
        messagebox.showwarning("Внимание", "Выберите монету в каталоге справа.")
        return

    text = lb_catalog.get(selection[0])
    symbol = text.split("(")[1].split(")")[0]

    if symbol in COINS:
        messagebox.showinfo("Инфо", "Эта монета уже есть в таблице.")
        return

    COINS.append(symbol)
    refresh_current_list()
    on_refresh()


def on_remove_coin():
    selection = lb_current.curselection()
    if not selection:
        messagebox.showwarning("Внимание", "Сначала выберите монету в списке «Текущие».")
        return
    index = selection[0]
    COINS.pop(index)
    refresh_current_list()
    on_refresh()


# --- ИНТЕРФЕЙС (ПОЛНЫЙ GRID + АДАПТИВНОСТЬ + РУБЛИ) ---
root = tk.Tk()
root.title("ACR_crypto-rates")
root.geometry("1120x600")  # Чуть шире для третьего столбца

# Настраиваем главный контейнер: 2 столбца (левая часть, правая часть)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# Левая часть: таблица и кнопки
frame_main = ttk.Frame(root)
frame_main.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)

frame_main.columnconfigure(0, weight=1)
frame_main.rowconfigure(1, weight=1)

ttk.Label(frame_main, text="Курсы криптовалют", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(0, 18))

frame_table = ttk.Frame(frame_main)
frame_table.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
# Три колонки таблицы: монета, USD, RUB
frame_table.columnconfigure(0, weight=1)
frame_table.columnconfigure(1, weight=0)
frame_table.columnconfigure(2, weight=0)

btn_refresh = ttk.Button(frame_main, text="Обновить курсы", command=on_refresh)
btn_refresh.grid(row=2, column=0, pady=10)

lbl_updated = ttk.Label(frame_main, text="Обновлено: —", foreground="gray")
lbl_updated.grid(row=3, column=0, sticky="s", pady=12)

# Правая часть: два столбца рядом (Текущие и Каталог)
frame_panel = ttk.Frame(root)
frame_panel.grid(row=0, column=1, sticky="nsew", padx=12, pady=8)

frame_panel.columnconfigure(0, weight=1)
frame_panel.columnconfigure(1, weight=1)
frame_panel.rowconfigure(0, weight=1)

# Левый столбец панели: Текущие монеты
frame_current = ttk.LabelFrame(frame_panel, text="Текущие монеты", padding=6)
frame_current.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
frame_current.columnconfigure(0, weight=1)
frame_current.rowconfigure(1, weight=1)

lb_current = tk.Listbox(frame_current, height=14, width=26)
lb_current.grid(row=1, column=0, sticky="nsew")

btn_remove = ttk.Button(frame_current, text="Удалить выбранную", command=on_remove_coin)
btn_remove.grid(row=2, column=0, sticky="ew", pady=(8, 0))

# Правый столбец панели: Каталог монет
frame_catalog = ttk.LabelFrame(frame_panel, text="Каталог монет", padding=6)
frame_catalog.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)
frame_catalog.columnconfigure(0, weight=1)
frame_catalog.rowconfigure(1, weight=1)

lb_catalog = tk.Listbox(frame_catalog, height=14, width=26)
lb_catalog.grid(row=1, column=0, sticky="nsew")

btn_add = ttk.Button(frame_catalog, text="Добавить выбранную", command=on_add_from_catalog)
btn_add.grid(row=2, column=0, sticky="ew", pady=(8, 0))

# Инициализация списков
refresh_current_list()
refresh_catalog()

# Первое обновление сразу при запуске
root.after(0, on_refresh)
root.mainloop()