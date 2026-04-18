"""Tests for file-organizer core logic."""
import json
import shutil
import tempfile
from pathlib import Path

import pytest

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def make_dir_with_files(tmp_path: Path, filenames: list[str]) -> Path:
    for name in filenames:
        (tmp_path / name).write_text(f"content of {name}")
    return tmp_path


# ──────────────────────────────────────────────
# rules
# ──────────────────────────────────────────────

class TestBuildExtensionMap:
    def test_basic_mapping(self):
        from organizer.rules import build_extension_map
        rules = {"Images": [".jpg", ".PNG"], "Docs": [".pdf"]}
        m = build_extension_map(rules)
        assert m[".jpg"] == "Images"
        assert m[".png"] == "Images"   # normalised to lower
        assert m[".pdf"] == "Docs"

    def test_last_rule_wins_on_conflict(self):
        from organizer.rules import build_extension_map
        rules = {"A": [".x"], "B": [".x"]}
        m = build_extension_map(rules)
        assert m[".x"] == "B"


# ──────────────────────────────────────────────
# config
# ──────────────────────────────────────────────

class TestLoadConfig:
    def test_defaults_returned_when_no_config_file(self, tmp_path):
        from organizer.config import load_config
        cfg = load_config(target_dir=tmp_path)
        assert "type_rules" in cfg
        assert "Images" in cfg["type_rules"]

    def test_user_config_overrides_defaults(self, tmp_path):
        from organizer.config import load_config, CONFIG_FILENAME
        user_cfg = {"others_folder": "Misc", "type_rules": {"Custom": [".xyz"]}}
        (tmp_path / CONFIG_FILENAME).write_text(json.dumps(user_cfg))
        cfg = load_config(target_dir=tmp_path)
        assert cfg["others_folder"] == "Misc"
        assert "Custom" in cfg["type_rules"]
        assert "Images" in cfg["type_rules"]   # defaults still present

    def test_init_config_writes_file(self, tmp_path):
        from organizer.config import write_default_config, CONFIG_FILENAME
        dest = tmp_path / CONFIG_FILENAME
        write_default_config(dest)
        assert dest.exists()
        data = json.loads(dest.read_text())
        assert "type_rules" in data


# ──────────────────────────────────────────────
# duplicates
# ──────────────────────────────────────────────

class TestDuplicates:
    def test_identical_files_detected(self, tmp_path):
        from organizer.duplicates import find_duplicates
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"hello world")
        b.write_bytes(b"hello world")
        groups = find_duplicates([a, b])
        assert len(groups) == 1
        found_paths = list(groups.values())[0]
        assert set(found_paths) == {a, b}

    def test_unique_files_not_reported(self, tmp_path):
        from organizer.duplicates import find_duplicates
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"hello")
        b.write_bytes(b"world")
        groups = find_duplicates([a, b])
        assert groups == {}

    def test_is_duplicate_of_same_content(self, tmp_path):
        from organizer.duplicates import is_duplicate_of
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"\x00" * 100)
        b.write_bytes(b"\x00" * 100)
        assert is_duplicate_of(a, b) is True

    def test_is_duplicate_of_different_content(self, tmp_path):
        from organizer.duplicates import is_duplicate_of
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"\x00" * 100)
        b.write_bytes(b"\xFF" * 100)
        assert is_duplicate_of(a, b) is False

    def test_is_duplicate_of_missing_dest(self, tmp_path):
        from organizer.duplicates import is_duplicate_of
        a = tmp_path / "a.bin"
        a.write_bytes(b"data")
        assert is_duplicate_of(a, tmp_path / "nonexistent.bin") is False


# ──────────────────────────────────────────────
# undo
# ──────────────────────────────────────────────

class TestUndo:
    def test_save_and_load(self, tmp_path):
        from organizer.undo import save_undo_log, load_last_operations
        ops = [{"src": "/a/x.txt", "dest": "/a/Docs/x.txt", "folder": "Docs"}]
        save_undo_log(tmp_path, ops)
        loaded = load_last_operations(tmp_path)
        assert loaded == ops

    def test_multiple_saves_stack(self, tmp_path):
        from organizer.undo import save_undo_log, load_last_operations
        save_undo_log(tmp_path, [{"src": "a", "dest": "b", "folder": "X"}])
        save_undo_log(tmp_path, [{"src": "c", "dest": "d", "folder": "Y"}])
        loaded = load_last_operations(tmp_path)
        assert loaded[0]["src"] == "c"

    def test_pop_removes_last(self, tmp_path):
        from organizer.undo import save_undo_log, load_last_operations, pop_last_entry
        save_undo_log(tmp_path, [{"src": "a", "dest": "b", "folder": "X"}])
        save_undo_log(tmp_path, [{"src": "c", "dest": "d", "folder": "Y"}])
        pop_last_entry(tmp_path)
        loaded = load_last_operations(tmp_path)
        assert loaded[0]["src"] == "a"

    def test_undo_operations_restores_files(self, tmp_path):
        from organizer.undo import undo_operations
        src_original = tmp_path / "photo.jpg"
        dest_moved = tmp_path / "Images" / "photo.jpg"
        dest_moved.parent.mkdir()
        dest_moved.write_bytes(b"img data")

        ops = [{"src": str(src_original), "dest": str(dest_moved), "folder": "Images"}]
        success, errors = undo_operations(ops)
        assert success == 1
        assert errors == []
        assert src_original.exists()
        assert not dest_moved.exists()

    def test_undo_missing_file_reports_error(self, tmp_path):
        from organizer.undo import undo_operations
        ops = [{"src": str(tmp_path / "a.txt"), "dest": str(tmp_path / "X" / "a.txt"), "folder": "X"}]
        success, errors = undo_operations(ops)
        assert success == 0
        assert len(errors) == 1


