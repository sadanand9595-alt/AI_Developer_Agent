PRAGMA foreign_keys = ON;

-- ==========================================================
-- GEETA AI IDE
-- Database Schema
-- Version : 2.3.0
-- ==========================================================

-- ==========================================================
-- WORKSPACE
-- ==========================================================
CREATE TABLE IF NOT EXISTS workspace (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    root_path TEXT NOT NULL UNIQUE,

    language TEXT,
    framework TEXT,

    total_files INTEGER DEFAULT 0,

    indexed INTEGER DEFAULT 0,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_scan TEXT
);

-- ==========================================================
-- FILES
-- ==========================================================
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    workspace_id INTEGER,

    path TEXT NOT NULL UNIQUE,
    relative_path TEXT,
    file_name TEXT,

    extension TEXT,
    language TEXT,

    size INTEGER DEFAULT 0,
    line_count INTEGER DEFAULT 0,

    modified_time TEXT,
    checksum TEXT,

    FOREIGN KEY(workspace_id)
        REFERENCES workspace(id)
        ON DELETE CASCADE
);

-- ==========================================================
-- CLASSES
-- ==========================================================
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    file_id INTEGER NOT NULL,

    class_name TEXT NOT NULL,
    line_number INTEGER,

    docstring TEXT,

    FOREIGN KEY(file_id)
        REFERENCES files(id)
        ON DELETE CASCADE
);

-- ==========================================================
-- FUNCTIONS
-- ==========================================================
CREATE TABLE IF NOT EXISTS functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    file_id INTEGER NOT NULL,

    function_name TEXT NOT NULL,

    class_name TEXT,

    line_number INTEGER,

    arguments TEXT,
    return_type TEXT,

    docstring TEXT,

    FOREIGN KEY(file_id)
        REFERENCES files(id)
        ON DELETE CASCADE
);

-- ==========================================================
-- IMPORTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    file_id INTEGER NOT NULL,

    module_name TEXT NOT NULL,

    imported_name TEXT,

    alias TEXT,

    FOREIGN KEY(file_id)
        REFERENCES files(id)
        ON DELETE CASCADE
);

-- ==========================================================
-- DEPENDENCIES
-- ==========================================================
CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_file TEXT NOT NULL,

    target_module TEXT NOT NULL,

    dependency_type TEXT
);

-- ==========================================================
-- SYMBOLS
-- ==========================================================
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    file_id INTEGER NOT NULL,

    symbol_name TEXT NOT NULL,

    symbol_type TEXT NOT NULL,

    line_number INTEGER,

    FOREIGN KEY(file_id)
        REFERENCES files(id)
        ON DELETE CASCADE
);

-- ==========================================================
-- PROJECT SETTINGS
-- ==========================================================
CREATE TABLE IF NOT EXISTS project_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    setting_key TEXT UNIQUE,

    setting_value TEXT
);

-- ==========================================================
-- AI MEMORY
-- ==========================================================
CREATE TABLE IF NOT EXISTS ai_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    memory_key TEXT UNIQUE,

    memory_value TEXT,

    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- INDEXES
-- ==========================================================
CREATE INDEX IF NOT EXISTS idx_files_path
ON files(path);

CREATE INDEX IF NOT EXISTS idx_files_name
ON files(file_name);

CREATE INDEX IF NOT EXISTS idx_classes_name
ON classes(class_name);

CREATE INDEX IF NOT EXISTS idx_functions_name
ON functions(function_name);

CREATE INDEX IF NOT EXISTS idx_symbols_name
ON symbols(symbol_name);

CREATE INDEX IF NOT EXISTS idx_imports_module
ON imports(module_name);