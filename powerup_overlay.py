"""
MB Helper - Overlay Flotante de Powerups (DirectX / MPO Native Mode)
Ventana compacta sin bordes, fondo negro mate, números blancos y esquinas redondeadas.
Se puede mover a cualquier parte de la pantalla y recuerda su posición.
Atajo global F6 para activar / desactivar.

Arquitectura de Cero Impacto en DirectX (Solución de Desenfoque y Frame Pacing):
1. NO utiliza WS_EX_LAYERED ni LWA_COLORKEY (-transparentcolor).
   Las ventanas colorkey fuerzan a Windows DWM a desactivar el Multi-Plane Overlay (MPO)
   y el DirectX Independent Flip Model, causando judder de presentación y desenfoque
   de movimiento multiplicado (ghosting retiniano) en monitores de 144Hz / G-Sync.
2. Utiliza redondeo nativo de hardware de Windows 11 (DWMWA_WINDOW_CORNER_PREFERENCE).
3. Borde de hardware DWM (DWMWA_BORDER_COLOR).
4. Estilos WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST.
5. Elementos GDI persistentes in-place y comprobación delta (0 repintados en reposo).
"""

import tkinter as tk
import json
import os
import time
import ctypes
from ctypes import wintypes

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "overlay_position.json")

# Constantes de la API de Windows DWM y User32
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWCP_ROUND = 2  # Esquinas redondeadas suaves nativas de Windows 11

COLOR_BG = "#101115"
COLOR_OUTLINE_NORMAL = "#252630"
COLOR_OUTLINE_CRITICAL = "#FF1744"
COLOR_OUTLINE_WARNING = "#FFEA00"

DWM_COLOR_NORMAL = 0x00302625      # BGR para #252630
DWM_COLOR_CRITICAL = 0x004417FF    # BGR para #FF1744
DWM_COLOR_WARNING = 0x0000EAFF     # BGR para #FFEA00

