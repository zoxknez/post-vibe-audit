"""
VAF Scanner — Semgrep

Runs Semgrep pattern-based SAST across multiple languages.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vaf.config import VAFConfig


def is_available() -> bool:
    return shutil.which("semgrep") is not None


def run(root_dir: Path, config: VAFConfig) -> dict[str, Any]:
    """Run semgrep with auto config and return normalized results."""
    output_dir = root_dir / ".vibe_audit" / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_path = output_dir / "semgrep.json"

    cmd = [
        "semgrep",
        "--config=auto",
        "--json",
        f"--output={raw_output_path}",
        "--timeout=30",
        "--max-memory=1000",
        str(root_dir),
    ]

    # Exclude dirs
    for excl in config.exclude_dirs:
        cmd.extend(["--exclude-dir", excl])

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired:
        return {
            "tool": "semgrep",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Semgrep timed out.",
        }
    except (FileNotFoundError, OSError) as exc:
        return {
            "tool": "semgrep",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": str(exc),
        }

    if not raw_output_path.exists():
        return {
            "tool": "semgrep",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Semgrep produced no output.",
        }

    try:
        data = json.loads(raw_output_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "tool": "semgrep",
            "status": "error",
            "findings": [],
            "raw_output_path": str(raw_output_path),
            "error_message": str(exc),
        }

    findings = []
    for r in data.get("results", []):
        severity_raw = r.get("extra", {}).get("severity", "WARNING").upper()
        severity_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
        severity = severity_map.get(severity_raw, "medium")

        findings.append({
            "id": r.get("check_id", ""),
            "title": r.get("check_id", "").split(".")[-1],
            "severity": severity,
            "type": "sast",
            "file": r.get("path", ""),
            "line_start": r.get("start", {}).get("line", 0),
            "line_end": r.get("end", {}).get("line", 0),
            "message": r.get("extra", {}).get("message", ""),
            "fix": r.get("extra", {}).get("fix", ""),
        })

    return {
        "tool": "semgrep",
        "status": "executed",
        "findings": findings,
        "raw_output_path": str(raw_output_path),
        "error_message": None,
        "summary": {
            "high": sum(1 for f in findings if f.get("severity") == "high"),
            "medium": sum(1 for f in findings if f.get("severity") == "medium"),
            "low": sum(1 for f in findings if f.get("severity") == "low"),
        },
    }
