import json
import os
from copy import deepcopy


class Config:
    DEFAULTS = {
        "window": {
            "width": 800,
            "height": 600,
            "title": "Yaws3",
            "vsync": True,
        }
    }

    def __init__(self, settings=None, path="app/configuration.json"):
        self.path = path
        self.last_modified = None
        self.settings = {}
        if settings is not None:
            self._apply_settings(settings)
        else:
            self.reload()

    def _apply_settings(self, settings):
        merged = deepcopy(self.DEFAULTS)
        self._merge_dicts(merged, settings)
        self.settings = merged

    def _merge_dicts(self, base, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    def _load_from_disk(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def get(self, path, default=None):
        keys = path.split(".")
        value = self.settings
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
        return value

    def has_changed(self):
        if not os.path.exists(self.path):
            return False
        current_mtime = os.path.getmtime(self.path)
        if self.last_modified is None:
            return False
        return current_mtime > self.last_modified

    def reload(self):
        loaded = self._load_from_disk()
        self._apply_settings(loaded)
        try:
            self.last_modified = os.path.getmtime(self.path)
        except FileNotFoundError:
            self.last_modified = None

    def initialize(self):
        self.reload()

    def shutdown(self):
        pass
