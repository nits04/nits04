import json
import shutil
from datetime import datetime
from pathlib import Path

UNDO_LOG_FILENAME = ".organizer_undo.json"


def get_undo_log_path(target_dir: Path) -> Path:
    return target_dir / UNDO_LOG_FILENAME


def save_undo_log(target_dir: Path, operations: list[dict]) -> None:
    log_path = get_undo_log_path(target_dir)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "operations": operations,
    }

    history = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []

    history.append(entry)
    with open(log_path, "w") as f:
        json.dump(history, f, indent=2)


def load_last_operations(target_dir: Path) -> list[dict] | None:
    log_path = get_undo_log_path(target_dir)
    if not log_path.exists():
        return None
    try:
        with open(log_path) as f:
            history = json.load(f)
        if not history:
            return None
        return history[-1]["operations"]
    except (json.JSONDecodeError, OSError, KeyError):
        return None


def pop_last_entry(target_dir: Path) -> None:
    log_path = get_undo_log_path(target_dir)
    if not log_path.exists():
        return
    try:
        with open(log_path) as f:
            history = json.load(f)
        if history:
            history.pop()
        with open(log_path, "w") as f:
            json.dump(history, f, indent=2)
    except (json.JSONDecodeError, OSError):
        pass


def undo_operations(operations: list[dict]) -> tuple[int, list[str]]:
    """Reverse a list of move operations. Returns (success_count, errors)."""
    errors = []
    success = 0
    for op in reversed(operations):
        src = Path(op["dest"])
        dst = Path(op["src"])
        try:
            if not src.exists():
                errors.append(f"Missing: {src}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            success += 1
            # Remove empty parent directories left behind
            _remove_empty_parents(src.parent, stop_at=dst.parent.parent)
        except (OSError, shutil.Error) as e:
            errors.append(f"{src} -> {dst}: {e}")
    return success, errors


def _remove_empty_parents(directory: Path, stop_at: Path) -> None:
    try:
        while directory != stop_at and directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
            directory = directory.parent
    except OSError:
        pass
