from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


class MemoryAnalyzer:
    """Simple memory/path analyzer for workspace inspection."""

    def analyze_path(self, path: str | Path) -> Dict[str, Any]:
        target = Path(path)
        return {"path": str(target), "exists": target.exists(), "size": sum(p.stat().st_size for p in target.rglob('*') if p.is_file()) if target.exists() else 0}
