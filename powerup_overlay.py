"""Compact, opaque powerup timers: one colored number per active effect."""

import ctypes
from ctypes import wintypes
import json
import math
import os
import tkinter as tk
from tkinter import font as tkfont

from runtime_paths import data_path

CONFIG_PATH = data_path("overlay_position.json")
user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
gdi32 = ctypes.windll.gdi32
user32.GetParent.argtypes = [wintypes.HWND]
user32.GetParent.restype = wintypes.HWND
user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
gdi32.CreateRoundRectRgn.restype = wintypes.HANDLE
user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HANDLE, wintypes.BOOL]
user32.SetWindowRgn.restype = ctypes.c_int
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWCP_ROUND = 2
DWM_COLOR_NONE = 0xFFFFFFFE

COLOR_BG = "#08090B"
COLOR_IDLE = "#D8DEE9"
POWERUP_COLORS = {
    "Clock": "#00E5FF",
    "Shield": "#76FF03",
    "Rage": "#B56CFF",
    "Haste": "#FF9F1C",
    "Stonks": "#FFD700",
}
POWERUP_BY_ID = {1: "Rage", 2: "Shield", 3: "Stonks", 4: "Clock",
                 5: "Shield", 6: "Rage", 7: "Haste", 8: "Stonks"}
# Stable positions as timers cross, without reordering on every update.
POWERUP_ORDER = {name: index for index, name in enumerate(POWERUP_COLORS)}


