import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import requests

# Список монет для отображения (тикеры: BTC, ETH и т. д.).
# Пользователь может добавлять и удалять монеты прямо в приложении.
COINS = ["BTC", "ETH", "SOL", "ADA", "DOGE"]

# Публичные API бирж — цены без ключей и регистрации.
# Каждый источник запрашивается ТОЧЕЧНО: по одной паре за запрос.
# Ответ крошечный, поэтому тайм-ауты и медленная сеть не страшны.
# Пробуем Bybit, если не отвечает — MEXC, затем KuCoin.
PROVIDERS = [
    {"name": "Bybit", "url": "https://api.bybit.com/v5/market/tickers"},
    {"name": "MEXC", "url": "https://api.mexc.com/api/v3/ticker/price"},
    {"name": "KuCoin", "url": "https://api.kucoin.com/api/v1/market/orderbook/level1"},
]

REFRESH_INTERVAL_MS = 120_000  # автообновление раз в 2 минуты

# Обычный заголовок браузера — некоторые API отклоняют
# запросы со стандартным User-Agent библиотеки requests.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Локальный словарь популярных монет для поиска: имя -> тикер.
# Поиск работает мгновенно и без запросов к сети.
POPULAR_COINS = {
    "Bitcoin": "BTC",
    "Ethereum": "ETH",
    "Tether": "USDT",
    "BNB": "BNB",
    "Solana": "SOL",
    "Ripple": "XRP",
    "Cardano": "ADA",
    "Dogecoin": "DOGE",
    "TRON": "TRX",
    "Toncoin": "TON",
    "Avalanche": "AVAX",
    "Polkadot": "DOT",
    "Chainlink": "LINK",
    "Polygon": "POL",
    "Litecoin": "LTC",
    "Shiba Inu": "SHIB",
    "Bitcoin Cash": "BCH",
    "Uniswap": "UNI",
    "Cosmos": "ATOM",
    "Stellar": "XLM",
    "Ethereum Classic": "ETC",
    "Filecoin": "FIL",
    "Arbitrum": "ARB",
    "Optimism": "OP",
    "Aptos": "APT",
    "Sui": "SUI",
    "NEAR Protocol": "NEAR",
    "Injective": "INJ",
    "Aave": "AAVE",
    "Algorand": "ALGO",
    "VeChain": "VET",
    "Internet Computer": "ICP",
    "Hedera": "HBAR",
    "Pepe": "PEPE",
    "FLOKI": "FLOKI",
    "Bonk": "BONK",
    "USD Coin": "USDC",
    "Dai": "DAI",
    "Wrapped Bitcoin": "WBTC",
    "Render": "RENDER",
    "Artificial Superintelligence Alliance": "FET",
    "Celestia": "TIA",
    "Jupiter": "JUP",
    "Pyth Network": "PYTH",
    "THORChain": "RUNE",
    "The Graph": "GRT",
    "The Sandbox": "SAND",
    "Decentraland": "MANA",
    "Gala": "GALA",
    "Chiliz": "CHZ",
    "Curve DAO": "CRV",
    "Maker": "MKR",
    "Lido DAO": "LDO",
    "Stacks": "STX",
    "Sei": "SEI",
    "Kaspa": "KAS",
}

# Тикеры, по которым мы хоть раз получили цену (для фильтра поиска)
available_pairs = set()

last_error = ""  # текст последней ошибки для показа в окне


def fetch_one_price(provider, symbol):
    """Получает цену одной пары у конкретной биржи.

    Возвращает число или None, если пара у этой биржи не торгуется.
    """
    if provider["name"] == "Bybit":
        params = {"category": "spot", "symbol": f"{symbol}USDT"}
    elif provider["name"] == "MEXC":
        params = {"symbol": f"{symbol}USDT"}
    else:  # KuCoin — пары пишутся через дефис: BTC-USDT
        params = {"symbol": f"{symbol}-USDT"}

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
        # Если пары нет, Bybit отвечает с кодом ошибки в retCode
        if body.get("retCode") != 0 or not items:
            return None
        return float(items[0]["lastPrice"])
    elif provider["name"] == "MEXC":
        # Если пары нет, MEXC отдаёт HTTP-ошибку — её поймает raise_for_status
        return float(body["price"])
    else:  # KuCoin
        data = body.get("data")
        if not data or not data.get("price"):
            return None
        return float(data["price"])


def fetch_prices():
    """Получает курсы всех монет списка точечными запросами.

    Перебирает биржи по очереди: если биржа ответила хотя бы по одной
    монете, дальше спрашиваем только у неё. Возвращает словарь
    {тикер: цена в USD} или None, если не ответила ни одна биржа.
    """
    global last_error, available_pairs
    last_error = ""
    errors = []

    for provider in PROVIDERS:
        prices = {}
        for symbol in COINS:
            try:
                price = fetch_one_price(provider, symbol)
                if price is not None:
                    prices[symbol] = price
            except Exception as e:
                print(f"Ошибка запроса ({provider['name']} {symbol}):", e)
                errors.append(f"{provider['name']} {symbol}: {e}")

        if prices:
            # Запоминаем монеты с известной ценой — для фильтра поиска
            available_pairs = available_pairs | set(prices)
            return prices

    last_error = "\n".join(errors) if errors else "неизвестная ошибка"
    return None


