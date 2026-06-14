"""
VAF SARIF Reporter

Generates SARIF 2.1.0 output for GitHub Code Scanning integration.

SARIF format: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
GitHub Code Scanning: https://docs.github.com/en/code-security/code-scanning
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vaf import __version__

_SEVERITY_TO_SARIF_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "none",
}

_SEVERITY_TO_SECURITY_SEVERITY = {
    "critical": "9.5",
    "high": "7.5",
    "medium": "5.0",
    "low": "2.5",
    "info": "1.0",
}


def generate(input_dir: Path, output_dir: Path) -> Path | None:
    """
    Generate SARIF 2.1.0 report from scan results.

    Args:
        input_dir: Directory containing scan outputs.
        output_dir: Where to write vaf.sarif.

    Returns:
        Path to generated SARIF file, or None on failure.
    """
    scans_dir = input_dir / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "vaf.sarif"

    # Collect all findings
    all_findings: list[dict[str, Any]] = []
    if scans_dir.exists():
        for scan_file in sorted(scans_dir.glob("*.json")):
            try:
                data = json.loads(scan_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for f in data.get("findings", []):
                        all_findings.append({"tool": scan_file.stem, **f})
            except (json.JSONDecodeError, OSError):
                continue

    # Build SARIF rules from unique finding IDs
    rules: list[dict[str, Any]] = []
    seen_rules: set[str] = set()
    results: list[dict[str, Any]] = []

    for finding in all_findings:
        rule_id = finding.get("id", "VAF-UNKNOWN")
        severity = finding.get("severity", "info").lower()
        sarif_level = _SEVERITY_TO_SARIF_LEVEL.get(severity, "note")
        security_severity = _SEVERITY_TO_SECURITY_SEVERITY.get(severity, "1.0")

        # Add rule if not seen
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            title = finding.get("title") or rule_id
            rules.append({
                "id": rule_id,
                "name": _to_pascal_case(str(title)),
                "shortDescription": {
                    "text": finding.get("title", rule_id),
                },
                "fullDescription": {
                    "text": finding.get("description", finding.get("message", finding.get("title", ""))),
                },
                "defaultConfiguration": {
                    "level": sarif_level,
                },
                "properties": {
                    "security-severity": security_severity,
                    "tags": ["security", finding.get("type", "unknown")],
                },
            })

        # Build result
        file_path = finding.get("file", "")
        line = finding.get("line", finding.get("line_start", 1))
        line_end = finding.get("line_end", line)

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": sarif_level,
            "message": {
                "text": finding.get("description", finding.get("message", finding.get("title", rule_id))),
            },
        }

        if file_path:
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path.replace("\\", "/"),
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": max(1, int(line or 1)),
                            "endLine": max(1, int(line_end or line or 1)),
                        },
                    },
                }
            ]

        results.append(result)

    # Build SARIF document
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "VAF",
                        "fullName": "Vibe-Audit Framework",
                        "version": __version__,
                        "informationUri": "https://github.com/zoxknez/post-vibe-audit",
                        "rules": rules,
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "endTimeUtc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                ],
            }
        ],
    }

    output_path.write_text(
        json.dumps(sarif, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def _to_pascal_case(s: str) -> str:
    """Convert a string to PascalCase for SARIF rule names."""
    return "".join(word.capitalize() for word in s.replace("-", " ").replace("_", " ").split())
