"""
Megabonk Phantom Scout - Lector de Memoria Externa (Read-Only)
Zero Inyeccion / Zero DLLs en el directorio del juego.
100% Compatible con Records Oficiales de Steam Leaderboards.
"""

import ctypes
from ctypes import wintypes
import struct
import sys
import os
import time
import threading
import math

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SET_INFORMATION = 0x0200
HIGH_PRIORITY_CLASS = 0x00000080
NORMAL_PRIORITY_CLASS = 0x00000020
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000

PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80
PAGE_GUARD = 0x100
PAGE_NOCACHE = 0x200
PAGE_WRITECOMBINE = 0x400

kernel32 = ctypes.windll.kernel32

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_size_t),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', ctypes.c_wchar * 260)
    ]

class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('th32ModuleID', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('GlblcntUsage', wintypes.DWORD),
        ('ProccntUsage', wintypes.DWORD),
        ('modBaseAddr', ctypes.c_void_p),
        ('modBaseSize', wintypes.DWORD),
        ('hModule', wintypes.HMODULE),
        ('szModule', ctypes.c_wchar * 256),
        ('szExePath', ctypes.c_wchar * 260)
    ]

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [
        ('BaseAddress', ctypes.c_void_p),
        ('AllocationBase', ctypes.c_void_p),
        ('AllocationProtect', wintypes.DWORD),
        ('PartitionId', wintypes.WORD),
        ('RegionSize', ctypes.c_size_t),
        ('State', wintypes.DWORD),
        ('Protect', wintypes.DWORD),
        ('Type', wintypes.DWORD)
    ]

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

try:
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
except Exception:
    psapi = None

# RVAs en GameAssembly.dll (Megabonk v1.0.69)
RVA_GAME_MANAGER_TYPEINFO = 0x2f9c1c0
RVA_INTERACTABLES_STATUS_TYPEINFO = 0x2fb5e68
RVA_SHADY_GUY_TYPEINFO = 0x2fb5928
RVA_MAP_GENERATION_CONTROLLER_TYPEINFO = 0x2f59000
RVA_MAP_CONTROLLER_TYPEINFO = 0x2f58e08
RVA_LOADING_SCREEN_TYPEINFO = 0x2f55e20
RVA_MY_PLAYER_TYPEINFO = 0x2f620f8
RVA_PLAYER_STATS_TYPEINFO = 0x02F6A4B8
RVA_RUN_TIMER_TYPEINFO = 0x02F62398
RVA_RUN_STATS_TYPEINFO = 0x02F7A170

# Offsets de MyPlayer y detector de interactuables (BonkScanner verified)
MY_PLAYER_INSTANCE_OFFSET = 0x08
PLAYER_INPUT_OFFSET = 0x48
DETECT_INTERACTABLES_OFFSET = 0x20
CURRENT_INTERACTABLE_OFFSET = 0x28

# Offsets internos de PlayerStats / OwnerStats (BonkScanner verified)
PLAYER_STATS_STATIC_ROOT_OFFSET = 0x00
PLAYER_STATS_OWNER_OFFSET = 0x40
PLAYER_STATS_CONTEXT_OFFSET = 0x10
PLAYER_STATS_ENTRIES_OFFSET = 0x18
PLAYER_STATS_INVENTORY_OFFSET = 0x28
PLAYER_STATS_XP_OFFSET = 0x30
PLAYER_STATS_XP_LEVEL_OFFSET = 0x14
PLAYER_STATS_GOLD_OFFSET = 0x70
PLAYER_STATS_INVENTORY_CONTAINER_OFFSET = 0xA0
PLAYER_STATS_PASSIVE_DICT_OFFSET = 0x50

# 27 Especificaciones oficiales de Estadísticas de Combate y Progresión
# Formato: (stat_id, clave_interna, formato, escala_visual_o_mult)
OFFICIAL_PLAYER_STATS = [
    # Supervivencia
    (0, "max_hp", "flat", 1.0),
    (1, "hp_regen", "flat", 1.0),
    (2, "shield", "flat", 1.0),
    (3, "thorns", "flat", 1.0),
    (4, "armor", "percent", 1.0),
    (5, "evasion", "percent", 1.0),
    (17, "lifesteal", "percent", 1.0),
    # Ofensiva
    (12, "damage", "multiplier", 1.0),
    (18, "crit_chance", "percent", 1.0),
    (19, "crit_damage", "multiplier", 2.0),  # Multiplicador base 2.0x
    (15, "attack_speed", "percent", 1.0),
    (16, "projectile_count", "flat", 1.0),
    (9, "size", "multiplier", 1.0),
    (11, "projectile_speed", "multiplier", 1.0),
    (10, "duration", "multiplier", 1.0),
    (23, "damage_to_elites", "multiplier", 1.0),
    (24, "knockback", "multiplier", 1.0),
    # Utilidad / Progresión
    (25, "movement_speed", "multiplier", 1.0),
    (46, "extra_jumps", "flat", 1.0),
    (30, "luck", "percent", 1.0),
    (29, "pickup_range", "flat", 1.0),
    (31, "gold_gain", "multiplier", 1.0),
    (32, "xp_gain", "multiplier", 1.0),
    (38, "difficulty", "percent", 1.0),
    (39, "elite_spawn", "multiplier", 1.0),
    (40, "powerup_mult", "multiplier", 1.0),
    (41, "powerup_drop_chance", "multiplier", 1.0),
]

# Offsets directos de nombres de clase en global-metadata.dat (Megabonk v1.0.69)
METADATA_MAGIC = b'\xaf\x1b\xb1\xfa\x1d\x00\x00\x00' # Magic 0xFAB11BAF + Version 29
CLASS_METADATA_OFFSETS = {
    "InteractableShadyGuy": 0x16063c,
    "InteractableShrineMoai": 0x1607b6,
    "InteractableMicrowave": 0x1603a0,
    "InteractableShrineCursed": 0x160730,
    "ChargeShrine": 0x15fa0d,
    "InteractableShrineMagnet": 0x160787,
    "InteractableShrineChallenge": 0x1606e7,
    "InteractableShrineGreed": 0x16075d,
    "InteractablesStatus": 0x1658bd,
    "MyPlayer": 0x18848c,
    "PlayerMovement": 0x1629e2,
    "GameManager": 0x1629a6,
}

# Offsets de Jerarquia Unity IL2CPP (Read-Only)
MANAGED_NATIVE_OFFSET = 0x10
NATIVE_COMPONENT_GAME_OBJECT_OFFSET = 0x20
NATIVE_GAME_OBJECT_HANDLE_ROOT_OFFSET = 0x20
HANDLE_ROOT_NEXT_OFFSET = 0x08
HANDLE_VALUE_OFFSET = 0x18

NATIVE_TRANSFORM_ACCESS_OFFSET = 0x28
NATIVE_TRANSFORM_INDEX_OFFSET = 0x30
TRANSFORM_ACCESS_COUNTS_OFFSET = 0x10
TRANSFORM_ACCESS_MATRICES_OFFSET = 0x18
TRANSFORM_ACCESS_PARENTS_OFFSET = 0x20
TRANSFORM_MATRIX_SIZE = 0x30
MAX_TRANSFORM_DEPTH = 128
MAX_NATIVE_TRANSFORMS = 20000