def on_refresh():
    """Обновляет таблицу курсов и планирует следующее обновление."""
    # Блокируем кнопку во время загрузки (чтобы не нажимали много раз)
    btn_refresh.config(state="disabled")
    lbl_updated.config(text="Загрузка...")

    data = fetch_prices()

    if data is None:
        messagebox.showerror(
            "Ошибка",
            f"Не удалось получить курсы.\nПодробности:\n{last_error}",
        )
        lbl_updated.config(text="Обновлено: —")
    else:
        # Очищаем и заново заполняем таблицу
        for widget in frame_table.winfo_children():
            widget.destroy()

        # Заголовки таблицы
        ttk.Label(frame_table, text="Криптовалюта", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10)
        ttk.Label(frame_table, text="Цена (USD)", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="e", padx=10)

        row = 1
        for symbol in COINS:
            name = get_coin_name(symbol)
            price = data.get(symbol)
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


def get_coin_name(symbol):
    """Возвращает полное имя монеты по тикеру из локального словаря."""
    for name, sym in POPULAR_COINS.items():
        if sym == symbol:
            return name
    return symbol


def refresh_coin_list():
    """Перерисовывает список монет в панели справа."""
    lb_coins.delete(0, tk.END)
    for symbol in COINS:
        lb_coins.insert(tk.END, f"{get_coin_name(symbol)} ({symbol})")


def on_search_coin():
    """Ищет монеты по названию или тикеру в локальном словаре.

    Если по каким-то монетам уже приходили цены — показывает только их,
    иначе всё, что нашлось в словаре.
    """
    global search_results

    query = entry_search.get().strip()
    if not query:
        messagebox.showwarning("Внимание", "Введите название монеты, например Bitcoin.")
        return

    q = query.lower()

    matches = [
        {"symbol": sym, "name": name}
        for name, sym in POPULAR_COINS.items()
        if q in name.lower() or q in sym.lower()
    ]

    if available_pairs:
        # Есть данные с биржи — фильтруем по монетам с известной ценой
        results = [c for c in matches if c["symbol"] in available_pairs]
    else:
        results = matches

    lb_results.delete(0, tk.END)
    search_results = results

    if not results:
        lb_results.insert(tk.END, "Ничего не найдено")
        return

    for c in results[:10]:
        lb_results.insert(tk.END, f"{c['name']} ({c['symbol']})")


def on_add_selected():
    """Добавляет монету, выбранную в списке результатов поиска."""
    selection = lb_results.curselection()
    if not selection:
        messagebox.showwarning("Внимание", "Сначала найдите монету и выберите её в списке результатов.")
        return

    coin = search_results[selection[0]]
    symbol = coin["symbol"]

    if symbol in COINS:
        messagebox.showwarning("Внимание", "Эта монета уже в списке.")
        return

    COINS.append(symbol)
    entry_search.delete(0, tk.END)
    lb_results.delete(0, tk.END)
    refresh_coin_list()
    on_refresh()  # сразу показываем новую монету в таблице


def on_remove_coin():
    """Удаляет монету, выбранную в списке справа."""
    selection = lb_coins.curselection()
    if not selection:
        messagebox.showwarning("Внимание", "Выберите монету в списке справа.")
        return
    index = selection[0]
    COINS.pop(index)
    refresh_coin_list()
    on_refresh()


# Создаём главное окно
root = tk.Tk()
root.title("Курсы криптовалют")
root.geometry("700x460")

# Левая часть: таблица, кнопка, статус
frame_main = ttk.Frame(root)
frame_main.pack(side="left", fill="both", expand=True, padx=10, pady=5)

# Заголовок
lbl_title = ttk.Label(frame_main, text="Курсы криптовалют", font=("Arial", 16, "bold"))
lbl_title.pack(pady=20)

# Таблица курсов
frame_table = ttk.Frame(frame_main)
frame_table.pack(fill="both", expand=True, padx=10, pady=5)

# Кнопка ручного обновления курсов
btn_refresh = ttk.Button(frame_main, text="Обновить курсы", command=on_refresh)
btn_refresh.pack(pady=10)

# Статус обновления
lbl_updated = ttk.Label(frame_main, text="Обновлено: —", foreground="gray")
lbl_updated.pack(side="bottom", pady=10)

# Правая часть: управление списком монет
frame_panel = ttk.Frame(root)
frame_panel.pack(side="right", fill="y", padx=10, pady=5)

lbl_panel = ttk.Label(frame_panel, text="Мои монеты", font=("Arial", 12, "bold"))
lbl_panel.pack(pady=5)

lb_coins = tk.Listbox(frame_panel, height=7, width=26)
lb_coins.pack(padx=5, pady=5)

btn_remove = ttk.Button(frame_panel, text="Удалить выбранную", command=on_remove_coin)
btn_remove.pack(fill="x", padx=5, pady=(5, 0))

# Блок поиска монет
lbl_search = ttk.Label(frame_panel, text="Поиск монеты", font=("Arial", 12, "bold"))
lbl_search.pack(pady=(15, 5))

entry_search = ttk.Entry(frame_panel, width=26)
entry_search.pack(padx=5, pady=(0, 5))

btn_search = ttk.Button(frame_panel, text="Найти", command=on_search_coin)
btn_search.pack(fill="x", padx=5, pady=(0, 5))

lb_results = tk.Listbox(frame_panel, height=7, width=26)
lb_results.pack(padx=5, pady=5)

btn_add = ttk.Button(frame_panel, text="Добавить выбранную", command=on_add_selected)
btn_add.pack(fill="x", padx=5, pady=(5, 0))

refresh_coin_list()
search_results = []  # сюда сохраняются результаты последнего поиска

# Первое обновление сразу при запуске
root.after(0, on_refresh)

root.mainloop()