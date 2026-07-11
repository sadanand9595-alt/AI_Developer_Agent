from __future__ import annotations

from pathlib import Path


class CrashReporter:
    """Simple crash reporter that writes a text report for later inspection."""

    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir or Path(__file__).resolve().parent.parent / "logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, message: str) -> str:
        report_path = self.output_dir / "crash_report.txt"
        report_path.write_text(message, encoding="utf-8")
        return str(report_path)
