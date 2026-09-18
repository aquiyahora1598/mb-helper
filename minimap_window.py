"""
Megabonk Helper - Minimapa Táctico Cuadrado Always-On-Top [F6]
Mapa cuadrado 1:1 fiel a la isla de Megabonk con cuadrícula táctica de sectores,
posicionamiento exacto de todos los interactuables (Moáis, Vendedores, Santuarios,
Maldiciones, Desafíos y Microondas) y cero sobrecarga de CPU / 0% lag en DirectX.
"""

import tkinter as tk
from tkinter import ttk
import math
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = -1
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008
SW_SHOWNOACTIVATE = 4

BG_COLOR = "#0B0F19"
CARD_BG = "#131C2E"
CANVAS_BG = "#090D16"
TERRAIN_BG = "#0E1626"
GRID_COLOR = "#1C2B46"
BORDER_COLOR = "#2D3F63"
BORDER_HIGHLIGHT = "#38BDF8"
TEXT_COLOR = "#F1F5F9"
DIM_COLOR = "#94A3B8"
ACCENT_BLUE = "#38BDF8"
ACCENT_GOLD = "#F59E0B"
ACCENT_PURPLE = "#A855F7"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"

FONT_HEADER = ("Bahnschrift SemiBold", 10)
FONT_BADGE = ("Segoe UI", 8, "bold")
FONT_LABEL = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 8, "bold")
FONT_TOOLTIP = ("Segoe UI", 9)
FONT_COMPASS = ("Bahnschrift", 9, "bold")
FONT_SECTOR = ("Bahnschrift", 7)
FONT_ITEM = ("Segoe UI", 8)


class MinimapTooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show(self, text, x, y):
        self.hide()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.configure(bg="#0F172A")

        label = tk.Label(
            tw,
            text=text,
            justify="left",
            background="#0F172A",
            foreground="#F8FAFC",
            font=FONT_TOOLTIP,
            relief="solid",
            borderwidth=1,
            padx=9,
            pady=6
        )
        label.pack()
        tw.wm_geometry(f"+{x + 14}+{y + 14}")

    def hide(self):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


MINIMAP_I18N = {
    "es": {
        "title": "MB Helper - Minimapa [F6]",
        "header": "🗺️ MAPA TÁCTICO",
        "hotkeys": "[F6 Alternar]  [Clic Der: Limpiar]",
        "you": "TÚ",
        "you_pos": "🟢 Tu Posición",
        "beacon": "🚩 Baliza #{num}",
        "empty": "Radar táctico activo.\nAcércate a interactuables para detectarlos\no haz clic para colocar una baliza 🚩.",
        "coords": "Coords: ({x:.1f}, {z:.1f})"
    },
    "en": {
        "title": "MB Helper - Minimap [F6]",
        "header": "🗺️ TACTICAL MAP",
        "hotkeys": "[F6 Toggle]  [Right Click: Clear]",
        "you": "YOU",
        "you_pos": "🟢 Your Position",
        "beacon": "🚩 Beacon #{num}",
        "empty": "Tactical radar active.\nApproach interactables to detect them\nor click to place a beacon 🚩.",
        "coords": "Coords: ({x:.1f}, {z:.1f})"
    },
    "pt": {
        "title": "MB Helper - Minimapa [F6]",
        "header": "🗺️ MAPA TÁTICO",
        "hotkeys": "[F6 Alternar]  [Clique Dir: Limpar]",
        "you": "VOCÊ",
        "you_pos": "🟢 Sua Posição",
        "beacon": "🚩 Sinalizador #{num}",
        "empty": "Radar tático ativo.\nAproxime-se de estruturas para detectá-las\nou clique para colocar um sinalizador 🚩.",
        "coords": "Coords: ({x:.1f}, {z:.1f})"
    }
}


