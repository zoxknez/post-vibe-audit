"""
VAF Scanner — Gitleaks

Scans git history and working tree for leaked secrets.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vaf.config import VAFConfig


def is_available() -> bool:
    return shutil.which("gitleaks") is not None


def run(root_dir: Path, config: VAFConfig) -> dict[str, Any]:
    """Run gitleaks and return normalized results."""
    output_dir = root_dir / ".vibe_audit" / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_path = output_dir / "gitleaks.json"

    cmd = [
        "gitleaks", "detect",
        "--source", str(root_dir),
        "--report-format", "json",
        "--report-path", str(raw_output_path),
        "--exit-code", "0",  # Don't fail — we handle it
        "--no-banner",
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        return {
            "tool": "gitleaks",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Gitleaks timed out.",
        }
    except (FileNotFoundError, OSError) as exc:
        return {
            "tool": "gitleaks",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": str(exc),
        }

    # Gitleaks returns empty file or no file if no secrets found — that's ok
    if not raw_output_path.exists():
        return {
            "tool": "gitleaks",
            "status": "executed",
            "findings": [],
            "raw_output_path": None,
            "error_message": None,
        }

    try:
        content = raw_output_path.read_text(encoding="utf-8").strip()
        if not content or content == "null":
            data = []
        else:
            data = json.loads(content)
            if not isinstance(data, list):
                data = []
    except (json.JSONDecodeError, OSError):
        data = []

    findings = []
    for leak in data:
        findings.append({
            "id": f"GITLEAKS-{leak.get('RuleID', 'UNKNOWN')}",
            "title": f"Secret leaked: {leak.get('Description', leak.get('RuleID', ''))}",
            "severity": "high",
            "type": "secret",
            "file": leak.get("File", ""),
            "line": leak.get("StartLine", 0),
            "commit": leak.get("Commit", ""),
            "author": leak.get("Author", ""),
            "date": leak.get("Date", ""),
            "fingerprint": leak.get("Fingerprint", ""),
            # Never include the actual secret value
            "redacted": True,
        })

    return {
        "tool": "gitleaks",
        "status": "executed",
        "findings": findings,
        "raw_output_path": str(raw_output_path),
        "error_message": None,
        "summary": {
            "secrets_found": len(findings),
        },
    }