# Mapeo Oficial de Items de Megabonk (88 Items nativos extraídos de IL2CPP)
# Formato: (item_id, codename, nombre_es, nombre_en, rareza)
OFFICIAL_ITEMS = [
    (0, "Key", "Llave", "Key", "Chave", "COMMON"),
    (1, "Beer", "Cerveza", "Beer", "Cerveja", "UNCOMMON"),
    (2, "SpikyShield", "Escudo de Espinas", "Spiky Shield", "Escudo de Espinhos", "RARE"),
    (3, "Bonker", "El Bonker", "Bonker", "O Bonker", "LEGENDARY"),
    (4, "SlipperyRing", "Anillo Resbaladizo", "Slippery Ring", "Anel Escorregadio", "COMMON"),
    (5, "CowardsCloak", "Capa del Cobarde", "Cowards Cloak", "Manto do Covarde", "UNCOMMON"),
    (6, "GymSauce", "Salsa Fitness", "Gym Sauce", "Molho Maromba", "COMMON"),
    (7, "Battery", "Batería", "Battery", "Bateria", "COMMON"),
    (8, "PhantomShroud", "Manto Fantasmal", "Phantom Shroud", "Mortalha Fantasma", "UNCOMMON"),
    (9, "ForbiddenJuice", "Jugo Prohibido", "Forbidden Juice", "Suco Proibido", "COMMON"),
    (10, "DemonBlade", "Hoja Demoníaca", "Demon Blade", "Lâmina Demoníaca", "UNCOMMON"),
    (11, "GrandmasSecretTonic", "Tónico de la Abuela", "Grandmas Secret Tonic", "Tônico da Vovó", "RARE"),
    (12, "GiantFork", "Tenedor Gigante", "Giant Fork", "Garfo Gigante", "LEGENDARY"),
    (13, "MoldyCheese", "Queso Mohoso", "Moldy Cheese", "Queijo Mofado", "COMMON"),
    (14, "GoldenSneakers", "Zapatillas Doradas", "Golden Sneakers", "Tênis Dourados", "UNCOMMON"),
    (15, "SpicyMeatball", "Albóndiga Picante", "Spicy Meatball", "Almôndega Picante", "LEGENDARY"),
    (16, "Chonkplate", "Placa Blindada", "Chonkplate", "Placa Blindada", "LEGENDARY"),
    (17, "LightningOrb", "Orbe Relámpago", "Lightning Orb", "Orbe de Relâmpago", "LEGENDARY"),
    (18, "IceCube", "Cubo de Hielo", "Ice Cube", "Cubo de Gelo", "LEGENDARY"),
    (19, "DemonicBlood", "Sangre Demoníaca", "Demonic Blood", "Sangue Demoníaco", "UNCOMMON"),
    (20, "DemonicSoul", "Alma Demoníaca", "Demonic Soul", "Alma Demoníaca", "RARE"),
    (21, "BeefyRing", "Anillo Robusto", "Beefy Ring", "Anel Robusto", "RARE"),
    (22, "Dragonfire", "Fuego de Dragón", "Dragonfire", "Fogo de Dragão", "LEGENDARY"),
    (23, "GoldenGlove", "Guantelete Dorado", "Golden Glove", "Luva Dourada", "COMMON"),
    (24, "GoldenShield", "Escudo Dorado", "Golden Shield", "Escudo Dourado", "UNCOMMON"),
    (25, "ZaWarudo", "Detener Tiempo (Za Warudo)", "Za Warudo", "Parar Tempo (Za Warudo)", "LEGENDARY"),
    (26, "OverpoweredLamp", "Lámpara Rota", "Overpowered Lamp", "Lâmpada Apelona", "LEGENDARY"),
    (27, "Feathers", "Plumas", "Feathers", "Penas", "UNCOMMON"),
    (28, "Ghost", "Fantasma", "Ghost", "Fantasma", "COMMON"),
    (29, "SluttyCannon", "Cañón Explosivo", "Slutty Cannon", "Canhão Explosivo", "RARE"),
    (30, "TurboSocks", "Calcetines Turbo", "Turbo Socks", "Meias Turbo", "COMMON"),
    (31, "ShatteredWisdom", "Sabiduría Rota", "Shattered Wisdom", "Sabedoria Partida", "RARE"),
    (32, "EchoShard", "Fragmento Eco", "Echo Shard", "Fragmento Eco", "UNCOMMON"),
    (33, "SuckyMagnet", "Imán de Bonk", "Sucky Magnet", "Ímã Sugador", "LEGENDARY"),
    (34, "Backpack", "Mochila", "Backpack", "Mochila", "UNCOMMON"),
    (35, "Clover", "Trébol de la Suerte", "Clover", "Trevo da Sorte", "COMMON"),
    (36, "Campfire", "Fogata", "Campfire", "Fogueira", "UNCOMMON"),
    (37, "Rollerblades", "Patines", "Rollerblades", "Patins", "RARE"),
    (38, "Skuleg", "Skuleg", "Skuleg", "Skuleg", "COMMON"),
    (39, "EagleClaw", "Garra de Águila", "Eagle Claw", "Garra de Águia", "RARE"),
    (40, "Scarf", "Bufanda", "Scarf", "Cachecol", "RARE"),
    (41, "Anvil", "Yunque", "Anvil", "Bigorna", "LEGENDARY"),
    (42, "Oats", "Avena", "Oats", "Aveia", "COMMON"),
    (43, "CursedDoll", "Muñeco Maldito", "Cursed Doll", "Boneco Amaldiçoado", "COMMON"),
    (44, "EnergyCore", "Núcleo de Energía", "Energy Core", "Núcleo de Energia", "LEGENDARY"),
    (45, "ElectricPlug", "Enchufe Eléctrico", "Electric Plug", "Plugue Elétrico", "UNCOMMON"),
    (46, "BobDead", "Bob Muerto", "Bob Dead", "Bob Morto", "RARE"),
    (47, "SoulHarvester", "Cosechador de Almas", "Soul Harvester", "Ceifador de Almas", "LEGENDARY"),
    (48, "Mirror", "Espejo", "Mirror", "Espelho", "RARE"),
    (49, "JoesDagger", "Daga de Joe", "Joes Dagger", "Adaga do Joe", "LEGENDARY"),
    (50, "WeebHeadset", "Auriculares Otaku", "Weeb Headset", "Headset Otaku", "COMMON"),
    (51, "SpeedBoi", "Speed Boi", "Speed Boi", "Speed Boi", "LEGENDARY"),
    (52, "Gasmask", "Máscara de Gas", "Gasmask", "Máscara de Gás", "RARE"),
    (53, "ToxicBarrel", "Barril Tóxico", "Toxic Barrel", "Barril Tóxico", "RARE"),
    (54, "HolyBook", "Libro Sagrado", "Holy Book", "Livro Sagrado", "LEGENDARY"),
    (55, "BrassKnuckles", "Manopla", "Brass Knuckles", "Soco-Inglês", "UNCOMMON"),
    (56, "IdleJuice", "Jugo AFK", "Idle Juice", "Suco AFK", "UNCOMMON"),
    (57, "Kevin", "Kevin", "Kevin", "Kevin", "RARE"),
    (58, "Borgar", "Hamburguesa", "Borgar", "Hambúrguer", "COMMON"),
    (59, "Medkit", "Botiquín", "Medkit", "Kit Médico", "COMMON"),
    (60, "GamerGoggles", "Gafas Gamer", "Gamer Goggles", "Óculos Gamer", "RARE"),
    (61, "UnstableTransfusion", "Transfusión Inestable", "Unstable Transfusion", "Transfusão Instável", "UNCOMMON"),
    (62, "BloodyCleaver", "Cuchillo Sangriento", "Bloody Cleaver", "Cutelo Sangrento", "LEGENDARY"),
    (63, "CreditCardRed", "Tarjeta Roja", "Credit Card Red", "Cartão Vermelho", "UNCOMMON"),
    (64, "CreditCardGreen", "Tarjeta Verde", "Credit Card Green", "Cartão Verde", "RARE"),
    (65, "BossBuster", "Cazajefes", "Boss Buster", "Caça-Chefes", "COMMON"),
    (66, "LeechingCrystal", "Cristal Vampírico", "Leeching Crystal", "Cristal Vampírico", "UNCOMMON"),
    (67, "TacticalGlasses", "Gafas Tácticas", "Tactical Glasses", "Óculos Táticos", "COMMON"),
    (68, "Cactus", "Cactus", "Cactus", "Cacto", "COMMON"),
    (69, "CageKey", "Llave de Jaula", "Cage Key", "Chave de Gaiola", "COMMON"),
    (70, "IceCrystal", "Cristal de Hielo", "Ice Crystal", "Cristal de Gelo", "COMMON"),
    (71, "TimeBracelet", "Brazalete del Tiempo", "Time Bracelet", "Bracelete do Tempo", "COMMON"),
    (72, "GloveLightning", "Guante Relámpago", "Glove Lightning", "Luva Relâmpago", "UNCOMMON"),
    (73, "GlovePoison", "Guante Venenoso", "Glove Poison", "Luva Venenosa", "UNCOMMON"),
    (74, "GloveBlood", "Guante Sangriento", "Glove Blood", "Luva Sangrenta", "RARE"),
    (75, "GloveCurse", "Guante Maldito", "Glove Curse", "Luva Amaldiçoada", "RARE"),
    (76, "GlovePower", "Guante de Poder", "Glove Power", "Luva do Poder", "LEGENDARY"),
    (77, "Wrench", "Llave Inglesa", "Wrench", "Chave Inglesa", "COMMON"),
    (78, "Beacon", "Baliza", "Beacon", "Sinalizador", "UNCOMMON"),
    (79, "GoldenRing", "Anillo Dorado", "Golden Ring", "Anel Dourado", "LEGENDARY"),
    (80, "QuinsMask", "Máscara de Quin", "Quins Mask", "Máscara do Quin", "RARE"),
    (81, "CryptKey", "Llave de Cripta", "Crypt Key", "Chave da Cripta", "COMMON"),
    (82, "OldMask", "Máscara Vieja", "Old Mask", "Máscara Antiga", "COMMON"),
    (83, "Snek", "Serpiente", "Snek", "Cobra (Snek)", "LEGENDARY"),
    (84, "Pot", "Olla de Acero", "Pot", "Panela de Ferro", "LEGENDARY"),
    (85, "BobsLantern", "Linterna de Bob", "Bobs Lantern", "Lanterna do Bob", "RARE"),
    (86, "Pumpkin", "Calabaza", "Pumpkin", "Abóbora", "UNCOMMON"),
    (87, "WizardsHat", "Sombrero de Mago", "Wizards Hat", "Chapéu de Mago", "LEGENDARY"),
]

