from core.file_scanner import FileScanner
from pathlib import Path


def test_scan_returns_supported_files_and_excludes_ignored_directories(workspace):
    files = FileScanner(workspace).scan()
    by_path = {item.relative_path: item for item in files}

    assert set(by_path) == {
        "README.md",
        "settings.yaml",
        str(Path("src") / "helpers.py"),
        str(Path("src") / "main.py"),
    }
    main_path = str(Path("src") / "main.py")
    assert by_path[main_path].extension == ".py"
    assert by_path[main_path].line_count == 13
    assert by_path["README.md"].size > 0


def test_scanner_rejects_missing_workspace(tmp_path):
    missing = tmp_path / "missing"

    try:
        FileScanner(missing)
    except FileNotFoundError as error:
        assert error.args[0] == missing.resolve()
    else:
        raise AssertionError("FileScanner must reject a missing workspace")
