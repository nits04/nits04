import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

from .config import load_config
from .duplicates import find_duplicates, is_duplicate_of
from .rules import build_extension_map
from .undo import save_undo_log

console = Console()


# ──────────────────────────────────────────────
# Destination resolvers
# ──────────────────────────────────────────────

def _dest_by_type(file: Path, ext_map: dict, others_folder: str) -> str:
    return ext_map.get(file.suffix.lower(), others_folder)


def _dest_by_date(file: Path, date_format: str) -> str:
    mtime = datetime.fromtimestamp(file.stat().st_mtime)
    return mtime.strftime(date_format)


def _dest_by_extension(file: Path, others_folder: str) -> str:
    ext = file.suffix.lstrip(".").upper()
    return ext if ext else others_folder


# ──────────────────────────────────────────────
# Conflict resolution
# ──────────────────────────────────────────────

def _resolve_dest_path(src: Path, dest_dir: Path) -> Path:
    dest = dest_dir / src.name
    if not dest.exists():
        return dest
    # Append counter to avoid overwriting
    stem, suffix = src.stem, src.suffix
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{stem} ({counter}){suffix}"
        counter += 1
    return dest


# ──────────────────────────────────────────────
# Core organizer
# ──────────────────────────────────────────────

def organize(
    target_dir: Path,
    by: str = "type",
    dry_run: bool = False,
    config_path: Path | None = None,
    handle_duplicates: bool = False,
) -> list[dict]:
    cfg = load_config(config_path, target_dir)
    ext_map = build_extension_map(cfg["type_rules"])
    ignored = {f.lower() for f in cfg["ignored_files"]}
    others = cfg["others_folder"]
    date_fmt = cfg["date_format"]
    dup_action = cfg["duplicate_action"]

    files = [
        f for f in target_dir.iterdir()
        if f.is_file() and f.name.lower() not in ignored and not f.name.startswith(".")
    ]

    if not files:
        console.print("[yellow]No files to organize.[/yellow]")
        return []

    # Duplicate scan (whole folder)
    dup_hashes: set[str] = set()
    if handle_duplicates:
        from .duplicates import file_hash
        dup_groups = find_duplicates(files)
        if dup_groups:
            _print_duplicate_report(dup_groups, dry_run, dup_action, target_dir)
            # Collect hashes of duplicates to skip moving them later
            for paths in dup_groups.values():
                for p in paths[1:]:  # keep first, mark rest
                    dup_hashes.add(str(p))

    operations: list[dict] = []
    skipped: list[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        disable=dry_run,
    ) as progress:
        task = progress.add_task("Organizing files…", total=len(files))

        for file in files:
            progress.advance(task)

            if str(file) in dup_hashes and dup_action == "skip":
                skipped.append(file.name)
                continue

            if by == "type":
                subfolder = _dest_by_type(file, ext_map, others)
            elif by == "date":
                subfolder = _dest_by_date(file, date_fmt)
            else:  # extension
                subfolder = _dest_by_extension(file, others)

            dest_dir = target_dir / subfolder
            dest_path = _resolve_dest_path(file, dest_dir)

            operations.append({"src": str(file), "dest": str(dest_path), "folder": subfolder})

    if dry_run:
        _print_dry_run_table(operations, skipped)
        return operations

    _execute_moves(operations, skipped)
    if operations:
        save_undo_log(target_dir, operations)
    return operations


# ──────────────────────────────────────────────
# Execution
# ──────────────────────────────────────────────

def _execute_moves(operations: list[dict], skipped: list[str]) -> None:
    moved = 0
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Moving files…", total=len(operations))
        for op in operations:
            progress.advance(task)
            src, dest = Path(op["src"]), Path(op["dest"])
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                moved += 1
            except (OSError, shutil.Error) as e:
                errors.append(f"[red]✗[/red] {src.name}: {e}")

    console.print(f"\n[bold green]✓ Moved {moved} file(s)[/bold green]", end="")
    if skipped:
        console.print(f"  [dim]({len(skipped)} duplicate(s) skipped)[/dim]")
    else:
        console.print()
    for err in errors:
        console.print(err)


# ──────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────

def _print_dry_run_table(operations: list[dict], skipped: list[str]) -> None:
    console.print("\n[bold yellow]── Dry Run Preview ──[/bold yellow]\n")
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("File", style="white")
    table.add_column("→ Destination Folder", style="green")

    for op in operations:
        table.add_row(Path(op["src"]).name, op["folder"])

    console.print(table)
    console.print(f"\n[bold]{len(operations)} file(s)[/bold] would be moved.", end="")
    if skipped:
        console.print(f"  [dim]({len(skipped)} duplicate(s) skipped)[/dim]")
    else:
        console.print()
    console.print("[yellow]Run without --dry-run to apply changes.[/yellow]\n")


def _print_duplicate_report(
    dup_groups: dict, dry_run: bool, dup_action: str, target_dir: Path
) -> None:
    console.print("\n[bold red]── Duplicate Files Detected ──[/bold red]\n")
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold red")
    table.add_column("Group", style="dim")
    table.add_column("File")
    table.add_column("Size")

    for i, (_, paths) in enumerate(dup_groups.items(), 1):
        for j, p in enumerate(paths):
            size = f"{p.stat().st_size:,} B"
            label = f"#{i}" if j == 0 else ""
            style = "" if j == 0 else "red"
            table.add_row(label, p.name, size, style=style)
        table.add_row("", "", "")  # blank row between groups

    console.print(table)
    total_dups = sum(len(ps) - 1 for ps in dup_groups.values())
    console.print(f"[red]{total_dups} duplicate(s)[/red] found across {len(dup_groups)} group(s).\n")
