"""Tk menu presentation; catalog and price controls keep their widget identities."""

import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata
from search_config import SEARCH_MODES, whole_number

from phantom_reader import OFFICIAL_ITEMS, ITEM_BY_ID, PRESET_TEMPLATES, TIER_INFO

COLOR_BG = "#0B111B"
COLOR_CARD = "#121C2A"
COLOR_CARD_ALT = "#1A283A"
COLOR_BORDER = "#2A3B50"
COLOR_BORDER_GLOW = "#58C9EE"
COLOR_GOLD = "#F8C65B"
COLOR_PURPLE = "#BC91FF"
COLOR_BLUE = "#76B8FF"
COLOR_GREEN = "#68D8A0"
COLOR_RED = "#FF7D87"
COLOR_TEXT = "#EDF3FA"
COLOR_TEXT_DIM = "#9CABC0"
FONT_TITLE = ("Segoe UI Semibold", 18)
FONT_SUBTITLE = ("Segoe UI Semibold", 12)
FONT_BODY = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI Semibold", 11)
FONT_TAB = ("Segoe UI Semibold", 13)
FONT_SMALL = ("Segoe UI", 10)
FONT_CAPTION = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_COUNTER = ("Segoe UI Semibold", 10)
RARITY_COLORS = {"LEGENDARY": COLOR_GOLD, "RARE": COLOR_PURPLE,
                 "UNCOMMON": COLOR_BLUE, "COMMON": COLOR_TEXT_DIM}
THEORETICAL_MIN_PRICE = {"COMMON": 15, "UNCOMMON": 35, "RARE": 50, "LEGENDARY": 120}
RARITIES = [("LEGENDARY", "rarity_golden"), ("RARE", "rarity_epic"),
            ("UNCOMMON", "rarity_rare"), ("COMMON", "rarity_common")]
