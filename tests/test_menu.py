from contextlib import ExitStack
import threading
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

import phantom_gui as gui
from phantom_reader import OFFICIAL_ITEMS, PRESET_TEMPLATES, TIER_INFO
from search_config import capture_configuration


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        for name in ("start_hotkey_listener", "start_background_monitor", "start_bot_worker", "start_powerup_overlay_loop"):
            self.stack.enter_context(patch.object(gui.MegabonkHelperApp, name))
        for name in ("TelemetryLogger", "log_event"):
            self.stack.enter_context(patch.object(gui, name))
        self.stack.enter_context(patch.object(gui.kernel32, "Beep"))
        self.stack.enter_context(patch.object(gui, "PowerupOverlay", return_value=None))
        self.app = gui.MegabonkHelperApp()
        self.errors = []
        self.app.report_callback_exception = lambda *args: self.errors.append(str(args[1]))
        self.app.update_idletasks()
        self.anvil = next(item for item in OFFICIAL_ITEMS if item[1] == "Anvil")

    def tearDown(self):
        self.app.on_exit()
        self.stack.close()
        self.assertEqual(self.errors, [])

    def select(self, item):
        self.app.toggle_item_selection(*item[:5])

    def test_prices_keep_one_live_callback_and_survive_languages_and_other_selections(self):
        app = self.app
        self.select(self.anvil)
        var = app.item_max_prices[self.anvil[0]]
        card = app._selected_cards[self.anvil[0]]["frame"]
        for lang in ("en", "pt", "es") * 3:
            app.current_lang = lang
            app.update_ui_language()
        self.assertEqual(len(var.trace_info()), 1)
        self.assertIs(app._selected_cards[self.anvil[0]]["frame"], card)
        var.set("180")
        self.select(next(item for item in OFFICIAL_ITEMS if item[1] == "Beer"))
        self.assertEqual(var.get(), "180")
        app.clear_selected_items()
        self.assertEqual(len(var.trace_info()), 0)
        var.set("200")  # Removed controls must never receive callbacks.

    def test_catalog_debounces_and_reuses_widgets_for_accent_insensitive_search(self):
        app = self.app
        widgets = dict(app._item_buttons)
        app.search_var.set("a")
        old_timer = app._catalog_after
        app.search_var.set("garra de aguila")
        self.assertNotEqual(old_timer, app._catalog_after)
        self.assertNotIn(old_timer, app.tk.splitlist(app.tk.call("after", "info")))
        app.refresh_items_grid()
        found = [tid for tid, btn in widgets.items() if btn.winfo_manager()]
        self.assertEqual([app._item_records[tid][1] for tid in found], ["EagleClaw"])
        app.search_var.set("no existe este item")
        app.refresh_items_grid()
        self.assertTrue(app._empty_catalog.winfo_manager())
        self.assertEqual(widgets, app._item_buttons)
        app.search_var.set("")
        app._select_rarity("LEGENDARY")
        app.refresh_items_grid()
        self.assertTrue(all(app._item_records[tid][5] == "LEGENDARY"
                            for tid, btn in widgets.items() if btn.winfo_manager()))

    def test_fourth_item_is_rejected_and_every_preset_can_be_selected(self):
        for item in OFFICIAL_ITEMS[1:4]:
            self.select(item)
        with patch.object(gui.messagebox, "showinfo") as alert:
            self.select(OFFICIAL_ITEMS[4])
            alert.assert_called_once()
        self.assertEqual(len(self.app.selected_items), 3)
        for pid, template in PRESET_TEMPLATES.items():
            self.app.apply_preset_template(pid)
            self.assertEqual(self.app.selected_template.get(), pid)
            self.assertEqual(self.app.target_tier.get(), template["tier"])
            self.assertEqual(self.app.score_submode.get(), "template")
        self.app.target_tier.set("Good")
        self.app.on_select_tier()
        self.assertEqual(self.app.score_submode.get(), "tier")

    def test_invalid_prices_and_removed_mode_cannot_start_a_search(self):
        app = self.app
        self.select(self.anvil)
        for value in ("-5", "hello", "12.5", "²", "9" * 20):
            app.item_max_prices[self.anvil[0]].set(value)
            self.assertFalse(app.start_search(), value)
            self.assertFalse(app.is_running)
        app.selected_mode.set(3)
        self.assertFalse(app.start_search())
        self.assertFalse(app.is_running)

    def test_worker_evaluations_use_captured_settings_without_touching_tk(self):
        app = self.app
        self.select(self.anvil)
        app.item_max_prices[self.anvil[0]].set("180")
        app.selected_mode.set(4)
        app.require_mode1_items.set(True)
        app.apply_preset_template("double_microwave_white")
        app._search_config = capture_configuration(app)
        app.item_max_prices[self.anvil[0]].set("1")
        app.selected_items.clear()
        app.selected_template.set("graveyard_bald_heads")
        output = []
        def evaluate():
            try:
                output.append(app.check_vendors_have_items(
                    [{"item_ids": [self.anvil[0]], "item_prices": [150]}], app._search_config["selected_items"])[0])
                output.append(app.evaluate_template_match({"score": 20, "tier": "Good", "microwaves": 2, "microwaves_white": 2}))
            except Exception as exc:
                output.append(str(exc))
        worker = threading.Thread(target=evaluate)
        worker.start()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(output, [True, True])
        with self.assertRaises(TypeError):
            app._search_config["item_max_prices"][self.anvil[0]] = 999

    def test_every_template_accepts_its_requirements_and_rejects_missing_requirements(self):
        app = self.app
        for pid, template in PRESET_TEMPLATES.items():
            app.apply_preset_template(pid)
            stats = {"tier": template["tier"], "score": template["min_score"],
                     "moais": template.get("min_moais", 0), "vendors_total": template.get("min_vendors", 0),
                     "microwaves": template.get("min_microwaves", 0), "microwaves_white": template.get("min_white_microwaves", 0),
                     "boss_curses": template.get("min_boss", 0), "bald_heads": template.get("min_bald_heads", 0)}
            self.assertTrue(app.evaluate_template_match(dict(stats)), pid)
            for field in ("score", "moais", "vendors_total", "microwaves", "microwaves_white", "boss_curses", "bald_heads"):
                if stats[field] > 0:
                    missing = dict(stats)
                    missing[field] -= 1
                    self.assertFalse(app.evaluate_template_match(missing), (pid, field))
        app.on_select_tier()
        for tier in ("Light", "Good", "Perfect", "Perfect+"):
            app.target_tier.set(tier)
            self.assertTrue(app.evaluate_template_match({"tier": tier}))
        app.target_tier.set("Perfect")
        self.assertFalse(app.evaluate_template_match({"tier": "Good"}))

    def test_layout_keeps_controls_reachable_at_small_and_large_sizes(self):
        app = self.app
        for item in OFFICIAL_ITEMS[1:4]:
            self.select(item)
        for size in ("760x540", "1160x820"):
            app.geometry(size)
            for mode in (1, 2, 4):
                app.switch_mode(mode)
                app.update()
                self.assertGreater(app.btn_action.winfo_height(), 20)
                self.assertLessEqual(app.btn_action.winfo_rooty()+app.btn_action.winfo_height(),
                                     app.winfo_rooty()+app.winfo_height())
                self.assertGreater(getattr(app, f"tab{mode}_frame").winfo_height(), 40)
        app.selected_mode.set(1)
        app._search_config = capture_configuration(app)
        app.set_menu_editable(False)
        self.assertEqual(str(app.btn_tab1.cget("state")), "disabled")
        app.set_menu_editable(True)
        self.assertEqual(str(app.search_entry.cget("state")), "normal")

    def test_all_modes_start_with_valid_settings_and_unlock_on_stop(self):
        app = self.app
        self.assertNotIn("btn_tab3", vars(app))
        self.assertNotIn("tab3_frame", vars(app))
        self.assertEqual(len(app.btn_tab1.master.winfo_children()), 3)
        app.switch_mode(3)
        self.assertEqual(app.selected_mode.get(), 1)
        self.select(self.anvil)
        app.require_mode1_items.set(True)
        app.require_golden_vendors.set(True)
        for mode in (1, 2, 4):
            app.switch_mode(mode)
            self.assertTrue(app.start_search(), mode)
            self.assertEqual(app._search_config["selected_mode"], mode)
            for removed in ("active_filters", "max_attempts", "max_search_seconds"):
                self.assertNotIn(removed, app._search_config)
            self.assertTrue(app.is_running)
            self.assertEqual(str(app.search_entry.cget("state")), "disabled")
            app.switch_mode(1 if mode != 1 else 2)
            self.assertEqual(app.selected_mode.get(), mode)
            app.stop_search()
            app._drain_ui_queue()
            self.assertEqual(str(app.search_entry.cget("state")), "normal")

    def test_manual_reset_focuses_the_game_and_runs_off_the_tk_thread(self):
        app = self.app
        app.reader.find_process = Mock(return_value=True)
        app.reader.pid = 123
        entered, release = threading.Event(), threading.Event()
        calls = []
        def focus(**kwargs):
            calls.append(("focus", kwargs, threading.current_thread()))
            entered.set()
            release.wait(2)
            return True
        app.bot.focus_game = focus
        app.bot.trigger_restart = Mock(return_value=True)
        app.test_quick_reset()
        self.assertTrue(entered.wait(1))
        self.assertEqual(str(app.btn_test_reset.cget("state")), "disabled")
        self.assertFalse(app.start_search())
        self.assertIsNot(calls[0][2], threading.current_thread())
        self.assertEqual(calls[0][1], {"pid": 123})
        release.set()
        calls[0][2].join(2)
        self.assertFalse(calls[0][2].is_alive())
        app.bot.trigger_restart.assert_called_once_with(pid=123)
        app._drain_ui_queue()
        self.assertEqual(str(app.btn_test_reset.cget("state")), "normal")


if __name__ == "__main__":
    unittest.main()