class PowerupOverlay:
    def __init__(self, master=None):
        self.master = master
        self.language = "es"  # Compatibility with the main UI; no labels are drawn.
        self._hwnd = None
        self._use_region = False
        self.window = tk.Toplevel(master)
        self.is_visible = True
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.config(bg=COLOR_BG)

        self.timer_font = tkfont.Font(self.window, family="Consolas", size=18, weight="bold")
        self._fonts = {18: self.timer_font}
        self.padding_x = 4
        self.gap = 4
        self.slot_width = self.timer_font.measure("00:00") + 2 * self.padding_x
        self.width = self.slot_width
        self.height = self.timer_font.metrics("linespace") + 4
        self._counter_count = 1
        self.pos_x, self.pos_y = self._load_position()
        self.window.geometry(f"{self.width}x{self.height}+0+0")

        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height,
                                bg=COLOR_BG, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)
        self._timer_ids = []
        for index in range(5):
            self._timer_ids.append(self.canvas.create_text(
                index * (self.slot_width + self.gap) + self.slot_width / 2, self.height / 2,
                text="00:00" if index == 0 else "", font=self.timer_font,
                fill=COLOR_IDLE, state="normal" if index == 0 else "hidden",
            ))
        self.text_id = self._timer_ids[0]
        self._last_counters = (("00:00", COLOR_IDLE),)
        self._is_idle = True

        self._drag_start_x = self._drag_start_y = 0
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._apply_native_dwm_styles()
        self._move_window(self.pos_x, self.pos_y)

    def _get_hwnd(self):
        if self._hwnd:
            return self._hwnd
        try:
            self.window.update_idletasks()
            self._hwnd = user32.GetParent(self.window.winfo_id()) or self.window.winfo_id()
            return self._hwnd
        except tk.TclError:
            return None

    def _apply_native_dwm_styles(self):
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        styles = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        styles = (styles | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~WS_EX_LAYERED
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, styles)
        for attribute, value in ((DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
                                 (DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND),
                                 (DWMWA_BORDER_COLOR, DWM_COLOR_NONE)):
            data = ctypes.c_uint(value)
            result = dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(data), ctypes.sizeof(data))
            if attribute == DWMWA_WINDOW_CORNER_PREFERENCE:
                self._use_region = result != 0
        if self._use_region:
            self._update_native_region()

    def _update_native_region(self):
        region = gdi32.CreateRoundRectRgn(0, 0, self.width + 1, self.height + 1, 8, 8)
        if region and not user32.SetWindowRgn(self._get_hwnd(), region, True):
            gdi32.DeleteObject(region)

    def _load_position(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as stream:
                data = json.load(stream)
                return int(data.get("x", 100)), int(data.get("y", 80))
        except (OSError, ValueError, TypeError, AttributeError):
            return 100, 80

    def _save_position(self):
        try:
            with open(CONFIG_PATH + ".tmp", "w", encoding="utf-8") as stream:
                json.dump({"x": self.pos_x, "y": self.pos_y}, stream)
            os.replace(CONFIG_PATH + ".tmp", CONFIG_PATH)
        except OSError:
            pass

    def _on_drag_start(self, event):
        self._drag_start_x, self._drag_start_y = event.x, event.y

    def _on_drag_motion(self, event):
        self._move_window(self.window.winfo_x() + event.x - self._drag_start_x,
                          self.window.winfo_y() + event.y - self._drag_start_y)

    def _on_drag_end(self, event):
        self._save_position()

    def _move_window(self, x, y):
        left, top = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
        screen_w, screen_h = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
        self.pos_x = max(left, min(int(x), left + max(0, screen_w - self.width)))
        self.pos_y = max(top, min(int(y), top + max(0, screen_h - self.height)))
        hwnd = self._get_hwnd()
        if hwnd:
            user32.SetWindowPos(hwnd, ctypes.c_void_p(-1), self.pos_x, self.pos_y, 0, 0, 0x0011)

    def toggle(self):
        self.hide() if self.is_visible else self.show()
        return self.is_visible

    def show(self):
        if not self.is_visible:
            self.window.deiconify()
            self.window.lift()
            self.is_visible = True
            self._apply_native_dwm_styles()

    def hide(self):
        if self.is_visible:
            self.window.withdraw()
            self.is_visible = False

    def _font_for_text(self, text):
        available = self.slot_width - 2 * self.padding_x
        size = 18
        while self._fonts[size].measure(text) > available and size > 6:
            size -= 1
            if size not in self._fonts:
                self._fonts[size] = tkfont.Font(self.window, family="Consolas", size=size, weight="bold")
        return self._fonts[size]

    def _render_counters(self, counters):
        if counters == self._last_counters:
            return
        count = len(counters)
        while len(self._timer_ids) < count:
            index = len(self._timer_ids)
            self._timer_ids.append(self.canvas.create_text(
                index * (self.slot_width + self.gap) + self.slot_width / 2, self.height / 2,
                font=self.timer_font, state="hidden",
            ))
        if count != self._counter_count:
            self.width = count * self.slot_width + (count - 1) * self.gap
            self.window.geometry(f"{self.width}x{self.height}")
            self._counter_count = count
            if self._use_region:
                self._update_native_region()
            self._move_window(self.pos_x, self.pos_y)
        for index, (text, color) in enumerate(counters):
            previous = self._last_counters[index] if index < len(self._last_counters) else None
            if previous != (text, color):
                self.canvas.itemconfig(self._timer_ids[index], text=text, fill=color,
                                       font=self._font_for_text(text), state="normal")
        for index in range(count, len(self._last_counters)):
            self.canvas.itemconfig(self._timer_ids[index], state="hidden")
        self._last_counters = counters

    def render_idle(self):
        if self._is_idle:
            return
        self._render_counters((("00:00", COLOR_IDLE),))
        self._is_idle = True

    @staticmethod
    def _kind(powerup):
        return powerup.get("codename") or POWERUP_BY_ID.get(powerup.get("id"), "")

    @staticmethod
    def _format_time(remaining):
        if remaining >= 60:
            minutes, seconds = divmod(int(remaining), 60)
            return f"{minutes:02d}:{seconds:02d}"
        return f"{remaining:04.1f}s"

    def update_data(self, powerups_data):
        if not self.is_visible:
            return
        powerups = powerups_data.get("powerups", []) if powerups_data and powerups_data.get("valid") else []
        powerups = [p for p in powerups if isinstance(p.get("remaining"), (int, float))
                    and math.isfinite(p["remaining"]) and p["remaining"] > 0]
        if not powerups:
            self.render_idle()
            return
        powerups.sort(key=lambda p: (POWERUP_ORDER.get(self._kind(p), len(POWERUP_ORDER)),
                                     str(p.get("id", ""))))
        counters = tuple((self._format_time(p["remaining"]), POWERUP_COLORS.get(self._kind(p), COLOR_IDLE))
                         for p in powerups)
        self._render_counters(counters)
        self._is_idle = False
