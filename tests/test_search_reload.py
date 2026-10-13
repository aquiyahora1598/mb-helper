from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from phantom_gui import MegabonkHelperApp


class ReloadTests(unittest.TestCase):
    def app(self, seed=12):
        reader = SimpleNamespace(
            pid=123, find_process=lambda: True,
            get_full_map_data=lambda **kwargs: {"stats": {"vendors_total": 1, "moais": 6}},
            get_map_generation_state=lambda: {"map_seed": seed, "has_loaded_map": True},
        )
        return SimpleNamespace(
            reader=reader, bot=SimpleNamespace(is_game_window_active=lambda **kwargs: True),
            is_running=True, is_focus_paused=False, selected_mode=SimpleNamespace(get=lambda: 0),
            waiting_for_scene_reload=True, last_reroll_time=1000, last_seed=11,
            generation_seen=False, saw_zero_interactables=False,
            current_map_detected_time=None, last_activity_time=1000, start_time=1000,
            attempt_count=2, safe_ui_update=Mock(), lbl_counter=SimpleNamespace(config=Mock()),
            t=lambda key, **kwargs: key, _check_reload_performance=Mock(),
        )

    def test_changed_seed_does_not_require_observing_intermediate_loading(self):
        app = self.app()
        with patch("phantom_gui.time.time", return_value=1001.5):
            MegabonkHelperApp.bot_step(app)
        self.assertFalse(app.waiting_for_scene_reload)
        self.assertEqual(app.last_seed, 12)
        app._check_reload_performance.assert_called_once_with(1.5)

    def test_unchanged_or_unknown_seed_still_waits_without_loading_evidence(self):
        for seed in (11, None):
            app = self.app(seed)
            with patch("phantom_gui.time.time", return_value=1001.5):
                MegabonkHelperApp.bot_step(app)
            self.assertTrue(app.waiting_for_scene_reload)
            app._check_reload_performance.assert_not_called()

    def test_changed_seed_still_respects_minimum_fade(self):
        app = self.app()
        with patch("phantom_gui.time.time", return_value=1000.8):
            MegabonkHelperApp.bot_step(app)
        self.assertTrue(app.waiting_for_scene_reload)
        app._check_reload_performance.assert_not_called()

    def test_failed_reset_does_not_wait_for_a_reload_that_was_not_sent(self):
        app = self.app()
        app.current_lang = "es"
        app._logged_item_timing = False
        app.lbl_status = SimpleNamespace(config=Mock())
        app.bot.trigger_restart = Mock(return_value=False)
        app.stop_search = Mock()
        with patch("phantom_gui.log_event"):
            MegabonkHelperApp.trigger_reroll_step(app)
        self.assertFalse(app.waiting_for_scene_reload)
        self.assertIsNone(app.last_reroll_time)
        app.stop_search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
