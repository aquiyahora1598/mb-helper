"""An isolated GUI/resource check for the actual compiled executable."""

from contextlib import ExitStack
import json
from pathlib import Path
import sys
import traceback
from unittest.mock import patch

from powerup_overlay import POWERUP_COLORS
from runtime_paths import application_dir


def run_build_check(app_type, output_path):
    report = {"passed": False, "frozen": bool(getattr(sys, "frozen", False))}
    module = sys.modules[app_type.__module__]
    app = None
    try:
        with ExitStack() as stack:
            # Do not connect to the game, sample telemetry or listen for keys.
            for name in ("start_hotkey_listener", "start_background_monitor",
                         "start_bot_worker", "start_powerup_overlay_loop"):
                stack.enter_context(patch.object(app_type, name))
            stack.enter_context(patch.object(module, "TelemetryLogger"))
            stack.enter_context(patch.object(module, "log_event"))
            app = app_type()
            app.withdraw()
            errors = []
            app.report_callback_exception = lambda *args: errors.append(str(args[1]))
            if app.powerup_overlay is None:
                raise RuntimeError("The compiled HUD could not be initialized")
            app.powerup_overlay.window.withdraw()
            missing = sorted(item[1] for item in app._item_records.values() if item[1] not in app.item_icons)
            if missing:
                raise RuntimeError(f"Missing bundled icons: {missing}")
            for language in ("es", "en", "pt"):
                app.current_lang = language
                app.update_ui_language()
                for mode in (1, 2, 4):
                    app.switch_mode(mode)
                    app.update_idletasks()
                if any(char.isdigit() for btn in (app.btn_tab1, app.btn_tab2, app.btn_tab4)
                       for char in btn.cget("text")):
                    raise RuntimeError("Navigation still has category numbers")
            for preset in module.PRESET_TEMPLATES:
                app.apply_preset_template(preset)
            if hasattr(app, "tab3_frame"):
                raise RuntimeError("The removed Custom panel is still present")
            overlay = app.powerup_overlay
            single_width = overlay.width
            overlay.update_data({"valid": True, "powerups": [
                {"codename": "Clock", "remaining": 10}, {"codename": "Shield", "remaining": 12}]})
            if overlay.width != single_width * 2 + overlay.gap:
                raise RuntimeError("HUD did not expand for simultaneous timers")
            for kind, color in POWERUP_COLORS.items():
                overlay.update_data({"valid": True, "powerups": [{"codename": kind, "remaining": 10}]})
                if overlay.canvas.itemcget(overlay.text_id, "fill") != color:
                    raise RuntimeError(f"Incorrect HUD color: {kind}")
            received = []
            app.safe_ui_update(received.append, "delivered")
            app._drain_ui_queue()
            if errors or received != ["delivered"]:
                raise RuntimeError(f"GUI callbacks failed: {errors}")
            report.update(icons=len(app.item_icons), catalog_items=len(app._item_records),
                          languages=["es", "en", "pt"], modes=["items", "golden", "templates"],
                          templates=len(module.PRESET_TEMPLATES), hud_colors=len(POWERUP_COLORS),
                          data_directory=application_dir())
            app.on_exit()
            app = None
            report["passed"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if app is not None:
            app.on_exit()
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1
