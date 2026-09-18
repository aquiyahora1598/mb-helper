"""
MB Helper - Aplicacion Externa Legal para Steam Leaderboards
Autor: Asistente AI & Usuario
100% Legal: Cero inyeccion de DLLs en el directorio del juego.
Lectura pasiva de memoria + Automatizacion con hardware input nativo y vision artificial.
Atajo Global F5 para Iniciar / Detener en cualquier momento sin Alt+Tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import atexit
import itertools
import ctypes
from ctypes import wintypes

try:
    import keyboard
except Exception:
    keyboard = None

from phantom_reader import (
    PhantomMemoryReader,
    OFFICIAL_ITEMS,
    ITEM_NAMES_ES,
    ITEM_NAMES_EN,
    ITEM_NAMES_PT,
    calculate_map_score,
    evaluate_map_tier,
    TIER_INFO,
    PRESET_TEMPLATES
)
from phantom_bot import PhantomBot
from telemetry_logger import TelemetryLogger

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
# PALETA DE COLORES MODERNA (DARK CYBERNETIC)
# ==========================================
COLOR_BG = "#0B0D14"
COLOR_CARD = "#141724"
COLOR_CARD_ALT = "#1C2033"
COLOR_BORDER = "#252B45"
COLOR_BORDER_GLOW = "#38BDF8"
COLOR_GOLD = "#FBBF24"
COLOR_PURPLE = "#A855F7"
COLOR_BLUE = "#60A5FA"
COLOR_GREEN = "#22C55E"
COLOR_RED = "#EF4444"
COLOR_TEXT = "#F1F5F9"
COLOR_TEXT_DIM = "#94A3B8"

# ==========================================
# SISTEMA DE AUDITORIA Y LOGGING
# ==========================================
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "megabonk_helper.log")
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

FONT_TITLE = ("Bahnschrift SemiBold", 14)
FONT_SUBTITLE = ("Bahnschrift SemiBold", 11)
FONT_BODY = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_TAB = ("Bahnschrift SemiBold", 10)
FONT_MONO = ("Consolas", 9)
FONT_COUNTER = ("Bahnschrift SemiBold", 11)

# Catalogo clasificado por rarezas oficiales con nombres en Espanol, Ingles y Portugues
CATALOG_BY_RARITY = {
    "Dorados (Legendarios)": [
        (it[0], it[1], it[2], it[3], it[4]) for it in OFFICIAL_ITEMS if it[5] == "LEGENDARY"
    ],
    "Epicos (Morados)": [
        (it[0], it[1], it[2], it[3], it[4]) for it in OFFICIAL_ITEMS if it[5] == "RARE"
    ],
    "Raros (Azules)": [
        (it[0], it[1], it[2], it[3], it[4]) for it in OFFICIAL_ITEMS if it[5] == "UNCOMMON"
    ],
    "Comunes (Grises)": [
        (it[0], it[1], it[2], it[3], it[4]) for it in OFFICIAL_ITEMS if it[5] == "COMMON"
    ],
}

LIMITS_MAP = {
    "vendors_golden": ("Vendedores Dorados", "Golden Vendors", "Vendedores Dourados", 3, "👑"),
    "boss_curses": ("Maldiciones de Jefe", "Boss Curses", "Maldições de Chefe", 3, "💀"),
    "moais": ("Moais de Piedra", "Stone Moais", "Moais de Pedra", 3, "🗿"),
    "charge_shrines": ("Torres de Carga", "Upgrade Towers", "Torres de Carga", 20, "🏛️"),
    "greed_shrines": ("Santuarios de Codicia", "Greed Shrines", "Santuários de Ganância", 12, "💰"),
    "magnet_shrines": ("Santuarios de Iman", "Magnet Shrines", "Santuários de Ímã", 6, "🧲"),
    "challenges": ("Desafios de Combate", "Combat Challenges", "Desafios de Combate", 6, "⚔️"),
    "microwaves": ("Microondas", "Microwaves", "Micro-ondas", 4, "☢️"),
    "chests": ("Cofres Totales", "Total Chests", "Baús Totais", 60, "📦"),
    "pots": ("Vasijas Totales", "Total Pots", "Vasos Totais", 80, "🏺"),
}

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
        "tab3": "⚙️ MODO 3: ESPECIFICO",
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
        "gold_opt1_desc": "Comun (~25% · Segundos)",
        "gold_opt2": "👑👑 2 Vendedores Dorados",
        "gold_opt2_desc": "Raro (~3% · Muy recomendado)",
        "gold_opt3": "👑👑👑 3 Vendedores Dorados",
        "gold_opt3_desc": "Legendario (~0.1% · Perfect)",
        # Tab 3
        "tab3_title": "FILTRO ESPECIFICO",
        "min_lbl": "Minimo:",
        # Tab 4
        "tab4_title": "PUNTUACION & PLANTILLAS",
        "tier_title": "🎯 1. Rango Objetivo (Tier)",
        "preset_title": "⚡ 2. Cargar Plantilla Rapida",
        "combo_chk": "🔗 Exigir tambien Items del Modo 1",
        "combo_none": "Modo 1: Ninguno seleccionado",
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
        "preset_wr": "🏆 Record Mundial (Perfect+)",
        "preset_good": "⭐ Gran Partida (Perfect)",
        "preset_fast": "⏱️ Busqueda Rapida (Good)",
        "preset_moai": "🗿 Lluvia Moais (5+)",
        "preset_vendor": "💰 Vendedores 5+ (Shady)",
        "preset_micro": "⚡ 2x Microondas",
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
        "tab3": "⚙️ MODE 3: SPECIFIC",
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
        "tab3_title": "SPECIFIC FILTER",
        "min_lbl": "Minimum:",
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
        "preset_wr": "🏆 World Record (Perfect+)",
        "preset_good": "⭐ Great Run (Perfect)",
        "preset_fast": "⏱️ Fast Search (Good)",
        "preset_moai": "🗿 Moai Rain (5+)",
        "preset_vendor": "💰 Vendors 5+ (Shady)",
        "preset_micro": "⚡ 2x Microwaves",
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
        "tab3": "⚙️ MODO 3: ESPECIFICO",
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
        "gold_opt1_desc": "Comum (~25% · Segundos)",
        "gold_opt2": "👑👑 2 Vendedores Dourados",
        "gold_opt2_desc": "Raro (~3% · Muito recomendado)",
        "gold_opt3": "👑👑👑 3 Vendedores Dourados",
        "gold_opt3_desc": "Lendario (~0.1% · Perfeito)",
        # Tab 3
        "tab3_title": "FILTRO ESPECIFICO",
        "min_lbl": "Minimo:",
        # Tab 4
        "tab4_title": "PONTUACAO & PRESETS",
        "tier_title": "🎯 1. Rank Objetivo (Tier)",
        "preset_title": "⚡ 2. Carregar Preset Rapido",
        "combo_chk": "🔗 Exigir tambem Itens do Modo 1",
        "combo_none": "Modo 1: Nenhum selecionado",
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
        "preset_wr": "🏆 Recorde Mundial (Perfect+)",
        "preset_good": "⭐ Otima Partida (Perfect)",
        "preset_fast": "⏱️ Busca Rapida (Good)",
        "preset_moai": "🗿 Chuva de Moais (5+)",
        "preset_vendor": "💰 Vendedores 5+ (Shady)",
        "preset_micro": "⚡ 2x Micro-ondas",
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
    }
}

PRESET_HOVER_DATA = {
    "es": {
        "record_perfect_plus": {
            "title": "🏆 Record Mundial (Perfect+)",
            "tier": "Tier: 🔴 PERFECT+ (Score >= 30.0 pts)",
            "reqs": "• Requisitos: Score >= 30.0 pts + 2 Microondas\n• Probabilidad: ~0.05% (Semilla Elite)\n• Uso: Speedruns y records mundiales."
        },
        "record_perfect": {
            "title": "⭐ Gran Partida (Perfect)",
            "tier": "Tier: 🟡 PERFECT (Score >= 25.0 pts)",
            "reqs": "• Requisitos: Score >= 25.0 pts + 1 Microondas\n• Probabilidad: ~2.5% (~10-20 segundos)\n• Uso: Partidas competitivas de alto nivel."
        },
        "fast_good": {
            "title": "⏱️ Busqueda Rapida (Good)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Score global >= 20.0 pts\n• Probabilidad: ~20% (3 a 5 segundos)\n• Uso: Recomendada para jugar de inmediato."
        },
        "moai_rain": {
            "title": "🗿 Lluvia de Moais (5+)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Minimo 5 Moais + Score >= 20.0 pts\n• Probabilidad: ~4% (~10-15 segundos)\n• Uso: Builds pasivas de stats gratis."
        },
        "vendor_paradise": {
            "title": "💰 Vendedores 5+ (Shady)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Minimo 5 Vendedores + Score >= 20.0 pts\n• Probabilidad: ~3.5% (~15 segundos)\n• Uso: Economia y compra masiva de items."
        },
        "double_microwave": {
            "title": "⚡ 2x Microondas",
            "tier": "Tier: ⚪ LIGHT (Score >= 18.0 pts)",
            "reqs": "• Requisitos: Minimo 2 Microondas + Score >= 18.0 pts\n• Probabilidad: ~5% (~5-10 segundos)\n• Uso: Duplicacion y coccion de items."
        }
    },
    "en": {
        "record_perfect_plus": {
            "title": "🏆 World Record (Perfect+)",
            "tier": "Tier: 🔴 PERFECT+ (Score >= 30.0 pts)",
            "reqs": "• Requirements: Score >= 30.0 pts + 2 Microwaves\n• Probability: ~0.05% (Elite Seed)\n• Usage: Speedruns and leaderboard records."
        },
        "record_perfect": {
            "title": "⭐ Great Run (Perfect)",
            "tier": "Tier: 🟡 PERFECT (Score >= 25.0 pts)",
            "reqs": "• Requirements: Score >= 25.0 pts + 1 Microwave\n• Probability: ~2.5% (~10-20 seconds)\n• Usage: High-tier competitive runs."
        },
        "fast_good": {
            "title": "⏱️ Fast Search (Good)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requirements: Overall score >= 20.0 pts\n• Probability: ~20% (3-5 seconds)\n• Usage: Recommended to play immediately with a top seed."
        },
        "moai_rain": {
            "title": "🗿 Moai Rain (5+)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requirements: Minimum 5 Moais + Score >= 20.0 pts\n• Probability: ~4% (~10-15 seconds)\n• Usage: Passive free-stat builds with Moais."
        },
        "vendor_paradise": {
            "title": "💰 Vendors 5+ (Shady)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requirements: Minimum 5 Vendors + Score >= 20.0 pts\n• Probability: ~3.5% (~15 seconds)\n• Usage: Economy and mass shopping."
        },
        "double_microwave": {
            "title": "⚡ 2x Microwaves",
            "tier": "Tier: ⚪ LIGHT (Score >= 18.0 pts)",
            "reqs": "• Requirements: Minimum 2 Microwaves + Score >= 18.0 pts\n• Probability: ~5% (~5-10 seconds)\n• Usage: Item duplication and crafting."
        }
    },
    "pt": {
        "record_perfect_plus": {
            "title": "🏆 Recorde Mundial (Perfect+)",
            "tier": "Tier: 🔴 PERFECT+ (Score >= 30.0 pts)",
            "reqs": "• Requisitos: Score >= 30.0 pts + 2 Micro-ondas\n• Chance: ~0.05% (Seed Lendaria)\n• Uso: Speedruns e recordes mundiais."
        },
        "record_perfect": {
            "title": "⭐ Otima Partida (Perfect)",
            "tier": "Tier: 🟡 PERFECT (Score >= 25.0 pts)",
            "reqs": "• Requisitos: Score >= 25.0 pts + 1 Micro-ondas\n• Chance: ~2.5% (~10-20 segundos)\n• Uso: Partidas competitivas de alto nivel."
        },
        "fast_good": {
            "title": "⏱️ Busca Rapida (Good)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Score global >= 20.0 pts\n• Chance: ~20% (3 a 5 segundos)\n• Uso: Recomendado para jogar direto com mapa top."
        },
        "moai_rain": {
            "title": "🗿 Chuva de Moais (5+)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Minimo 5 Moais + Score >= 20.0 pts\n• Chance: ~4% (~10-15 segundos)\n• Uso: Builds focadas em atributos gratis de Moais."
        },
        "vendor_paradise": {
            "title": "💰 Vendedores 5+ (Shady)",
            "tier": "Tier: 🟢 GOOD (Score >= 20.0 pts)",
            "reqs": "• Requisitos: Minimo 5 Vendedores + Score >= 20.0 pts\n• Chance: ~3.5% (~15 segundos)\n• Uso: Economia, ouro e compras massivas."
        },
        "double_microwave": {
            "title": "⚡ 2x Micro-ondas",
            "tier": "Tier: ⚪ LIGHT (Score >= 18.0 pts)",
            "reqs": "• Requisitos: Minimo 2 Micro-ondas + Score >= 18.0 pts\n• Chance: ~5% (~5-10 segundos)\n• Uso: Estrategias de duplicacao de itens."
        }
    }
}




class MegabonkHelperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_lang = "es"
        self.title(self.t("title"))
        self.geometry("1080x820")
        self.minsize(760, 480)
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
                        self.item_icons[cname] = tk.PhotoImage(file=os.path.join(icons_dir, fname))
                    except Exception:
                        pass

        # Control de ciclo de vida
        self.is_closing = False
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

        # Filtros Modo 3
        self.ultra_filters = {}
        for key, (label_es, label_en, label_pt, max_val, icon) in LIMITS_MAP.items():
            self.ultra_filters[key] = {
                "active": tk.BooleanVar(value=False),
                "min_val": tk.IntVar(value=1),
                "max_val": max_val,
                "label_es": f"{icon} {label_es}",
                "label_en": f"{icon} {label_en}",
                "label_pt": f"{icon} {label_pt}",
                "icon": icon
            }

        # Construir Interfaz de Usuario
        self.setup_ui()

        # Timestamp para debounce de atajo F5
        self._last_f5_time = 0.0

        # Atajos de teclado locales Tkinter
        self.bind("<F5>", lambda e: self.trigger_f5_action())

        # Desplazamiento global con rueda del raton (MouseWheel) para ventanas reducidas
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", lambda e: self._on_global_mousewheel_linux(-1))
        self.bind_all("<Button-5>", lambda e: self._on_global_mousewheel_linux(1))

        # Hilos secundarios independientes
        self.start_hotkey_listener()
        self.start_background_monitor()
        self.start_bot_worker()

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
        self.title(self.t("title"))
        self.lbl_legal.config(text=self.t("legal_badge"))
        self.lbl_lang_prefix.config(text=self.t("lang_lbl"))

        # Actualizar pestanas
        self.btn_tab1.config(text=self.t("tab1"))
        self.btn_tab2.config(text=self.t("tab2"))
        self.btn_tab3.config(text=self.t("tab3"))
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

        # Tab 3
        self.lbl_tab3_title.config(text=self.t("tab3_title"))
        for key, f in self.ultra_filters.items():
            if self.current_lang == "pt":
                lbl_txt = f["label_pt"]
            elif self.current_lang == "en":
                lbl_txt = f["label_en"]
            else:
                lbl_txt = f["label_es"]
            f["chk_widget"].config(text=lbl_txt)
            f["lbl_min_widget"].config(text=self.t("min_lbl"))

        # Tab 4
        self.lbl_tab4_title.config(text=self.t("tab4_title"))
        self.lbl_tier_sec_title.config(text=self.t("tier_title"))
        self.lbl_preset_sec_title.config(text=self.t("preset_title"))

        # Presets text
        preset_key_map = {
            "record_perfect_plus": "preset_wr",
            "record_perfect": "preset_good",
            "fast_good": "preset_fast",
            "moai_rain": "preset_moai",
            "vendor_paradise": "preset_vendor",
            "double_microwave": "preset_micro",
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

        # Actualizar estado de objetivo de preset o tier
        if self.score_submode.get() == "tier":
            self.on_select_tier()
        else:
            self.apply_preset_template(self.selected_template.get())

    def on_exit(self):
        self.is_closing = True
        self.is_running = False
        if hasattr(self, "telemetry") and self.telemetry:
            try:
                self.telemetry.stop()
            except Exception:
                pass
        self.destroy()

    def setup_ui(self):
        # 1. ENCABEZADO SUPERIOR
        header = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        header.pack(side="top", fill="x", padx=14, pady=(10, 5))

        title_box = tk.Frame(header, bg=COLOR_CARD)
        title_box.pack(side="left", padx=12, pady=6)

        tk.Label(
            title_box,
            text="MB HELPER",
            font=FONT_TITLE,
            bg=COLOR_CARD,
            fg=COLOR_GOLD
        ).pack(side="left")

        self.lbl_legal = tk.Label(
            title_box,
            text=self.t("legal_badge"),
            font=("Bahnschrift", 9, "bold"),
            bg="#143320",
            fg=COLOR_GREEN,
            padx=8,
            pady=2
        )
        self.lbl_legal.pack(side="left", padx=10)

        # Selector de Idioma (Derecha)
        lang_box = tk.Frame(header, bg=COLOR_CARD)
        lang_box.pack(side="right", padx=12, pady=6)

        self.lbl_lang_prefix = tk.Label(
            lang_box,
            text=self.t("lang_lbl"),
            font=FONT_BODY,
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DIM
        )
        self.lbl_lang_prefix.pack(side="left", padx=(0, 4))

        self.lang_combo = ttk.Combobox(
            lang_box,
            values=["Español", "English", "Português (BR)"],
            state="readonly",
            width=14,
            font=("Segoe UI", 9)
        )
        self.lang_combo.set("Español")
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        self.lang_combo.pack(side="left", padx=(0, 10))

        self.status_conn_lbl = tk.Label(
            header,
            text=self.t("looking_game"),
            font=FONT_SUBTITLE,
            bg=COLOR_CARD,
            fg=COLOR_RED
        )
        self.status_conn_lbl.pack(side="right", padx=12, pady=6)

        # 2. SELECTOR DE PESTANAS (NAV TABS)
        nav_frame = tk.Frame(self, bg=COLOR_BG)
        nav_frame.pack(side="top", fill="x", padx=14, pady=3)

        self.btn_tab1 = tk.Button(
            nav_frame, text=self.t("tab1"),
            font=FONT_TAB, bg=COLOR_CARD_ALT, fg=COLOR_BORDER_GLOW,
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_BORDER_GLOW,
            relief="flat", pady=7, cursor="hand2",
            command=lambda: self.switch_mode(1)
        )
        self.btn_tab1.pack(side="left", expand=True, fill="x", padx=(0, 3))

        self.btn_tab2 = tk.Button(
            nav_frame, text=self.t("tab2"),
            font=FONT_TAB, bg=COLOR_CARD, fg=COLOR_TEXT_DIM,
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_GOLD,
            relief="flat", pady=7, cursor="hand2",
            command=lambda: self.switch_mode(2)
        )
        self.btn_tab2.pack(side="left", expand=True, fill="x", padx=3)

        self.btn_tab3 = tk.Button(
            nav_frame, text=self.t("tab3"),
            font=FONT_TAB, bg=COLOR_CARD, fg=COLOR_TEXT_DIM,
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_PURPLE,
            relief="flat", pady=7, cursor="hand2",
            command=lambda: self.switch_mode(3)
        )
        self.btn_tab3.pack(side="left", expand=True, fill="x", padx=3)

        self.btn_tab4 = tk.Button(
            nav_frame, text=self.t("tab4"),
            font=FONT_TAB, bg=COLOR_CARD, fg=COLOR_TEXT_DIM,
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_GOLD,
            relief="flat", pady=7, cursor="hand2",
            command=lambda: self.switch_mode(4)
        )
        self.btn_tab4.pack(side="left", expand=True, fill="x", padx=(3, 0))

        # 3. PANEL INFERIOR DE CONTROL Y ESTADISTICAS (Empaquetado primero en el fondo para garantizar visibilidad 100%)
        bottom_panel = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        bottom_panel.pack(side="bottom", fill="x", padx=14, pady=(5, 10))

        # FILA 1: Acciones principales y Badge AFK
        ctrl_row1 = tk.Frame(bottom_panel, bg=COLOR_CARD)
        ctrl_row1.pack(fill="x", padx=12, pady=(8, 4))

        self.btn_action = tk.Button(
            ctrl_row1,
            text=self.t("btn_start"),
            font=("Bahnschrift SemiBold", 11, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=18,
            pady=7,
            cursor="hand2",
            command=self.toggle_search
        )
        self.btn_action.pack(side="left")

        self.btn_test_reset = tk.Button(
            ctrl_row1,
            text=self.t("btn_test_reset"),
            font=("Bahnschrift", 9),
            bg=COLOR_CARD_ALT,
            fg=COLOR_GOLD,
            activebackground="#2A3048",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.test_quick_reset
        )
        self.btn_test_reset.pack(side="left", padx=8)

        self.btn_logs = tk.Button(
            ctrl_row1,
            text=self.t("btn_logs"),
            font=("Bahnschrift", 9),
            bg=COLOR_CARD_ALT,
            fg="#A7F3D0",
            activebackground="#2A3048",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=10,
            pady=7,
            cursor="hand2",
            command=self.open_log_file
        )
        self.btn_logs.pack(side="left", padx=4)
        self.badge_afk = tk.Label(
            ctrl_row1,
            text=self.t("badge_afk"),
            font=("Bahnschrift", 9),
            bg="#292010",
            fg=COLOR_GOLD,
            padx=12,
            pady=6
        )
        self.badge_afk.pack(side="right")

        # FILA 2: Contador Intentos/Tiempo + Mensaje de Estado
        ctrl_row2 = tk.Frame(bottom_panel, bg=COLOR_CARD)
        ctrl_row2.pack(fill="x", padx=12, pady=(3, 5))

        counter_box = tk.Frame(ctrl_row2, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=10, pady=4)
        counter_box.pack(side="left")

        self.lbl_counter = tk.Label(
            counter_box,
            text=f"{self.t('attempts')}: #0  |  {self.t('time')}: 00:00",
            font=FONT_COUNTER,
            bg=COLOR_CARD_ALT,
            fg=COLOR_GOLD
        )
        self.lbl_counter.pack()

        self.lbl_status = tk.Label(
            ctrl_row2,
            text=self.t("status_stopped_user"),
            font=FONT_BOLD,
            bg=COLOR_CARD,
            fg=COLOR_TEXT
        )
        self.lbl_status.pack(side="left", padx=14)

        # FILA 3: Desglose de memoria en vivo
        ctrl_row3 = tk.Frame(bottom_panel, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=10, pady=4)
        ctrl_row3.pack(fill="x", padx=12, pady=(0, 6))

        self.lbl_live_data = tk.Label(
            ctrl_row3,
            text=f"⭐ {self.t('stat_score')}: 0.0 [{self.t('tier_standard')}] | {self.t('stat_gold')}: 0/3 | {self.t('stat_moais')}: 0 | {self.t('stat_curses')}: 0 | {self.t('stat_micros')}: 0 | {self.t('stat_chests')}: 0 | {self.t('stat_vendors')}: {self.t('status_reading')}",
            font=FONT_MONO,
            bg=COLOR_CARD_ALT,
            fg=COLOR_TEXT_DIM,
            anchor="w"
        )
        self.lbl_live_data.pack(fill="x")

        # 4. CONTENEDOR PRINCIPAL (Ocupa todo el espacio dinamico restante entre pestanas y panel de control)
        self.content_container = tk.Frame(self, bg=COLOR_BG)
        self.content_container.pack(side="top", fill="both", expand=True, padx=14, pady=3)

        self.tab1_frame = self.build_tab1_ui()
        self.tab2_frame = self.build_tab2_ui()
        self.tab3_frame = self.build_tab3_ui()
        self.tab4_frame = self.build_tab4_ui()

        self.tab1_frame.pack(fill="both", expand=True)

    def create_scrollable_tab_frame(self):
        """
        Crea un contenedor con Canvas y Scrollbar vertical integrado para pestanas.
        Permite desplazamiento fluido con la rueda del raton en resoluciones bajas o ventanas reducidas.
        """
        outer_frame = tk.Frame(self.content_container, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        canvas = tk.Canvas(outer_frame, bg=COLOR_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=COLOR_CARD)

        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        win_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(win_id, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return outer_frame, canvas, content_frame

    def _on_global_mousewheel(self, event):
        if not event.delta:
            return
        scroll_units = int(-1 * (event.delta / 120) * 2)
        if scroll_units == 0:
            scroll_units = -1 if event.delta > 0 else 1

        mode = self.selected_mode.get()
        target_canvas = None
        if mode == 1:
            target_canvas = getattr(self, "items_canvas", None)
        elif mode == 2:
            target_canvas = getattr(self, "tab2_canvas", None)
        elif mode == 3:
            target_canvas = getattr(self, "tab3_canvas", None)
        elif mode == 4:
            target_canvas = getattr(self, "tab4_canvas", None)

        if target_canvas:
            try:
                target_canvas.yview_scroll(scroll_units, "units")
            except Exception:
                pass

    def _on_global_mousewheel_linux(self, units):
        mode = self.selected_mode.get()
        canvases = {
            1: getattr(self, "items_canvas", None),
            2: getattr(self, "tab2_canvas", None),
            3: getattr(self, "tab3_canvas", None),
            4: getattr(self, "tab4_canvas", None)
        }
        target = canvases.get(mode)
        if target:
            try:
                target.yview_scroll(units * 2, "units")
            except Exception:
                pass

    # ==========================================================
    # PESTANA 1: MODO ITEMS ESPECIFICOS
    # ==========================================================
    def build_tab1_ui(self):
        frame = tk.Frame(self.content_container, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)

        sel_bar = tk.Frame(frame, bg=COLOR_CARD)
        sel_bar.pack(fill="x", padx=10, pady=(8, 4))

        self.lbl_items_chosen_title = tk.Label(
            sel_bar,
            text=self.t("items_chosen"),
            font=FONT_BOLD,
            bg=COLOR_CARD,
            fg=COLOR_BORDER_GLOW
        )
        self.lbl_items_chosen_title.pack(side="left", padx=(0, 8))

        self.lbl_selected_items = tk.Label(
            sel_bar,
            text=self.t("items_none"),
            font=FONT_BODY,
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DIM
        )
        self.lbl_selected_items.pack(side="left")

        self.btn_clear_items = tk.Button(
            sel_bar,
            text=self.t("btn_clear"),
            font=("Bahnschrift", 9),
            bg=COLOR_CARD_ALT,
            fg=COLOR_RED,
            activebackground=COLOR_CARD,
            activeforeground="#FFFFFF",
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.clear_selected_items
        )
        self.btn_clear_items.pack(side="right")

        search_bar = tk.Frame(frame, bg=COLOR_CARD)
        search_bar.pack(fill="x", padx=10, pady=(2, 6))

        self.lbl_search_title = tk.Label(search_bar, text=self.t("search_item"), font=FONT_BOLD, bg=COLOR_CARD, fg=COLOR_TEXT)
        self.lbl_search_title.pack(side="left", padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_items_grid())
        search_entry = tk.Entry(
            search_bar,
            textvariable=self.search_var,
            font=FONT_BODY,
            bg=COLOR_CARD_ALT,
            fg=COLOR_TEXT,
            insertbackground="white",
            relief="solid",
            bd=1,
            width=30
        )
        search_entry.pack(side="left")

        # Canvas con scroll para los items
        canvas_box = tk.Frame(frame, bg=COLOR_CARD)
        canvas_box.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.items_canvas = tk.Canvas(canvas_box, bg=COLOR_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_box, orient="vertical", command=self.items_canvas.yview)
        self.items_grid_frame = tk.Frame(self.items_canvas, bg=COLOR_CARD)

        self.items_grid_frame.bind(
            "<Configure>",
            lambda e: self.items_canvas.configure(scrollregion=self.items_canvas.bbox("all"))
        )
        self.canvas_window = self.items_canvas.create_window((0, 0), window=self.items_grid_frame, anchor="nw")
        self.items_canvas.bind("<Configure>", lambda e: self.items_canvas.itemconfig(self.canvas_window, width=e.width))

        self.items_canvas.configure(yscrollcommand=scrollbar.set)
        self.items_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh_items_grid()
        return frame

    def refresh_items_grid(self):
        for widget in self.items_grid_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower().strip()

        rarity_keys = [
            ("Dorados (Legendarios)", "rarity_golden", COLOR_GOLD),
            ("Epicos (Morados)", "rarity_epic", COLOR_PURPLE),
            ("Raros (Azules)", "rarity_rare", COLOR_BLUE),
            ("Comunes (Grises)", "rarity_common", COLOR_TEXT_DIM)
        ]

        for cat_raw, i18n_key, cat_color in rarity_keys:
            items = CATALOG_BY_RARITY.get(cat_raw, [])
            filtered = []
            for it in items:
                # it: (id, codename, es_name, en_name, pt_name)
                it_id, codename, es_name, en_name, pt_name = it
                if self.current_lang == "pt":
                    disp_name = pt_name
                elif self.current_lang == "en":
                    disp_name = en_name
                else:
                    disp_name = es_name

                if (query == "" or query in codename.lower() or query in es_name.lower() or
                        query in en_name.lower() or query in pt_name.lower()):
                    filtered.append((it_id, codename, es_name, en_name, pt_name, disp_name))

            if not filtered:
                continue

            sec_title = self.t(i18n_key)
            sec_lbl = tk.Label(
                self.items_grid_frame,
                text=f"── {sec_title} ──",
                font=("Bahnschrift SemiBold", 10),
                bg=COLOR_CARD,
                fg=cat_color,
                anchor="w"
            )
            sec_lbl.pack(fill="x", padx=10, pady=(10, 4))

            # Diseno de filas en 3 columnas uniformes
            curr_row = None
            for idx, (it_id, codename, es_name, en_name, pt_name, disp_name) in enumerate(filtered):
                col = idx % 3
                if col == 0:
                    curr_row = tk.Frame(self.items_grid_frame, bg=COLOR_CARD)
                    curr_row.pack(fill="x", padx=8, pady=2)
                    for c in range(3):
                        curr_row.columnconfigure(c, weight=1, uniform="item_col")

                is_selected = any(s[0] == it_id for s in self.selected_items)
                sel_idx = -1
                for s_i, s in enumerate(self.selected_items):
                    if s[0] == it_id:
                        sel_idx = s_i + 1
                        break

                btn_bg = "#166534" if is_selected else COLOR_CARD_ALT
                btn_fg = "#86EFAC" if is_selected else COLOR_TEXT
                text_lbl = f"✓ #{sel_idx} {disp_name}" if is_selected else f"  {disp_name}"

                icon_img = self.item_icons.get(codename)

                btn = tk.Button(
                    curr_row,
                    text=text_lbl,
                    image=icon_img,
                    compound="left" if icon_img else "none",
                    font=("Segoe UI", 9, "bold" if is_selected else "normal"),
                    bg=btn_bg,
                    fg=btn_fg,
                    activebackground="#22C55E",
                    activeforeground="#FFFFFF",
                    relief="flat",
                    padx=6,
                    pady=4,
                    anchor="w",
                    cursor="hand2",
                    command=lambda tid=it_id, tc=codename, te=es_name, tn=en_name, tp=pt_name: self.toggle_item_selection(tid, tc, te, tn, tp)
                )
                btn.grid(row=0, column=col, padx=4, pady=2, sticky="ew")

    def toggle_item_selection(self, it_id, codename, es_name, en_name, pt_name):
        existing = [idx for idx, s in enumerate(self.selected_items) if s[0] == it_id]
        if existing:
            self.selected_items.pop(existing[0])
        else:
            if len(self.selected_items) >= 3:
                messagebox.showinfo(self.t("alert_item_limit_title"), self.t("alert_item_limit_msg"))
                return
            self.selected_items.append((it_id, codename, es_name, en_name, pt_name))

        self.update_selected_items_label()
        self.refresh_items_grid()
        self.update_tab4_items_label()

    def update_selected_items_label(self):
        if self.selected_items:
            names = []
            for idx, s in enumerate(self.selected_items):
                n = s[4] if self.current_lang == "pt" else (s[3] if self.current_lang == "en" else s[2])
                names.append(f"#{idx+1}: {n}")
            self.lbl_selected_items.config(text=" | ".join(names), fg=COLOR_GREEN)
        else:
            self.lbl_selected_items.config(text=self.t("items_none"), fg=COLOR_TEXT_DIM)

    def clear_selected_items(self):
        self.selected_items.clear()
        self.update_selected_items_label()
        self.refresh_items_grid()
        self.update_tab4_items_label()

    # ==========================================================
    # PESTANA 2: VENDEDORES DORADOS
    # ==========================================================
    def build_tab2_ui(self):
        outer_frame, self.tab2_canvas, frame = self.create_scrollable_tab_frame()

        self.lbl_tab2_title = tk.Label(
            frame,
            text=self.t("tab2_title"),
            font=FONT_TITLE,
            bg=COLOR_CARD,
            fg=COLOR_GOLD
        )
        self.lbl_tab2_title.pack(pady=(16, 12))

        opts_frame = tk.Frame(frame, bg=COLOR_CARD)
        opts_frame.pack(pady=4)

        # Opcion 1
        box1 = tk.Frame(opts_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=20, pady=10)
        box1.pack(fill="x", pady=5)
        self.rb_gold1 = tk.Radiobutton(
            box1, text=self.t("gold_opt1"), variable=self.target_golden_vendors, value=1,
            font=FONT_BOLD, bg=COLOR_CARD_ALT, fg=COLOR_BORDER_GLOW, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_BORDER_GLOW, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_gold1.pack(anchor="w")
        self.lbl_gold1_desc = tk.Label(box1, text=self.t("gold_opt1_desc"), font=FONT_BODY, bg=COLOR_CARD_ALT, fg=COLOR_TEXT_DIM)
        self.lbl_gold1_desc.pack(anchor="w", padx=24)

        # Opcion 2
        box2 = tk.Frame(opts_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=20, pady=10)
        box2.pack(fill="x", pady=5)
        self.rb_gold2 = tk.Radiobutton(
            box2, text=self.t("gold_opt2"), variable=self.target_golden_vendors, value=2,
            font=FONT_BOLD, bg=COLOR_CARD_ALT, fg=COLOR_PURPLE, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_PURPLE, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_gold2.pack(anchor="w")
        self.lbl_gold2_desc = tk.Label(box2, text=self.t("gold_opt2_desc"), font=FONT_BODY, bg=COLOR_CARD_ALT, fg=COLOR_TEXT_DIM)
        self.lbl_gold2_desc.pack(anchor="w", padx=24)

        # Opcion 3
        box3 = tk.Frame(opts_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=20, pady=10)
        box3.pack(fill="x", pady=5)
        self.rb_gold3 = tk.Radiobutton(
            box3, text=self.t("gold_opt3"), variable=self.target_golden_vendors, value=3,
            font=FONT_BOLD, bg=COLOR_CARD_ALT, fg=COLOR_GOLD, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_GOLD, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_gold3.pack(anchor="w")
        self.lbl_gold3_desc = tk.Label(box3, text=self.t("gold_opt3_desc"), font=FONT_BODY, bg=COLOR_CARD_ALT, fg=COLOR_TEXT_DIM)
        self.lbl_gold3_desc.pack(anchor="w", padx=24)

        return outer_frame

    # ==========================================================
    # PESTANA 3: ESPECIFICO INTERACTUABLES
    # ==========================================================
    def build_tab3_ui(self):
        outer_frame, self.tab3_canvas, frame = self.create_scrollable_tab_frame()

        self.lbl_tab3_title = tk.Label(
            frame,
            text=self.t("tab3_title"),
            font=FONT_TITLE,
            bg=COLOR_CARD,
            fg=COLOR_PURPLE
        )
        self.lbl_tab3_title.pack(pady=(16, 12))

        grid_frame = tk.Frame(frame, bg=COLOR_CARD)
        grid_frame.pack(padx=16, pady=4)

        row, col = 0, 0
        for key, filter_info in self.ultra_filters.items():
            cell = tk.Frame(grid_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=12, pady=8)
            cell.grid(row=row, column=col, padx=6, pady=4, sticky="ew")

            chk = tk.Checkbutton(
                cell,
                text=filter_info["label_es"],
                variable=filter_info["active"],
                font=FONT_BOLD,
                bg=COLOR_CARD_ALT,
                fg=COLOR_TEXT,
                selectcolor="#0D0F18",
                activebackground=COLOR_CARD_ALT,
                activeforeground=COLOR_TEXT,
                cursor="hand2"
            )
            chk.pack(anchor="w")
            filter_info["chk_widget"] = chk

            spin_frame = tk.Frame(cell, bg=COLOR_CARD_ALT)
            spin_frame.pack(anchor="w", pady=(2, 0))

            lbl_m = tk.Label(spin_frame, text=self.t("min_lbl"), font=FONT_BODY, bg=COLOR_CARD_ALT, fg=COLOR_TEXT_DIM)
            lbl_m.pack(side="left")
            filter_info["lbl_min_widget"] = lbl_m

            sp = tk.Spinbox(
                spin_frame,
                from_=0,
                to=filter_info["max_val"],
                textvariable=filter_info["min_val"],
                width=4,
                font=FONT_BOLD,
                bg=COLOR_BG,
                fg=COLOR_GOLD,
                buttonbackground=COLOR_CARD
            )
            sp.pack(side="left", padx=4)

            tk.Label(spin_frame, text=f"(Max: {filter_info['max_val']})", font=FONT_BODY, bg=COLOR_CARD_ALT, fg=COLOR_TEXT_DIM).pack(side="left")

            col += 1
            if col >= 2:
                col = 0
                row += 1

        return outer_frame

    # ==========================================================
    # PESTANA 4: PUNTUACION, RANGOS Y PLANTILLAS (SCORES)
    # ==========================================================
    def build_tab4_ui(self):
        outer_frame, self.tab4_canvas, frame = self.create_scrollable_tab_frame()

        self.lbl_tab4_title = tk.Label(
            frame,
            text=self.t("tab4_title"),
            font=FONT_TITLE,
            bg=COLOR_CARD,
            fg=COLOR_GOLD
        )
        self.lbl_tab4_title.pack(pady=(12, 6))

        columns_frame = tk.Frame(frame, bg=COLOR_CARD)
        columns_frame.pack(fill="x", padx=14, pady=2)

        # COLUMNA IZQUIERDA: SELECTOR DE RANGOS
        left_col = tk.Frame(columns_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=12, pady=8)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.lbl_tier_sec_title = tk.Label(
            left_col,
            text=self.t("tier_title"),
            font=FONT_SUBTITLE,
            bg=COLOR_CARD_ALT,
            fg=COLOR_BORDER_GLOW
        )
        self.lbl_tier_sec_title.pack(anchor="w", pady=(0, 4))

        tiers_order = [
            ("Perfect+", "🔴 PERFECT+ (Score ≥ 30)", "#EF4444"),
            ("Perfect", "🟡 PERFECT (Score ≥ 25)", "#FBBF24"),
            ("Good", "🟢 GOOD (Score ≥ 20)", "#22C55E"),
            ("Light", "⚪ LIGHT (Score ≥ 14)", "#E2E8F0")
        ]

        for tier_key, tier_lbl, tier_col in tiers_order:
            box = tk.Frame(left_col, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=8, pady=3)
            box.pack(fill="x", pady=2)

            rb = tk.Radiobutton(
                box,
                text=tier_lbl,
                variable=self.target_tier,
                value=tier_key,
                font=FONT_BOLD,
                bg=COLOR_CARD,
                fg=tier_col,
                selectcolor="#0D0F18",
                activebackground=COLOR_CARD,
                activeforeground=tier_col,
                cursor="hand2",
                command=self.on_select_tier
            )
            rb.pack(anchor="w")

        # COLUMNA DERECHA: PLANTILLAS RAPIDAS (PRESETS)
        right_col = tk.Frame(columns_frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=12, pady=8)
        right_col.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.lbl_preset_sec_title = tk.Label(
            right_col,
            text=self.t("preset_title"),
            font=FONT_SUBTITLE,
            bg=COLOR_CARD_ALT,
            fg=COLOR_PURPLE
        )
        self.lbl_preset_sec_title.pack(anchor="w", pady=(0, 4))

        presets_list = [
            ("record_perfect_plus", "🏆 Record Mundial (Perfect+)", "#EF4444"),
            ("record_perfect", "⭐ Gran Partida (Perfect)", "#FBBF24"),
            ("fast_good", "⏱️ Busqueda Rapida (Good)", "#22C55E"),
            ("moai_rain", "🗿 Lluvia Moais (5+)", "#38BDF8"),
            ("vendor_paradise", "💰 Vendedores 5+ (Shady)", "#F59E0B"),
            ("double_microwave", "⚡ 2x Microondas (Hornos)", "#A855F7")
        ]

        preset_grid = tk.Frame(right_col, bg=COLOR_CARD_ALT)
        preset_grid.pack(fill="both", expand=True)

        self.preset_buttons = {}
        for p_idx, (p_id, p_name, p_color) in enumerate(presets_list):
            p_row = p_idx // 2
            p_col = p_idx % 2
            btn_preset = tk.Button(
                preset_grid,
                text=p_name,
                font=("Bahnschrift", 9),
                bg=COLOR_CARD,
                fg=p_color,
                activebackground="#252B45",
                activeforeground="#FFFFFF",
                relief="flat",
                padx=6,
                pady=6,
                wraplength=170,
                cursor="hand2",
                command=lambda pid=p_id: self.apply_preset_template(pid)
            )
            btn_preset.grid(row=p_row, column=p_col, padx=4, pady=3, sticky="ew")
            btn_preset.bind("<Enter>", lambda e, pid=p_id: self.on_preset_hover(pid))
            btn_preset.bind("<Leave>", lambda e: self.on_preset_leave())
            preset_grid.columnconfigure(p_col, weight=1)
            self.preset_buttons[p_id] = btn_preset

        self.lbl_preset_active = tk.Label(
            right_col,
            text="Objetivo actual: 🟢 GOOD (Score ≥ 20)",
            font=FONT_BODY,
            bg=COLOR_CARD_ALT,
            fg=COLOR_GREEN,
            anchor="w"
        )
        self.lbl_preset_active.pack(fill="x", pady=(8, 0))

        # Cuadro de Informacion / Hover de Plantilla
        self.preset_hover_card = tk.Frame(right_col, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=8, pady=5)
        self.preset_hover_card.pack(fill="x", pady=(6, 0))

        self.lbl_preset_hover_title = tk.Label(
            self.preset_hover_card,
            text=self.t("preset_hover_hint"),
            font=FONT_BOLD,
            bg=COLOR_CARD,
            fg=COLOR_BORDER_GLOW,
            anchor="w"
        )
        self.lbl_preset_hover_title.pack(fill="x")

        self.lbl_preset_hover_desc = tk.Label(
            self.preset_hover_card,
            text=self.t("preset_hover_default"),
            font=FONT_BODY,
            bg=COLOR_CARD,
            fg=COLOR_TEXT_DIM,
            anchor="w",
            justify="left",
            wraplength=380
        )
        self.lbl_preset_hover_desc.pack(fill="x", pady=(2, 0))

        # CARD INTERMEDIO: COMBINACION CON MODO 1 Y MODO 2 (VENDEDORES DORADOS)
        combo_card = tk.Frame(frame, bg=COLOR_CARD_ALT, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=12, pady=6)
        combo_card.pack(fill="x", padx=14, pady=(4, 4))

        # 1. Filtro de Items Modo 1
        self.chk_combo = tk.Checkbutton(
            combo_card,
            text=self.t("combo_chk"),
            variable=self.require_mode1_items,
            font=FONT_BOLD,
            bg=COLOR_CARD_ALT,
            fg=COLOR_GOLD,
            selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT,
            activeforeground=COLOR_GOLD,
            cursor="hand2",
            command=self.update_tab4_items_label
        )
        self.chk_combo.pack(anchor="w")

        self.lbl_tab4_items_preview = tk.Label(
            combo_card,
            text=self.t("combo_none"),
            font=FONT_BODY,
            bg=COLOR_CARD_ALT,
            fg=COLOR_TEXT_DIM,
            anchor="w"
        )
        self.lbl_tab4_items_preview.pack(fill="x", pady=(1, 4))

        # Separador visual
        tk.Frame(combo_card, bg=COLOR_BORDER, height=1).pack(fill="x", pady=(2, 4))

        # 2. Filtro de Vendedores Dorados Modo 2
        golden_row = tk.Frame(combo_card, bg=COLOR_CARD_ALT)
        golden_row.pack(fill="x", anchor="w")

        self.chk_combo_golden = tk.Checkbutton(
            golden_row,
            text=self.t("combo_golden_chk"),
            variable=self.require_golden_vendors,
            font=FONT_BOLD,
            bg=COLOR_CARD_ALT,
            fg=COLOR_GOLD,
            selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT,
            activeforeground=COLOR_GOLD,
            cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.chk_combo_golden.pack(side="left", anchor="w")

        self.gold_btns_frame = tk.Frame(golden_row, bg=COLOR_CARD_ALT)
        self.gold_btns_frame.pack(side="left", padx=(10, 0))

        self.rb_tab4_g1 = tk.Radiobutton(
            self.gold_btns_frame, text="1 👑", variable=self.target_golden_vendors, value=1,
            font=("Bahnschrift", 9), bg=COLOR_CARD_ALT, fg=COLOR_BORDER_GLOW, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_BORDER_GLOW, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_tab4_g1.pack(side="left", padx=2)

        self.rb_tab4_g2 = tk.Radiobutton(
            self.gold_btns_frame, text="2 👑👑", variable=self.target_golden_vendors, value=2,
            font=("Bahnschrift", 9), bg=COLOR_CARD_ALT, fg=COLOR_PURPLE, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_PURPLE, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_tab4_g2.pack(side="left", padx=2)

        self.rb_tab4_g3 = tk.Radiobutton(
            self.gold_btns_frame, text="3 👑👑👑", variable=self.target_golden_vendors, value=3,
            font=("Bahnschrift", 9), bg=COLOR_CARD_ALT, fg=COLOR_GOLD, selectcolor="#0D0F18",
            activebackground=COLOR_CARD_ALT, activeforeground=COLOR_GOLD, cursor="hand2",
            command=self.update_tab4_golden_label
        )
        self.rb_tab4_g3.pack(side="left", padx=2)

        self.lbl_tab4_golden_preview = tk.Label(
            combo_card,
            text="",
            font=FONT_BODY,
            bg=COLOR_CARD_ALT,
            fg=COLOR_TEXT_DIM,
            anchor="w"
        )
        self.lbl_tab4_golden_preview.pack(fill="x", pady=(1, 0))
        self.update_tab4_golden_label()

        # CARD INFERIOR: LIVE SCORE METER
        score_card = tk.Frame(frame, bg="#0D111E", highlightbackground=COLOR_BORDER_GLOW, highlightthickness=1, padx=12, pady=6)
        score_card.pack(fill="x", padx=14, pady=(4, 8))

        sc_top = tk.Frame(score_card, bg="#0D111E")
        sc_top.pack(fill="x")

        self.lbl_score_meter_title = tk.Label(
            sc_top,
            text=self.t("score_meter_title"),
            font=FONT_BOLD,
            bg="#0D111E",
            fg=COLOR_BORDER_GLOW
        )
        self.lbl_score_meter_title.pack(side="left")

        self.lbl_live_score_val = tk.Label(
            sc_top,
            text=self.t("score_waiting"),
            font=FONT_TITLE,
            bg="#0D111E",
            fg=COLOR_GOLD
        )
        self.lbl_live_score_val.pack(side="right")

        return outer_frame

    def update_tab4_items_label(self):
        if not hasattr(self, "lbl_tab4_items_preview"):
            return
        if self.selected_items:
            if self.current_lang == "pt":
                names = [s[4] if len(s) > 4 else s[2] for s in self.selected_items]
            elif self.current_lang == "en":
                names = [s[3] for s in self.selected_items]
            else:
                names = [s[2] for s in self.selected_items]
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
        lang = self.current_lang if self.current_lang in ("en", "pt") else "es"
        data = PRESET_HOVER_DATA.get(lang, {}).get(preset_id)
        if data and hasattr(self, "lbl_preset_hover_title"):
            self.lbl_preset_hover_title.config(text=f"{data['title']}  |  {data['tier']}", fg=COLOR_GOLD)
            self.lbl_preset_hover_desc.config(text=data['reqs'], fg=COLOR_TEXT)

    def on_preset_leave(self):
        self.restore_preset_info()

    def restore_preset_info(self):
        if not hasattr(self, "lbl_preset_hover_title"):
            return
        curr_pid = self.selected_template.get()
        lang = self.current_lang if self.current_lang in ("en", "pt") else "es"
        data = PRESET_HOVER_DATA.get(lang, {}).get(curr_pid)
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

    def apply_preset_template(self, preset_id):
        tmpl = PRESET_TEMPLATES.get(preset_id)
        if not tmpl:
            return
        self.score_submode.set("template")
        self.selected_template.set(preset_id)
        self.target_tier.set(tmpl["tier"])
        name = tmpl["name"]
        tier = tmpl["tier"]
        min_score = tmpl["min_score"]
        self.lbl_preset_active.config(
            text=self.t("target_preset_active", name=name, tier=tier, min_score=min_score),
            fg=COLOR_GOLD
        )
        self.restore_preset_info()

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
        self.selected_mode.set(mode)
        self.tab1_frame.pack_forget()
        self.tab2_frame.pack_forget()
        self.tab3_frame.pack_forget()
        self.tab4_frame.pack_forget()

        self.btn_tab1.config(bg=COLOR_CARD, fg=COLOR_TEXT_DIM)
        self.btn_tab2.config(bg=COLOR_CARD, fg=COLOR_TEXT_DIM)
        self.btn_tab3.config(bg=COLOR_CARD, fg=COLOR_TEXT_DIM)
        self.btn_tab4.config(bg=COLOR_CARD, fg=COLOR_TEXT_DIM)

        if mode == 1:
            self.tab1_frame.pack(fill="both", expand=True)
            self.btn_tab1.config(bg=COLOR_CARD_ALT, fg=COLOR_BORDER_GLOW)
        elif mode == 2:
            self.tab2_frame.pack(fill="both", expand=True)
            self.btn_tab2.config(bg=COLOR_CARD_ALT, fg=COLOR_GOLD)
            if hasattr(self, "tab2_canvas"):
                self.tab2_canvas.yview_moveto(0)
        elif mode == 3:
            self.tab3_frame.pack(fill="both", expand=True)
            self.btn_tab3.config(bg=COLOR_CARD_ALT, fg=COLOR_PURPLE)
            if hasattr(self, "tab3_canvas"):
                self.tab3_canvas.yview_moveto(0)
        elif mode == 4:
            self.tab4_frame.pack(fill="both", expand=True)
            self.btn_tab4.config(bg=COLOR_CARD_ALT, fg=COLOR_GOLD)
            self.update_tab4_items_label()
            self.update_tab4_golden_label()
            self.restore_preset_info()
            if hasattr(self, "tab4_canvas"):
                self.tab4_canvas.yview_moveto(0)

    def test_quick_reset(self):
        connected = self.reader.find_process()
        if not connected:
            messagebox.showwarning(self.t("alert_game_not_found_title"), self.t("alert_game_not_found_msg"))
            return

        ok = self.bot.trigger_restart(pid=self.reader.pid)
        if ok:
            self.lbl_status.config(text=self.t("status_quick_reset_sent"), fg=COLOR_GREEN)
        else:
            messagebox.showerror(self.t("alert_reset_error_title"), self.t("alert_reset_error_msg"))

    def open_log_file(self):
        try:
            if not os.path.exists(LOG_FILE_PATH):
                log_event("Archivo de log inicializado por el usuario.", level="INFO")
            os.startfile(LOG_FILE_PATH)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo de log: {e}")

    # ==========================================================
    # ATAJO GLOBAL DE TECLADO (F5)
    # ==========================================================
    def trigger_f5_action(self):
        now = time.time()
        if now - self._last_f5_time < 0.35:
            return
        self._last_f5_time = now
        self.after(0, self.toggle_search)

    def start_hotkey_listener(self):
        if keyboard is not None:
            try:
                keyboard.add_hotkey("f5", self.trigger_f5_action, suppress=False)
            except Exception:
                pass

        t = threading.Thread(target=self.hotkey_listener_loop, daemon=True)
        t.start()

    def hotkey_listener_loop(self):
        """
        Sondea el estado fisico de la tecla F5 en todo Windows (GetAsyncKeyState & 0x8000).
        Responde en menos de 20ms sin importar el foco, incluso en pantalla completa DirectX.
        """
        f5_was_down = False
        while not self.is_closing:
            try:
                # 0x74 = VK_F5 (Iniciar/Detener Busqueda)
                f5_is_down = bool(user32.GetAsyncKeyState(0x74) & 0x8000)
                if f5_is_down and not f5_was_down:
                    self.trigger_f5_action()
                f5_was_down = f5_is_down
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
        try:
            self.after(0, lambda: func(*args, **kwargs))
        except Exception:
            pass

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
            try:
                kernel32.Beep(600, 150)
            except Exception:
                pass
        else:
            if self.start_search():
                try:
                    kernel32.Beep(1200, 150)
                except Exception:
                    pass

    def start_search(self):
        mode = self.selected_mode.get()
        if mode == 1 and not self.selected_items:
            try:
                kernel32.Beep(400, 180)
                kernel32.Beep(400, 180)
            except Exception:
                pass
            msg = "Debes seleccionar al menos 1 item en el Modo 1 antes de iniciar la busqueda." if self.current_lang == "es" else "You must select at least 1 item in Mode 1 before starting search."
            self.lbl_status.config(text=f"⚠️ {msg}", fg="#EF4444")
            self.lift()
            return False

        if mode == 4 and self.require_mode1_items.get() and not self.selected_items:
            try:
                kernel32.Beep(400, 180)
                kernel32.Beep(400, 180)
            except Exception:
                pass
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

        self.is_running = True
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
            if not self.reader._cached_heap_regions:
                self.reader.refresh_cached_heap_regions()
            self.reader._cached_vendor_regions = []
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

        # Feedback sonoro al iniciar búsqueda F5
        try:
            threading.Thread(target=lambda: (kernel32.Beep(800, 80), kernel32.Beep(1100, 100)), daemon=True).start()
        except Exception:
            pass

        log_event(f"Iniciando búsqueda automática en Modo {mode}. Tecla F5 activa.", level="START")
        if mode == 4:
            log_event(f"Modo 4 configurado: Submodo={self.score_submode.get()}, Tier={self.target_tier.get()}, Plantilla={self.selected_template.get()}, Exigir items Modo 1={self.require_mode1_items.get()}, Exigir dorados={self.require_golden_vendors.get()} ({self.target_golden_vendors.get()} dorados)", level="CONFIG")
        elif mode == 1:
            item_names = [s[2] for s in self.selected_items]
            log_event(f"Modo 1 configurado: Items requeridos: {', '.join(item_names)}", level="CONFIG")
        elif mode == 2:
            log_event(f"Modo 2 configurado: Vendedores dorados requeridos: {self.target_golden_vendors.get()}", level="CONFIG")
        return True

    def stop_search(self, msg=""):
        self.is_running = False
        if self.reader:
            self.reader.set_high_priority(False)
        self.last_reroll_time = None
        self.current_map_detected_time = None
        self._logged_item_timing = False
        self.waiting_for_scene_reload = False
        self.saw_zero_interactables = False
        self.btn_action.config(
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
            self.lbl_status.config(text=msg, fg=COLOR_TEXT)
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
            self.after(0, lambda: messagebox.showwarning(
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
        self.current_map_detected_time = None
        if self.reader:
            self.reader._cached_vendor_regions = []
        self.bot.trigger_restart(pid=self.reader.pid)

    def handle_target_found(self, stats, vendors=None):
        self.match_found = True
        self.stop_search()

        log_event(f"🎉 ¡PARTIDA OBJETIVO CONFIRMADA EN EL INTENTO #{self.attempt_count}!", level="SUCCESS")
        if vendors:
            v_desc = []
            for idx, v in enumerate(vendors):
                r_name = v.get("rarity_name", "")
                items_str = ", ".join(v.get("item_names", []))
                v_desc.append(f"V#{idx+1}({r_name}): [{items_str}]")
            if v_desc:
                log_event(f"Detalle Vendedores: {' | '.join(v_desc)}", level="SUCCESS")

        # 1. PAUSA DE SEGURIDAD AFK INMEDIATA (lo primero en ejecutarse para proteger al jugador)
        try:
            self.bot.trigger_afk_safety_pause(pid=self.reader.pid)
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

        mode = self.selected_mode.get()
        # Verificación ultrarrápida del estado de la partida (< 1ms). CERO escaneo de heap durante carga/reset.
        data = self.reader.get_full_map_data(scan_landmarks=False, scan_vendors=False)
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
                # 5) Se observó la fase de generación/vaciado (generation_seen o saw_zero_interactables)
                # 6) La semilla cambió respecto a la partida anterior
                if time_since_reroll < 1.10:
                    return

                if not (self.generation_seen or self.saw_zero_interactables):
                    # Todavía estamos viendo los interactuables de la partida vieja antes de que empiece a recargar!
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

                    self.waiting_for_scene_reload = False
                    self.saw_zero_interactables = False
                    self.generation_seen = False
                    self.last_reroll_time = None
                    self.current_map_detected_time = now
                    if current_seed is not None:
                        self.last_seed = current_seed
                else:
                    return
        elif is_gen or is_reset or is_loading or not has_loaded_map or total_interactables < 6:
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

            summary_text = (
                f"⭐ {self.t('stat_score')}: {score_val:.1f} [{tier_val}] | "
                f"Moáis: {stats.get('moais', 0)} | "
                f"Maldiciones: {stats.get('boss_curses', 0)} | "
                f"Micros: {stats.get('microwaves', 0)} | "
                f"Cofres: {stats.get('chests', 0)}"
            )
            self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

            # PASO 1: Verificar si cumple la plantilla/tier (< 1ms)
            template_matches = self.evaluate_template_match(stats)

            if not template_matches:
                # No cumple -> REINICIO INMEDIATO (< 0.35s)! Cero tiempo perdido en vendedores.
                log_event(
                    f"Intento #{self.attempt_count}: Score={score_val:.1f} ({tier_val}) | Moáis={stats.get('moais',0)} Mald={stats.get('boss_curses',0)} Micros={stats.get('microwaves',0)} -> No cumple. Reiniciando...",
                    level="REROLL"
                )
                self.trigger_reroll_step()
                return

            # PASO 2: CUMPLIO LA PLANTILLA -> VERIFICAR SI TAMBIEN SE EXIGIERON OBJETOS
            log_event(
                f"⭐ ¡PLANTILLA COINCIDE! Intento #{self.attempt_count}: Tier={tier_val}, Score={score_val:.1f}",
                level="MATCH"
            )

            needs_vendors = (self.require_mode1_items.get() and self.selected_items) or self.require_golden_vendors.get()
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
                if self.require_golden_vendors.get():
                    target_gold = self.target_golden_vendors.get()
                    if num_map_vendors < target_gold:
                        log_event(f"-> La plantilla era {tier_val} pero faltan Vendedores Dorados (hay {num_map_vendors}/{target_gold}). Reiniciando...", level="REROLL")
                        self.safe_ui_update(
                            self.lbl_status.config,
                            text=f"Plantilla {tier_val} ok, pero faltan Dorados ({num_map_vendors}/{target_gold}). Reiniciando...",
                            fg=COLOR_GOLD
                        )
                        self.trigger_reroll_step()
                        return

                needs_items = self.require_mode1_items.get() and self.selected_items
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
                    items_str = ", ".join(v.get("item_names", []))
                    v_desc.append(f"V#{idx+1}({r_name}): [{items_str}]")
                log_event(f"Vendedores encontrados ({len(vendors)}): {' | '.join(v_desc)}", level="EVAL")

                # 1. Comprobar Vendedores Dorados si está marcado
                if self.require_golden_vendors.get():
                    target_gold = self.target_golden_vendors.get()
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
                    has_items = self.check_vendors_have_items(vendors, self.selected_items)
                    if not has_items:
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
            if num_map_vendors < len(self.selected_items):
                log_event(f"Intento #{self.attempt_count}: Mapa solo tiene {num_map_vendors} vendedores (pedidos {len(self.selected_items)}). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            time_since_map = (now - self.current_map_detected_time) if self.current_map_detected_time else 0.0

            # 1. Grace period reactivo (0.05s): escaneo temprano ultra-ligero (< 0.1ms en C)
            if time_since_map < 0.05:
                return

            # 2. Escaneo reactivo: esperar pasivamente a que Unity popule los items
            expected_v = min(num_map_vendors, 3)
            force_rescan = (time_since_map > 0.35)
            vendors = self.reader.scan_shady_vendors(expected_count=expected_v, force_rescan=force_rescan)
            vendors_with_items = sum(1 for v in vendors if v.get("item_ids"))

            # Éxito temprano: si los vendedores que ya cargaron ya tienen los objetos requeridos, terminar de inmediato!
            if vendors and self.check_vendors_have_items(vendors, self.selected_items):
                if not self._logged_item_timing:
                    self._logged_item_timing = True
                    log_event(f"⏱️ Objetos de vendedores cargados en {int(time_since_map * 1000)}ms (Intento #{self.attempt_count}).", level="INFO")
                log_event(f"⭐ ¡OBJETOS ENCONTRADOS! Intento #{self.attempt_count}", level="SUCCESS")
                self.handle_target_found(stats, vendors)
                return

            # Si los vendedores aún no tienen sus items (Unity ejecutando FindItems()):
            # Esperamos pasivamente cada tick (20ms) hasta un máximo de 0.35s
            if vendors_with_items < expected_v:
                if time_since_map < 0.35:
                    wait_ms = int(time_since_map * 1000)
                    self.safe_ui_update(
                        self.lbl_status.config,
                        text=f"⏳ Esperando objetos de vendedores... ({wait_ms}ms) [F5 para parar]",
                        fg=COLOR_GOLD
                    )
                    return
                # Si tras 350ms aún falta algún vendedor pero los cargados ya tienen el objeto, éxito inmediato!
                if vendors and self.check_vendors_have_items(vendors, self.selected_items):
                    log_event(f"⭐ ¡OBJETOS ENCONTRADOS! Intento #{self.attempt_count}", level="SUCCESS")
                    self.handle_target_found(stats, vendors)
                    return
                # Timeout de seguridad: si tras 350ms nunca cargaron items suficientes, reiniciar
                log_event(f"Intento #{self.attempt_count}: Timeout (350ms) esperando items de vendedores ({vendors_with_items}/{expected_v} listos). Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            # ¡LOS ITEMS YA APARECIERON EN MEMORIA!
            if not self._logged_item_timing:
                self._logged_item_timing = True
                log_event(f"⏱️ Objetos de vendedores cargados en {int(time_since_map * 1000)}ms (Intento #{self.attempt_count}).", level="INFO")

            v_desc = []
            for idx, v in enumerate(vendors):
                r_name = v.get("rarity_name", "")
                items_str = ", ".join(v.get("item_names", []))
                v_desc.append(f"V#{idx+1}({r_name}): [{items_str}]")
            summary_text = f"Vendedores: {' | '.join(v_desc) if v_desc else self.t('status_reading')}"
            self.safe_ui_update(self.lbl_live_data.config, text=summary_text)

            has_items = self.check_vendors_have_items(vendors, self.selected_items)
            if not has_items:
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
            target_gold = self.target_golden_vendors.get()
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

        # =========================================================================
        # CASO D: MODO 3 (Filtros Ultra)
        # =========================================================================
        elif mode == 3:
            data = self.reader.get_full_map_data(scan_landmarks=False, scan_vendors=False)
            stats = data.get("stats", {})
            self.safe_ui_update(self.update_live_score_ui, stats)

            match = self.evaluate_simple_match(mode, stats)
            if not match:
                log_event(f"Intento #{self.attempt_count}: No cumple filtros de Modo 3. Reiniciando...", level="REROLL")
                self.trigger_reroll_step()
                return

            log_event(f"⭐ ¡OBJETIVO ALCANZADO en Modo 3! Intento #{self.attempt_count}", level="SUCCESS")
            self.handle_target_found(stats, [])
            return

    def check_vendors_have_items(self, vendors, selected_items):
        """
        Verifica si todos los objetos seleccionados pueden ser comprados en la partida,
        garantizando que cada objeto provenga de un vendedor Shady Guy DIFERENTE
        (ya que cada vendedor solo permite comprar un único objeto por partida).
        Soporta 1, 2 o 3 objetos seleccionados.
        """
        if not selected_items or not vendors:
            return False

        target_ids = [s[0] for s in selected_items]
        num_targets = len(target_ids)

        # Si hay menos vendedores que objetos pedidos, es físicamente imposible comprar todos
        if len(vendors) < num_targets:
            return False

        # Sets de items disponibles en cada vendedor
        vendor_item_sets = [set(v.get("item_ids", [])) for v in vendors]

        # Comprobar si existe una asignación inyectiva: un vendedor distinto para cada item pedido
        for vendor_perm in itertools.permutations(range(len(vendors)), num_targets):
            if all(target_ids[i] in vendor_item_sets[vendor_perm[i]] for i in range(num_targets)):
                return True

        return False

    def evaluate_template_match(self, stats):
        submode = self.score_submode.get()
        current_score = stats.get("score", 0.0)
        current_tier = stats.get("tier", "Normal")
        microwaves = stats.get("microwaves", 0)
        moais = stats.get("moais", 0)
        shady = stats.get("vendors_total", 0)
        boss = stats.get("boss_curses", 0)

        tier_priority = {"Normal": 0, "Light": 1, "Good": 2, "Perfect": 3, "Perfect+": 4}

        if submode == "tier":
            target_tier = self.target_tier.get()
            return (tier_priority.get(current_tier, 0) >= tier_priority.get(target_tier, 0))

        elif submode == "template":
            tmpl_id = self.selected_template.get()
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
            if tmpl.get("min_boss", 0) > 0 and boss < tmpl["min_boss"]:
                return False

            req_tier = tmpl.get("tier")
            if req_tier and tier_priority.get(current_tier, 0) < tier_priority.get(req_tier, 0):
                return False

            return True

        return False

    def evaluate_simple_match(self, mode, stats):
        if mode == 2:
            target_count = self.target_golden_vendors.get()
            current_golden = stats.get("vendors_golden", 0)
            return (current_golden >= target_count)
        elif mode == 3:
            for key, f in self.ultra_filters.items():
                if f["active"].get():
                    min_req = f["min_val"].get()
                    curr = stats.get(key, 0)
                    if curr < min_req:
                        return False
            return True
        return False

MBHelperApp = MegabonkHelperApp

if __name__ == "__main__":
    app = MBHelperApp()
    app.mainloop()