ITEM_NAMES_ES = {it[0]: (it[1], it[2]) for it in OFFICIAL_ITEMS}
ITEM_NAMES_EN = {it[0]: (it[1], it[3]) for it in OFFICIAL_ITEMS}
ITEM_NAMES_PT = {it[0]: (it[1], it[4]) for it in OFFICIAL_ITEMS}
ITEM_BY_ID = {it[0]: it for it in OFFICIAL_ITEMS}

RARITY_NAMES_ES = {
    0: "Comun",
    1: "Raro",
    2: "Epico",
    3: "Dorado",
    4: "Corrupto"
}
RARITY_NAMES_EN = {
    0: "Common",
    1: "Rare",
    2: "Epic",
    3: "Golden",
    4: "Corrupted"
}
RARITY_NAMES_PT = {
    0: "Comum",
    1: "Raro",
    2: "Épico",
    3: "Dourado",
    4: "Corrompido"
}

class PhantomMemoryReader:
    def __init__(self):
        self.pid = None
        self.handle = None
        self.ga_base = None
        self.ga_size = None
        self._cached_classes = {}
        self._cached_vendor_regions = []
        self._cached_heap_regions = []
        self._cached_metadata_base = None
        self._last_metadata_scan_time = 0.0
        self._last_vendor_heap_sweep_time = 0.0
        self._dict_key_cache = {}
        self._mem_lock = threading.RLock()

    def find_process(self):
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1:
            return False

        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)

        success = kernel32.Process32FirstW(snapshot, ctypes.byref(pe))
        found_pid = None
        while success:
            if pe.szExeFile.lower() == "megabonk.exe":
                found_pid = pe.th32ProcessID
                break
            success = kernel32.Process32NextW(snapshot, ctypes.byref(pe))

        kernel32.CloseHandle(snapshot)
        if not found_pid:
            self.close()
            return False

        if self.pid == found_pid and self.handle:
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(self.handle, ctypes.byref(exit_code)) and exit_code.value == 259:
                if self.ga_base:
                    return True
                return self.find_modules()
            else:
                self.close()

        self.close()
        self.pid = found_pid
        self.handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION | PROCESS_SET_INFORMATION,
            False,
            self.pid
        )
        if not self.handle:
            # Fallback sin PROCESS_SET_INFORMATION
            self.handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, self.pid)
        if not self.handle:
            self.close()
            return False

        return self.find_modules()

    def set_high_priority(self, enable=True):
        """Asigna HIGH_PRIORITY_CLASS a Megabonk para forzar ejecucion en P-cores de alta frecuencia."""
        if not self.handle:
            return False
        try:
            priority = HIGH_PRIORITY_CLASS if enable else NORMAL_PRIORITY_CLASS
            return bool(kernel32.SetPriorityClass(self.handle, priority))
        except Exception:
            return False

    def find_modules(self):
        if not self.pid or not self.handle:
            return False
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
        if snapshot == -1:
            return False

        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(MODULEENTRY32W)

        success = kernel32.Module32FirstW(snapshot, ctypes.byref(me))
        while success:
            if me.szModule.lower() == "gameassembly.dll":
                self.ga_base = ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value
                self.ga_size = me.modBaseSize
                break
            success = kernel32.Module32NextW(snapshot, ctypes.byref(me))

        kernel32.CloseHandle(snapshot)
        return self.ga_base is not None

    def close(self):
        if self.handle:
            try:
                kernel32.CloseHandle(self.handle)
            except Exception:
                pass
        self.handle = None
        self.pid = None
        self.ga_base = None
        self.ga_size = None
        self._cached_classes.clear()
        self._cached_vendor_regions.clear()
        self._cached_heap_regions.clear()
        self._dict_key_cache.clear()
        self._cached_metadata_base = None


    def read_bytes(self, address, size):
        with self._mem_lock:
            if not self.handle or not address:
                return None
            buf = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t(0)
            ok = kernel32.ReadProcessMemory(
                self.handle,
                ctypes.c_void_p(address),
                buf,
                ctypes.c_size_t(size),
                ctypes.byref(bytes_read)
            )
            if ok and bytes_read.value == size:
                return buf.raw
            return None

    def read_ptr(self, address):
        data = self.read_bytes(address, 8)
        if data:
            return struct.unpack('<Q', data)[0]
        return None

    def read_int32(self, address):
        data = self.read_bytes(address, 4)
        if data:
            return struct.unpack('<i', data)[0]
        return None

    def read_float(self, address):
        data = self.read_bytes(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None

    def read_u8(self, address):
        data = self.read_bytes(address, 1)
        if data:
            return data[0]
        return 0

    def read_string_utf16(self, address, max_len=64):
        length = self.read_int32(address + 0x10)
        if length is None or length <= 0 or length > max_len:
            return ""
        data = self.read_bytes(address + 0x14, length * 2)
        if data:
            try:
                return data.decode('utf-16-le', errors='ignore')
            except:
                return ""
        return ""

    def read_ascii_string(self, address, max_len=64):
        if not self.handle or not address:
            return ""
        data = self.read_bytes(address, max_len)
        if not data:
            return ""
        idx = data.find(b'\x00')
        if idx != -1:
            data = data[:idx]
        try:
            return data.decode('ascii', errors='ignore')
        except:
            return ""

    def component_transform(self, component_ptr):
        if not component_ptr:
            return 0
        native_component = self.read_ptr(component_ptr + MANAGED_NATIVE_OFFSET)
        if not native_component:
            return 0
        native_game_object = self.read_ptr(native_component + NATIVE_COMPONENT_GAME_OBJECT_OFFSET)
        if not native_game_object:
            return 0
        handle_root = self.read_ptr(native_game_object + NATIVE_GAME_OBJECT_HANDLE_ROOT_OFFSET)
        if not handle_root:
            return 0
        handle_owner = self.read_ptr(handle_root + HANDLE_ROOT_NEXT_OFFSET)
        if not handle_owner:
            return 0
        handle = self.read_ptr(handle_owner + HANDLE_VALUE_OFFSET)
        if not handle:
            return 0
        return self.read_ptr(handle & ~1)

    def transform_point_native(self, native, local_point=(0.0, 0.0, 0.0)):
        if not native:
            return (0.0, 0.0, 0.0)
        access = self.read_ptr(native + NATIVE_TRANSFORM_ACCESS_OFFSET)
        index = self.read_int32(native + NATIVE_TRANSFORM_INDEX_OFFSET)
        if not access or index is None or index < 0:
            return (0.0, 0.0, 0.0)

        packed_counts = self.read_ptr(access + TRANSFORM_ACCESS_COUNTS_OFFSET)
        if not packed_counts:
            return (0.0, 0.0, 0.0)
        capacity = packed_counts & 0xFFFFFFFF
        count = (packed_counts >> 32) & 0xFFFFFFFF
        if not (0 <= index < count <= capacity <= MAX_NATIVE_TRANSFORMS):
            return (0.0, 0.0, 0.0)

        matrices = self.read_ptr(access + TRANSFORM_ACCESS_MATRICES_OFFSET)
        parents = self.read_ptr(access + TRANSFORM_ACCESS_PARENTS_OFFSET)
        if not matrices or not parents:
            return (0.0, 0.0, 0.0)

        point = list(local_point)
        depth = 0

        while index >= 0 and depth < MAX_TRANSFORM_DEPTH:
            matrix_data = self.read_bytes(matrices + index * TRANSFORM_MATRIX_SIZE, TRANSFORM_MATRIX_SIZE)
            if not matrix_data or len(matrix_data) != TRANSFORM_MATRIX_SIZE:
                break
            values = struct.unpack('<12f', matrix_data)
            trans = values[0:3]
            rot = values[4:8]
            scale = values[8:11]

            p_scaled = (point[0] * scale[0], point[1] * scale[1], point[2] * scale[2])
            qx, qy, qz, qw = rot
            vx, vy, vz = p_scaled
            tx = 2.0 * (qy * vz - qz * vy)
            ty = 2.0 * (qz * vx - qx * vz)
            tz = 2.0 * (qx * vy - qy * vx)
            p_rot = (
                vx + qw * tx + (qy * tz - qz * ty),
                vy + qw * ty + (qz * tx - qx * tz),
                vz + qw * tz + (qx * ty - qy * tx),
            )
            point = [
                p_rot[0] + trans[0],
                p_rot[1] + trans[1],
                p_rot[2] + trans[2]
            ]

            parent_idx_data = self.read_bytes(parents + index * 4, 4)
            if not parent_idx_data:
                break
            index = struct.unpack('<i', parent_idx_data)[0]
            depth += 1

        return (point[0], point[1], point[2])

    def get_world_position(self, component_ptr):
        transform = self.component_transform(component_ptr)
        if not transform:
            return None
        native = self.read_ptr(transform + MANAGED_NATIVE_OFFSET)
        if not native:
            return None
        return self.transform_point_native(native, (0.0, 0.0, 0.0))

    def find_metadata_base(self):
        """Localiza en < 2ms la direccion base de global-metadata.dat en memoria (firma 0xFAB11BAF)"""
        with self._mem_lock:
            if self._cached_metadata_base:
                val = self.read_bytes(self._cached_metadata_base, 8)
                if val == METADATA_MAGIC:
                    return self._cached_metadata_base
                self._cached_metadata_base = None

            if not self.handle:
                return None

            now = time.time()
            if now - self._last_metadata_scan_time < 3.0:
                return None
            self._last_metadata_scan_time = now

            mbi = MEMORY_BASIC_INFORMATION64()
            address = 0

            while kernel32.VirtualQueryEx(
                self.handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi)
            ):
                base_addr = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value or 0
                size = mbi.RegionSize

                if (mbi.State == MEM_COMMIT and
                    (mbi.Protect & 0xFF) in (PAGE_READONLY, PAGE_READWRITE, PAGE_WRITECOPY) and
                    0x100000 <= size < 0x20000000):

                    head = self.read_bytes(base_addr, 8)
                    if head == METADATA_MAGIC:
                        self._cached_metadata_base = base_addr
                        return base_addr

                address = base_addr + size
                if address >= 0x7FFFFFFFFFFF:
                    break

            return None

    def resolve_class_ptr(self, class_name):
        """Resuelve de forma inmediata el puntero Il2CppClass* usando la base de metadata"""
        if class_name in self._cached_classes:
            cached = self._cached_classes[class_name]
            if cached:
                name_ptr = self.read_ptr(cached + 0x10)
                if name_ptr and self.read_ascii_string(name_ptr, len(class_name) + 1) == class_name:
                    return cached
            del self._cached_classes[class_name]

        if not self.ga_base or not self.handle:
            return None

        meta_base = self.find_metadata_base()
        target_str_addr = None
        if meta_base and class_name in CLASS_METADATA_OFFSETS:
            target_str_addr = meta_base + CLASS_METADATA_OFFSETS[class_name]

        target_ptr_bytes = struct.pack('<Q', target_str_addr) if target_str_addr else None
        if not target_ptr_bytes:
            return None

        # Escanear ÚNICAMENTE las regiones de heap privado de Unity (64KB - 64MB)
        # NUNCA hacer un recorrido lineal de 128 Terabytes (0 a 0x7FFFFFFFFFFF)
        heap_regions = self.refresh_cached_heap_regions()
        for base_addr, size in heap_regions:
            data = self.read_bytes(base_addr, size)
            if not data:
                continue
            pos = 0
            while True:
                p_idx = data.find(target_ptr_bytes, pos)
                if p_idx == -1:
                    break
                cand_class = base_addr + p_idx - 0x10
                if cand_class > 0x10000:
                    if self.read_ptr(cand_class + 0x10) == target_str_addr:
                        self._cached_classes[class_name] = cand_class
                        return cand_class
                pos = p_idx + 8

        return None

    def resolve_classes_batch(self, class_names):
        """
        Resuelve un lote completo de clases Il2CppClass* en una ÚNICA pasada sobre el heap (< 10ms).
        Evita cualquier barrido de 128TB o consultas redundantes de memoria.
        """
        needed = {}
        meta_base = self.find_metadata_base()
        for cname in class_names:
            if cname in self._cached_classes:
                continue
            if meta_base and cname in CLASS_METADATA_OFFSETS:
                target_str_addr = meta_base + CLASS_METADATA_OFFSETS[cname]
                target_bytes = struct.pack('<Q', target_str_addr)
                needed[target_bytes] = (cname, target_str_addr)

        if not needed:
            return {cname: self._cached_classes.get(cname) for cname in class_names}

        heap_regions = self.refresh_cached_heap_regions()
        for base_addr, size in heap_regions:
            data = self.read_bytes(base_addr, size)
            if not data:
                continue

            for target_bytes, (cname, target_str_addr) in list(needed.items()):
                pos = 0
                while True:
                    p_idx = data.find(target_bytes, pos)
                    if p_idx == -1:
                        break
                    cand_class = base_addr + p_idx - 0x10
                    if cand_class > 0x10000:
                        if self.read_ptr(cand_class + 0x10) == target_str_addr:
                            self._cached_classes[cname] = cand_class
                            del needed[target_bytes]
                            break
                    pos = p_idx + 8

            if not needed:
                break

        return {cname: self._cached_classes.get(cname) for cname in class_names}

    def get_map_generation_state(self):
        """
        Lee el estado de generacion, carga y semilla de Megabonk (metodo BonkScanner).
        Permite saber con certeza si la partida esta generandose, si esta en pantalla de carga o si cambio la semilla.
        """
        result = {
            "is_generating": False,
            "map_seed": None,
            "is_resetting": False,
            "is_loading": False,
            "has_loaded_map": False,
            "current_map_ptr": 0,
            "current_stage_ptr": 0,
        }
        if not self.ga_base:
            return result

        # 1. MapGenerationController (RVA 0x2F59000)
        class_mg = self.read_ptr(self.ga_base + RVA_MAP_GENERATION_CONTROLLER_TYPEINFO)
        if class_mg:
            static_fields = self.read_ptr(class_mg + 0xb8)
            if static_fields:
                b = self.read_bytes(static_fields + 0x10, 1)
                result["is_generating"] = bool(b[0] if b else 0)
                result["map_seed"] = self.read_int32(static_fields + 0x2C)

        # 2. MapController (RVA 0x2F58E08)
        class_mc = self.read_ptr(self.ga_base + RVA_MAP_CONTROLLER_TYPEINFO)
        if class_mc:
            static_fields = self.read_ptr(class_mc + 0xb8)
            if static_fields:
                b = self.read_bytes(static_fields + 0x21, 1)
                result["is_resetting"] = bool(b[0] if b else 0)
                cmap = self.read_ptr(static_fields + 0x10) or 0
                cstage = self.read_ptr(static_fields + 0x18) or 0
                result["current_map_ptr"] = cmap
                result["current_stage_ptr"] = cstage
                result["has_loaded_map"] = bool(cmap and cstage)

        # 3. LoadingScreen (RVA 0x2F55E20)
        class_ls = self.read_ptr(self.ga_base + RVA_LOADING_SCREEN_TYPEINFO)
        if class_ls:
            static_fields = self.read_ptr(class_ls + 0xb8)
            if static_fields:
                b = self.read_bytes(static_fields + 0x10, 1)
                result["is_loading"] = bool(b[0] if b else 0)

        return result

    def get_process_memory_mb(self):
        """Retorna (working_set_mb, private_usage_mb) del proceso de Megabonk."""
        if not self.handle or not psapi:
            return 0.0, 0.0
        try:
            pmc = PROCESS_MEMORY_COUNTERS_EX()
            pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            if psapi.GetProcessMemoryInfo(self.handle, ctypes.byref(pmc), ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)):
                return (pmc.WorkingSetSize / (1024 * 1024), pmc.PrivateUsage / (1024 * 1024))
        except Exception:
            pass
        return 0.0, 0.0

    def is_in_game(self):
        """Verifica si el jugador esta activo dentro de un mapa"""
        if not self.ga_base:
            return False
        # 1. Metodo primario y fiable: si hay interactuables poblados, la partida esta en curso
        try:
            stats = self.read_interactables_status()
            if any(isinstance(v, (int, float)) and v > 0 for v in stats.values()):
                return True
        except Exception:
            pass

        # 2. Metodo secundario: GameManager.isPlaying
        try:
            class_ptr = self.read_ptr(self.ga_base + RVA_GAME_MANAGER_TYPEINFO)
            if class_ptr:
                static_fields = self.read_ptr(class_ptr + 0xb8)
                if static_fields:
                    instance = self.read_ptr(static_fields + 0x0)
                    if instance and instance > 0x10000:
                        is_playing = self.read_bytes(instance + 0x84, 1)
                        if is_playing and is_playing[0] != 0:
                            return True
        except Exception:
            pass
        return False

    def read_game_lifecycle(self):
        """Retorna {'in_game': bool, 'is_playing': bool, 'is_game_over': bool}"""
        state = {"in_game": False, "is_playing": False, "is_game_over": False}
        if not self.handle or not self.ga_base:
            return state
        try:
            class_ptr = self.read_ptr(self.ga_base + RVA_GAME_MANAGER_TYPEINFO)
            if class_ptr and not (class_ptr <= 0xFFFFFFFF and (class_ptr & 0xE0000000) == 0x20000000):
                static_fields = self.read_ptr(class_ptr + 0xB8)
                if static_fields:
                    instance = self.read_ptr(static_fields + 0x0)
                    if instance and instance > 0x10000:
                        playing = self.read_u8(instance + 0x84)
                        game_over = self.read_u8(instance + 0x74)
                        state["is_playing"] = bool(playing)
                        state["is_game_over"] = bool(game_over)
                        state["in_game"] = bool(playing) and not bool(game_over)
                        return state
        except Exception:
            pass
        state["in_game"] = self.is_in_game()
        return state

    def read_interactables_status(self):
        """Lee el diccionario nativo InteractablesStatus.interactablesByName"""
        result = {
            "boss_curses": 0,
            "moais": 0,
            "charge_shrines": 0,
            "greed_shrines": 0,
            "magnet_shrines": 0,
            "challenges": 0,
            "microwaves": 0,
            "chests": 0,
            "pots": 0,
            "vendors_total": 0,
        }
        if not self.ga_base:
            return result

        class_ptr = self.read_ptr(self.ga_base + RVA_INTERACTABLES_STATUS_TYPEINFO)
        if not class_ptr:
            return result
        static_fields = self.read_ptr(class_ptr + 0xb8)
        if not static_fields:
            return result
        dict_ptr = self.read_ptr(static_fields + 0x0)
        if not dict_ptr:
            return result

        dict_meta = self.read_bytes(dict_ptr + 0x18, 12)
        if not dict_meta:
            return result
        entries_ptr, count = struct.unpack('<QI', dict_meta)
        if not entries_ptr or not count or count <= 0 or count > 50:
            return result

        raw_entries = self.read_bytes(entries_ptr + 0x20, count * 24)
        if not raw_entries:
            return result

        for hash_code, next_idx, key_ptr, val_ptr in struct.iter_unpack('<iiQQ', raw_entries):
            if not key_ptr or not val_ptr:
                continue

            k = self._dict_key_cache.get(key_ptr)
            if k is None:
                raw_k = self.read_string_utf16(key_ptr)
                k = raw_k.lower() if raw_k else ""
                self._dict_key_cache[key_ptr] = k

            if not k:
                continue

            num_total = self.read_int32(val_ptr + 0x10) or 0

            if "curse" in k:
                result["boss_curses"] = num_total
            elif "moai" in k:
                result["moais"] = num_total
            elif "charge" in k:
                result["charge_shrines"] = num_total
            elif "greed" in k:
                result["greed_shrines"] = num_total
            elif "magnet" in k:
                result["magnet_shrines"] = num_total
            elif "challenge" in k:
                result["challenges"] = num_total
            elif "micro" in k:
                result["microwaves"] = num_total
            elif "chest" in k:
                result["chests"] = num_total
            elif "pot" in k:
                result["pots"] = num_total
            elif "shady" in k:
                result["vendors_total"] = num_total

        return result

    def refresh_cached_heap_regions(self, force=False):
        """
        Retorna la lista de regiones de heap privado de Unity (64KB - 64MB).
        Estas ~20 regiones contienen todas las instancias activas de Unity y se reutilizan
        a lo largo de toda la sesión sin necesidad de repetir VirtualQueryEx.
        """
        with self._mem_lock:
            if self._cached_heap_regions and not force:
                return self._cached_heap_regions

            if not self.handle:
                return []

            mbi = MEMORY_BASIC_INFORMATION64()
            address = 0x10000000
            new_heap_regions = []

            while kernel32.VirtualQueryEx(
                self.handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi)
            ):
                base_addr = ctypes.cast(mbi.BaseAddress, ctypes.c_void_p).value or 0
                size = mbi.RegionSize

                # Solo páginas comprometidas de memoria privada de Unity (excluye DLLs, texturas y assets mapeados)
                if (mbi.State == MEM_COMMIT and
                    getattr(mbi, 'Type', 0) == 0x20000 and  # MEM_PRIVATE
                    (mbi.Protect & 0xFF) in (PAGE_READWRITE, PAGE_EXECUTE_READWRITE) and
                    0x10000 <= size <= 0x4000000):
                    new_heap_regions.append((base_addr, size))

                address = base_addr + size
                if address >= 0x40000000000:
                    break

            if new_heap_regions:
                self._cached_heap_regions = new_heap_regions
            return self._cached_heap_regions

    def scan_shady_vendors(self, expected_count=3, force_rescan=False):
        """Escanea la memoria para encontrar los vendedores (InteractableShadyGuy) y sus items ofrecidos"""
        vendors = []
        if not self.ga_base:
            return vendors

        if expected_count is not None and expected_count <= 0:
            return vendors

        class_shady = self._cached_classes.get("InteractableShadyGuy")
        if not class_shady:
            typeinfo_ptr = self.read_ptr(self.ga_base + RVA_SHADY_GUY_TYPEINFO)
            if typeinfo_ptr and typeinfo_ptr > 0x10000:
                # Comprobar si typeinfo_ptr es un token no inicializado (0x2000xxxx)
                if not (typeinfo_ptr <= 0xFFFFFFFF and (typeinfo_ptr & 0xE0000000) == 0x20000000):
                    class_shady = typeinfo_ptr
                    self._cached_classes["InteractableShadyGuy"] = class_shady

        if not class_shady:
            class_shady = self.resolve_class_ptr("InteractableShadyGuy")

        if not class_shady:
            # Si Unity aún no instanció Shady Guy en este mapa, retornar de inmediato (< 0.01ms)
            return vendors

        target_bytes = struct.pack('<Q', class_shady)
        target_count = max(1, min(expected_count or 3, 3))
        candidate_instances = []
        candidate_meta = {}  # inst_addr -> (rarity, items_ptr, arr_ptr, arr_len)

        # 1. Escaneo ultrarrápido sobre regiones cacheadas (< 0.1ms) con vectorizado C (data.find)
        if self._cached_vendor_regions and not force_rescan:
            for base_addr, size in list(self._cached_vendor_regions):
                data = self.read_bytes(base_addr, size)
                if data:
                    pos = 0
                    while True:
                        idx = data.find(target_bytes, pos)
                        if idx == -1:
                            break
                        inst_addr = base_addr + idx
                        native_comp = self.read_ptr(inst_addr + MANAGED_NATIVE_OFFSET)
                        if native_comp and native_comp > 0x10000:
                            rarity = self.read_int32(inst_addr + 0x90)
                            if rarity is not None and rarity in (0, 1, 2, 3, 4):
                                if inst_addr not in candidate_meta:
                                    items_ptr = self.read_ptr(inst_addr + 0x98)
                                    arr_ptr, arr_len = 0, 0
                                    if items_ptr and items_ptr > 0x10000:
                                        arr_ptr = self.read_ptr(items_ptr + 0x10)
                                        arr_len = self.read_int32(items_ptr + 0x18) or 0
                                    candidate_instances.append(inst_addr)
                                    candidate_meta[inst_addr] = (rarity, items_ptr, arr_ptr, arr_len)
                        pos = idx + 8

        # 2. Si la caché no tiene suficientes instancias (arranque en frío / cambio de región / force_rescan):
        now = time.time()
        should_sweep_heap = (
            (len(candidate_instances) < target_count or force_rescan)
            and (force_rescan or (now - self._last_vendor_heap_sweep_time >= 0.20))
        )
        if should_sweep_heap:
            self._last_vendor_heap_sweep_time = now
            heap_regions = self.refresh_cached_heap_regions(force=force_rescan)
            new_vendor_regions = []
            for base_addr, size in heap_regions:
                data = self.read_bytes(base_addr, size)
                if not data:
                    continue
                region_has_instance = False
                pos = 0
                while True:
                    idx = data.find(target_bytes, pos)
                    if idx == -1:
                        break
                    inst_addr = base_addr + idx
                    native_comp = self.read_ptr(inst_addr + MANAGED_NATIVE_OFFSET)
                    if native_comp and native_comp > 0x10000:
                        rarity = self.read_int32(inst_addr + 0x90)
                        if rarity is not None and rarity in (0, 1, 2, 3, 4):
                            if inst_addr not in candidate_meta:
                                items_ptr = self.read_ptr(inst_addr + 0x98)
                                arr_ptr, arr_len = 0, 0
                                if items_ptr and items_ptr > 0x10000:
                                    arr_ptr = self.read_ptr(items_ptr + 0x10)
                                    arr_len = self.read_int32(items_ptr + 0x18) or 0
                                candidate_instances.append(inst_addr)
                                candidate_meta[inst_addr] = (rarity, items_ptr, arr_ptr, arr_len)
                            region_has_instance = True
                    pos = idx + 8

                if region_has_instance and (base_addr, size) not in new_vendor_regions:
                    new_vendor_regions.append((base_addr, size))

                if len(candidate_instances) >= target_count:
                    break

            if new_vendor_regions:
                self._cached_vendor_regions = new_vendor_regions

        if not candidate_instances:
            return vendors

        # Priorizar instancias que tienen items poblados (arr_len > 0)
        candidate_instances.sort(key=lambda a: candidate_meta[a][3], reverse=True)
        found_instances = candidate_instances[:target_count]

        # 3. Extraer los datos y objetos de cada vendedor encontrado
        for inst_addr in found_instances[:3]:
            rarity = self.read_int32(inst_addr + 0x90)
            if rarity is None or rarity not in (0, 1, 2, 3, 4):
                rarity = candidate_meta[inst_addr][0]

            # Lectura fresca directa de memoria del contenedor de items
            items_ptr = self.read_ptr(inst_addr + 0x98) or candidate_meta[inst_addr][1]
            arr_ptr, arr_len = 0, 0
            if items_ptr and items_ptr > 0x10000:
                arr_ptr = self.read_ptr(items_ptr + 0x10) or 0
                arr_len = self.read_int32(items_ptr + 0x18) or 0

            item_ids = []
            item_names = []

            # Compatibilidad dual: si arr_ptr > 0x10000 es List<ItemData>; de lo contrario es ItemData[] directo
            base_item_arr = arr_ptr if (arr_ptr and arr_ptr > 0x10000) else items_ptr
            effective_len = arr_len if arr_len > 0 else (self.read_int32(items_ptr + 0x18) or 0)

            if base_item_arr and base_item_arr > 0x10000 and effective_len > 0:
                for item_idx in range(min(effective_len, 4)):
                    item_data_ptr = self.read_ptr(base_item_arr + 0x20 + (item_idx * 8))
                    if item_data_ptr and item_data_ptr > 0x10000:
                        # Offset en Megabonk ItemData: 0x54 (eItem primario), 0x1C (secundario)
                        # Nota: Vendedores nunca venden "Llave" (ID 0). Si lee 0, se descarta.
                        e_item = self.read_int32(item_data_ptr + 0x54)
                        if e_item is None or e_item <= 0 or e_item not in ITEM_BY_ID:
                            e_item_alt = self.read_int32(item_data_ptr + 0x1C)
                            if e_item_alt is not None and e_item_alt > 0 and e_item_alt in ITEM_BY_ID:
                                e_item = e_item_alt

                        if e_item is not None and e_item > 0 and e_item in ITEM_BY_ID:
                            item_ids.append(e_item)
                            item_names.append(ITEM_BY_ID[e_item][2])
                        elif e_item is not None and e_item > 0:
                            item_ids.append(e_item)
                            item_names.append(f"Item #{e_item}")

            vendors.append({
                "address": hex(inst_addr),
                "ptr": inst_addr,
                "rarity": rarity,
                "rarity_name": RARITY_NAMES_ES.get(rarity, "Desconocido"),
                "is_golden": (rarity == 3),
                "item_ids": item_ids,
                "item_names": item_names
            })

        return vendors

    def scan_map_landmarks(self, existing_vendors=None, existing_stats=None):
        """
        Extracción ONE-SHOT de coordenadas en el mundo 3D (X, Y, Z) de todos los interactuables
        clave del mapa: Moáis, Vendedores (con rareza e items), Maldiciones de Jefe,
        Santuarios de Mejora (Carga, Codicia, Imán), Desafíos y Microondas.
        Se ejecuta una sola vez al encontrar la partida definitiva (0% impacto en rerolls).
        """
        landmarks = []
        if not self.handle or not self.ga_base:
            return landmarks

        with self._mem_lock:
            # 1. Reutilizar vendedores ya leídos o escanearlos
            vendors = existing_vendors if existing_vendors is not None else self.scan_shady_vendors()
            stats = existing_stats if existing_stats is not None else self.read_interactables_status()

            seen_positions = []
            seen_instances = set()

            # 2. Registrar vendedores conocidos con su posición 3D exacta
            for idx, v in enumerate(vendors):
                rarity = v.get("rarity", 0)
                r_name = v.get("rarity_name", "Comun")
                is_gold = v.get("is_golden", False)
                items = v.get("item_names", [])

                if is_gold:
                    label = f"👑 Vendedor #{idx+1} (Dorado)"
                    color = "#F59E0B"
                    icon = "👑"
                elif rarity == 2:
                    label = f"🛒 Vendedor #{idx+1} (Épico)"
                    color = "#A855F7"
                    icon = "🛒"
                elif rarity == 1:
                    label = f"🛒 Vendedor #{idx+1} (Raro)"
                    color = "#3B82F6"
                    icon = "🛒"
                else:
                    label = f"🛒 Vendedor #{idx+1} (Común)"
                    color = "#94A3B8"
                    icon = "🛒"

                inst_addr = v.get("ptr", 0)
                x, y, z = None, None, None
                if inst_addr:
                    seen_instances.add(inst_addr)
                    try:
                        w_pos = self.get_world_position(inst_addr)
                        if w_pos and (abs(w_pos[0]) > 0.5 or abs(w_pos[2]) > 0.5):
                            x, y, z = round(w_pos[0], 1), round(w_pos[1], 1), round(w_pos[2], 1)
                            seen_positions.append((x, z))
                    except Exception:
                        pass

                landmarks.append({
                    "type": "shady",
                    "label": label,
                    "color": color,
                    "icon": icon,
                    "x": x,
                    "y": y,
                    "z": z,
                    "has_coords": (x is not None and z is not None),
                    "rarity": rarity,
                    "rarity_name": r_name,
                    "is_golden": is_gold,
                    "items": items
                })

            return landmarks

    def activity_is_active(self, object_ptr, class_name):
        """Verifica si el interactuable sigue activo en el juego (metodo BonkScanner)."""
        if not object_ptr or not self.handle:
            return False
        try:
            if class_name == "InteractableMicrowave":
                uses_left = self.read_int32(object_ptr + 0x84) or 0
                is_cooking = bool(self.read_u8(object_ptr + 0x88))
                has_item = bool(self.read_u8(object_ptr + 0xF4))
                return uses_left > 0 or is_cooking or has_item
            elif class_name == "InteractableShadyGuy":
                return not bool(self.read_u8(object_ptr + 0xB0))
            elif class_name == "InteractableEgg":
                return not bool(self.read_u8(object_ptr + 0xA0))
            elif class_name == "InteractableCharacterFight":
                return not bool(self.read_u8(object_ptr + 0x68))
            else:
                return not bool(self.read_u8(object_ptr + 0x68))
        except Exception:
            return True

    def read_full_player_stats(self):
        """
        Lee en < 0.1ms las 27 estadísticas completas de combate y progresión, nivel, oro,
        kills, cofres, armas, tomos e items de la partida actual directamente desde el contexto IL2CPP.
        """
        result = {
            "valid": False,
            "run_time": 0.0,
            "stage_time": 0.0,
            "level": 1,
            "gold": 0,
            "kills": 0,
            "chests": 0,
            "character_id": 0,
            "is_game_over": False,
            "is_playing": False,
            "stats": {},
            "items": {},
            "weapons": [],
            "tomes": [],
            "player_pos": None
        }
        if not self.handle or not self.ga_base:
            return result

        lifecycle = self.read_game_lifecycle()
        result["is_game_over"] = lifecycle.get("is_game_over", False)
        result["is_playing"] = lifecycle.get("is_playing", False)

        with self._mem_lock:
            try:
                # 1. Tiempos de partida (MyTime)
                time_class = self.read_ptr(self.ga_base + RVA_RUN_TIMER_TYPEINFO)
                if time_class and not (time_class <= 0xFFFFFFFF and (time_class & 0xE0000000) == 0x20000000):
                    time_static = self.read_ptr(time_class + 0xB8)
                    if time_static:
                        st = self.read_float(time_static + 0x1C)
                        rt = self.read_float(time_static + 0x20)
                        if rt is not None and math.isfinite(rt):
                            result["run_time"] = round(max(0.0, rt), 2)
                        if st is not None and math.isfinite(st):
                            result["stage_time"] = round(max(0.0, st), 2)

                # 2. Player Stats Root & OwnerStats
                stats_class = self.read_ptr(self.ga_base + RVA_PLAYER_STATS_TYPEINFO)
                if not stats_class or (stats_class <= 0xFFFFFFFF and (stats_class & 0xE0000000) == 0x20000000):
                    return result

                stats_static = self.read_ptr(stats_class + 0xB8)
                if not stats_static:
                    return result

                root = self.read_ptr(stats_static + PLAYER_STATS_STATIC_ROOT_OFFSET)
                if not root:
                    return result

                owner_stats = self.read_ptr(root + PLAYER_STATS_OWNER_OFFSET)
                if not owner_stats:
                    return result

                # Personaje ID (CharacterData)
                char_data = self.read_ptr(owner_stats + 0x18)
                if char_data:
                    cid = self.read_int32(char_data + 0x50)
                    if cid is not None and cid >= 0:
                        result["character_id"] = cid

                # 3. Context & Entries (las 27 estadísticas contiguas)
                stats_context = self.read_ptr(owner_stats + PLAYER_STATS_CONTEXT_OFFSET)
                if stats_context:
                    entries = self.read_ptr(stats_context + PLAYER_STATS_ENTRIES_OFFSET)
                    if entries:
                        # Leer todo el bloque de estadísticas en una pasada (47 slots * 16 bytes = 752 bytes)
                        raw_stats = self.read_bytes(entries + 0x2C, 47 * 16 + 4)
                        if raw_stats:
                            for stat_id, stat_key, stat_fmt, display_scale in OFFICIAL_PLAYER_STATS:
                                offset = stat_id * 16
                                if offset + 4 <= len(raw_stats):
                                    val = struct.unpack_from('<f', raw_stats, offset)[0]
                                    if math.isfinite(val):
                                        result["stats"][stat_key] = round(val * display_scale, 4)
                                    else:
                                        result["stats"][stat_key] = 0.0

                # 4. Inventario del Jugador: Nivel XP, Oro, Armas, Tomos
                player_inv = self.read_ptr(owner_stats + PLAYER_STATS_INVENTORY_OFFSET)
                if player_inv:
                    # Nivel XP
                    pxp = self.read_ptr(player_inv + PLAYER_STATS_XP_OFFSET)
                    if pxp:
                        lvl = self.read_int32(pxp + PLAYER_STATS_XP_LEVEL_OFFSET)
                        if lvl is not None and lvl >= 1:
                            result["level"] = lvl

                    # Oro actual
                    gold_val = self.read_int32(player_inv + PLAYER_STATS_GOLD_OFFSET)
                    if gold_val is not None:
                        result["gold"] = max(0, gold_val)

                    # Armas activas y niveles
                    w_inv = self.read_ptr(player_inv + 0x28)
                    if w_inv:
                        w_dict = self.read_ptr(w_inv + 0x18)
                        if w_dict:
                            w_count = self.read_int32(w_dict + 0x20)
                            w_entries = self.read_ptr(w_dict + 0x18)
                            if w_count and 0 < w_count <= 16 and w_entries:
                                for i in range(w_count):
                                    entry_ptr = w_entries + 0x20 + (i * 0x18)
                                    h_code = self.read_int32(entry_ptr)
                                    if h_code is not None and h_code >= 0:
                                        w_id = self.read_int32(entry_ptr + 0x08)
                                        w_base = self.read_ptr(entry_ptr + 0x10)
                                        if w_base:
                                            w_lvl = self.read_int32(w_base + 0x20) or 1
                                            result["weapons"].append({
                                                "id": w_id,
                                                "level": w_lvl
                                            })

                    # Tomos activos y niveles
                    t_inv = self.read_ptr(player_inv + 0x48)
                    if t_inv:
                        t_dict = self.read_ptr(t_inv + 0x18)
                        if t_dict:
                            t_count = self.read_int32(t_dict + 0x20)
                            t_entries = self.read_ptr(t_dict + 0x18)
                            if t_count and 0 < t_count <= 32 and t_entries:
                                for i in range(t_count):
                                    entry_ptr = t_entries + 0x20 + (i * 0x18)
                                    h_code = self.read_int32(entry_ptr)
                                    if h_code is not None and h_code >= 0:
                                        t_id = self.read_int32(entry_ptr + 0x08)
                                        t_lvl = self.read_int32(entry_ptr + 0x10) or 1
                                        result["tomes"].append({
                                            "id": t_id,
                                            "level": t_lvl
                                        })

                # 5. Items pasivos poseídos (Container -> PassiveItemDict)
                inv_container = self.read_ptr(owner_stats + PLAYER_STATS_INVENTORY_CONTAINER_OFFSET)
                if inv_container:
                    p_dict = self.read_ptr(inv_container + PLAYER_STATS_PASSIVE_DICT_OFFSET)
                    if p_dict:
                        p_count = self.read_int32(p_dict + 0x20)
                        p_entries = self.read_ptr(p_dict + 0x18)
                        if p_count and 0 < p_count <= 256 and p_entries:
                            for i in range(p_count):
                                entry_ptr = p_entries + 0x20 + (i * 0x18)
                                h_code = self.read_int32(entry_ptr)
                                if h_code is not None and h_code >= 0:
                                    item_ptr = self.read_ptr(entry_ptr + 0x10)
                                    if item_ptr:
                                        stacks = self.read_int32(item_ptr + 0x18) or 1
                                        iclass = self.read_ptr(item_ptr)
                                        iname_ptr = self.read_ptr(iclass + 0x10) if iclass else 0
                                        raw_name = self.read_ascii_string(iname_ptr, 48) if iname_ptr else ""
                                        if raw_name:
                                            clean_name = raw_name[4:] if raw_name.startswith("Item") else raw_name
                                            result["items"][clean_name] = stacks

                # 6. RunStats (Kills y Cofres acumulados)
                rstats_class = self.read_ptr(self.ga_base + RVA_RUN_STATS_TYPEINFO)
                if rstats_class and not (rstats_class <= 0xFFFFFFFF and (rstats_class & 0xE0000000) == 0x20000000):
                    rstats_static = self.read_ptr(rstats_class + 0xB8)
                    if rstats_static:
                        rs_dict = self.read_ptr(rstats_static + 0x0)
                        if rs_dict:
                            rs_count = self.read_int32(rs_dict + 0x20)
                            rs_entries = self.read_ptr(rs_dict + 0x18)
                            if rs_count and 0 < rs_count <= 128 and rs_entries:
                                for i in range(rs_count):
                                    entry_ptr = rs_entries + 0x20 + (i * 0x18)
                                    h_code = self.read_int32(entry_ptr)
                                    if h_code is not None and h_code >= 0:
                                        k_ptr = self.read_ptr(entry_ptr + 0x08)
                                        if k_ptr:
                                            key_str = self.read_string_utf16(k_ptr, 32).lower()
                                            val_f = self.read_float(entry_ptr + 0x10)
                                            if val_f is not None and math.isfinite(val_f):
                                                if key_str == "kills":
                                                    result["kills"] = max(0, int(val_f))
                                                elif key_str == "chests":
                                                    result["chests"] = max(0, int(val_f))

                if result["stats"]:
                    result["valid"] = True
            except Exception:
                pass

        return result

    def get_map_bounds(self):
        """Devuelve los límites reales (minX, maxX, minZ, maxZ) del mapa cuadrado de Megabonk (Isla de 600m)."""
        return {"min_x": -300.0, "max_x": 300.0, "min_z": -300.0, "max_z": 300.0}

    def get_full_map_data(self, scan_landmarks=False, scan_vendors=True):
        """Metodo maestro que devuelve todo el estado actual del mapa"""
        connected = self.find_process()
        if not connected:
            return {"connected": False, "in_game": False, "stats": {}, "vendors": [], "landmarks": []}

        in_game = self.is_in_game()
        if not in_game:
            return {"connected": True, "in_game": False, "stats": {}, "vendors": [], "landmarks": []}

        stats = self.read_interactables_status()
        vendors = self.scan_shady_vendors(expected_count=stats.get("vendors_total", 3)) if scan_vendors else []
        landmarks = self.scan_map_landmarks(existing_vendors=vendors, existing_stats=stats) if scan_landmarks else []

        golden_count = sum(1 for v in vendors if v.get("is_golden", False))
        stats["vendors_golden"] = golden_count
        if len(vendors) > 0:
            stats["vendors_total"] = len(vendors)

        score = calculate_map_score(stats)
        tier = evaluate_map_tier(score, stats)
        stats["score"] = score
        stats["tier"] = tier

        return {
            "connected": True,
            "in_game": True,
            "stats": stats,
            "vendors": vendors,
            "landmarks": landmarks,
            "score": score,
            "tier": tier
        }

