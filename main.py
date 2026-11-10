
# ACR_crypto-rates — учебный проект мониторинга курсов криптовалют с конвертацией в RUB
# API: Bybit, MEXC, KuCoin (криптовалюты); kurs-rublya.ru (курс USD/RUB)
# Особенности: многоисточниковость, fallback-курс, неблокирующее обновление (threading)
# Автор: [ТВОЁ ИМЯ]
# Платформа: Python + Tkinter

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import requests
import threading

# --- НАСТРОЙКИ ---
COINS = ["BTC", "ETH", "SOL", "ADA", "DOGE"]

PROVIDERS = [
    {"name": "Bybit", "url": "https://api.bybit.com/v5/market/tickers"},
    {"name": "MEXC", "url": "https://api.mexc.com/api/v3/ticker/24hr"},
    {"name": "KuCoin", "url": "https://api.kucoin.com/api/v1/market/stats"},
]

REFRESH_INTERVAL_MS = 120_000
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

COLOR_GROWTH = "#15803d"
COLOR_FALL = "#dc2626"

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

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
last_error = ""
usd_rub_rate = 92.5
use_fallback_rate = True


# ==============================================================================
# ФУНКЦИЯ ПОЛУЧЕНИЯ КУРСА РУБЛЯ
# ==============================================================================
"""
   Получает актуальный курс USD/RUB из внешнего API.
   При ошибке сети или неверном формате ответа возвращает None.
   Используется запасной курс (fallback) для устойчивости приложения.
   """

