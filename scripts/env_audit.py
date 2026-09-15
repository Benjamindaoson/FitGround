#!/usr/bin/env python3
"""Write environment audit report."""

import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPORTS = Path(__file__).resolve().parents[1] / "reports"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage("/workspace").free
    total = shutil.disk_usage("/workspace").total

    git_head = "NO_GIT"
    git_status = "NO_GIT"
    try:
        git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        git_status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
    except Exception:
        pass

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "disk_total_bytes": total,
        "disk_free_bytes": free,
        "filesystem": subprocess.check_output(["df", "-T", "/workspace"], text=True).strip(),
        "git_head": git_head,
        "git_status": git_status,
    }
    (REPORTS / "environment_audit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
