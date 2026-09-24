"""
Megabonk Helper - Controlador de Reinicios y Teclado Win32 (SendInput)
Zero Inyeccion / Zero DLLs en el directorio del juego.
Sistema de Reinicio Rapido Nativo de Megabonk (Metodo BonkScanner - Hold 'R').
"""

import ctypes
from ctypes import wintypes
import time
import os
import json

try:
    import keyboard
except ImportError:
    keyboard = None

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_ESCAPE = 0x1B
VK_R = 0x52

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT),
        ('hi', HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', INPUT_UNION)
    ]

class PhantomBot:
    def __init__(self):
        self.hwnd = None
        self._cached_reset_settings = None
        self._last_config_check_time = 0.0
        self._last_config_mtime = 0.0

    def find_game_window(self, pid=None):
        hwnd = user32.FindWindowW(None, "Megabonk")
        if not hwnd:
            hwnd = user32.FindWindowW("UnityWndClass", "Megabonk")
        if not hwnd and pid:
            holder = [0]
            def enum_proc_pid(h, lParam):
                w_pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(h, ctypes.byref(w_pid))
                if w_pid.value == pid and user32.IsWindowVisible(h):
                    holder[0] = h
                    return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_proc_pid), 0)
            hwnd = holder[0]

        if not hwnd:
            holder = [0]
            def enum_proc_title(h, lParam):
                length = user32.GetWindowTextLengthW(h)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buf, length + 1)
                    title = buf.value.lower()
                    if "megabonk" in title and "helper" not in title and user32.IsWindowVisible(h):
                        holder[0] = h
                        return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_proc_title), 0)
            hwnd = holder[0]

        self.hwnd = hwnd if hwnd else None
        return self.hwnd is not None

    def is_game_window_active(self, pid=None):
        """Comprueba de forma pasiva si Megabonk esta en primer plano."""
        fg_hwnd = user32.GetForegroundWindow()
        if not fg_hwnd:
            return False
        if pid:
            fg_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(fg_pid))
            if fg_pid.value == pid:
                return True
        if self.hwnd and fg_hwnd == self.hwnd:
            return True
        length = user32.GetWindowTextLengthW(fg_hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg_hwnd, buf, length + 1)
            title = buf.value.lower()
            if "megabonk" in title and "helper" not in title:
                return True
        return False

    def focus_game(self, pid=None):
        """
        Trae la ventana del juego al frente solo si no esta activa,
        usando SW_SHOW (5) de forma limpia sin romper DirectX ni pantalla completa.
        """
        if self.is_game_window_active(pid=pid):
            return True

        if not self.find_game_window(pid=pid):
            return False

        try:
            user32.ShowWindow(self.hwnd, 5)  # SW_SHOW (5)
            user32.SetForegroundWindow(self.hwnd)
            user32.BringWindowToTop(self.hwnd)
        except Exception:
            pass

        time.sleep(0.05)
        return True

    def read_game_reset_settings(self):
        """
        Lee la configuracion nativa de Megabonk (Saves/LocalDir/config.json)
        para saber el tiempo exacto de quick_reset_time que exige el juego.
        Utiliza cache en memoria con verificacion de mtime para eliminar I/O a disco en cada reinicio.
        """
        now = time.time()
        if self._cached_reset_settings is not None and (now - self._last_config_check_time < 10.0):
            return self._cached_reset_settings

        self._last_config_check_time = now
        user_profile = os.environ.get('USERPROFILE', '')
        config_path = os.path.join(
            user_profile,
            "AppData", "LocalLow", "Ved", "Megabonk", "Saves", "LocalDir", "config.json"
        )
        if os.path.exists(config_path):
            try:
                mtime = os.path.getmtime(config_path)
                if self._cached_reset_settings is not None and mtime == self._last_config_mtime:
                    return self._cached_reset_settings
                self._last_config_mtime = mtime

                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                settings = data.get("cfGameSettings", {})
                quick_reset = settings.get("quick_reset", 1)
                quick_reset_time = float(settings.get("quick_reset_time", 0.1))
                # Duracion segura y optimizada: 280ms (70ms mas rapido que los 350ms originales y con margen para que Unity jamas ignore 'R')
                hold_dur = max(0.28, quick_reset_time + 0.15)
                self._cached_reset_settings = {
                    "enabled": bool(quick_reset),
                    "hold_duration": hold_dur
                }
                return self._cached_reset_settings
            except Exception:
                pass
        if self._cached_reset_settings is None:
            self._cached_reset_settings = {"enabled": True, "hold_duration": 0.28}
        return self._cached_reset_settings

    def trigger_quick_reset(self, pid=None):
        """
        SISTEMA DE REINICIO BONKSCANNER EXACTO (METODO NATIVO DE MEGABONK):
        Mantiene presionada la tecla 'R' de forma limpia exactamente como BonkScanner.
        Sin llamadas invasivas a ShowWindow() que rompen el foco exclusivo de DirectX.
        """
        settings = self.read_game_reset_settings()
        hold_time = settings.get("hold_duration", 0.35)

        if keyboard is not None:
            try:
                keyboard.press('r')
                time.sleep(hold_time)
                keyboard.release('r')
                return True
            except Exception:
                pass

        # Fallback nativo con Hardware Scan Code si keyboard fallase
        scan_r = user32.MapVirtualKeyW(VK_R, 0)
        inp_hw_down = INPUT()
        inp_hw_down.type = INPUT_KEYBOARD
        inp_hw_down.u.ki.wVk = 0
        inp_hw_down.u.ki.wScan = scan_r
        inp_hw_down.u.ki.dwFlags = KEYEVENTF_SCANCODE
        user32.SendInput(1, ctypes.byref(inp_hw_down), ctypes.sizeof(INPUT))

        time.sleep(hold_time)

        inp_hw_up = INPUT()
        inp_hw_up.type = INPUT_KEYBOARD
        inp_hw_up.u.ki.wVk = 0
        inp_hw_up.u.ki.wScan = scan_r
        inp_hw_up.u.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        user32.SendInput(1, ctypes.byref(inp_hw_up), ctypes.sizeof(INPUT))
        return True

    def trigger_restart(self, pid=None):
        """
        Ejecuta el reinicio rapido nativo de BonkScanner (mantener presionada la tecla 'R').
        """
        return self.trigger_quick_reset(pid=pid)

    def trigger_warning_beep(self):
        """Alerta sonora para notificar de estancamientos o errores."""
        try:
            kernel32.Beep(480, 220)
        except Exception:
            try:
                user32.MessageBeep(0x00000030)
            except Exception:
                pass

    def send_key(self, vk_code, hold_time=0.06):
        """Envia pulsacion de tecla individual (util para Esc de Pausa AFK)"""
        scan = user32.MapVirtualKeyW(vk_code, 0)

        # Hardware Scan Code
        inp_hw_down = INPUT()
        inp_hw_down.type = INPUT_KEYBOARD
        inp_hw_down.u.ki.wVk = 0
        inp_hw_down.u.ki.wScan = scan
        inp_hw_down.u.ki.dwFlags = KEYEVENTF_SCANCODE
        user32.SendInput(1, ctypes.byref(inp_hw_down), ctypes.sizeof(INPUT))

        # Virtual Key
        inp_vk_down = INPUT()
        inp_vk_down.type = INPUT_KEYBOARD
        inp_vk_down.u.ki.wVk = vk_code
        inp_vk_down.u.ki.wScan = scan
        inp_vk_down.u.ki.dwFlags = 0
        user32.SendInput(1, ctypes.byref(inp_vk_down), ctypes.sizeof(INPUT))

        time.sleep(hold_time)

        # Hardware Scan Code Up
        inp_hw_up = INPUT()
        inp_hw_up.type = INPUT_KEYBOARD
        inp_hw_up.u.ki.wVk = 0
        inp_hw_up.u.ki.wScan = scan
        inp_hw_up.u.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        user32.SendInput(1, ctypes.byref(inp_hw_up), ctypes.sizeof(INPUT))

        # Virtual Key Up
        inp_vk_up = INPUT()
        inp_vk_up.type = INPUT_KEYBOARD
        inp_vk_up.u.ki.wVk = vk_code
        inp_vk_up.u.ki.wScan = scan
        inp_vk_up.u.ki.dwFlags = KEYEVENTF_KEYUP
        user32.SendInput(1, ctypes.byref(inp_vk_up), ctypes.sizeof(INPUT))

    def trigger_afk_safety_pause(self, pid=None):
        """
        Pausa de seguridad AFK: activa la pausa en el juego y reproduce
        una melodía de victoria audible para avisar al usuario.
        Envía UNA SOLA pulsación de ESC para evitar despausar por doble toque.
        """
        self.focus_game(pid=pid)
        time.sleep(0.06)

        esc_sent = False
        if keyboard is not None:
            try:
                keyboard.send('esc')
                esc_sent = True
            except Exception:
                esc_sent = False

        if not esc_sent:
            self.send_key(VK_ESCAPE, hold_time=0.08)

        # Melodía triunfal audible
        try:
            kernel32.Beep(1000, 200)
            time.sleep(0.03)
            kernel32.Beep(1300, 250)
            time.sleep(0.03)
            kernel32.Beep(1700, 450)
        except Exception:
            user32.MessageBeep(0x00000040)

        return True

if __name__ == "__main__":
    bot = PhantomBot()
    print("Megabonk Helper - Controlador BonkScanner listo.")