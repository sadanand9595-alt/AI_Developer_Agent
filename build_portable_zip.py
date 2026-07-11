import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DIST = PROJECT_ROOT / "dist"

APP_NAME = "GEETA_AI"

SOURCE = DIST / APP_NAME
ZIP_FILE = DIST / f"{APP_NAME}_Portable.zip"

if not SOURCE.exists():
    raise FileNotFoundError(
        f"Folder not found: {SOURCE}\nRun build_windows_installer.py first."
    )

if ZIP_FILE.exists():
    ZIP_FILE.unlink()

print("Creating Portable ZIP...")

with zipfile.ZipFile(
    ZIP_FILE,
    "w",
    zipfile.ZIP_DEFLATED
) as z:

    for file in SOURCE.rglob("*"):
        z.write(
            file,
            file.relative_to(SOURCE.parent)
        )

print("Portable ZIP created:")
print(ZIP_FILE)