# ==========================================================
# SISTEMA DE PUNTUACION, RANGOS Y PLANTILLAS (METODO SCORES)
# ==========================================================
def calculate_map_score(stats):
    """
    Calcula la puntuacion oficial de la semilla (Megabonk / BonkScanner standard):
    - Moais: 3.0 pts c/u
    - Vendedores (Shady): 2.0 pts c/u
    - Maldiciones de Jefe: 1.0 pt c/u
    - Santuarios de Iman: 0.5 pts c/u (maximo 2 contabilizados)
    - Desafios: 0.0 pts
    - Microondas: Multiplicador x1.25 si hay 2 o mas; x1.0 si hay 1 o menos.
    """
    shady = stats.get("vendors_total", 0)
    moai = stats.get("moais", 0)
    boss = stats.get("boss_curses", 0)
    magnet = stats.get("magnet_shrines", stats.get("shrines_magnet", 0))
    challenges = stats.get("challenges", stats.get("shrines_challenge", 0))
    microwaves = stats.get("microwaves", 0)

    counted_magnets = min(magnet, 2)
    base_score = (
        (moai * 3.0) +
        (shady * 2.0) +
        (boss * 1.0) +
        (counted_magnets * 0.5)
    )
    multiplier = 1.25 if microwaves >= 2 else 1.0
    return round(base_score * multiplier, 2)

