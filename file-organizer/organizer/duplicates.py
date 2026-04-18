import hashlib
from pathlib import Path
from collections import defaultdict


def file_hash(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(paths: list[Path]) -> dict[str, list[Path]]:
    """Return a dict of hash -> [paths] for files that share content."""
    hash_map: dict[str, list[Path]] = defaultdict(list)
    for p in paths:
        if p.is_file():
            try:
                h = file_hash(p)
                hash_map[h].append(p)
            except (OSError, PermissionError):
                pass
    return {h: ps for h, ps in hash_map.items() if len(ps) > 1}


def is_duplicate_of(source: Path, dest: Path) -> bool:
    """Check if source has the same content as dest."""
    if not dest.exists():
        return False
    if source.stat().st_size != dest.stat().st_size:
        return False
    return file_hash(source) == file_hash(dest)
