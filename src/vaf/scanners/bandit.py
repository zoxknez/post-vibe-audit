"""
VAF Scanner — Bandit

Runs Bandit AST-based security analysis for Python projects.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vaf.config import VAFConfig


def is_available() -> bool:
    """Check if bandit is installed."""
    return shutil.which("bandit") is not None


def run(root_dir: Path, config: VAFConfig) -> dict[str, Any]:
    """Run bandit and return normalized results."""
    if not (root_dir / "pyproject.toml").exists() and not (root_dir / "requirements.txt").exists():
        return {
            "tool": "bandit",
            "status": "skipped",
            "findings": [],
            "raw_output_path": None,
            "error_message": "No Python project detected.",
        }

    output_dir = root_dir / ".vibe_audit" / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_path = output_dir / "bandit.json"

    cmd = [
        "bandit", "-r", str(root_dir),
        "-f", "json",
        "-o", str(raw_output_path),
        "--exit-zero",
        "--exclude", ",".join(f"{root_dir}/{d}" for d in config.exclude_dirs if (root_dir / d).exists()),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired:
        return {
            "tool": "bandit",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Bandit timed out after 60 seconds.",
        }
    except (FileNotFoundError, OSError) as exc:
        return {
            "tool": "bandit",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": str(exc),
        }

    if not raw_output_path.exists():
        return {
            "tool": "bandit",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Bandit produced no output.",
        }

    try:
        data = json.loads(raw_output_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "tool": "bandit",
            "status": "error",
            "findings": [],
            "raw_output_path": str(raw_output_path),
            "error_message": str(exc),
        }

    findings = []
    for result in data.get("results", []):
        findings.append({
            "id": result.get("test_id", ""),
            "title": result.get("test_name", ""),
            "severity": result.get("issue_severity", "").lower(),
            "confidence": result.get("issue_confidence", "").lower(),
            "type": "sast",
            "file": result.get("filename", ""),
            "line": result.get("line_number", 0),
            "code": result.get("code", ""),
            "cwe": result.get("issue_cwe", {}).get("id", ""),
            "description": result.get("issue_text", ""),
        })

    severity_map = {"high": 3, "medium": 2, "low": 1}
    findings.sort(key=lambda f: severity_map.get(f.get("severity", ""), 0), reverse=True)

    return {
        "tool": "bandit",
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