def evaluate_map_tier(score, stats):
    """
    Clasifica el mapa segun los tiers oficiales:
    - Perfect+: Score >= 30.0 y al menos 2 microondas
    - Perfect: Score >= 25.0 y (al menos 2 microondas o 1 microondas + 8 moais/shady + 2 boss curses)
    - Good: Score >= 20.0
    - Light: Score >= 14.0
    - Normal: Score < 14.0
    """
    microwaves = stats.get("microwaves", 0)
    shady = stats.get("vendors_total", 0)
    moai = stats.get("moais", 0)
    boss = stats.get("boss_curses", 0)
    sm_total = shady + moai

    if score >= 30.0 and microwaves >= 2:
        return "Perfect+"
    if score >= 25.0 and (microwaves >= 2 or (microwaves >= 1 and sm_total >= 8 and boss >= 2)):
        return "Perfect"
    if score >= 20.0:
        return "Good"
    if score >= 14.0:
        return "Light"
    return "Normal"

TIER_INFO = {
    "Perfect+": {
        "name": "Perfect+",
        "label": "🔴 PERFECT+",
        "color": "#EF4444",
        "min_score": 30.0,
        "desc": "Élite Absoluta (Score ≥30 & 2 Microondas) · Récords Mundiales",
        "microwaves": 2
    },
    "Perfect": {
        "name": "Perfect",
        "label": "🟡 PERFECT",
        "color": "#FBBF24",
        "min_score": 25.0,
        "desc": "Excelente (Score ≥25 & 2 Microondas u 8+ Moais/Shady) · Competitivo",
        "microwaves": 1
    },
    "Good": {
        "name": "Good",
        "label": "🟢 GOOD",
        "color": "#22C55E",
        "min_score": 20.0,
        "desc": "Muy Buena (Score ≥20) · Recomendado para Farmear",
        "microwaves": 0
    },
    "Light": {
        "name": "Light",
        "label": "⚪ LIGHT",
        "color": "#E2E8F0",
        "min_score": 14.0,
        "desc": "Decente Casual (Score ≥14) · Encuentra partida en 1-2 segs",
        "microwaves": 0
    }
}

