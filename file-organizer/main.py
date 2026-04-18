#!/usr/bin/env python3
"""
organize — File Organizer CLI
Automatically organizes files by type, date, or extension.
"""
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich import box
import argparse

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="organize",
        description="Automatically organize files in a directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  organize ~/Downloads
  organize ~/Downloads --by date
  organize ~/Downloads --by extension
  organize ~/Downloads --dry-run
  organize ~/Downloads --duplicates
  organize ~/Downloads --undo
  organize ~/Downloads --watch
  organize ~/Downloads --init-config
""",
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Target directory to organize (default: current directory)",
    )
    parser.add_argument(
        "--by",
        choices=["type", "date", "extension"],
        default="type",
        help="Organization strategy (default: type)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving any files",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last organize operation in the target directory",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the directory and auto-organize new files in real time",
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Detect and report duplicate files before organizing",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Path to a custom .organizer.json config file",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Write a default .organizer.json into the target directory",
    )

    return parser


def cmd_undo(target_dir: Path) -> None:
    from organizer.undo import load_last_operations, undo_operations, pop_last_entry

    ops = load_last_operations(target_dir)
    if ops is None:
        console.print("[yellow]No undo history found for this directory.[/yellow]")
        return

    console.print(f"[bold]Undoing {len(ops)} move(s)…[/bold]")
    success, errors = undo_operations(ops)
    pop_last_entry(target_dir)

    console.print(f"[bold green]✓ Restored {success} file(s)[/bold green]")
    for err in errors:
        console.print(f"[red]✗[/red] {err}")


def cmd_init_config(target_dir: Path) -> None:
    from organizer.config import write_default_config, CONFIG_FILENAME

    dest = target_dir / CONFIG_FILENAME
    if dest.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {dest}")
        return
    write_default_config(dest)
    console.print(f"[bold green]✓ Created config:[/bold green] {dest}")


def cmd_watch(target_dir: Path, by: str, config_path: Path | None) -> None:
    from organizer.watcher import watch
    watch(target_dir, by=by, config_path=config_path)


def cmd_organize(
    target_dir: Path,
    by: str,
    dry_run: bool,
    duplicates: bool,
    config_path: Path | None,
) -> None:
    from organizer.core import organize

    mode_label = {"type": "file type", "date": "date", "extension": "extension"}[by]
    action = "[yellow]DRY RUN[/yellow] — " if dry_run else ""
    console.print(
        Panel.fit(
            f"{action}Organizing [cyan]{target_dir}[/cyan] by [bold]{mode_label}[/bold]",
            box=box.ROUNDED,
            border_style="blue",
        )
    )

    organize(
        target_dir,
        by=by,
        dry_run=dry_run,
        config_path=config_path,
        handle_duplicates=duplicates,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    target_dir = Path(args.directory).expanduser().resolve()

    if not target_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {target_dir}")
        sys.exit(1)
    if not target_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] Not a directory: {target_dir}")
        sys.exit(1)

    config_path = Path(args.config).expanduser().resolve() if args.config else None

    if args.init_config:
        cmd_init_config(target_dir)
    elif args.undo:
        cmd_undo(target_dir)
    elif args.watch:
        cmd_watch(target_dir, by=args.by, config_path=config_path)
    else:
        cmd_organize(
            target_dir,
            by=args.by,
            dry_run=args.dry_run,
            duplicates=args.duplicates,
            config_path=config_path,
        )


if __name__ == "__main__":
    main()
