import ctypes
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from phantom_bot import PhantomBot, INPUT, KEYEVENTF_KEYUP, user32
from phantom_reader import (PhantomMemoryReader, RVA_RUN_TIMER_TYPEINFO,
                            RVA_PLAYER_STATS_TYPEINFO, MY_TIME_CURRENT_TIME_OFFSET)
from telemetry_logger import TelemetryLogger
from video_telemetry import parse_value, crop_bounds, sample_video


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.reader = type("Reader", (), {})()
        self.reader.read_full_player_stats = lambda: self.data
        self.logger = TelemetryLogger(self.reader, db_path=str(Path(self.directory.name) / "test.db"))
        self.data = {"valid": True, "run_time": 120, "level": 12, "kills": 450,
                     "stats": {"damage": 2.5}, "is_game_over": False}

    def tearDown(self):
        self.logger.stop()
        self.directory.cleanup()

    def rows(self, query):
        with closing(sqlite3.connect(self.logger.db_path)) as conn:
            return conn.execute(query).fetchall()

    def test_invalid_death_preserves_last_good_snapshot_and_does_not_start_another_run(self):
        self.logger._tick()
        self.data = {"valid": False, "run_time": 0, "is_game_over": True}
        self.logger._tick()
        self.logger._tick()
        self.assertEqual(self.rows("select duration_seconds, final_level, final_kills, outcome from runs"),
                         [(120, 12, 450, "death")])
        self.assertEqual(len(self.rows("select id from snapshots")), 1)

    def test_invalid_grace_is_independent_of_exports_and_never_implies_victory(self):
        with patch("telemetry_logger.time.monotonic", return_value=100):
            self.data["run_time"] = 1400
            self.logger._tick()
            self.data = {"valid": False}
            self.logger._tick()
        with patch("telemetry_logger.time.monotonic", return_value=105):
            self.logger.flush_buffer()
            self.logger._tick()
            self.assertIsNotNone(self.logger.current_run_id)
        with patch("telemetry_logger.time.monotonic", return_value=111):
            self.logger._tick()
        self.assertEqual(self.rows("select outcome from runs"), [("interrupted",)])

    def test_failed_flush_retries_without_losing_or_duplicating_rows(self):
        self.logger._tick()
        self.data["run_time"] = 125
        self.logger._tick()
        with patch.object(self.logger, "_get_connection", side_effect=sqlite3.OperationalError("busy")):
            with self.assertLogs("telemetry_logger", level="ERROR"):
                self.assertFalse(self.logger.flush_buffer())
        self.assertEqual(len(self.logger.snapshots_buffer), 1)
        self.assertTrue(self.logger.flush_buffer())
        self.assertTrue(self.logger.flush_buffer())
        self.assertEqual(len(self.rows("select id from snapshots")), 2)

    def test_discard_and_flush_are_serialized(self):
        self.logger._start_new_run({"run_time": 3}, "now")
        barrier = threading.Barrier(3)
        def flush():
            barrier.wait()
            self.logger.flush_buffer()
        def discard():
            barrier.wait()
            self.logger._discard_current_run()
        workers = [threading.Thread(target=flush), threading.Thread(target=discard)]
        for worker in workers:
            worker.start()
        barrier.wait()
        for worker in workers:
            worker.join(3)
            self.assertFalse(worker.is_alive())
        self.assertEqual(self.rows("select count(*) from snapshots"), [(0,)])
        self.assertEqual(self.rows("select count(*) from runs"), [(0,)])

    def test_stop_wakes_long_sampling_interval(self):
        self.logger.sample_interval = 60
        self.logger.start()
        started = time.monotonic()
        self.logger.stop()
        self.assertLess(time.monotonic() - started, 1)
        self.assertFalse(self.logger._worker_thread.is_alive())

    def test_stop_reports_failed_save_and_preserves_pending_rows(self):
        self.logger._tick()
        self.data["run_time"] = 125
        self.logger._tick()
        with patch.object(self.logger, "_get_connection", side_effect=sqlite3.OperationalError("busy")):
            with self.assertRaises(sqlite3.OperationalError):
                self.logger.stop()
        self.assertEqual(len(self.logger.snapshots_buffer), 1)


class KeyboardTests(unittest.TestCase):
    def test_escape_sends_exactly_one_down_and_one_up(self):
        events = []
        def send(count, pointer, size):
            events.append(ctypes.cast(pointer, ctypes.POINTER(INPUT)).contents.u.ki.dwFlags)
            return 1
        with patch.object(user32, "SendInput", side_effect=send), patch("phantom_bot.time.sleep"):
            self.assertTrue(PhantomBot().send_key(0x1B))
        self.assertEqual(len(events), 2)
        self.assertFalse(events[0] & KEYEVENTF_KEYUP)
        self.assertTrue(events[1] & KEYEVENTF_KEYUP)

    def test_key_is_released_after_sleep_fails(self):
        with patch.object(user32, "SendInput", return_value=1) as send:
            with patch("phantom_bot.time.sleep", side_effect=RuntimeError("interrupted")):
                with self.assertRaises(RuntimeError):
                    PhantomBot().send_key(0x52)
        self.assertEqual(send.call_count, 2)

    def test_reset_refuses_wrong_foreground_and_disabled_quick_reset(self):
        bot = PhantomBot()
        with patch.object(bot, "read_game_reset_settings", return_value={"enabled": True}):
            with patch.object(bot, "is_game_window_active", return_value=False):
                with patch.object(bot, "send_key") as send:
                    self.assertFalse(bot.trigger_restart(pid=123))
                    send.assert_not_called()
        with patch.object(bot, "read_game_reset_settings", return_value={"enabled": False}):
            with patch.object(bot, "send_key") as send:
                self.assertFalse(bot.trigger_restart())
                send.assert_not_called()


