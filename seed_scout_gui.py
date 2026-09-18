import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Megabonk\BepInEx\config\com.facu.megabonkseedscout.cfg"

POPULAR_ITEMS = [
    ("SoulHarvester (Cosechador de almas)", "SoulHarvester,Cosechador"),
    ("SuckyHoof / Magnet (Iman)", "SuckyHoof,SuckyMagnet,Magnet,Iman"),
    ("GoldenShield (Escudo dorado)", "GoldenShield"),
    ("GoldenGlove (Guantelete dorado)", "GoldenGlove"),
    ("GoldenSneakers (Zapatillas doradas)", "GoldenSneakers"),
    ("ZaWarudo (Detener el tiempo)", "ZaWarudo"),
    ("Dragonfire (Fuego de dragon)", "Dragonfire"),
    ("DemonicBlood (Sangre demoniaca)", "DemonicBlood"),
    ("DemonicSoul (Alma demoniaca)", "DemonicSoul"),
    ("LightningOrb (Orbe relampago)", "LightningOrb"),
    ("SluttyCannon (Canon)", "SluttyCannon"),
    ("CreditCardRed (Tarjeta roja)", "CreditCardRed"),
    ("CreditCardGreen (Tarjeta verde)", "CreditCardGreen"),
]

def load_config():
    values = {
        "ModoDeBusqueda": "CustomSelectedItems",
        "ItemsPersonalizados": "SoulHarvester,SuckyMagnet",
        "ItemObjetivo1": "SoulHarvester,Cosechador",
        "ItemObjetivo2": "SuckyHoof,SuckyMagnet,Magnet,Iman",
        "RetardoEscaneoSegundos": "0.45",
        "SonidoDeAlerta": "true",
        "MostrarHUD": "true",
        "MostrarIndicadorMapa": "true"
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    values[k.strip()] = v.strip()
    return values

def save_config(values):
    content = f"""## Configuracion de Megabonk Seed Scout & Auto-Reset

[1. General]
ModoDeBusqueda = {values.get('ModoDeBusqueda', 'CustomSelectedItems')}
ItemsPersonalizados = {values.get('ItemsPersonalizados', 'SoulHarvester,SuckyMagnet')}
ItemObjetivo1 = {values.get('ItemObjetivo1', 'SoulHarvester,Cosechador')}
ItemObjetivo2 = {values.get('ItemObjetivo2', 'SuckyHoof,SuckyMagnet,Magnet,Iman')}

[2. Ajustes]
RetardoEscaneoSegundos = {values.get('RetardoEscaneoSegundos', '0.45')}
SonidoDeAlerta = {values.get('SonidoDeAlerta', 'true')}
MostrarHUD = {values.get('MostrarHUD', 'true')}
MostrarIndicadorMapa = {values.get('MostrarIndicadorMapa', 'true')}

[3. Atajos]
TeclaIniciar = F5
TeclaPausar = F6
TeclaOcultarHUD = F7
TeclaCambiarModo = F8
TeclaIndicadorMapa = F9
"""

"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

class SeedScoutApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Megabonk Seed Scout - Configurador")
        self.geometry("540x520")
        self.resizable(False, False)
        self.configure(bg="#181824")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#181824", foreground="#E0E0E0", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#FFD700")
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"), foreground="#64B5F6")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TRadiobutton", background="#181824", foreground="#FFFFFF", font=("Segoe UI", 10))

        self.cfg = load_config()

        # Title
        lbl_title = ttk.Label(self, text="MEGABONK SEED SCOUT", style="Title.TLabel")
        lbl_title.pack(pady=(16, 4))
        lbl_sub = ttk.Label(self, text="Filtro de Semillas Récord y Auto-Reset Sin Trampas", font=("Segoe UI", 9), foreground="#AAAAAA")
        lbl_sub.pack(pady=(0, 14))

        # Mode Selection
        frame_mode = tk.LabelFrame(self, text=" 1. Modo de Búsqueda ", bg="#222232", fg="#64B5F6", font=("Segoe UI", 10, "bold"), padx=12, pady=10)
        frame_mode.pack(fill="x", padx=18, pady=6)

        self.mode_var = tk.StringVar(value=self.cfg.get("ModoDeBusqueda", "CustomSelectedItems"))
        r0 = ttk.Radiobutton(frame_mode, text="🎒 Personalizado: Seleccionar hasta 3 Ítems de Cualquier Rareza", value="CustomSelectedItems", variable=self.mode_var)
        r0.pack(anchor="w", pady=3)
        r1 = ttk.Radiobutton(frame_mode, text="⭐ Doble Vendedor Dorado (Cosechador de Almas + Imán)", value="DualVendor_SoulHarvester_And_Magnet", variable=self.mode_var)
        r1.pack(anchor="w", pady=3)
        r2 = ttk.Radiobutton(frame_mode, text="🎯 Ítem Único Dorado (Cosechador de Almas / Ítem 1)", value="SingleItem_SoulHarvester", variable=self.mode_var)
        r2.pack(anchor="w", pady=3)
        r3 = ttk.Radiobutton(frame_mode, text="👑 Cualquier Vendedor Dorado (Cabeza Dorada visible)", value="AnyGoldenVendor", variable=self.mode_var)
        r3.pack(anchor="w", pady=3)

        # Target Items
        frame_items = tk.LabelFrame(self, text=" 2. Ítems Objetivo ", bg="#222232", fg="#64B5F6", font=("Segoe UI", 10, "bold"), padx=12, pady=10)
        frame_items.pack(fill="x", padx=18, pady=6)

        # Custom Items
        lbl_custom = ttk.Label(frame_items, text="Ítems Personalizados:", background="#222232")
        lbl_custom.grid(row=0, column=0, sticky="w", pady=4)
        self.entry_custom = ttk.Entry(frame_items, width=32)
        self.entry_custom.insert(0, self.cfg.get("ItemsPersonalizados", "SoulHarvester,SuckyMagnet"))
        self.entry_custom.grid(row=0, column=1, padx=8, pady=4)

        # Item 1
        lbl_it1 = ttk.Label(frame_items, text="Ítem 1 (Modo Único):", background="#222232")
        lbl_it1.grid(row=1, column=0, sticky="w", pady=4)
        self.entry_item1 = ttk.Entry(frame_items, width=32)
        self.entry_item1.insert(0, self.cfg.get("ItemObjetivo1", "SoulHarvester,Cosechador"))
        self.entry_item1.grid(row=1, column=1, padx=8, pady=4)

        # Item 2
        lbl_it2 = ttk.Label(frame_items, text="Ítem 2 (Modo Dual):", background="#222232")
        lbl_it2.grid(row=2, column=0, sticky="w", pady=4)
        self.entry_item2 = ttk.Entry(frame_items, width=32)
        self.entry_item2.insert(0, self.cfg.get("ItemObjetivo2", "SuckyHoof,SuckyMagnet,Magnet,Iman"))
        self.entry_item2.grid(row=2, column=1, padx=8, pady=4)

        # Quick preset dropdown
        lbl_quick = ttk.Label(frame_items, text="Añadir ítem rápido:", background="#222232")
        lbl_quick.grid(row=3, column=0, sticky="w", pady=4)
        self.combo_presets = ttk.Combobox(frame_items, values=[p[0] for p in POPULAR_ITEMS], width=30, state="readonly")
        self.combo_presets.set("Seleccionar ítem...")
        self.combo_presets.grid(row=3, column=1, padx=8, pady=4)
        self.combo_presets.bind("<<ComboboxSelected>>", self.on_preset_selected)

        # Controls reference
        frame_controls = tk.LabelFrame(self, text=" 3. Controles en el Juego ", bg="#222232", fg="#64B5F6", font=("Segoe UI", 10, "bold"), padx=12, pady=8)
        frame_controls.pack(fill="x", padx=18, pady=6)

        ctrl_text = "• [F5] Iniciar / Reanudar búsqueda automática\n• [F6] Pausar / Detener búsqueda automática\n• [F7] Ocultar / Mostrar panel de control (HUD)\n• [F8] Cambiar modo de búsqueda\n• [F9] Ocultar / Mostrar indicador de mapa en español"
        lbl_ctrl = ttk.Label(frame_controls, text=ctrl_text, background="#222232", font=("Segoe UI", 9))
        lbl_ctrl.pack(anchor="w")


        # Save Button
        frame_btns = tk.Frame(self, bg="#181824")
        frame_btns.pack(fill="x", padx=18, pady=12)

        btn_save = tk.Button(frame_btns, text="💾 GUARDAR CONFIGURACIÓN", bg="#00C853", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=6, command=self.on_save)
        btn_save.pack(side="left", expand=True, fill="x", padx=4)

        btn_launch = tk.Button(frame_btns, text="🚀 ABRIR MEGABONK", bg="#1976D2", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", padx=12, pady=6, command=self.on_launch)
        btn_launch.pack(side="right", expand=True, fill="x", padx=4)

    def on_preset_selected(self, event):
        idx = self.combo_presets.current()
        if idx >= 0:
            val = POPULAR_ITEMS[idx][1]
            self.entry_item1.delete(0, tk.END)
            self.entry_item1.insert(0, val)

    def on_save(self):
        vals = {
            "ModoDeBusqueda": self.mode_var.get(),
            "ItemsPersonalizados": self.entry_custom.get().strip(),
            "ItemObjetivo1": self.entry_item1.get().strip(),
            "ItemObjetivo2": self.entry_item2.get().strip(),
            "RetardoEscaneoSegundos": "0.45",
            "SonidoDeAlerta": "true",
            "MostrarHUD": "true",
            "MostrarIndicadorMapa": "true"
        }

        try:
            save_config(vals)
            messagebox.showinfo("Configuración Guardada", "La configuración se ha guardado correctamente.\nSe aplicará automáticamente en Megabonk.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")

    def on_launch(self):
        self.on_save()
        os.system("start steam://rungameid/2456420")

if __name__ == "__main__":
    app = SeedScoutApp()
    app.mainloop()