# ──────────────────────────────────────────────
# core organize — by type
# ──────────────────────────────────────────────

class TestOrganizeByType:
    def test_dry_run_does_not_move_files(self, tmp_path):
        from organizer.core import organize
        make_dir_with_files(tmp_path, ["photo.jpg", "report.pdf"])
        ops = organize(tmp_path, by="type", dry_run=True)
        assert len(ops) == 2
        assert (tmp_path / "photo.jpg").exists()
        assert (tmp_path / "report.pdf").exists()

    def test_files_moved_to_correct_folders(self, tmp_path):
        from organizer.core import organize
        make_dir_with_files(tmp_path, ["photo.jpg", "clip.mp4", "notes.txt"])
        organize(tmp_path, by="type")
        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Videos" / "clip.mp4").exists()
        assert (tmp_path / "Documents" / "notes.txt").exists()

    def test_unknown_extension_goes_to_others(self, tmp_path):
        from organizer.core import organize
        make_dir_with_files(tmp_path, ["mystery.xyz123"])
        organize(tmp_path, by="type")
        assert (tmp_path / "Others" / "mystery.xyz123").exists()

    def test_empty_directory_no_crash(self, tmp_path):
        from organizer.core import organize
        ops = organize(tmp_path, by="type")
        assert ops == []

    def test_naming_conflict_resolved(self, tmp_path):
        from organizer.core import organize
        make_dir_with_files(tmp_path, ["photo.jpg"])
        (tmp_path / "Images").mkdir()
        (tmp_path / "Images" / "photo.jpg").write_bytes(b"existing")
        make_dir_with_files(tmp_path, ["photo.jpg"])
        organize(tmp_path, by="type")
        images = list((tmp_path / "Images").iterdir())
        assert len(images) == 2

    def test_hidden_files_ignored(self, tmp_path):
        from organizer.core import organize
        (tmp_path / ".hidden.jpg").write_bytes(b"x")
        (tmp_path / "visible.jpg").write_bytes(b"x")
        organize(tmp_path, by="type")
        assert (tmp_path / ".hidden.jpg").exists()
        assert (tmp_path / "Images" / "visible.jpg").exists()

    def test_undo_log_saved_after_move(self, tmp_path):
        from organizer.core import organize
        from organizer.undo import load_last_operations, UNDO_LOG_FILENAME
        make_dir_with_files(tmp_path, ["song.mp3"])
        organize(tmp_path, by="type")
        ops = load_last_operations(tmp_path)
        assert ops is not None
        assert len(ops) == 1
        assert "Audio" in ops[0]["dest"]


# ──────────────────────────────────────────────
# core organize — by date
# ──────────────────────────────────────────────

class TestOrganizeByDate:
    def test_file_moved_into_date_folder(self, tmp_path):
        from organizer.core import organize
        import os, time
        f = tmp_path / "file.txt"
        f.write_text("hello")
        # Set mtime to a known date: 2024-03-15
        ts = 1710460800  # 2024-03-15 00:00:00 UTC
        os.utime(f, (ts, ts))
        organize(tmp_path, by="date")
        # default date_format is %Y/%m
        assert (tmp_path / "2024" / "03" / "file.txt").exists()

    def test_dry_run_by_date(self, tmp_path):
        from organizer.core import organize
        (tmp_path / "a.txt").write_text("x")
        ops = organize(tmp_path, by="date", dry_run=True)
        assert len(ops) == 1
        assert (tmp_path / "a.txt").exists()


# ──────────────────────────────────────────────
# core organize — by extension
# ──────────────────────────────────────────────

class TestOrganizeByExtension:
    def test_grouped_by_extension(self, tmp_path):
        from organizer.core import organize
        make_dir_with_files(tmp_path, ["a.jpg", "b.jpg", "c.pdf"])
        organize(tmp_path, by="extension")
        assert (tmp_path / "JPG" / "a.jpg").exists()
        assert (tmp_path / "JPG" / "b.jpg").exists()
        assert (tmp_path / "PDF" / "c.pdf").exists()

    def test_no_extension_goes_to_others(self, tmp_path):
        from organizer.core import organize
        (tmp_path / "Makefile").write_text("all:")
        organize(tmp_path, by="extension")
        assert (tmp_path / "Others" / "Makefile").exists()


# ──────────────────────────────────────────────
# custom config rules
# ──────────────────────────────────────────────

class TestCustomConfig:
    def test_custom_extension_rule_applied(self, tmp_path):
        from organizer.core import organize
        from organizer.config import CONFIG_FILENAME
        cfg = {"type_rules": {"Projects": [".project"]}}
        (tmp_path / CONFIG_FILENAME).write_text(json.dumps(cfg))
        (tmp_path / "work.project").write_text("data")
        organize(tmp_path, by="type")
        assert (tmp_path / "Projects" / "work.project").exists()

    def test_custom_others_folder(self, tmp_path):
        from organizer.core import organize
        from organizer.config import CONFIG_FILENAME
        cfg = {"others_folder": "Unsorted"}
        (tmp_path / CONFIG_FILENAME).write_text(json.dumps(cfg))
        (tmp_path / "weird.zzz").write_text("?")
        organize(tmp_path, by="type")
        assert (tmp_path / "Unsorted" / "weird.zzz").exists()
