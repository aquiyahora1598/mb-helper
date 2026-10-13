import tkinter as tk
import unittest
from unittest.mock import patch

from powerup_overlay import (
    PowerupOverlay, WS_EX_LAYERED, WS_EX_NOACTIVATE, user32,
    COLOR_BG, COLOR_IDLE, POWERUP_COLORS,
)


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.overlay = PowerupOverlay(self.root)
        self.data = {"valid": True, "powerups": [
            {"id": 4, "codename": "Clock", "remaining": 8.2},
            {"id": 2, "codename": "Shield", "remaining": 10},
        ]}

    def tearDown(self):
        self.root.destroy()

    def visible_items(self):
        return [item for item in self.overlay.canvas.find_all()
                if self.overlay.canvas.itemcget(item, "state") != "hidden"]

    def test_single_counter_fits_numbers_and_only_grows_horizontally(self):
        overlay = self.overlay
        single_width, height = overlay.width, overlay.height
        self.assertEqual(single_width, overlay.timer_font.measure("00:00") + 8)
        self.assertEqual(height, overlay.timer_font.metrics("linespace") + 4)
        for count in range(1, 6):
            data = {"valid": True, "powerups": [
                {"codename": kind, "remaining": 8.2 + index}
                for index, kind in enumerate(list(POWERUP_COLORS)[:count])
            ]}
            overlay.update_data(data)
            self.root.update_idletasks()
            self.assertEqual(overlay.width, single_width * count + 4 * (count - 1))
            self.assertEqual(overlay.height, height)
            self.assertEqual(len(self.visible_items()), count)
            for item in self.visible_items():
                self.assertEqual(overlay.canvas.type(item), "text")
                x1, y1, x2, y2 = overlay.canvas.bbox(item)
                self.assertGreaterEqual(x1, 0)
                self.assertGreaterEqual(y1, 0)
                self.assertLessEqual(x2, overlay.width)
                self.assertLessEqual(y2, overlay.height)
        overlay.update_data({"valid": True, "powerups": [{"id": 4, "remaining": 59.9}]})
        self.assertEqual(overlay.width, single_width)
        self.assertEqual(overlay.height, height)
        self.assertEqual(len(self.visible_items()), 1)

    def test_requested_colors_are_fixed_even_at_critical_time(self):
        for kind, color in POWERUP_COLORS.items():
            self.overlay.update_data({"valid": True, "powerups": [
                {"codename": kind, "remaining": 1.2, "is_critical": True, "is_warning": True}
            ]})
            self.assertEqual(self.overlay.canvas.itemcget(self.overlay.text_id, "fill"), color)
        self.assertEqual(self.overlay.canvas.cget("background"), COLOR_BG)
        self.assertEqual(len(self.overlay.canvas.find_all()), 5)

    def test_unchanged_data_and_idle_do_not_repaint_or_allocate(self):
        with patch.object(self.overlay.canvas, "itemconfig", wraps=self.overlay.canvas.itemconfig) as update:
            self.overlay.render_idle()
            update.assert_not_called()
            self.overlay.update_data(self.data)
            item_count = len(self.overlay.canvas.find_all())
            update.reset_mock()
            with patch.object(self.overlay.window, "geometry", wraps=self.overlay.window.geometry) as resize:
                self.overlay.update_data(self.data)
                update.assert_not_called()
                resize.assert_not_called()
            self.assertEqual(len(self.overlay.canvas.find_all()), item_count)
        self.overlay.update_data({"valid": False, "powerups": self.data["powerups"]})
        self.assertEqual(len(self.visible_items()), 1)
        self.assertEqual(self.overlay.canvas.itemcget(self.overlay.text_id, "text"), "00:00")
        self.assertEqual(self.overlay.canvas.itemcget(self.overlay.text_id, "fill"), COLOR_IDLE)

    def test_positions_do_not_swap_when_remaining_times_cross(self):
        self.overlay.update_data(self.data)
        self.assertEqual(self.overlay.canvas.itemcget(self.overlay._timer_ids[0], "fill"), POWERUP_COLORS["Clock"])
        self.data["powerups"][1]["remaining"] = .5
        self.overlay.update_data(self.data)
        self.assertEqual(self.overlay.canvas.itemcget(self.overlay._timer_ids[0], "fill"), POWERUP_COLORS["Clock"])
        self.assertEqual(self.overlay.canvas.itemcget(self.overlay._timer_ids[1], "fill"), POWERUP_COLORS["Shield"])

    def test_long_timer_fits_without_widening_single_slot(self):
        width = self.overlay.width
        self.overlay.update_data({"valid": True, "powerups": [{"id": 4, "remaining": 7200}]})
        self.root.update_idletasks()
        self.assertEqual(self.overlay.width, width)
        bounds = self.overlay.canvas.bbox(self.overlay.text_id)
        self.assertGreaterEqual(bounds[0], 0)
        self.assertLessEqual(bounds[2], width)

    def test_native_styles_are_not_layered_and_do_not_activate(self):
        styles = user32.GetWindowLongPtrW(self.overlay._get_hwnd(), -20)
        self.assertFalse(styles & WS_EX_LAYERED)
        self.assertTrue(styles & WS_EX_NOACTIVATE)


if __name__ == "__main__":
    unittest.main()
