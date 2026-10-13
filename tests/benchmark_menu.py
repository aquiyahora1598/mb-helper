"""Local Tk timings, isolated from the game, database, input and HUD workers."""

from contextlib import ExitStack
import json
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import phantom_gui as gui


def benchmark():
    with ExitStack() as stack:
        for name in ("start_hotkey_listener", "start_background_monitor", "start_bot_worker", "start_powerup_overlay_loop"):
            stack.enter_context(patch.object(gui.MegabonkHelperApp, name))
        for name in ("TelemetryLogger", "log_event"):
            stack.enter_context(patch.object(gui, name))
        stack.enter_context(patch.object(gui, "PowerupOverlay", return_value=None))
        start = time.perf_counter()
        app = gui.MegabonkHelperApp()
        app.update_idletasks()
        build_ms = (time.perf_counter() - start) * 1000
        try:
            unchanged, changed = [], []
            for _ in range(12):
                start = time.perf_counter()
                app.refresh_items_grid()
                app.update_idletasks()
                unchanged.append((time.perf_counter() - start) * 1000)
            identities = dict(app._item_buttons)
            for query in ["a", "anvil", "", "beer", "garra de aguila", "no existe"] * 5:
                start = time.perf_counter()
                app.search_var.set(query)
                app.refresh_items_grid()
                app.update_idletasks()
                changed.append((time.perf_counter() - start) * 1000)
            item = next(item for item in gui.OFFICIAL_ITEMS if item[1] == "Anvil")
            app.toggle_item_selection(*item[:5])
            var = app.item_max_prices[item[0]]
            for _ in range(15):
                app.update_selected_items_label()
            errors = []
            app.report_callback_exception = lambda *args: errors.append(str(args[1]))
            var.set("180")
            app.update_idletasks()
            return {"initial_build_ms": round(build_ms, 2),
                    "full_catalog_median_ms": round(statistics.median(unchanged), 2),
                    "full_catalog_max_ms": round(max(unchanged), 2),
                    "changed_filter_median_ms": round(statistics.median(changed), 2),
                    "changed_filter_max_ms": round(max(changed), 2),
                    "price_traces_after_16_renders": len(var.trace_info()),
                    "callback_errors_on_price_change": len(errors),
                    "catalog_widget_count": len(identities),
                    "catalog_widgets_reused": identities == app._item_buttons}
        finally:
            app.on_exit()


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
