import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BUILD = PROJECT_ROOT / "build"
DIST = PROJECT_ROOT / "dist"

APP_NAME = "GEETA_AI"
MAIN_FILE = "main.py"


def safe_remove(folder: Path):
    if folder.exists():
        for _ in range(3):
            try:
                shutil.rmtree(folder)
                return
            except PermissionError:
                print(f"Folder locked: {folder}")
                time.sleep(2)
        print(f"Warning: Could not remove {folder}. Continuing...")


print("=" * 60)
print("GEETA AI Build")
print("=" * 60)

safe_remove(BUILD)
safe_remove(DIST)

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    "--windowed",
    "--name",
    APP_NAME,
    MAIN_FILE,
]

print("Running:")
print(" ".join(cmd))

subprocess.check_call(cmd)

print("\nBuild Finished.")
print("Output Folder:", DIST / APP_NAME)