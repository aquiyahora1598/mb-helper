"""Validate on the Tk thread, then hand plain immutable settings to the worker."""

from types import MappingProxyType


SEARCH_MODES = (1, 2, 4)  # Stable internal IDs; templates are the third visible tab.

SETTING_NAMES = ("selected_mode", "score_submode", "target_tier", "selected_template",
                 "require_mode1_items", "require_golden_vendors", "target_golden_vendors")


def whole_number(value):
    text = str(value).strip()
    if not text or not text.isascii() or not text.isdecimal() or len(text) > 9:
        raise ValueError("invalid number")
    return int(text)


def capture_configuration(app):
    values = {name: getattr(app, name).get() for name in SETTING_NAMES}
    mode = values["selected_mode"]
    if mode not in SEARCH_MODES:
        raise ValueError(app.t("invalid_mode"))
    prices = {}
    needs_items = mode == 1 or (mode == 4 and values["require_mode1_items"])
    for item in app.selected_items:
        raw = app.item_max_prices[item[0]].get().strip()
        try:
            prices[item[0]] = whole_number(raw) if raw else 0
        except ValueError:
            if needs_items:
                raise ValueError(app.t("invalid_prices")) from None
            prices[item[0]] = 0
    values["selected_items"] = tuple(app.selected_items)
    values["item_max_prices"] = MappingProxyType(prices)
    return MappingProxyType(values)


def search_setting(app, name):
    config = getattr(app, "_search_config", None)
    if config is not None:
        return config[name]
    # Used by standalone diagnostic callers/tests before a search has started.
    value = getattr(app, name)
    return value.get() if name in SETTING_NAMES else value
