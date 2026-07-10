from core.workspace_index import WorkspaceIndex


def test_workspace_index_builds_consistent_runtime_artifacts(workspace, isolated_database):
    index = WorkspaceIndex(workspace)

    indexed = index.build()
    summary = index.summary()
    context = index.get_context("src/main.py")

    assert indexed == 4
    assert index.total_files() == 2
    assert index.total_symbols() == 4
    assert index.total_dependencies() == 2
    assert index.get_file("src/main.py") is not None
    assert [symbol.name for symbol in index.get_symbols("src/main.py")] == [
        "Application",
        "run",
        "shutdown",
    ]
    assert context is not None
    assert context.dependencies == ["os", "src.helpers"]
    assert summary["failed_files"] == 0


def test_workspace_index_refreshes_and_removes_files_incrementally(workspace, isolated_database):
    index = WorkspaceIndex(workspace)
    index.build()
    main = workspace / "src" / "main.py"
    main.write_text("def replacement(value):\n    return value\n", encoding="utf-8")

    assert index.refresh_file(main)
    assert [symbol.name for symbol in index.get_symbols(main)] == ["replacement"]
    assert index.get_context(main).functions == ["replacement"]

    main.unlink()

    assert index.remove_file(main)
    assert not index.has_file(main)
    assert index.get_context(main) is None


def test_workspace_index_rejects_paths_outside_the_workspace(workspace, isolated_database, tmp_path):
    index = WorkspaceIndex(workspace)
    external = workspace.parent / f"{workspace.name}-external.py"
    external.write_text("def external():\n    return True\n", encoding="utf-8")

    assert not index.index_file(external)
    assert not index.remove_file(external)
