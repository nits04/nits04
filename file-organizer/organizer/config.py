import json
import os
from pathlib import Path
from .rules import DEFAULT_TYPE_RULES, IGNORED_FILES

DEFAULT_CONFIG = {
    "type_rules": DEFAULT_TYPE_RULES,
    "ignored_files": list(IGNORED_FILES),
    "duplicate_action": "report",  # report | move | delete
    "others_folder": "Others",
    "date_format": "%Y/%m",  # used when organizing by date
}

CONFIG_FILENAME = ".organizer.json"


def find_config(start_path: Path) -> Path | None:
    for parent in [start_path, *start_path.parents]:
        candidate = parent / CONFIG_FILENAME
        if candidate.exists():
            return candidate
    home_config = Path.home() / CONFIG_FILENAME
    if home_config.exists():
        return home_config
    return None


def load_config(config_path: Path | None = None, target_dir: Path | None = None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["type_rules"] = {k: list(v) for k, v in DEFAULT_TYPE_RULES.items()}
    cfg["ignored_files"] = list(IGNORED_FILES)

    resolved = config_path or (find_config(target_dir) if target_dir else None)
    if resolved and resolved.exists():
        with open(resolved) as f:
            user_cfg = json.load(f)
        if "type_rules" in user_cfg:
            cfg["type_rules"].update(user_cfg["type_rules"])
        for key in ("ignored_files", "duplicate_action", "others_folder", "date_format"):
            if key in user_cfg:
                cfg[key] = user_cfg[key]

    return cfg


def write_default_config(path: Path) -> None:
    with open(path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
