# -*- coding: utf-8 -*-
"""
Megabonk Telemetry Logger - Registro Asíncrono de Partidas y Estadísticas Completas
Registra snapshots periódicos (cada 5s) y eventos clave con cero impacto en FPS.
Almacena en SQLite y exporta matrices tabulares listas para LightGBM y Optuna.
"""

import os
import time
import json
import sqlite3
import threading
import math
import logging
import uuid
from datetime import datetime
from runtime_paths import data_path

log = logging.getLogger(__name__)

class TelemetryLogger:
    def __init__(self, reader, is_searching_callback=None, db_path=None, sample_interval=5.0):
        self.reader = reader
        self.is_searching_callback = is_searching_callback
        self.db_path = db_path or data_path("telemetry.db")
        self.sample_interval = float(sample_interval)
        if not math.isfinite(self.sample_interval) or self.sample_interval <= 0:
            raise ValueError("sample_interval debe ser positivo y finito")
        
        self.is_running = False
        self._worker_thread = None
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._invalid_since = None
        
        # Estado de la partida actual
        self.current_run_id = None
        self.run_start_time = None
        self.last_run_time = 0.0
        self.last_stats = None
        self.snapshots_buffer = []
        self._last_flush_time = 0.0
        
        # Inicializar base de datos
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Tabla de partidas (Runs)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    character_id INTEGER DEFAULT 0,
                    final_level INTEGER DEFAULT 1,
                    final_kills INTEGER DEFAULT 0,
                    final_gold INTEGER DEFAULT 0,
                    final_chests INTEGER DEFAULT 0,
                    outcome TEXT DEFAULT 'active',
                    is_record INTEGER DEFAULT 0
                )
            """)
            
            # Tabla de instantáneas periódicas (Snapshots para ML)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    timestamp TEXT,
                    run_time REAL,
                    stage_time REAL,
                    level INTEGER,
                    gold INTEGER,
                    kills INTEGER,
                    chests INTEGER,
                    character_id INTEGER,
                    
                    -- 27 Estadísticas de Combate y Progresión
                    max_hp REAL,
                    hp_regen REAL,
                    shield REAL,
                    thorns REAL,
                    armor REAL,
                    evasion REAL,
                    lifesteal REAL,
                    damage REAL,
                    crit_chance REAL,
                    crit_damage REAL,
                    attack_speed REAL,
                    projectile_count REAL,
                    size REAL,
                    projectile_speed REAL,
                    duration REAL,
                    damage_to_elites REAL,
                    knockback REAL,
                    movement_speed REAL,
                    extra_jumps REAL,
                    luck REAL,
                    pickup_range REAL,
                    gold_gain REAL,
                    xp_gain REAL,
                    difficulty REAL,
                    elite_spawn REAL,
                    powerup_mult REAL,
                    powerup_drop_chance REAL,
                    
                    -- Inventario y Posición
                    items_json TEXT,
                    weapons_json TEXT,
                    tomes_json TEXT,
                    pos_x REAL,
                    pos_z REAL,
                    
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_run_id ON snapshots(run_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_run_time ON snapshots(run_time);")
            conn.commit()
            conn.close()

    def start(self):
        """Inicia el hilo de registro en segundo plano (daemon, 0% impacto en GUI)."""
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="TelemetryWorker")
            self._worker_thread.start()

    def stop(self):
        """Detiene el hilo y vuelca todos los datos pendientes a disco."""
        with self._lock:
            self.is_running = False
            self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=12.0)
            if self._worker_thread.is_alive():
                raise TimeoutError("El lector de telemetría no terminó a tiempo")
        if not self.flush_buffer(close_run=True):
            raise RuntimeError("No se pudo guardar la telemetría pendiente")

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                t0 = time.monotonic()
                self._tick()
                elapsed = time.monotonic() - t0
                sleep_time = max(0.2, self.sample_interval - elapsed)
                self._stop_event.wait(sleep_time)
            except Exception:
                log.exception("Error al registrar telemetría")
                self._stop_event.wait(1.0)

    def _tick(self):
        if not self.reader:
            return

        # 0. Si el bot está buscando activamente semillas (F5), pausar 100% la telemetría (0% impacto CPU/disco)
        if self.is_searching_callback and self.is_searching_callback():
            if self.current_run_id and self.last_run_time < 15.0:
                self._discard_current_run()
            return

        # 1. Leer estadísticas completas de la RAM (< 0.1ms)
        data = self.reader.read_full_player_stats()
        is_valid = data.get("valid", False)
        run_time = data.get("run_time", 0.0)
        is_game_over = data.get("is_game_over", False)

        with self._lock:
            now_iso = datetime.now().isoformat()
            now = time.monotonic()

            # Caso Muerte: Si el juego activó la pantalla de Game Over
            if is_game_over:
                if self.current_run_id is not None:
                    if is_valid and run_time >= self.last_run_time:
                        self.last_run_time = run_time
                        self.last_stats = data
                        self._record_snapshot(data, now_iso)
                    self._close_run(outcome="death", now_iso=now_iso)
                self._invalid_since = None
                return

            if is_valid:
                self._invalid_since = None
                # Caso A: Se detecta nueva partida iniciada
                if self.current_run_id is None:
                    self._start_new_run(data, now_iso)
                # Caso B: Partida existente se reinició con 'R' o volvió a 0
                elif run_time < (self.last_run_time - 3.0) and run_time <= 10.0:
                    self._close_run(outcome="restarted", now_iso=now_iso)
                    self._start_new_run(data, now_iso)
                # Caso C: Partida en curso
                else:
                    self._record_snapshot(data, now_iso)

                self.last_run_time = run_time
                self.last_stats = data
            else:
                # Si veníamos de una partida activa y ahora la lectura es inválida
                # (jugador salió al menú o cerró el juego)
                if self.current_run_id is not None:
                    if self._invalid_since is None:
                        self._invalid_since = now
                    elif now - self._invalid_since >= 10.0:
                        self._close_run(outcome="interrupted", now_iso=now_iso)

            # Volcar a SQLite periódicamente (cada 15s)
            if (now - self._last_flush_time) >= 15.0:
                self.flush_buffer(close_run=False)

    def _start_new_run(self, data, now_iso):
        run_id = f"run_{uuid.uuid4().hex}"
        self.current_run_id = run_id
        self.run_start_time = now_iso
        self.last_run_time = data.get("run_time", 0.0)
        self.last_stats = data

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO runs (
                run_id, start_time, duration_seconds, character_id,
                final_level, final_kills, final_gold, final_chests, outcome, is_record
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', 0)
        """, (
            run_id,
            now_iso,
            self.last_run_time,
            data.get("character_id", 0),
            data.get("level", 1),
            data.get("kills", 0),
            data.get("gold", 0),
            data.get("chests", 0)
        ))
        conn.commit()
        conn.close()

        self._record_snapshot(data, now_iso)

    def _record_snapshot(self, data, now_iso):
        stats = data.get("stats", {})
        p_pos = data.get("player_pos") or (None, None, None)

        row = (
            self.current_run_id,
            now_iso,
            data.get("run_time", 0.0),
            data.get("stage_time", 0.0),
            data.get("level", 1),
            data.get("gold", 0),
            data.get("kills", 0),
            data.get("chests", 0),
            data.get("character_id", 0),
            
            # 27 Stats
            stats.get("max_hp", 0.0),
            stats.get("hp_regen", 0.0),
            stats.get("shield", 0.0),
            stats.get("thorns", 0.0),
            stats.get("armor", 0.0),
            stats.get("evasion", 0.0),
            stats.get("lifesteal", 0.0),
            stats.get("damage", 1.0),
            stats.get("crit_chance", 0.0),
            stats.get("crit_damage", 2.0),
            stats.get("attack_speed", 0.0),
            stats.get("projectile_count", 0.0),
            stats.get("size", 1.0),
            stats.get("projectile_speed", 1.0),
            stats.get("duration", 1.0),
            stats.get("damage_to_elites", 1.0),
            stats.get("knockback", 1.0),
            stats.get("movement_speed", 1.0),
            stats.get("extra_jumps", 0.0),
            stats.get("luck", 0.0),
            stats.get("pickup_range", 0.0),
            stats.get("gold_gain", 1.0),
            stats.get("xp_gain", 1.0),
            stats.get("difficulty", 0.0),
            stats.get("elite_spawn", 1.0),
            stats.get("powerup_mult", 1.0),
            stats.get("powerup_drop_chance", 1.0),
            
            json.dumps(data.get("items", {})),
            json.dumps(data.get("weapons", [])),
            json.dumps(data.get("tomes", [])),
            p_pos[0] if p_pos else None,
            p_pos[2] if p_pos else None
        )
        self.snapshots_buffer.append(row)

    def _close_run(self, outcome="completed", now_iso=None):
        if not self.current_run_id:
            return

        duration = self.last_run_time
        # Si la partida duró menos de 15 segundos (semillas descartadas / reinicio rápido), descartar
        if duration < 15.0:
            self._discard_current_run()
            return

        now_iso = now_iso or datetime.now().isoformat()
        last = self.last_stats or {}

        level = last.get("level", 1)
        kills = last.get("kills", 0)
        gold = last.get("gold", 0)
        chests = last.get("chests", 0)

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE runs SET
                end_time = ?,
                duration_seconds = ?,
                final_level = ?,
                final_kills = ?,
                final_gold = ?,
                final_chests = ?,
                outcome = ?
            WHERE run_id = ?
        """, (
            now_iso,
            duration,
            level,
            kills,
            gold,
            chests,
            outcome,
            self.current_run_id
        ))
        conn.commit()
        conn.close()

        self.flush_buffer(close_run=False)
        self.current_run_id = None
        self.run_start_time = None
        self.last_run_time = 0.0
        self.last_stats = None

    def _discard_current_run(self):
        """Elimina de la base de datos una partida descartada por durar < 15s."""
        if not self.current_run_id:
            return
        with self._lock:
            run_id = self.current_run_id
            if not run_id:
                return
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("DELETE FROM snapshots WHERE run_id = ?;", (run_id,))
                    conn.execute("DELETE FROM runs WHERE run_id = ?;", (run_id,))
            finally:
                conn.close()
            self.snapshots_buffer = [r for r in self.snapshots_buffer if r[0] != run_id]
            self.current_run_id = None
            self.run_start_time = None
            self.last_run_time = 0.0
            self.last_stats = None
            self._invalid_since = None

    def flush_buffer(self, close_run=False):
        """Vuelca snapshots acumulados en RAM directamente a SQLite en una sola transacción."""
        # Serialize the transaction with discards and run closure, so a
        # concurrent export cannot reinsert snapshots from a discarded run.
        with self._lock:
            if close_run and self.current_run_id:
                self._close_run(outcome="stopped")

            if not self.snapshots_buffer:
                self._last_flush_time = time.monotonic()
                return True

            rows_to_insert = list(self.snapshots_buffer)
            conn = None
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.executemany("""
                INSERT INTO snapshots (
                    run_id, timestamp, run_time, stage_time, level, gold, kills, chests, character_id,
                    max_hp, hp_regen, shield, thorns, armor, evasion, lifesteal,
                    damage, crit_chance, crit_damage, attack_speed, projectile_count,
                    size, projectile_speed, duration, damage_to_elites, knockback,
                    movement_speed, extra_jumps, luck, pickup_range, gold_gain,
                    xp_gain, difficulty, elite_spawn, powerup_mult, powerup_drop_chance,
                    items_json, weapons_json, tomes_json, pos_x, pos_z
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, rows_to_insert)
                conn.commit()
                self.snapshots_buffer.clear()
                self._last_flush_time = time.monotonic()
                return True
            except Exception:
                # Keep the original buffer intact until the transaction commits.
                log.exception("No se pudo guardar la telemetría; se conserva en memoria")
                return False
            finally:
                if conn is not None:
                    conn.close()

    def mark_run_as_record(self, run_id=None, is_record=1):
        """Marca una partida específica o la última como Récord (etiqueta target para LightGBM)."""
        target_id = run_id or self.current_run_id
        conn = self._get_connection()
        cur = conn.cursor()
        if not target_id:
            cur.execute("SELECT run_id FROM runs ORDER BY start_time DESC LIMIT 1;")
            row = cur.fetchone()
            if row:
                target_id = row[0]
        if target_id:
            cur.execute("UPDATE runs SET is_record = ? WHERE run_id = ?;", (is_record, target_id))
            conn.commit()
        conn.close()
        return target_id

    def export_dataset_csv(self, output_path=None):
        """
        Exporta la matriz completa de snapshots enriquecida con el resultado final de cada partida.
        Genera el CSV tabular perfecto para entrenar directamente con LightGBM.
        """
        output_path = output_path or data_path("telemetry_dataset.csv")
        self.flush_buffer(close_run=False)

        conn = self._get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                s.run_id, s.timestamp, s.run_time, s.stage_time, s.level, s.gold, s.kills, s.chests, s.character_id,
                s.max_hp, s.hp_regen, s.shield, s.thorns, s.armor, s.evasion, s.lifesteal,
                s.damage, s.crit_chance, s.crit_damage, s.attack_speed, s.projectile_count,
                s.size, s.projectile_speed, s.duration, s.damage_to_elites, s.knockback,
                s.movement_speed, s.extra_jumps, s.luck, s.pickup_range, s.gold_gain,
                s.xp_gain, s.difficulty, s.elite_spawn, s.powerup_mult, s.powerup_drop_chance,
                s.items_json,
                r.duration_seconds AS final_run_duration,
                r.final_level,
                r.final_kills,
                r.is_record AS target_is_record
            FROM snapshots s
            JOIN runs r ON s.run_id = r.run_id
            WHERE r.duration_seconds > 10.0 AND r.outcome != 'active'
            ORDER BY s.run_id, s.run_time ASC
        """
        cur.execute(query)
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description]
        conn.close()

        if not rows:
            return 0

        import csv
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            writer.writerows(rows)

        return len(rows)

    def get_summary(self):
        """Retorna resumen estadístico de la base de datos de telemetría."""
        self.flush_buffer(close_run=False)
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*), SUM(duration_seconds), MAX(duration_seconds), MAX(final_kills), MAX(final_level) FROM runs;")
        r_stats = cur.fetchone()
        
        cur.execute("SELECT COUNT(*) FROM snapshots;")
        s_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM runs WHERE is_record = 1;")
        records_count = cur.fetchone()[0]
        
        conn.close()
        
        total_runs = r_stats[0] or 0
        total_time_sec = r_stats[1] or 0.0
        max_duration = r_stats[2] or 0.0
        max_kills = r_stats[3] or 0
        max_level = r_stats[4] or 0

        return {
            "total_runs": total_runs,
            "total_snapshots": s_count,
            "total_playtime_minutes": round(total_time_sec / 60.0, 1),
            "records_count": records_count,
            "max_duration_seconds": round(max_duration, 1),
            "max_kills": max_kills,
            "max_level": max_level,
            "is_active_run": self.current_run_id is not None,
            "current_run_id": self.current_run_id,
            "current_run_time": self.last_run_time
        }
