"""
MB Helper - Buscador externo de semillas y HUD de powerups.
Lectura de memoria sin inyeccion de DLLs en el directorio del juego.
Lectura pasiva de memoria + Automatizacion con hardware input nativo y vision artificial.
Atajo Global F5 para Iniciar / Detener en cualquier momento sin Alt+Tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import atexit
import itertools
import ctypes
import queue
from ctypes import wintypes

try:
    import keyboard
except Exception:
    keyboard = None

from phantom_reader import (
    PhantomMemoryReader,
    OFFICIAL_ITEMS,
    ITEM_BY_ID,
    ITEM_NAMES_ES,
    ITEM_NAMES_EN,
    ITEM_NAMES_PT,
    calculate_map_score,
    evaluate_map_tier,
    TIER_INFO,
    PRESET_TEMPLATES,
    OFFICIAL_POWERUPS
)
from phantom_bot import PhantomBot
from telemetry_logger import TelemetryLogger
from powerup_overlay import PowerupOverlay
from runtime_paths import application_dir
from search_config import SEARCH_MODES, capture_configuration, search_setting
from menu_ui import (MenuUI, COLOR_BG, COLOR_CARD, COLOR_CARD_ALT, COLOR_BORDER, COLOR_BORDER_GLOW,
                     COLOR_GOLD, COLOR_PURPLE, COLOR_BLUE, COLOR_GREEN, COLOR_RED, COLOR_TEXT, COLOR_TEXT_DIM,
                     FONT_TITLE, FONT_SUBTITLE, FONT_BODY, FONT_BOLD, FONT_TAB, FONT_MONO, FONT_COUNTER,
                     RARITY_COLORS, THEORETICAL_MIN_PRICE, PRESET_KEYS, MENU_TEXT)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Intentar habilitar Per-Monitor DPI Awareness en Windows para nitidez maxima
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

# ==========================================
# ==========================================
# SISTEMA DE AUDITORIA Y LOGGING
# ==========================================
APP_DIR = application_dir()
LOG_FILE_PATH = os.path.join(APP_DIR, "megabonk_helper.log")
_log_lock = threading.Lock()
_log_file = None

def _cleanup_log():
    global _log_file
    with _log_lock:
        if _log_file and not _log_file.closed:
            try:
                _log_file.flush()
                _log_file.close()
            except Exception:
                pass
            _log_file = None

atexit.register(_cleanup_log)

def log_event(message, level="INFO"):
    global _log_file
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level:<7}] {message}\n"
    with _log_lock:
        try:
            if _log_file is None or _log_file.closed:
                _log_file = open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=4096)
            _log_file.write(line)
            if level in ("MATCH", "SUCCESS", "ERROR", "START", "STOP", "WARN", "TEST"):
                _log_file.flush()
        except Exception:
            pass

# ==========================================
# DICCIONARIO DE INTERNACIONALIZACION (I18N)
# ==========================================
I18N = {
    "es": {
        "title": "MB Helper - Buscador de Semillas Record (100% Legal Steam)",
        "legal_badge": "✓ 100% LEGAL STEAM",
        "lang_lbl": "🌐 Idioma:",
        "looking_game": "● Buscando juego...",
        "game_connected": "● En Menu",
        "game_in_match": "● En Partida",
        "game_closed": "● Cerrado",
        "tab1": "🎯 MODO 1: ITEMS",
        "tab2": "👑 MODO 2: DORADOS",
        "tab4": "⭐ MODO 4: PUNTUACION & PLANTILLAS",
        # Tab 1
        "items_chosen": "Items Elegidos (Max 3):",
        "items_none": "Ninguno (Selecciona abajo)",
        "btn_clear": "🧹 Limpiar",
        "search_item": "🔍 Buscar Item:",
        "rarity_golden": "Dorados (Legendarios)",
        "rarity_epic": "Epicos (Morados)",
        "rarity_rare": "Raros (Azules)",
        "rarity_common": "Comunes (Grises)",
        # Tab 2
        "tab2_title": "VENDEDORES DORADOS",
        "gold_opt1": "👑 1 Vendedor Dorado",
        "gold_opt2": "👑👑 2 Vendedores Dorados",
        "gold_opt3": "👑👑👑 3 Vendedores Dorados (0.1%)",
        # Tab 4
        "tier_title": "1. ELEGIR RANGO MINIMO:",
        "preset_title": "2. O ELEGIR UNA PLANTILLA META:",
        "combo_chk": "🔗 Exigir tambien Items de Vendedores (Modo 1)",
        "combo_none": "Ningun item seleccionado en Modo 1",
        "combo_active": "🔗 Items activos: ",
        "combo_inactive": "Modo 1 (inactivo): ",
        "combo_golden_chk": "👑 Exigir tambien Dorados (Modo 2)",
        "combo_golden_active": "👑 Activo: Minimo {count} Dorado(s) {crowns}",
        "combo_golden_inactive": "Modo 2 (inactivo): {count} {crowns}",
        "preset_hover_hint": "ℹ️ DETALLES:",
        "preset_hover_default": "Pasa el cursor sobre un preset para ver requisitos.",
        "preset_active_pref": "Plantilla Activa:",
        "score_meter_title": "📊 MEDIDOR DE PUNTUACION EN VIVO:",
        "score_waiting": "Puntaje: 0.0 pts  |  Rango: Esperando...",
        # Presets
        "preset_sec_forest": "🌿 Plantillas Bosque / Desierto",
        "preset_sec_graveyard": "⚰️ Plantillas Cementerio",
        "preset_wr": "🏆 Record Mundial (Perfect+)",
        "preset_wr_white": "🏆 Récord (2x Blancos)",
        "preset_good": "⭐ Gran Partida (Perfect)",
        "preset_fast": "⏱️ Busqueda Rapida (Good)",
        "preset_moai": "🗿 Lluvia Moais (5+)",
        "preset_vendor": "💰 Vendedores 5+ (Shady)",
        "preset_micro": "⚡ 2x Microondas",
        "preset_micro_white": "⚡ 2x Micros Blancos",
        "preset_graveyard_bald": "💀 Moáis Calvos (10+)",
        # Bottom controls
        "btn_start": "▶ INICIAR BUSQUEDA [F5]",
        "btn_stop": "⏸ DETENER BUSQUEDA [F5]",
        "btn_test_reset": "⚡ Probar Reinicio ('R')",
        "btn_logs": "📄 Ver Registro",
        "badge_afk": "🛡️ Pausa AFK",
        "attempts": "Intentos",
        "time": "Tiempo",
        "status_stopped_user": "Busqueda detenida por usuario [F5].",
        "status_running": "Buscando semilla record... [F5 para parar]",
        "status_found": "¡¡PARTIDA ENCONTRADA EN #{count}!! Juego pausado.",
        "status_reading": "Leyendo...",
        "status_waiting_game": "Esperando inicio del juego...",
        "status_waiting_match": "Esperando inicio de partida...",
        "status_resetting": "Reiniciando... (Intento #{count}) [F5 para parar]",
        "status_stalled": "⚠️ Estancado ({sec}s). Reenviando reinicio 'R'...",
        "status_paused_focus": "⏳ Pausado: Haz clic en el juego para reanudar...",
        "tier_standard": "Estandar",
        "stat_score": "Puntaje",
        "stat_tier": "Rango",
        "stat_gold": "Dorados",
        "stat_moais": "Moais",
        "stat_curses": "Maldiciones",
        "stat_micros": "Micros",
        "stat_chests": "Cofres",
        "stat_vendors": "Vendedores",
        "target_mode_direct": "Objetivo: {label} (Score >= {min_score})",
        "target_preset_active": "Plantilla: {name} -> {tier} (Score >= {min_score})",
        # Alertas y dialogos
        "alert_item_limit_title": "Limite de Items",
        "alert_item_limit_msg": "Solo puedes seleccionar hasta 3 items a la vez (1 por vendedor).",
        "alert_no_items_title": "Sin Items",
        "alert_no_items_msg": "Debes seleccionar al menos 1 item en el Modo 1.",
        "alert_combo_no_items_msg": "Activaste exigir items, pero no tienes ninguno seleccionado en Modo 1.",
        "alert_game_not_found_title": "Juego no detectado",
        "alert_game_not_found_msg": "No se encontro el proceso del juego. Abre el juego y entra a una partida primero.",
        "alert_restart_required_title": "Reinicio Requerido",
        "alert_restart_required_msg": "El juego se ha vuelto lento ({avg:.1f}s recarga promedio). Cierra y reabre el juego para recuperar velocidad maxima.",
        "alert_reset_error_title": "Error de Reinicio",
        "alert_reset_error_msg": "No se pudo enviar la senal de reinicio al juego.",
        "status_quick_reset_sent": "⚡ Senal de reinicio rapido ('R') enviada al juego.",
        # Precios de items
        "price_max_label": "Precio Máx:",
        "price_gold": "oro",
        "price_min_hint": "(Mín. juego: ~{min}g · Vacío=sin límite)",
        "price_below_min": "⚠️ Menor al mín. ({min}g)",
        "price_ok_hint": "✓ Techo: {max}g (Mín: ~{min}g)",
    },
    "en": {
        "title": "MB Helper - Record Seed Finder (100% Legal Steam)",
        "legal_badge": "✓ 100% LEGAL STEAM",
        "lang_lbl": "🌐 Language:",
        "looking_game": "● Searching game...",
        "game_connected": "● In Menu",
        "game_in_match": "● In Game",
        "game_closed": "● Closed",
        "tab1": "🎯 MODE 1: ITEMS",
        "tab2": "👑 MODE 2: GOLDENS",
        "tab4": "⭐ MODE 4: SCORES & PRESETS",
        # Tab 1
        "items_chosen": "Chosen Items (Max 3):",
        "items_none": "None (Select below)",
        "btn_clear": "🧹 Clear",
        "search_item": "🔍 Search Item:",
        "rarity_golden": "Golden (Legendary)",
        "rarity_epic": "Epic (Purple)",
        "rarity_rare": "Rare (Blue)",
        "rarity_common": "Common (Gray)",
        # Tab 2
        "tab2_title": "GOLDEN VENDORS",
        "gold_opt1": "👑 1 Golden Vendor",
        "gold_opt1_desc": "Common (~25% · Seconds)",
        "gold_opt2": "👑👑 2 Golden Vendors",
        "gold_opt2_desc": "Rare (~3% · Highly recommended)",
        "gold_opt3": "👑👑👑 3 Golden Vendors",
        "gold_opt3_desc": "Legendary (~0.1% · Perfect)",
        # Tab 3
        # Tab 4
        "tab4_title": "SCORES & PRESETS",
        "tier_title": "🎯 1. Target Tier",
        "preset_title": "⚡ 2. Load Quick Preset",
        "combo_chk": "🔗 Also require Mode 1 Items",
        "combo_none": "Mode 1: None selected",
        "combo_active": "🔗 Active items: ",
        "combo_inactive": "Mode 1 (inactive): ",
        "combo_golden_chk": "👑 Also require Goldens (Mode 2)",
        "combo_golden_active": "👑 Active: At least {count} Golden(s) {crowns}",
        "combo_golden_inactive": "Mode 2 (inactive): {count} {crowns}",
        "preset_hover_hint": "ℹ️ DETAILS:",
        "preset_hover_default": "Hover mouse over any preset to see requirements.",
        "preset_active_pref": "Active Preset:",
        "score_meter_title": "📊 LIVE SCORE METER:",
        "score_waiting": "Score: 0.0 pts  |  Tier: Waiting...",
        # Presets
        "preset_sec_forest": "🌿 Forest / Desert Templates",
        "preset_sec_graveyard": "⚰️ Graveyard Templates",
        "preset_wr": "🏆 World Record (Perfect+)",
        "preset_wr_white": "🏆 WR (2x White Micros)",
        "preset_good": "⭐ Great Run (Perfect)",
        "preset_fast": "⏱️ Fast Search (Good)",
        "preset_moai": "🗿 Moai Rain (5+)",
        "preset_vendor": "💰 Vendors 5+ (Shady)",
        "preset_micro": "⚡ 2x Microwaves",
        "preset_micro_white": "⚡ 2x White Microwaves",
        "preset_graveyard_bald": "💀 Bald Heads (10+)",
        # Bottom controls
        "btn_start": "▶ START SEARCH [F5]",
        "btn_stop": "⏸ STOP SEARCH [F5]",
        "btn_test_reset": "⚡ Test Reset ('R')",
        "btn_logs": "📄 View Log",
        "badge_afk": "🛡️ AFK Pause",
        "attempts": "Attempts",
        "time": "Time",
        "status_stopped_user": "Search stopped by user [F5].",
        "status_running": "Searching record seed... [F5 to stop]",
        "status_found": "PERFECT RUN FOUND ON #{count}! Game paused.",
        "status_reading": "Reading...",
        "status_waiting_game": "Waiting for game process...",
        "status_waiting_match": "Waiting for match to start...",
        "status_resetting": "Resetting... (Attempt #{count}) [F5 to stop]",
        "status_stalled": "⚠️ Stalled ({sec}s). Retrying 'R'...",
        "status_paused_focus": "⏳ Paused: Click game window to resume...",
        "tier_standard": "Standard",
        "stat_score": "Score",
        "stat_tier": "Tier",
        "stat_gold": "Goldens",
        "stat_moais": "Moais",
        "stat_curses": "Curses",
        "stat_micros": "Micros",
        "stat_chests": "Chests",
        "stat_vendors": "Vendors",
        "target_mode_direct": "Target: {label} (Score >= {min_score})",
        "target_preset_active": "Preset: {name} -> {tier} (Score >= {min_score})",
        # Alerts & dialogs
        "alert_item_limit_title": "Item Limit",
        "alert_item_limit_msg": "Only up to 3 items can be selected at once (1 per vendor).",
        "alert_no_items_title": "No Items",
        "alert_no_items_msg": "You must select at least 1 item in Mode 1.",
        "alert_combo_no_items_msg": "You enabled requiring items, but none selected in Mode 1.",
        "alert_game_not_found_title": "Game not detected",
        "alert_game_not_found_msg": "Game process not found. Please open the game and start a run first.",
        "alert_restart_required_title": "Restart Required",
        "alert_restart_required_msg": "Game became slow ({avg:.1f}s average reload). Please restart the game to restore max speed.",
        "alert_reset_error_title": "Reset Error",
        "alert_reset_error_msg": "Could not send restart signal to the game.",
        "status_quick_reset_sent": "⚡ Quick reset signal ('R') sent to game.",
        # Item prices
        "price_max_label": "Max Price:",
        "price_gold": "gold",
        "price_min_hint": "(Game min: ~{min}g · Empty=no limit)",
        "price_below_min": "⚠️ Below min ({min}g)",
        "price_ok_hint": "✓ Cap: {max}g (Min: ~{min}g)",
    },
    "pt": {
        "title": "MB Helper - Localizador de Seeds Recorde (100% Legal Steam)",
        "legal_badge": "✓ 100% LEGAL STEAM",
        "lang_lbl": "🌐 Idioma:",
        "looking_game": "● Procurando jogo...",
        "game_connected": "● No Menu",
        "game_in_match": "● Em Jogo",
        "game_closed": "● Fechado",
        "tab1": "🎯 MODO 1: ITENS",
        "tab2": "👑 MODO 2: DOURADOS",
        "tab4": "⭐ MODO 4: PONTOS & PRESETS",
        # Tab 1
        "items_chosen": "Itens Escolhidos (Max 3):",
        "items_none": "Nenhum (Selecione abaixo)",
        "btn_clear": "🧹 Limpar",
        "search_item": "🔍 Buscar Item:",
        "rarity_golden": "Dourados (Lendarios)",
        "rarity_epic": "Epicos (Roxos)",
        "rarity_rare": "Raros (Azuis)",
        "rarity_common": "Comuns (Cinzas)",
        # Tab 2
        "tab2_title": "VENDEDORES DOURADOS",
        "gold_opt1": "👑 1 Vendedor Dourado",
        "gold_opt2": "👑👑 2 Vendedores Dourados",
        "gold_opt3": "👑👑👑 3 Vendedores Dourados (0.1%)",
        # Tab 3
        # Tab 4
        "tier_title": "1. ESCOLHER TIER MINIMO:",
        "preset_title": "2. OU ESCOLHER UM PRESET META:",
        "combo_chk": "🔗 Exigir tambem Itens de Vendedores (Modo 1)",
        "combo_none": "Nenhum item selecionado no Modo 1",
        "combo_active": "🔗 Itens ativos: ",
        "combo_inactive": "Modo 1 (inativo): ",
        "combo_golden_chk": "👑 Exigir tambem Dourados (Modo 2)",
        "combo_golden_active": "👑 Ativo: Minimo {count} Dourado(s) {crowns}",
        "combo_golden_inactive": "Modo 2 (inativo): {count} {crowns}",
        "preset_hover_hint": "ℹ️ DETALHES:",
        "preset_hover_default": "Passe o cursor sobre um preset para ver os requisitos.",
        "preset_active_pref": "Preset Ativo:",
        "score_meter_title": "📊 MEDIDOR DE SCORE EM TEMPO REAL:",
        "score_waiting": "Pontos: 0.0 pts  |  Tier: Aguardando...",
        # Presets
        "preset_sec_forest": "🌿 Modelos Floresta / Deserto",
        "preset_sec_graveyard": "⚰️ Modelos Cemitério",
        "preset_wr": "🏆 Recorde Mundial (Perfect+)",
        "preset_wr_white": "🏆 Recorde (2x Brancos)",
        "preset_good": "⭐ Otima Partida (Perfect)",
        "preset_fast": "⏱️ Busca Rapida (Good)",
        "preset_moai": "🗿 Chuva de Moais (5+)",
        "preset_vendor": "💰 Vendedores 5+ (Shady)",
        "preset_micro": "⚡ 2x Micro-ondas",
        "preset_micro_white": "⚡ 2x Micros Brancos",
        "preset_graveyard_bald": "💀 Cabeças Calvas (10+)",
        # Bottom controls
        "btn_start": "▶ INICIAR BUSCA [F5]",
        "btn_stop": "⏸ PARAR BUSCA [F5]",
        "btn_test_reset": "⚡ Testar Reinicio ('R')",
        "btn_logs": "📄 Ver Registro",
        "badge_afk": "🛡️ Pausa AFK",
        "attempts": "Tentativas",
        "time": "Tempo",
        "status_stopped_user": "Busca parada pelo usuario [F5].",
        "status_running": "Buscando seed recorde... [F5 para parar]",
        "status_found": "PARTIDA ENCONTRADA EM #{count}!! Jogo pausado.",
        "status_reading": "Lendo...",
        "status_waiting_game": "Aguardando inicializacao do jogo...",
        "status_waiting_match": "Aguardando inicio da partida...",
        "status_resetting": "Reiniciando... (Tentativa #{count}) [F5 para parar]",
        "status_stalled": "⚠️ Travado ({sec}s). Reenviando 'R'...",
        "status_paused_focus": "⏳ Pausado: Clique no jogo para continuar...",
        "tier_standard": "Padrao",
        "stat_score": "Pontos",
        "stat_tier": "Tier",
        "stat_gold": "Dourados",
        "stat_moais": "Moais",
        "stat_curses": "Maldicoes",
        "stat_micros": "Micros",
        "stat_chests": "Baus",
        "stat_vendors": "Vendedores",
        "target_mode_direct": "Objetivo: {label} (Score >= {min_score})",
        "target_preset_active": "Preset: {name} -> {tier} (Score >= {min_score})",
        # Alertas e dialogos
        "alert_item_limit_title": "Limite de Itens",
        "alert_item_limit_msg": "Voce so pode selecionar ate 3 itens por vez (1 por vendedor).",
        "alert_no_items_title": "Sem Itens",
        "alert_no_items_msg": "Selecione pelo menos 1 item no Modo 1.",
        "alert_combo_no_items_msg": "Voce ativou exigir itens, mas nao selecionou nenhum no Modo 1.",
        "alert_game_not_found_title": "Jogo nao detectado",
        "alert_game_not_found_msg": "Processo do jogo nao encontrado. Abra o jogo e entre em uma partida primeiro.",
        "alert_restart_required_title": "Reinicio Necessario",
        "alert_restart_required_msg": "O jogo ficou lento ({avg:.1f}s recarga media). Feche e abra o jogo para restaurar a velocidade maxima.",
        "alert_reset_error_title": "Erro de Reinicio",
        "alert_reset_error_msg": "Nao foi possivel enviar o sinal de reinicio para o jogo.",
        "status_quick_reset_sent": "⚡ Sinal de reinicio rapido ('R') enviado ao jogo.",
        # Precos de itens
        "price_max_label": "Preço Máx:",
        "price_gold": "ouro",
        "price_min_hint": "(Mín. jogo: ~{min}g · Vazio=sem limite)",
        "price_below_min": "⚠️ Menor que o mín. ({min}g)",
        "price_ok_hint": "✓ Teto: {max}g (Mín: ~{min}g)",
    }
}

for _language, _text in MENU_TEXT.items():
    I18N[_language].update(_text)


class MegabonkHelperApp(MenuUI, tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_lang = "es"
        self.title(self.t("title"))
        self.geometry(f"{min(1160, self.winfo_screenwidth()-80)}x{min(820, self.winfo_screenheight()-100)}")
        self.minsize(760, 540)
        self.configure(bg=COLOR_BG)

        self.reader = PhantomMemoryReader()
        self.bot = PhantomBot()

        # Cargar iconos nativos de items
        self.item_icons = {}
        icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "item_icons")
        if os.path.exists(icons_dir):
            for fname in os.listdir(icons_dir):
                if fname.endswith(".png"):
                    cname = fname[:-4]
                    try:
                        image = tk.PhotoImage(file=os.path.join(icons_dir, fname))
                        factor = max(1, (max(image.width(), image.height()) + 35) // 36)
                        self.item_icons[cname] = image.subsample(factor, factor) if factor > 1 else image
                    except Exception:
                        pass

        # Control de ciclo de vida
        self.is_closing = False
        self._closing_event = threading.Event()
        self._ui_queue = queue.SimpleQueue()
        self._hotkey_lock = threading.Lock()
        self._powerup_lock = threading.Lock()
        self._powerup_sample = (0.0, None)
        self._overlay_enabled = threading.Event()
        self._overlay_enabled.set()
        self.after(20, self._drain_ui_queue)
        self._search_config = None
        self._testing_reset = False
        self.is_running = False
        self.attempt_count = 0
        self.start_time = 0
        self.match_found = False
        self._current_match_start_time = None
        self.last_seed = None
        self.last_reroll_time = None
        self.last_map_sig = None
        self.current_map_detected_time = None
        self.last_activity_time = time.time()
        self.is_focus_paused = False
        self.watchdog_stalls_count = 0
        self.generation_seen = False
        self.bloated_game_blocked = False
        self.bloated_pid = None
        self.consecutive_slow_reloads = 0
        self.recent_reloads = []
        log_event("=== MB Helper Iniciado ===", level="INIT")

        # Variables de estado
        self.selected_mode = tk.IntVar(value=1)
        self.selected_items = []  # [(id, codename, es_name, en_name, pt_name), ...]
        self.item_max_prices = {}  # {item_id: tk.StringVar}
        self.target_golden_vendors = tk.IntVar(value=1)

        # Modo 4: Puntuacion, Rangos y Plantillas
        self.score_submode = tk.StringVar(value="tier")
        self.target_tier = tk.StringVar(value="Good")
        self.selected_template = tk.StringVar(value="fast_good")
        self.require_mode1_items = tk.BooleanVar(value=False)
        self.require_golden_vendors = tk.BooleanVar(value=False)
        self._logged_item_timing = False
        self.waiting_for_scene_reload = False
        self.saw_zero_interactables = False

        # Construir Interfaz de Usuario
        self.setup_ui()

        # Timestamp para debounce de atajos F5 y F6
        self._last_f5_time = 0.0
        self._last_f6_time = 0.0

        # Atajos de teclado locales Tkinter
        self.bind("<F5>", lambda e: self.trigger_f5_action())
        self.bind("<F6>", lambda e: self.trigger_f6_action())

        # Overlay Flotante de Powerups (F6)
        try:
            self.powerup_overlay = PowerupOverlay(self)
        except Exception:
            self.powerup_overlay = None

        # Desplazamiento global con rueda del raton (MouseWheel) para ventanas reducidas
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", lambda e: self._on_global_mousewheel_linux(-1))
        self.bind_all("<Button-5>", lambda e: self._on_global_mousewheel_linux(1))

        # Hilos secundarios independientes y bucle de overlay
        self.start_hotkey_listener()
        self.start_background_monitor()
        self.start_bot_worker()
        self.start_powerup_overlay_loop()

        # Telemetría de partidas y estadísticas completas (LightGBM & Optuna)
        # Pausa 100% durante búsqueda automática F5 (0% interferencia en rerolls)
        self.telemetry = TelemetryLogger(
            self.reader,
            is_searching_callback=lambda: self.is_running,
            sample_interval=5.0
        )
        self.telemetry.start()

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def t(self, key, **kwargs):
        lang_dict = I18N.get(self.current_lang, I18N["es"])
        val = lang_dict.get(key, I18N["es"].get(key, key))
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return val

    def on_language_change(self, event=None):
        val = self.lang_combo.get()
        if "Portugu" in val:
            self.current_lang = "pt"
        elif "English" in val:
            self.current_lang = "en"
        else:
            self.current_lang = "es"
        self.update_ui_language()

    def update_ui_language(self):
        if getattr(self, "powerup_overlay", None):
            self.powerup_overlay.language = self.current_lang
        self.title(self.t("title"))
        self.lbl_legal.config(text=self.t("legal_badge"))
        self.lbl_lang_prefix.config(text=self.t("lang_lbl"))

        # Actualizar pestanas
        self.btn_tab1.config(text=self.t("tab1"))
        self.btn_tab2.config(text=self.t("tab2"))
        self.btn_tab4.config(text=self.t("tab4"))

        # Tab 1
        self.lbl_items_chosen_title.config(text=self.t("items_chosen"))
        self.btn_clear_items.config(text=self.t("btn_clear"))
        self.lbl_search_title.config(text=self.t("search_item"))
        self.update_selected_items_label()
        self.refresh_items_grid()

        # Tab 2
        self.lbl_tab2_title.config(text=self.t("tab2_title"))
        self.rb_gold1.config(text=self.t("gold_opt1"))
        self.lbl_gold1_desc.config(text=self.t("gold_opt1_desc"))
        self.rb_gold2.config(text=self.t("gold_opt2"))
        self.lbl_gold2_desc.config(text=self.t("gold_opt2_desc"))
        self.rb_gold3.config(text=self.t("gold_opt3"))
        self.lbl_gold3_desc.config(text=self.t("gold_opt3_desc"))

        # Tab 4
        self.lbl_tab4_title.config(text=self.t("tab4_title"))
        self.lbl_tier_sec_title.config(text=self.t("tier_title"))
        self.lbl_preset_sec_title.config(text=self.t("preset_title"))
        if hasattr(self, "lbl_forest_title"):
            self.lbl_forest_title.config(text=self.t("preset_sec_forest"))
        if hasattr(self, "lbl_graveyard_title"):
            self.lbl_graveyard_title.config(text=self.t("preset_sec_graveyard"))

        # Presets text
        preset_key_map = {
            "record_perfect_plus": "preset_wr",
            "record_perfect_plus_white": "preset_wr_white",
            "record_perfect": "preset_good",
            "fast_good": "preset_fast",
            "moai_rain": "preset_moai",
            "vendor_paradise": "preset_vendor",
            "double_microwave": "preset_micro",
            "double_microwave_white": "preset_micro_white",
            "graveyard_bald_heads": "preset_graveyard_bald",
        }
        for pid, btn in self.preset_buttons.items():
            key = preset_key_map.get(pid)
            if key:
                btn.config(text=self.t(key))

        self.chk_combo.config(text=self.t("combo_chk"))
        self.update_tab4_items_label()
        if hasattr(self, "chk_combo_golden"):
            self.chk_combo_golden.config(text=self.t("combo_golden_chk"))
        if hasattr(self, "update_tab4_golden_label"):
            self.update_tab4_golden_label()
        if hasattr(self, "restore_preset_info"):
            self.restore_preset_info()
        self.lbl_score_meter_title.config(text=self.t("score_meter_title"))

        # Botroles inferiores
        self.btn_action.config(text=self.t("btn_stop") if self.is_running else self.t("btn_start"))
        self.btn_test_reset.config(text=self.t("btn_test_reset"))
        if hasattr(self, "btn_logs"):
            self.btn_logs.config(text=self.t("btn_logs"))
        self.badge_afk.config(text=self.t("badge_afk"))

        self.update_menu_language()

        # Actualizar estado de objetivo de preset o tier
        if self.score_submode.get() == "tier":
            self.on_select_tier()
        else:
            self.apply_preset_template(self.selected_template.get())

    def on_exit(self):
        self.is_running = False
        if hasattr(self, "telemetry") and self.telemetry:
            try:
                self.telemetry.stop()
            except Exception as exc:
                self.reader.set_high_priority(False)
                log_event(f"No se pudo guardar al cerrar: {exc}", level="ERROR")
                messagebox.showerror("Telemetría", "No se pudo guardar el registro pendiente.\nLa ventana seguirá abierta para poder reintentar el cierre.")
                return
        self.is_closing = True
        self._closing_event.set()
        # Tcl timers can outlive widget commands when another Tk instance is
        # created later in the same process. Cancel them before destruction.
        for after_id in self.tk.splitlist(self.tk.call("after", "info")):
            self.after_cancel(after_id)
        if hasattr(self, "powerup_overlay") and self.powerup_overlay:
            try:
                self.powerup_overlay.window.destroy()
            except Exception:
                pass
        self.reader.close()
        self.destroy()

    def update_tab4_items_label(self):
        if not hasattr(self, "lbl_tab4_items_preview"):
            return
        if self.selected_items:
            names = []
            for s in self.selected_items:
                n = s[4] if self.current_lang == "pt" else (s[3] if self.current_lang == "en" else s[2])
                it_id = s[0]
                p_var = self.item_max_prices.get(it_id)
                p_val = p_var.get().strip() if isinstance(p_var, tk.StringVar) else str(p_var or "").strip()
                if p_val and p_val.isascii() and p_val.isdecimal() and len(p_val) <= 9 and int(p_val) > 0:
                    names.append(f"{n} (≤{p_val}g)")
                else:
                    names.append(n)
            status_color = COLOR_BORDER_GLOW if self.require_mode1_items.get() else COLOR_TEXT_DIM
            prefix = self.t("combo_active") if self.require_mode1_items.get() else self.t("combo_inactive")
            self.lbl_tab4_items_preview.config(
                text=f"{prefix}{' + '.join(names)} ({len(self.selected_items)}/3)",
                fg=status_color
            )
        else:
            self.lbl_tab4_items_preview.config(
                text=self.t("combo_none"),
                fg=COLOR_TEXT_DIM
            )

    def update_tab4_golden_label(self):
        if not hasattr(self, "lbl_tab4_golden_preview"):
            return
        g_count = self.target_golden_vendors.get()
        crowns = "👑" * g_count
        if self.require_golden_vendors.get():
            txt = self.t("combo_golden_active", count=g_count, crowns=crowns)
            self.lbl_tab4_golden_preview.config(text=txt, fg=COLOR_GOLD)
        else:
            txt = self.t("combo_golden_inactive", count=g_count, crowns=crowns)
            self.lbl_tab4_golden_preview.config(text=txt, fg=COLOR_TEXT_DIM)

    def on_preset_hover(self, preset_id):
        data = self.preset_details(preset_id)
        if data and hasattr(self, "lbl_preset_hover_title"):
            self.lbl_preset_hover_title.config(text=f"{data['title']}  |  {data['tier']}", fg=COLOR_GOLD)
            self.lbl_preset_hover_desc.config(text=data['reqs'], fg=COLOR_TEXT)

    def on_preset_leave(self):
        self.restore_preset_info()

    def restore_preset_info(self):
        if not hasattr(self, "lbl_preset_hover_title"):
            return
        curr_pid = self.selected_template.get()
        data = self.preset_details(curr_pid)
        if data and self.score_submode.get() == "template":
            pref = self.t("preset_active_pref")
            self.lbl_preset_hover_title.config(text=f"{pref} {data['title']} ({data['tier']})", fg=COLOR_BORDER_GLOW)
            self.lbl_preset_hover_desc.config(text=data['reqs'], fg=COLOR_TEXT_DIM)
        else:
            self.lbl_preset_hover_title.config(text=self.t("preset_hover_hint"), fg=COLOR_BORDER_GLOW)
            self.lbl_preset_hover_desc.config(text=self.t("preset_hover_default"), fg=COLOR_TEXT_DIM)

    def on_select_tier(self):
        self.score_submode.set("tier")
        tier = self.target_tier.get()
        t_info = TIER_INFO.get(tier, {})
        label = t_info.get('label', tier)
        min_score = t_info.get('min_score', 0)
        self.lbl_preset_active.config(
            text=self.t("target_mode_direct", label=label, min_score=min_score),
            fg=t_info.get("color", COLOR_GOLD)
        )
        self.restore_preset_info()
        self.update_preset_selection()

    def apply_preset_template(self, preset_id):
        tmpl = PRESET_TEMPLATES.get(preset_id)
        if not tmpl:
            return
        self.score_submode.set("template")
        self.selected_template.set(preset_id)
        self.target_tier.set(tmpl["tier"])
        name = self.t(PRESET_KEYS[preset_id])
        tier = tmpl["tier"]
        min_score = tmpl["min_score"]
        self.lbl_preset_active.config(
            text=self.t("target_preset_active", name=name, tier=tier, min_score=min_score),
            fg=COLOR_GOLD
        )
        self.restore_preset_info()
        self.update_preset_selection()

    def update_live_score_ui(self, stats):
        score = stats.get("score", 0.0)
        tier = stats.get("tier", "Normal")
        t_info = TIER_INFO.get(tier, {})
        tier_label = t_info.get("label", tier)
        if tier == "Normal":
            tier_label = self.t("tier_standard")

        score_lbl = self.t("stat_score")
        tier_lbl = self.t("stat_tier")

        self.lbl_live_score_val.config(
            text=f"{score_lbl}: {score:.2f} pts  |  {tier_lbl}: {tier_label}",
            fg=t_info.get("color", COLOR_GOLD)
        )

    def switch_mode(self, mode):
        if self.is_running or mode not in SEARCH_MODES:
            return
        self.selected_mode.set(mode)
        tabs = {1: (self.tab1_frame, self.btn_tab1, COLOR_BORDER_GLOW),
                2: (self.tab2_frame, self.btn_tab2, COLOR_GOLD),
                4: (self.tab4_frame, self.btn_tab4, COLOR_GOLD)}
        for frame, btn, _ in tabs.values():
            frame.pack_forget()
            btn.config(bg=COLOR_CARD, fg=COLOR_TEXT_DIM)
        frame, btn, color = tabs[mode]
        frame.pack(fill="both", expand=True)
        btn.config(bg=COLOR_CARD_ALT, fg=color)
        if mode == 4:
            self.update_tab4_items_label()
            self.update_tab4_golden_label()
            self.restore_preset_info()

    def test_quick_reset(self):
        if self.is_running or self._testing_reset:
            return
        self._testing_reset = True
        self.btn_action.config(state="disabled")
        self.btn_test_reset.config(state="disabled")
        def worker():
            try:
                if not self.reader.find_process():
                    self.safe_ui_update(messagebox.showwarning, self.t("alert_game_not_found_title"),
                                        self.t("alert_game_not_found_msg"))
                    return
                # Clicking this button puts Helper in front; focus the game before
                # the same PID guard used by the normal search sends any input.
                focused = self.bot.focus_game(pid=self.reader.pid)
                ok = focused and self.bot.trigger_restart(pid=self.reader.pid)
                if ok:
                    self.safe_ui_update(self.lbl_status.config, text=self.t("status_quick_reset_sent"), fg=COLOR_GREEN)
                else:
                    self.safe_ui_update(messagebox.showerror, self.t("alert_reset_error_title"),
                                        self.t("alert_reset_error_msg"))
            except Exception as exc:
                log_event(f"Error al probar reinicio: {exc}", level="ERROR")
                self.safe_ui_update(self.lbl_status.config, text=self.t("alert_reset_error_msg"), fg=COLOR_RED)
            finally:
                self.safe_ui_update(self._finish_test_reset)
        threading.Thread(target=worker, daemon=True).start()

    def _finish_test_reset(self):
        self._testing_reset = False
        self.btn_action.config(state="normal")
        self.btn_test_reset.config(state="disabled" if self.is_running else "normal")

    def open_log_file(self):
        try:
            if not os.path.exists(LOG_FILE_PATH):
                log_event("Archivo de log inicializado por el usuario.", level="INFO")
            os.startfile(LOG_FILE_PATH)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo de log: {e}")

    # ==========================================================
    # ATAJOS GLOBALES DE TECLADO (F5: BUSQUEDA, F6: OVERLAY POWERUPS)
    # ==========================================================
    def trigger_f5_action(self):
        with self._hotkey_lock:
            now = time.monotonic()
            if now - self._last_f5_time < 0.35:
                return
            self._last_f5_time = now
        self.safe_ui_update(self.toggle_search)

    def trigger_f6_action(self):
        with self._hotkey_lock:
            now = time.monotonic()
            if now - self._last_f6_time < 0.35:
                return
            self._last_f6_time = now
        self.safe_ui_update(self.toggle_powerup_overlay)

    def toggle_powerup_overlay(self):
        if hasattr(self, "powerup_overlay") and self.powerup_overlay:
            is_vis = self.powerup_overlay.toggle()
            if is_vis:
                self._overlay_enabled.set()
            else:
                self._overlay_enabled.clear()
            badge_text = "⚡ HUD [F6]: ON" if is_vis else "⚡ HUD [F6]: OFF"
            badge_fg = "#10B981" if is_vis else "#64748B"
            if hasattr(self, "btn_overlay_toggle") and self.btn_overlay_toggle:
                self.btn_overlay_toggle.config(text=f"⚡ HUD Powerups [F6]: {'ON' if is_vis else 'OFF'}", fg=badge_fg)
            if hasattr(self, "btn_header_overlay") and self.btn_header_overlay:
                self.btn_header_overlay.config(text=badge_text, fg=badge_fg)

    def show_audit_powerups_dialog(self):
        """Muestra una ventana modal de auditoría en vivo del contador de powerups"""
        dialog = tk.Toplevel(self)
        dialog.title("🔍 Auditoría de Memoria - HUD Powerups")
        dialog.geometry("700x520")
        dialog.configure(bg="#0B0E14")
        dialog.transient(self)

        # Encabezado
        header_frame = tk.Frame(dialog, bg="#111827", padx=14, pady=10)
        header_frame.pack(fill="x")
        lbl_title = tk.Label(
            header_frame,
            text="Auditoría de Memoria IL2CPP (Powerups & Time)",
            font=("Bahnschrift", 12, "bold"),
            fg="#F8FAFC",
            bg="#111827"
        )
        lbl_title.pack(side="left")

        # Área de texto
        text_frame = tk.Frame(dialog, bg="#0B0E14", padx=10, pady=10)
        text_frame.pack(fill="both", expand=True)

        txt_audit = tk.Text(
            text_frame,
            bg="#030712",
            fg="#E2E8F0",
            insertbackground="#38BDF8",
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            padx=10,
            pady=10
        )
        scroll = tk.Scrollbar(text_frame, command=txt_audit.yview)
        txt_audit.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt_audit.pack(side="left", fill="both", expand=True)

        txt_audit.insert("1.0", "⏳ Ejecutando diagnóstico de punteros y memoria en vivo...\nEspere un momento...")
        txt_audit.config(state="disabled")

        # Botones inferiores
        bottom_bar = tk.Frame(dialog, bg="#111827", padx=14, pady=8)
        bottom_bar.pack(fill="x")

        def run_audit_worker():
            try:
                import audit_powerups
                report = audit_powerups.get_audit_report_text()
            except Exception as e:
                report = f"❌ Error ejecutando auditoría: {e}"

            def update_text():
                if not dialog.winfo_exists():
                    return
                txt_audit.config(state="normal")
                txt_audit.delete("1.0", "end")
                txt_audit.insert("1.0", report)
                txt_audit.config(state="disabled")

            self.safe_ui_update(update_text)

        def copy_to_clipboard():
            try:
                content = txt_audit.get("1.0", "end-1c")
                self.clipboard_clear()
                self.clipboard_append(content)
                btn_copy.config(text="✅ Copiado!")
                dialog.after(1500, lambda: btn_copy.config(text="📋 Copiar Reporte") if dialog.winfo_exists() else None)
            except Exception:
                pass

        btn_copy = tk.Button(
            bottom_bar,
            text="📋 Copiar Reporte",
            font=("Bahnschrift", 9),
            bg="#1E293B",
            fg="#38BDF8",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=copy_to_clipboard
        )
        btn_copy.pack(side="left", padx=4)

        btn_rerun = tk.Button(
            bottom_bar,
            text="🔄 Re-ejecutar",
            font=("Bahnschrift", 9),
            bg="#1E293B",
            fg="#F8FAFC",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: [
                txt_audit.config(state="normal"),
                txt_audit.delete("1.0", "end"),
                txt_audit.insert("1.0", "⏳ Re-ejecutando diagnóstico en vivo...\n"),
                txt_audit.config(state="disabled"),
                threading.Thread(target=run_audit_worker, daemon=True).start()
            ]
        )
        btn_rerun.pack(side="left", padx=4)

        btn_close = tk.Button(
            bottom_bar,
            text="Cerrar",
            font=("Bahnschrift", 9),
            bg="#334155",
            fg="#F8FAFC",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=dialog.destroy
        )
        btn_close.pack(side="right", padx=4)

        # Ejecutar en segundo plano
        threading.Thread(target=run_audit_worker, daemon=True).start()

    def start_powerup_overlay_loop(self):
        self._powerup_thread = threading.Thread(
            target=self._powerup_reader_loop, daemon=True, name="PowerupReader"
        )
        self._powerup_thread.start()
        self._update_powerup_overlay_tick()

    def _powerup_reader_loop(self):
        while not self._closing_event.is_set():
            delay = 0.25
            if self._overlay_enabled.is_set():
                try:
                    data = self.reader.read_active_powerups()
                    with self._powerup_lock:
                        self._powerup_sample = (time.monotonic(), data)
                    delay = 0.05 if data.get("powerups") else 0.1
                    if not self.reader.handle:
                        delay = 0.5
                except Exception as exc:
                    log_event(f"Lectura del HUD fallida: {exc}", level="WARN")
            self._closing_event.wait(delay)

    def _update_powerup_overlay_tick(self):
        if self.is_closing:
            return
        next_delay = 50
        try:
            overlay = getattr(self, "powerup_overlay", None)
            if overlay and overlay.is_visible:
                with self._powerup_lock:
                    sampled_at, data = self._powerup_sample
                if data and time.monotonic() - sampled_at < 1.0:
                    has_powerups = bool(data and data.get("powerups"))
                    overlay.update_data(data)
                    # Si no hay powerups activos (00:00), sondeo a 10 Hz (100ms) para 0 impacto CPU/DWM
                    # Si hay powerup activo, 20 Hz (50ms) para transición fluida
                    next_delay = 50 if has_powerups else 100
                else:
                    overlay.render_idle()
                    # Juego cerrado o desconectado: verificar cada 250ms sin llamadas pesadas de proceso
                    next_delay = 250
            else:
                next_delay = 200
        except Exception:
            pass
        self.after(next_delay, self._update_powerup_overlay_tick)

    def start_hotkey_listener(self):
        t = threading.Thread(target=self.hotkey_listener_loop, daemon=True)
        t.start()

    def hotkey_listener_loop(self):
        """
        Sondea el estado fisico de las teclas F5 y F6 en todo Windows (GetAsyncKeyState & 0x8000).
        Responde en menos de 20ms sin importar el foco, incluso en pantalla completa DirectX.
        """
        f5_was_down = False
        f6_was_down = False
        while not self.is_closing:
            try:
                # 0x74 = VK_F5 (Iniciar/Detener Busqueda)
                f5_is_down = bool(user32.GetAsyncKeyState(0x74) & 0x8000)
                if f5_is_down and not f5_was_down:
                    self.trigger_f5_action()
                f5_was_down = f5_is_down

                # 0x75 = VK_F6 (Activar/Desactivar Overlay Powerups)
                f6_is_down = bool(user32.GetAsyncKeyState(0x75) & 0x8000)
                if f6_is_down and not f6_was_down:
                    self.trigger_f6_action()
                f6_was_down = f6_is_down
            except Exception:
                pass
            time.sleep(0.02)

    # ==========================================================
    # MONITOR DE CONEXION EN SEGUNDO PLANO
    # ==========================================================
    def start_background_monitor(self):
        t = threading.Thread(target=self.monitor_loop, daemon=True)
        t.start()

    def safe_ui_update(self, func, *args, **kwargs):
        if self.is_closing:
            return
        self._ui_queue.put((func, args, kwargs))

    def _drain_ui_queue(self):
        if self.is_closing:
            return
        for _ in range(100):
            try:
                func, args, kwargs = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                func(*args, **kwargs)
            except tk.TclError:
                pass  # The target dialog may have been closed in the meantime.
            except Exception as exc:
                log_event(f"Error al actualizar la interfaz: {exc}", level="ERROR")
        self.after(20, self._drain_ui_queue)

    def monitor_loop(self):
        while not self.is_closing:
            try:
                connected = self.reader.find_process()
                if connected and self.reader.ga_base:
                    # Desbloquear automáticamente si el juego fue reiniciado con nuevo PID limpio
                    if self.bloated_game_blocked and self.reader.pid != self.bloated_pid:
                        self.bloated_game_blocked = False
                        self.bloated_pid = None
                        self.consecutive_slow_reloads = 0
                        self.recent_reloads = []

                    # Pre-calentamiento en segundo plano del heap para que la 1ra búsqueda sea instantánea (< 90ms)
                    if not self.reader._cached_heap_regions:
                        self.reader.refresh_cached_heap_regions()

                    in_game = self.reader.is_in_game()
                    if in_game:
                        self.safe_ui_update(self.status_conn_lbl.config, text=self.t("game_in_match"), fg=COLOR_GREEN)
                        if not self.is_running:
                            s = self.reader.read_interactables_status()
                            if s and any(isinstance(v, (int, float)) and v > 0 for v in s.values()):
                                self.safe_ui_update(self.update_live_score_ui, s)
                    else:
                        self.safe_ui_update(self.status_conn_lbl.config, text=self.t("game_connected"), fg=COLOR_BLUE)
                else:
                    self.safe_ui_update(self.status_conn_lbl.config, text=self.t("game_closed"), fg=COLOR_RED)
            except Exception:
                pass
            time.sleep(0.5)

    # ==========================================================
    # TRABAJADOR DE BUSQUEDA (BOT WORKER)
    # ==========================================================
    def start_bot_worker(self):
        t = threading.Thread(target=self.bot_worker_loop, daemon=True)
        t.start()

    def bot_worker_loop(self):
        while not self.is_closing:
            if not self.is_running:
                time.sleep(0.05)
                continue

            try:
                self.bot_step()
            except Exception as e:
                import traceback
                err_tb = traceback.format_exc()
                log_event(f"❌ ERROR EN BÚSQUEDA: {e}\n{err_tb}", level="ERROR")
                time.sleep(0.5)

            # Pausa breve entre ciclos de búsqueda para máxima velocidad y respuesta inmediata a F5
            time.sleep(0.02)

    def toggle_search(self):
        if self.is_running:
            self.stop_search(self.t("status_stopped_user"))
        else:
            self.start_search()

    def start_search(self):
        if self._testing_reset:
            return False
        mode = self.selected_mode.get()
        try:
            config = capture_configuration(self)
        except ValueError as exc:
            self.lbl_status.config(text=str(exc), fg=COLOR_RED)
            return False
        if mode == 1 and not self.selected_items:
            msg = "Debes seleccionar al menos 1 item en el Modo 1 antes de iniciar la busqueda." if self.current_lang == "es" else "You must select at least 1 item in Mode 1 before starting search."
            self.lbl_status.config(text=f"⚠️ {msg}", fg="#EF4444")
            self.lift()
            return False

        if mode == 4 and self.require_mode1_items.get() and not self.selected_items:
            msg = self.t("alert_combo_no_items_msg")
            self.lbl_status.config(text=f"⚠️ {msg}", fg="#EF4444")
            self.lift()
            return False

        # 1. Comprobar si el juego fue bloqueado por lentitud/saturación previa
        if self.bloated_game_blocked:
            if self.reader and self.reader.pid and self.reader.pid == self.bloated_pid:
                self.bot.trigger_warning_beep()
                msg = self.t("alert_restart_required_msg", avg=4.5)
                self.lbl_status.config(text=f"⚠️ {self.t('alert_restart_required_title')}", fg="#EF4444")
                self.lift()
                messagebox.showwarning(self.t("alert_restart_required_title"), msg)
                return False
            else:
                # El proceso cambió (nuevo PID) -> Desbloquear!
                self.bloated_game_blocked = False
                self.bloated_pid = None
                self.consecutive_slow_reloads = 0
                self.recent_reloads = []

        self._search_config = config
        self.attempt_count = 1
        self.start_time = time.time()
        self.match_found = False
        self.last_seed = None
        self.last_reroll_time = None
        self.last_map_sig = None
        self.last_activity_time = time.time()
        self.current_map_detected_time = time.time()
        self.is_focus_paused = False
        self.watchdog_stalls_count = 0
        self._logged_item_timing = False
        self.waiting_for_scene_reload = False
        self.saw_zero_interactables = False
        self.generation_seen = False
        if self.reader:
            # Optimización de arranque: mantener y precalentar el heap para que el Intento #1 sea tan rápido como el #2 (< 90ms)
            # Heap warming belongs to the background monitor, never the Tk thread.
            self.reader._cached_vendor_regions = []
            self.reader._cached_microwave_regions = []
            self.reader.set_high_priority(True)

        # Traer Megabonk al primer plano de forma limpia si esta en segundo plano
        if self.reader.pid:
            self.bot.focus_game(pid=self.reader.pid)

        self.btn_action.config(
            text=self.t("btn_stop"),
            bg=COLOR_RED,
            activebackground="#B91C1C"
        )
        self.lbl_status.config(text=self.t("status_running"), fg=COLOR_BORDER_GLOW)
        self.set_menu_editable(False)
        self.is_running = True

        # Feedback sonoro al iniciar búsqueda F5
        try:
            threading.Thread(target=lambda: (kernel32.Beep(800, 80), kernel32.Beep(1100, 100)), daemon=True).start()
        except Exception:
            pass

        log_event(f"Iniciando búsqueda automática en Modo {mode}. Tecla F5 activa.", level="START")
        if mode == 4:
            items_str = ""
            if self.require_mode1_items.get() and self.selected_items:
                i_desc = []
                for s in self.selected_items:
                    tid, _, es_n, en_n, pt_n = s[:5]
                    n = pt_n if self.current_lang == "pt" else (en_n if self.current_lang == "en" else es_n)
                    p_var = self.item_max_prices.get(tid)
                    p_val = p_var.get().strip() if hasattr(p_var, "get") else str(p_var or "").strip()
                    if p_val and p_val.isascii() and p_val.isdecimal() and len(p_val) <= 9 and int(p_val) > 0:
                        i_desc.append(f"{n} (≤{p_val}g)")
                    else:
                        i_desc.append(n)
                items_str = f", Exigir items Modo 1={self.require_mode1_items.get()} [{', '.join(i_desc)}]"
            else:
                items_str = f", Exigir items Modo 1={self.require_mode1_items.get()}"
            log_event(f"Modo 4 configurado: Submodo={self.score_submode.get()}, Tier={self.target_tier.get()}, Plantilla={self.selected_template.get()}{items_str}, Exigir dorados={self.require_golden_vendors.get()} ({self.target_golden_vendors.get()} dorados)", level="CONFIG")
        elif mode == 1:
            item_desc = []
            for s in self.selected_items:
                tid, _, es_n, en_n, pt_n = s[:5]
                n = pt_n if self.current_lang == "pt" else (en_n if self.current_lang == "en" else es_n)
                p_var = self.item_max_prices.get(tid)
                p_val = p_var.get().strip() if hasattr(p_var, "get") else str(p_var or "").strip()
                if p_val and p_val.isascii() and p_val.isdecimal() and len(p_val) <= 9 and int(p_val) > 0:
                    item_desc.append(f"{n} (≤{p_val}g)")
                else:
                    item_desc.append(n)
            log_event(f"Modo 1 configurado: Items requeridos: {', '.join(item_desc)}", level="CONFIG")
        elif mode == 2:
            log_event(f"Modo 2 configurado: Vendedores dorados requeridos: {self.target_golden_vendors.get()}", level="CONFIG")
        return True

    def stop_search(self, msg=""):
        self.is_running = False
        self.safe_ui_update(self.set_menu_editable, True)
        if self.reader:
            self.reader.set_high_priority(False)
        self.last_reroll_time = None
        self.current_map_detected_time = None
        self._logged_item_timing = False
        self.waiting_for_scene_reload = False
        self.saw_zero_interactables = False
        self.safe_ui_update(self.btn_action.config,
            text=self.t("btn_start"),
            bg="#0284C7",
            activebackground="#0369A1"
        )

        # Feedback sonoro al detener búsqueda
        try:
            threading.Thread(target=lambda: (kernel32.Beep(800, 80), kernel32.Beep(600, 100)), daemon=True).start()
        except Exception:
            pass

        if msg:
            self.safe_ui_update(self.lbl_status.config, text=msg, fg=COLOR_TEXT)
            log_event(f"Búsqueda detenida: {msg}", level="STOP")
        else:
            log_event("Búsqueda detenida por el usuario.", level="STOP")

    def _check_reload_performance(self, reload_dur):
        """
        Monitorea si las recargas se vuelven lentas debido a degradacion o fuga de memoria de Unity tras jugar mucho rato.
        Usa ventana móvil de las últimas recargas para evitar que mapas vacíos de 1s reseteen el estado de lentitud.
        """
        if reload_dur is None or reload_dur <= 0:
            return

        self.recent_reloads.append(reload_dur)
        if len(self.recent_reloads) > 4:
            self.recent_reloads.pop(0)

        # Contar cuántas recargas lentas (> 4.2s) hay en las muestras recientes
        slow_count = sum(1 for d in self.recent_reloads if d > 4.2)
        avg_dur = sum(self.recent_reloads) / len(self.recent_reloads)

        # Disparar si hay al menos 2 recargas lentas o promedio de recargas supera 4.5s
        if (len(self.recent_reloads) >= 2 and slow_count >= 2) or (len(self.recent_reloads) >= 3 and avg_dur > 4.5):
            ws_mb, priv_mb = self.reader.get_process_memory_mb() if self.reader else (0.0, 0.0)
            self.bloated_game_blocked = True
            self.bloated_pid = self.reader.pid if self.reader else None
            log_event(
                f"⚠️ Degradación crítica detectada: Recargas lentas recurrentes (Promedio: {avg_dur:.1f}s, Muestras: {[round(x,1) for x in self.recent_reloads]}, RAM: {int(priv_mb)}MB). Bloqueando búsqueda...",
                level="WARN"
            )
            self.stop_search(self.t("alert_restart_required_title"))
            self.bot.trigger_warning_beep()
            msg = self.t("alert_restart_required_msg", avg=avg_dur)
            self.safe_ui_update(
                self.lbl_status.config,
                text=f"⚠️ {self.t('alert_restart_required_title')}",
                fg="#EF4444"
            )
            self.safe_ui_update(lambda: messagebox.showwarning(
                self.t("alert_restart_required_title"),
                msg
            ))

    def trigger_reroll_step(self):
        if not self.is_running:
            return
        self.attempt_count += 1
        self._logged_item_timing = False
        self.waiting_for_scene_reload = True
        self.saw_zero_interactables = False
        self.generation_seen = False
        self.safe_ui_update(
            self.lbl_status.config,
            text=self.t("status_resetting", count=self.attempt_count),
            fg=COLOR_BORDER_GLOW
        )
        self.last_reroll_time = time.time()
        self._reroll_started_at = time.perf_counter()
        self.current_map_detected_time = None
        if self.reader:
            self.reader._cached_vendor_regions = []
            self.reader._cached_microwave_regions = []
        sent = self.bot.trigger_restart(pid=self.reader.pid)
        self._last_reset_input_ms = (time.perf_counter() - self._reroll_started_at) * 1000
        if not sent:
            self.waiting_for_scene_reload = False
            self.last_reroll_time = None
            msg = {"es": "No se pudo enviar R: comprobá el foco y el reinicio rápido del juego.",
                   "en": "Could not send R: check game focus and quick reset settings.",
                   "pt": "Não foi possível enviar R: confira o foco e o reinício rápido do jogo."}
            log_event(msg.get(self.current_lang, msg["es"]), level="WARN")
            self.stop_search(msg.get(self.current_lang, msg["es"]))

    def handle_target_found(self, stats, vendors=None):
        self.match_found = True
        self.stop_search()

        log_event(f"🎉 ¡PARTIDA OBJETIVO CONFIRMADA EN EL INTENTO #{self.attempt_count}!", level="SUCCESS")
        if vendors:
            v_desc = []
            for idx, v in enumerate(vendors):
                r_name = v.get("rarity_name", "")
                i_names = v.get("item_names", [])
                i_prices = v.get("item_prices", [])
                i_parts = []
                for i_idx, name in enumerate(i_names):
                    p = i_prices[i_idx] if i_idx < len(i_prices) else 0
                    i_parts.append(f"{name} ({p}g)" if p > 0 else name)
                v_desc.append(f"V#{idx+1}({r_name}): [{', '.join(i_parts)}]")
            if v_desc:
                log_event(f"Detalle Vendedores: {' | '.join(v_desc)}", level="SUCCESS")
                summary_text = f"Vendedores: {' | '.join(v_desc)}"
                self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

        # 1. PAUSA DE SEGURIDAD AFK INMEDIATA (lo primero en ejecutarse para proteger al jugador)
        try:
            if not self.bot.trigger_afk_safety_pause(pid=self.reader.pid):
                log_event("No se pudo confirmar la pulsación de pausa AFK", level="WARN")
        except Exception as e:
            log_event(f"Error al activar pausa de seguridad: {e}", level="WARN")


        # 3. Actualizar estado de la interfaz
        self.safe_ui_update(
            self.lbl_status.config,
            text=self.t("status_found", count=self.attempt_count),
            fg=COLOR_GREEN
        )

    def bot_step(self):
        if not self.is_running:
            return

        now = time.time()

        # 1. Comprobar conexion con el proceso
        if not self.reader.find_process():
            self.safe_ui_update(self.lbl_status.config, text=self.t("status_waiting_game"), fg=COLOR_RED)
            if now - self.last_activity_time > 5.0:
                log_event("Esperando a que Megabonk.exe sea iniciado...", level="WAIT")
                self.last_activity_time = now
            return

        # 2. Comprobar foco de la ventana de Megabonk (Watchdog de Foco pasivo)
        if not self.bot.is_game_window_active(pid=self.reader.pid):
            if not self.is_focus_paused:
                self.is_focus_paused = True
                self.safe_ui_update(
                    self.lbl_status.config,
                    text="⏸️ En pausa: Haz clic en la ventana de Megabonk para continuar",
                    fg=COLOR_GOLD
                )
                log_event("Megabonk en segundo plano. Búsqueda en pausa pasiva...", level="PAUSE")
            time.sleep(0.2)
            return
        else:
            if self.is_focus_paused:
                self.is_focus_paused = False
                log_event("Megabonk en primer plano. Reanudando búsqueda...", level="RESUME")

        mode = search_setting(self, 'selected_mode')
        # Verificación ultrarrápida del estado de la partida (< 1ms). CERO escaneo de heap durante carga/reset.
        data = self.reader.get_full_map_data(scan_vendors=False)
        stats = data.get("stats", {})
        total_interactables = sum(v for k, v in stats.items() if isinstance(v, (int, float)) and k not in ("score",)) if stats else 0

        # Verificación de ciclo de vida nativo de Unity (BonkScanner):
        # Unity aún está generando, reiniciando, en pantalla de carga fade, o sin mapa cargado
        gen_state = self.reader.get_map_generation_state()
        is_gen = gen_state.get("is_generating", False)
        is_reset = gen_state.get("is_resetting", False)
        is_loading = gen_state.get("is_loading", False)
        has_loaded_map = gen_state.get("has_loaded_map", False)

        current_seed = gen_state.get("map_seed")

        # 3. Comprobar si estamos esperando la recarga de escena tras enviar 'R'
        if self.waiting_for_scene_reload:
            time_since_reroll = (now - self.last_reroll_time) if self.last_reroll_time else 0.0

            # Watchdog global: si tras 5.0s nunca se completó el reinicio ('R' no registrado o congelamiento), reintentar
            # Se evalúa antes de cualquier estado de carga para no quedar atrapado en cargas lentas de Unity
            if time_since_reroll > 5.0:
                log_event("⚠️ WATCHDOG: La partida no reinició tras 5.0s de enviar 'R'. Reintentando...", level="WARN")
                self.bot.trigger_warning_beep()
                self.last_reroll_time = now
                self.generation_seen = False
                self.saw_zero_interactables = False
                self.bot.trigger_restart(pid=self.reader.pid)
                return

            if is_gen or is_reset or is_loading or not has_loaded_map or total_interactables < 6:
                self.saw_zero_interactables = True
                self.generation_seen = True
                self.safe_ui_update(self.lbl_status.config, text=self.t("status_waiting_match"), fg=COLOR_GOLD)
                return
            else:
                # El nuevo mapa está 100% listo cuando:
                # 1) Hay interactuables poblados (mínimo 6)
                # 2) Unity no está en pantalla de carga (not is_loading)
                # 3) Tiene un mapa y fase instanciados (has_loaded_map)
                # 4) Pasó el tiempo físico mínimo de fade (mínimo 1.10s)
                # 5) Hay evidencia de transición: carga/vaciado observado o semilla distinta
                if time_since_reroll < 1.10:
                    return

                definite_seed_change = (current_seed is not None and self.last_seed is not None
                                        and current_seed != self.last_seed)
                if not (self.generation_seen or self.saw_zero_interactables or definite_seed_change):
                    # Sin transición observada ni semilla nueva, podría ser el mapa anterior.
                    return

                seed_changed = False
                if current_seed is not None and self.last_seed is not None:
                    seed_changed = (current_seed != self.last_seed)
                elif self.saw_zero_interactables or time_since_reroll > 2.0:
                    seed_changed = True

                if seed_changed or self.saw_zero_interactables:
                    # Monitoreo de salud/rendimiento de recarga tras partidas largas
                    reload_dur = (now - self.last_reroll_time) if self.last_reroll_time else 0.0
                    self._check_reload_performance(reload_dur)
                    reset_started = getattr(self, "_reroll_started_at", None)
                    if reset_started is not None:
                        ready_ms = (time.perf_counter() - reset_started) * 1000
                        input_ms = getattr(self, "_last_reset_input_ms", 0.0)
                        log_event(f"Recarga #{self.attempt_count}: R={input_ms:.1f}ms, "
                                  f"mapa_listo={ready_ms:.1f}ms, semilla_cambio={seed_changed}", level="PERF")

                    self.waiting_for_scene_reload = False
                    self.saw_zero_interactables = False
                    self.generation_seen = False
                    self.last_reroll_time = None
                    self.current_map_detected_time = None
                    if self.reader:
                        self.reader._cached_vendor_regions = []
                        self.reader._cached_microwave_regions = []
                        self.reader._last_vendor_heap_sweep_time = 0
                    if current_seed is not None:
                        self.last_seed = current_seed
                else:
                    return
        elif is_gen or is_reset or is_loading or not has_loaded_map or total_interactables < 6:
            self.current_map_detected_time = None
            self.safe_ui_update(self.lbl_status.config, text=self.t("status_waiting_match"), fg=COLOR_GOLD)
            return

        if self.current_map_detected_time is None:
            self.current_map_detected_time = now
        if current_seed is not None and self.last_seed is None:
            self.last_seed = current_seed

        self.last_activity_time = now

        # Actualizar contador de tiempo e intentos en UI
        elapsed = int(now - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.safe_ui_update(
            self.lbl_counter.config,
            text=f"{self.t('attempts')}: #{self.attempt_count}  |  {self.t('time')}: {mins:02d}:{secs:02d}"
        )

        # =========================================================================
        # CASO A: MODO 4 (Plantillas o Rangos) -> ORDEN ESTRICTO DEL USUARIO
        # =========================================================================
        if mode == 4:
            score_val = stats.get("score", 0.0)
            tier_val = stats.get("tier", "Normal")
            self.safe_ui_update(self.update_live_score_ui, stats)

            bald = stats.get("bald_heads", 0)
            bald_str = f" | Calvos: {bald}" if bald > 0 else ""
            white_detail = stats.get("microwaves_detail")
            white_m = stats.get("microwaves_white")
            white_m_str = f" ({white_detail})" if white_detail else (f" (⚪{white_m})" if white_m is not None else "")
            summary_text = (
                f"⭐ {self.t('stat_score')}: {score_val:.1f} [{tier_val}] | "
                f"Moáis: {stats.get('moais', 0)}{bald_str} | "
                f"Maldiciones: {stats.get('boss_curses', 0)} | "
                f"Micros: {stats.get('microwaves', 0)}{white_m_str} | "
                f"Cofres: {stats.get('chests', 0)}"
            )
            self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

            # PASO 1: Verificar si cumple la plantilla/tier (< 1ms)
            template_matches = self.evaluate_template_match(stats)

            if not template_matches:
                # Actualizar white_m si se calculó durante evaluate_template_match
                white_detail = stats.get("microwaves_detail")
                white_m = stats.get("microwaves_white")
                white_m_str = f" ({white_detail})" if white_detail else (f" (⚪{white_m})" if white_m is not None else "")
                # No cumple -> REINICIO INMEDIATO (< 0.35s)! Cero tiempo perdido en vendedores.
                log_event(
                    f"Intento #{self.attempt_count}: Score={score_val:.1f} ({tier_val}) | Moáis={stats.get('moais',0)}{bald_str} Mald={stats.get('boss_curses',0)} Micros={stats.get('microwaves',0)}{white_m_str} -> No cumple. Reiniciando...",
                    level="REROLL"
                )
                self.trigger_reroll_step()
                return

            # PASO 2: CUMPLIO LA PLANTILLA -> VERIFICAR SI TAMBIEN SE EXIGIERON OBJETOS
            white_detail = stats.get("microwaves_detail")
            white_m = stats.get("microwaves_white")
            white_m_str = f" ({white_detail})" if white_detail else (f" (⚪{white_m})" if white_m is not None else "")
            log_event(
                f"⭐ ¡PLANTILLA COINCIDE! Intento #{self.attempt_count}: Tier={tier_val}, Score={score_val:.1f} | Moáis={stats.get('moais',0)}{bald_str} Micros={stats.get('microwaves',0)}{white_m_str}",
                level="MATCH"
            )

            needs_vendors = (search_setting(self, 'require_mode1_items') and search_setting(self, 'selected_items')) or search_setting(self, 'require_golden_vendors')
            vendors = []
            if needs_vendors:
                self.safe_ui_update(
                    self.lbl_status.config,
                    text=f"⭐ Plantilla {tier_val} coincide! Escaneando vendedores...",
                    fg=COLOR_GOLD
                )
                log_event("⭐ Plantilla aprobada. Escaneando vendedores para verificar requisitos...", level="EVAL")
                num_map_vendors = stats.get("vendors_total", 0)
                expected_v = min(num_map_vendors, 3)

                if expected_v == 0:
                    log_event(f"-> La plantilla era {tier_val} pero el mapa no tiene vendedores. Reiniciando...", level="REROLL")
                    self.safe_ui_update(
                        self.lbl_status.config,
                        text=f"Plantilla {tier_val} ok, pero no hay vendedores. Reiniciando...",
                        fg=COLOR_GOLD
                    )
                    self.trigger_reroll_step()
                    return

                # Pre-filtro instantáneo de dorados
                if search_setting(self, 'require_golden_vendors'):
                    target_gold = search_setting(self, 'target_golden_vendors')
                    if num_map_vendors < target_gold:
                        log_event(f"-> La plantilla era {tier_val} pero faltan Vendedores Dorados (hay {num_map_vendors}/{target_gold}). Reiniciando...", level="REROLL")
                        self.safe_ui_update(
                            self.lbl_status.config,
                            text=f"Plantilla {tier_val} ok, pero faltan Dorados ({num_map_vendors}/{target_gold}). Reiniciando...",
                            fg=COLOR_GOLD
                        )
                        self.trigger_reroll_step()
                        return

                needs_items = search_setting(self, 'require_mode1_items') and search_setting(self, 'selected_items')
                time_since_map = (now - self.current_map_detected_time) if self.current_map_detected_time else 0.0

                # Grace period reactivo breve (0.05s) para escaneo ultra-temprano
                if time_since_map < 0.05:
                    return

                # Disparo ultrarrápido (< 1ms con caché de regiones)
                vendors = self.reader.scan_shady_vendors(expected_count=expected_v)
                vendors_with_items = sum(1 for v in vendors if v.get("item_ids"))

                # Si exige items y aún no se poblaron todos, esperar pasivamente hasta 0.35s
                if needs_items and vendors_with_items < expected_v and time_since_map < 0.35:
                    return

                v_desc = []
                for idx, v in enumerate(vendors):
                    r_name = v.get("rarity_name", "")
                    i_names = v.get("item_names", [])
                    i_prices = v.get("item_prices", [])
                    i_parts = []
                    for i_i, name in enumerate(i_names):
                        p = i_prices[i_i] if i_i < len(i_prices) else 0
                        i_parts.append(f"{name} ({p}g)" if p > 0 else name)
                    v_desc.append(f"V#{idx+1}({r_name}): [{', '.join(i_parts)}]")
                log_event(f"Vendedores encontrados ({len(vendors)}): {' | '.join(v_desc)}", level="EVAL")

                # 1. Comprobar Vendedores Dorados si está marcado
                if search_setting(self, 'require_golden_vendors'):
                    target_gold = search_setting(self, 'target_golden_vendors')
                    curr_gold = sum(1 for v in vendors if v.get("is_golden", False))
                    if curr_gold < target_gold:
                        log_event(f"-> La plantilla era {tier_val} pero faltan Vendedores Dorados (hay {curr_gold}/{target_gold}). Reiniciando...", level="REROLL")
                        self.safe_ui_update(
                            self.lbl_status.config,
                            text=f"Plantilla {tier_val} ok, pero faltan Dorados ({curr_gold}/{target_gold}). Reiniciando...",
                            fg=COLOR_GOLD
                        )
                        self.trigger_reroll_step()
                        return

                # 2. Comprobar Items de Modo 1 si está marcado
                if needs_items:
                    has_items, price_reason = self.check_vendors_have_items(vendors, search_setting(self, 'selected_items'))
                    if not has_items:
                        if price_reason:
                            log_event(f"-> La plantilla era {tier_val} pero supera precio máx: {price_reason}. Reiniciando...", level="REROLL")
                            self.safe_ui_update(
                                self.lbl_status.config,
                                text=f"Plantilla {tier_val} ok, pero precio alto: {price_reason}. Reiniciando...",
                                fg=COLOR_GOLD
                            )
                        else:
                            log_event(f"-> La plantilla era {tier_val} pero los vendedores no ofrecían los objetos pedidos. Reiniciando...", level="REROLL")
                            self.safe_ui_update(
                                self.lbl_status.config,
                                text=f"Plantilla {tier_val} ok, pero faltan items. Reiniciando...",
                                fg=COLOR_GOLD
                            )
                        self.trigger_reroll_step()
                        return

            # EXITO TOTAL: Cumplio plantilla y requisitos adicionales
            self.handle_target_found(stats, vendors)
            return

        # =========================================================================
        # CASO B: MODO 1 (Solo Objetos de Vendedores)
        # =========================================================================
        elif mode == 1:
            num_map_vendors = stats.get("vendors_total", 0)
            # Pre-filtro instantáneo en < 0.1ms: si el mapa no tiene suficientes vendedores
            if num_map_vendors < len(search_setting(self, 'selected_items')):
                log_event(f"Intento #{self.attempt_count}: Mapa solo tiene {num_map_vendors} vendedores (pedidos {len(search_setting(self, 'selected_items'))}). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            time_since_map = (now - self.current_map_detected_time) if self.current_map_detected_time else 0.0

            # 1. Grace period reactivo (0.05s): escaneo temprano ultra-ligero (< 0.1ms en C)
            if time_since_map < 0.05:
                return

            # 2. Escaneo reactivo: esperar pasivamente a que Unity popule los items
            expected_v = min(num_map_vendors, 3)
            force_rescan = (time_since_map > 0.40)
            vendors = self.reader.scan_shady_vendors(expected_count=expected_v, force_rescan=force_rescan)
            vendors_with_items = sum(1 for v in vendors if v.get("item_ids"))

            v_desc = []
            if vendors_with_items > 0:
                for idx, v in enumerate(vendors):
                    r_name = v.get("rarity_name", "")
                    i_names = v.get("item_names", [])
                    i_prices = v.get("item_prices", [])
                    i_parts = []
                    for i_i, name in enumerate(i_names):
                        p = i_prices[i_i] if i_i < len(i_prices) else 0
                        i_parts.append(f"{name} ({p}g)" if p > 0 else name)
                    v_desc.append(f"V#{idx+1}({r_name}): [{', '.join(i_parts)}]")
                summary_text = f"Vendedores: {' | '.join(v_desc)}"
                self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

            # Éxito temprano: si los vendedores que ya cargaron ya tienen los objetos requeridos y cumplen precio, terminar de inmediato!
            if vendors:
                has_items_early, _ = self.check_vendors_have_items(vendors, search_setting(self, 'selected_items'))
                if has_items_early:
                    if not self._logged_item_timing:
                        self._logged_item_timing = True
                        log_event(f"⏱️ Objetos de vendedores cargados en {int(time_since_map * 1000)}ms (Intento #{self.attempt_count}).", level="INFO")
                    log_event(f"⭐ ¡OBJETOS ENCONTRADOS! Intento #{self.attempt_count}", level="SUCCESS")
                    self.handle_target_found(stats, vendors)
                    return

            # Si los vendedores aún no tienen sus items (Unity ejecutando FindItems()):
            # Esperamos pasivamente cada tick (20ms) hasta un máximo de 0.45s
            if vendors_with_items < expected_v:
                if time_since_map < 0.45:
                    wait_ms = int(time_since_map * 1000)
                    self.safe_ui_update(
                        self.lbl_status.config,
                        text=f"⏳ Esperando objetos de vendedores... ({wait_ms}ms) [F5 para parar]",
                        fg=COLOR_GOLD
                    )
                    return
                # Si tras 450ms aún falta algún vendedor pero los cargados ya tienen el objeto y cumplen precio, éxito inmediato!
                if vendors:
                    has_items_timeout, _ = self.check_vendors_have_items(vendors, search_setting(self, 'selected_items'))
                    if has_items_timeout:
                        log_event(f"⭐ ¡OBJETOS ENCONTRADOS! Intento #{self.attempt_count}", level="SUCCESS")
                        self.handle_target_found(stats, vendors)
                        return
                # Timeout de seguridad: si tras 450ms nunca cargaron items suficientes, reiniciar
                v_diag = [f"{v.get('address')}(R:{v.get('rarity')},D:{v.get('done', 0)},Items:{len(v.get('item_ids',[]))})" for v in vendors]
                diag_str = f" [{', '.join(v_diag)}]" if v_diag else ""
                log_event(f"Intento #{self.attempt_count}: Timeout ({int(time_since_map*1000)}ms) esperando items de vendedores ({vendors_with_items}/{expected_v} listos, {len(vendors)} detectados){diag_str}. Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            # ¡LOS ITEMS YA APARECIERON EN MEMORIA!
            if not self._logged_item_timing:
                self._logged_item_timing = True
                log_event(f"⏱️ Objetos de vendedores cargados en {int(time_since_map * 1000)}ms (Intento #{self.attempt_count}).", level="INFO")

            has_items, price_reason = self.check_vendors_have_items(vendors, search_setting(self, 'selected_items'))
            if not has_items:
                if price_reason:
                    log_event(f"Intento #{self.attempt_count}: Objeto encontrado pero supera precio máx: {price_reason}. Reiniciando...", level="REROLL")
                else:
                    log_event(f"Intento #{self.attempt_count}: Vendedores no tienen los items buscados ({' | '.join(v_desc) if v_desc else 'Vacío'}). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            log_event(f"⭐ ¡OBJETOS ENCONTRADOS! Intento #{self.attempt_count}", level="SUCCESS")
            self.handle_target_found(stats, vendors)
            return

        # =========================================================================
        # CASO C: MODO 2 (Vendedores Dorados)
        # =========================================================================
        elif mode == 2:
            num_map_vendors = stats.get("vendors_total", 0)
            target_gold = search_setting(self, 'target_golden_vendors')
            if num_map_vendors < target_gold:
                log_event(f"Intento #{self.attempt_count}: Mapa solo tiene {num_map_vendors} vendedores (pedidos {target_gold} dorados). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            expected_v = min(num_map_vendors, 3)
            vendors = self.reader.scan_shady_vendors(expected_count=expected_v)
            golden_count = sum(1 for v in vendors if v.get("is_golden", False))
            stats["vendors_golden"] = golden_count

            v_desc = [f"V#{idx+1}({v.get('rarity_name', '')})" for idx, v in enumerate(vendors)]
            summary_text = f"Vendedores: {' | '.join(v_desc) if v_desc else self.t('status_reading')} [👑 Dorados: {golden_count}/{target_gold}]"
            self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

            if golden_count < target_gold:
                log_event(f"Intento #{self.attempt_count}: Vendedores dorados insuficientes ({golden_count}/{target_gold}). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            log_event(f"⭐ ¡VENDEDORES DORADOS ENCONTRADOS ({golden_count}/{target_gold})! Intento #{self.attempt_count}", level="SUCCESS")
            self.handle_target_found(stats, vendors)
            return

    def check_vendors_have_items(self, vendors, selected_items):
        """
        Verifica si todos los objetos seleccionados pueden ser comprados en la partida,
        garantizando que cada objeto provenga de un vendedor Shady Guy DIFERENTE
        (ya que cada vendedor solo permite comprar un único objeto por partida).
        Además, valida que el precio de cada objeto no supere el precio máximo configurado (si existe).
        Retorna una tupla: (exito: bool, motivo_rechazo_precio: str)
        """
        if not selected_items or not vendors:
            return False, ""

        target_ids = [s[0] for s in selected_items]
        num_targets = len(target_ids)

        # Si hay menos vendedores que objetos pedidos, es físicamente imposible comprar todos
        if len(vendors) < num_targets:
            return False, ""

        # Mapear precio máximo por objeto si el usuario lo configuró
        max_prices = {}
        target_names = {}
        for s in selected_items:
            tid = s[0]
            name = s[4] if self.current_lang == "pt" else (s[3] if self.current_lang == "en" else s[2])
            target_names[tid] = name
            p_var = search_setting(self, 'item_max_prices').get(tid)
            val_str = p_var.get().strip() if hasattr(p_var, "get") else str(p_var or "").strip()
            if val_str and val_str.isdigit() and int(val_str) > 0:
                max_prices[tid] = int(val_str)

        # Estructurar items y sus precios en cada vendedor
        vendor_maps = []
        for v in vendors:
            v_ids = v.get("item_ids", [])
            v_prices = v.get("item_prices", [])
            v_dict = {}
            for idx, i_id in enumerate(v_ids):
                price = v_prices[idx] if idx < len(v_prices) else 0
                previous = v_dict.get(i_id)
                if previous is None or (price > 0 and (previous <= 0 or price < previous)):
                    v_dict[i_id] = price
            vendor_maps.append(v_dict)

        items_matched_any = False
        rejection_reasons = []

        # Comprobar si existe una asignación inyectiva: un vendedor distinto para cada item pedido
        for vendor_perm in itertools.permutations(range(len(vendors)), num_targets):
            matches_items = True
            for i in range(num_targets):
                tid = target_ids[i]
                if tid not in vendor_maps[vendor_perm[i]]:
                    matches_items = False
                    break

            if not matches_items:
                continue

            items_matched_any = True

            # Validar techos de precios para esta asignación
            price_ok = True
            perm_overprices = []
            for i in range(num_targets):
                tid = target_ids[i]
                price_limit = max_prices.get(tid)
                if price_limit:
                    actual_price = vendor_maps[vendor_perm[i]][tid]
                    if actual_price <= 0:
                        price_ok = False
                        unknown_price = {"es": "precio sin confirmar", "en": "price unavailable", "pt": "preço não confirmado"}
                        perm_overprices.append(f"{target_names[tid]}: {unknown_price.get(self.current_lang, unknown_price['es'])}")
                    elif actual_price > price_limit:
                        price_ok = False
                        perm_overprices.append(f"{target_names[tid]}: {actual_price}g > {price_limit}g")

            if price_ok:
                return True, ""
            else:
                rejection_reasons.append(", ".join(perm_overprices))

        if items_matched_any:
            best_reason = rejection_reasons[0] if rejection_reasons else ""
            return False, best_reason

        return False, ""

    def format_microwave_details(self, micros_found, total_map_micros=None):
        """Genera desglose detallado de rarezas de microondas encontrados."""
        if not micros_found:
            total = total_map_micros or 0
            return f"⚪0/{total}" if total > 0 else "⚪0"
        white_count = sum(1 for m in micros_found if m.get("is_white", False))
        rarity_counts = {}
        rarity_names = {0: "Blanco", 1: "Azul", 2: "Morado", 3: "Dorado"}
        for m in micros_found:
            r = m.get("rarity", 0)
            name = rarity_names.get(r, f"R{r}")
            rarity_counts[name] = rarity_counts.get(name, 0) + 1
        
        breakdown_parts = [f"{cnt} {name}" for name, cnt in rarity_counts.items()]
        total_found = len(micros_found)
        total_expected = total_map_micros if total_map_micros and total_map_micros > total_found else total_found
        return f"⚪{white_count}/{total_expected}: {', '.join(breakdown_parts)}"

    def evaluate_template_match(self, stats):
        submode = search_setting(self, 'score_submode')
        current_score = stats.get("score", 0.0)
        current_tier = stats.get("tier", "Normal")
        microwaves = stats.get("microwaves", 0)
        moais = stats.get("moais", 0)
        shady = stats.get("vendors_total", 0)
        boss = stats.get("boss_curses", 0)

        tier_priority = {"Normal": 0, "Light": 1, "Good": 2, "Perfect": 3, "Perfect+": 4}

        if submode == "tier":
            target_tier = search_setting(self, 'target_tier')
            return (tier_priority.get(current_tier, 0) >= tier_priority.get(target_tier, 0))

        elif submode == "template":
            tmpl_id = search_setting(self, 'selected_template')
            tmpl = PRESET_TEMPLATES.get(tmpl_id, {})
            if not tmpl:
                return False

            min_score = tmpl.get("min_score", 0.0)
            if current_score < min_score:
                return False
            if tmpl.get("min_moais", 0) > 0 and moais < tmpl["min_moais"]:
                return False
            if tmpl.get("min_vendors", 0) > 0 and shady < tmpl["min_vendors"]:
                return False
            if tmpl.get("min_microwaves", 0) > 0 and microwaves < tmpl["min_microwaves"]:
                return False
            min_white_micros = tmpl.get("min_white_microwaves", 0)
            if min_white_micros > 0:
                if microwaves < min_white_micros:
                    return False
                white_count = stats.get("microwaves_white")
                if white_count is None:
                    target_to_scan = max(microwaves, min_white_micros)
                    micros_found = self.reader.scan_microwaves(expected_count=target_to_scan)
                    white_count = sum(1 for m in micros_found if m.get("is_white", False))
                    stats["microwaves_white"] = white_count
                    stats["microwaves_detail"] = self.format_microwave_details(micros_found, microwaves)
                if white_count < min_white_micros:
                    return False
            if tmpl.get("min_boss", 0) > 0 and boss < tmpl["min_boss"]:
                return False
            if tmpl.get("min_bald_heads", 0) > 0 and stats.get("bald_heads", 0) < tmpl["min_bald_heads"]:
                return False

            req_tier = tmpl.get("tier")
            if req_tier and tier_priority.get(current_tier, 0) < tier_priority.get(req_tier, 0):
                return False

            return True

        return False

MBHelperApp = MegabonkHelperApp

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--check-build":
        from release_checks import run_build_check
        raise SystemExit(run_build_check(MBHelperApp, sys.argv[2]))
    else:
        app = MBHelperApp()
        app.mainloop()