class MinimapWindow(tk.Toplevel):
    def __init__(self, parent, landmarks=None, stats=None, vendors=None, map_bounds=None, lang="es"):
        super().__init__(parent)
        self.parent = parent
        self.lang = lang
        self.landmarks = landmarks or []
        self.stats = stats or {}
        self.vendors = vendors or []
        self.map_bounds = map_bounds or {"min_x": -300.0, "max_x": 300.0, "min_z": -300.0, "max_z": 300.0}

        self.title(self.t("title"))
        self.geometry("450x480")
        self.minsize(360, 360)
        self.configure(bg=BG_COLOR)

        # Always-On-Top para permanecer visible sobre el juego
        self.attributes("-topmost", True)
        self._is_visible = True

        self.tooltip = MinimapTooltip(self)
        self.drawn_landmarks = []  # (cx, cy, radius, landmark_dict)
        self.player_pos = None
        self.manual_markers = []

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Redibujar cuando cambie de tamaño y gestionar ratón
        self.canvas.bind("<Configure>", lambda e: self.draw_minimap())
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        self.canvas.bind("<Leave>", lambda e: self.tooltip.hide())
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        # Vínculo directo con F6 en la misma ventana del minimapa
        self.bind("<F6>", lambda e: self.toggle_visibility())

        self.update_content()

    def t(self, key, **kwargs):
        lang_dict = MINIMAP_I18N.get(self.lang, MINIMAP_I18N["es"])
        val = lang_dict.get(key, MINIMAP_I18N["es"].get(key, key))
        return val.format(**kwargs) if kwargs else val

    def set_language(self, lang):
        self.lang = lang
        self.title(self.t("title"))
        if hasattr(self, "lbl_title"):
            self.lbl_title.config(text=self.t("header"))
        if hasattr(self, "lbl_hotkey"):
            self.lbl_hotkey.config(text=self.t("hotkeys"))
        self.draw_minimap()

    def setup_ui(self):
        # 1. Barra Superior Compacta (Solo Título y Atajos)
        top_bar = tk.Frame(self, bg=BG_COLOR, padx=10, pady=5)
        top_bar.pack(fill="x")

        self.lbl_title = tk.Label(
            top_bar,
            text=self.t("header"),
            font=FONT_HEADER,
            bg=BG_COLOR,
            fg=ACCENT_BLUE
        )
        self.lbl_title.pack(side="left")

        # Label dummy para retrocompatibilidad
        self.lbl_count = tk.Label(top_bar, text="", bg=BG_COLOR, fg=BG_COLOR)

        self.lbl_hotkey = tk.Label(
            top_bar,
            text=self.t("hotkeys"),
            font=FONT_LABEL,
            bg=BG_COLOR,
            fg=DIM_COLOR
        )
        self.lbl_hotkey.pack(side="right", padx=4)

        # 2. Contenedor del Canvas Cuadrado 1:1 que Ocupa Toda la Ventana
        map_container = tk.Frame(self, bg=BORDER_COLOR, padx=1, pady=1)
        map_container.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        self.canvas = tk.Canvas(
            map_container,
            bg=CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)

    def on_canvas_click(self, event):
        """Permite colocar o retirar una baliza táctica personalizada con clic izquierdo."""
        min_x = self.map_bounds.get("min_x", -300.0)
        max_x = self.map_bounds.get("max_x", 300.0)
        min_z = self.map_bounds.get("min_z", -300.0)
        max_z = self.map_bounds.get("max_z", 300.0)
        span_x = max(max_x - min_x, 1.0)
        span_z = max(max_z - min_z, 1.0)

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        map_size = max(min(w, h) - 24, 100)
        ox = (w - map_size) // 2
        oy = (h - map_size) // 2

        cx, cy = event.x, event.y
        norm_x = (cx - ox) / map_size
        norm_z = 1.0 - ((cy - oy) / map_size)

        if 0.0 <= norm_x <= 1.0 and 0.0 <= norm_z <= 1.0:
            wx = round(min_x + norm_x * span_x, 1)
            wz = round(min_z + norm_z * span_z, 1)

            # Si se hace clic sobre un marcador manual existente, eliminarlo
            for i, m in enumerate(self.manual_markers):
                if math.hypot(wx - m["x"], wz - m["z"]) < 25.0:
                    self.manual_markers.pop(i)
                    self.draw_minimap()
                    return

            # Agregar nueva baliza táctica
            num = len(self.manual_markers) + 1
            self.manual_markers.append({
                "type": "marker",
                "label": self.t("beacon", num=num),
                "icon": "🚩",
                "color": "#E11D48",
                "x": wx,
                "z": wz,
                "has_coords": True
            })
            self.draw_minimap()

    def on_canvas_right_click(self, event):
        """Clic derecho borra todas las balizas manuales."""
        if self.manual_markers:
            self.manual_markers.clear()
            self.draw_minimap()

    def set_player_pos(self, pos):
        """Actualiza la posición en vivo del jugador y redibuja."""
        if self.player_pos != pos:
            self.player_pos = pos
            self.draw_minimap()

    def set_data(self, landmarks, stats=None, vendors=None, map_bounds=None, player_pos=None):
        """Actualiza todos los datos del minimapa y redibuja inmediatamente."""
        self.landmarks = landmarks or []
        self.stats = stats or {}
        self.vendors = vendors or []
        if map_bounds:
            self.map_bounds = map_bounds
        if player_pos is not None:
            self.player_pos = player_pos
        self.update_content()

    def set_landmarks(self, landmarks):
        """Compatibilidad con llamadas legacy."""
        self.landmarks = landmarks or []
        self.update_content()

    def set_status(self, text):
        """Muestra un mensaje de estado en el canvas."""
        self.canvas.delete("all")
        self.drawn_landmarks = []
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50 or h < 50:
            w, h = 420, 310
        self.canvas.create_text(
            w // 2, h // 2,
            text=text,
            fill=ACCENT_BLUE,
            font=FONT_LABEL,
            justify="center"
        )

    def update_content(self):
        # Dibujar Mapa Cuadrado táctico limpio en Canvas (ocupa toda la ventana)
        self.draw_minimap()

    def populate_vendor_cards(self):
        pass

    def populate_shrine_chips(self):
        pass

    def draw_minimap(self):
        """Dibuja el mapa CUADRADO 1:1 con cuadrícula táctica y todos los interactuables."""
        self.canvas.delete("all")
        self.drawn_landmarks = []

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50 or h < 50:
            w, h = 420, 310

        # Calcular dimensiones para mantener proporción estrictamente CUADRADA 1:1
        margin_x = 22
        margin_y = 20
        map_size = min(w - 2 * margin_x, h - 2 * margin_y)
        map_size = max(map_size, 180)

        # Centrar el cuadrado en el canvas
        ox = (w - map_size) // 2
        oy = (h - map_size) // 2
        ex = ox + map_size
        ey = oy + map_size

        # 1. Fondo de Terreno de la Isla (Cuadrado táctico)
        self.canvas.create_rectangle(
            ox, oy, ex, ey,
            fill=TERRAIN_BG,
            outline=BORDER_COLOR,
            width=2
        )

        # 2. Cuadrícula Táctica Cuadrada (4x4 Sectores)
        num_cells = 4
        cell_size = map_size / num_cells
        for i in range(1, num_cells):
            line_x = ox + i * cell_size
            line_y = oy + i * cell_size
            self.canvas.create_line(line_x, oy, line_x, ey, fill=GRID_COLOR, width=1, dash=(2, 4))
            self.canvas.create_line(ox, line_y, ex, line_y, fill=GRID_COLOR, width=1, dash=(2, 4))

        # 3. Marcas de Esquina Tácticas
        corner_len = 10
        for cx_corner, cy_corner, dx, dy in [
            (ox, oy, 1, 1),
            (ex, oy, -1, 1),
            (ox, ey, 1, -1),
            (ex, ey, -1, -1)
        ]:
            self.canvas.create_line(cx_corner, cy_corner, cx_corner + dx * corner_len, cy_corner, fill=BORDER_HIGHLIGHT, width=2)
            self.canvas.create_line(cx_corner, cy_corner, cx_corner, cy_corner + dy * corner_len, fill=BORDER_HIGHLIGHT, width=2)

        # 4. Indicadores Cardinales en los bordes del mapa cuadrado
        mid_x = ox + map_size // 2
        mid_y = oy + map_size // 2

        self.canvas.create_text(mid_x, oy - 9, text="NORTE (N)", fill="#94A3B8", font=FONT_COMPASS)
        self.canvas.create_text(mid_x, ey + 9, text="SUR (S)", fill="#64748B", font=FONT_COMPASS)
        self.canvas.create_text(ex + 12, mid_y, text="E", fill="#64748B", font=FONT_COMPASS)
        self.canvas.create_text(ox - 12, mid_y, text="O", fill="#64748B", font=FONT_COMPASS)

        # Etiquetas sutiles de cuadrantes
        quadrant_labels = [
            (ox + cell_size * 0.5, oy + cell_size * 0.5, "NO"),
            (ox + cell_size * 3.5, oy + cell_size * 0.5, "NE"),
            (ox + cell_size * 0.5, oy + cell_size * 3.5, "SO"),
            (ox + cell_size * 3.5, oy + cell_size * 3.5, "SE"),
            (mid_x, mid_y, "CENTRO")
        ]
        for qx, qy, qtxt in quadrant_labels:
            self.canvas.create_text(qx, qy, text=qtxt, fill="#1B2A47", font=FONT_SECTOR)

        # 5. Mapear y Dibujar los Marcadores Manuales (Balizas)
        min_x = self.map_bounds.get("min_x", -300.0)
        max_x = self.map_bounds.get("max_x", 300.0)
        min_z = self.map_bounds.get("min_z", -300.0)
        max_z = self.map_bounds.get("max_z", 300.0)
        span_x = max(max_x - min_x, 1.0)
        span_z = max(max_z - min_z, 1.0)

        for m in self.manual_markers:
            x, z = m.get("x"), m.get("z")
            if x is not None and z is not None:
                norm_x = (x - min_x) / span_x
                norm_z = (z - min_z) / span_z
                cx = ox + norm_x * map_size
                cy = oy + (1.0 - norm_z) * map_size
                m_copy = dict(m)
                m_copy["zone_desc"] = f"Baliza: ({x:.1f}, {z:.1f})"
                self.draw_landmark_node(cx, cy, m_copy)

        # 6. Mapear y Dibujar los Interactuables con Coordenadas Reales de Unity (Isla 600m: -300 a +300)
        for lm in self.landmarks:
            x = lm.get("x")
            z = lm.get("z")
            if x is not None and z is not None:
                norm_x = (x - min_x) / span_x
                norm_z = (z - min_z) / span_z
                norm_x = max(0.04, min(0.96, norm_x))
                norm_z = max(0.04, min(0.96, norm_z))
                cx = ox + norm_x * map_size
                cy = oy + (1.0 - norm_z) * map_size
                lm_copy = dict(lm)
                lm_copy["zone_desc"] = f"Coords: ({x:.1f}, {z:.1f})"
                self.draw_landmark_node(cx, cy, lm_copy)

        # 7. Posición en Vivo del Jugador (MyPlayer)
        if self.player_pos is not None:
            px = self.player_pos[0]
            pz = self.player_pos[2] if len(self.player_pos) > 2 else self.player_pos[1]
            norm_px = (px - min_x) / span_x
            norm_pz = (pz - min_z) / span_z
            norm_px = max(0.04, min(0.96, norm_px))
            norm_pz = max(0.04, min(0.96, norm_pz))
            pcx = ox + norm_px * map_size
            pcy = oy + (1.0 - norm_pz) * map_size

            # Halo verde brillante para el jugador
            self.canvas.create_oval(
                pcx - 12, pcy - 12, pcx + 12, pcy + 12,
                outline="#34D399", width=2
            )
            self.canvas.create_oval(
                pcx - 6, pcy - 6, pcx + 6, pcy + 6,
                fill="#059669", outline="#A7F3D0", width=1.5
            )
            self.canvas.create_text(
                pcx, pcy - 15,
                text=f"{self.t('you')} ({px:.0f}, {pz:.0f})",
                fill="#6EE7B7",
                font=("Segoe UI", 7, "bold")
            )
            player_dict = {
                "type": "player",
                "label": self.t("you_pos"),
                "icon": "🟢",
                "color": "#10B981",
                "zone_desc": f"Coords: ({px:.1f}, {pz:.1f})",
                "x": px,
                "z": pz
            }
            self.drawn_landmarks.append((pcx, pcy, 14, player_dict))

        # Mensaje de ayuda si no hay datos
        if not self.landmarks and self.player_pos is None and not self.manual_markers:
            self.canvas.create_text(
                mid_x, mid_y,
                text=self.t("empty"),
                fill=DIM_COLOR,
                font=FONT_LABEL,
                justify="center"
            )

    def draw_landmark_node(self, cx, cy, lm):
        """Dibuja un nodo táctico en el mapa cuadrado."""
        icon = lm.get("icon", "📍")
        color = lm.get("color", "#FFFFFF")
        is_gold = lm.get("is_golden", False) or lm.get("rarity") == 3
        lm_type = lm.get("type", "")

        # Tamaño y halo según importancia
        if is_gold:
            radius = 12
            # Halo dorado pulsante
            self.canvas.create_oval(
                cx - radius - 3, cy - radius - 3,
                cx + radius + 3, cy + radius + 3,
                outline="#F59E0B", width=2
            )
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill="#78350F", outline="#FBBF24", width=1.5
            )
        elif lm_type == "shady":
            radius = 11
            rarity = lm.get("rarity", 0)
            if rarity == 2:
                self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#2E1065", outline="#C084FC", width=1.5)
            elif rarity == 1:
                self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#082F49", outline="#38BDF8", width=1.5)
            else:
                self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#1E293B", outline="#94A3B8", width=1.5)
        elif lm_type == "moai":
            radius = 10
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#082F49", outline="#06B6D4", width=1.5)
        elif lm_type == "curse":
            radius = 10
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#450A0A", outline="#EF4444", width=1.5)
        elif lm_type == "charge":
            radius = 8
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#451A03", outline="#FBBF24", width=1)
        elif lm_type == "magnet":
            radius = 9
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#3B0764", outline="#D946EF", width=1.5)
        elif lm_type == "microwave":
            radius = 10
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#431407", outline="#FB923C", width=1.5)
        elif lm_type == "challenge":
            radius = 10
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#4C0519", outline="#F43F5E", width=1.5)
        elif lm_type == "marker":
            radius = 10
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#881337", outline="#F43F5E", width=1.5)
        else:
            radius = 9
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#1E293B", outline=color, width=1.5)

        # Icono emoji centrado
        font_size = 9 if is_gold or lm_type in ("shady", "moai", "curse") else 7
        self.canvas.create_text(
            cx, cy,
            text=icon,
            font=("Segoe UI Emoji", font_size)
        )

        self.drawn_landmarks.append((cx, cy, radius + 4, lm))

    def on_mouse_motion(self, event):
        mx, my = event.x, event.y
        hovered_lm = None

        for cx, cy, rad, lm in self.drawn_landmarks:
            dist = math.hypot(mx - cx, my - cy)
            if dist <= rad:
                hovered_lm = lm
                break

        if hovered_lm:
            lbl = hovered_lm.get("label", "Interactuable")
            items = hovered_lm.get("items", [])
            zone = hovered_lm.get("zone_desc", "")
            x = hovered_lm.get("x")
            z = hovered_lm.get("z")

            lines = [f"{lbl}"]
            if zone:
                lines.append(f"📍 Ubicación: {zone}")
            elif x is not None and z is not None:
                lines.append(f"📍 Posición: ({x:.1f}, {z:.1f})")

            if items:
                lines.append("🎁 Objetos en venta:")
                for it in items:
                    lines.append(f"  • {it}")

            text = "\n".join(lines)
            root_x = self.canvas.winfo_rootx() + mx
            root_y = self.canvas.winfo_rooty() + my
            self.tooltip.show(text, root_x, root_y)
        else:
            self.tooltip.hide()

    def show_window(self):
        if user32:
            try:
                hwnd = self.winfo_id()
                parent_hwnd = user32.GetParent(hwnd) or hwnd
                # Aplicar WS_EX_NOACTIVATE para NUNCA robar foco ni minimizar Megabonk.exe
                cur_style = user32.GetWindowLongW(parent_hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(parent_hwnd, GWL_EXSTYLE, cur_style | WS_EX_NOACTIVATE | WS_EX_TOPMOST)
                user32.ShowWindow(parent_hwnd, SW_SHOWNOACTIVATE)
                user32.SetWindowPos(
                    parent_hwnd, HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
                self._is_visible = True
                self.update()
                return
            except Exception:
                pass
        self._is_visible = True
        self.deiconify()
        self.attributes("-topmost", True)
        self.lift()

    def toggle_visibility(self):
        if not getattr(self, "_is_visible", True) or self.state() == "withdrawn":
            self.show_window()
        else:
            self.hide_window()

    def hide_window(self):
        self._is_visible = False
        self.tooltip.hide()
        self.withdraw()

    def close_window(self):
        self.tooltip.hide()
        try:
            self.destroy()
        except Exception:
            pass
