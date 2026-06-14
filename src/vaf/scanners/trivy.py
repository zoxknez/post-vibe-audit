"""
VAF Scanner — Trivy

Runs Trivy filesystem scan for vulnerabilities, misconfigurations, secrets, and licenses.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vaf.config import VAFConfig


def is_available() -> bool:
    """Check if trivy is installed."""
    return shutil.which("trivy") is not None


def run(root_dir: Path, config: VAFConfig) -> dict[str, Any]:
    """
    Run trivy fs scan and return normalized results.

    Args:
        root_dir: Directory to scan.
        config: VAF configuration.

    Returns:
        Normalized scan result dict.
    """
    output_dir = root_dir / ".vibe_audit" / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_path = output_dir / "trivy.json"

    cmd = [
        "trivy", "fs",
        "--scanners", "vuln,misconfig,secret,license",
        "--format", "json",
        "--output", str(raw_output_path),
        "--exit-code", "0",  # Don't fail — we handle severity ourselves
        str(root_dir),
    ]

    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "tool": "trivy",
            "status": "error",
            "findings": [],
            "raw_output_path": str(raw_output_path),
            "error_message": "Trivy scan timed out after 120 seconds.",
        }
    except (FileNotFoundError, OSError) as exc:
        return {
            "tool": "trivy",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": str(exc),
        }

    if not raw_output_path.exists():
        return {
            "tool": "trivy",
            "status": "error",
            "findings": [],
            "raw_output_path": None,
            "error_message": "Trivy produced no output file.",
        }

    # Parse and normalize
    try:
        data = json.loads(raw_output_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "tool": "trivy",
            "status": "error",
            "findings": [],
            "raw_output_path": str(raw_output_path),
            "error_message": f"Failed to parse trivy output: {exc}",
        }

    findings = []
    results = data.get("Results", [])
    for result in results:
        # Vulnerabilities
        for vuln in result.get("Vulnerabilities", []) or []:
            findings.append({
                "id": vuln.get("VulnerabilityID", ""),
                "title": vuln.get("Title", vuln.get("VulnerabilityID", "")),
                "severity": vuln.get("Severity", "UNKNOWN").lower(),
                "type": "vulnerability",
                "package": vuln.get("PkgName", ""),
                "version": vuln.get("InstalledVersion", ""),
                "fixed_version": vuln.get("FixedVersion", ""),
                "file": result.get("Target", ""),
                "cvss": vuln.get("CVSS", {}),
                "references": vuln.get("References", [])[:3],
            })

        # Secrets
        for secret in result.get("Secrets", []) or []:
            findings.append({
                "id": f"TRIVY-SECRET-{secret.get('RuleID', 'UNKNOWN')}",
                "title": f"Secret détecté: {secret.get('Title', secret.get('RuleID', ''))}",
                "severity": "high",
                "type": "secret",
                "file": result.get("Target", ""),
                "line": secret.get("StartLine", 0),
            })

        # Misconfigs
        for mc in result.get("Misconfigurations", []) or []:
            findings.append({
                "id": mc.get("ID", ""),
                "title": mc.get("Title", ""),
                "severity": mc.get("Severity", "UNKNOWN").lower(),
                "type": "misconfiguration",
                "file": result.get("Target", ""),
                "description": mc.get("Description", ""),
                "resolution": mc.get("Resolution", ""),
            })

    return {
        "tool": "trivy",
        "status": "executed",
        "findings": findings,
        "raw_output_path": str(raw_output_path),
        "error_message": None,
        "summary": {
            "critical": sum(1 for f in findings if f.get("severity") == "critical"),
            "high": sum(1 for f in findings if f.get("severity") == "high"),
            "medium": sum(1 for f in findings if f.get("severity") == "medium"),
            "low": sum(1 for f in findings if f.get("severity") == "low"),
        },
    }
