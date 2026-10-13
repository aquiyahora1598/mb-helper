from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import phantom_gui
from phantom_reader import PhantomMemoryReader
from telemetry_logger import TelemetryLogger


class GuiSmokeTests(unittest.TestCase):
    def test_vendor_duplicates_use_cheapest_known_price_and_distinct_vendors(self):
        app = SimpleNamespace(current_lang="es", item_max_prices={1: "50"})
        selected = [(1, "A", "A", "A", "A")]
        check = phantom_gui.MegabonkHelperApp.check_vendors_have_items
        self.assertTrue(check(app, [{"item_ids": [1, 1], "item_prices": [20, 100]}], selected)[0])
        self.assertFalse(check(app, [{"item_ids": [1], "item_prices": []}], selected)[0])
        selected.append((2, "B", "B", "B", "B"))
        vendors = [{"item_ids": [1, 2], "item_prices": [20, 30]}, {"item_ids": [3], "item_prices": [10]}]
        self.assertFalse(check(app, vendors, selected)[0])
        vendors[1] = {"item_ids": [2], "item_prices": [30]}
        self.assertTrue(check(app, vendors, selected)[0])

    def test_diagnostic_closes_its_reader_when_game_is_missing(self):
        import audit_powerups
        from unittest.mock import Mock
        reader = Mock()
        reader.find_process.return_value = False
        with patch.object(audit_powerups, "PhantomMemoryReader", return_value=reader):
            audit_powerups.get_audit_report_text()
        reader.close.assert_called_once()

    def test_application_starts_drains_queue_and_closes_without_a_game(self):
        reader = PhantomMemoryReader()
        with tempfile.TemporaryDirectory() as folder:
            logger = TelemetryLogger(reader, db_path=str(Path(folder) / "test.db"))
            with patch.object(reader, "find_process", return_value=False), \
                    patch.object(phantom_gui, "PhantomMemoryReader", return_value=reader), \
                    patch.object(phantom_gui, "TelemetryLogger", return_value=logger), \
                    patch.object(phantom_gui, "log_event"):
                app = phantom_gui.MegabonkHelperApp()
                received = []
                app.safe_ui_update(received.append, "delivered")
                app.after(150, app.on_exit)
                app.mainloop()
                self.assertTrue(app.is_closing)
                self.assertEqual(received, ["delivered"])
                self.assertFalse(logger._worker_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
