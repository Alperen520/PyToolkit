"""Tests for tools.file_renamer."""

import pytest

from tools import file_renamer


def make_files(directory, names):
    for name in names:
        (directory / name).write_text("x")


def test_regex_replace(tmp_path):
    make_files(tmp_path, ["IMG_001.jpg", "IMG_002.jpg", "note.txt"])
    exit_code = file_renamer.main([
        "--dir", str(tmp_path),
        "--pattern", "IMG_",
        "--replace", "photo_",
        "--ext", ".jpg",
    ])
    assert exit_code == 0
    assert (tmp_path / "photo_001.jpg").exists()
    assert (tmp_path / "photo_002.jpg").exists()
    assert (tmp_path / "note.txt").exists()  # untouched


def test_prefix_suffix(tmp_path):
    make_files(tmp_path, ["report.pdf"])
    file_renamer.main([
        "--dir", str(tmp_path),
        "--prefix", "2026_",
        "--suffix", "_final",
    ])
    assert (tmp_path / "2026_report_final.pdf").exists()


def test_lowercase(tmp_path):
    make_files(tmp_path, ["MIXED_Case.TXT"])
    file_renamer.main(["--dir", str(tmp_path), "--lowercase"])
    # Extension preserved as-is; only stem transformed.
    assert (tmp_path / "mixed_case.TXT").exists()


def test_sequence(tmp_path):
    make_files(tmp_path, ["a.pdf", "b.pdf", "c.pdf"])
    file_renamer.main([
        "--dir", str(tmp_path),
        "--sequence", "scan_{n:03d}",
    ])
    assert (tmp_path / "scan_001.pdf").exists()
    assert (tmp_path / "scan_002.pdf").exists()
    assert (tmp_path / "scan_003.pdf").exists()


def test_dry_run_does_not_rename(tmp_path):
    make_files(tmp_path, ["old.txt"])
    file_renamer.main([
        "--dir", str(tmp_path),
        "--pattern", "old",
        "--replace", "new",
        "--dry-run",
    ])
    assert (tmp_path / "old.txt").exists()
    assert not (tmp_path / "new.txt").exists()


def test_no_transformation_returns_error(tmp_path):
    make_files(tmp_path, ["x.txt"])
    assert file_renamer.main(["--dir", str(tmp_path)]) == 2


def test_invalid_directory_returns_error(tmp_path):
    missing = tmp_path / "nope"
    assert file_renamer.main(["--dir", str(missing), "--lowercase"]) == 2


def test_recursive_picks_up_subdirectories(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    make_files(sub, ["NESTED.md"])
    file_renamer.main([
        "--dir", str(tmp_path),
        "--lowercase",
        "--recursive",
    ])
    assert (sub / "nested.md").exists()


def test_collision_is_skipped(tmp_path):
    (tmp_path / "a.txt").write_text("first")
    (tmp_path / "b.txt").write_text("second")
    # Renaming b->a would collide; the tool must refuse to overwrite.
    file_renamer.main([
        "--dir", str(tmp_path),
        "--pattern", "b",
        "--replace", "a",
    ])
    assert (tmp_path / "a.txt").read_text() == "first"
    assert (tmp_path / "b.txt").read_text() == "second"