def get_usd_rub_rate():

    url = "https://kurs-rublya.ru/api/v1/rates/latest/"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "currencies" in data and "USD" in data["currencies"]:
            usd_info = data["currencies"]["USD"]
            rate = float(usd_info.get("ratePerUnit"))
            print(f" Курс USD/RUB получен из kurs-rublya: {rate:.4f}")
            return rate
        else:
            print(" В ответе нет ожидаемой структуры (нет currencies/USD).")
            return None

    except requests.exceptions.RequestException as e:
        print(f" Ошибка сети или HTTP: {e}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        print(f" Ошибка парсинга: {e}. Возможно, API изменил структуру.")
        return None


# Парсеры бирж
def parse_bybit(body):
    result = body.get("result", {})
    items = result.get("list", [])
    if body.get("retCode") != 0 or not items:
        return None
    item = items[0]
    price = float(item["lastPrice"])
    change_raw = item.get("price24hPcnt")
    change = float(change_raw) * 100 if change_raw is not None else None
    return price, change


def parse_mexc(body):
    if isinstance(body, list):
        if not body: return None
        item = body[0]
    else:
        item = body
    price_raw = item.get("lastPrice")
    if price_raw is None: return None
    price = float(price_raw)
    change_raw = item.get("priceChangePercent")
    change = float(change_raw) if change_raw is not None else None
    return price, change


def parse_kucoin(body):
    data = body.get("data")
    if not data or not data.get("last"): return None
    price = float(data["last"])
    change_raw = data.get("changeRate")
    change = float(change_raw) * 100 if change_raw is not None else None
    return price, change


PARSERS = {
    "Bybit": parse_bybit,
    "MEXC": parse_mexc,
    "KuCoin": parse_kucoin,
}


def fetch_one_pair(provider, symbol):
    if provider["name"] == "Bybit":
        pair_name = f"{symbol}USDT"
    elif provider["name"] == "MEXC":
        pair_name = f"{symbol}USDT"
    else:  # KuCoin
        pair_name = f"{symbol}-USDT"

    params = {"symbol": pair_name}
    if provider["name"] == "Bybit":
        params["category"] = "spot"

    response = requests.get(
        provider["url"],
        params=params,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    body = response.json()
    return PARSERS[provider["name"]](body)


# ==============================================================================
# ЛОГИКА ЗАГРУЗКИ
# ==============================================================================
def fetch_prices():
    global last_error, usd_rub_rate, use_fallback_rate
    last_error = ""
    errors = []

    # 1. Сначала получаем курс рубля
    rate = get_usd_rub_rate()
    if rate and rate > 0:
        usd_rub_rate = rate
        use_fallback_rate = False
        print(f"[DEBUG] Курс USD/RUB установлен: {usd_rub_rate}")
    else:
        use_fallback_rate = True
        print("[DEBUG] Не удалось получить курс рубля. Используем запасной: 92.5")

    # 2. Собираем цены криптовалют
    prices = {}
    found_any_crypto = False

    for provider in PROVIDERS:
        for symbol in COINS:
            try:
                pair = fetch_one_pair(provider, symbol)
                if pair is not None:
                    prices[symbol] = pair
                    found_any_crypto = True
            except Exception as e:
                err_msg = f"{provider['name']} {symbol}: {e}"
                print(err_msg)
                errors.append(err_msg)

        if found_any_crypto:
            break

    last_error = "\n".join(errors) if errors else ""
    return prices


def format_change(change):
    if change is None: return "—", "gray"
    if change > 0: return f"{change:+.2f}%", COLOR_GROWTH
    if change < 0: return f"{change:+.2f}%", COLOR_FALL
    return "0.00%", "gray"


# ==============================================================================
# ИНТЕРФЕЙС
# ==============================================================================

def on_refresh():
    btn_refresh.config(state="disabled")
    lbl_updated.config(text="Загрузка данных...")

    def worker():
        data = fetch_prices()
        root.after(0, lambda: process_data(data))

    threading.Thread(target=worker, daemon=True).start()


def process_data(data):
    if data is None or len(data) == 0:
        messagebox.showerror("Ошибка", f"Не удалось получить данные.\nПодробности:\n{last_error}")
        lbl_updated.config(text="Обновлено: —")
    else:
        # Очистка таблицы
        for widget in frame_table.winfo_children():
            widget.destroy()

        cols = ["Криптовалюта", "Цена (USD)", "В рублях (RUB)", "Изменение за 24 ч"]
        for i, text in enumerate(cols):
            ttk.Label(frame_table, text=text, font=("Arial", 12, "bold")).grid(row=0, column=i,
                                                                               sticky="w" if i == 0 else "e", padx=10)

        row = 1
        for symbol in COINS:
            name = get_coin_name(symbol)
            pair = data.get(symbol)

            if pair:
                price_usd, change = pair
                price_rub = price_usd * usd_rub_rate
                change_str, change_color = format_change(change)

                ttk.Label(frame_table, text=name).grid(row=row, column=0, sticky="w", padx=10, pady=5)
                ttk.Label(frame_table, text=f"{price_usd:,.2f}").grid(row=row, column=1, sticky="e", padx=10, pady=5)
                ttk.Label(frame_table, text=f"{price_rub:,.2f} ₽").grid(row=row, column=2, sticky="e", padx=10, pady=5)
                ttk.Label(frame_table, text=change_str, foreground=change_color).grid(row=row, column=3, sticky="e",
                                                                                      padx=10, pady=5)
            else:
                ttk.Label(frame_table, text=name, foreground="gray").grid(row=row, column=0, sticky="w", padx=10,
                                                                          pady=5)
                ttk.Label(frame_table, text="Нет данных", foreground="gray").grid(row=row, column=1, columnspan=3,
                                                                                  sticky="w", padx=10, pady=5)
            row += 1

        now = datetime.now().strftime("%H:%M:%S")

        if use_fallback_rate:
            lbl_updated.config(
                text=f"Обновлено: {now} | USD/RUB ≈ {usd_rub_rate:,.2f} ⚠️ (запасной курс)",
                foreground="#dc2626",
                font=("Arial", 11, "bold")
            )
        else:
            lbl_updated.config(
                text=f"Обновлено: {now} | USD/RUB ≈ {usd_rub_rate:,.2f}",
                foreground="gray",
                font=("Arial", 11)
            )

    btn_refresh.config(state="normal")
    root.after(REFRESH_INTERVAL_MS, on_refresh)


def get_coin_name(symbol):
    for name, sym in POPULAR_COINS.items():
        if sym == symbol: return name
    return symbol


# Управление списками
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


# Создание интерфейса (продолжение)
root = tk.Tk()
root.title("ACR_crypto-rates (Курс RUB из kurs-rublya)")
root.geometry("1040x560")

# Левая часть: таблица
frame_main = ttk.Frame(root)
frame_main.pack(side="left", fill="both", expand=True, padx=12, pady=8)
ttk.Label(frame_main, text="Курсы криптовалют", font=("Arial", 16, "bold")).pack(pady=18)

frame_table = ttk.Frame(frame_main)
frame_table.pack(fill="both", expand=True, padx=8, pady=4)

btn_refresh = ttk.Button(frame_main, text="Обновить курсы", command=on_refresh)
btn_refresh.pack(pady=10)

lbl_updated = ttk.Label(frame_main, text="Обновлено: —", foreground="gray")
lbl_updated.pack(side="bottom", pady=12)

# Правая часть: панель
frame_panel = ttk.Frame(root)
frame_panel.pack(side="right", fill="y", padx=12, pady=8)
frame_panel.columnconfigure(0, weight=1)
frame_panel.columnconfigure(1, weight=1)
frame_panel.rowconfigure(0, weight=1)

# Текущие монеты
frame_current = ttk.LabelFrame(frame_panel, text="Текущие монеты", padding=6)
frame_current.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
frame_current.columnconfigure(0, weight=1)
frame_current.rowconfigure(1, weight=1)

lb_current = tk.Listbox(frame_current, height=14, width=26)
lb_current.grid(row=1, column=0, sticky="nsew")

btn_remove = ttk.Button(frame_current, text="Удалить монету", command=on_remove_coin)
btn_remove.grid(row=2, column=0, sticky="ew", pady=8)

# Каталог монет
frame_catalog = ttk.LabelFrame(frame_panel, text="Каталог монет", padding=6)
frame_catalog.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)
frame_catalog.columnconfigure(0, weight=1)
frame_catalog.rowconfigure(1, weight=1)

lb_catalog = tk.Listbox(frame_catalog, height=14, width=26)
lb_catalog.grid(row=1, column=0, sticky="nsew")

btn_add = ttk.Button(frame_catalog, text="Добавить монету", command=on_add_from_catalog)
btn_add.grid(row=2, column=0, sticky="ew", pady=8)

# Инициализируем списки при старте
refresh_current_list()
refresh_catalog()

# Запускаем первое обновление сразу после старта (в отдельном потоке, чтобы не морозить GUI)
root.after(100, on_refresh)

root.mainloop()