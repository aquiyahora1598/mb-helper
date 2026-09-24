"""
MB Helper - Herramienta de Auditoría y Diagnóstico de Powerups en Memoria
Inspecciona paso a paso toda la cadena de punteros en GameAssembly.dll y en el Heap.
"""

import io
import struct
import math
import sys
import os
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phantom_reader import (
    PhantomMemoryReader,
    RVA_MY_PLAYER_TYPEINFO,
    RVA_RUN_TIMER_TYPEINFO,
    RVA_PLAYER_STATS_TYPEINFO,
    OFFICIAL_POWERUPS
)

def run_powerup_audit():
    print("=" * 70)
    print("🔍 AUDITORÍA DE CONTADOR DE POWERUPS - MEGABONK MEMORY SCANNER")
    print("=" * 70)

    reader = PhantomMemoryReader()
    connected = reader.find_process()
    if not connected:
        print("\n❌ Megabonk NO está en ejecución.")
        print("   Por favor abre el juego, entra a una partida y vuelve a ejecutar este diagnóstico.")
        return {"status": "GAME_NOT_RUNNING"}

    print(f"\n[1] Conectado a Megabonk.exe (PID: {reader.pid})")
    print(f"    GameAssembly.dll Base: {hex(reader.ga_base)} | Tamaño: {hex(reader.ga_size)}")

    report = {"status": "OK", "checks": {}}

    # -------------------------------------------------------------
    # PASO 1: Comprobar MyTime (Cronómetro del Juego)
    # -------------------------------------------------------------
    print("\n[2] Comprobando MyTime (RVA 0x2f62398)...")
    time_class = reader.read_ptr(reader.ga_base + RVA_RUN_TIMER_TYPEINFO)
    print(f"    time_class: {hex(time_class) if time_class else 'None'}")
    cur_time = 0.0
    if time_class and time_class > 0xFFFFFFFF:
        time_static = reader.read_ptr(time_class + 0xB8)
        print(f"    time_static (+0xB8): {hex(time_static) if time_static else 'None'}")
        if time_static and time_static > 0xFFFFFFFF:
            raw_floats = reader.read_bytes(time_static, 48)
            if raw_floats:
                floats = [round(struct.unpack_from('<f', raw_floats, o)[0], 2) for o in range(0, 48, 4)]
                print(f"    MyTime static floats (0x00..0x2C): {floats}")
                cur_time = floats[1] if len(floats) > 1 else 0.0
                print(f"    -> my_time_seconds (+0x04): {cur_time}s | stage_timer (+0x1C): {floats[7] if len(floats) > 7 else 'N/A'}s")
                report["checks"]["my_time_floats"] = floats
    else:
        print("    ⚠️ time_class no es un puntero válido de 64 bits.")

    # -------------------------------------------------------------
    # PASO 2: Cadena Primaria (PlayerStats -> OwnerStats -> PlayerInventory)
    # -------------------------------------------------------------
    print("\n[3] Comprobando Cadena Primaria: PlayerStats (RVA 0x02F6A4B8)...")
    stats_class = reader.read_ptr(reader.ga_base + RVA_PLAYER_STATS_TYPEINFO)
    print(f"    stats_class: {hex(stats_class) if stats_class else 'None'}")
    owner_stats = None
    target_effects_inst = None
    if stats_class and stats_class > 0xFFFFFFFF:
        stats_static = reader.read_ptr(stats_class + 0xB8)
        print(f"    stats_static (+0xB8): {hex(stats_static) if stats_static else 'None'}")
        if stats_static and stats_static > 0xFFFFFFFF:
            root = reader.read_ptr(stats_static)
            print(f"    stats_root (+0x00): {hex(root) if root else 'None'}")
            if root and root > 0xFFFFFFFF:
                owner_stats = reader.read_ptr(root + 0x40)
                print(f"    owner_stats (+0x40): {hex(owner_stats) if owner_stats else 'None'}")
                if owner_stats and owner_stats > 0xFFFFFFFF:
                    player_inv = reader.read_ptr(owner_stats + 0x28)
                    print(f"    player_inventory (+0x28): {hex(player_inv) if player_inv else 'None'}")
                    if player_inv and player_inv > 0xFFFFFFFF:
                        target_effects_inst = reader.read_ptr(player_inv + 0x38)
                        print(f"    status_effects (+0x38): {hex(target_effects_inst) if target_effects_inst else 'None'} [✅ OK]")

    # -------------------------------------------------------------
    # PASO 3: Cadena Secundaria (MyPlayer RVA 0x2f620f8)
    # -------------------------------------------------------------
    print("\n[4] Comprobando Cadena Secundaria: MyPlayer (RVA 0x2f620f8)...")
    player_class = reader.read_ptr(reader.ga_base + RVA_MY_PLAYER_TYPEINFO)
    print(f"    player_class: {hex(player_class) if player_class else 'None'}")
    if not target_effects_inst and player_class and player_class > 0xFFFFFFFF:
        player_static = reader.read_ptr(player_class + 0xB8)
        if player_static and player_static > 0xFFFFFFFF:
            player_inst = reader.read_ptr(player_static + 0x08)
            print(f"    player_inst (+0x08): {hex(player_inst) if player_inst else 'None'}")
            if player_inst and player_inst > 0xFFFFFFFF:
                player_comp = reader.read_ptr(player_inst + 0x90)
                if player_comp and player_comp > 0xFFFFFFFF:
                    sec_eff = reader.read_ptr(player_comp + 0x38)
                    if sec_eff and sec_eff > 0xFFFFFFFF:
                        target_effects_inst = sec_eff
                        print(f"    status_effects secundario (+0x38): {hex(target_effects_inst)}")

    # -------------------------------------------------------------
    # PASO 4: Cadena Terciaria (Heap Sweep de PlayerStatusEffects)
    # -------------------------------------------------------------
    print("\n[5] Buscando clases e instancias de Status Effects en Heap...")
    pse_class = reader.resolve_class_ptr("PlayerStatusEffects")
    print(f"    Il2CppClass* PlayerStatusEffects: {hex(pse_class) if pse_class else 'No encontrado'}")

    heap_regions = reader.refresh_cached_heap_regions()
    alive_pse_instances = []

    if pse_class:
        for base_addr, size in heap_regions:
            scan_len = min(size, 0x400000)
            data = reader.read_bytes(base_addr, scan_len)
            if not data or len(data) < 16:
                continue
            num_q = len(data) // 8
            qwords = struct.unpack(f'<{num_q}Q', data[:num_q*8])
            for i, val in enumerate(qwords):
                if val == pse_class:
                    alive_pse_instances.append(base_addr + (i * 8))

    print(f"    Instancias vivas PlayerStatusEffects en Heap: {len(alive_pse_instances)} ({[hex(x) for x in alive_pse_instances[:3]]})")
    if not target_effects_inst and alive_pse_instances:
        target_effects_inst = alive_pse_instances[0]
        print(f"    Usando instancia viva de Heap: {hex(target_effects_inst)}")

    # -------------------------------------------------------------
    # PASO 5: Inspeccionar Diccionario de Status Effects
    # -------------------------------------------------------------
    found_powerups = []
    if target_effects_inst and target_effects_inst > 0xFFFFFFFF:
        print(f"\n[6] Analizando Diccionario en PlayerStatusEffects ({hex(target_effects_inst)})...")
        dict_ptr = reader.read_ptr(target_effects_inst + 0x10)
        print(f"    PlayerStatusEffects +0x10 (Dictionary): {hex(dict_ptr) if dict_ptr else 'None'}")
        if dict_ptr and dict_ptr > 0xFFFFFFFF:
            count = reader.read_int32(dict_ptr + 0x20)
            entries = reader.read_ptr(dict_ptr + 0x18)
            capacity = reader.read_int32(entries + 0x18) if (entries and entries > 0xFFFFFFFF) else 0
            print(f"    Dictionary count (+0x20): {count} | capacity (+0x18): {capacity} | entries: {hex(entries) if entries else 'None'}")
            
            num_slots = capacity if (capacity and 0 < capacity <= 64) else (count if (count and 0 < count <= 64) else 0)
            if num_slots > 0 and entries and entries > 0xFFFFFFFF:
                raw_entries = reader.read_bytes(entries + 0x20, num_slots * 24)
                if raw_entries:
                    for i in range(num_slots):
                        offset = i * 24
                        h = struct.unpack_from('<i', raw_entries, offset)[0]
                        if h < 0:
                            continue
                        sid = struct.unpack_from('<i', raw_entries, offset + 8)[0]
                        eptr = struct.unpack_from('<Q', raw_entries, offset + 16)[0]
                        info = OFFICIAL_POWERUPS.get(sid, {"name": f"Efecto #{sid}", "icon": "⚡"})
                        print(f"      [Slot #{i}] Hash: {h} | ID: {sid} ({info['name']}) | EffectPtr: {hex(eptr)}")
                        if eptr and eptr > 0x10000:
                            end_t = reader.read_float(eptr + 0x20)
                            start_t = reader.read_float(eptr + 0x24)
                            rem = round(end_t - cur_time, 2)
                            is_active = (rem > 0)
                            print(f"        -> start_time: {start_t} | end_time: {end_t} | restante: {rem}s | Activo: {'SI 🟢' if is_active else 'NO ⚪'}")
                            if is_active:
                                found_powerups.append({"id": sid, "name": info["name"], "rem": rem})
    else:
        print("\n[6] ❌ No se pudo resolver la instancia de PlayerStatusEffects.")

    # -------------------------------------------------------------
    # PASO 6: Probar directamente read_active_powerups()
    # -------------------------------------------------------------
    print("\n[7] Probando reader.read_active_powerups()...")
    t0 = time.perf_counter()
    active_res = reader.read_active_powerups()
    cost_ms = (time.perf_counter() - t0) * 1000.0
    print(f"    Resultado: {active_res}")
    print(f"    Tiempo de lectura en memoria: {cost_ms:.4f} ms")

    print("\n" + "=" * 70)
    if active_res.get("powerups"):
        print("✅ DIAGNÓSTICO EXITOSO: Powerups activos detectados correctamente.")
    elif target_effects_inst:
        print("ℹ️ CONEXIÓN Y CADENA VÁLIDAS: El juego está conectado y sincronizado, sin powerups activos actualmente.")
    else:
        print("⚠️ ATENCIÓN: No se detectó la instancia del jugador en la partida actual.")
    print("=" * 70)

    return {
        "connected": True,
        "cur_time": cur_time,
        "target_effects_inst": hex(target_effects_inst) if target_effects_inst else None,
        "powerups_count": len(found_powerups),
        "active_powerups_result": active_res
    }

def get_audit_report_text():
    """Captura toda la salida de la auditoría en un string para mostrar en la interfaz gráfica"""
    buf = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = buf
        run_powerup_audit()
    finally:
        sys.stdout = old_stdout
    return buf.getvalue()

if __name__ == "__main__":
    run_powerup_audit()
