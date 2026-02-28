# -*- coding: utf-8 -*-
"""
Калькулятор коммунальных платежей (ХВС, ГВС, свет день/ночь).
Поддержка нескольких объектов (квартир) с отдельными тарифами и историей.
"""
import json
import os
import sys
import uuid
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from calc import calculate

# Путь к данным: рядом с exe или рядом со скриптом
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
OBJECTS_PATH = os.path.join(BASE_DIR, "objects.json")

MONTHS_RU = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
)

DEFAULT_TARIFFS = {
    "tariff_sewage": 46.73,
    "tariff_xvs": 43.24,
    "tariff_gvs": 43.24,
    "tariff_heating_per_gcal": 2891.74,
    "norm_gcal_per_m3": 0.06,
    "tariff_el_day": 6.79,
    "tariff_el_night": 2.81,
}


def load_objects():
    """Загружает все объекты. Миграция с config.json + history.json при первом запуске."""
    if os.path.isfile(OBJECTS_PATH):
        try:
            with open(OBJECTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("objects"):
                    return data
        except Exception:
            pass
    # Миграция: создать первый объект из старых файлов
    tariffs = dict(DEFAULT_TARIFFS)
    history = []
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                tariffs = {**tariffs, **json.load(f)}
        except Exception:
            pass
    if os.path.isfile(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
    obj_id = f"obj_{uuid.uuid4().hex[:8]}"
    data = {
        "current_id": obj_id,
        "objects": [{"id": obj_id, "name": "Квартира 1", "tariffs": tariffs, "history": history}],
    }
    save_objects(data)
    return data


def save_objects(data):
    try:
        with open(OBJECTS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_object(data, obj_id):
    for o in data.get("objects", []):
        if o.get("id") == obj_id:
            return o
    return None


def default_period_name():
    now = datetime.now()
    return f"{MONTHS_RU[now.month - 1]} {now.year}"


def parse_float(s, default=None):
    s = (s or "").strip().replace(",", ".")
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return None


# Premium Apple-style: чистый, воздушный, премиальный
BG_MAIN = "#fafafa"
BG_CARD = "#ffffff"
BG_SUBTLE = "#f2f2f7"
ACCENT = "#0071e3"
ACCENT_HOVER = "#0077ed"
TEXT = "#1d1d1f"
TEXT_SECONDARY = "#86868b"
TEXT_TERTIARY = "#aeaeb2"
BORDER = "#d2d2d7"
RADIUS = 12
FONT_UI = "Segoe UI"
FONT_SIZE = 11
FONT_HEAD = 13
FONT_LARGE = 28
# Цвета для графиков (Apple-inspired)
CHART_WATER = "#34c759"
CHART_ELEC = "#ff9500"
CHART_ACCENT = "#0071e3"
CHART_MUTED = "#8e8e93"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Калькулятор ЖКХ")
        self.root.geometry("660x720")
        self.root.resizable(True, True)
        self.root.minsize(480, 560)
        self.root.configure(bg=BG_MAIN)
        self._setup_style()

        self._data = load_objects()
        self._current_id = self._data.get("current_id")
        self._tab_widgets = {}
        self._setup_menu()
        self._build_ui()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)

        m_objects = tk.Menu(menubar, tearoff=0)
        m_objects.add_command(label="Новый объект", command=self._add_new_object)
        m_objects.add_command(label="Переименовать текущий", command=self._rename_current_object)
        m_objects.add_command(label="Удалить текущий", command=self._delete_current_object)
        menubar.add_cascade(label="Объекты", menu=m_objects)

        self.root.config(menu=menubar)

    def _rename_current_object(self):
        if not self._current_id:
            return
        self._rename_object(self._current_id)

    def _delete_current_object(self):
        if not self._current_id:
            return
        self._delete_object(self._current_id)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=BG_MAIN, foreground=TEXT, font=(FONT_UI, FONT_SIZE))
        style.configure("TFrame", background=BG_MAIN)
        style.configure("TLabel", background=BG_MAIN, foreground=TEXT, font=(FONT_UI, FONT_SIZE))
        style.configure("TLabelframe", background=BG_MAIN, padding=6)
        style.configure(
            "TLabelframe.Label",
            background=BG_MAIN,
            foreground=TEXT_SECONDARY,
            font=(FONT_UI, FONT_SIZE),
        )
        style.configure("TButton", padding=(18, 10), font=(FONT_UI, FONT_SIZE))
        style.map("TButton", background=[("active", BG_SUBTLE)])
        style.configure("TEntry", padding=8, font=(FONT_UI, FONT_SIZE))

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=(0, 0))
        top.pack(fill=tk.BOTH, expand=True)

        self._notebook = ttk.Notebook(top)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook.bind("<Button-3>", self._on_tab_rightclick)
        self._notebook.bind("<Button-2>", self._on_tab_rightclick)
        self._notebook.bind("<Control-Button-1>", self._on_tab_rightclick)
        self._notebook.bind("<Double-Button-1>", self._on_tab_doubleclick)

        for obj in self._data.get("objects", []):
            self._add_object_tab(obj["id"])

        tab_add = ttk.Frame(self._notebook)
        self._notebook.add(tab_add, text="  +  ")
        self._notebook.bind("<Button-1>", self._on_notebook_click)

        idx = next((i for i, o in enumerate(self._data["objects"]) if o["id"] == self._current_id), 0)
        self._notebook.select(idx)

        self._rebuild_tabs_display()

    def _on_notebook_click(self, event):
        try:
            idx = self._notebook.index(f"@{event.x},{event.y}")
            if idx == len(self._data["objects"]):
                self._add_new_object()
                return "break"
        except tk.TclError:
            pass

    def _add_new_object(self):
        obj_id = f"obj_{uuid.uuid4().hex[:8]}"
        n = len(self._data["objects"]) + 1
        name = f"Квартира {n}"
        self._data["objects"].append({
            "id": obj_id, "name": name,
            "tariffs": dict(DEFAULT_TARIFFS),
            "history": []
        })
        self._data["current_id"] = obj_id
        save_objects(self._data)
        self._add_object_tab(obj_id)
        self._rebuild_tabs_display()
        self._notebook.select(len(self._data["objects"]) - 1)

    def _add_object_tab(self, obj_id):
        obj = get_object(self._data, obj_id)
        if not obj:
            return
        frame = ttk.Frame(self._notebook, padding=(0, 0))
        num_tabs = self._notebook.index("end")
        if num_tabs > 0:
            last_text = self._notebook.tab(num_tabs - 1, "text")
            if last_text.strip() == "+":
                self._notebook.insert(num_tabs - 1, frame, text=obj["name"])
            else:
                self._notebook.add(frame, text=obj["name"])
        else:
            self._notebook.add(frame, text=obj["name"])
        widgets = self._build_object_form(frame, obj_id)
        self._tab_widgets[obj_id] = widgets
        self._refresh_timeline_for(obj_id)
        self._fill_previous_for(obj_id)

    def _rebuild_tabs_display(self):
        for i, obj in enumerate(self._data["objects"]):
            self._notebook.tab(i, text=f"  {obj['name']}  ")
            w = self._tab_widgets.get(obj["id"])
            if w and w.get("title_label"):
                w["title_label"].config(text=obj["name"])

    def _on_tab_doubleclick(self, event):
        # На Mac это удобнее, чем ПКМ
        try:
            idx = self._notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        if idx >= len(self._data["objects"]):
            return
        self._rename_object(self._data["objects"][idx]["id"])

    def _on_tab_changed(self, event):
        try:
            idx = self._notebook.index(self._notebook.select())
            if idx < len(self._data["objects"]):
                self._current_id = self._data["objects"][idx]["id"]
                self._data["current_id"] = self._current_id
                save_objects(self._data)
        except tk.TclError:
            pass

    def _on_tab_rightclick(self, event):
        try:
            idx = self._notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        if idx >= len(self._data["objects"]):
            return
        obj = self._data["objects"][idx]
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Переименовать", command=lambda: self._rename_object(obj["id"]))
        if len(self._data["objects"]) > 1:
            menu.add_command(label="Удалить объект", command=lambda: self._delete_object(obj["id"]))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _rename_object(self, obj_id):
        obj = get_object(self._data, obj_id)
        if not obj:
            return
        win = tk.Toplevel(self.root)
        win.title("Переименовать")
        win.geometry("360x120")
        win.transient(self.root)
        win.configure(bg=BG_MAIN)
        f = ttk.Frame(win, padding=24)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Название:").pack(anchor=tk.W)
        e = ttk.Entry(f, width=30)
        e.pack(fill=tk.X, pady=(0, 12))
        e.insert(0, obj.get("name", ""))
        e.focus()

        def do_rename():
            name = (e.get() or "").strip()
            if not name:
                messagebox.showwarning("Переименовать", "Введите название.")
                return
            obj["name"] = name
            if save_objects(self._data):
                self._rebuild_tabs_display()
                win.destroy()

        ttk.Button(f, text="Сохранить", command=do_rename).pack(anchor=tk.W)
        win.bind("<Return>", lambda ev: do_rename())

    def _delete_object(self, obj_id):
        obj = get_object(self._data, obj_id)
        if not obj or len(self._data["objects"]) <= 1:
            return
        if not messagebox.askyesno("Удалить объект", f"Удалить «{obj.get('name', '')}» и всю его историю?"):
            return
        self._data["objects"] = [o for o in self._data["objects"] if o["id"] != obj_id]
        if self._current_id == obj_id:
            self._current_id = self._data["objects"][0]["id"] if self._data["objects"] else None
        self._data["current_id"] = self._current_id
        save_objects(self._data)
        self._tab_widgets.pop(obj_id, None)
        self._rebuild_all_tabs()

    def _rebuild_all_tabs(self):
        for child in self._notebook.winfo_children():
            child.destroy()
        self._tab_widgets.clear()
        for obj in self._data.get("objects", []):
            self._add_object_tab(obj["id"])
        tab_add = ttk.Frame(self._notebook)
        self._notebook.add(tab_add, text="  +  ")
        idx = next((i for i, o in enumerate(self._data["objects"]) if o["id"] == self._current_id), 0)
        self._notebook.select(idx)
        self._rebuild_tabs_display()

    def _build_object_form(self, parent, obj_id):
        canvas = tk.Canvas(parent, bg=BG_MAIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent)
        # Показываем полосу прокрутки только когда она реально нужна
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)

        main = ttk.Frame(canvas, padding=(32, 28))
        cw = canvas.create_window((0, 0), window=main, anchor=tk.NW)

        def _update_scrollbar():
            bbox = canvas.bbox("all")
            if not bbox:
                return
            content_h = bbox[3] - bbox[1]
            view_h = canvas.winfo_height()
            need = content_h > (view_h + 2)
            if need:
                if not scrollbar.winfo_ismapped():
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                if scrollbar.winfo_ismapped():
                    scrollbar.pack_forget()
                canvas.yview_moveto(0)

        def _on_cf(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            _update_scrollbar()
        main.bind("<Configure>", _on_cf)

        def _on_cc(e):
            canvas.itemconfig(cw, width=e.width)
            _update_scrollbar()
        canvas.bind("<Configure>", _on_cc)

        def _mw(e):
            if hasattr(e, "delta") and e.delta:
                canvas.yview_scroll(int(-e.delta / 120), "units")
        def _bs(_):
            canvas.bind_all("<MouseWheel>", _mw)
            canvas.bind_all("<Button-4>", lambda ev: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda ev: canvas.yview_scroll(1, "units"))
        def _us(_):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", _bs)
        canvas.bind("<Leave>", _us)

        row_top = 0
        obj = get_object(self._data, obj_id)
        title = tk.Label(main, text=obj.get("name", "Объект"), font=(FONT_UI, FONT_HEAD), fg=TEXT, bg=BG_MAIN)
        title.grid(row=row_top, column=0, columnspan=5, sticky=tk.W, pady=(0, 16))

        row_top += 1
        lf_timeline = ttk.LabelFrame(main, text="  Периоды  ")
        lf_timeline.grid(row=row_top, column=0, columnspan=5, sticky=tk.EW, pady=(0, 16))
        lf_timeline.columnconfigure(0, weight=1)
        inner = ttk.Frame(lf_timeline, padding=12)
        inner.grid(row=0, column=0, sticky=tk.EW)
        inner.columnconfigure(0, weight=1)
        list_frame = ttk.Frame(inner)
        list_frame.grid(row=0, column=0, sticky=tk.EW)
        list_frame.columnconfigure(0, weight=1)
        timeline_listbox = tk.Listbox(
            list_frame, height=4, font=(FONT_UI, FONT_SIZE),
            bg=BG_CARD, fg=TEXT, selectbackground=ACCENT, selectforeground="white",
            relief=tk.FLAT, highlightthickness=0, borderwidth=0
        )
        scroll_t = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=timeline_listbox.yview)
        timeline_listbox.configure(yscrollcommand=scroll_t.set)
        timeline_listbox.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_t.grid(row=0, column=1, sticky=tk.NS)
        list_frame.columnconfigure(0, weight=1)
        timeline_listbox.bind("<<ListboxSelect>>", lambda e: self._on_timeline_select(obj_id))
        timeline_listbox.bind("<Button-3>", lambda e: self._on_timeline_rightclick(e, obj_id))
        timeline_listbox.bind("<Button-2>", lambda e: self._on_timeline_rightclick(e, obj_id))
        timeline_listbox.bind("<Control-Button-1>", lambda e: self._on_timeline_rightclick(e, obj_id))
        btn_del = ttk.Button(inner, text="Удалить выбранный", command=lambda: self._delete_selected_timeline_record(obj_id))
        btn_del.grid(row=0, column=1, padx=(12, 0), sticky=tk.N)
        analytics_label = tk.Label(inner, text="", font=(FONT_UI, FONT_SIZE), fg=TEXT_SECONDARY, bg=BG_MAIN, anchor=tk.CENTER)
        analytics_label.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(12, 0))
        inner.columnconfigure(0, weight=1)

        row_start = row_top + 1

        # --- Карточка показаний ---
        input_card = ttk.LabelFrame(main, text="  Показания  ")
        input_card.grid(row=row_start, column=0, columnspan=5, sticky=tk.EW, pady=(0, 16))

        input_inner = ttk.Frame(input_card, padding=12)
        input_inner.grid(row=0, column=0, sticky=tk.EW)

        # Колонки: 0 — название, 1 — предыдущие, 2 — текущие
        input_inner.columnconfigure(0, weight=1)
        input_inner.columnconfigure(1, weight=0, minsize=140)
        input_inner.columnconfigure(2, weight=0, minsize=140)

        ttk.Label(input_inner, text="Показание").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        ttk.Label(input_inner, text="Предыдущие").grid(row=0, column=1, sticky=tk.W, pady=(0, 8))
        ttk.Label(input_inner, text="Текущие").grid(row=0, column=2, sticky=tk.W, pady=(0, 8))

        labels = [
            ("ХВС (холодная вода), м³", "xvs_prev", "xvs_curr"),
            ("ГВС (горячая вода), м³", "gvs_prev", "gvs_curr"),
            ("Электричество день, кВт·ч", "el_day_prev", "el_day_curr"),
            ("Электричество ночь, кВт·ч", "el_night_prev", "el_night_curr"),
        ]

        entries = {}
        for i, (text, key_prev, key_curr) in enumerate(labels, start=1):
            ttk.Label(input_inner, text=text).grid(row=i, column=0, sticky=tk.W, pady=6)

            e_prev = ttk.Entry(input_inner)
            e_prev.grid(row=i, column=1, sticky=tk.EW, padx=(8, 8), pady=6)

            e_curr = ttk.Entry(input_inner)
            e_curr.grid(row=i, column=2, sticky=tk.EW, padx=(8, 0), pady=6)

            entries[key_prev] = e_prev
            entries[key_curr] = e_curr

        ttk.Separator(main, orient=tk.HORIZONTAL).grid(
            row=row_start + 1,
            column=0,
            columnspan=5,
            sticky=tk.EW,
            pady=18
        )

        row_btns = row_start + 2

        btn_row = ttk.Frame(main)
        btn_row.grid(row=row_btns, column=0, columnspan=5, sticky=tk.EW, pady=(6, 10))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        btn_calc = ttk.Button(
            btn_row,
            text="Рассчитать",
            command=lambda: self._on_calc(obj_id)
        )
        btn_calc.grid(row=0, column=0, sticky=tk.EW, padx=(0, 8), ipady=2)

        btn_save_history = ttk.Button(
            btn_row,
            text="Сохранить в историю",
            command=lambda: self._save_to_history(obj_id),
            state=tk.DISABLED
        )
        btn_save_history.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), ipady=2)

        row_actions = row_btns + 1

        actions = ttk.Frame(main)
        actions.grid(row=row_actions, column=0, columnspan=5, sticky=tk.W, pady=(0, 16))

        ttk.Button(
            actions,
            text="История",
            command=lambda: self._show_history(obj_id)
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            actions,
            text="Графики",
            command=lambda: self._show_charts(obj_id)
        ).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            actions,
            text="Тарифы",
            command=lambda: self._edit_tariffs(obj_id)
        ).pack(side=tk.LEFT, padx=8)

        result_frame = ttk.LabelFrame(main, text="  Результат  ", padding=20)
        result_frame.grid(row=row_actions + 1, column=0, columnspan=5, sticky=tk.EW, pady=12)
        result_top = ttk.Frame(result_frame)
        result_top.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(result_top, text="Копировать", command=lambda: self._copy_result(obj_id)).pack(side=tk.RIGHT)
        result_text = tk.Text(result_frame, height=8, width=50, wrap=tk.WORD, font=(FONT_UI, FONT_SIZE), bg=BG_SUBTLE, fg=TEXT, relief=tk.FLAT, padx=16, pady=16)
        result_text.pack(fill=tk.BOTH, expand=True)
        result_text.config(state=tk.DISABLED)

        for c in (0, 1, 2, 3):
            main.columnconfigure(c, weight=0)
        main.columnconfigure(4, weight=1)

        return {
            "timeline_listbox": timeline_listbox, "analytics_label": analytics_label,
            "entries": entries, "result_text": result_text, "btn_save_history": btn_save_history,
            "title_label": title,
            "last_result": None,
        }

    def _get_widgets(self, obj_id=None):
        oid = obj_id or self._current_id
        return self._tab_widgets.get(oid, {})

    def _get_inputs(self, obj_id):
        w = self._get_widgets(obj_id)
        entries = w.get("entries", {})
        if not entries:
            return None, "xvs_prev"
        out = {}
        for key in ("xvs_prev", "xvs_curr", "gvs_prev", "gvs_curr", "el_day_prev", "el_day_curr", "el_night_prev", "el_night_curr"):
            e = entries.get(key)
            val = parse_float(e.get() if e else "")
            if val is None:
                return None, key
            out[key] = val
        return out, None

    def _get_records(self, obj_id):
        obj = get_object(self._data, obj_id)
        return obj.get("history", [])

    def _refresh_timeline_for(self, obj_id):
        w = self._get_widgets(obj_id)
        if not w:
            return
        records = sorted(self._get_records(obj_id), key=lambda r: r.get("date_saved", ""))
        lb = w.get("timeline_listbox")
        al = w.get("analytics_label")
        if not lb:
            return
        lb.delete(0, tk.END)
        total_sum = 0
        for r in records:
            total_sum += r.get("total", 0)
            lb.insert(tk.END, f"  {r.get('period', '—')}  —  {r.get('total', 0):,.2f} руб".replace(",", " "))
        n = len(records)
        if n == 0:
            al and al.config(text="Нет сохранённых периодов. После расчёта нажмите «Сохранить в историю».")
        else:
            avg = total_sum / n
            last_period = records[-1].get("period", "—") if records else "—"
            al and al.config(text=f"Всего за {n} мес.: {total_sum:,.2f} руб  |  В среднем: {avg:,.2f} руб/мес.  |  Последний: {last_period}".replace(",", " "))

    def _on_timeline_select(self, obj_id):
        w = self._get_widgets(obj_id)
        records = sorted(self._get_records(obj_id), key=lambda r: r.get("date_saved", ""))
        lb, entries = w.get("timeline_listbox"), w.get("entries", {})
        if not lb or not entries:
            return
        sel = lb.curselection()
        if not sel or sel[0] >= len(records):
            return
        r = records[sel[0]]
        for key, attr in [("xvs_prev", "xvs_curr"), ("gvs_prev", "gvs_curr"), ("el_day_prev", "el_day_curr"), ("el_night_prev", "el_night_curr")]:
            val = r.get(attr)
            if val is not None and key in entries:
                entries[key].delete(0, tk.END)
                entries[key].insert(0, str(val))
            elif key == "xvs_prev":
                messagebox.showinfo("Периоды", "В этой записи нет показаний для подстановки.")
                break

    def _fill_previous_for(self, obj_id):
        w = self._get_widgets(obj_id)
        records = sorted(self._get_records(obj_id), key=lambda r: r.get("date_saved", ""))
        if not records or records[-1].get("xvs_curr") is None:
            return
        r = records[-1]
        entries = w.get("entries", {})
        for key, attr in [("xvs_prev", "xvs_curr"), ("gvs_prev", "gvs_curr"), ("el_day_prev", "el_day_curr"), ("el_night_prev", "el_night_curr")]:
            val = r.get(attr)
            if val is not None and key in entries:
                entries[key].delete(0, tk.END)
                entries[key].insert(0, str(val))

    def _on_timeline_rightclick(self, event, obj_id):
        w = self._get_widgets(obj_id)
        records = sorted(self._get_records(obj_id), key=lambda r: r.get("date_saved", ""))
        lb = w.get("timeline_listbox")
        if not lb:
            return
        sel = lb.curselection()
        if not sel or sel[0] >= len(records):
            return
        idx = sel[0]
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Удалить запись", command=lambda: self._delete_timeline_record(obj_id, idx))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _delete_selected_timeline_record(self, obj_id):
        w = self._get_widgets(obj_id)
        records = sorted(self._get_records(obj_id), key=lambda r: r.get("date_saved", ""))
        lb = w.get("timeline_listbox")
        if not lb:
            return
        sel = lb.curselection()
        if not sel or sel[0] >= len(records):
            messagebox.showinfo("Удаление", "Выберите период в списке для удаления.")
            return
        self._delete_timeline_record(obj_id, sel[0])

    def _delete_timeline_record(self, obj_id, listbox_index):
        obj = get_object(self._data, obj_id)
        records = sorted(obj.get("history", []), key=lambda r: r.get("date_saved", ""))
        if listbox_index >= len(records):
            return
        r = records[listbox_index]
        period = r.get("period", "")
        if not messagebox.askyesno("Удалить запись", f"Удалить период «{period}» из истории?"):
            return
        key = (r.get("period"), r.get("date_saved"))
        obj["history"] = [x for x in obj.get("history", []) if (x.get("period"), x.get("date_saved")) != key]
        if save_objects(self._data):
            self._refresh_timeline_for(obj_id)
            messagebox.showinfo("История", "Запись удалена.")
        else:
            messagebox.showwarning("История", "Не удалось сохранить изменения.")

    def _on_calc(self, obj_id):
        inputs, missing = self._get_inputs(obj_id)
        if inputs is None:
            messagebox.showwarning("Ввод", "Заполните все поля показаний числами.")
            return
        if any(inputs[k] < 0 for k in inputs):
            messagebox.showwarning("Ввод", "Показания не могут быть отрицательными.")
            return
        if inputs["xvs_curr"] < inputs["xvs_prev"] or inputs["gvs_curr"] < inputs["gvs_prev"]:
            messagebox.showwarning("Ввод", "Текущие показания воды должны быть не меньше предыдущих.")
            return
        if inputs["el_day_curr"] < inputs["el_day_prev"] or inputs["el_night_curr"] < inputs["el_night_prev"]:
            messagebox.showwarning("Ввод", "Текущие показания электричества должны быть не меньше предыдущих.")
            return

        obj = get_object(self._data, obj_id)
        tariffs = {k: obj.get("tariffs", {}).get(k, v) for k, v in DEFAULT_TARIFFS.items()}
        result = calculate(**inputs, **tariffs)

        cons = result["consumption"]
        lines = [
            "Расход: ХВС {:.2f} м³, ГВС {:.2f} м³ | эл. день {:.2f}, ночь {:.2f} кВт·ч".format(
                cons["xvs"], cons["gvs"], cons["el_day"], cons["el_night"]
            ),
            "",
            "——— Вода ———",
            f"  Водоотведение:     {result['sum_sewage']:.2f} руб",
            f"  ХВС:               {result['sum_xvs']:.2f} руб",
            f"  Подогрев ГВС:      {result['sum_heating']:.2f} руб",
            f"  ГВС:               {result['sum_gvs']:.2f} руб",
            f"  Итого за воду:     {result['sum_water']:.2f} руб",
            "",
            "——— Электричество ———",
            f"  День:              {result['sum_el_day']:.2f} руб",
            f"  Ночь:              {result['sum_el_night']:.2f} руб",
            f"  Итого за свет:     {result['sum_electricity']:.2f} руб",
            "",
            "═══════════════════════",
            f"  ИТОГО (свет+вода): {result['total']:.2f} руб",
        ]

        w = self._get_widgets(obj_id)
        rt = w.get("result_text")
        if rt:
            rt.config(state=tk.NORMAL)
            rt.delete("1.0", tk.END)
            rt.insert(tk.END, "\n".join(lines))
            rt.config(state=tk.DISABLED)
        w["last_result"] = dict(result)
        w["last_result"]["inputs"] = inputs
        btn = w.get("btn_save_history")
        if btn:
            btn.config(state=tk.NORMAL)

    def _copy_result(self, obj_id):
        w = self._get_widgets(obj_id)
        rt = w.get("result_text")
        text = rt.get("1.0", tk.END) if rt else ""
        if not text.strip():
            messagebox.showinfo("Копирование", "Нет данных для копирования. Сначала выполните расчёт.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Копирование", "Расчёт скопирован в буфер обмена.")

    def _save_to_history(self, obj_id):
        w = self._get_widgets(obj_id)
        last_result = w.get("last_result")
        if not last_result:
            return
        win = tk.Toplevel(self.root)
        win.title("Сохранить в историю")
        win.geometry("400x180")
        win.transient(self.root)
        win.configure(bg=BG_MAIN)
        f = ttk.Frame(win, padding=28)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Период (например: Ноябрь 2025):").pack(anchor=tk.W)
        e_period = ttk.Entry(f, width=30)
        e_period.pack(fill=tk.X, pady=(0, 12))
        e_period.insert(0, default_period_name())
        e_period.focus()

        def do_save():
            period = (e_period.get() or "").strip()
            if not period:
                messagebox.showwarning("История", "Введите название периода.")
                return
            obj = get_object(self._data, obj_id)
            inp = last_result.get("inputs") or {}
            obj.setdefault("history", []).append({
                "period": period,
                "date_saved": datetime.now().strftime("%Y-%m-%d"),
                "sum_water": last_result["sum_water"],
                "sum_electricity": last_result["sum_electricity"],
                "total": last_result["total"],
                "xvs_curr": inp.get("xvs_curr"),
                "gvs_curr": inp.get("gvs_curr"),
                "el_day_curr": inp.get("el_day_curr"),
                "el_night_curr": inp.get("el_night_curr"),
            })
            if save_objects(self._data):
                messagebox.showinfo("История", f"Период «{period}» сохранён в историю.")
                self._refresh_timeline_for(obj_id)
                win.destroy()
            else:
                messagebox.showwarning("История", "Не удалось сохранить.")

        ttk.Button(f, text="Сохранить", command=do_save).pack(anchor=tk.W)
        win.bind("<Return>", lambda e: do_save())

    def _show_history(self, obj_id):
        obj = get_object(self._data, obj_id)
        records = obj.get("history", [])
        win = tk.Toplevel(self.root)
        win.title(f"История — {obj.get('name', 'Объект')}")
        win.geometry("620x460")
        win.transient(self.root)
        win.configure(bg=BG_MAIN)
        f = ttk.Frame(win, padding=28)
        f.pack(fill=tk.BOTH, expand=True)

        cols = ("period", "water", "electricity", "total", "date")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=12)
        tree.heading("period", text="Период")
        tree.heading("water", text="Вода, руб")
        tree.heading("electricity", text="Свет, руб")
        tree.heading("total", text="Итого, руб")
        tree.heading("date", text="Дата сохранения")
        tree.column("period", width=140)
        tree.column("water", width=90)
        tree.column("electricity", width=90)
        tree.column("total", width=90)
        tree.column("date", width=110)
        scroll = ttk.Scrollbar(f, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        sorted_records = sorted(records, key=lambda r: r.get("date_saved", ""), reverse=True)
        total_sum = 0
        for r in sorted_records:
            total_sum += r.get("total", 0)
            tree.insert("", tk.END, values=(
                r.get("period", ""),
                f"{r.get('sum_water', 0):.2f}",
                f"{r.get('sum_electricity', 0):.2f}",
                f"{r.get('total', 0):.2f}",
                r.get("date_saved", ""),
            ))
        n = len(records)
        avg = total_sum / n if n else 0
        last3 = sum(r.get("total", 0) for r in sorted_records[:3])
        lines = [f"Всего за {n} мес.: {total_sum:,.2f} руб  |  В среднем: {avg:,.2f} руб/мес.".replace(",", " ")]
        if n >= 3:
            lines.append(f"  За последние 3 мес.: {last3:,.2f} руб".replace(",", " "))
        lbl = ttk.Label(f, text="  ".join(lines))
        lbl.pack(anchor=tk.W, pady=(8, 0))

    def _show_charts(self, obj_id):
        obj = get_object(self._data, obj_id)
        if not obj:
            return
        records = obj.get("history", [])
        if not records:
            messagebox.showinfo(
                "Графики",
                "Нет данных для графика. Сохраните хотя бы один период в историю.",
            )
            return

        sorted_records = sorted(records, key=lambda r: r.get("date_saved", ""))
        periods = [r.get("period", "—") for r in sorted_records]
        totals = [r.get("total", 0) for r in sorted_records]
        water = [r.get("sum_water", 0) for r in sorted_records]
        electricity = [r.get("sum_electricity", 0) for r in sorted_records]

        win = tk.Toplevel(self.root)
        win.title(f"Аналитика — {obj.get('name', 'Объект')}")
        win.geometry("820x620")
        win.transient(self.root)
        win.configure(bg=BG_MAIN)

        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["Segoe UI", "Helvetica Neue", "Arial"]
        plt.rcParams["axes.unicode_minus"] = False

        fig = Figure(figsize=(8, 6), dpi=110, facecolor=BG_MAIN)
        fig.subplots_adjust(hspace=0.28, left=0.07, right=0.98, top=0.92, bottom=0.16)

        x = list(range(len(periods)))
        max_w = max(water) if water else 0
        max_e = max(electricity) if electricity else 0

        def _style_axes(ax):
            ax.set_facecolor("none")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(colors=TEXT_SECONDARY)
            ax.yaxis.grid(True, linestyle="--", alpha=0.35)
            ax.set_axisbelow(True)

        # 1) Вода по месяцам (бар)
        ax1 = fig.add_subplot(2, 1, 1)
        _style_axes(ax1)
        bars1 = ax1.bar(x, water, color=CHART_WATER, width=0.62)
        ax1.set_title("Вода по месяцам", fontsize=12, pad=10)
        ax1.set_ylabel("Руб", fontsize=10, color=TEXT_SECONDARY)
        ax1.set_xticks(x)
        ax1.set_xticklabels([])

        pad1 = max_w * 0.03 if max_w else 0
        for i, b in enumerate(bars1):
            v = b.get_height()
            if v:
                ax1.text(i, v + pad1, f"{v:,.0f}".replace(",", " "), ha="center", va="bottom",
                         fontsize=9, color=TEXT_SECONDARY)

        # 2) Электричество по месяцам (бар)
        ax2 = fig.add_subplot(2, 1, 2)
        _style_axes(ax2)
        bars2 = ax2.bar(x, electricity, color=CHART_ELEC, width=0.62)
        ax2.set_title("Электричество по месяцам", fontsize=12, pad=10)
        ax2.set_ylabel("Руб", fontsize=10, color=TEXT_SECONDARY)
        ax2.set_xticks(x)
        ax2.set_xticklabels(periods, rotation=30, ha="right", fontsize=9)

        pad2 = max_e * 0.03 if max_e else 0
        for i, b in enumerate(bars2):
            v = b.get_height()
            if v:
                ax2.text(i, v + pad2, f"{v:,.0f}".replace(",", " "), ha="center", va="bottom",
                         fontsize=9, color=TEXT_SECONDARY)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

    def _edit_tariffs(self, obj_id):
        obj = get_object(self._data, obj_id)
        tariffs = obj.get("tariffs", {})
        win = tk.Toplevel(self.root)
        win.title(f"Тарифы — {obj.get('name', 'Объект')}")
        win.geometry("440x380")
        win.transient(self.root)
        win.configure(bg=BG_MAIN)
        f = ttk.Frame(win, padding=28)
        f.pack(fill=tk.BOTH, expand=True)

        entries_t = {}
        rows = [
            ("Водоотведение, руб/м³", "tariff_sewage"),
            ("ХВС, руб/м³", "tariff_xvs"),
            ("ГВС, руб/м³", "tariff_gvs"),
            ("Подогрев, руб/Гкал", "tariff_heating_per_gcal"),
            ("Норматив Гкал/м³", "norm_gcal_per_m3"),
            ("Электричество день, руб/кВт·ч", "tariff_el_day"),
            ("Электричество ночь, руб/кВт·ч", "tariff_el_night"),
        ]
        for i, (label, key) in enumerate(rows):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            e = ttk.Entry(f, width=14)
            e.insert(0, str(tariffs.get(key, DEFAULT_TARIFFS[key])))
            e.grid(row=i, column=1, padx=6, pady=2)
            entries_t[key] = e

        def save():
            new_config = {}
            for key in DEFAULT_TARIFFS:
                v = parse_float(entries_t[key].get(), DEFAULT_TARIFFS[key])
                if v is None or v < 0:
                    messagebox.showwarning("Тарифы", f"Некорректное значение для «{key}».")
                    return
                new_config[key] = v
            obj["tariffs"] = new_config
            if save_objects(self._data):
                messagebox.showinfo("Тарифы", "Тарифы сохранены.")
            else:
                messagebox.showwarning("Тарифы", "Не удалось сохранить.")
            win.destroy()

        ttk.Button(f, text="Сохранить", command=save).grid(
            row=len(rows), column=0, columnspan=2, pady=12
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