class PowerupReaderTests(unittest.TestCase):
    def test_live_process_check_does_not_enumerate_processes(self):
        from phantom_reader import kernel32
        reader = PhantomMemoryReader()
        reader.handle, reader.ga_base = 0x123456789, 0x200000000
        def alive(handle, pointer):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ulong)).contents.value = 259
            return True
        with patch.object(kernel32, "GetExitCodeProcess", side_effect=alive):
            with patch.object(kernel32, "CreateToolhelp32Snapshot") as snapshot:
                self.assertTrue(reader.find_process())
                snapshot.assert_not_called()

    def test_priority_is_restored_to_original_class(self):
        from phantom_reader import kernel32
        reader = PhantomMemoryReader()
        reader.handle = 1
        with patch.object(kernel32, "GetPriorityClass", return_value=0x8000):
            with patch.object(kernel32, "SetPriorityClass", return_value=True) as setter:
                self.assertTrue(reader.set_high_priority())
                self.assertTrue(reader.set_high_priority())
                self.assertTrue(reader.set_high_priority(False))
                self.assertEqual(setter.call_args.args, (1, 0x8000))

    def test_unresolved_offsets_do_not_scan_heap_in_normal_hud(self):
        reader = PhantomMemoryReader()
        reader.handle, reader.ga_base = 1, 0x100000
        with patch.object(reader, "read_ptr", return_value=None):
            with patch.object(reader, "resolve_class_ptr") as scan:
                self.assertFalse(reader.read_active_powerups()["valid"])
                scan.assert_not_called()

    def test_zero_current_time_is_valid_and_missing_current_time_is_not_substituted(self):
        reader = PhantomMemoryReader()
        reader.handle, reader.ga_base = 1, 0x100000
        base = 0x200000000
        time_class, time_static, stats_class, stats_static, root, owner, inventory, effects, dictionary, entries, effect = [base + i * 0x1000 for i in range(11)]
        pointers = {reader.ga_base + RVA_RUN_TIMER_TYPEINFO: time_class, time_class + 0xB8: time_static,
                    reader.ga_base + RVA_PLAYER_STATS_TYPEINFO: stats_class, stats_class + 0xB8: stats_static,
                    stats_static: root, root + 0x40: owner, owner + 0x28: inventory,
                    inventory + 0x38: effects, effects + 0x10: dictionary, dictionary + 0x18: entries}
        floats = {time_static + MY_TIME_CURRENT_TIME_OFFSET: 0.0, time_static + 0x1C: 999,
                  effect + 0x20: 10.0, effect + 0x24: 0.0}
        raw = struct.pack("<iiiiQ", 1, 0, 4, 0, effect)
        with patch.object(reader, "read_ptr", side_effect=lambda addr: pointers.get(addr)):
            with patch.object(reader, "read_float", side_effect=lambda addr: floats.get(addr)):
                with patch.object(reader, "read_int32", return_value=1), patch.object(reader, "read_bytes", return_value=raw):
                    result = reader.read_active_powerups()
                    self.assertTrue(result["valid"])
                    self.assertEqual(result["clock_remaining"], 10.0)
                    del floats[time_static + MY_TIME_CURRENT_TIME_OFFSET]
                    self.assertFalse(reader.read_active_powerups()["valid"])


class VideoTests(unittest.TestCase):
    def test_numeric_units_and_ambiguous_ocr(self):
        self.assertEqual(parse_value("03:07", "timer"), 187)
        self.assertIsNone(parse_value("03:79", "timer"))
        self.assertIsNone(parse_value("1O5", "integer"))
        self.assertEqual(parse_value("12,5%", "percent"), .125)
        self.assertEqual(parse_value("2.5x", "multiplier"), 2.5)
        self.assertIsNone(parse_value("", "float"))

    def test_roi_validation(self):
        self.assertEqual(crop_bounds([.1, .2, .3, .4], 100, 100), (10, 20, 40, 60))
        for roi in ([.9, 0, .2, .1], [0, 0, 0, .1], [float("nan"), 0, .1, .1]):
            with self.assertRaises(ValueError):
                crop_bounds(roi, 100, 100)

    def test_video_sampling_timestamps_and_unknown_game_time(self):
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV opcional no instalado")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            video = path / "test.avi"
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (80, 60))
            self.assertTrue(writer.isOpened())
            for index in range(30):
                writer.write(np.full((60, 80, 3), index * 5, dtype=np.uint8))
            writer.release()
            output = path / "sampled"
            self.assertEqual(sample_video(video, output, start=1, end=3), 2)
            observations = [json.loads(line) for line in (output / "observations.jsonl").read_text().splitlines()]
            self.assertEqual([row["video_time"] for row in observations], [1.0, 2.0])
            self.assertTrue(all(row["run_time"] is None and row["needs_review"] for row in observations))
            with self.assertRaises(ValueError):
                sample_video(video, output)


if __name__ == "__main__":
    unittest.main()
