import time
from pathlib import Path

from rich.console import Console
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from .core import organize

console = Console()


class _OrganizeHandler(FileSystemEventHandler):
    def __init__(self, target_dir: Path, by: str, config_path: Path | None):
        self.target_dir = target_dir
        self.by = by
        self.config_path = config_path
        self._pending: set[str] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        # Ignore already-organized subfolders
        if path.parent != self.target_dir:
            return
        if str(path) in self._pending:
            return
        self._pending.add(str(path))
        console.print(f"\n[cyan]Detected:[/cyan] {path.name}")
        # Small delay to ensure the file is fully written
        time.sleep(0.5)
        try:
            organize(self.target_dir, by=self.by, config_path=self.config_path)
        finally:
            self._pending.discard(str(path))


def watch(target_dir: Path, by: str = "type", config_path: Path | None = None) -> None:
    handler = _OrganizeHandler(target_dir, by, config_path)
    observer = Observer()
    observer.schedule(handler, str(target_dir), recursive=False)
    observer.start()

    console.print(f"[bold green]Watching[/bold green] [cyan]{target_dir}[/cyan] — press Ctrl+C to stop\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping watcher…[/yellow]")
    finally:
        observer.stop()
        observer.join()