class PowerupOverlay:
    def __init__(self, master=None):
        self.master = master
        self.window = tk.Toplevel(master)
        self.is_visible = True

        # Configuración de ventana flotante sin bordes
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.config(bg=COLOR_BG)

        # Dimensiones compactas HUD (130 x 42)
        self.width = 130
        self.height = 42

        # Cargar posición guardada o centrar arriba
        self.pos_x, self.pos_y = self._load_position()
        self.window.geometry(f"{self.width}x{self.height}+{self.pos_x}+{self.pos_y}")

        # Canvas para dibujo in-place
        self.canvas = tk.Canvas(
            self.window,
            width=self.width,
            height=self.height,
            bg=COLOR_BG,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Drag and Drop
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # Aplicar estilos nativos DWM (Sin WS_EX_LAYERED para no romper DirectX Flip/MPO)
        self._apply_native_dwm_styles()

        # Geometría de barra de progreso
        self.bar_x1 = 16
        self.bar_max_x2 = self.width - 16
        self.bar_y = 33
        self.bar_len = self.bar_max_x2 - self.bar_x1

        # Elementos GDI persistentes creados UNA SOLA VEZ
        self.card_id = self._draw_rounded_card(
            1, 1, self.width - 2, self.height - 2, radius=10, fill=COLOR_BG, outline=COLOR_OUTLINE_NORMAL
        )
        self.text_id = self.canvas.create_text(
            self.width // 2, 17,
            text="00:00",
            font=("Consolas", 18, "bold"),
            fill="#FFFFFF"
        )
        self.bar_bg_id = self.canvas.create_line(
            self.bar_x1, self.bar_y, self.bar_max_x2, self.bar_y,
            fill="#1c1d24", width=3, capstyle=tk.ROUND
        )
        self.bar_fg_id = self.canvas.create_line(
            self.bar_x1, self.bar_y, self.bar_x1, self.bar_y,
            fill="#00E5FF", width=3, capstyle=tk.ROUND, state="hidden"
        )

        # Estado de caché delta (Evita repintados innecesarios)
        self._is_idle = True
        self._last_text = "00:00"
        self._last_time_color = "#FFFFFF"
        self._last_card_outline = COLOR_OUTLINE_NORMAL
        self._last_bar_x2 = self.bar_x1
        self._last_bar_color = "#00E5FF"
        self._last_bar_visible = False

        self._blink_state = False
        self._last_blink_time = 0.0

    def _get_hwnd(self):
        try:
            self.window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            return hwnd if hwnd else self.window.winfo_id()
        except Exception:
            return None

    def _apply_native_dwm_styles(self):
        """
        Configura el HWND con estilos nativos de DirectComposition:
        - WS_EX_NOACTIVATE: No roba foco ni confunde a G-Sync en modo ventana.
        - WS_EX_TOOLWINDOW: No genera entrada en la barra de tareas ni Alt+Tab.
        - WS_EX_TOPMOST: Siempre visible sobre el juego.
        - ELIMINA WS_EX_LAYERED: Permite a DirectX mantener Hardware MPO y Independent Flip a 140 FPS.
        - DWMWA_WINDOW_CORNER_PREFERENCE: Esquinas redondeadas por hardware.
        - DWMWA_BORDER_COLOR: Borde nativo acelerado por GPU.
        """
        hwnd = self._get_hwnd()
        if not hwnd:
            return

        try:
            # 1. Estilos extendidos Win32
            cur_ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_ex = (cur_ex | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~WS_EX_LAYERED
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex)

            # 2. Modo Oscuro Nativo DWM
            dark_mode = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
            )

            # 3. Esquinas redondeadas por hardware (Windows 11)
            corner_pref = ctypes.c_int(DWMWCP_ROUND)
            hr_corners = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner_pref), ctypes.sizeof(corner_pref)
            )

            # Fallback de región para Windows 10 si DWM no soporta DWMWA_WINDOW_CORNER_PREFERENCE
            if hr_corners != 0:
                hrgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, self.width + 1, self.height + 1, 14, 14)
                ctypes.windll.user32.SetWindowRgn(hwnd, hrgn, True)

            # 4. Color de borde nativo DWM
            border_color = ctypes.c_uint(DWM_COLOR_NORMAL)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color)
            )
        except Exception:
            pass

    def _set_dwm_border_color(self, bgr_color):
        hwnd = self._get_hwnd()
        if not hwnd:
            return
        try:
            c = ctypes.c_uint(bgr_color)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_BORDER_COLOR, ctypes.byref(c), ctypes.sizeof(c)
            )
        except Exception:
            pass

    def _load_position(self):
        default_x = 100
        default_y = 80
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return int(data.get("x", default_x)), int(data.get("y", default_y))
        except Exception:
            pass
        return default_x, default_y

    def _save_position(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"x": self.pos_x, "y": self.pos_y}, f)
        except Exception:
            pass

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        deltax = event.x - self._drag_start_x
        deltay = event.y - self._drag_start_y
        new_x = self.window.winfo_x() + deltax
        new_y = self.window.winfo_y() + deltay
        self.pos_x = new_x
        self.pos_y = new_y
        self.window.geometry(f"+{new_x}+{new_y}")

    def _on_drag_end(self, event):
        self._save_position()

    def toggle(self):
        """Activa o desactiva la visibilidad del overlay (F6)"""
        if self.is_visible:
            self.window.withdraw()
            self.is_visible = False
        else:
            self.window.deiconify()
            self.window.lift()
            self.is_visible = True
            self._apply_native_dwm_styles()
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

    def _draw_rounded_card(self, x1, y1, x2, y2, radius=10, fill=COLOR_BG, outline=COLOR_OUTLINE_NORMAL):
        """Dibuja un rectángulo con esquinas redondeadas suaves persistente"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=1.2)

    def render_idle(self):
        """
        Estado en reposo sin powerups activos (00:00).
        Si ya está en reposo, retorno inmediato (0 llamadas GDI, 0 costo CPU/DWM).
        """
        if self._is_idle:
            return

        self.canvas.itemconfig(self.card_id, fill=COLOR_BG, outline=COLOR_OUTLINE_NORMAL)
        self.canvas.itemconfig(self.text_id, text="00:00", fill="#FFFFFF")
        self.canvas.itemconfig(self.bar_bg_id, fill="#1c1d24")
        self.canvas.itemconfig(self.bar_fg_id, state="hidden")
        self._set_dwm_border_color(DWM_COLOR_NORMAL)

        self._is_idle = True
        self._last_text = "00:00"
        self._last_time_color = "#FFFFFF"
        self._last_card_outline = COLOR_OUTLINE_NORMAL
        self._last_bar_visible = False
        self._last_bar_x2 = self.bar_x1

    def update_data(self, powerups_data):
        """
        Actualiza el HUD con la información leída en tiempo real.
        Usa actualizaciones delta in-place (itemconfig / coords) para no invalidar el pipeline DWM.
        """
        if not self.is_visible:
            return

        powerups = powerups_data.get("powerups", []) if powerups_data else []

        if not powerups:
            self.render_idle()
            return

        # Priorizar siempre el Reloj si está activo, sino el que tenga menor tiempo
        p = powerups[0]
        remaining = p.get("remaining", 0.0)
        pct = max(0.0, min(1.0, p.get("pct", 1.0)))
        bar_color = p.get("color", "#00E5FF")
        is_clock = p.get("is_clock", False)
        is_critical = p.get("is_critical", False)

        now = time.time()
        if now - self._last_blink_time >= 0.20:
            self._blink_state = not self._blink_state
            self._last_blink_time = now

        # Color del texto de tiempo: Blanco por defecto, parpadeo en últimos 2s
        if is_critical and is_clock:
            time_color = "#FF1744" if self._blink_state else "#FFEA00"
            card_outline = COLOR_OUTLINE_CRITICAL if self._blink_state else "#601010"
            dwm_border = DWM_COLOR_CRITICAL if self._blink_state else DWM_COLOR_NORMAL
            bar_color = "#FF1744"
        elif is_critical:
            time_color = "#FFEA00"
            card_outline = COLOR_OUTLINE_WARNING
            dwm_border = DWM_COLOR_WARNING
        else:
            time_color = "#FFFFFF"
            card_outline = COLOR_OUTLINE_NORMAL
            dwm_border = DWM_COLOR_NORMAL

        # Formato de tiempo: '04.2s' o '00:04'
        if remaining >= 60.0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            time_str = f"{mins:02d}:{secs:02d}"
        else:
            time_str = f"{remaining:04.1f}s"

        self._is_idle = False

        # 1. Delta en Texto / Color
        if time_str != self._last_text or time_color != self._last_time_color:
            self.canvas.itemconfig(self.text_id, text=time_str, fill=time_color)
            self._last_text = time_str
            self._last_time_color = time_color

        # 2. Delta en Borde de Tarjeta y Borde DWM
        if card_outline != self._last_card_outline:
            self.canvas.itemconfig(self.card_id, fill=COLOR_BG, outline=card_outline)
            self._set_dwm_border_color(dwm_border)
            self._last_card_outline = card_outline

        # 3. Delta en Barra de Progreso
        active_x2 = self.bar_x1 + int(self.bar_len * pct)
        if active_x2 > self.bar_x1 + 1:
            if active_x2 != self._last_bar_x2:
                self.canvas.coords(self.bar_fg_id, self.bar_x1, self.bar_y, active_x2, self.bar_y)
                self._last_bar_x2 = active_x2
            if not self._last_bar_visible or bar_color != self._last_bar_color:
                self.canvas.itemconfig(self.bar_fg_id, fill=bar_color, state="normal")
                self._last_bar_color = bar_color
                self._last_bar_visible = True
        else:
            if self._last_bar_visible:
                self.canvas.itemconfig(self.bar_fg_id, state="hidden")
                self._last_bar_visible = False
