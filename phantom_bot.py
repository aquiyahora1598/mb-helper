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
import math

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

user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
for _name in ("IsWindowVisible", "SetForegroundWindow", "BringWindowToTop"):
    getattr(user32, _name).argtypes = [wintypes.HWND]
    getattr(user32, _name).restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

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
        if hwnd and pid:
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value != pid:
                hwnd = None
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

        if not hwnd and not pid:
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
            return fg_pid.value == pid
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
        return self.is_game_window_active(pid=pid)

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
                if not math.isfinite(quick_reset_time) or not 0 <= quick_reset_time <= 30:
                    raise ValueError("Tiempo de reinicio inválido")
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
        if not settings.get("enabled", True) or not self.is_game_window_active(pid=pid):
            return False
        hold_time = settings.get("hold_duration", 0.35)
        return self.send_key(VK_R, hold_time=hold_time)

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
        """Una pulsación física; siempre intenta soltar la tecla en finally."""
        scan = user32.MapVirtualKeyW(vk_code, 0)
        if not scan:
            return False
        down = INPUT(type=INPUT_KEYBOARD)
        down.u.ki.wScan = scan
        down.u.ki.dwFlags = KEYEVENTF_SCANCODE
        up = INPUT(type=INPUT_KEYBOARD)
        up.u.ki.wScan = scan
        up.u.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        try:
            if user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT)) != 1:
                return False
            time.sleep(hold_time)
        finally:
            released = user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT)) == 1
        return released

    def trigger_afk_safety_pause(self, pid=None):
        """
        Pausa de seguridad AFK: activa la pausa en el juego y reproduce
        una melodía de victoria audible para avisar al usuario.
        Envía UNA SOLA pulsación de ESC para evitar despausar por doble toque.
        """
        if not self.focus_game(pid=pid):
            return False
        time.sleep(0.06)
        if not self.is_game_window_active(pid=pid) or not self.send_key(VK_ESCAPE, hold_time=0.08):
            return False

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
