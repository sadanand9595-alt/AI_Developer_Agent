# GEETA AI

GEETA AI is a Python-based desktop development assistant with a PySide6 interface, modular agent architecture, workspace indexing, and SQLite-backed project metadata.

## Release status
- Current release: v2.4.1
- Verified test status: 13 passed

## Key capabilities
- Open and browse project folders from the integrated explorer.
- Edit files in the built-in editor and save them back to disk.
- Scan and index workspace files through the existing core modules.
- Run the project test suite with pytest.

## Development
```bash
python -m pytest -q
```

## Notes
The project keeps backward compatibility by reusing the existing architecture and extending it with small, focused modules where needed.
