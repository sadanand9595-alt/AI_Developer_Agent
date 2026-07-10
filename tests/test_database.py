def test_database_initializes_schema_and_persists_rows(isolated_database):
    isolated_database.execute(
        "INSERT INTO project_settings (setting_key, setting_value) VALUES (?, ?)",
        ("theme", "dark"),
    )

    row = isolated_database.fetchone(
        "SELECT setting_value FROM project_settings WHERE setting_key = ?",
        ("theme",),
    )
    table = isolated_database.fetchone(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'files'"
    )

    assert row["setting_value"] == "dark"
    assert table["name"] == "files"