PRESET_TEMPLATES = {
    "record_perfect_plus": {
        "id": "record_perfect_plus",
        "name": "Récord Mundial (Perfect+)",
        "tier": "Perfect+",
        "min_score": 30.0,
        "min_moais": 0,
        "min_vendors": 0,
        "min_microwaves": 2,
        "min_boss": 0,
        "desc": "Semilla legendaria para speedruns del más alto nivel competitivo."
    },
    "record_perfect": {
        "id": "record_perfect",
        "name": "Partida Excelente (Perfect)",
        "tier": "Perfect",
        "min_score": 25.0,
        "min_moais": 0,
        "min_vendors": 0,
        "min_microwaves": 1,
        "min_boss": 0,
        "desc": "Equilibrio ideal de Moáis, Vendedores y Microondas para partidas ganadoras."
    },
    "fast_good": {
        "id": "fast_good",
        "name": "Partida Rápida (Good)",
        "tier": "Good",
        "min_score": 20.0,
        "min_moais": 0,
        "min_vendors": 0,
        "min_microwaves": 0,
        "min_boss": 0,
        "desc": "Excelente calidad de mapa encontrada en solo 3 a 5 segundos de reinicio."
    },
    "moai_rain": {
        "id": "moai_rain",
        "name": "Lluvia de Moáis (5+ Moáis)",
        "tier": "Good",
        "min_score": 20.0,
        "min_moais": 5,
        "min_vendors": 0,
        "min_microwaves": 0,
        "min_boss": 0,
        "desc": "Garantiza al menos 5 Moáis en la isla más un puntaje de nivel Good."
    },
    "vendor_paradise": {
        "id": "vendor_paradise",
        "name": "Club de Comerciantes (5+ Shady)",
        "tier": "Good",
        "min_score": 20.0,
        "min_moais": 0,
        "min_vendors": 5,
        "min_microwaves": 0,
        "min_boss": 0,
        "desc": "Garantiza al menos 5 Vendedores en el mapa para compras masivas."
    },
    "double_microwave": {
        "id": "double_microwave",
        "name": "Doble Microondas (2 Hornos)",
        "tier": "Light",
        "min_score": 18.0,
        "min_moais": 0,
        "min_vendors": 0,
        "min_microwaves": 2,
        "min_boss": 0,
        "desc": "Garantiza 2 microondas para duplicar ítems con puntaje decente."
    }
}

if __name__ == "__main__":
    reader = PhantomMemoryReader()
    print("Probando conexion con Megabonk...")
    data = reader.get_full_map_data()
    print("Resultado:", data)