PRESET_KEYS = {
    "record_perfect_plus": "preset_wr", "record_perfect_plus_white": "preset_wr_white",
    "record_perfect": "preset_good", "fast_good": "preset_fast", "moai_rain": "preset_moai",
    "vendor_paradise": "preset_vendor", "double_microwave": "preset_micro",
    "double_microwave_white": "preset_micro_white", "graveyard_bald_heads": "preset_graveyard_bald",
}
MENU_TEXT = {
    "es": {"white_microwaves": "Microondas blancos", "bald_heads": "Cabezas calvas",
           "invalid_mode": "Elegí Ítems, Dorados o Plantillas antes de buscar.", "title": "MB Helper · Buscador de semillas", "legal_badge": "BUSCADOR DE SEMILLAS · LECTURA EXTERNA",
           "tab1": "Ítems", "tab2": "Dorados", "tab4": "Plantillas",
           "items_chosen": "Tu selección", "items_none": "Elegí hasta 3 ítems del catálogo. Cada uno requiere un vendedor distinto.",
           "search_item": "Catálogo de ítems", "rarity_all": "Todos", "rarity_golden": "Dorados", "rarity_epic": "Épicos",
           "rarity_rare": "Raros", "rarity_common": "Comunes", "catalog_count": "{count} de {total} ítems · Ctrl+F para buscar",
           "catalog_empty": "Sin coincidencias. Probá otro nombre o rareza.", "selection_count": "{count}/3 ítems · Un vendedor por ítem",
           "price_invalid": "Ingresá un precio entero positivo o dejalo vacío.", "audit_hud": "Diagnóstico del HUD",
           "btn_start": "Iniciar búsqueda · F5", "btn_stop": "Detener búsqueda · F5", "btn_clear": "Limpiar selección",
           "tab4_title": "Rangos y plantillas", "tier_title": "Rango mínimo",
           "preset_title": "O elegí una plantilla", "btn_test_reset": "Probar reinicio", "btn_logs": "Ver registro",
           "invalid_prices": "Revisá los precios: solo enteros positivos, cero o vacío.",
           "config_locked": "Detené la búsqueda para cambiar el objetivo."},
    "en": {"white_microwaves": "White microwaves", "bald_heads": "Bald heads",
           "invalid_mode": "Choose Items, Golden or Templates before searching.", "title": "MB Helper · Seed finder", "legal_badge": "SEED FINDER · EXTERNAL READER",
           "tab1": "Items", "tab2": "Golden", "tab4": "Templates",
           "items_chosen": "Your selection", "items_none": "Choose up to 3 catalog items. Each needs a different vendor.",
           "search_item": "Item catalog", "rarity_all": "All", "rarity_golden": "Golden", "rarity_epic": "Epic",
           "rarity_rare": "Rare", "rarity_common": "Common", "catalog_count": "{count} of {total} items · Ctrl+F to search",
           "catalog_empty": "No matches. Try another name or rarity.", "selection_count": "{count}/3 items · One vendor per item",
           "price_invalid": "Enter a positive whole price or leave empty.", "audit_hud": "HUD diagnostics",
           "btn_start": "Start search · F5", "btn_stop": "Stop search · F5", "btn_clear": "Clear selection",
           "tab4_title": "Tiers and templates", "tier_title": "Minimum tier",
           "preset_title": "Or choose a template", "btn_test_reset": "Test reset", "btn_logs": "View log",
           "invalid_prices": "Check prices: positive whole numbers, zero or empty.",
           "config_locked": "Stop searching before changing the target."},
    "pt": {"white_microwaves": "Micro-ondas brancos", "bald_heads": "Cabeças calvas",
           "invalid_mode": "Escolha Itens, Dourados ou Modelos antes de buscar.", "title": "MB Helper · Buscador de sementes", "legal_badge": "BUSCADOR DE SEMENTES · LEITURA EXTERNA",
           "tab1": "Itens", "tab2": "Dourados", "tab4": "Modelos",
           "items_chosen": "Sua seleção", "items_none": "Escolha até 3 itens do catálogo. Cada um requer um vendedor diferente.",
           "search_item": "Catálogo de itens", "rarity_all": "Todos", "rarity_golden": "Dourados", "rarity_epic": "Épicos",
           "rarity_rare": "Raros", "rarity_common": "Comuns", "catalog_count": "{count} de {total} itens · Ctrl+F para buscar",
           "catalog_empty": "Nenhum resultado. Tente outro nome ou raridade.", "selection_count": "{count}/3 itens · Um vendedor por item",
           "price_invalid": "Digite um preço inteiro positivo ou deixe vazio.", "audit_hud": "Diagnóstico do HUD",
           "btn_start": "Iniciar busca · F5", "btn_stop": "Parar busca · F5", "btn_clear": "Limpar seleção",
           "tab4_title": "Níveis e modelos", "tier_title": "Nível mínimo",
           "preset_title": "Ou escolha um modelo", "btn_test_reset": "Testar reinício", "btn_logs": "Ver registro",
           "invalid_prices": "Verifique os preços: inteiros positivos, zero ou vazio.",
           "config_locked": "Pare a busca antes de alterar o objetivo."},
}
def search_key(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


def label(parent, text="", **kwargs):
    options = dict(text=text, bg=parent.cget("bg"), fg=COLOR_TEXT, font=FONT_BODY, anchor="w")
    options.update(kwargs)
    return tk.Label(parent, **options)


def button(parent, text, command, **kwargs):
    options = dict(text=text, command=command, font=FONT_BODY, bg=COLOR_CARD_ALT,
                   fg=COLOR_TEXT, activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT,
                   relief="flat", borderwidth=0, padx=12, pady=8, cursor="hand2")
    options.update(kwargs)
    return tk.Button(parent, **options)


class MenuUI:
    def setup_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=COLOR_CARD_ALT, background=COLOR_BORDER,
                        foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT, borderwidth=0, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_CARD_ALT)],
                  foreground=[("readonly", COLOR_TEXT)], selectbackground=[("readonly", COLOR_CARD_ALT)])
        style.configure("Vertical.TScrollbar", background=COLOR_BORDER, troughcolor=COLOR_CARD,
                        borderwidth=0, arrowcolor=COLOR_TEXT_DIM)
        self.option_add("*TCombobox*Listbox.background", COLOR_CARD_ALT)
        self.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT)
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(16, 12))
        title = tk.Frame(header, bg=COLOR_BG)
        title.pack(side="left")
        label(title, "MB HELPER", font=FONT_TITLE).pack(anchor="w")
        self.lbl_legal = label(title, self.t("legal_badge"), fg=COLOR_TEXT_DIM, font=FONT_SMALL)
        self.lbl_legal.pack(anchor="w", pady=(2, 0))
        language = tk.Frame(header, bg=COLOR_BG)
        language.pack(side="right")
        self.lbl_lang_prefix = label(language, self.t("lang_lbl"), font=FONT_SMALL, fg=COLOR_TEXT_DIM)
        self.lbl_lang_prefix.pack(side="left", padx=(0, 6))
        self.lang_combo = ttk.Combobox(language, values=["Español", "English", "Português (BR)"],
                                       state="readonly", width=13, font=FONT_BODY)
        self.lang_combo.set("Español")
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        self.btn_header_overlay = button(header, "HUD · F6", self.toggle_powerup_overlay,
                                          fg=COLOR_GREEN, font=FONT_BOLD)
        self.btn_header_overlay.pack(side="right", padx=12)
        self.btn_overlay_toggle = self.btn_header_overlay
        self.status_conn_lbl = label(header, self.t("looking_game"), fg=COLOR_TEXT_DIM, font=FONT_SMALL)
        self.status_conn_lbl.pack(side="right", padx=8)
        nav = tk.Frame(self, bg=COLOR_BG)
        nav.pack(fill="x", padx=20, pady=(0, 10))
        for column, mode in enumerate(SEARCH_MODES):
            btn = button(nav, self.t(f"tab{mode}"), lambda selected=mode: self.switch_mode(selected),
                         font=FONT_TAB, pady=12)
            btn.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 3, 0))
            nav.columnconfigure(column, weight=1, uniform="navigation")
            setattr(self, f"btn_tab{mode}", btn)
        self.btn_tab1.config(bg=COLOR_BORDER, fg=COLOR_BORDER_GLOW)

        # Footer is packed before content, so start/stop stays reachable on small windows.
        footer = tk.Frame(self, bg=COLOR_CARD, padx=14, pady=12,
                          highlightbackground=COLOR_BORDER, highlightthickness=1)
        footer.pack(side="bottom", fill="x", padx=20, pady=(10, 14))
        actions = tk.Frame(footer, bg=COLOR_CARD)
        actions.pack(fill="x")
        self.btn_action = button(actions, self.t("btn_start"), self.toggle_search,
                                 bg="#1979A4", activebackground="#238AB6", font=FONT_BOLD, pady=11)
        self.btn_action.pack(side="left")
        self.badge_afk = label(actions, self.t("badge_afk"), fg=COLOR_GREEN, font=FONT_SMALL)
        self.badge_afk.pack(side="left", padx=12)
        self.lbl_counter = label(actions, f"{self.t('attempts')}: #0  |  {self.t('time')}: 00:00",
                                  fg=COLOR_GOLD, font=FONT_COUNTER)
        self.lbl_counter.pack(side="right")
        tools = tk.Frame(footer, bg=COLOR_CARD)
        tools.pack(fill="x", pady=(8, 6))
        self.btn_test_reset = button(tools, self.t("btn_test_reset"), self.test_quick_reset, pady=5, font=FONT_SMALL)
        self.btn_test_reset.pack(side="left")
        self.btn_logs = button(tools, self.t("btn_logs"), self.open_log_file, pady=5, font=FONT_SMALL)
        self.btn_logs.pack(side="left", padx=6)
        self.btn_audit_powerups = button(tools, self.t("audit_hud"), self.show_audit_powerups_dialog,
                                         pady=5, font=FONT_SMALL, fg=COLOR_TEXT_DIM)
        self.btn_audit_powerups.pack(side="left")
        self.lbl_shortcuts_hint = label(tools, "F5 · Start / Stop    F6 · HUD", fg=COLOR_TEXT_DIM, font=FONT_SMALL)
        self.lbl_shortcuts_hint.pack(side="right")
        self.lbl_status = label(footer, self.t("status_stopped_user"), font=FONT_BOLD)
        self.lbl_status.pack(fill="x", pady=(0, 4))
        self.lbl_live_data = label(footer, self.t("status_reading"), font=FONT_MONO, fg=COLOR_TEXT_DIM)
        self.lbl_live_data.pack(fill="x")
        footer.bind("<Configure>", lambda e: (self.lbl_status.config(wraplength=max(240, e.width-30)),
                                               self.lbl_live_data.config(wraplength=max(240, e.width-30))))
        self.content_container = tk.Frame(self, bg=COLOR_BG)
        self.content_container.pack(fill="both", expand=True, padx=20)
        self.tab1_frame = self.build_tab1_ui()
        self.tab2_frame = self.build_tab2_ui()
        self.tab4_frame = self.build_tab4_ui()
        self.tab1_frame.pack(fill="both", expand=True)
        self.on_select_tier()

    def create_scrollable_tab_frame(self, parent=None):
        outer = tk.Frame(parent or self.content_container, bg=COLOR_CARD,
                         highlightbackground=COLOR_BORDER, highlightthickness=1)
        canvas = tk.Canvas(outer, bg=COLOR_CARD, highlightthickness=0, yscrollincrement=24)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=COLOR_CARD)
        win_id = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        return outer, canvas, content

    def _on_global_mousewheel(self, event):
        if not event.delta:
            return
        # Let dropdowns and numeric controls consume their own wheel events.
        if isinstance(event.widget, (tk.Entry, tk.Spinbox, ttk.Combobox)):
            return
        self._scroll_menu(event.widget, int(-event.delta / 120) * 2 or (-1 if event.delta > 0 else 1))

    def _scroll_menu(self, widget, units):
        canvases = [self.items_canvas, self.selection_canvas, self.tab2_canvas, self.tab4_canvas]
        current = widget
        while current is not None:
            if current in canvases:
                if current.yview() != (0.0, 1.0):
                    current.yview_scroll(units, "units")
                return
            current = getattr(current, "master", None)

    def _on_global_mousewheel_linux(self, units):
        x, y = self.winfo_pointerxy()
        self._scroll_menu(self.winfo_containing(x, y), units)

    def build_tab1_ui(self):
        frame = tk.Frame(self.content_container, bg=COLOR_BG)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, minsize=280)
        frame.rowconfigure(0, weight=1)
        catalog = tk.Frame(frame, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        catalog.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        search = tk.Frame(catalog, bg=COLOR_CARD)
        search.pack(fill="x", padx=14, pady=(12, 8))
        self.lbl_search_title = label(search, self.t("search_item"), font=FONT_SUBTITLE)
        self.lbl_search_title.pack(anchor="w", pady=(0, 8))
        self.search_var = tk.StringVar(self)
        self.rarity_filter = tk.StringVar(self, value="ALL")
        self.search_entry = tk.Entry(search, textvariable=self.search_var, bg=COLOR_BG, fg=COLOR_TEXT,
                                     insertbackground=COLOR_TEXT, relief="flat", font=FONT_BODY,
                                     highlightthickness=1, highlightbackground=COLOR_BORDER,
                                     highlightcolor=COLOR_BORDER_GLOW)
        self.search_entry.pack(fill="x", ipady=8)
        self.search_entry.bind("<Escape>", lambda e: self.search_var.set(""))
        self.bind("<Control-f>", lambda e: (self.switch_mode(1), self.search_entry.focus_set()))
        filters = tk.Frame(search, bg=COLOR_CARD)
        filters.pack(fill="x", pady=(8, 0))
        self.rarity_buttons = {}
        for index, (key, i18n) in enumerate([("ALL", "rarity_all")] + RARITIES):
            btn = button(filters, self.t(i18n), lambda value=key: self._select_rarity(value),
                         padx=5, pady=6, font=FONT_CAPTION)
            btn.grid(row=0, column=index, sticky="ew", padx=(0, 3))
            filters.columnconfigure(index, weight=1, uniform="rarities")
            self.rarity_buttons[key] = btn
        self.lbl_catalog_count = label(search, "", font=FONT_SMALL, fg=COLOR_TEXT_DIM)
        self.lbl_catalog_count.pack(anchor="w", pady=(8, 0))
        outer, self.items_canvas, self.items_grid_frame = self.create_scrollable_tab_frame(catalog)
        outer.config(highlightthickness=0)
        outer.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._catalog_columns = 2
        self._catalog_layout = None
        self._catalog_after = None
        self._item_buttons = {}
        self._item_search = {}
        self._item_records = {}
        self._item_presentation = {}
        for item in OFFICIAL_ITEMS:
            if item[0] == 0:
                continue
            tid, codename = item[:2]
            self._item_records[tid] = item
            self._item_search[tid] = search_key(" ".join(item[1:5]))
            self._item_buttons[tid] = button(self.items_grid_frame, "", lambda data=item: self.toggle_item_selection(*data[:5]),
                                             image=self.item_icons.get(codename), compound="left", anchor="w", padx=10, pady=12)
        self._empty_catalog = label(self.items_grid_frame, self.t("catalog_empty"), fg=COLOR_TEXT_DIM, justify="center")
        self.items_canvas.bind("<Configure>", self._on_catalog_resize, add="+")
        self.search_var.trace_add("write", self._schedule_catalog_refresh)
        self.rarity_filter.trace_add("write", self._schedule_catalog_refresh)
        side = tk.Frame(frame, bg=COLOR_CARD, width=280, highlightbackground=COLOR_BORDER, highlightthickness=1)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.columnconfigure(0, weight=1)
        side.rowconfigure(2, weight=1)
        self.lbl_items_chosen_title = label(side, self.t("items_chosen"), font=FONT_SUBTITLE)
        self.lbl_items_chosen_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        self.lbl_selected_items = label(side, self.t("items_none"), fg=COLOR_TEXT_DIM, wraplength=245, justify="left")
        self.lbl_selected_items.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        selected, self.selection_canvas, self.f_selected_cards = self.create_scrollable_tab_frame(side)
        selected.config(highlightthickness=0)
        selected.grid(row=2, column=0, sticky="nsew", padx=8)
        self.btn_clear_items = button(side, self.t("btn_clear"), self.clear_selected_items, fg=COLOR_RED)
        self.btn_clear_items.grid(row=3, column=0, sticky="ew", padx=14, pady=12)
        self._selected_cards = {}
        self.refresh_items_grid()
        return frame

    def _select_rarity(self, value):
        self.rarity_filter.set(value)

    def _on_catalog_resize(self, event):
        columns = max(1, min(4, event.width // 215))
        if columns != self._catalog_columns or event.width != getattr(self, "_catalog_width", None):
            self._catalog_columns = columns
            self._catalog_width = event.width
            self._schedule_catalog_refresh()

    def _schedule_catalog_refresh(self, *_):
        if self._catalog_after is not None:
            self.after_cancel(self._catalog_after)
        self._catalog_after = self.after(90, self.refresh_items_grid)

    def refresh_items_grid(self):
        if self._catalog_after is not None:
            self.after_cancel(self._catalog_after)
            self._catalog_after = None
        query, rarity = search_key(self.search_var.get().strip()), self.rarity_filter.get()
        ids = tuple(tid for kind, _ in RARITIES for tid, item in self._item_records.items()
                    if item[5] == kind and (rarity == "ALL" or rarity == kind) and query in self._item_search[tid])
        layout = (ids, self._catalog_columns)
        if layout != self._catalog_layout:
            for btn in self._item_buttons.values():
                btn.grid_remove()
            self._empty_catalog.grid_remove()
            for col in range(4):
                self.items_grid_frame.columnconfigure(col, weight=1 if col < self._catalog_columns else 0,
                                                       uniform="catalog" if col < self._catalog_columns else "")
            for index, tid in enumerate(ids):
                self._item_buttons[tid].grid(row=index // self._catalog_columns, column=index % self._catalog_columns,
                                             padx=5, pady=4, sticky="ew")
            if not ids:
                self._empty_catalog.grid(row=0, column=0, columnspan=self._catalog_columns, padx=12, pady=30)
            self.items_canvas.yview_moveto(0)
            self._catalog_layout = layout
        selected = {item[0]: i+1 for i, item in enumerate(self.selected_items)}
        for tid, btn in self._item_buttons.items():
            item = self._item_records[tid]
            name = item[4] if self.current_lang == "pt" else item[3] if self.current_lang == "en" else item[2]
            number = selected.get(tid)
            wrap_width = max(100, self.items_canvas.winfo_width() // self._catalog_columns - 75)
            state = (name, number, wrap_width)
            if self._item_presentation.get(tid) != state:
                btn.config(text=f"  {number:02d} · {name}" if number else f"  {name}",
                           bg="#173B3A" if number else COLOR_CARD_ALT,
                           fg=COLOR_GREEN if number else RARITY_COLORS[item[5]],
                           font=FONT_BOLD if number else FONT_BODY,
                           wraplength=wrap_width)
                self._item_presentation[tid] = state
        self.lbl_catalog_count.config(text=self.t("catalog_count", count=len(ids), total=len(self._item_records)))
        for key, btn in self.rarity_buttons.items():
            btn.config(bg=COLOR_BORDER if key == rarity else COLOR_CARD_ALT,
                       fg=RARITY_COLORS.get(key, COLOR_BORDER_GLOW) if key == rarity else COLOR_TEXT_DIM)

    def toggle_item_selection(self, it_id, codename, es_name, en_name, pt_name):
        if self.is_running:
            return
        existing = next((i for i, item in enumerate(self.selected_items) if item[0] == it_id), None)
        if existing is not None:
            self.selected_items.pop(existing)
        elif len(self.selected_items) >= 3:
            messagebox.showinfo(self.t("alert_item_limit_title"), self.t("alert_item_limit_msg"))
            return
        else:
            self.selected_items.append((it_id, codename, es_name, en_name, pt_name))
            if it_id not in self.item_max_prices:
                self.item_max_prices[it_id] = tk.StringVar(self, value="")
        self.update_selected_items_label()
        if existing is not None:
            self.item_max_prices.pop(it_id, None)
        self.refresh_items_grid()
        self.update_tab4_items_label()

    def update_selected_items_label(self):
        active = {item[0] for item in self.selected_items}
        for tid in list(self._selected_cards):
            if tid not in active:
                controls = self._selected_cards.pop(tid)
                controls["var"].trace_remove("write", controls["trace"])
                controls["frame"].destroy()
        self.lbl_selected_items.config(text=self.t("selection_count", count=len(active)) if active else self.t("items_none"),
                                       fg=COLOR_GREEN if active else COLOR_TEXT_DIM)
        for index, item in enumerate(self.selected_items):
            tid, codename = item[:2]
            if tid not in self._selected_cards:
                card = tk.Frame(self.f_selected_cards, bg=COLOR_CARD_ALT, padx=10, pady=12,
                                highlightbackground=COLOR_BORDER, highlightthickness=1)
                card.pack(fill="x", padx=4, pady=(0, 8))
                title = tk.Frame(card, bg=COLOR_CARD_ALT)
                title.pack(fill="x")
                name = label(title, "", font=FONT_BOLD, wraplength=175, justify="left",
                              image=self.item_icons.get(codename), compound="left")
                name.pack(side="left", fill="x", expand=True)
                button(title, "×", lambda data=item: self.toggle_item_selection(*data[:5]),
                       fg=COLOR_RED, padx=5, pady=2).pack(side="right")
                price_label = label(card, "", fg=COLOR_TEXT_DIM, font=FONT_SMALL)
                price_label.pack(anchor="w", pady=(10, 4))
                var = self.item_max_prices[tid]
                entry = tk.Entry(card, textvariable=var, width=8, font=FONT_BOLD, bg=COLOR_BG,
                                 fg=COLOR_GOLD, insertbackground=COLOR_GOLD, relief="flat")
                entry.pack(fill="x", ipady=6)
                hint = label(card, "", font=FONT_CAPTION, wraplength=215, justify="left")
                hint.pack(fill="x", pady=(6, 0))
                trace = var.trace_add("write", lambda *_, item_id=tid: self._update_price_hint(item_id))
                self._selected_cards[tid] = {"frame": card, "name": name, "label": price_label, "hint": hint,
                                             "entry": entry, "var": var, "trace": trace}
            controls = self._selected_cards[tid]
            name = item[4] if self.current_lang == "pt" else item[3] if self.current_lang == "en" else item[2]
            controls["name"].config(text=f"  {index+1:02d} · {name}", fg=RARITY_COLORS[ITEM_BY_ID[tid][5]])
            controls["label"].config(text=self.t("price_max_label") + " · " + self.t("price_gold"))
            self._update_price_hint(tid)

    def _update_price_hint(self, tid):
        controls = self._selected_cards[tid]
        value = controls["var"].get().strip()
        minimum = THEORETICAL_MIN_PRICE[ITEM_BY_ID[tid][5]]
        try:
            number = whole_number(value) if value else 0
        except ValueError:
            number = None
        if number == 0:
            text, color = self.t("price_min_hint", min=minimum), COLOR_TEXT_DIM
        elif number is None:
            text, color = self.t("price_invalid"), COLOR_RED
        elif number < minimum:
            text, color = self.t("price_below_min", min=minimum), COLOR_RED
        else:
            text, color = self.t("price_ok_hint", max=number, min=minimum), COLOR_GREEN
        controls["hint"].config(text=text, fg=color)
        self.update_tab4_items_label()

    def clear_selected_items(self):
        if self.is_running:
            return
        self.selected_items.clear()
        self.update_selected_items_label()
        self.item_max_prices.clear()
        self.refresh_items_grid()
        self.update_tab4_items_label()

    def build_tab2_ui(self):
        outer, self.tab2_canvas, content = self.create_scrollable_tab_frame()
        self.lbl_tab2_title = label(content, self.t("tab2_title"), font=FONT_TITLE)
        self.lbl_tab2_title.pack(anchor="w", padx=20, pady=(18, 12))
        for count in (1, 2, 3):
            card = tk.Frame(content, bg=COLOR_CARD_ALT, padx=18, pady=16,
                            highlightbackground=COLOR_BORDER, highlightthickness=1)
            card.pack(fill="x", padx=20, pady=(0, 10))
            rb = tk.Radiobutton(card, text=self.t(f"gold_opt{count}"), variable=self.target_golden_vendors,
                                value=count, command=self.update_tab4_golden_label, bg=COLOR_CARD_ALT,
                                fg=COLOR_GOLD, selectcolor=COLOR_BG, activebackground=COLOR_CARD_ALT,
                                activeforeground=COLOR_TEXT, font=FONT_SUBTITLE, cursor="hand2")
            rb.pack(anchor="w")
            desc = label(card, self.t(f"gold_opt{count}_desc"), fg=COLOR_TEXT_DIM, wraplength=600, justify="left")
            desc.pack(anchor="w", padx=24, pady=(4, 0))
            setattr(self, f"rb_gold{count}", rb)
            setattr(self, f"lbl_gold{count}_desc", desc)
        return outer

    def build_tab4_ui(self):
        outer, self.tab4_canvas, content = self.create_scrollable_tab_frame()
        self.lbl_tab4_title = label(content, self.t("tab4_title"), font=FONT_TITLE)
        self.lbl_tab4_title.pack(anchor="w", padx=20, pady=(18, 12))
        self.lbl_tier_sec_title = label(content, self.t("tier_title"), font=FONT_SUBTITLE)
        self.lbl_tier_sec_title.pack(anchor="w", padx=20, pady=(0, 6))
        tiers = tk.Frame(content, bg=COLOR_CARD)
        tiers.pack(fill="x", padx=20)
        self.tier_buttons = {}
        for index, tier in enumerate(("Light", "Good", "Perfect", "Perfect+")):
            info = TIER_INFO[tier]
            rb = tk.Radiobutton(tiers, text=f"{tier}\n≥ {info['min_score']:g} pts", variable=self.target_tier,
                                value=tier, indicatoron=False, command=self.on_select_tier,
                                bg=COLOR_CARD_ALT, fg=info["color"], selectcolor=COLOR_BORDER,
                                activebackground=COLOR_BORDER, activeforeground=COLOR_TEXT,
                                font=FONT_BOLD, relief="flat", borderwidth=0, pady=10, cursor="hand2")
            rb.grid(row=0, column=index, sticky="ew", padx=(0, 6))
            tiers.columnconfigure(index, weight=1, uniform="tier")
            self.tier_buttons[tier] = rb
        self.lbl_preset_sec_title = label(content, self.t("preset_title"), font=FONT_SUBTITLE)
        self.lbl_preset_sec_title.pack(anchor="w", padx=20, pady=(16, 4))
        self.lbl_forest_title = label(content, self.t("preset_sec_forest"), fg=COLOR_TEXT_DIM, font=FONT_SMALL)
        self.lbl_forest_title.pack(anchor="w", padx=20, pady=(0, 6))
        presets = tk.Frame(content, bg=COLOR_CARD)
        presets.pack(fill="x", padx=16)
        for col in (0, 1):
            presets.columnconfigure(col, weight=1, uniform="preset")
        self.preset_buttons = {}
        for index, (pid, tmpl) in enumerate(PRESET_TEMPLATES.items()):
            btn = button(presets, self.t(PRESET_KEYS[pid]), lambda value=pid: self.apply_preset_template(value),
                         anchor="w", font=FONT_BOLD, wraplength=310, pady=12,
                         fg=TIER_INFO.get(tmpl["tier"], {}).get("color", COLOR_PURPLE))
            btn.grid(row=index//2, column=index%2, sticky="nsew", padx=4, pady=4,
                     columnspan=2 if pid == "graveyard_bald_heads" else 1)
            btn.bind("<Enter>", lambda e, value=pid: self.on_preset_hover(value))
            btn.bind("<Leave>", lambda e: self.on_preset_leave())
            self.preset_buttons[pid] = btn
        detail = tk.Frame(content, bg=COLOR_CARD_ALT, padx=14, pady=12)
        detail.pack(fill="x", padx=20, pady=12)
        self.lbl_preset_active = label(detail, "", font=FONT_BOLD, wraplength=650)
        self.lbl_preset_active.pack(fill="x")
        self.lbl_preset_hover_title = label(detail, self.t("preset_hover_hint"), fg=COLOR_BORDER_GLOW, font=FONT_BOLD, wraplength=650)
        self.lbl_preset_hover_title.pack(fill="x", pady=(8, 4))
        self.lbl_preset_hover_desc = label(detail, self.t("preset_hover_default"), fg=COLOR_TEXT_DIM, wraplength=650, justify="left")
        self.lbl_preset_hover_desc.pack(fill="x")
        detail.bind("<Configure>", lambda e: [lbl.config(wraplength=max(200, e.width-32)) for lbl in
                    (self.lbl_preset_active, self.lbl_preset_hover_title, self.lbl_preset_hover_desc)])
        combo = tk.Frame(content, bg=COLOR_CARD_ALT, padx=14, pady=12)
        combo.pack(fill="x", padx=20, pady=(0, 12))
        self.chk_combo = tk.Checkbutton(combo, text=self.t("combo_chk"), variable=self.require_mode1_items,
                                        command=self.update_tab4_items_label, bg=COLOR_CARD_ALT, fg=COLOR_TEXT,
                                        selectcolor=COLOR_BG, activebackground=COLOR_CARD_ALT,
                                        activeforeground=COLOR_TEXT, font=FONT_BOLD, cursor="hand2")
        self.chk_combo.pack(anchor="w")
        self.lbl_tab4_items_preview = label(combo, self.t("combo_none"), fg=COLOR_TEXT_DIM, wraplength=620, justify="left")
        self.lbl_tab4_items_preview.pack(fill="x", padx=5, pady=(2, 8))
        self.chk_combo_golden = tk.Checkbutton(combo, text=self.t("combo_golden_chk"), variable=self.require_golden_vendors,
                                               command=self.update_tab4_golden_label, bg=COLOR_CARD_ALT, fg=COLOR_GOLD,
                                               selectcolor=COLOR_BG, activebackground=COLOR_CARD_ALT,
                                               activeforeground=COLOR_TEXT, font=FONT_BOLD, cursor="hand2")
        self.chk_combo_golden.pack(anchor="w")
        row = tk.Frame(combo, bg=COLOR_CARD_ALT)
        row.pack(anchor="w", padx=5, pady=5)
        for count in (1, 2, 3):
            rb = tk.Radiobutton(row, text=str(count), variable=self.target_golden_vendors, value=count,
                                command=self.update_tab4_golden_label, indicatoron=False, bg=COLOR_CARD,
                                selectcolor=COLOR_BORDER, fg=COLOR_GOLD, activebackground=COLOR_BORDER,
                                activeforeground=COLOR_TEXT, font=FONT_BOLD, padx=18, pady=5, relief="flat", borderwidth=0)
            rb.pack(side="left", padx=(0, 6))
            setattr(self, f"rb_tab4_g{count}", rb)
        self.lbl_tab4_golden_preview = label(combo, "", fg=COLOR_TEXT_DIM)
        self.lbl_tab4_golden_preview.pack(fill="x", padx=5)
        self.update_tab4_golden_label()
        score = tk.Frame(content, bg=COLOR_CARD_ALT, padx=14, pady=12)
        score.pack(fill="x", padx=20, pady=(0, 16))
        self.lbl_score_meter_title = label(score, self.t("score_meter_title"), fg=COLOR_TEXT_DIM, font=FONT_SMALL)
        self.lbl_score_meter_title.pack(anchor="w")
        self.lbl_live_score_val = label(score, self.t("score_waiting"), font=FONT_SUBTITLE, fg=COLOR_GOLD)
        self.lbl_live_score_val.pack(anchor="w", pady=(4, 0))
        return outer

    def update_menu_language(self):
        self.btn_audit_powerups.config(text=self.t("audit_hud"))
        for key, i18n in [("ALL", "rarity_all")] + RARITIES:
            self.rarity_buttons[key].config(text=self.t(i18n))
        self._empty_catalog.config(text=self.t("catalog_empty"))

    def preset_details(self, preset_id):
        template = PRESET_TEMPLATES.get(preset_id)
        if not template:
            return None
        requirements = [f"{self.t('stat_score')} ≥ {template['min_score']:g}"]
        for key, label_key in (("min_moais", "stat_moais"), ("min_vendors", "stat_vendors"),
                               ("min_microwaves", "stat_micros"), ("min_white_microwaves", "white_microwaves"),
                               ("min_boss", "stat_curses"), ("min_bald_heads", "bald_heads")):
            minimum = template.get(key, 0)
            if minimum:
                requirements.append(f"{self.t(label_key)} ≥ {minimum}")
        tier = template["tier"]
        return {"title": self.t(PRESET_KEYS[preset_id]),
                "tier": f"{self.t('stat_tier')} ≥ {tier}" if tier != "Normal" else self.t("preset_sec_graveyard"),
                "reqs": "\n".join(requirements)}

    def update_preset_selection(self):
        template_mode = self.score_submode.get() == "template"
        for pid, btn in self.preset_buttons.items():
            selected = template_mode and pid == self.selected_template.get()
            btn.config(bg="#173B3A" if selected else COLOR_CARD_ALT,
                       relief="flat", highlightthickness=1,
                       highlightbackground=COLOR_GREEN if selected else COLOR_CARD_ALT)
        for tier, btn in self.tier_buttons.items():
            btn.config(fg=COLOR_TEXT_DIM if template_mode else TIER_INFO[tier]["color"])

    def set_menu_editable(self, editable):
        """Keep the visible target consistent with the worker's captured settings."""
        editable = editable and not self.is_running
        state = "normal" if editable else "disabled"
        def visit(widget):
            if isinstance(widget, (tk.Button, tk.Radiobutton, tk.Checkbutton, tk.Entry, tk.Spinbox)):
                widget.config(state=state)
            for child in widget.winfo_children():
                visit(child)
        visit(self.content_container)
        for btn in (self.btn_tab1, self.btn_tab2, self.btn_tab4):
            btn.config(state=state)
        self.btn_test_reset.config(state=state)
