"""Small user settings kept in ~/.notescos/config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .store import NoteError

ALERT_LEVELS = ("quiet", "normal", "loud")  # how much the startup banner shows
DEFAULTS = {"alert_level": "normal"}


def load(home: Path) -> Dict:
    """Settings with defaults filled in. A missing or damaged file means defaults."""
    config = dict(DEFAULTS)
    try:
        saved = json.loads((home / "config.json").read_text())
        if isinstance(saved, dict):
            config.update(saved)
    except (OSError, ValueError):
        pass
    if config["alert_level"] not in ALERT_LEVELS:
        config["alert_level"] = DEFAULTS["alert_level"]
    return config


def set_alert_level(home: Path, level: str) -> Dict:
    level = level.lower()
    if level not in ALERT_LEVELS:
        raise NoteError(f"Alert level must be one of: {', '.join(ALERT_LEVELS)}.")
    config = load(home)
    config["alert_level"] = level
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    return config
