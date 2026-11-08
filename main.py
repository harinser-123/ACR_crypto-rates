import tkinter as tk
from tkinter import ttk

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